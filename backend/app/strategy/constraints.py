"""
组合约束处理

提供:
- 仓位约束 (单资产、行业、总仓位)
- 换手率约束
- 流动性约束
- 风险约束
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import pandas as pd
import structlog

logger = structlog.get_logger()


class ConstraintType(str, Enum):
    """约束类型"""
    POSITION_WEIGHT = "position_weight"     # 单资产权重
    SECTOR_WEIGHT = "sector_weight"         # 行业权重
    TOTAL_EXPOSURE = "total_exposure"       # 总敞口
    TURNOVER = "turnover"                   # 换手率
    LIQUIDITY = "liquidity"                 # 流动性
    BETA = "beta"                           # Beta 值
    VOLATILITY = "volatility"               # 波动率
    TRACKING_ERROR = "tracking_error"       # 跟踪误差
    FACTOR_EXPOSURE = "factor_exposure"     # 因子敞口


@dataclass
class Constraint:
    """单个约束定义"""
    type: ConstraintType
    min_value: float | None = None
    max_value: float | None = None
    target_value: float | None = None
    assets: list[str] | None = None         # 适用的资产
    sector: str | None = None               # 适用的行业
    factor: str | None = None               # 适用的因子
    penalty: float = 1.0                    # 违反惩罚系数
    description: str = ""


@dataclass
class ConstraintViolation:
    """约束违反记录"""
    constraint: Constraint
    current_value: float
    violation_amount: float
    severity: str  # "warning", "error", "critical"
    message: str


@dataclass
class PortfolioConstraints:
    """
    组合约束集合

    管理多个约束条件
    """
    constraints: list[Constraint] = field(default_factory=list)

    # === 快捷属性 ===
    max_position_weight: float = 0.10       # 单资产最大权重 10%
    min_position_weight: float = 0.00       # 单资产最小权重
    max_sector_weight: float = 0.30         # 单行业最大权重 30%
    max_holdings: int = 100                 # 最大持仓数量
    min_holdings: int = 10                  # 最小持仓数量
    max_turnover: float = 1.0               # 最大换手率 (单次)
    long_only: bool = True                  # 是否只做多
    max_leverage: float = 1.0               # 最大杠杆

    def add_constraint(self, constraint: Constraint) -> "PortfolioConstraints":
        """添加约束"""
        self.constraints.append(constraint)
        return self

    def add_position_constraint(
        self,
        min_weight: float | None = None,
        max_weight: float | None = None,
        assets: list[str] | None = None,
    ) -> "PortfolioConstraints":
        """添加仓位约束"""
        self.constraints.append(
            Constraint(
                type=ConstraintType.POSITION_WEIGHT,
                min_value=min_weight,
                max_value=max_weight,
                assets=assets,
                description=f"仓位约束: {min_weight} - {max_weight}",
            )
        )
        return self

    def add_sector_constraint(
        self,
        sector: str,
        max_weight: float,
    ) -> "PortfolioConstraints":
        """添加行业约束"""
        self.constraints.append(
            Constraint(
                type=ConstraintType.SECTOR_WEIGHT,
                max_value=max_weight,
                sector=sector,
                description=f"行业约束: {sector} <= {max_weight:.0%}",
            )
        )
        return self

    def add_turnover_constraint(
        self,
        max_turnover: float,
    ) -> "PortfolioConstraints":
        """添加换手率约束"""
        self.constraints.append(
            Constraint(
                type=ConstraintType.TURNOVER,
                max_value=max_turnover,
                description=f"换手率约束: <= {max_turnover:.0%}",
            )
        )
        self.max_turnover = max_turnover
        return self

    def add_beta_constraint(
        self,
        min_beta: float | None = None,
        max_beta: float | None = None,
    ) -> "PortfolioConstraints":
        """添加 Beta 约束"""
        self.constraints.append(
            Constraint(
                type=ConstraintType.BETA,
                min_value=min_beta,
                max_value=max_beta,
                description=f"Beta 约束: {min_beta} - {max_beta}",
            )
        )
        return self

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "max_position_weight": self.max_position_weight,
            "min_position_weight": self.min_position_weight,
            "max_sector_weight": self.max_sector_weight,
            "max_holdings": self.max_holdings,
            "min_holdings": self.min_holdings,
            "max_turnover": self.max_turnover,
            "long_only": self.long_only,
            "max_leverage": self.max_leverage,
            "constraints_count": len(self.constraints),
        }


class ConstraintChecker:
    """
    约束检查器

    验证组合是否满足所有约束条件
    """

    def __init__(self, constraints: PortfolioConstraints):
        """
        Args:
            constraints: 约束集合
        """
        self.constraints = constraints

    def check_all(
        self,
        weights: dict[str, float],
        current_weights: dict[str, float] | None = None,
        sector_map: dict[str, str] | None = None,
        betas: dict[str, float] | None = None,
        volumes: dict[str, float] | None = None,
    ) -> list[ConstraintViolation]:
        """
        检查所有约束

        Args:
            weights: 目标权重
            current_weights: 当前权重 (用于计算换手率)
            sector_map: 资产-行业映射
            betas: 资产 Beta 值
            volumes: 资产成交量

        Returns:
            约束违反列表
        """
        violations = []

        # 检查基本约束
        violations.extend(self._check_position_weights(weights))
        violations.extend(self._check_holdings_count(weights))

        # 检查行业约束
        if sector_map:
            violations.extend(self._check_sector_weights(weights, sector_map))

        # 检查换手率
        if current_weights:
            violations.extend(self._check_turnover(weights, current_weights))

        # 检查 Beta
        if betas:
            violations.extend(self._check_beta(weights, betas))

        # 检查杠杆
        violations.extend(self._check_leverage(weights))

        # 检查自定义约束
        for constraint in self.constraints.constraints:
            v = self._check_custom_constraint(constraint, weights, sector_map, betas)
            if v:
                violations.append(v)

        return violations

    def _check_position_weights(
        self,
        weights: dict[str, float],
    ) -> list[ConstraintViolation]:
        """检查单资产权重"""
        violations = []
        max_w = self.constraints.max_position_weight
        min_w = self.constraints.min_position_weight
        long_only = self.constraints.long_only

        for asset, w in weights.items():
            # 检查做空约束
            if long_only and w < 0:
                violations.append(
                    ConstraintViolation(
                        constraint=Constraint(
                            type=ConstraintType.POSITION_WEIGHT,
                            min_value=0.0,
                        ),
                        current_value=w,
                        violation_amount=abs(w),
                        severity="error",
                        message=f"{asset}: 禁止做空，当前权重 {w:.2%}",
                    )
                )

            # 检查最大权重
            if w > max_w:
                violations.append(
                    ConstraintViolation(
                        constraint=Constraint(
                            type=ConstraintType.POSITION_WEIGHT,
                            max_value=max_w,
                        ),
                        current_value=w,
                        violation_amount=w - max_w,
                        severity="warning",
                        message=f"{asset}: 权重 {w:.2%} 超过上限 {max_w:.2%}",
                    )
                )

            # 检查最小权重 (非零仓位)
            if 0 < w < min_w:
                violations.append(
                    ConstraintViolation(
                        constraint=Constraint(
                            type=ConstraintType.POSITION_WEIGHT,
                            min_value=min_w,
                        ),
                        current_value=w,
                        violation_amount=min_w - w,
                        severity="warning",
                        message=f"{asset}: 权重 {w:.2%} 低于下限 {min_w:.2%}",
                    )
                )

        return violations

    def _check_holdings_count(
        self,
        weights: dict[str, float],
    ) -> list[ConstraintViolation]:
        """检查持仓数量"""
        violations = []
        non_zero = sum(1 for w in weights.values() if abs(w) > 1e-6)

        if non_zero > self.constraints.max_holdings:
            violations.append(
                ConstraintViolation(
                    constraint=Constraint(
                        type=ConstraintType.POSITION_WEIGHT,
                        max_value=float(self.constraints.max_holdings),
                    ),
                    current_value=float(non_zero),
                    violation_amount=float(non_zero - self.constraints.max_holdings),
                    severity="warning",
                    message=f"持仓数量 {non_zero} 超过上限 {self.constraints.max_holdings}",
                )
            )

        if non_zero < self.constraints.min_holdings and non_zero > 0:
            violations.append(
                ConstraintViolation(
                    constraint=Constraint(
                        type=ConstraintType.POSITION_WEIGHT,
                        min_value=float(self.constraints.min_holdings),
                    ),
                    current_value=float(non_zero),
                    violation_amount=float(self.constraints.min_holdings - non_zero),
                    severity="warning",
                    message=f"持仓数量 {non_zero} 低于下限 {self.constraints.min_holdings}",
                )
            )

        return violations

    def _check_sector_weights(
        self,
        weights: dict[str, float],
        sector_map: dict[str, str],
    ) -> list[ConstraintViolation]:
        """检查行业权重"""
        violations = []
        max_sector = self.constraints.max_sector_weight

        # 计算各行业权重
        sector_weights: dict[str, float] = {}
        for asset, w in weights.items():
            sector = sector_map.get(asset, "Unknown")
            sector_weights[sector] = sector_weights.get(sector, 0.0) + w

        # 检查
        for sector, w in sector_weights.items():
            if w > max_sector:
                violations.append(
                    ConstraintViolation(
                        constraint=Constraint(
                            type=ConstraintType.SECTOR_WEIGHT,
                            max_value=max_sector,
                            sector=sector,
                        ),
                        current_value=w,
                        violation_amount=w - max_sector,
                        severity="warning",
                        message=f"行业 {sector}: 权重 {w:.2%} 超过上限 {max_sector:.2%}",
                    )
                )

        return violations

    def _check_turnover(
        self,
        weights: dict[str, float],
        current_weights: dict[str, float],
    ) -> list[ConstraintViolation]:
        """检查换手率"""
        violations = []
        max_turnover = self.constraints.max_turnover

        # 计算换手率 (单边)
        all_assets = set(weights.keys()) | set(current_weights.keys())
        turnover = 0.0
        for asset in all_assets:
            new_w = weights.get(asset, 0.0)
            old_w = current_weights.get(asset, 0.0)
            turnover += abs(new_w - old_w)
        turnover /= 2  # 单边

        if turnover > max_turnover:
            violations.append(
                ConstraintViolation(
                    constraint=Constraint(
                        type=ConstraintType.TURNOVER,
                        max_value=max_turnover,
                    ),
                    current_value=turnover,
                    violation_amount=turnover - max_turnover,
                    severity="warning",
                    message=f"换手率 {turnover:.2%} 超过上限 {max_turnover:.2%}",
                )
            )

        return violations

    def _check_beta(
        self,
        weights: dict[str, float],
        betas: dict[str, float],
    ) -> list[ConstraintViolation]:
        """检查组合 Beta"""
        violations = []

        # 计算组合 Beta
        port_beta = sum(w * betas.get(a, 1.0) for a, w in weights.items())

        # 检查自定义 Beta 约束
        for constraint in self.constraints.constraints:
            if constraint.type != ConstraintType.BETA:
                continue

            if constraint.min_value is not None and port_beta < constraint.min_value:
                violations.append(
                    ConstraintViolation(
                        constraint=constraint,
                        current_value=port_beta,
                        violation_amount=constraint.min_value - port_beta,
                        severity="warning",
                        message=f"组合 Beta {port_beta:.2f} 低于下限 {constraint.min_value}",
                    )
                )

            if constraint.max_value is not None and port_beta > constraint.max_value:
                violations.append(
                    ConstraintViolation(
                        constraint=constraint,
                        current_value=port_beta,
                        violation_amount=port_beta - constraint.max_value,
                        severity="warning",
                        message=f"组合 Beta {port_beta:.2f} 超过上限 {constraint.max_value}",
                    )
                )

        return violations

    def _check_leverage(
        self,
        weights: dict[str, float],
    ) -> list[ConstraintViolation]:
        """检查杠杆"""
        violations = []
        max_leverage = self.constraints.max_leverage

        # 总敞口 = abs(多头) + abs(空头)
        long_exposure = sum(w for w in weights.values() if w > 0)
        short_exposure = abs(sum(w for w in weights.values() if w < 0))
        gross_exposure = long_exposure + short_exposure

        if gross_exposure > max_leverage:
            violations.append(
                ConstraintViolation(
                    constraint=Constraint(
                        type=ConstraintType.TOTAL_EXPOSURE,
                        max_value=max_leverage,
                    ),
                    current_value=gross_exposure,
                    violation_amount=gross_exposure - max_leverage,
                    severity="error",
                    message=f"总敞口 {gross_exposure:.2f}x 超过杠杆上限 {max_leverage}x",
                )
            )

        return violations

    def _check_custom_constraint(
        self,
        constraint: Constraint,
        weights: dict[str, float],
        sector_map: dict[str, str] | None,
        betas: dict[str, float] | None,
    ) -> ConstraintViolation | None:
        """检查自定义约束"""
        # 已在其他方法中处理的类型跳过
        if constraint.type in [
            ConstraintType.BETA,
            ConstraintType.TURNOVER,
        ]:
            return None

        # 处理特定资产的仓位约束
        if constraint.type == ConstraintType.POSITION_WEIGHT and constraint.assets:
            for asset in constraint.assets:
                w = weights.get(asset, 0.0)
                if constraint.max_value is not None and w > constraint.max_value:
                    return ConstraintViolation(
                        constraint=constraint,
                        current_value=w,
                        violation_amount=w - constraint.max_value,
                        severity="warning",
                        message=f"{asset}: 权重 {w:.2%} 超过约束上限 {constraint.max_value:.2%}",
                    )

        return None

    def is_feasible(
        self,
        weights: dict[str, float],
        **kwargs: Any,
    ) -> bool:
        """
        检查组合是否可行

        Returns:
            True 如果没有错误级别的违反
        """
        violations = self.check_all(weights, **kwargs)
        errors = [v for v in violations if v.severity in ["error", "critical"]]
        return len(errors) == 0


def apply_constraints(
    weights: pd.Series,
    constraints: PortfolioConstraints,
) -> pd.Series:
    """
    应用约束到权重

    简单的约束投影:
    - 裁剪超限权重
    - 重新归一化

    Args:
        weights: 原始权重
        constraints: 约束条件

    Returns:
        调整后的权重
    """
    adjusted = weights.copy()

    # 裁剪单资产权重
    if constraints.long_only:
        adjusted = adjusted.clip(lower=0.0)

    adjusted = adjusted.clip(
        lower=constraints.min_position_weight,
        upper=constraints.max_position_weight,
    )

    # 限制持仓数量
    if len(adjusted[adjusted > 0]) > constraints.max_holdings:
        # 保留权重最大的 N 个
        sorted_weights = adjusted.sort_values(ascending=False)
        top_n = sorted_weights.head(constraints.max_holdings).index
        adjusted.loc[~adjusted.index.isin(top_n)] = 0.0

    # 重新归一化
    total = adjusted.sum()
    if total > 0:
        adjusted = adjusted / total

    return adjusted
