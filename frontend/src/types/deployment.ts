/**
 * 策略部署类型定义
 * Sprint 4 增强: 股票池配置、执行模式、前置检查
 */

// 部署环境
export type DeploymentEnvironment = 'paper' | 'live';

// 部署状态
export type DeploymentStatus = 'draft' | 'running' | 'paused' | 'stopped';

// 策略类型
export type StrategyType = 'intraday' | 'short_term' | 'medium_term' | 'long_term';

// ==================== Sprint 4 新增类型 ====================

// 执行模式 (F11)
export type ExecutionMode = 'auto' | 'confirm' | 'notify_only';

// 股票池配置模式
export type UniverseMode = 'full' | 'custom' | 'exclude';

// 股票池配置 (继承自策略，部署时不可修改)
export interface UniverseSubsetConfig {
  mode: UniverseMode;                   // 默认使用'full'继承策略配置
  maxPositions?: number;                 // 最大持股数量（继承自策略）
}

// 前置检查项 (F12)
export interface PreDeploymentCheck {
  id: string;
  name: string;
  description: string;
  status: 'pending' | 'passed' | 'failed' | 'warning';
  message?: string;
  required: boolean;  // 是否必须通过
}

// 前置检查结果 (F12)
export interface PreDeploymentCheckResult {
  allPassed: boolean;
  requiredPassed: boolean;
  checks: PreDeploymentCheck[];
}

// 执行模式配置 (F11)
export const EXECUTION_MODE_CONFIG: Record<ExecutionMode, {
  label: string;
  description: string;
  icon: string;
}> = {
  auto: {
    label: '全自动',
    description: '系统自动执行所有交易信号，无需人工确认',
    icon: '⚡'
  },
  confirm: {
    label: '确认执行',
    description: '每笔交易前需要您手动确认',
    icon: '👆'
  },
  notify_only: {
    label: '仅通知',
    description: '仅发送交易信号通知，不自动执行',
    icon: '🔔'
  },
};

// 股票池配置说明 (部署时继承策略配置)
// 注意: 股票池配置在策略构建器中定义，部署时自动继承，不再单独配置

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

// 部署配置 (Sprint 4 扩展)
export interface DeploymentConfig {
  strategyId: string;
  deploymentName: string;
  environment: DeploymentEnvironment;
  strategyType: StrategyType;
  // F10: 股票池配置
  universeConfig: UniverseSubsetConfig;
  // F11: 执行模式
  executionMode: ExecutionMode;
  // 原有配置
  riskParams: RiskParams;
  capitalConfig: CapitalConfig;
  rebalanceFrequency: string;
  rebalanceTime: string;
}

// 默认股票池配置 (F10)
export const DEFAULT_UNIVERSE_CONFIG: UniverseSubsetConfig = {
  mode: 'full',
  maxPositions: 20,
};

// 默认执行模式 (F11)
export const DEFAULT_EXECUTION_MODE: ExecutionMode = 'confirm';

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

// 部署列表响应
export interface DeploymentListResponse {
  total: number;
  items: Deployment[];
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

// 创建部署请求
export interface DeploymentCreateRequest {
  config: DeploymentConfig;
  autoStart?: boolean;
}

// 更新部署请求
export interface DeploymentUpdateRequest {
  deploymentName?: string;
  riskParams?: RiskParams;
  capitalConfig?: CapitalConfig;
  rebalanceFrequency?: string;
  rebalanceTime?: string;
}

// 状态配置
export const STATUS_CONFIG: Record<DeploymentStatus, {
  label: string;
  color: string;
  bgColor: string;
}> = {
  draft: { label: '草稿', color: 'gray', bgColor: 'bg-gray-500' },
  running: { label: '运行中', color: 'green', bgColor: 'bg-green-500' },
  paused: { label: '已暂停', color: 'orange', bgColor: 'bg-orange-500' },
  stopped: { label: '已停止', color: 'red', bgColor: 'bg-red-500' },
};

// 环境配置
export const ENV_CONFIG: Record<DeploymentEnvironment, {
  label: string;
  color: string;
  bgColor: string;
}> = {
  paper: { label: '模拟盘', color: 'blue', bgColor: 'bg-blue-500' },
  live: { label: '实盘', color: 'green', bgColor: 'bg-green-500' },
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

// 默认风控参数
export const DEFAULT_RISK_PARAMS: RiskParams = {
  stopLoss: -0.05,
  takeProfit: 0.10,
  maxPositionPct: 0.10,
  maxDrawdown: -0.15,
};

// 默认资金配置
export const DEFAULT_CAPITAL_CONFIG: CapitalConfig = {
  totalCapital: 10000,
  initialPositionPct: 0.80,
  reserveCashPct: 0.20,
};
