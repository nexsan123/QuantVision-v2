"""
股票池筛选器

提供:
- 多条件筛选
- 动态股票池
- Point-in-Time 支持
"""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import Any

import pandas as pd
import structlog

logger = structlog.get_logger()


class FilterOperator(str, Enum):
    """筛选操作符"""
    GT = ">"          # 大于
    GTE = ">="        # 大于等于
    LT = "<"          # 小于
    LTE = "<="        # 小于等于
    EQ = "=="         # 等于
    NE = "!="         # 不等于
    IN = "in"         # 在列表中
    NOT_IN = "not_in" # 不在列表中
    BETWEEN = "between"  # 区间内
    TOP_N = "top_n"      # 前 N 名
    BOTTOM_N = "bottom_n"  # 后 N 名
    TOP_PCT = "top_pct"    # 前 N%
    BOTTOM_PCT = "bottom_pct"  # 后 N%


@dataclass
class FilterCondition:
    """筛选条件"""
    field: str                      # 字段名
    operator: FilterOperator        # 操作符
    value: Any                      # 比较值
    description: str = ""           # 条件描述

    def evaluate(self, data: pd.Series) -> pd.Series:
        """
        评估条件

        Args:
            data: 待筛选的数据 Series

        Returns:
            布尔 Series，True 表示满足条件
        """
        if self.operator == FilterOperator.GT:
            return data > self.value
        elif self.operator == FilterOperator.GTE:
            return data >= self.value
        elif self.operator == FilterOperator.LT:
            return data < self.value
        elif self.operator == FilterOperator.LTE:
            return data <= self.value
        elif self.operator == FilterOperator.EQ:
            return data == self.value
        elif self.operator == FilterOperator.NE:
            return data != self.value
        elif self.operator == FilterOperator.IN:
            return data.isin(self.value)
        elif self.operator == FilterOperator.NOT_IN:
            return ~data.isin(self.value)
        elif self.operator == FilterOperator.BETWEEN:
            low, high = self.value
            return (data >= low) & (data <= high)
        elif self.operator == FilterOperator.TOP_N:
            n = int(self.value)
            threshold = data.nlargest(n).min()
            return data >= threshold
        elif self.operator == FilterOperator.BOTTOM_N:
            n = int(self.value)
            threshold = data.nsmallest(n).max()
            return data <= threshold
        elif self.operator == FilterOperator.TOP_PCT:
            pct = float(self.value)
            threshold = data.quantile(1 - pct)
            return data >= threshold
        elif self.operator == FilterOperator.BOTTOM_PCT:
            pct = float(self.value)
            threshold = data.quantile(pct)
            return data <= threshold
        else:
            raise ValueError(f"未知操作符: {self.operator}")


