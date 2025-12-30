"""
因子相关 Schema

提供:
- 因子创建请求
- 因子响应
- IC 分析响应
"""

from datetime import date
from typing import Any

from pydantic import BaseModel, Field


class FactorCreateRequest(BaseModel):
    """
    因子创建请求

    支持公式定义或代码定义
    """
    name: str = Field(..., min_length=1, max_length=100, description="因子名称")
    description: str | None = Field(None, max_length=500, description="因子描述")

    # 公式定义
    formula: str | None = Field(
        None,
        description="因子公式 (如 'ma(close, 20) / ma(close, 60)')",
    )

    # 代码定义
    code: str | None = Field(
        None,
        description="因子计算代码 (Python)",
    )

    # 分类
    category: str = Field(
        "custom",
        description="因子分类 (momentum, value, quality, volatility, custom)",
    )

    # 参数
    params: dict[str, Any] = Field(
        default_factory=dict,
        description="因子参数",
    )


class FactorResponse(BaseModel):
    """因子响应"""
    id: str
    name: str
    description: str | None
    formula: str | None
    category: str
    created_at: str
    updated_at: str


class FactorListResponse(BaseModel):
    """因子列表响应"""
    factors: list[FactorResponse]
    total: int


class ICAnalysisRequest(BaseModel):
    """IC 分析请求"""
    factor_id: str | None = Field(None, description="因子 ID")
    formula: str | None = Field(None, description="因子公式 (临时计算)")
    symbols: list[str] = Field(..., min_length=1, description="股票列表")
    start_date: date = Field(..., description="开始日期")
    end_date: date = Field(..., description="结束日期")
    holding_period: int = Field(1, ge=1, le=60, description="持有期")


class ICAnalysisResponse(BaseModel):
    """IC 分析响应"""

    # 基础统计
    ic_mean: float = Field(..., description="IC 均值")
    ic_std: float = Field(..., description="IC 标准差")
    ic_ir: float = Field(..., description="IC 信息比率")
    rank_ic_mean: float = Field(..., description="Rank IC 均值")
    rank_ic_ir: float = Field(..., description="Rank IC 信息比率")

    # 显著性
    t_statistic: float = Field(..., description="t 统计量")
    p_value: float = Field(..., description="p 值")
    is_significant: bool = Field(..., description="是否显著 (p < 0.05)")

    # 稳定性
    ic_positive_ratio: float = Field(..., description="IC > 0 的比例")
    ic_abs_gt_2_ratio: float = Field(..., description="|IC| > 0.02 的比例")

    # 衰减
    ic_decay: list[float] = Field(default_factory=list, description="不同持有期的 IC")

    # 时间序列
    ic_series: dict[str, float] | None = Field(None, description="IC 时间序列")


class GroupBacktestRequest(BaseModel):
    """分组回测请求"""
    factor_id: str | None = Field(None, description="因子 ID")
    formula: str | None = Field(None, description="因子公式")
    symbols: list[str] = Field(..., min_length=10, description="股票列表")
    start_date: date = Field(..., description="开始日期")
    end_date: date = Field(..., description="结束日期")
    n_groups: int = Field(10, ge=2, le=20, description="分组数量")


class GroupBacktestResponse(BaseModel):
    """分组回测响应"""
    monotonicity: float = Field(..., description="单调性")
    long_short_return: float = Field(..., description="多空年化收益")
    long_short_sharpe: float = Field(..., description="多空夏普比率")
    group_stats: dict[str, dict[str, float]] = Field(..., description="各组统计")
    cumulative_returns: dict[str, float] | None = Field(None, description="累计收益")
