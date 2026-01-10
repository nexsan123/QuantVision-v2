# Sprint 1: 策略管理基础 (5天)

> **文档版本**: 1.0  
> **预计时长**: 5天  
> **前置依赖**: Sprint 0 完成  
> **PRD参考**: 4.1 我的策略列表, 4.15.2 策略部署向导  
> **交付物**: 我的策略列表页面、4步部署向导

---

## 目标

实现策略管理的核心功能：策略列表展示和部署流程

---

## Task 1.1: 部署Schema定义 (后端)

**文件**: `backend/app/schemas/deployment.py`

```python
"""
策略部署 Pydantic Schema

包含:
- 部署配置
- 参数范围限制
- 环境类型
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, Any
from pydantic import BaseModel, Field, validator


class DeploymentEnvironment(str, Enum):
    """部署环境"""
    PAPER = "paper"  # 模拟盘
    LIVE = "live"    # 实盘


class DeploymentStatus(str, Enum):
    """部署状态"""
    DRAFT = "draft"      # 草稿
    RUNNING = "running"  # 运行中
    PAUSED = "paused"    # 已暂停
    STOPPED = "stopped"  # 已停止


class StrategyType(str, Enum):
    """策略类型"""
    INTRADAY = "intraday"       # 日内交易
    SHORT_TERM = "short_term"   # 短线 (1-5天)
    MEDIUM_TERM = "medium_term" # 中线 (1-4周)
    LONG_TERM = "long_term"     # 长线 (>1月)


# ============ 参数范围定义 ============

class ParamRange(BaseModel):
    """参数范围"""
    min_value: float
    max_value: float
    default_value: float
    step: float = 0.01
    unit: str = ""
    description: str = ""


class RiskParams(BaseModel):
    """风控参数"""
    stop_loss: float = Field(-0.05, ge=-0.50, le=-0.01, description="止损比例")
    take_profit: float = Field(0.10, ge=0.02, le=1.0, description="止盈比例")
    max_position_pct: float = Field(0.10, ge=0.01, le=0.50, description="单只最大仓位")
    max_drawdown: float = Field(-0.15, ge=-0.50, le=-0.05, description="最大回撤限制")


class CapitalConfig(BaseModel):
    """资金配置"""
    total_capital: Decimal = Field(..., gt=0, description="总资金")
    initial_position_pct: float = Field(0.80, ge=0.10, le=1.0, description="初始仓位比例")
    reserve_cash_pct: float = Field(0.20, ge=0.0, le=0.50, description="预留现金比例")


# ============ 部署配置 ============

class DeploymentConfig(BaseModel):
    """部署配置"""
    # 基础信息
    strategy_id: str
    deployment_name: str = Field(..., min_length=1, max_length=100)
    environment: DeploymentEnvironment = DeploymentEnvironment.PAPER
    strategy_type: StrategyType = StrategyType.MEDIUM_TERM
    
    # 股票池配置 (继承自策略，可选择子集)
    universe_subset: Optional[list[str]] = None  # 为空则使用策略默认股票池
    
    # 风控参数 (继承自策略回测，可在范围内调整)
    risk_params: RiskParams = Field(default_factory=RiskParams)
    
    # 资金配置
    capital_config: CapitalConfig
    
    # 调仓设置
    rebalance_frequency: str = Field("daily", pattern="^(daily|weekly|monthly)$")
    rebalance_time: str = Field("09:35", pattern="^[0-2][0-9]:[0-5][0-9]$")


class DeploymentCreate(BaseModel):
    """创建部署请求"""
    config: DeploymentConfig
    auto_start: bool = False


class DeploymentUpdate(BaseModel):
    """更新部署请求"""
    deployment_name: Optional[str] = None
    risk_params: Optional[RiskParams] = None
    capital_config: Optional[CapitalConfig] = None
    rebalance_frequency: Optional[str] = None
    rebalance_time: Optional[str] = None


class Deployment(BaseModel):
    """部署实体"""
    deployment_id: str
    strategy_id: str
    strategy_name: str
    deployment_name: str
    environment: DeploymentEnvironment
    status: DeploymentStatus
    strategy_type: StrategyType
    
    # 配置
    config: DeploymentConfig
    
    # 运行时数据
    current_pnl: Decimal = Decimal("0")
    current_pnl_pct: float = 0
    total_trades: int = 0
    win_rate: float = 0
    
    # 时间戳
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class DeploymentListResponse(BaseModel):
    """部署列表响应"""
    total: int
    items: list[Deployment]


# ============ 参数范围限制 ============

class ParamLimits(BaseModel):
    """参数范围限制 (从策略回测结果继承)"""
    strategy_id: str
    
    # 风控参数范围
    stop_loss_range: ParamRange
    take_profit_range: ParamRange
    max_position_pct_range: ParamRange
    max_drawdown_range: ParamRange
    
    # 资金范围
    min_capital: Decimal = Field(Decimal("1000"), description="最低资金要求")
    
    # 股票池
    available_symbols: list[str] = Field(default_factory=list)
    
    class Config:
        from_attributes = True
```

**验收标准**:
- [ ] 所有字段验证规则正确
- [ ] 环境/状态枚举完整
- [ ] 参数范围类型定义清晰

---

## Task 1.2: 部署服务 (后端)

**文件**: `backend/app/services/deployment_service.py`

