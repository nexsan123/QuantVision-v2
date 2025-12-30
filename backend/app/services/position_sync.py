"""
持仓同步服务

同步本地持仓与券商持仓:
- 定期同步
- 差异检测
- 自动修正
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Callable

import structlog

from app.services.alpaca_client import AlpacaClient, AlpacaPosition, get_alpaca_client

logger = structlog.get_logger()


class SyncStatus(str, Enum):
    """同步状态"""
    SYNCED = "synced"               # 已同步
    DRIFTED = "drifted"             # 有偏差
    LOCAL_ONLY = "local_only"       # 仅本地有
    REMOTE_ONLY = "remote_only"     # 仅远端有
    QUANTITY_MISMATCH = "qty_mismatch"  # 数量不匹配


@dataclass
class PositionDiff:
    """持仓差异"""
    symbol: str
    status: SyncStatus
    local_quantity: Decimal | None
    remote_quantity: Decimal | None
    quantity_diff: Decimal = Decimal("0")
    local_avg_price: Decimal | None = None
    remote_avg_price: Decimal | None = None
    price_diff: Decimal = Decimal("0")


@dataclass
class SyncResult:
    """同步结果"""
    timestamp: datetime = field(default_factory=datetime.now)
    is_synced: bool = True
    total_positions: int = 0
    synced_count: int = 0
    drifted_count: int = 0
    local_only_count: int = 0
    remote_only_count: int = 0
    diffs: list[PositionDiff] = field(default_factory=list)


@dataclass
class LocalPosition:
    """本地持仓"""
    symbol: str
    quantity: Decimal
    avg_price: Decimal
    updated_at: datetime = field(default_factory=datetime.now)


class PositionSyncService:
    """
    持仓同步服务

    保持本地持仓与券商持仓一致

    使用示例:
    ```python
    service = PositionSyncService()

    # 检查差异
    result = await service.check_sync()
    if not result.is_synced:
        print(f"发现 {len(result.diffs)} 个差异")

    # 同步到本地
    await service.sync_to_local()

    # 定期同步
    await service.start_auto_sync(interval_seconds=60)
    ```
    """

    def __init__(
        self,
        alpaca_client: AlpacaClient | None = None,
        tolerance_pct: float = 0.01,
        on_drift: Callable[[list[PositionDiff]], None] | None = None,
    ):
        """
        Args:
            alpaca_client: Alpaca 客户端
            tolerance_pct: 数量差异容忍度 (1%)
            on_drift: 发现差异时的回调
        """
        self.alpaca_client = alpaca_client or get_alpaca_client()
        self.tolerance_pct = tolerance_pct
        self.on_drift = on_drift

        # 本地持仓存储
        self._local_positions: dict[str, LocalPosition] = {}
        self._last_sync: datetime | None = None
        self._is_running = False

    async def check_sync(self) -> SyncResult:
        """
        检查同步状态

        Returns:
            同步结果
        """
        # 获取远端持仓
        remote_positions = await self.alpaca_client.get_positions()
        remote_map = {p.symbol: p for p in remote_positions}

        result = SyncResult()
        all_symbols = set(self._local_positions.keys()) | set(remote_map.keys())
        result.total_positions = len(all_symbols)

        for symbol in all_symbols:
            local = self._local_positions.get(symbol)
            remote = remote_map.get(symbol)

            diff = self._compare_position(symbol, local, remote)
            result.diffs.append(diff)

            if diff.status == SyncStatus.SYNCED:
                result.synced_count += 1
            elif diff.status == SyncStatus.LOCAL_ONLY:
                result.local_only_count += 1
            elif diff.status == SyncStatus.REMOTE_ONLY:
                result.remote_only_count += 1
            else:
                result.drifted_count += 1

        result.is_synced = result.drifted_count == 0 and result.local_only_count == 0 and result.remote_only_count == 0

        logger.info(
            "持仓同步检查完成",
            is_synced=result.is_synced,
            total=result.total_positions,
            synced=result.synced_count,
            drifted=result.drifted_count,
        )

        # 触发差异回调
        if not result.is_synced and self.on_drift:
            self.on_drift(result.diffs)

        return result

    def _compare_position(
        self,
        symbol: str,
        local: LocalPosition | None,
        remote: AlpacaPosition | None,
    ) -> PositionDiff:
        """比较单个持仓"""
        if local is None and remote is None:
            return PositionDiff(
                symbol=symbol,
                status=SyncStatus.SYNCED,
                local_quantity=None,
                remote_quantity=None,
            )

        if local is None:
            return PositionDiff(
                symbol=symbol,
                status=SyncStatus.REMOTE_ONLY,
                local_quantity=None,
                remote_quantity=remote.quantity if remote else None,
                remote_avg_price=remote.avg_entry_price if remote else None,
            )

        if remote is None:
            return PositionDiff(
                symbol=symbol,
                status=SyncStatus.LOCAL_ONLY,
                local_quantity=local.quantity,
                remote_quantity=None,
                local_avg_price=local.avg_price,
            )

        # 两边都有，比较数量
        qty_diff = abs(local.quantity - remote.quantity)
        tolerance = max(abs(local.quantity), abs(remote.quantity)) * Decimal(str(self.tolerance_pct))

        if qty_diff <= tolerance:
            status = SyncStatus.SYNCED
        else:
            status = SyncStatus.QUANTITY_MISMATCH

        return PositionDiff(
            symbol=symbol,
            status=status,
            local_quantity=local.quantity,
            remote_quantity=remote.quantity,
            quantity_diff=local.quantity - remote.quantity,
            local_avg_price=local.avg_price,
            remote_avg_price=remote.avg_entry_price,
            price_diff=local.avg_price - remote.avg_entry_price,
        )

    async def sync_to_local(self) -> SyncResult:
        """
        将远端持仓同步到本地

        Returns:
            同步结果
        """
        remote_positions = await self.alpaca_client.get_positions()

        # 更新本地持仓
        self._local_positions.clear()
        for pos in remote_positions:
            self._local_positions[pos.symbol] = LocalPosition(
                symbol=pos.symbol,
                quantity=pos.quantity,
                avg_price=pos.avg_entry_price,
                updated_at=datetime.now(),
            )

        self._last_sync = datetime.now()

        logger.info(
            "持仓已同步到本地",
            n_positions=len(self._local_positions),
        )

        return await self.check_sync()

    async def sync_to_remote(self, diffs: list[PositionDiff] | None = None) -> list[dict[str, Any]]:
        """
        将本地持仓同步到远端 (通过下单)

        Args:
            diffs: 要同步的差异列表 (默认同步所有)

        Returns:
            同步操作结果
        """
        if diffs is None:
            result = await self.check_sync()
            diffs = [d for d in result.diffs if d.status != SyncStatus.SYNCED]

        results = []

        for diff in diffs:
            try:
                if diff.status == SyncStatus.LOCAL_ONLY:
                    # 本地有远端没有，需要买入
                    if diff.local_quantity and diff.local_quantity > 0:
                        order = await self.alpaca_client.submit_order(
                            symbol=diff.symbol,
                            qty=float(diff.local_quantity),
                            side="buy",
                        )
                        results.append({
                            "symbol": diff.symbol,
                            "action": "buy",
                            "quantity": float(diff.local_quantity),
                            "order_id": order.id,
                            "status": "submitted",
                        })

                elif diff.status == SyncStatus.REMOTE_ONLY:
                    # 远端有本地没有，需要平仓
                    order = await self.alpaca_client.close_position(diff.symbol)
                    results.append({
                        "symbol": diff.symbol,
                        "action": "close",
                        "quantity": float(diff.remote_quantity) if diff.remote_quantity else 0,
                        "order_id": order.id,
                        "status": "submitted",
                    })

                elif diff.status == SyncStatus.QUANTITY_MISMATCH:
                    # 数量不匹配，调整持仓
                    if diff.quantity_diff and diff.quantity_diff > 0:
                        # 本地多，需要卖出
                        order = await self.alpaca_client.submit_order(
                            symbol=diff.symbol,
                            qty=float(diff.quantity_diff),
                            side="sell",
                        )
                        results.append({
                            "symbol": diff.symbol,
                            "action": "sell",
                            "quantity": float(diff.quantity_diff),
                            "order_id": order.id,
                            "status": "submitted",
                        })
                    elif diff.quantity_diff and diff.quantity_diff < 0:
                        # 本地少，需要买入
                        order = await self.alpaca_client.submit_order(
                            symbol=diff.symbol,
                            qty=float(abs(diff.quantity_diff)),
                            side="buy",
                        )
                        results.append({
                            "symbol": diff.symbol,
                            "action": "buy",
                            "quantity": float(abs(diff.quantity_diff)),
                            "order_id": order.id,
                            "status": "submitted",
                        })

            except Exception as e:
                logger.error(
                    "同步持仓失败",
                    symbol=diff.symbol,
                    error=str(e),
                )
                results.append({
                    "symbol": diff.symbol,
                    "action": "error",
                    "error": str(e),
                    "status": "failed",
                })

        return results

    def update_local_position(
        self,
        symbol: str,
        quantity: Decimal,
        avg_price: Decimal,
    ) -> None:
        """
        更新本地持仓

        Args:
            symbol: 股票代码
            quantity: 数量
            avg_price: 均价
        """
        if quantity == 0:
            self._local_positions.pop(symbol, None)
        else:
            self._local_positions[symbol] = LocalPosition(
                symbol=symbol,
                quantity=quantity,
                avg_price=avg_price,
                updated_at=datetime.now(),
            )

    def get_local_positions(self) -> dict[str, LocalPosition]:
        """获取本地持仓"""
        return self._local_positions.copy()

    async def start_auto_sync(
        self,
        interval_seconds: float = 60,
        sync_to_local: bool = True,
    ) -> None:
        """
        启动自动同步

        Args:
            interval_seconds: 同步间隔
            sync_to_local: 是否同步到本地 (否则仅检查)
        """
        self._is_running = True

        logger.info(
            "持仓自动同步已启动",
            interval_seconds=interval_seconds,
        )

        while self._is_running:
            try:
                if sync_to_local:
                    await self.sync_to_local()
                else:
                    await self.check_sync()

            except Exception as e:
                logger.error("自动同步失败", error=str(e))

            await asyncio.sleep(interval_seconds)

    def stop_auto_sync(self) -> None:
        """停止自动同步"""
        self._is_running = False
        logger.info("持仓自动同步已停止")

    def get_status(self) -> dict[str, Any]:
        """获取服务状态"""
        return {
            "is_running": self._is_running,
            "last_sync": self._last_sync.isoformat() if self._last_sync else None,
            "local_positions_count": len(self._local_positions),
            "positions": {
                symbol: {
                    "quantity": float(pos.quantity),
                    "avg_price": float(pos.avg_price),
                    "updated_at": pos.updated_at.isoformat(),
                }
                for symbol, pos in self._local_positions.items()
            },
        }


# 单例服务
_position_sync_service: PositionSyncService | None = None


def get_position_sync_service() -> PositionSyncService:
    """获取持仓同步服务单例"""
    global _position_sync_service
    if _position_sync_service is None:
        _position_sync_service = PositionSyncService()
    return _position_sync_service
