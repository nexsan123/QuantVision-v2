"""
数据库迁移: 创建核心数据表

Revision ID: 001
Create Date: 2025-12-27

创建表:
- stock_ohlcv: 股票日线 OHLCV 数据
- macro_data: 宏观经济数据
- financial_statements: 财务报表数据
- universes: 股票池定义
- universe_snapshots: 股票池快照
- data_lineage: 数据血缘记录
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """创建数据表"""

    # === 股票日线 OHLCV 数据 ===
    op.create_table(
        'stock_ohlcv',
        sa.Column('id', postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column('symbol', sa.String(20), nullable=False, index=True, comment='股票代码'),
        sa.Column('trade_date', sa.Date, nullable=False, index=True, comment='交易日期'),
        # 原始价格
        sa.Column('open', sa.Numeric(18, 4), nullable=False, comment='开盘价'),
        sa.Column('high', sa.Numeric(18, 4), nullable=False, comment='最高价'),
        sa.Column('low', sa.Numeric(18, 4), nullable=False, comment='最低价'),
        sa.Column('close', sa.Numeric(18, 4), nullable=False, comment='收盘价'),
        sa.Column('volume', sa.BigInteger, nullable=False, comment='成交量'),
        # 复权价格
        sa.Column('adj_open', sa.Numeric(18, 4), nullable=True, comment='复权开盘价'),
        sa.Column('adj_high', sa.Numeric(18, 4), nullable=True, comment='复权最高价'),
        sa.Column('adj_low', sa.Numeric(18, 4), nullable=True, comment='复权最低价'),
        sa.Column('adj_close', sa.Numeric(18, 4), nullable=True, comment='复权收盘价'),
        # 衍生指标
        sa.Column('vwap', sa.Numeric(18, 4), nullable=True, comment='成交量加权平均价'),
        sa.Column('turnover', sa.Numeric(22, 2), nullable=True, comment='成交额'),
        sa.Column('trade_count', sa.BigInteger, nullable=True, comment='成交笔数'),
        # 元信息
        sa.Column('source', sa.String(50), server_default='alpaca', comment='数据来源'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        # 约束
        sa.UniqueConstraint('symbol', 'trade_date', name='uq_stock_ohlcv_symbol_date'),
        comment='股票日线 OHLCV 数据'
    )

    op.create_index('ix_stock_ohlcv_symbol_date', 'stock_ohlcv', ['symbol', 'trade_date'])
    op.create_index('ix_stock_ohlcv_date', 'stock_ohlcv', ['trade_date'])

    # === 宏观经济数据 ===
    op.create_table(
        'macro_data',
        sa.Column('id', postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column('indicator', sa.String(50), nullable=False, index=True, comment='指标代码'),
        sa.Column('report_date', sa.Date, nullable=False, index=True, comment='报告日期'),
        sa.Column('release_date', sa.Date, nullable=False, index=True, comment='发布日期 (PIT)'),
        sa.Column('value', sa.Numeric(22, 6), nullable=False, comment='指标值'),
        sa.Column('unit', sa.String(50), nullable=True, comment='单位'),
        sa.Column('frequency', sa.String(20), server_default='monthly', comment='频率'),
        sa.Column('source', sa.String(50), server_default='fred', comment='数据来源'),
        sa.Column('description', sa.String(500), nullable=True, comment='指标描述'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        # 约束
        sa.UniqueConstraint('indicator', 'report_date', 'release_date', name='uq_macro_data_indicator_dates'),
        comment='宏观经济数据 (支持 PIT)'
    )

    op.create_index('ix_macro_data_indicator_release', 'macro_data', ['indicator', 'release_date'])

    # === 财务报表数据 ===
    op.create_table(
        'financial_statements',
        sa.Column('id', postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column('symbol', sa.String(20), nullable=False, index=True, comment='股票代码'),
        sa.Column('statement_type', sa.String(20), nullable=False, comment='报表类型'),
        sa.Column('fiscal_period', sa.String(10), nullable=False, comment='财年期间'),
        sa.Column('fiscal_year', sa.Integer, nullable=False, comment='财年年份'),
        # PIT 日期
        sa.Column('report_date', sa.Date, nullable=False, comment='报告期末日期'),
        sa.Column('release_date', sa.Date, nullable=False, index=True, comment='发布日期 (PIT)'),
        # 资产负债表
        sa.Column('total_assets', sa.Numeric(22, 2), nullable=True, comment='总资产'),
        sa.Column('total_liabilities', sa.Numeric(22, 2), nullable=True, comment='总负债'),
        sa.Column('total_equity', sa.Numeric(22, 2), nullable=True, comment='股东权益'),
        sa.Column('current_assets', sa.Numeric(22, 2), nullable=True, comment='流动资产'),
        sa.Column('current_liabilities', sa.Numeric(22, 2), nullable=True, comment='流动负债'),
        sa.Column('cash_and_equivalents', sa.Numeric(22, 2), nullable=True, comment='现金及等价物'),
        sa.Column('inventory', sa.Numeric(22, 2), nullable=True, comment='存货'),
        sa.Column('accounts_receivable', sa.Numeric(22, 2), nullable=True, comment='应收账款'),
        sa.Column('accounts_payable', sa.Numeric(22, 2), nullable=True, comment='应付账款'),
        sa.Column('long_term_debt', sa.Numeric(22, 2), nullable=True, comment='长期负债'),
        # 利润表
        sa.Column('revenue', sa.Numeric(22, 2), nullable=True, comment='营业收入'),
        sa.Column('cost_of_revenue', sa.Numeric(22, 2), nullable=True, comment='营业成本'),
        sa.Column('gross_profit', sa.Numeric(22, 2), nullable=True, comment='毛利润'),
        sa.Column('operating_income', sa.Numeric(22, 2), nullable=True, comment='营业利润'),
        sa.Column('net_income', sa.Numeric(22, 2), nullable=True, comment='净利润'),
        sa.Column('ebitda', sa.Numeric(22, 2), nullable=True, comment='EBITDA'),
        sa.Column('eps', sa.Numeric(18, 4), nullable=True, comment='每股收益'),
        sa.Column('eps_diluted', sa.Numeric(18, 4), nullable=True, comment='稀释每股收益'),
        # 现金流量表
        sa.Column('operating_cash_flow', sa.Numeric(22, 2), nullable=True, comment='经营活动现金流'),
        sa.Column('investing_cash_flow', sa.Numeric(22, 2), nullable=True, comment='投资活动现金流'),
        sa.Column('financing_cash_flow', sa.Numeric(22, 2), nullable=True, comment='筹资活动现金流'),
        sa.Column('free_cash_flow', sa.Numeric(22, 2), nullable=True, comment='自由现金流'),
        sa.Column('capital_expenditure', sa.Numeric(22, 2), nullable=True, comment='资本支出'),
        sa.Column('dividends_paid', sa.Numeric(22, 2), nullable=True, comment='股息支付'),
        # 其他
        sa.Column('shares_outstanding', sa.BigInteger, nullable=True, comment='流通股数'),
        sa.Column('shares_outstanding_diluted', sa.BigInteger, nullable=True, comment='稀释后流通股数'),
        sa.Column('source', sa.String(50), server_default='alpaca', comment='数据来源'),
        sa.Column('is_restated', sa.Boolean, server_default='false', comment='是否为修正数据'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        # 约束
        sa.UniqueConstraint(
            'symbol', 'statement_type', 'fiscal_year', 'fiscal_period', 'release_date',
            name='uq_financial_statement'
        ),
        comment='财务报表数据 (PIT)'
    )

    op.create_index('ix_financial_symbol_release', 'financial_statements', ['symbol', 'release_date'])
    op.create_index('ix_financial_symbol_report', 'financial_statements', ['symbol', 'report_date'])

    # === 股票池定义 ===
    op.create_table(
        'universes',
        sa.Column('id', postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False, unique=True, comment='股票池名称'),
        sa.Column('description', sa.Text, nullable=True, comment='描述'),
        sa.Column('universe_type', sa.String(20), server_default='custom', comment='股票池类型'),
        sa.Column('base_index', sa.String(20), nullable=True, comment='基准指数'),
        sa.Column('filter_rules', sa.Text, nullable=True, comment='筛选规则 (JSON)'),
        sa.Column('is_active', sa.Boolean, server_default='true', comment='是否启用'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        comment='股票池定义'
    )

    # === 股票池快照 ===
    op.create_table(
        'universe_snapshots',
        sa.Column('id', postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column('universe_id', postgresql.UUID(as_uuid=False),
                  sa.ForeignKey('universes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('snapshot_date', sa.Date, nullable=False, index=True, comment='快照日期'),
        sa.Column('symbols', postgresql.ARRAY(sa.String(20)), nullable=False, comment='成分股列表'),
        sa.Column('count', sa.Integer, nullable=False, comment='成分股数量'),
        sa.Column('added_symbols', postgresql.ARRAY(sa.String(20)), nullable=True, comment='新增成分股'),
        sa.Column('removed_symbols', postgresql.ARRAY(sa.String(20)), nullable=True, comment='移除成分股'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        # 约束
        sa.UniqueConstraint('universe_id', 'snapshot_date', name='uq_universe_snapshot'),
        comment='股票池历史快照'
    )

    op.create_index('ix_universe_snapshot_date', 'universe_snapshots', ['universe_id', 'snapshot_date'])

    # === 数据血缘记录 ===
    op.create_table(
        'data_lineage',
        sa.Column('id', postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column('task_type', sa.String(50), nullable=False, index=True, comment='任务类型'),
        sa.Column('task_id', sa.String(100), nullable=True, comment='Celery 任务 ID'),
        sa.Column('source', sa.String(20), server_default='alpaca', comment='数据来源'),
        sa.Column('symbols', postgresql.JSON, nullable=True, comment='处理的股票列表'),
        sa.Column('start_date', sa.Date, nullable=True, comment='数据起始日期'),
        sa.Column('end_date', sa.Date, nullable=True, comment='数据结束日期'),
        # 执行结果
        sa.Column('status', sa.String(20), server_default='pending', index=True, comment='执行状态'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True, comment='开始时间'),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True, comment='完成时间'),
        sa.Column('duration_seconds', sa.Float, nullable=True, comment='执行时长'),
        # 统计
        sa.Column('records_fetched', sa.Integer, server_default='0', comment='获取记录数'),
        sa.Column('records_inserted', sa.Integer, server_default='0', comment='插入记录数'),
        sa.Column('records_updated', sa.Integer, server_default='0', comment='更新记录数'),
        sa.Column('records_failed', sa.Integer, server_default='0', comment='失败记录数'),
        # 质量
        sa.Column('quality_score', sa.Float, nullable=True, comment='数据质量评分'),
        sa.Column('missing_rate', sa.Float, nullable=True, comment='缺失率'),
        sa.Column('anomaly_count', sa.Integer, server_default='0', comment='异常值数量'),
        # 详情
        sa.Column('error_message', sa.Text, nullable=True, comment='错误信息'),
        sa.Column('metadata', postgresql.JSON, nullable=True, comment='附加元数据'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        comment='数据血缘记录'
    )

    op.create_index('ix_lineage_task_status', 'data_lineage', ['task_type', 'status'])
    op.create_index('ix_lineage_created', 'data_lineage', ['created_at'])


def downgrade() -> None:
    """删除数据表"""
    op.drop_table('data_lineage')
    op.drop_table('universe_snapshots')
    op.drop_table('universes')
    op.drop_table('financial_statements')
    op.drop_table('macro_data')
    op.drop_table('stock_ohlcv')
