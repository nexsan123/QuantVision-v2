/**
 * QuantVision 7步策略构建流程类型定义
 * Phase 8: 策略构建增强
 *
 * 7步流程:
 * 1. 投资池 (Universe) - 定义可交易的股票范围
 * 2. 因子层 (Alpha) - 选择和配置用于生成信号的因子
 * 3. 信号层 (Signal) - 定义入场和出场规则
 * 4. 风险层 (Risk) - 设置风险约束和暴露限制
 * 5. 组合层 (Portfolio) - 仓位分配和权重优化
 * 6. 执行层 (Execution) - 交易执行配置
 * 7. 监控层 (Monitor) - 持续监控和告警配置
 */

// ==================== Step 1: 投资池配置 ====================

/** 基础股票池类型 */
export type BasePool =
  | 'SP500'
  | 'NASDAQ100'
  | 'DOW30'
  | 'RUSSELL1000'
  | 'RUSSELL2000'
  | 'CUSTOM'

/** 市值范围配置 */
export interface MarketCapRange {
  min: number | null  // 最小市值(亿美元), null表示无限制
  max: number | null  // 最大市值(亿美元), null表示无限制
}

/** 行业枚举 */
export type Sector =
  | 'technology'
  | 'healthcare'
  | 'financials'
  | 'consumer_discretionary'
  | 'consumer_staples'
  | 'industrials'
  | 'materials'
  | 'energy'
  | 'utilities'
  | 'real_estate'
  | 'communication_services'

/** Step 1: 投资池配置 */
export interface UniverseConfig {
  /** 基础股票池 */
  basePool: BasePool
  /** 市值范围 */
  marketCap: MarketCapRange
  /** 日均成交额下限(万美元) */
  avgVolume: number
  /** 最短上市时间(年) */
  listingAge: number
  /** 排除的行业 */
  excludeSectors: Sector[]
  /** 自定义股票列表(仅当basePool为CUSTOM时) */
  customSymbols?: string[]
}

// ==================== Step 2: 因子层配置 ====================

/** 因子分类 */
export type FactorCategory =
  | 'momentum'     // 动量类
  | 'value'        // 价值类
  | 'quality'      // 质量类
  | 'volatility'   // 波动率类
  | 'size'         // 规模类
  | 'growth'       // 成长类
  | 'technical'    // 技术指标
  | 'fundamental'  // 基本面
  | 'custom'       // 自定义

/** 因子中性化类型 */
export type NeutralizeType = 'sector' | 'market_cap' | 'both' | 'none'

/** 因子标准化类型 */
export type NormalizeType = 'zscore' | 'rank' | 'percentile' | 'minmax' | 'none'

/** 因子组合方式 */
export type CombineMethod =
  | 'equal_weight'      // 等权重
  | 'ic_weight'         // IC加权
  | 'ir_weight'         // IR加权
  | 'custom_weight'     // 自定义权重

/** 单个因子选择配置 */
export interface FactorSelection {
  /** 因子名称/ID */
  factorId: string
  /** 因子表达式 */
  expression: string
  /** 自定义权重(仅当combineMethod为custom_weight时使用) */
  weight?: number
  /** 方向: 1表示因子越大越好, -1表示因子越小越好 */
  direction: 1 | -1
  /** 回望周期(天) */
  lookbackPeriod: number
}

/** Step 2: 因子层配置 */
export interface AlphaConfig {
  /** 已选因子列表 */
  factors: FactorSelection[]
  /** 因子组合方式 */
  combineMethod: CombineMethod
  /** 标准化方式 */
  normalize: NormalizeType
  /** 中性化处理 */
  neutralize: NeutralizeType
}

// ==================== Step 3: 信号层配置 ====================

/** 信号类型 */
export type SignalType = 'long_only' | 'long_short'

/** 规则操作符 */
export type RuleOperator =
  | 'gt'   // 大于
  | 'gte'  // 大于等于
  | 'lt'   // 小于
  | 'lte'  // 小于等于
  | 'eq'   // 等于
  | 'neq'  // 不等于

/** 规则字段类型 */
export type RuleField =
  | 'factor_rank'        // 因子排名
  | 'factor_score'       // 因子得分
  | 'holding_pnl'        // 持仓盈亏
  | 'holding_days'       // 持仓天数
  | 'price_change'       // 价格变化
  | 'volume_change'      // 成交量变化

/** 信号规则 */
export interface SignalRule {
  /** 规则ID */
  id: string
  /** 规则名称 */
  name: string
  /** 规则字段 */
  field: RuleField
  /** 操作符 */
  operator: RuleOperator
  /** 阈值 */
  threshold: number
  /** 是否启用 */
  enabled: boolean
}

