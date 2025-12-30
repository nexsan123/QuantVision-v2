"""
财务数据模型

提供 Point-in-Time (PIT) 支持的财务报表数据:
- 资产负债表
- 利润表
- 现金流量表

PIT 说明:
- report_date: 财报所属期间 (如 2024-03-31 表示 Q1 财报)
- release_date: 财报实际发布日期 (如 2024-04-28)
- 回测时使用 release_date 确保无前视偏差
"""

from datetime import date
from decimal import Decimal
from enum import Enum

from sqlalchemy import (
    Date,
    Index,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy import (
    Enum as SQLEnum,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class StatementType(str, Enum):
    """财报类型"""
    BALANCE_SHEET = "balance_sheet"      # 资产负债表
    INCOME_STATEMENT = "income"          # 利润表
    CASH_FLOW = "cash_flow"              # 现金流量表


class FiscalPeriod(str, Enum):
    """财年期间"""
    Q1 = "Q1"
    Q2 = "Q2"
    Q3 = "Q3"
    Q4 = "Q4"
    FY = "FY"  # 全年


class FinancialStatement(Base, UUIDMixin, TimestampMixin):
    """
    财务报表数据

    支持 Point-in-Time (PIT) 的财务指标存储:
    - 避免前视偏差
    - 支持财报修正追踪
    - 灵活的指标扩展
    """

    __tablename__ = "financial_statements"

    # === 标识字段 ===
    symbol: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        comment="股票代码",
    )
    statement_type: Mapped[StatementType] = mapped_column(
        SQLEnum(StatementType),
        nullable=False,
        comment="报表类型",
    )
    fiscal_period: Mapped[FiscalPeriod] = mapped_column(
        SQLEnum(FiscalPeriod),
        nullable=False,
        comment="财年期间",
    )
    fiscal_year: Mapped[int] = mapped_column(
        nullable=False,
        comment="财年年份",
    )

    # === PIT 日期 ===
    report_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="报告期末日期 (财报所属期间)",
    )
    release_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
        comment="发布日期 (财报公开日期，PIT 基准)",
    )

    # === 资产负债表指标 ===
    total_assets: Mapped[Decimal | None] = mapped_column(
        Numeric(22, 2),
        nullable=True,
        comment="总资产",
    )
    total_liabilities: Mapped[Decimal | None] = mapped_column(
        Numeric(22, 2),
        nullable=True,
        comment="总负债",
    )
    total_equity: Mapped[Decimal | None] = mapped_column(
        Numeric(22, 2),
        nullable=True,
        comment="股东权益",
    )
    current_assets: Mapped[Decimal | None] = mapped_column(
        Numeric(22, 2),
        nullable=True,
        comment="流动资产",
    )
    current_liabilities: Mapped[Decimal | None] = mapped_column(
        Numeric(22, 2),
        nullable=True,
        comment="流动负债",
    )
    cash_and_equivalents: Mapped[Decimal | None] = mapped_column(
        Numeric(22, 2),
        nullable=True,
        comment="现金及等价物",
    )
    inventory: Mapped[Decimal | None] = mapped_column(
        Numeric(22, 2),
        nullable=True,
        comment="存货",
    )
    accounts_receivable: Mapped[Decimal | None] = mapped_column(
        Numeric(22, 2),
        nullable=True,
        comment="应收账款",
    )
    accounts_payable: Mapped[Decimal | None] = mapped_column(
        Numeric(22, 2),
        nullable=True,
        comment="应付账款",
    )
    long_term_debt: Mapped[Decimal | None] = mapped_column(
        Numeric(22, 2),
        nullable=True,
        comment="长期负债",
    )

    # === 利润表指标 ===
    revenue: Mapped[Decimal | None] = mapped_column(
        Numeric(22, 2),
        nullable=True,
        comment="营业收入",
    )
    cost_of_revenue: Mapped[Decimal | None] = mapped_column(
        Numeric(22, 2),
        nullable=True,
        comment="营业成本",
    )
    gross_profit: Mapped[Decimal | None] = mapped_column(
        Numeric(22, 2),
        nullable=True,
        comment="毛利润",
    )
    operating_income: Mapped[Decimal | None] = mapped_column(
        Numeric(22, 2),
        nullable=True,
        comment="营业利润",
    )
    net_income: Mapped[Decimal | None] = mapped_column(
        Numeric(22, 2),
        nullable=True,
        comment="净利润",
    )
    ebitda: Mapped[Decimal | None] = mapped_column(
        Numeric(22, 2),
        nullable=True,
        comment="EBITDA",
    )
    eps: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 4),
        nullable=True,
        comment="每股收益",
    )
    eps_diluted: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 4),
        nullable=True,
        comment="稀释每股收益",
    )

    # === 现金流量表指标 ===
    operating_cash_flow: Mapped[Decimal | None] = mapped_column(
        Numeric(22, 2),
        nullable=True,
        comment="经营活动现金流",
    )
    investing_cash_flow: Mapped[Decimal | None] = mapped_column(
        Numeric(22, 2),
        nullable=True,
        comment="投资活动现金流",
    )
    financing_cash_flow: Mapped[Decimal | None] = mapped_column(
        Numeric(22, 2),
        nullable=True,
        comment="筹资活动现金流",
    )
    free_cash_flow: Mapped[Decimal | None] = mapped_column(
        Numeric(22, 2),
        nullable=True,
        comment="自由现金流",
    )
    capital_expenditure: Mapped[Decimal | None] = mapped_column(
        Numeric(22, 2),
        nullable=True,
        comment="资本支出",
    )
    dividends_paid: Mapped[Decimal | None] = mapped_column(
        Numeric(22, 2),
        nullable=True,
        comment="股息支付",
    )

    # === 其他指标 ===
    shares_outstanding: Mapped[int | None] = mapped_column(
        nullable=True,
        comment="流通股数",
    )
    shares_outstanding_diluted: Mapped[int | None] = mapped_column(
        nullable=True,
        comment="稀释后流通股数",
    )

    # === 数据来源 ===
    source: Mapped[str] = mapped_column(
        String(50),
        default="alpaca",
        comment="数据来源",
    )
    is_restated: Mapped[bool] = mapped_column(
        default=False,
        comment="是否为修正数据",
    )

    __table_args__ = (
        UniqueConstraint(
            "symbol", "statement_type", "fiscal_year", "fiscal_period", "release_date",
            name="uq_financial_statement"
        ),
        Index("ix_financial_symbol_release", "symbol", "release_date"),
        Index("ix_financial_symbol_report", "symbol", "report_date"),
        {"comment": "财务报表数据 (PIT)"},
    )

    # === 计算属性 ===
    @property
    def current_ratio(self) -> Decimal | None:
        """流动比率"""
        if self.current_assets and self.current_liabilities:
            return self.current_assets / self.current_liabilities
        return None

    @property
    def debt_to_equity(self) -> Decimal | None:
        """资产负债率"""
        if self.total_liabilities and self.total_equity:
            return self.total_liabilities / self.total_equity
        return None

    @property
    def gross_margin(self) -> Decimal | None:
        """毛利率"""
        if self.gross_profit and self.revenue:
            return self.gross_profit / self.revenue
        return None

    @property
    def operating_margin(self) -> Decimal | None:
        """营业利润率"""
        if self.operating_income and self.revenue:
            return self.operating_income / self.revenue
        return None

    @property
    def net_margin(self) -> Decimal | None:
        """净利率"""
        if self.net_income and self.revenue:
            return self.net_income / self.revenue
        return None