```python
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

from app.schemas.deployment import (
    Deployment, DeploymentCreate, DeploymentUpdate,
    DeploymentConfig, DeploymentStatus, DeploymentEnvironment,
    ParamLimits, ParamRange, RiskParams
)


class DeploymentService:
    """部署服务"""
    
    # 默认参数范围
    DEFAULT_PARAM_LIMITS = {
        "stop_loss": ParamRange(min_value=-0.30, max_value=-0.02, default_value=-0.05, step=0.01, unit="%"),
        "take_profit": ParamRange(min_value=0.05, max_value=0.50, default_value=0.10, step=0.01, unit="%"),
        "max_position_pct": ParamRange(min_value=0.02, max_value=0.30, default_value=0.10, step=0.01, unit="%"),
        "max_drawdown": ParamRange(min_value=-0.30, max_value=-0.05, default_value=-0.15, step=0.01, unit="%"),
    }
    
    async def create_deployment(self, data: DeploymentCreate) -> Deployment:
        """创建部署"""
        deployment_id = str(uuid.uuid4())
        
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
        
        # TODO: 保存到数据库
        
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
        if data.deployment_name:
            deployment.deployment_name = data.deployment_name
        if data.risk_params:
            deployment.config.risk_params = data.risk_params
        if data.capital_config:
            deployment.config.capital_config = data.capital_config
        if data.rebalance_frequency:
            deployment.config.rebalance_frequency = data.rebalance_frequency
        if data.rebalance_time:
            deployment.config.rebalance_time = data.rebalance_time
        
        deployment.updated_at = datetime.now()
        
        # TODO: 更新数据库
        
        return deployment
    
    async def delete_deployment(self, deployment_id: str) -> bool:
        """删除部署"""
        deployment = await self.get_deployment(deployment_id)
        
        # 只允许删除非运行状态的部署
        if deployment.status == DeploymentStatus.RUNNING:
            raise ValueError("请先停止部署再删除")
        
        # TODO: 从数据库删除
        
        return True
    
    async def start_deployment(self, deployment_id: str) -> Deployment:
        """启动部署"""
        deployment = await self.get_deployment(deployment_id)
        
        if deployment.status == DeploymentStatus.RUNNING:
            return deployment
        
        # 验证配置
        await self._validate_config(deployment.config)
        
        deployment.status = DeploymentStatus.RUNNING
        deployment.started_at = datetime.now()
        deployment.updated_at = datetime.now()
        
        # TODO: 启动交易引擎
        # TODO: 更新数据库
        
        return deployment
    
    async def pause_deployment(self, deployment_id: str) -> Deployment:
        """暂停部署"""
        deployment = await self.get_deployment(deployment_id)
        
        if deployment.status != DeploymentStatus.RUNNING:
            raise ValueError("只能暂停运行中的部署")
        
        deployment.status = DeploymentStatus.PAUSED
        deployment.updated_at = datetime.now()
        
        # TODO: 暂停交易引擎
        # TODO: 更新数据库
        
        return deployment
    
    async def stop_deployment(self, deployment_id: str) -> Deployment:
        """停止部署"""
        deployment = await self.get_deployment(deployment_id)
        
        deployment.status = DeploymentStatus.STOPPED
        deployment.updated_at = datetime.now()
        
        # TODO: 停止交易引擎、平仓处理
        # TODO: 更新数据库
        
        return deployment
    
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
        
        # 切换环境
        deployment.config.environment = target_env
        deployment.environment = target_env
        deployment.updated_at = datetime.now()
        
        # TODO: 更新数据库
        
        return deployment
    
    async def get_deployment(self, deployment_id: str) -> Deployment:
        """获取部署详情"""
        # TODO: 从数据库查询
        raise NotImplementedError()
    
    async def list_deployments(
        self, 
        strategy_id: Optional[str] = None,
        status: Optional[DeploymentStatus] = None,
        environment: Optional[DeploymentEnvironment] = None
    ) -> list[Deployment]:
        """获取部署列表"""
        # TODO: 从数据库查询
        return []
    
    async def get_param_limits(self, strategy_id: str) -> ParamLimits:
        """获取策略的参数范围限制"""
        # TODO: 从策略回测结果获取
        # 这里返回默认值
        
        return ParamLimits(
            strategy_id=strategy_id,
            stop_loss_range=self.DEFAULT_PARAM_LIMITS["stop_loss"],
            take_profit_range=self.DEFAULT_PARAM_LIMITS["take_profit"],
            max_position_pct_range=self.DEFAULT_PARAM_LIMITS["max_position_pct"],
            max_drawdown_range=self.DEFAULT_PARAM_LIMITS["max_drawdown"],
            min_capital=Decimal("1000"),
            available_symbols=["AAPL", "MSFT", "GOOGL", "AMZN", "META"],  # 示例
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
            raise ValueError(f"止损比例超出范围 [{limits.stop_loss_range.min_value}, {limits.stop_loss_range.max_value}]")
        
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
            raise ValueError(f"胜率需大于40%才能切换实盘 (当前{deployment.win_rate*100:.1f}%)")


# 全局服务实例
deployment_service = DeploymentService()
```

**验收标准**:
- [ ] CRUD操作完整
- [ ] 状态转换逻辑正确
- [ ] 参数验证在范围内
- [ ] 实盘切换条件检查

---

## Task 1.3: 部署API (后端)

**文件**: `backend/app/api/v1/deployment.py`

