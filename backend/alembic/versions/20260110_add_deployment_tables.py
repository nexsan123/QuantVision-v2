"""add deployment intraday_trades pdt_status tables

Revision ID: 20260110_deployment
Revises:
Create Date: 2026-01-10

部署相关数据表:
- deployments: 策略部署实例
- intraday_trades: 日内交易记录
- pdt_status: PDT规则状态
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20260110_deployment'
down_revision = None  # First migration or set to previous revision
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create deployments table
    op.create_table(
        'deployments',
        sa.Column('id', sa.String(36), nullable=False, primary_key=True),
        sa.Column('strategy_id', sa.String(36), nullable=False, index=True),
        sa.Column('strategy_name', sa.String(200), nullable=False),
        sa.Column('deployment_name', sa.String(200), nullable=False),
        sa.Column(
            'environment',
            sa.Enum('paper', 'live', name='deploymentenvironmentenum'),
            nullable=False,
            server_default='paper'
        ),
        sa.Column(
            'status',
            sa.Enum('draft', 'running', 'paused', 'stopped', 'error', name='deploymentstatusenum'),
            nullable=False,
            server_default='draft'
        ),
        sa.Column(
            'strategy_type',
            sa.Enum('long_term', 'medium_term', 'short_term', 'intraday', name='strategytypeenum'),
            nullable=False,
            server_default='medium_term'
        ),
        sa.Column('config', postgresql.JSON(astext_type=sa.Text()), nullable=True, default={}),
        sa.Column('current_pnl', sa.Float(), nullable=False, server_default='0'),
        sa.Column('current_pnl_pct', sa.Float(), nullable=False, server_default='0'),
        sa.Column('total_trades', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('win_rate', sa.Float(), nullable=False, server_default='0'),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('stopped_at', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )

    # Create indexes for deployments
    op.create_index('ix_deployments_strategy_status', 'deployments', ['strategy_id', 'status'])
    op.create_index('ix_deployments_environment', 'deployments', ['environment'])

    # Create intraday_trades table
    op.create_table(
        'intraday_trades',
        sa.Column('id', sa.String(36), nullable=False, primary_key=True),
        sa.Column('deployment_id', sa.String(36), sa.ForeignKey('deployments.id'), nullable=True, index=True),
        sa.Column('user_id', sa.String(36), nullable=False, index=True),
        sa.Column('symbol', sa.String(20), nullable=False, index=True),
        sa.Column('side', sa.String(10), nullable=False),  # buy/sell
        sa.Column('quantity', sa.Float(), nullable=False),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('order_type', sa.String(20), nullable=True, server_default='market'),
        sa.Column('stop_loss', sa.Float(), nullable=True),
        sa.Column('take_profit', sa.Float(), nullable=True),
        sa.Column('is_open', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('exit_price', sa.Float(), nullable=True),
        sa.Column('exit_time', sa.DateTime(), nullable=True),
        sa.Column('pnl', sa.Float(), nullable=True),
        sa.Column('pnl_pct', sa.Float(), nullable=True),
        sa.Column('alpaca_order_id', sa.String(100), nullable=True),
        sa.Column('alpaca_fill_price', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Create indexes for intraday_trades
    op.create_index('ix_intraday_trades_user_symbol', 'intraday_trades', ['user_id', 'symbol'])
    op.create_index('ix_intraday_trades_date', 'intraday_trades', ['created_at'])

    # Create pdt_status table
    op.create_table(
        'pdt_status',
        sa.Column('id', sa.String(36), nullable=False, primary_key=True),
        sa.Column('user_id', sa.String(36), nullable=False, unique=True),
        sa.Column('account_equity', sa.Float(), nullable=False, server_default='0'),
        sa.Column('is_pdt_account', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('day_trades_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('remaining_day_trades', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('reset_date', sa.DateTime(), nullable=True),
        sa.Column('is_warning', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('last_sync_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )


def downgrade() -> None:
    # Drop tables in reverse order (respect foreign keys)
    op.drop_table('pdt_status')
    op.drop_table('intraday_trades')
    op.drop_table('deployments')

    # Drop enum types
    op.execute('DROP TYPE IF EXISTS strategytypeenum')
    op.execute('DROP TYPE IF EXISTS deploymentstatusenum')
    op.execute('DROP TYPE IF EXISTS deploymentenvironmentenum')
