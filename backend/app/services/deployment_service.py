"""
策略部署服务

核心功能:
- 创建/更新/删除部署
- 启动/暂停/停止
- 环境切换
- 配置快照
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional
import uuid

import structlog

from app.schemas.deployment import (
    Deployment, DeploymentCreate, DeploymentUpdate,
    DeploymentConfig, DeploymentStatus, DeploymentEnvironment,
    ParamLimits, ParamRange, RiskParams, CapitalConfig, StrategyType
)

logger = structlog.get_logger()


class DeploymentService:
    """部署服务"""

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

    # 内存存储 (生产环境应使用数据库)
    _deployments: dict[str, Deployment] = {}

    async def create_deployment(self, data: DeploymentCreate) -> Deployment:
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

        deployment = Deployment(
            deployment_id=deployment_id,
            strategy_id=data.config.strategy_id,
            strategy_name=strategy.name,
            deployment_name=data.config.deployment_name,
            environment=data.config.environment,
            status=DeploymentStatus.DRAFT,
            strategy_type=data.config.strategy_type,
            config=data.config,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # 保存到内存
        self._deployments[deployment_id] = deployment

        # 自动启动
        if data.auto_start:
            deployment = await self.start_deployment(deployment_id)

        return deployment

    async def update_deployment(
        self,
        deployment_id: str,
        data: DeploymentUpdate
    ) -> Deployment:
        """更新部署配置"""
        deployment = await self.get_deployment(deployment_id)

        # 只允许在非运行状态下修改
        if deployment.status == DeploymentStatus.RUNNING:
            raise ValueError("请先暂停部署再修改配置")

        # 更新字段
        update_dict = {}
        if data.deployment_name:
            update_dict["deployment_name"] = data.deployment_name
        if data.risk_params:
            update_dict["config"] = deployment.config.model_copy(
                update={"risk_params": data.risk_params}
            )
        if data.capital_config:
            update_dict["config"] = deployment.config.model_copy(
                update={"capital_config": data.capital_config}
            )
        if data.rebalance_frequency:
            update_dict["config"] = deployment.config.model_copy(
                update={"rebalance_frequency": data.rebalance_frequency}
            )
        if data.rebalance_time:
            update_dict["config"] = deployment.config.model_copy(
                update={"rebalance_time": data.rebalance_time}
            )

        # 更新时间戳
        updated_deployment = deployment.model_copy(
            update={**update_dict, "updated_at": datetime.now()}
        )
        self._deployments[deployment_id] = updated_deployment

        logger.info("deployment_update", deployment_id=deployment_id)

        return updated_deployment

    async def delete_deployment(self, deployment_id: str) -> bool:
        """删除部署"""
        deployment = await self.get_deployment(deployment_id)

        # 只允许删除非运行状态的部署
        if deployment.status == DeploymentStatus.RUNNING:
            raise ValueError("请先停止部署再删除")

        del self._deployments[deployment_id]
        logger.info("deployment_delete", deployment_id=deployment_id)

        return True

    async def start_deployment(self, deployment_id: str) -> Deployment:
        """启动部署"""
        deployment = await self.get_deployment(deployment_id)

        if deployment.status == DeploymentStatus.RUNNING:
            return deployment

        # 验证配置
        await self._validate_config(deployment.config)

        updated = deployment.model_copy(update={
            "status": DeploymentStatus.RUNNING,
            "started_at": datetime.now(),
            "updated_at": datetime.now(),
        })
        self._deployments[deployment_id] = updated

        logger.info(
            "deployment_start",
            deployment_id=deployment_id,
            environment=updated.environment.value,
        )

        return updated

    async def pause_deployment(self, deployment_id: str) -> Deployment:
        """暂停部署"""
        deployment = await self.get_deployment(deployment_id)

        if deployment.status != DeploymentStatus.RUNNING:
            raise ValueError("只能暂停运行中的部署")

        updated = deployment.model_copy(update={
            "status": DeploymentStatus.PAUSED,
            "updated_at": datetime.now(),
        })
        self._deployments[deployment_id] = updated

        logger.info("deployment_pause", deployment_id=deployment_id)

        return updated

    async def stop_deployment(self, deployment_id: str) -> Deployment:
        """停止部署"""
        deployment = await self.get_deployment(deployment_id)

        updated = deployment.model_copy(update={
            "status": DeploymentStatus.STOPPED,
            "updated_at": datetime.now(),
        })
        self._deployments[deployment_id] = updated

        logger.info("deployment_stop", deployment_id=deployment_id)

        return updated

    async def switch_environment(
        self,
        deployment_id: str,
        target_env: DeploymentEnvironment
    ) -> Deployment:
        """切换环境 (模拟盘 <-> 实盘)"""
        deployment = await self.get_deployment(deployment_id)

        if deployment.environment == target_env:
            return deployment

        # 切换到实盘需要满足条件
        if target_env == DeploymentEnvironment.LIVE:
            await self._validate_live_switch(deployment)

        # 停止当前环境
        if deployment.status == DeploymentStatus.RUNNING:
            await self.stop_deployment(deployment_id)
            deployment = await self.get_deployment(deployment_id)

        # 切换环境
        new_config = deployment.config.model_copy(update={"environment": target_env})
        updated = deployment.model_copy(update={
            "config": new_config,
            "environment": target_env,
            "updated_at": datetime.now(),
        })
        self._deployments[deployment_id] = updated

        logger.info(
            "deployment_switch_env",
            deployment_id=deployment_id,
            target_env=target_env.value,
        )

        return updated

    async def get_deployment(self, deployment_id: str) -> Deployment:
        """获取部署详情"""
        if deployment_id not in self._deployments:
            raise ValueError(f"部署不存在: {deployment_id}")
        return self._deployments[deployment_id]

    async def list_deployments(
        self,
        strategy_id: Optional[str] = None,
        status: Optional[DeploymentStatus] = None,
        environment: Optional[DeploymentEnvironment] = None
    ) -> list[Deployment]:
        """获取部署列表"""
        result = list(self._deployments.values())

        if strategy_id:
            result = [d for d in result if d.strategy_id == strategy_id]
        if status:
            result = [d for d in result if d.status == status]
        if environment:
            result = [d for d in result if d.environment == environment]

        # 按更新时间倒序
        result.sort(key=lambda x: x.updated_at, reverse=True)

        return result

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


# 全局服务实例
deployment_service = DeploymentService()