```python
"""
策略部署 API

端点:
- POST   /deployments              创建部署
- GET    /deployments              获取部署列表
- GET    /deployments/{id}         获取部署详情
- PUT    /deployments/{id}         更新部署
- DELETE /deployments/{id}         删除部署
- POST   /deployments/{id}/start   启动
- POST   /deployments/{id}/pause   暂停
- POST   /deployments/{id}/stop    停止
- POST   /deployments/{id}/switch-env  切换环境
- GET    /deployments/{id}/param-limits  获取参数范围
"""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional

from app.schemas.deployment import (
    Deployment, DeploymentCreate, DeploymentUpdate,
    DeploymentListResponse, DeploymentStatus, DeploymentEnvironment,
    ParamLimits
)
from app.services.deployment_service import deployment_service

router = APIRouter(prefix="/deployments", tags=["策略部署"])


@router.post("", response_model=Deployment, summary="创建部署")
async def create_deployment(data: DeploymentCreate):
    """创建新的策略部署"""
    try:
        return await deployment_service.create_deployment(data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=DeploymentListResponse, summary="获取部署列表")
async def list_deployments(
    strategy_id: Optional[str] = Query(None, description="策略ID筛选"),
    status: Optional[DeploymentStatus] = Query(None, description="状态筛选"),
    environment: Optional[DeploymentEnvironment] = Query(None, description="环境筛选"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100)
):
    """获取部署列表"""
    deployments = await deployment_service.list_deployments(
        strategy_id=strategy_id,
        status=status,
        environment=environment
    )
    return DeploymentListResponse(total=len(deployments), items=deployments)


@router.get("/{deployment_id}", response_model=Deployment, summary="获取部署详情")
async def get_deployment(deployment_id: str):
    """获取部署详情"""
    try:
        return await deployment_service.get_deployment(deployment_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail="部署不存在")


@router.put("/{deployment_id}", response_model=Deployment, summary="更新部署")
async def update_deployment(deployment_id: str, data: DeploymentUpdate):
    """更新部署配置"""
    try:
        return await deployment_service.update_deployment(deployment_id, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{deployment_id}", summary="删除部署")
async def delete_deployment(deployment_id: str):
    """删除部署"""
    try:
        await deployment_service.delete_deployment(deployment_id)
        return {"message": "删除成功"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{deployment_id}/start", response_model=Deployment, summary="启动部署")
async def start_deployment(deployment_id: str):
    """启动部署"""
    try:
        return await deployment_service.start_deployment(deployment_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{deployment_id}/pause", response_model=Deployment, summary="暂停部署")
async def pause_deployment(deployment_id: str):
    """暂停部署"""
    try:
        return await deployment_service.pause_deployment(deployment_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{deployment_id}/stop", response_model=Deployment, summary="停止部署")
async def stop_deployment(deployment_id: str):
    """停止部署"""
    try:
        return await deployment_service.stop_deployment(deployment_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{deployment_id}/switch-env", response_model=Deployment, summary="切换环境")
async def switch_environment(
    deployment_id: str, 
    target_env: DeploymentEnvironment = Query(..., description="目标环境")
):
    """切换部署环境 (模拟盘 <-> 实盘)"""
    try:
        return await deployment_service.switch_environment(deployment_id, target_env)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{deployment_id}/param-limits", response_model=ParamLimits, summary="获取参数范围")
async def get_param_limits(deployment_id: str):
    """获取部署的参数范围限制"""
    deployment = await deployment_service.get_deployment(deployment_id)
    return await deployment_service.get_param_limits(deployment.strategy_id)
```

**验收标准**:
- [ ] 所有端点可正常调用
- [ ] 参数验证正确
- [ ] 错误处理完善

---

## Task 1.4: 前端类型定义

**文件**: `frontend/src/types/deployment.ts`

```typescript
/**
 * 策略部署类型定义
 */

// 部署环境
export type DeploymentEnvironment = 'paper' | 'live';

// 部署状态
export type DeploymentStatus = 'draft' | 'running' | 'paused' | 'stopped';

// 策略类型
export type StrategyType = 'intraday' | 'short_term' | 'medium_term' | 'long_term';

// 参数范围
export interface ParamRange {
  minValue: number;
  maxValue: number;
  defaultValue: number;
  step: number;
  unit: string;
  description: string;
}

// 风控参数
export interface RiskParams {
  stopLoss: number;
  takeProfit: number;
  maxPositionPct: number;
  maxDrawdown: number;
}

// 资金配置
export interface CapitalConfig {
  totalCapital: number;
  initialPositionPct: number;
  reserveCashPct: number;
}

// 部署配置
export interface DeploymentConfig {
  strategyId: string;
  deploymentName: string;
  environment: DeploymentEnvironment;
  strategyType: StrategyType;
  universeSubset?: string[];
  riskParams: RiskParams;
  capitalConfig: CapitalConfig;
  rebalanceFrequency: string;
  rebalanceTime: string;
}

// 部署实体
export interface Deployment {
  deploymentId: string;
  strategyId: string;
  strategyName: string;
  deploymentName: string;
  environment: DeploymentEnvironment;
  status: DeploymentStatus;
  strategyType: StrategyType;
  config: DeploymentConfig;
  currentPnl: number;
  currentPnlPct: number;
  totalTrades: number;
  winRate: number;
  createdAt: string;
  updatedAt: string;
  startedAt?: string;
}

// 参数范围限制
export interface ParamLimits {
  strategyId: string;
  stopLossRange: ParamRange;
  takeProfitRange: ParamRange;
  maxPositionPctRange: ParamRange;
  maxDrawdownRange: ParamRange;
  minCapital: number;
  availableSymbols: string[];
}

// 状态配置
export const STATUS_CONFIG: Record<DeploymentStatus, {
  label: string;
  color: string;
  icon: string;
}> = {
  draft: { label: '草稿', color: 'gray', icon: '📝' },
  running: { label: '运行中', color: 'green', icon: '▶️' },
  paused: { label: '已暂停', color: 'orange', icon: '⏸️' },
  stopped: { label: '已停止', color: 'red', icon: '⏹️' },
};

// 环境配置
export const ENV_CONFIG: Record<DeploymentEnvironment, {
  label: string;
  color: string;
  icon: string;
}> = {
  paper: { label: '模拟盘', color: 'blue', icon: '📊' },
  live: { label: '实盘', color: 'green', icon: '💰' },
};

// 策略类型配置
export const STRATEGY_TYPE_CONFIG: Record<StrategyType, {
  label: string;
  holdingPeriod: string;
}> = {
  intraday: { label: '日内交易', holdingPeriod: '日内' },
  short_term: { label: '短线策略', holdingPeriod: '1-5天' },
  medium_term: { label: '中线策略', holdingPeriod: '1-4周' },
  long_term: { label: '长线策略', holdingPeriod: '>1月' },
};
```

