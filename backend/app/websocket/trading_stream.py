"""
交易流 WebSocket 端点

提供实时交易事件推送
"""

import asyncio
import json
import random
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from pydantic import BaseModel
import logging

from .connection_manager import manager

logger = logging.getLogger(__name__)
router = APIRouter()


class WebSocketMessage(BaseModel):
    """WebSocket 消息格式"""
    type: str  # "subscribe", "unsubscribe", "heartbeat"
    channel: Optional[str] = None
    symbols: Optional[List[str]] = None


@router.websocket("/ws/trading")
async def trading_websocket(
    websocket: WebSocket,
    mode: str = Query(default="paper", regex="^(live|paper)$"),
):
    """
    交易流 WebSocket 端点

    连接参数:
    - mode: "live" 或 "paper"

    消息类型:
    - subscribe: 订阅频道
    - unsubscribe: 取消订阅
    - heartbeat: 心跳

    频道:
    - orders: 订单事件
    - positions: 持仓事件
    - prices: 价格更新
    - pnl: 盈亏更新
    - alerts: 风险警报
    - all: 所有事件
    """
    client_id = f"client-{datetime.now().timestamp()}"

    await manager.connect(websocket, client_id, mode)

    # 启动模拟数据推送 (仅 paper 模式)
    simulation_task = None
    if mode == "paper":
        simulation_task = asyncio.create_task(
            simulate_trading_events(client_id)
        )

    try:
        while True:
            # 接收消息
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
                    symbols = message.get("symbols")
                    await manager.subscribe(client_id, channel, symbols)

                elif msg_type == "unsubscribe":
                    channel = message.get("channel")
                    if channel:
                        await manager.unsubscribe(client_id, channel)

            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON from {client_id}: {data}")

    except WebSocketDisconnect:
        logger.info(f"Client {client_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error for {client_id}: {e}")
    finally:
        if simulation_task:
            simulation_task.cancel()
        manager.disconnect(client_id)