/** Step 3: 信号层配置 */
export interface SignalConfig {
  /** 信号类型 */
  signalType: SignalType
  /** 目标持仓数 */
  targetPositions: number
  /** 入场规则 (AND逻辑) */
  entryRules: SignalRule[]
  /** 出场规则 (OR逻辑) */
  exitRules: SignalRule[]
  /** 强制止损阈值(%) - 必填 */
  stopLoss: number
  /** 止盈阈值(%) - 可选 */
  takeProfit?: number
}

// ==================== Step 4: 风险层配置 ====================

/** 熔断级别 */
export interface CircuitBreakerLevel {
  /** 级别 */
  level: 1 | 2 | 3
  /** 触发条件类型 */
  triggerType: 'daily_loss' | 'drawdown'
  /** 触发阈值(%) */
  threshold: number
  /** 触发动作 */
  action: 'notify' | 'pause_new' | 'full_stop'
}

/** Step 4: 风险层配置 */
export interface RiskConfig {
  /** 最大单股仓位(%) - 必填 */
  maxSinglePosition: number
  /** 最大行业仓位(%) - 必填 */
  maxIndustryPosition: number
  /** 最大回撤(%) - 必填 */
  maxDrawdown: number
  /** 最大波动率(%) - 可选 */
  maxVolatility?: number
  /** 最大VaR(%) - 可选 */
  maxVaR?: number
  /** 熔断规则 - 系统默认不可关闭 */
  circuitBreakers: CircuitBreakerLevel[]
  /** 是否启用风险监控 */
  enableRiskMonitor: boolean
}

// ==================== Step 5: 组合层配置 ====================

/** 权重优化方法 */
export type WeightOptimizer =
  | 'equal_weight'      // 等权重
  | 'market_cap'        // 市值加权
  | 'min_variance'      // 最小方差
  | 'max_sharpe'        // 最大夏普
  | 'risk_parity'       // 风险平价
  | 'factor_score'      // 因子得分加权
  | 'custom'            // 自定义

/** 调仓频率 */
export type RebalanceFrequency =
  | 'daily'
  | 'weekly'
  | 'biweekly'
  | 'monthly'
  | 'quarterly'

/** Step 5: 组合层配置 */
export interface PortfolioConfig {
  /** 权重优化方法 */
  optimizer: WeightOptimizer
  /** 调仓频率 */
  rebalanceFrequency: RebalanceFrequency
  /** 最小持仓数 */
  minHoldings: number
  /** 最大持仓数 */
  maxHoldings: number
  /** 最大换手率(%) */
  maxTurnover: number
  /** 是否仅做多 */
  longOnly: boolean
  /** 现金比例(%) */
  cashRatio: number
}

// ==================== Step 6: 执行层配置 ====================

/** 滑点模型类型 */
export type SlippageModel =
  | 'fixed'         // 固定滑点
  | 'volume_based'  // 基于成交量
  | 'sqrt'          // 平方根模型

/** 执行算法类型 */
export type ExecutionAlgorithm =
  | 'market'   // 市价单
  | 'twap'     // 时间加权
  | 'vwap'     // 成交量加权
  | 'pov'      // 成交量占比

/** Step 6: 执行层配置 */
export interface ExecutionConfig {
  /** 手续费率(%) */
  commissionRate: number
  /** 滑点模型 */
  slippageModel: SlippageModel
  /** 滑点参数(%) */
  slippageRate: number
  /** 执行算法 */
  algorithm: ExecutionAlgorithm
  /** 是否启用模拟交易 */
  paperTrade: boolean
  /** 券商连接配置(实盘时使用) */
  brokerConfig?: {
    broker: 'alpaca' | 'interactive_brokers'
    apiKey?: string
    secretKey?: string
  }
}

// ==================== Step 7: 监控层配置 ====================

/** 告警类型 */
export type AlertType =
  | 'drawdown'          // 回撤告警
  | 'daily_loss'        // 日亏损告警
  | 'position_drift'    // 持仓偏离告警
  | 'factor_decay'      // 因子衰减告警
  | 'execution_fail'    // 执行失败告警
  | 'circuit_breaker'   // 熔断告警

/** 告警通知方式 */
export type NotifyChannel = 'email' | 'sms' | 'push' | 'webhook'

/** 告警规则 */
export interface AlertRule {
  /** 规则ID */
  id: string
  /** 告警类型 */
  type: AlertType
  /** 阈值 */
  threshold: number
  /** 通知渠道 */
  channels: NotifyChannel[]
  /** 是否启用 */
  enabled: boolean
}