**验收标准**:
- [ ] 类型定义与后端Schema一致
- [ ] 配置常量完整

---

## Task 1.5: 我的策略列表页面

**文件**: `frontend/src/pages/MyStrategies/index.tsx`

```tsx
/**
 * 我的策略列表页面
 * 
 * 功能:
 * - 展示所有策略
 * - 筛选和搜索
 * - 快速操作入口
 */
import { useState, useEffect } from 'react';
import { Card, Table, Tag, Button, Input, Select, Space, Dropdown, message } from 'antd';
import { 
  PlusOutlined, SearchOutlined, PlayCircleOutlined, 
  PauseCircleOutlined, SettingOutlined, MoreOutlined 
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { 
  Deployment, DeploymentStatus, DeploymentEnvironment,
  STATUS_CONFIG, ENV_CONFIG, STRATEGY_TYPE_CONFIG 
} from '@/types/deployment';

export default function MyStrategiesPage() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [strategies, setStrategies] = useState<Deployment[]>([]);
  const [statusFilter, setStatusFilter] = useState<DeploymentStatus | ''>('');
  const [envFilter, setEnvFilter] = useState<DeploymentEnvironment | ''>('');
  const [searchText, setSearchText] = useState('');

  useEffect(() => {
    fetchStrategies();
  }, [statusFilter, envFilter]);

  const fetchStrategies = async () => {
    setLoading(true);
    try {
      // TODO: 调用API
      // const params = new URLSearchParams();
      // if (statusFilter) params.append('status', statusFilter);
      // if (envFilter) params.append('environment', envFilter);
      // const response = await fetch(`/api/v1/deployments?${params}`);
      // const data = await response.json();
      // setStrategies(data.items);
      
      // 模拟数据
      setStrategies([
        {
          deploymentId: '1',
          strategyId: 's1',
          strategyName: '价值投资策略',
          deploymentName: '我的价值策略-模拟',
          environment: 'paper',
          status: 'running',
          strategyType: 'long_term',
          config: {} as any,
          currentPnl: 1234.56,
          currentPnlPct: 0.0523,
          totalTrades: 15,
          winRate: 0.67,
          createdAt: '2024-12-01',
          updatedAt: '2024-12-15',
          startedAt: '2024-12-01',
        },
        {
          deploymentId: '2',
          strategyId: 's2',
          strategyName: '动量突破策略',
          deploymentName: '动量实盘',
          environment: 'live',
          status: 'running',
          strategyType: 'short_term',
          config: {} as any,
          currentPnl: -234.12,
          currentPnlPct: -0.0156,
          totalTrades: 42,
          winRate: 0.52,
          createdAt: '2024-11-15',
          updatedAt: '2024-12-15',
          startedAt: '2024-11-15',
        },
      ]);
    } catch (error) {
      message.error('获取策略列表失败');
    } finally {
      setLoading(false);
    }
  };

  const handleStart = async (id: string) => {
    try {
      // await fetch(`/api/v1/deployments/${id}/start`, { method: 'POST' });
      message.success('启动成功');
      fetchStrategies();
    } catch (error) {
      message.error('启动失败');
    }
  };

  const handlePause = async (id: string) => {
    try {
      // await fetch(`/api/v1/deployments/${id}/pause`, { method: 'POST' });
      message.success('已暂停');
      fetchStrategies();
    } catch (error) {
      message.error('暂停失败');
    }
  };

  // 筛选
  const filteredStrategies = strategies.filter(s => {
    if (searchText && !s.strategyName.toLowerCase().includes(searchText.toLowerCase())) {
      return false;
    }
    return true;
  });

  const columns = [
    {
      title: '策略名称',
      dataIndex: 'strategyName',
      key: 'strategyName',
      render: (text: string, record: Deployment) => (
        <div>
          <div className="font-medium">{text}</div>
          <div className="text-xs text-gray-500">{record.deploymentName}</div>
        </div>
      ),
    },
    {
      title: '环境',
      dataIndex: 'environment',
      key: 'environment',
      render: (env: DeploymentEnvironment) => (
        <Tag color={ENV_CONFIG[env].color}>
          {ENV_CONFIG[env].icon} {ENV_CONFIG[env].label}
        </Tag>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: DeploymentStatus) => (
        <Tag color={STATUS_CONFIG[status].color}>
          {STATUS_CONFIG[status].icon} {STATUS_CONFIG[status].label}
        </Tag>
      ),
    },
    {
      title: '类型',
      dataIndex: 'strategyType',
      key: 'strategyType',
      render: (type: keyof typeof STRATEGY_TYPE_CONFIG) => STRATEGY_TYPE_CONFIG[type].label,
    },
    {
      title: '收益',
      key: 'pnl',
      render: (_: any, record: Deployment) => (
        <div className={record.currentPnl >= 0 ? 'text-green-500' : 'text-red-500'}>
          <div className="font-medium">
            {record.currentPnl >= 0 ? '+' : ''}{record.currentPnl.toFixed(2)}
          </div>
          <div className="text-xs">
            {record.currentPnl >= 0 ? '+' : ''}{(record.currentPnlPct * 100).toFixed(2)}%
          </div>
        </div>
      ),
    },
    {
      title: '胜率',
      dataIndex: 'winRate',
      key: 'winRate',
      render: (rate: number) => `${(rate * 100).toFixed(1)}%`,
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: Deployment) => (
        <Space>
          {record.status === 'running' ? (
            <Button 
              icon={<PauseCircleOutlined />} 
              size="small"
              onClick={() => handlePause(record.deploymentId)}
            />
          ) : (
            <Button 
              icon={<PlayCircleOutlined />} 
              size="small" 
              type="primary"
              onClick={() => handleStart(record.deploymentId)}
            />
          )}
          <Button 
            icon={<SettingOutlined />} 
            size="small"
            onClick={() => navigate(`/deployment/${record.deploymentId}/edit`)}
          />
          <Dropdown menu={{
            items: [
              { key: 'detail', label: '查看详情' },
              { key: 'signals', label: '查看信号' },
              { key: 'switch', label: '切换环境' },
              { key: 'delete', label: '删除', danger: true },
            ]
          }}>
            <Button icon={<MoreOutlined />} size="small" />
          </Dropdown>
        </Space>
      ),
    },
  ];

  return (
    <div className="p-6">
      {/* 页面标题 */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">📋 我的策略</h1>
          <p className="text-gray-400">管理您的所有策略部署</p>
        </div>
        <Button 
          type="primary" 
          icon={<PlusOutlined />}
          onClick={() => navigate('/strategy-builder')}
        >
          创建新策略
        </Button>
      </div>

      {/* 筛选栏 */}
      <Card className="bg-[#1a1a3a] mb-6">
        <div className="flex flex-wrap gap-4">
          <Input
            placeholder="搜索策略..."
            prefix={<SearchOutlined />}
            value={searchText}
            onChange={e => setSearchText(e.target.value)}
            className="w-64"
          />
          <Select
            placeholder="状态"
            value={statusFilter || undefined}
            onChange={setStatusFilter}
            allowClear
            className="w-32"
          >
            {Object.entries(STATUS_CONFIG).map(([key, config]) => (
              <Select.Option key={key} value={key}>
                {config.icon} {config.label}
              </Select.Option>
            ))}
          </Select>
          <Select
            placeholder="环境"
            value={envFilter || undefined}
            onChange={setEnvFilter}
            allowClear
            className="w-32"
          >
            {Object.entries(ENV_CONFIG).map(([key, config]) => (
              <Select.Option key={key} value={key}>
                {config.icon} {config.label}
              </Select.Option>
            ))}
          </Select>
        </div>
      </Card>

      {/* 策略列表 */}
      <Card className="bg-[#1a1a3a]">
        <Table
          columns={columns}
          dataSource={filteredStrategies}
          rowKey="deploymentId"
          loading={loading}
          pagination={{ pageSize: 10 }}
        />
      </Card>
    </div>
  );
}
```

