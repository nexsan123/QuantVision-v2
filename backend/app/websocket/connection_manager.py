"""
WebSocket 连接管理器

管理多个客户端连接、订阅和消息广播
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, List, Set, Optional, Any
from fastapi import WebSocket
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class ClientConnection:
    """客户端连接信息"""
    websocket: WebSocket
    client_id: str
    mode: str = "paper"  # "live" or "paper"
    subscriptions: Set[str] = field(default_factory=set)
    connected_at: datetime = field(default_factory=datetime.now)
    last_heartbeat: datetime = field(default_factory=datetime.now)


class ConnectionManager:
    """
    WebSocket 连接管理器

    功能:
    - 管理多个客户端连接
    - 订阅/取消订阅频道
    - 消息广播
    - 心跳检测
    """

    def __init__(self):
        self.active_connections: Dict[str, ClientConnection] = {}
        self.channel_subscribers: Dict[str, Set[str]] = {
            "orders": set(),
            "positions": set(),
            "prices": set(),
            "pnl": set(),
            "alerts": set(),
            "all": set(),
        }
        self._heartbeat_interval = 30  # 秒
        self._heartbeat_task: Optional[asyncio.Task] = None

    async def connect(self, websocket: WebSocket, client_id: str, mode: str = "paper"):
        """接受新连接"""
        await websocket.accept()

        connection = ClientConnection(
            websocket=websocket,
            client_id=client_id,
            mode=mode,
        )
        self.active_connections[client_id] = connection

        # 默认订阅 all 频道
        self.channel_subscribers["all"].add(client_id)
        connection.subscriptions.add("all")

        logger.info(f"Client {client_id} connected in {mode} mode")

        # 发送连接确认
        await self.send_personal_message({
            "type": "system_message",
            "payload": {
                "id": f"sys-{datetime.now().timestamp()}",
                "type": "system_message",
                "timestamp": datetime.now().isoformat(),
                "level": "success",
                "title": "连接成功",
                "message": f"已连接到{'实盘' if mode == 'live' else '模拟'}交易流",
            }
        }, client_id)

    def disconnect(self, client_id: str):
        """断开连接"""
        if client_id in self.active_connections:
            connection = self.active_connections[client_id]

            # 从所有频道移除
            for channel in connection.subscriptions:
                if channel in self.channel_subscribers:
                    self.channel_subscribers[channel].discard(client_id)

            del self.active_connections[client_id]
            logger.info(f"Client {client_id} disconnected")

    async def subscribe(self, client_id: str, channel: str, symbols: Optional[List[str]] = None):
        """订阅频道"""
        if client_id not in self.active_connections:
            return

        connection = self.active_connections[client_id]

        if channel in self.channel_subscribers:
            self.channel_subscribers[channel].add(client_id)
            connection.subscriptions.add(channel)

            logger.info(f"Client {client_id} subscribed to {channel}")

            await self.send_personal_message({
                "type": "system_message",
                "payload": {
                    "id": f"sys-{datetime.now().timestamp()}",
                    "type": "system_message",
                    "timestamp": datetime.now().isoformat(),
                    "level": "info",
                    "title": "订阅成功",
                    "message": f"已订阅 {channel} 频道",
                }
            }, client_id)

    async def unsubscribe(self, client_id: str, channel: str):
        """取消订阅"""
        if client_id not in self.active_connections:
            return

        connection = self.active_connections[client_id]

        if channel in self.channel_subscribers:
            self.channel_subscribers[channel].discard(client_id)
            connection.subscriptions.discard(channel)

            logger.info(f"Client {client_id} unsubscribed from {channel}")

    async def send_personal_message(self, message: Dict[str, Any], client_id: str):
        """发送个人消息"""
        if client_id in self.active_connections:
            connection = self.active_connections[client_id]
            try:
                await connection.websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error sending message to {client_id}: {e}")
                self.disconnect(client_id)

    async def broadcast_to_channel(self, message: Dict[str, Any], channel: str):
        """广播到频道"""
        if channel not in self.channel_subscribers:
            return

        # 同时发送给 all 订阅者
        recipients = self.channel_subscribers[channel] | self.channel_subscribers["all"]

        disconnected = []
        for client_id in recipients:
            if client_id in self.active_connections:
                try:
                    await self.active_connections[client_id].websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Error broadcasting to {client_id}: {e}")
                    disconnected.append(client_id)

        # 清理断开的连接
        for client_id in disconnected:
            self.disconnect(client_id)

    async def broadcast_all(self, message: Dict[str, Any]):
        """广播到所有连接"""
        disconnected = []
        for client_id, connection in self.active_connections.items():
            try:
                await connection.websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to {client_id}: {e}")
                disconnected.append(client_id)

        for client_id in disconnected:
            self.disconnect(client_id)

    async def send_heartbeat(self):
        """发送心跳"""
        message = {
            "type": "heartbeat",
            "timestamp": datetime.now().isoformat(),
        }
        await self.broadcast_all(message)

    def update_heartbeat(self, client_id: str):
        """更新客户端心跳时间"""
        if client_id in self.active_connections:
            self.active_connections[client_id].last_heartbeat = datetime.now()

    def get_connection_count(self) -> int:
        """获取连接数"""
        return len(self.active_connections)

    def get_channel_stats(self) -> Dict[str, int]:
        """获取频道统计"""
        return {channel: len(subs) for channel, subs in self.channel_subscribers.items()}


# 全局连接管理器实例
manager = ConnectionManager()