/** 监控指标配置 */
export interface MonitorMetric {
  /** 指标名称 */
  name: string
  /** 是否在仪表盘显示 */
  showOnDashboard: boolean
  /** 刷新频率(秒) */
  refreshInterval: number
}

/** Step 7: 监控层配置 */
export interface MonitorConfig {
  /** 告警规则列表 */
  alerts: AlertRule[]
  /** 监控指标配置 */
  metrics: MonitorMetric[]
  /** 是否启用实时监控 */
  enableRealtime: boolean
  /** 报告生成频率 */
  reportFrequency: 'daily' | 'weekly' | 'monthly'
}

// ==================== 完整策略配置 ====================

/** 策略状态 */
export type StrategyStatus =
  | 'draft'       // 草稿
  | 'backtest'    // 回测中
  | 'paper'       // 模拟交易
  | 'live'        // 实盘交易
  | 'paused'      // 已暂停
  | 'archived'    // 已归档

/** 完整7步策略配置 */
export interface StrategyConfig {
  /** 策略ID */
  id?: string
  /** 策略名称 */
  name: string
  /** 策略描述 */
  description: string
  /** 策略状态 */
  status: StrategyStatus
  /** 创建时间 */
  createdAt?: string
  /** 更新时间 */
  updatedAt?: string

  // 7步配置
  /** Step 1: 投资池配置 */
  universe: UniverseConfig
  /** Step 2: 因子层配置 */
  alpha: AlphaConfig
  /** Step 3: 信号层配置 */
  signal: SignalConfig
  /** Step 4: 风险层配置 */
  risk: RiskConfig
  /** Step 5: 组合层配置 */
  portfolio: PortfolioConfig
  /** Step 6: 执行层配置 */
  execution: ExecutionConfig
  /** Step 7: 监控层配置 */
  monitor: MonitorConfig
}

// ==================== 策略构建器状态 ====================

/** 步骤状态 */
export type StepStatus = 'pending' | 'current' | 'completed' | 'error'

/** 步骤元数据 */
export interface StepMeta {
  /** 步骤索引(0-6) */
  index: number
  /** 步骤名称 */
  title: string
  /** 步骤描述 */
  description: string
  /** 步骤状态 */
  status: StepStatus
  /** 教育提示 */
  educationTip: string
  /** 是否必填 */
  required: boolean
}

/** 策略构建器模式 */
export type BuilderMode = 'wizard' | 'workflow'

/** 策略构建器状态 */
export interface StrategyBuilderState {
  /** 当前模式 */
  mode: BuilderMode
  /** 当前步骤 */
  currentStep: number
  /** 步骤元数据 */
  steps: StepMeta[]
  /** 策略配置 */
  config: Partial<StrategyConfig>
  /** 是否有未保存的更改 */
  isDirty: boolean
  /** 验证错误 */
  errors: Record<string, string[]>
}

// ==================== AI 助手相关 ====================

/** AI 消息角色 */
export type AIMessageRole = 'user' | 'assistant' | 'system'

/** AI 消息 */
export interface AIMessage {
  id: string
  role: AIMessageRole
  content: string
  timestamp: string
  /** 关联的步骤 */
  relatedStep?: number
  /** 建议操作 */
  suggestedAction?: {
    type: 'apply_config' | 'show_detail' | 'navigate'
    payload: unknown
  }
}

/** AI 助手状态 */
export interface AIAssistantState {
  /** 是否展开 */
  expanded: boolean
  /** 消息历史 */
  messages: AIMessage[]
  /** 是否正在加载 */
  loading: boolean
  /** 当前上下文(当前步骤) */
  context: {
    step: number
    config: Partial<StrategyConfig>
  }
}

// ==================== 默认配置 ====================

/** 默认熔断规则(不可关闭) */
export const DEFAULT_CIRCUIT_BREAKERS: CircuitBreakerLevel[] = [
  { level: 1, triggerType: 'daily_loss', threshold: 3, action: 'notify' },
  { level: 2, triggerType: 'daily_loss', threshold: 5, action: 'pause_new' },
  { level: 3, triggerType: 'drawdown', threshold: 15, action: 'full_stop' },
]

/** 默认投资池配置 */
export const DEFAULT_UNIVERSE_CONFIG: UniverseConfig = {
  basePool: 'SP500',
  marketCap: { min: 10, max: null },
  avgVolume: 500,
  listingAge: 1,
  excludeSectors: [],
}

/** 默认因子层配置 */
export const DEFAULT_ALPHA_CONFIG: AlphaConfig = {
  factors: [],
  combineMethod: 'equal_weight',
  normalize: 'zscore',
  neutralize: 'sector',
}