**验收标准**:
- [ ] 策略列表正确显示
- [ ] 筛选功能正常
- [ ] 状态和环境标签正确
- [ ] 操作按钮可点击

---

## Task 1.6: 部署向导组件 (4步)

**文件**: `frontend/src/components/Deployment/DeploymentWizard.tsx`

```tsx
/**
 * 4步部署向导
 * 
 * Step 1: 选择环境 (模拟盘/实盘)
 * Step 2: 配置资金
 * Step 3: 调整风控参数
 * Step 4: 确认部署
 */
import { useState, useEffect } from 'react';
import { Modal, Steps, Button, Radio, InputNumber, Slider, Card, Alert, Descriptions, message } from 'antd';
import { 
  DeploymentConfig, ParamLimits, RiskParams, CapitalConfig,
  DeploymentEnvironment, StrategyType, ENV_CONFIG
} from '@/types/deployment';

interface DeploymentWizardProps {
  strategyId: string;
  strategyName: string;
  visible: boolean;
  onClose: () => void;
  onComplete: (config: DeploymentConfig) => void;
}

export default function DeploymentWizard({
  strategyId,
  strategyName,
  visible,
  onClose,
  onComplete,
}: DeploymentWizardProps) {
  const [currentStep, setCurrentStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [paramLimits, setParamLimits] = useState<ParamLimits | null>(null);
  
  // 配置状态
  const [environment, setEnvironment] = useState<DeploymentEnvironment>('paper');
  const [capitalConfig, setCapitalConfig] = useState<CapitalConfig>({
    totalCapital: 10000,
    initialPositionPct: 0.8,
    reserveCashPct: 0.2,
  });
  const [riskParams, setRiskParams] = useState<RiskParams>({
    stopLoss: -0.05,
    takeProfit: 0.10,
    maxPositionPct: 0.10,
    maxDrawdown: -0.15,
  });

  useEffect(() => {
    if (visible && strategyId) {
      fetchParamLimits();
    }
  }, [visible, strategyId]);

  const fetchParamLimits = async () => {
    try {
      // TODO: 调用API获取参数范围
      // const response = await fetch(`/api/v1/deployments/${strategyId}/param-limits`);
      // const data = await response.json();
      // setParamLimits(data);
      
      // 模拟数据
      setParamLimits({
        strategyId,
        stopLossRange: { minValue: -0.30, maxValue: -0.02, defaultValue: -0.05, step: 0.01, unit: '%', description: '止损比例' },
        takeProfitRange: { minValue: 0.05, maxValue: 0.50, defaultValue: 0.10, step: 0.01, unit: '%', description: '止盈比例' },
        maxPositionPctRange: { minValue: 0.02, maxValue: 0.30, defaultValue: 0.10, step: 0.01, unit: '%', description: '单只最大仓位' },
        maxDrawdownRange: { minValue: -0.30, maxValue: -0.05, defaultValue: -0.15, step: 0.01, unit: '%', description: '最大回撤' },
        minCapital: 1000,
        availableSymbols: ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META'],
      });
    } catch (error) {
      message.error('获取参数范围失败');
    }
  };

  const handleNext = () => {
    if (currentStep < 3) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handlePrev = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleComplete = async () => {
    setLoading(true);
    try {
      const config: DeploymentConfig = {
        strategyId,
        deploymentName: `${strategyName}-${environment === 'paper' ? '模拟' : '实盘'}`,
        environment,
        strategyType: 'medium_term',
        riskParams,
        capitalConfig,
        rebalanceFrequency: 'daily',
        rebalanceTime: '09:35',
      };
      
      await onComplete(config);
      message.success('部署创建成功！');
      onClose();
    } catch (error) {
      message.error('部署失败');
    } finally {
      setLoading(false);
    }
  };

  const steps = [
    { title: '选择环境', description: '模拟盘或实盘' },
    { title: '配置资金', description: '设置投资金额' },
    { title: '风控参数', description: '调整风险控制' },
    { title: '确认部署', description: '检查配置' },
  ];

  const renderStepContent = () => {
    switch (currentStep) {
      case 0:
        return (
          <div className="py-8">
            <div className="text-center mb-6">
              <h3 className="text-lg font-medium mb-2">选择部署环境</h3>
              <p className="text-gray-400">建议先在模拟盘验证策略效果</p>
            </div>
            <Radio.Group 
              value={environment} 
              onChange={e => setEnvironment(e.target.value)}
              className="w-full"
            >
              <div className="grid grid-cols-2 gap-4">
                <Radio.Button value="paper" className="h-32 flex items-center justify-center">
                  <div className="text-center">
                    <div className="text-3xl mb-2">📊</div>
                    <div className="font-medium">模拟盘</div>
                    <div className="text-xs text-gray-400">虚拟资金，无风险</div>
                  </div>
                </Radio.Button>
                <Radio.Button value="live" className="h-32 flex items-center justify-center">
                  <div className="text-center">
                    <div className="text-3xl mb-2">💰</div>
                    <div className="font-medium">实盘</div>
                    <div className="text-xs text-gray-400">真实交易，需谨慎</div>
                  </div>
                </Radio.Button>
              </div>
            </Radio.Group>
            {environment === 'live' && (
              <Alert 
                type="warning" 
                message="实盘交易存在风险，请确保您已充分了解策略逻辑并接受潜在亏损"
                className="mt-4"
              />
            )}
          </div>
        );
      
      case 1:
        return (
          <div className="py-6 space-y-6">
            <div>
              <label className="block text-sm font-medium mb-2">投资总金额</label>
              <InputNumber
                value={capitalConfig.totalCapital}
                onChange={v => setCapitalConfig({ ...capitalConfig, totalCapital: v || 1000 })}
                min={paramLimits?.minCapital || 1000}
                max={1000000}
                step={1000}
                addonBefore="$"
                className="w-full"
              />
              <div className="text-xs text-gray-500 mt-1">
                最低资金要求: ${paramLimits?.minCapital || 1000}
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-2">
                初始仓位比例: {(capitalConfig.initialPositionPct * 100).toFixed(0)}%
              </label>
              <Slider
                value={capitalConfig.initialPositionPct * 100}
                onChange={v => setCapitalConfig({ 
                  ...capitalConfig, 
                  initialPositionPct: v / 100,
                  reserveCashPct: 1 - v / 100
                })}
                min={10}
                max={100}
                step={5}
              />
              <div className="flex justify-between text-xs text-gray-500">
                <span>投入: ${(capitalConfig.totalCapital * capitalConfig.initialPositionPct).toFixed(0)}</span>
                <span>预留: ${(capitalConfig.totalCapital * capitalConfig.reserveCashPct).toFixed(0)}</span>
              </div>
            </div>
          </div>
        );
      
      case 2:
        return (
          <div className="py-6 space-y-6">
            <Alert 
              type="info" 
              message="以下参数继承自策略回测，您可以在允许范围内微调"
              className="mb-4"
            />
            
            {paramLimits && (
              <>
                <ParamSlider
                  label="止损比例"
                  value={riskParams.stopLoss}
                  onChange={v => setRiskParams({ ...riskParams, stopLoss: v })}
                  range={paramLimits.stopLossRange}
                />
                <ParamSlider
                  label="止盈比例"
                  value={riskParams.takeProfit}
                  onChange={v => setRiskParams({ ...riskParams, takeProfit: v })}
                  range={paramLimits.takeProfitRange}
                />
                <ParamSlider
                  label="单只最大仓位"
                  value={riskParams.maxPositionPct}
                  onChange={v => setRiskParams({ ...riskParams, maxPositionPct: v })}
                  range={paramLimits.maxPositionPctRange}
                />
                <ParamSlider
                  label="最大回撤限制"
                  value={riskParams.maxDrawdown}
                  onChange={v => setRiskParams({ ...riskParams, maxDrawdown: v })}
                  range={paramLimits.maxDrawdownRange}
                />
              </>
            )}
          </div>
        );
      
      case 3:
        return (
          <div className="py-6">
            <Card className="bg-[#12122a]">
              <Descriptions column={1} size="small">
                <Descriptions.Item label="策略名称">{strategyName}</Descriptions.Item>
                <Descriptions.Item label="部署环境">
                  <span className={environment === 'live' ? 'text-green-400' : 'text-blue-400'}>
                    {ENV_CONFIG[environment].icon} {ENV_CONFIG[environment].label}
                  </span>
                </Descriptions.Item>
                <Descriptions.Item label="投资金额">
                  ${capitalConfig.totalCapital.toLocaleString()}
                </Descriptions.Item>
                <Descriptions.Item label="初始仓位">
                  {(capitalConfig.initialPositionPct * 100).toFixed(0)}% 
                  (${(capitalConfig.totalCapital * capitalConfig.initialPositionPct).toFixed(0)})
                </Descriptions.Item>
                <Descriptions.Item label="止损">
                  {(riskParams.stopLoss * 100).toFixed(1)}%
                </Descriptions.Item>
                <Descriptions.Item label="止盈">
                  {(riskParams.takeProfit * 100).toFixed(1)}%
                </Descriptions.Item>
                <Descriptions.Item label="单只最大仓位">
                  {(riskParams.maxPositionPct * 100).toFixed(1)}%
                </Descriptions.Item>
              </Descriptions>
            </Card>
            
            {environment === 'live' && (
              <Alert 
                type="warning" 
                message="您即将开启实盘交易，请确认以上配置正确"
                className="mt-4"
              />
            )}
          </div>
        );
      
      default:
        return null;
    }
  };

  return (
    <Modal
      title={`部署策略: ${strategyName}`}
      open={visible}
      onCancel={onClose}
      width={600}
      footer={
        <div className="flex justify-between">
          <Button onClick={onClose}>取消</Button>
          <div className="space-x-2">
            {currentStep > 0 && (
              <Button onClick={handlePrev}>上一步</Button>
            )}
            {currentStep < 3 ? (
              <Button type="primary" onClick={handleNext}>下一步</Button>
            ) : (
              <Button type="primary" onClick={handleComplete} loading={loading}>
                {environment === 'live' ? '确认开启实盘' : '开始模拟交易'}
              </Button>
            )}
          </div>
        </div>
      }
    >
      <Steps current={currentStep} items={steps} className="mb-6" />
      {renderStepContent()}
    </Modal>
  );
}

// 参数滑块组件
function ParamSlider({ 
  label, 
  value, 
  onChange, 
  range 
}: { 
  label: string;
  value: number;
  onChange: (v: number) => void;
  range: ParamLimits['stopLossRange'];
}) {
  const displayValue = (range.minValue < 0 ? value : value) * 100;
  
  return (
    <div>
      <div className="flex justify-between mb-2">
        <label className="text-sm font-medium">{label}</label>
        <span className="text-sm text-blue-400">
          {displayValue.toFixed(1)}{range.unit}
        </span>
      </div>
      <Slider
        value={displayValue}
        onChange={v => onChange(v / 100)}
        min={range.minValue * 100}
        max={range.maxValue * 100}
        step={range.step * 100}
        marks={{
          [range.minValue * 100]: `${(range.minValue * 100).toFixed(0)}%`,
          [range.defaultValue * 100]: `默认`,
          [range.maxValue * 100]: `${(range.maxValue * 100).toFixed(0)}%`,
        }}
      />
    </div>
  );
}
```

