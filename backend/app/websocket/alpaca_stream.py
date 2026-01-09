"""
Alpaca WebSocket 流
Sprint 10: 实时 Alpaca 数据推送

功能:
- 账户/订单实时更新
- 持仓变动推送
- 风险预警推送
"""

import asyncio
import json
from datetime import datetime
from typing import Optional

import websockets
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
import structlog

from app.core.config import settings
from app.services.alpaca_client import get_alpaca_client
from app.services.realtime_monitor import realtime_monitor
from .connection_manager import manager

logger = structlog.get_logger()
router = APIRouter()


class AlpacaStreamHandler:
    """
    Alpaca WebSocket 流处理器

    连接 Alpaca 流并转发到客户端
    """

    def __init__(self):
        self._ws: Optional[websockets.WebSocketClientProtocol] = None
        self._running = False
        self._reconnect_delay = 3

    @property
    def stream_url(self) -> str:
        """获取 Alpaca 流 URL"""
        if "paper" in settings.ALPACA_BASE_URL:
            return "wss://paper-api.alpaca.markets/stream"
        return "wss://api.alpaca.markets/stream"

    async def connect(self):
        """连接到 Alpaca WebSocket"""
        if self._running:
            return

        self._running = True
        asyncio.create_task(self._stream_loop())

    async def disconnect(self):
        """断开连接"""
        self._running = False
        if self._ws:
            await self._ws.close()
            self._ws = None

    async def _stream_loop(self):
        """流处理主循环"""
        while self._running:
            try:
                async with websockets.connect(self.stream_url) as ws:
                    self._ws = ws
                    logger.info("alpaca_stream_connected")

                    # 认证
                    await self._authenticate(ws)

                    # 订阅
                    await self._subscribe(ws)

                    # 处理消息
                    async for message in ws:
                        await self._handle_message(message)

            except websockets.ConnectionClosed as e:
                logger.warning("alpaca_stream_closed", code=e.code, reason=e.reason)
            except Exception as e:
                logger.error("alpaca_stream_error", error=str(e))

            if self._running:
                logger.info("alpaca_stream_reconnecting", delay=self._reconnect_delay)
                await asyncio.sleep(self._reconnect_delay)

    async def _authenticate(self, ws):
        """发送认证"""
        auth_msg = {
            "action": "auth",
            "key": settings.ALPACA_API_KEY,
            "secret": settings.ALPACA_SECRET_KEY,
        }
        await ws.send(json.dumps(auth_msg))
        logger.info("alpaca_auth_sent")

    async def _subscribe(self, ws):
        """订阅数据流"""
        sub_msg = {
            "action": "listen",
            "data": {
                "streams": ["trade_updates"],
            },
        }
        await ws.send(json.dumps(sub_msg))
        logger.info("alpaca_subscribed")

    async def _handle_message(self, raw_message: str):
        """处理接收到的消息"""
        try:
            message = json.loads(raw_message)
            stream = message.get("stream")

            if stream == "authorization":
                status = message.get("data", {}).get("status")
                if status == "authorized":
                    logger.info("alpaca_authorized")
                else:
                    logger.error("alpaca_auth_failed", status=status)

            elif stream == "listening":
                streams = message.get("data", {}).get("streams", [])
                logger.info("alpaca_listening", streams=streams)

            elif stream == "trade_updates":
                await self._handle_trade_update(message.get("data", {}))

        except json.JSONDecodeError:
            logger.warning("alpaca_invalid_json", message=raw_message[:100])
        except Exception as e:
            logger.error("alpaca_message_error", error=str(e))

    async def _handle_trade_update(self, data: dict):
        """处理交易更新"""
        event = data.get("event")
        order = data.get("order", {})

        logger.info(
            "alpaca_trade_update",
            event=event,
            symbol=order.get("symbol"),
            side=order.get("side"),
        )

        # 构建推送消息
        ws_message = {
            "type": "event",
            "payload": {
                "id": f"alpaca-{datetime.now().timestamp()}",
                "type": f"order_{event}",
                "timestamp": datetime.now().isoformat(),
                "orderId": order.get("id"),
                "symbol": order.get("symbol"),
                "side": order.get("side"),
                "orderType": order.get("type"),
                "quantity": float(order.get("qty", 0)),
                "filledQuantity": float(order.get("filled_qty", 0)),
                "filledPrice": float(order.get("filled_avg_price") or 0),
                "status": order.get("status"),
                "event": event,
            },
        }

        # 广播到 orders 频道
        await manager.broadcast_to_channel(ws_message, "orders")

        # 如果是成交事件，也推送持仓更新
        if event in ["fill", "partial_fill"]:
            await self._broadcast_positions_update()

    async def _broadcast_positions_update(self):
        """广播持仓更新"""
        try:
            positions = await realtime_monitor.get_positions_detail()

            message = {
                "type": "event",
                "payload": {
                    "id": f"positions-{datetime.now().timestamp()}",
                    "type": "positions_snapshot",
                    "timestamp": datetime.now().isoformat(),
                    "positions": positions,
                    "count": len(positions),
                },
            }

            await manager.broadcast_to_channel(message, "positions")

        except Exception as e:
            logger.error("positions_broadcast_error", error=str(e))