async def simulate_trading_events(client_id: str):
    """
    模拟交易事件推送 (Paper Trading 模式)

    用于演示和测试
    """
    symbols = ["AAPL", "GOOGL", "MSFT", "AMZN", "META", "NVDA", "TSLA", "AMD"]
    base_prices = {
        "AAPL": 178.50,
        "GOOGL": 141.20,
        "MSFT": 378.90,
        "AMZN": 153.40,
        "META": 354.60,
        "NVDA": 495.20,
        "TSLA": 248.30,
        "AMD": 139.80,
    }

    # 模拟初始持仓
    positions = {
        "AAPL": {"qty": 100, "avg_price": 175.00},
        "MSFT": {"qty": 50, "avg_price": 370.00},
        "NVDA": {"qty": 30, "avg_price": 480.00},
    }

    try:
        # 初始推送: 持仓信息
        await asyncio.sleep(1)
        for symbol, pos in positions.items():
            current_price = base_prices[symbol]
            unrealized_pnl = (current_price - pos["avg_price"]) * pos["qty"]

            await manager.send_personal_message({
                "type": "event",
                "payload": {
                    "id": f"pos-{datetime.now().timestamp()}",
                    "type": "position_updated",
                    "timestamp": datetime.now().isoformat(),
                    "symbol": symbol,
                    "quantity": pos["qty"],
                    "avgPrice": pos["avg_price"],
                    "currentPrice": current_price,
                    "unrealizedPnl": unrealized_pnl,
                    "side": "buy",
                }
            }, client_id)
            await asyncio.sleep(0.2)

        # 初始推送: 盈亏摘要
        total_unrealized = sum(
            (base_prices[s] - p["avg_price"]) * p["qty"]
            for s, p in positions.items()
        )
        await manager.send_personal_message({
            "type": "event",
            "payload": {
                "id": f"pnl-{datetime.now().timestamp()}",
                "type": "pnl_update",
                "timestamp": datetime.now().isoformat(),
                "totalUnrealizedPnl": total_unrealized,
                "totalRealizedPnl": 1250.50,
                "dailyPnl": 325.80,
                "portfolioValue": 125000.00,
                "cashBalance": 45000.00,
            }
        }, client_id)

        # 持续推送价格更新
        event_counter = 0
        while client_id in manager.active_connections:
            await asyncio.sleep(random.uniform(1.5, 4.0))

            # 随机选择事件类型
            event_type = random.choices(
                ["price", "order", "alert"],
                weights=[0.7, 0.25, 0.05],
                k=1
            )[0]

            if event_type == "price":
                # 价格更新
                symbol = random.choice(symbols)
                prev_price = base_prices[symbol]
                change_pct = random.uniform(-0.02, 0.02)
                new_price = prev_price * (1 + change_pct)
                base_prices[symbol] = new_price
                change = new_price - prev_price

                await manager.broadcast_to_channel({
                    "type": "event",
                    "payload": {
                        "id": f"price-{datetime.now().timestamp()}",
                        "type": "price_update",
                        "timestamp": datetime.now().isoformat(),
                        "symbol": symbol,
                        "price": round(new_price, 2),
                        "previousPrice": round(prev_price, 2),
                        "change": round(change, 2),
                        "changePercent": round(change_pct * 100, 2),
                        "volume": random.randint(10000, 500000),
                    }
                }, "prices")

                # 更新持仓未实现盈亏
                if symbol in positions:
                    pos = positions[symbol]
                    unrealized_pnl = (new_price - pos["avg_price"]) * pos["qty"]

                    await manager.broadcast_to_channel({
                        "type": "event",
                        "payload": {
                            "id": f"pos-{datetime.now().timestamp()}",
                            "type": "position_updated",
                            "timestamp": datetime.now().isoformat(),
                            "symbol": symbol,
                            "quantity": pos["qty"],
                            "avgPrice": pos["avg_price"],
                            "currentPrice": round(new_price, 2),
                            "unrealizedPnl": round(unrealized_pnl, 2),
                            "side": "buy",
                        }
                    }, "positions")

            elif event_type == "order":
                # 模拟订单事件
                symbol = random.choice(symbols)
                side = random.choice(["buy", "sell"])
                qty = random.choice([10, 25, 50, 100])
                price = base_prices[symbol]

                order_status = random.choices(
                    ["filled", "partial_fill", "rejected"],
                    weights=[0.8, 0.15, 0.05],
                    k=1
                )[0]

                event_type_str = f"order_{order_status.replace('_', '_')}"
                if order_status == "partial_fill":
                    event_type_str = "order_partial_fill"
                elif order_status == "rejected":
                    event_type_str = "order_rejected"
                else:
                    event_type_str = "order_filled"

                await manager.broadcast_to_channel({
                    "type": "event",
                    "payload": {
                        "id": f"order-{datetime.now().timestamp()}",
                        "type": event_type_str,
                        "timestamp": datetime.now().isoformat(),
                        "orderId": f"ORD-{random.randint(10000, 99999)}",
                        "symbol": symbol,
                        "side": side,
                        "orderType": "market",
                        "quantity": qty,
                        "filledQuantity": qty if order_status == "filled" else int(qty * 0.6),
                        "filledPrice": round(price, 2),
                        "status": order_status,
                        "message": "模拟订单" if order_status != "rejected" else "余额不足",
                    }
                }, "orders")

            elif event_type == "alert":
                # 风险警报
                alert_types = [
                    ("info", "持仓集中度", "单只股票持仓超过 15%", "concentration", 18.5, 15.0),
                    ("warning", "波动率上升", "组合波动率超过阈值", "volatility", 25.3, 20.0),
                    ("critical", "最大回撤", "接近最大回撤限制", "max_drawdown", 8.5, 10.0),
                ]

                level, title, message, metric, current, threshold = random.choice(alert_types)

                await manager.broadcast_to_channel({
                    "type": "event",
                    "payload": {
                        "id": f"alert-{datetime.now().timestamp()}",
                        "type": "risk_alert",
                        "timestamp": datetime.now().isoformat(),
                        "level": level,
                        "title": title,
                        "message": message,
                        "metric": metric,
                        "currentValue": current,
                        "threshold": threshold,
                    }
                }, "alerts")

            event_counter += 1

    except asyncio.CancelledError:
        logger.info(f"Simulation stopped for {client_id}")
    except Exception as e:
        logger.error(f"Simulation error for {client_id}: {e}")


@router.get("/ws/stats")
async def websocket_stats():
    """获取 WebSocket 连接统计"""
    return {
        "connections": manager.get_connection_count(),
        "channels": manager.get_channel_stats(),
    }
