"""
策略回放API
PRD 4.17 策略回放功能
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect

from app.schemas.replay import (
    ReplayConfig,
    ReplayExport,
    ReplayInitResponse,
    ReplayInsight,
    ReplaySpeed,
    ReplayState,
    ReplayTickResponse,
    SeekRequest,
    SpeedRequest,
)
from app.services.replay_engine_service import get_replay_engine_service

router = APIRouter(prefix="/replay", tags=["策略回放"])

# 模拟用户ID
MOCK_USER_ID = "user_001"


@router.post(
    "/init",
    response_model=ReplayInitResponse,
    summary="初始化回放会话",
)
async def init_replay(config: ReplayConfig) -> ReplayInitResponse:
    """
    初始化回放会话

    1. 加载历史数据
    2. 预计算信号标记位置 (用于进度条)
    3. 返回初始状态
    """
    service = get_replay_engine_service()

    try:
        result = await service.init_replay(MOCK_USER_ID, config)
        return ReplayInitResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/{session_id}/play",
    response_model=ReplayState,
    summary="开始/继续播放",
)
async def play_replay(session_id: str) -> ReplayState:
    """开始或继续播放"""
    service = get_replay_engine_service()

    try:
        return await service.play(session_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post(
    "/{session_id}/pause",
    response_model=ReplayState,
    summary="暂停播放",
)
async def pause_replay(session_id: str) -> ReplayState:
    """暂停播放"""
    service = get_replay_engine_service()

    try:
        return await service.pause(session_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post(
    "/{session_id}/step-forward",
    response_model=ReplayTickResponse,
    summary="前进一步",
)
async def step_forward(session_id: str) -> ReplayTickResponse:
    """前进一步"""
    service = get_replay_engine_service()

    try:
        return await service.step_forward(session_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post(
    "/{session_id}/step-backward",
    response_model=ReplayTickResponse,
    summary="后退一步",
)
async def step_backward(session_id: str) -> ReplayTickResponse:
    """后退一步"""
    service = get_replay_engine_service()

    try:
        return await service.step_backward(session_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post(
    "/{session_id}/seek",
    response_model=ReplayTickResponse,
    summary="跳转到指定时间",
)
async def seek_to_time(session_id: str, request: SeekRequest) -> ReplayTickResponse:
    """跳转到指定时间"""
    service = get_replay_engine_service()

    try:
        return await service.seek_to_time(session_id, request.target_time)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post(
    "/{session_id}/next-signal",
    response_model=ReplayTickResponse,
    summary="跳转到下一个信号",
)
async def seek_to_next_signal(session_id: str) -> ReplayTickResponse:
    """跳转到下一个信号"""
    service = get_replay_engine_service()

    try:
        return await service.seek_to_next_signal(session_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put(
    "/{session_id}/speed",
    response_model=ReplayState,
    summary="设置回放速度",
)
async def set_speed(session_id: str, request: SpeedRequest) -> ReplayState:
    """设置回放速度 (0.5x/1x/2x/5x)"""
    service = get_replay_engine_service()

    try:
        return await service.set_speed(session_id, request.speed)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/{session_id}/insight",
    response_model=ReplayInsight,
    summary="获取回放洞察",
)
async def get_replay_insight(session_id: str) -> ReplayInsight:
    """获取回放洞察"""
    service = get_replay_engine_service()

    try:
        return await service.get_insight(session_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/{session_id}/export",
    response_model=ReplayExport,
    summary="导出回放记录",
)
async def export_replay(session_id: str) -> ReplayExport:
    """导出回放记录"""
    service = get_replay_engine_service()

    try:
        result = await service.export_replay(session_id)
        return ReplayExport(**result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.websocket("/{session_id}/stream")
async def replay_stream(websocket: WebSocket, session_id: str):
    """
    WebSocket实时回放流

    播放时持续推送:
    - 当前K线数据
    - 因子快照
    - 信号事件
    """
    await websocket.accept()

    service = get_replay_engine_service()

    try:
        # 验证会话存在
        session = service._get_session(session_id)
    except ValueError:
        await websocket.close(code=4004, reason="Session not found")
        return

    try:
        while True:
            # 等待客户端消息
            data = await websocket.receive_json()
            command = data.get("command")

            if command == "play":
                await service.play(session_id)

                # 自动播放循环
                state = session["state"]
                speed_map = {"0.5x": 2.0, "1x": 1.0, "2x": 0.5, "5x": 0.2}
                interval = speed_map.get(state.config.speed.value, 1.0)

                import asyncio

                while (
                    state.status.value == "playing"
                    and state.current_bar_index < state.total_bars - 1
                ):
                    tick = await service.step_forward(session_id)
                    await websocket.send_json(tick.model_dump(mode="json"))
                    await asyncio.sleep(interval)

            elif command == "pause":
                state = await service.pause(session_id)
                await websocket.send_json({"type": "state", "data": state.model_dump(mode="json")})

            elif command == "step_forward":
                tick = await service.step_forward(session_id)
                await websocket.send_json(tick.model_dump(mode="json"))

            elif command == "step_backward":
                tick = await service.step_backward(session_id)
                await websocket.send_json(tick.model_dump(mode="json"))

            elif command == "next_signal":
                tick = await service.seek_to_next_signal(session_id)
                await websocket.send_json(tick.model_dump(mode="json"))

            elif command == "set_speed":
                speed = ReplaySpeed(data.get("speed", "1x"))
                state = await service.set_speed(session_id, speed)
                await websocket.send_json({"type": "state", "data": state.model_dump(mode="json")})

    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.close(code=4000, reason=str(e))