/** 默认信号层配置 */
export const DEFAULT_SIGNAL_CONFIG: SignalConfig = {
  signalType: 'long_only',
  targetPositions: 20,
  entryRules: [
    { id: 'entry_1', name: '因子排名入场', field: 'factor_rank', operator: 'lte', threshold: 20, enabled: true },
  ],
  exitRules: [
    { id: 'exit_1', name: '排名出场', field: 'factor_rank', operator: 'gt', threshold: 50, enabled: true },
  ],
  stopLoss: 15,
}

/** 默认风险层配置 */
export const DEFAULT_RISK_CONFIG: RiskConfig = {
  maxSinglePosition: 5,
  maxIndustryPosition: 20,
  maxDrawdown: 15,
  circuitBreakers: DEFAULT_CIRCUIT_BREAKERS,
  enableRiskMonitor: true,
}

/** 默认组合层配置 */
export const DEFAULT_PORTFOLIO_CONFIG: PortfolioConfig = {
  optimizer: 'equal_weight',
  rebalanceFrequency: 'monthly',
  minHoldings: 10,
  maxHoldings: 50,
  maxTurnover: 100,
  longOnly: true,
  cashRatio: 5,
}

/** 默认执行层配置 */
export const DEFAULT_EXECUTION_CONFIG: ExecutionConfig = {
  commissionRate: 0.1,
  slippageModel: 'fixed',
  slippageRate: 0.1,
  algorithm: 'market',
  paperTrade: true,
}

/** 默认监控层配置 */
export const DEFAULT_MONITOR_CONFIG: MonitorConfig = {
  alerts: [
    { id: 'alert_1', type: 'drawdown', threshold: 10, channels: ['email'], enabled: true },
    { id: 'alert_2', type: 'daily_loss', threshold: 3, channels: ['email', 'push'], enabled: true },
  ],
  metrics: [
    { name: '总收益', showOnDashboard: true, refreshInterval: 60 },
    { name: '夏普比率', showOnDashboard: true, refreshInterval: 3600 },
    { name: '当前回撤', showOnDashboard: true, refreshInterval: 60 },
  ],
  enableRealtime: true,
  reportFrequency: 'weekly',
}

/** 7步元数据定义 */
export const STRATEGY_STEPS: Omit<StepMeta, 'status'>[] = [
  {
    index: 0,
    title: '投资池',
    description: '定义可交易的股票范围',
    educationTip: '专业投资者不会随便买股票。他们首先确定一个"可投资范围"，排除流动性差、市值太小、或自己不了解的股票。',
    required: true,
  },
  {
    index: 1,
    title: '因子层',
    description: '选择和配置选股因子',
    educationTip: '因子是量化投资的核心。好的因子能持续预测股票收益。常见因子包括动量、价值、质量等。',
    required: true,
  },
  {
    index: 2,
    title: '信号层',
    description: '定义买入和卖出规则',
    educationTip: '有了选股逻辑，还需要明确买卖规则。什么时候买？什么时候卖？止损怎么设？',
    required: true,
  },
  {
    index: 3,
    title: '风险层',
    description: '设置风险约束和限制',
    educationTip: '风险控制是长期盈利的前提。机构投资者通常限制单股仓位2-5%，而散户常常10-20%。',
    required: true,
  },
  {
    index: 4,
    title: '组合层',
    description: '仓位分配和权重优化',
    educationTip: '选好股票后，每只买多少？等权重还是按信号强度？调仓多频繁？这些都会影响最终收益。',
    required: true,
  },
  {
    index: 5,
    title: '执行层',
    description: '配置交易执行方式',
    educationTip: '交易成本和滑点会吃掉大部分利润。专业机构使用TWAP、VWAP等算法来降低成本。',
    required: false,
  },
  {
    index: 6,
    title: '监控层',
    description: '设置监控和告警',
    educationTip: '策略上线后需要持续监控。什么时候发警报？多久检查一次？这些配置很重要。',
    required: false,
  },
]

/** 创建默认策略配置 */
export function createDefaultStrategyConfig(name: string = ''): Partial<StrategyConfig> {
  return {
    name,
    description: '',
    status: 'draft',
    universe: DEFAULT_UNIVERSE_CONFIG,
    alpha: DEFAULT_ALPHA_CONFIG,
    signal: DEFAULT_SIGNAL_CONFIG,
    risk: DEFAULT_RISK_CONFIG,
    portfolio: DEFAULT_PORTFOLIO_CONFIG,
    execution: DEFAULT_EXECUTION_CONFIG,
    monitor: DEFAULT_MONITOR_CONFIG,
  }
}
