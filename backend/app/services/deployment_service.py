"""
策略部署服务

核心功能:
- 创建/更新/删除部署 (数据库持久化)
- 启动/暂停/停止
- 环境切换
- 配置快照

数据源: PostgreSQL 数据库
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional
import uuid

import structlog
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_context
from app.models.deployment import (
    Deployment as DeploymentModel,
    DeploymentStatusEnum,
    DeploymentEnvironmentEnum,
    StrategyTypeEnum,
)
from app.schemas.deployment import (
    Deployment, DeploymentCreate, DeploymentUpdate,
    DeploymentConfig, DeploymentStatus, DeploymentEnvironment,
    ParamLimits, ParamRange, RiskParams, CapitalConfig, StrategyType
)

logger = structlog.get_logger()


# ============ 枚举映射 ============

def schema_to_model_status(status: DeploymentStatus) -> DeploymentStatusEnum:
    """Schema状态转Model状态"""
    mapping = {
        DeploymentStatus.DRAFT: DeploymentStatusEnum.DRAFT,
        DeploymentStatus.RUNNING: DeploymentStatusEnum.RUNNING,
        DeploymentStatus.PAUSED: DeploymentStatusEnum.PAUSED,
        DeploymentStatus.STOPPED: DeploymentStatusEnum.STOPPED,
    }
    return mapping[status]


def model_to_schema_status(status: DeploymentStatusEnum) -> DeploymentStatus:
    """Model状态转Schema状态"""
    mapping = {
        DeploymentStatusEnum.DRAFT: DeploymentStatus.DRAFT,
        DeploymentStatusEnum.RUNNING: DeploymentStatus.RUNNING,
        DeploymentStatusEnum.PAUSED: DeploymentStatus.PAUSED,
        DeploymentStatusEnum.STOPPED: DeploymentStatus.STOPPED,
        DeploymentStatusEnum.ERROR: DeploymentStatus.STOPPED,  # error -> stopped
    }
    return mapping[status]


def schema_to_model_env(env: DeploymentEnvironment) -> DeploymentEnvironmentEnum:
    """Schema环境转Model环境"""
    mapping = {
        DeploymentEnvironment.PAPER: DeploymentEnvironmentEnum.PAPER,
        DeploymentEnvironment.LIVE: DeploymentEnvironmentEnum.LIVE,
    }
    return mapping[env]


def model_to_schema_env(env: DeploymentEnvironmentEnum) -> DeploymentEnvironment:
    """Model环境转Schema环境"""
    mapping = {
        DeploymentEnvironmentEnum.PAPER: DeploymentEnvironment.PAPER,
        DeploymentEnvironmentEnum.LIVE: DeploymentEnvironment.LIVE,
    }
    return mapping[env]


def schema_to_model_strategy_type(st: StrategyType) -> StrategyTypeEnum:
    """Schema策略类型转Model策略类型"""
    mapping = {
        StrategyType.INTRADAY: StrategyTypeEnum.INTRADAY,
        StrategyType.SHORT_TERM: StrategyTypeEnum.SHORT_TERM,
        StrategyType.MEDIUM_TERM: StrategyTypeEnum.MEDIUM_TERM,
        StrategyType.LONG_TERM: StrategyTypeEnum.LONG_TERM,
    }
    return mapping[st]


def model_to_schema_strategy_type(st: StrategyTypeEnum) -> StrategyType:
    """Model策略类型转Schema策略类型"""
    mapping = {
        StrategyTypeEnum.INTRADAY: StrategyType.INTRADAY,
        StrategyTypeEnum.SHORT_TERM: StrategyType.SHORT_TERM,
        StrategyTypeEnum.MEDIUM_TERM: StrategyType.MEDIUM_TERM,
        StrategyTypeEnum.LONG_TERM: StrategyType.LONG_TERM,
    }
    return mapping[st]


def model_to_schema(model: DeploymentModel) -> Deployment:
    """Model实例转Schema实例"""
    # 从model.config重建DeploymentConfig
    config_dict = model.config or {}

    # 构建风控参数
    risk_params_dict = config_dict.get("risk_params", {})
    risk_params = RiskParams(
        stop_loss=risk_params_dict.get("stop_loss", -0.05),
        take_profit=risk_params_dict.get("take_profit", 0.10),
        max_position_pct=risk_params_dict.get("max_position_pct", 0.10),
        max_drawdown=risk_params_dict.get("max_drawdown", -0.15),
    )

    # 构建资金配置
    capital_dict = config_dict.get("capital_config", {})
    capital_config = CapitalConfig(
        total_capital=Decimal(str(capital_dict.get("total_capital", 10000))),
        initial_position_pct=capital_dict.get("initial_position_pct", 0.80),
        reserve_cash_pct=capital_dict.get("reserve_cash_pct", 0.20),
    )

    # 构建部署配置
    deployment_config = DeploymentConfig(
        strategy_id=model.strategy_id,
        deployment_name=model.deployment_name,
        environment=model_to_schema_env(model.environment),
        strategy_type=model_to_schema_strategy_type(model.strategy_type),
        universe_subset=config_dict.get("universe_subset"),
        risk_params=risk_params,
        capital_config=capital_config,
        rebalance_frequency=config_dict.get("rebalance_frequency", "daily"),
        rebalance_time=config_dict.get("rebalance_time", "09:35"),
    )

    return Deployment(
        deployment_id=model.id,
        strategy_id=model.strategy_id,
        strategy_name=model.strategy_name,
        deployment_name=model.deployment_name,
        environment=model_to_schema_env(model.environment),
        status=model_to_schema_status(model.status),
        strategy_type=model_to_schema_strategy_type(model.strategy_type),
        config=deployment_config,
        current_pnl=Decimal(str(model.current_pnl)),
        current_pnl_pct=model.current_pnl_pct,
        total_trades=model.total_trades,
        win_rate=model.win_rate,
        created_at=model.created_at,
        updated_at=model.updated_at,
        started_at=model.started_at,
    )


class DeploymentService:
    """
    部署服务

    数据持久化到PostgreSQL数据库
    """

    # 默认参数范围
    DEFAULT_PARAM_LIMITS = {
        "stop_loss": ParamRange(
            min_value=-0.30, max_value=-0.02, default_value=-0.05,
            step=0.01, unit="%", description="止损比例"
        ),
        "take_profit": ParamRange(
            min_value=0.05, max_value=0.50, default_value=0.10,
            step=0.01, unit="%", description="止盈比例"
        ),
        "max_position_pct": ParamRange(
            min_value=0.02, max_value=0.30, default_value=0.10,
            step=0.01, unit="%", description="单只最大仓位"
        ),
        "max_drawdown": ParamRange(
            min_value=-0.30, max_value=-0.05, default_value=-0.15,
            step=0.01, unit="%", description="最大回撤"
        ),
    }

    async def create_deployment(
        self,
        data: DeploymentCreate,
        db: Optional[AsyncSession] = None
    ) -> Deployment:
        """创建部署"""
        deployment_id = str(uuid.uuid4())

        logger.info(
            "deployment_create",
            deployment_id=deployment_id,
            strategy_id=data.config.strategy_id,
            environment=data.config.environment.value,
        )

        # 获取策略信息
        strategy = await self._get_strategy(data.config.strategy_id)

        # 构建配置JSON
        config_json = {
            "strategy_id": data.config.strategy_id,
            "deployment_name": data.config.deployment_name,
            "environment": data.config.environment.value,
            "strategy_type": data.config.strategy_type.value,
            "universe_subset": data.config.universe_subset,
            "risk_params": {
                "stop_loss": data.config.risk_params.stop_loss,
                "take_profit": data.config.risk_params.take_profit,
                "max_position_pct": data.config.risk_params.max_position_pct,
                "max_drawdown": data.config.risk_params.max_drawdown,
            },
            "capital_config": {
                "total_capital": float(data.config.capital_config.total_capital),
                "initial_position_pct": data.config.capital_config.initial_position_pct,
                "reserve_cash_pct": data.config.capital_config.reserve_cash_pct,
            },
            "rebalance_frequency": data.config.rebalance_frequency,
            "rebalance_time": data.config.rebalance_time,
        }

        # 创建Model实例
        deployment_model = DeploymentModel(
            id=deployment_id,
            strategy_id=data.config.strategy_id,
            strategy_name=strategy.name,
            deployment_name=data.config.deployment_name,
            environment=schema_to_model_env(data.config.environment),
            status=DeploymentStatusEnum.DRAFT,
            strategy_type=schema_to_model_strategy_type(data.config.strategy_type),
            config=config_json,
        )

        # 保存到数据库
        if db:
            db.add(deployment_model)
            await db.commit()
            await db.refresh(deployment_model)
        else:
            async with get_db_context() as session:
                session.add(deployment_model)
                await session.commit()
                await session.refresh(deployment_model)
                deployment_model = deployment_model  # Keep reference

        deployment = model_to_schema(deployment_model)

        # 自动启动
        if data.auto_start:
            deployment = await self.start_deployment(deployment_id, db)

        return deployment

    async def update_deployment(
        self,
        deployment_id: str,
        data: DeploymentUpdate,
        db: Optional[AsyncSession] = None
    ) -> Deployment:
        """更新部署配置"""
        deployment = await self.get_deployment(deployment_id, db)

        # 只允许在非运行状态下修改
        if deployment.status == DeploymentStatus.RUNNING:
            raise ValueError("请先暂停部署再修改配置")

        # 构建更新字段
        update_data = {"updated_at": datetime.now()}

        if data.deployment_name:
            update_data["deployment_name"] = data.deployment_name

        # 获取当前配置并更新
        current_config = deployment.config.model_dump()

        if data.risk_params:
            current_config["risk_params"] = data.risk_params.model_dump()
        if data.capital_config:
            current_config["capital_config"] = {
                "total_capital": float(data.capital_config.total_capital),
                "initial_position_pct": data.capital_config.initial_position_pct,
                "reserve_cash_pct": data.capital_config.reserve_cash_pct,
            }
        if data.rebalance_frequency:
            current_config["rebalance_frequency"] = data.rebalance_frequency
        if data.rebalance_time:
            current_config["rebalance_time"] = data.rebalance_time

        update_data["config"] = current_config

        # 执行更新
        if db:
            stmt = (
                update(DeploymentModel)
                .where(DeploymentModel.id == deployment_id)
                .values(**update_data)
            )
            await db.execute(stmt)
            await db.commit()
        else:
            async with get_db_context() as session:
                stmt = (
                    update(DeploymentModel)
                    .where(DeploymentModel.id == deployment_id)
                    .values(**update_data)
                )
                await session.execute(stmt)

        logger.info("deployment_update", deployment_id=deployment_id)

        return await self.get_deployment(deployment_id, db)

    async def delete_deployment(
        self,
        deployment_id: str,
        db: Optional[AsyncSession] = None
    ) -> bool:
        """删除部署 (软删除)"""
        deployment = await self.get_deployment(deployment_id, db)

        # 只允许删除非运行状态的部署
        if deployment.status == DeploymentStatus.RUNNING:
            raise ValueError("请先停止部署再删除")

        # 软删除
        update_data = {
            "deleted_at": datetime.now(),
            "updated_at": datetime.now(),
        }

        if db:
            stmt = (
                update(DeploymentModel)
                .where(DeploymentModel.id == deployment_id)
                .values(**update_data)
            )
            await db.execute(stmt)
            await db.commit()
        else:
            async with get_db_context() as session:
                stmt = (
                    update(DeploymentModel)
                    .where(DeploymentModel.id == deployment_id)
                    .values(**update_data)
                )
                await session.execute(stmt)

        logger.info("deployment_delete", deployment_id=deployment_id)

        return True

    async def start_deployment(
        self,
        deployment_id: str,
        db: Optional[AsyncSession] = None
    ) -> Deployment:
        """启动部署"""
        deployment = await self.get_deployment(deployment_id, db)

        if deployment.status == DeploymentStatus.RUNNING:
            return deployment

        # 验证配置
        await self._validate_config(deployment.config)

        # 更新状态
        update_data = {
            "status": DeploymentStatusEnum.RUNNING,
            "started_at": datetime.now(),
            "updated_at": datetime.now(),
        }

        if db:
            stmt = (
                update(DeploymentModel)
                .where(DeploymentModel.id == deployment_id)
                .values(**update_data)
            )
            await db.execute(stmt)
            await db.commit()
        else:
            async with get_db_context() as session:
                stmt = (
                    update(DeploymentModel)
                    .where(DeploymentModel.id == deployment_id)
                    .values(**update_data)
                )
                await session.execute(stmt)

        logger.info(
            "deployment_start",
            deployment_id=deployment_id,
            environment=deployment.environment.value,
        )

        return await self.get_deployment(deployment_id, db)

    async def pause_deployment(
        self,
        deployment_id: str,
        db: Optional[AsyncSession] = None
    ) -> Deployment:
        """暂停部署"""
        deployment = await self.get_deployment(deployment_id, db)

        if deployment.status != DeploymentStatus.RUNNING:
            raise ValueError("只能暂停运行中的部署")

        update_data = {
            "status": DeploymentStatusEnum.PAUSED,
            "updated_at": datetime.now(),
        }

        if db:
            stmt = (
                update(DeploymentModel)
                .where(DeploymentModel.id == deployment_id)
                .values(**update_data)
            )
            await db.execute(stmt)
            await db.commit()
        else:
            async with get_db_context() as session:
                stmt = (
                    update(DeploymentModel)
                    .where(DeploymentModel.id == deployment_id)
                    .values(**update_data)
                )
                await session.execute(stmt)

        logger.info("deployment_pause", deployment_id=deployment_id)

        return await self.get_deployment(deployment_id, db)

    async def stop_deployment(
        self,
        deployment_id: str,
        db: Optional[AsyncSession] = None
    ) -> Deployment:
        """停止部署"""
        update_data = {
            "status": DeploymentStatusEnum.STOPPED,
            "stopped_at": datetime.now(),
            "updated_at": datetime.now(),
        }

        if db:
            stmt = (
                update(DeploymentModel)
                .where(DeploymentModel.id == deployment_id)
                .values(**update_data)
            )
            await db.execute(stmt)
            await db.commit()
        else:
            async with get_db_context() as session:
                stmt = (
                    update(DeploymentModel)
                    .where(DeploymentModel.id == deployment_id)
                    .values(**update_data)
                )
                await session.execute(stmt)

        logger.info("deployment_stop", deployment_id=deployment_id)

        return await self.get_deployment(deployment_id, db)

    async def switch_environment(
        self,
        deployment_id: str,
        target_env: DeploymentEnvironment,
        db: Optional[AsyncSession] = None
    ) -> Deployment:
        """切换环境 (模拟盘 <-> 实盘)"""
        deployment = await self.get_deployment(deployment_id, db)

        if deployment.environment == target_env:
            return deployment

        # 切换到实盘需要满足条件
        if target_env == DeploymentEnvironment.LIVE:
            await self._validate_live_switch(deployment)

        # 停止当前环境
        if deployment.status == DeploymentStatus.RUNNING:
            await self.stop_deployment(deployment_id, db)

        # 切换环境
        update_data = {
            "environment": schema_to_model_env(target_env),
            "updated_at": datetime.now(),
        }

        if db:
            stmt = (
                update(DeploymentModel)
                .where(DeploymentModel.id == deployment_id)
                .values(**update_data)
            )
            await db.execute(stmt)
            await db.commit()
        else:
            async with get_db_context() as session:
                stmt = (
                    update(DeploymentModel)
                    .where(DeploymentModel.id == deployment_id)
                    .values(**update_data)
                )
                await session.execute(stmt)

        logger.info(
            "deployment_switch_env",
            deployment_id=deployment_id,
            target_env=target_env.value,
        )

        return await self.get_deployment(deployment_id, db)

    async def get_deployment(
        self,
        deployment_id: str,
        db: Optional[AsyncSession] = None
    ) -> Deployment:
        """获取部署详情"""
        if db:
            stmt = select(DeploymentModel).where(
                DeploymentModel.id == deployment_id,
                DeploymentModel.deleted_at.is_(None)
            )
            result = await db.execute(stmt)
            model = result.scalar_one_or_none()
        else:
            async with get_db_context() as session:
                stmt = select(DeploymentModel).where(
                    DeploymentModel.id == deployment_id,
                    DeploymentModel.deleted_at.is_(None)
                )
                result = await session.execute(stmt)
                model = result.scalar_one_or_none()

        if not model:
            raise ValueError(f"部署不存在: {deployment_id}")

        return model_to_schema(model)

    async def list_deployments(
        self,
        strategy_id: Optional[str] = None,
        status: Optional[DeploymentStatus] = None,
        environment: Optional[DeploymentEnvironment] = None,
        db: Optional[AsyncSession] = None
    ) -> list[Deployment]:
        """获取部署列表"""
        # 构建查询
        stmt = select(DeploymentModel).where(
            DeploymentModel.deleted_at.is_(None)
        )

        if strategy_id:
            stmt = stmt.where(DeploymentModel.strategy_id == strategy_id)
        if status:
            stmt = stmt.where(DeploymentModel.status == schema_to_model_status(status))
        if environment:
            stmt = stmt.where(DeploymentModel.environment == schema_to_model_env(environment))

        # 按更新时间倒序
        stmt = stmt.order_by(DeploymentModel.updated_at.desc())

        if db:
            result = await db.execute(stmt)
            models = result.scalars().all()
        else:
            async with get_db_context() as session:
                result = await session.execute(stmt)
                models = result.scalars().all()

        return [model_to_schema(m) for m in models]

    async def get_param_limits(self, strategy_id: str) -> ParamLimits:
        """获取策略的参数范围限制"""
        # TODO: 从策略回测结果获取实际的参数范围
        # 这里返回默认值

        return ParamLimits(
            strategy_id=strategy_id,
            stop_loss_range=self.DEFAULT_PARAM_LIMITS["stop_loss"],
            take_profit_range=self.DEFAULT_PARAM_LIMITS["take_profit"],
            max_position_pct_range=self.DEFAULT_PARAM_LIMITS["max_position_pct"],
            max_drawdown_range=self.DEFAULT_PARAM_LIMITS["max_drawdown"],
            min_capital=Decimal("1000"),
            available_symbols=["AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA"],
        )

    async def update_runtime_metrics(
        self,
        deployment_id: str,
        pnl: float,
        pnl_pct: float,
        total_trades: int,
        win_rate: float,
        db: Optional[AsyncSession] = None
    ) -> None:
        """更新运行时指标"""
        update_data = {
            "current_pnl": pnl,
            "current_pnl_pct": pnl_pct,
            "total_trades": total_trades,
            "win_rate": win_rate,
            "updated_at": datetime.now(),
        }

        if db:
            stmt = (
                update(DeploymentModel)
                .where(DeploymentModel.id == deployment_id)
                .values(**update_data)
            )
            await db.execute(stmt)
            await db.commit()
        else:
            async with get_db_context() as session:
                stmt = (
                    update(DeploymentModel)
                    .where(DeploymentModel.id == deployment_id)
                    .values(**update_data)
                )
                await session.execute(stmt)

    async def _get_strategy(self, strategy_id: str):
        """获取策略信息"""
        # TODO: 从数据库/策略服务获取
        class MockStrategy:
            name = "测试策略"
        return MockStrategy()

    async def _validate_config(self, config: DeploymentConfig):
        """验证部署配置"""
        limits = await self.get_param_limits(config.strategy_id)

        # 验证风控参数在范围内
        rp = config.risk_params
        if not (limits.stop_loss_range.min_value <= rp.stop_loss <= limits.stop_loss_range.max_value):
            raise ValueError(
                f"止损比例超出范围 [{limits.stop_loss_range.min_value}, {limits.stop_loss_range.max_value}]"
            )

        # 验证资金
        if config.capital_config.total_capital < limits.min_capital:
            raise ValueError(f"资金不足，最低要求 ${limits.min_capital}")

    async def _validate_live_switch(self, deployment: Deployment):
        """验证切换到实盘的条件"""
        # 条件1: 模拟盘运行满30天
        if deployment.started_at:
            days = (datetime.now() - deployment.started_at).days
            if days < 30:
                raise ValueError(f"模拟盘需运行满30天才能切换实盘 (当前{days}天)")

        # 条件2: 胜率 > 40%
        if deployment.win_rate < 0.4:
            raise ValueError(
                f"胜率需大于40%才能切换实盘 (当前{deployment.win_rate*100:.1f}%)"
            )

    async def check_database_connection(self) -> dict:
        """检查数据库连接状态"""
        try:
            async with get_db_context() as session:
                # 执行简单查询测试连接
                stmt = select(DeploymentModel).limit(1)
                await session.execute(stmt)
                return {
                    "source": "database",
                    "is_mock": False,
                    "is_connected": True,
                    "error_message": None
                }
        except Exception as e:
            logger.error("deployment_db_check_failed", error=str(e))
            return {
                "source": "mock",
                "is_mock": True,
                "is_connected": False,
                "error_message": f"Database connection failed: {str(e)}"
            }


# 全局服务实例
deployment_service = DeploymentService()