**验收标准**:
- [ ] 4步流程完整
- [ ] 环境选择正常
- [ ] 资金配置正常
- [ ] 风控参数在范围内调整
- [ ] 确认页信息完整

---

## Task 1.7: 策略卡片组件

**文件**: `frontend/src/components/Strategy/StrategyCard.tsx`

```tsx
/**
 * 策略卡片组件
 */
import { Card, Tag, Progress, Button, Dropdown } from 'antd';
import { 
  PlayCircleOutlined, PauseCircleOutlined, 
  SettingOutlined, MoreOutlined 
} from '@ant-design/icons';
import { 
  Deployment, STATUS_CONFIG, ENV_CONFIG, STRATEGY_TYPE_CONFIG 
} from '@/types/deployment';

interface StrategyCardProps {
  deployment: Deployment;
  onStart?: () => void;
  onPause?: () => void;
  onEdit?: () => void;
  onDetail?: () => void;
}

export default function StrategyCard({
  deployment,
  onStart,
  onPause,
  onEdit,
  onDetail,
}: StrategyCardProps) {
  const statusConfig = STATUS_CONFIG[deployment.status];
  const envConfig = ENV_CONFIG[deployment.environment];
  const isProfitable = deployment.currentPnl >= 0;

  return (
    <Card 
      className="bg-[#1a1a3a] hover:border-blue-500 cursor-pointer transition-colors"
      onClick={onDetail}
    >
      {/* 头部 */}
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="text-lg font-bold text-white">{deployment.strategyName}</h3>
          <p className="text-sm text-gray-400">{deployment.deploymentName}</p>
        </div>
        <div className="flex gap-2">
          <Tag color={envConfig.color}>{envConfig.icon} {envConfig.label}</Tag>
          <Tag color={statusConfig.color}>{statusConfig.icon} {statusConfig.label}</Tag>
        </div>
      </div>

      {/* 收益 */}
      <div className="mb-4">
        <div className={`text-2xl font-bold ${isProfitable ? 'text-green-400' : 'text-red-400'}`}>
          {isProfitable ? '+' : ''}{deployment.currentPnl.toFixed(2)}
          <span className="text-sm ml-2">
            ({isProfitable ? '+' : ''}{(deployment.currentPnlPct * 100).toFixed(2)}%)
          </span>
        </div>
      </div>

      {/* 统计 */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <div className="text-xs text-gray-500">交易次数</div>
          <div className="text-lg font-medium">{deployment.totalTrades}</div>
        </div>
        <div>
          <div className="text-xs text-gray-500">胜率</div>
          <div className="text-lg font-medium">{(deployment.winRate * 100).toFixed(1)}%</div>
        </div>
      </div>

      {/* 胜率进度条 */}
      <Progress 
        percent={deployment.winRate * 100} 
        showInfo={false}
        strokeColor={deployment.winRate >= 0.5 ? '#52c41a' : '#ff4d4f'}
        size="small"
      />

      {/* 操作按钮 */}
      <div className="flex justify-between mt-4 pt-4 border-t border-[#2a2a4a]">
        <div className="space-x-2">
          {deployment.status === 'running' ? (
            <Button 
              icon={<PauseCircleOutlined />} 
              size="small"
              onClick={e => { e.stopPropagation(); onPause?.(); }}
            >
              暂停
            </Button>
          ) : (
            <Button 
              icon={<PlayCircleOutlined />} 
              size="small" 
              type="primary"
              onClick={e => { e.stopPropagation(); onStart?.(); }}
            >
              启动
            </Button>
          )}
        </div>
        <div className="space-x-2">
          <Button 
            icon={<SettingOutlined />} 
            size="small"
            onClick={e => { e.stopPropagation(); onEdit?.(); }}
          />
          <Dropdown menu={{
            items: [
              { key: 'signals', label: '查看信号' },
              { key: 'history', label: '交易历史' },
              { key: 'switch', label: '切换环境' },
              { key: 'delete', label: '删除', danger: true },
            ]
          }}>
            <Button 
              icon={<MoreOutlined />} 
              size="small"
              onClick={e => e.stopPropagation()}
            />
          </Dropdown>
        </div>
      </div>
    </Card>
  );
}
```