# 全局实例
alpaca_stream = AlpacaStreamHandler()


@router.websocket("/ws/alpaca")
async def alpaca_websocket(
    websocket: WebSocket,
    mode: str = Query(default="paper", regex="^(live|paper)$"),
):
    """
    Alpaca 实时数据 WebSocket

    接收:
    - trade_updates: 订单更新
    - positions: 持仓变动

    消息格式:
    {
        "type": "event",
        "payload": {
            "type": "order_fill" | "order_canceled" | "positions_snapshot",
            ...
        }
    }
    """
    client_id = f"alpaca-{datetime.now().timestamp()}"

    await manager.connect(websocket, client_id, mode)

    # 确保 Alpaca 流已连接
    await alpaca_stream.connect()

    try:
        # 发送初始状态
        status = await realtime_monitor.get_current_status()
        await manager.send_personal_message({
            "type": "event",
            "payload": {
                "id": f"init-{datetime.now().timestamp()}",
                "type": "initial_status",
                "timestamp": datetime.now().isoformat(),
                **status,
            },
        }, client_id)

        # 发送当前持仓
        positions = await realtime_monitor.get_positions_detail()
        await manager.send_personal_message({
            "type": "event",
            "payload": {
                "id": f"positions-{datetime.now().timestamp()}",
                "type": "positions_snapshot",
                "timestamp": datetime.now().isoformat(),
                "positions": positions,
                "count": len(positions),
            },
        }, client_id)

        # 处理客户端消息
        while True:
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
                msg_type = message.get("type")

                if msg_type == "heartbeat":
                    manager.update_heartbeat(client_id)
                    await manager.send_personal_message({
                        "type": "heartbeat",
                        "timestamp": datetime.now().isoformat(),
                    }, client_id)

                elif msg_type == "subscribe":
                    channel = message.get("channel", "all")
                    await manager.subscribe(client_id, channel)

                elif msg_type == "unsubscribe":
                    channel = message.get("channel")
                    if channel:
                        await manager.unsubscribe(client_id, channel)

                elif msg_type == "refresh_positions":
                    positions = await realtime_monitor.get_positions_detail()
                    await manager.send_personal_message({
                        "type": "event",
                        "payload": {
                            "id": f"positions-{datetime.now().timestamp()}",
                            "type": "positions_snapshot",
                            "timestamp": datetime.now().isoformat(),
                            "positions": positions,
                            "count": len(positions),
                        },
                    }, client_id)

                elif msg_type == "refresh_status":
                    status = await realtime_monitor.get_current_status()
                    await manager.send_personal_message({
                        "type": "event",
                        "payload": {
                            "id": f"status-{datetime.now().timestamp()}",
                            "type": "status_update",
                            "timestamp": datetime.now().isoformat(),
                            **status,
                        },
                    }, client_id)

            except json.JSONDecodeError:
                logger.warning("invalid_json", client=client_id)

    except WebSocketDisconnect:
        logger.info("client_disconnected", client=client_id)
    except Exception as e:
        logger.error("websocket_error", client=client_id, error=str(e))
    finally:
        manager.disconnect(client_id)