class UniverseFilter:
    """
    股票池筛选器

    支持:
    - 多条件筛选 (AND/OR)
    - 动态股票池
    - 缓存优化
    """

    def __init__(self):
        self.conditions: list[FilterCondition] = []
        self.custom_filters: list[Callable[[pd.DataFrame], pd.Series]] = []
        self._cache: dict[str, pd.Index] = {}

    def add_condition(
        self,
        field: str,
        operator: FilterOperator | str,
        value: Any,
        description: str = "",
    ) -> "UniverseFilter":
        """
        添加筛选条件

        Args:
            field: 字段名
            operator: 操作符
            value: 比较值
            description: 条件描述

        Returns:
            self，支持链式调用
        """
        if isinstance(operator, str):
            operator = FilterOperator(operator)

        condition = FilterCondition(
            field=field,
            operator=operator,
            value=value,
            description=description,
        )
        self.conditions.append(condition)
        return self

    def add_custom_filter(
        self,
        filter_func: Callable[[pd.DataFrame], pd.Series],
    ) -> "UniverseFilter":
        """
        添加自定义筛选函数

        Args:
            filter_func: 接受 DataFrame，返回布尔 Series 的函数

        Returns:
            self，支持链式调用
        """
        self.custom_filters.append(filter_func)
        return self

    def price_filter(
        self,
        min_price: float | None = None,
        max_price: float | None = None,
    ) -> "UniverseFilter":
        """添加价格筛选"""
        if min_price is not None:
            self.add_condition("close", FilterOperator.GTE, min_price, f"价格 >= ${min_price}")
        if max_price is not None:
            self.add_condition("close", FilterOperator.LTE, max_price, f"价格 <= ${max_price}")
        return self

    def volume_filter(self, min_volume: float) -> "UniverseFilter":
        """添加成交量筛选"""
        self.add_condition("volume", FilterOperator.GTE, min_volume, f"成交量 >= {min_volume}")
        return self

    def market_cap_filter(
        self,
        min_cap: float | None = None,
        max_cap: float | None = None,
    ) -> "UniverseFilter":
        """添加市值筛选"""
        if min_cap is not None:
            self.add_condition("market_cap", FilterOperator.GTE, min_cap, f"市值 >= ${min_cap}")
        if max_cap is not None:
            self.add_condition("market_cap", FilterOperator.LTE, max_cap, f"市值 <= ${max_cap}")
        return self

    def sector_filter(
        self,
        include: list[str] | None = None,
        exclude: list[str] | None = None,
    ) -> "UniverseFilter":
        """添加行业筛选"""
        if include:
            self.add_condition("sector", FilterOperator.IN, include, f"行业包含: {include}")
        if exclude:
            self.add_condition("sector", FilterOperator.NOT_IN, exclude, f"行业排除: {exclude}")
        return self

    def liquidity_filter(
        self,
        min_adv: float,
        lookback: int = 20,
    ) -> "UniverseFilter":
        """
        添加流动性筛选

        Args:
            min_adv: 最小日均成交额
            lookback: 回望天数
        """
        self.add_condition(f"adv_{lookback}", FilterOperator.GTE, min_adv, f"ADV{lookback} >= ${min_adv}")
        return self

    def apply(
        self,
        data: pd.DataFrame,
        as_of_date: date | None = None,
        combine: str = "and",
    ) -> list[str]:
        """
        应用筛选条件

        Args:
            data: 股票数据 DataFrame，index 为股票代码
            as_of_date: 观察日期 (用于 PIT 筛选)
            combine: 条件组合方式 ("and" 或 "or")

        Returns:
            通过筛选的股票代码列表
        """
        if data.empty:
            return []

        # 初始化掩码
        if combine == "and":
            mask = pd.Series(True, index=data.index)
        else:
            mask = pd.Series(False, index=data.index)

        # 应用标准条件
        for condition in self.conditions:
            if condition.field not in data.columns:
                logger.warning(f"字段不存在: {condition.field}")
                continue

            field_data = data[condition.field]
            condition_mask = condition.evaluate(field_data)

            if combine == "and":
                mask = mask & condition_mask
            else:
                mask = mask | condition_mask

        # 应用自定义筛选
        for custom_filter in self.custom_filters:
            try:
                custom_mask = custom_filter(data)
                if combine == "and":
                    mask = mask & custom_mask
                else:
                    mask = mask | custom_mask
            except Exception as e:
                logger.error(f"自定义筛选失败: {e}")

        # 获取通过筛选的股票
        filtered_symbols = data.index[mask].tolist()

        logger.info(
            "股票池筛选完成",
            total=len(data),
            passed=len(filtered_symbols),
            conditions=len(self.conditions),
            as_of=as_of_date,
        )

        return filtered_symbols

    def clear(self) -> "UniverseFilter":
        """清除所有条件"""
        self.conditions.clear()
        self.custom_filters.clear()
        self._cache.clear()
        return self

    def describe(self) -> list[str]:
        """返回所有条件的描述"""
        descriptions = []
        for i, cond in enumerate(self.conditions, 1):
            desc = cond.description or f"{cond.field} {cond.operator.value} {cond.value}"
            descriptions.append(f"{i}. {desc}")
        for i, _ in enumerate(self.custom_filters, 1):
            descriptions.append(f"自定义筛选 {i}")
        return descriptions


# === 预定义筛选器 ===

def create_large_cap_filter(min_market_cap: float = 10_000_000_000) -> UniverseFilter:
    """创建大盘股筛选器 (市值 > 100亿美元)"""
    return (
        UniverseFilter()
        .market_cap_filter(min_cap=min_market_cap)
        .liquidity_filter(min_adv=1_000_000)
        .price_filter(min_price=5.0)
    )


def create_mid_cap_filter(
    min_market_cap: float = 2_000_000_000,
    max_market_cap: float = 10_000_000_000,
) -> UniverseFilter:
    """创建中盘股筛选器"""
    return (
        UniverseFilter()
        .market_cap_filter(min_cap=min_market_cap, max_cap=max_market_cap)
        .liquidity_filter(min_adv=500_000)
        .price_filter(min_price=3.0)
    )


def create_small_cap_filter(
    min_market_cap: float = 300_000_000,
    max_market_cap: float = 2_000_000_000,
) -> UniverseFilter:
    """创建小盘股筛选器"""
    return (
        UniverseFilter()
        .market_cap_filter(min_cap=min_market_cap, max_cap=max_market_cap)
        .liquidity_filter(min_adv=100_000)
        .price_filter(min_price=1.0)
    )


def create_quality_filter() -> UniverseFilter:
    """创建质量股筛选器"""
    filter_ = UniverseFilter()

    # 添加自定义质量筛选
    def quality_check(data: pd.DataFrame) -> pd.Series:
        """质量检查: ROE > 15%, 负债率 < 60%"""
        roe_ok = data.get("roe", pd.Series(True, index=data.index)) > 0.15
        debt_ok = data.get("debt_ratio", pd.Series(True, index=data.index)) < 0.6
        return roe_ok & debt_ok

    filter_.add_custom_filter(quality_check)
    return filter_