**验收标准**:
- [ ] 卡片信息展示完整
- [ ] 收益颜色正确
- [ ] 操作按钮可点击

---

## Task 1.8: 路由配置

**修改文件**: `frontend/src/App.tsx`

```tsx
// 添加路由
import MyStrategiesPage from '@/pages/MyStrategies';

// 在路由配置中添加:
{
  path: '/my-strategies',
  element: <MyStrategiesPage />,
}
```

**修改文件**: `frontend/src/layouts/MainLayout.tsx`

```tsx
// 在侧边栏菜单中添加:
{
  key: 'my-strategies',
  icon: <FolderOutlined />,
  label: '我的策略',
  path: '/my-strategies',
}
```

---

## Task 1.9: 后端路由注册

**修改文件**: `backend/app/main.py`

```python
from app.api.v1 import deployment

app.include_router(
    deployment.router,
    prefix=settings.API_V1_PREFIX,
    tags=["策略部署"],
)
```

---

## Sprint 1 完成检查清单

### 后端
- [ ] Task 1.1: deployment.py Schema完整
- [ ] Task 1.2: deployment_service.py 服务完整
- [ ] Task 1.3: deployment.py API可调用
- [ ] Task 1.9: 路由已注册

### 前端
- [ ] Task 1.4: deployment.ts 类型定义完整
- [ ] Task 1.5: MyStrategies/index.tsx 页面正常
- [ ] Task 1.6: DeploymentWizard.tsx 4步流程完整
- [ ] Task 1.7: StrategyCard.tsx 组件正常
- [ ] Task 1.8: 路由配置完成

### 集成测试
- [ ] 我的策略列表显示正常
- [ ] 4步部署向导流程完整
- [ ] 启动/暂停操作正常

---

## 下一步

完成后进入 **Sprint 2: 交易监控升级**

---

## 新增API端点

```
POST   /api/v1/deployments              - 创建部署
GET    /api/v1/deployments              - 获取部署列表
GET    /api/v1/deployments/{id}         - 获取部署详情
PUT    /api/v1/deployments/{id}         - 更新部署
DELETE /api/v1/deployments/{id}         - 删除部署
POST   /api/v1/deployments/{id}/start   - 启动
POST   /api/v1/deployments/{id}/pause   - 暂停
POST   /api/v1/deployments/{id}/stop    - 停止
POST   /api/v1/deployments/{id}/switch-env - 切换环境
GET    /api/v1/deployments/{id}/param-limits - 获取参数范围
```

---

**预计完成时间**: 5天
