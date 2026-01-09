"""
策略冲突检测服务
PRD 4.6 策略冲突检测
"""

from datetime import datetime, timedelta
from typing import Optional
import uuid
import random

from app.schemas.conflict import (
    ConflictType,
    ConflictSeverity,
    ConflictStatus,
    ResolutionAction,
    ConflictingSignal,
    ConflictDetail,
    ConflictCheckResult,
)


class ConflictService:
    """策略冲突检测服务"""

    # 模拟数据存储
    _conflicts: dict[str, ConflictDetail] = {}
    _strategy_conflicts: dict[str, list[str]] = {}  # strategy_id -> [conflict_ids]

    def __init__(self):
        """初始化服务"""
        self._init_mock_data()

    def _init_mock_data(self):
        """初始化模拟冲突数据"""
        # 创建一些示例冲突
        symbols = ["AAPL", "MSFT", "GOOGL", "NVDA", "TSLA"]
        strategies = [
            ("strategy-001", "动量突破策略"),
            ("strategy-002", "均值回归策略"),
            ("strategy-003", "因子选股策略"),
        ]

        # 逻辑冲突示例: 同一股票相反信号
        conflict1 = ConflictDetail(
            conflict_id=str(uuid.uuid4()),
            conflict_type=ConflictType.LOGIC,
            severity=ConflictSeverity.CRITICAL,
            status=ConflictStatus.PENDING,
            signal_a=ConflictingSignal(
                strategy_id="strategy-001",
                strategy_name="动量突破策略",
                signal_id=str(uuid.uuid4()),
                symbol="AAPL",
                direction="buy",
                quantity=100,
                price=185.50,
                signal_time=datetime.now() - timedelta(minutes=5),
                signal_strength=0.85,
                expected_return=0.08,
                confidence=0.78,
            ),
            signal_b=ConflictingSignal(
                strategy_id="strategy-002",
                strategy_name="均值回归策略",
                signal_id=str(uuid.uuid4()),
                symbol="AAPL",
                direction="sell",
                quantity=80,
                price=186.00,
                signal_time=datetime.now() - timedelta(minutes=3),
                signal_strength=0.72,
                expected_return=0.05,
                confidence=0.65,
            ),
            description="AAPL 存在相反的交易信号",
            reason="动量策略看涨，均值回归策略看跌，形成逻辑冲突",
            impact="同时执行将形成对冲，可能导致交易成本浪费",
            suggested_resolution=ResolutionAction.EXECUTE_STRATEGY_A,
            resolution_reason="动量策略信号强度更高(0.85 vs 0.72)，且预期收益更好",
            alternative_resolutions=[
                ResolutionAction.EXECUTE_STRATEGY_B,
                ResolutionAction.CANCEL_BOTH,
            ],
            detected_at=datetime.now(),
            expires_at=datetime.now() + timedelta(hours=1),
        )
        self._conflicts[conflict1.conflict_id] = conflict1
        self._strategy_conflicts.setdefault("strategy-001", []).append(conflict1.conflict_id)
        self._strategy_conflicts.setdefault("strategy-002", []).append(conflict1.conflict_id)

        # 执行冲突示例: 资金不足
        conflict2 = ConflictDetail(
            conflict_id=str(uuid.uuid4()),
            conflict_type=ConflictType.EXECUTION,
            severity=ConflictSeverity.WARNING,
            status=ConflictStatus.PENDING,
            signal_a=ConflictingSignal(
                strategy_id="strategy-003",
                strategy_name="因子选股策略",
                signal_id=str(uuid.uuid4()),
                symbol="NVDA",
                direction="buy",
                quantity=50,
                price=875.00,
                signal_time=datetime.now() - timedelta(minutes=10),
                signal_strength=0.92,
                expected_return=0.12,
                confidence=0.88,
            ),
            signal_b=None,
            description="NVDA 买入信号资金不足",
            reason="信号需要 $43,750，但可用资金仅 $35,000",
            impact="无法完整执行买入信号，可能错过投资机会",
            suggested_resolution=ResolutionAction.REDUCE_POSITION,
            resolution_reason="建议减少买入数量至40股，确保在资金范围内执行",
            alternative_resolutions=[
                ResolutionAction.DELAY_EXECUTION,
                ResolutionAction.IGNORE,
            ],
            detected_at=datetime.now(),
            expires_at=datetime.now() + timedelta(hours=2),
        )
        self._conflicts[conflict2.conflict_id] = conflict2
        self._strategy_conflicts.setdefault("strategy-003", []).append(conflict2.conflict_id)

        # 重复冲突示例
        conflict3 = ConflictDetail(
            conflict_id=str(uuid.uuid4()),
            conflict_type=ConflictType.DUPLICATE,
            severity=ConflictSeverity.INFO,
            status=ConflictStatus.PENDING,
            signal_a=ConflictingSignal(
                strategy_id="strategy-001",
                strategy_name="动量突破策略",
                signal_id=str(uuid.uuid4()),
                symbol="MSFT",
                direction="buy",
                quantity=60,
                price=425.00,
                signal_time=datetime.now() - timedelta(minutes=8),
                signal_strength=0.78,
                expected_return=0.06,
                confidence=0.72,
            ),
            signal_b=ConflictingSignal(
                strategy_id="strategy-003",
                strategy_name="因子选股策略",
                signal_id=str(uuid.uuid4()),
                symbol="MSFT",
                direction="buy",
                quantity=45,
                price=424.50,
                signal_time=datetime.now() - timedelta(minutes=6),
                signal_strength=0.82,
                expected_return=0.07,
                confidence=0.75,
            ),
            description="MSFT 存在重复买入信号",
            reason="两个策略同时发出买入信号，可能导致过度集中",
            impact="同时执行将增加单股仓位占比，集中度风险上升",
            suggested_resolution=ResolutionAction.EXECUTE_STRATEGY_B,
            resolution_reason="因子选股策略信号质量更高，建议执行该策略",
            alternative_resolutions=[
                ResolutionAction.EXECUTE_BOTH,
                ResolutionAction.EXECUTE_STRATEGY_A,
            ],
            detected_at=datetime.now(),
            expires_at=datetime.now() + timedelta(hours=1),
        )
        self._conflicts[conflict3.conflict_id] = conflict3
        self._strategy_conflicts.setdefault("strategy-001", []).append(conflict3.conflict_id)
        self._strategy_conflicts.setdefault("strategy-003", []).append(conflict3.conflict_id)

    async def check_conflicts(
        self,
        strategy_ids: list[str],
        symbol: Optional[str] = None,
        check_execution: bool = True,
        check_timeout: bool = True,
    ) -> ConflictCheckResult:
        """检测策略冲突"""
        conflicts = []

        # 收集相关冲突
        seen_ids = set()
        for sid in strategy_ids:
            conflict_ids = self._strategy_conflicts.get(sid, [])
            for cid in conflict_ids:
                if cid not in seen_ids and cid in self._conflicts:
                    conflict = self._conflicts[cid]
                    # 过滤符号
                    if symbol and conflict.signal_a.symbol != symbol:
                        if not conflict.signal_b or conflict.signal_b.symbol != symbol:
                            continue
                    # 过滤类型
                    if not check_execution and conflict.conflict_type == ConflictType.EXECUTION:
                        continue
                    if not check_timeout and conflict.conflict_type == ConflictType.TIMEOUT:
                        continue
                    conflicts.append(conflict)
                    seen_ids.add(cid)

        # 统计
        critical_count = sum(1 for c in conflicts if c.severity == ConflictSeverity.CRITICAL)
        warning_count = sum(1 for c in conflicts if c.severity == ConflictSeverity.WARNING)
        info_count = sum(1 for c in conflicts if c.severity == ConflictSeverity.INFO)

        return ConflictCheckResult(
            total_conflicts=len(conflicts),
            critical_count=critical_count,
            warning_count=warning_count,
            info_count=info_count,
            conflicts=sorted(conflicts, key=lambda c: (
                0 if c.severity == ConflictSeverity.CRITICAL else
                1 if c.severity == ConflictSeverity.WARNING else 2
            )),
            checked_at=datetime.now(),
        )

    async def get_conflict_by_id(self, conflict_id: str) -> Optional[ConflictDetail]:
        """获取冲突详情"""
        return self._conflicts.get(conflict_id)

    async def get_pending_conflicts(
        self,
        strategy_id: Optional[str] = None,
        limit: int = 50,
    ) -> list[ConflictDetail]:
        """获取待处理冲突"""
        if strategy_id:
            conflict_ids = self._strategy_conflicts.get(strategy_id, [])
            conflicts = [
                self._conflicts[cid]
                for cid in conflict_ids
                if cid in self._conflicts and self._conflicts[cid].status == ConflictStatus.PENDING
            ]
        else:
            conflicts = [
                c for c in self._conflicts.values()
                if c.status == ConflictStatus.PENDING
            ]

        # 按严重程度排序
        conflicts.sort(key=lambda c: (
            0 if c.severity == ConflictSeverity.CRITICAL else
            1 if c.severity == ConflictSeverity.WARNING else 2
        ))

        return conflicts[:limit]

    async def resolve_conflict(
        self,
        conflict_id: str,
        resolution: ResolutionAction,
        reason: Optional[str] = None,
        resolved_by: str = "user",
    ) -> Optional[ConflictDetail]:
        """解决冲突"""
        conflict = self._conflicts.get(conflict_id)
        if not conflict:
            return None

        # 更新冲突状态
        conflict.status = ConflictStatus.RESOLVED if resolved_by == "user" else ConflictStatus.AUTO_RESOLVED
        conflict.resolution = resolution
        conflict.resolved_at = datetime.now()
        conflict.resolved_by = resolved_by
        if reason:
            conflict.resolution_reason = reason

        return conflict

    async def ignore_conflict(self, conflict_id: str) -> Optional[ConflictDetail]:
        """忽略冲突"""
        conflict = self._conflicts.get(conflict_id)
        if not conflict:
            return None

        conflict.status = ConflictStatus.IGNORED
        conflict.resolution = ResolutionAction.IGNORE
        conflict.resolved_at = datetime.now()
        conflict.resolved_by = "user"

        return conflict

    async def get_conflict_count(
        self,
        strategy_id: Optional[str] = None,
        status: Optional[ConflictStatus] = None,
    ) -> int:
        """获取冲突数量"""
        if strategy_id:
            conflict_ids = self._strategy_conflicts.get(strategy_id, [])
            conflicts = [self._conflicts[cid] for cid in conflict_ids if cid in self._conflicts]
        else:
            conflicts = list(self._conflicts.values())

        if status:
            conflicts = [c for c in conflicts if c.status == status]

        return len(conflicts)

    async def create_conflict(
        self,
        conflict_type: ConflictType,
        signal_a: ConflictingSignal,
        signal_b: Optional[ConflictingSignal] = None,
        description: str = "",
        reason: str = "",
        impact: str = "",
    ) -> ConflictDetail:
        """创建新冲突(用于实时检测)"""
        # 确定严重程度
        from app.schemas.conflict import CONFLICT_TYPE_CONFIG
        severity = CONFLICT_TYPE_CONFIG[conflict_type]["default_severity"]

        # 生成建议解决方案
        suggested_resolution, resolution_reason = self._suggest_resolution(
            conflict_type, signal_a, signal_b
        )

        conflict = ConflictDetail(
            conflict_id=str(uuid.uuid4()),
            conflict_type=conflict_type,
            severity=severity,
            status=ConflictStatus.PENDING,
            signal_a=signal_a,
            signal_b=signal_b,
            description=description,
            reason=reason,
            impact=impact,
            suggested_resolution=suggested_resolution,
            resolution_reason=resolution_reason,
            alternative_resolutions=self._get_alternative_resolutions(conflict_type),
            detected_at=datetime.now(),
            expires_at=datetime.now() + timedelta(hours=1),
        )

        # 存储
        self._conflicts[conflict.conflict_id] = conflict
        self._strategy_conflicts.setdefault(signal_a.strategy_id, []).append(conflict.conflict_id)
        if signal_b:
            self._strategy_conflicts.setdefault(signal_b.strategy_id, []).append(conflict.conflict_id)

        return conflict

    def _suggest_resolution(
        self,
        conflict_type: ConflictType,
        signal_a: ConflictingSignal,
        signal_b: Optional[ConflictingSignal],
    ) -> tuple[ResolutionAction, str]:
        """生成建议解决方案"""
        if conflict_type == ConflictType.LOGIC:
            if signal_b:
                # 比较信号强度
                if signal_a.signal_strength > signal_b.signal_strength:
                    return (
                        ResolutionAction.EXECUTE_STRATEGY_A,
                        f"策略A信号强度更高 ({signal_a.signal_strength:.2f} vs {signal_b.signal_strength:.2f})"
                    )
                else:
                    return (
                        ResolutionAction.EXECUTE_STRATEGY_B,
                        f"策略B信号强度更高 ({signal_b.signal_strength:.2f} vs {signal_a.signal_strength:.2f})"
                    )
            return (ResolutionAction.EXECUTE_STRATEGY_A, "仅有一个信号，建议执行")

        elif conflict_type == ConflictType.EXECUTION:
            return (
                ResolutionAction.REDUCE_POSITION,
                "建议减少仓位以满足执行条件"
            )

        elif conflict_type == ConflictType.TIMEOUT:
            return (
                ResolutionAction.CANCEL_BOTH,
                "信号已过期，建议取消"
            )

        elif conflict_type == ConflictType.DUPLICATE:
            if signal_b:
                if signal_a.confidence > signal_b.confidence:
                    return (
                        ResolutionAction.EXECUTE_STRATEGY_A,
                        f"策略A置信度更高 ({signal_a.confidence:.2f} vs {signal_b.confidence:.2f})"
                    )
                else:
                    return (
                        ResolutionAction.EXECUTE_STRATEGY_B,
                        f"策略B置信度更高 ({signal_b.confidence:.2f} vs {signal_a.confidence:.2f})"
                    )
            return (ResolutionAction.EXECUTE_STRATEGY_A, "仅有一个信号，建议执行")

        return (ResolutionAction.IGNORE, "无特定建议")

    def _get_alternative_resolutions(
        self, conflict_type: ConflictType
    ) -> list[ResolutionAction]:
        """获取可选解决方案"""
        if conflict_type == ConflictType.LOGIC:
            return [
                ResolutionAction.EXECUTE_STRATEGY_A,
                ResolutionAction.EXECUTE_STRATEGY_B,
                ResolutionAction.CANCEL_BOTH,
            ]
        elif conflict_type == ConflictType.EXECUTION:
            return [
                ResolutionAction.REDUCE_POSITION,
                ResolutionAction.DELAY_EXECUTION,
                ResolutionAction.IGNORE,
            ]
        elif conflict_type == ConflictType.TIMEOUT:
            return [
                ResolutionAction.CANCEL_BOTH,
                ResolutionAction.IGNORE,
            ]
        elif conflict_type == ConflictType.DUPLICATE:
            return [
                ResolutionAction.EXECUTE_STRATEGY_A,
                ResolutionAction.EXECUTE_STRATEGY_B,
                ResolutionAction.EXECUTE_BOTH,
            ]
        return [ResolutionAction.IGNORE]


# 单例服务实例
conflict_service = ConflictService()
