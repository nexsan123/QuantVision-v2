/**
 * Phase 10: 风险系统升级 - TypeScript 类型定义
 *
 * 包含:
 * - 风险因子模型类型
 * - 风险分解结果
 * - 压力测试类型
 * - 实时监控类型
 */

// ============ 风险因子类型 ============

/** 风格因子类型 */
export type StyleFactor =
  | 'size'        // 市值因子
  | 'value'       // 价值因子
  | 'momentum'    // 动量因子
  | 'volatility'  // 波动因子
  | 'quality'     // 质量因子
  | 'growth'      // 成长因子
  | 'liquidity'   // 流动因子
  | 'leverage'    // 杠杆因子

/** 行业因子类型 (GICS一级) */
export type IndustryFactor =
  | 'communication_services'  // 通讯服务
  | 'consumer_discretionary'  // 非必需消费
  | 'consumer_staples'        // 必需消费
  | 'energy'                  // 能源
  | 'financials'              // 金融
  | 'healthcare'              // 医疗
  | 'industrials'             // 工业
  | 'information_technology'  // 信息技术
  | 'materials'               // 材料
  | 'real_estate'             // 房地产
  | 'utilities'               // 公用事业

/** 风格因子标签 */
export const STYLE_FACTOR_LABELS: Record<StyleFactor, string> = {
  size: '\u5e02\u503c',
  value: '\u4ef7\u503c',
  momentum: '\u52a8\u91cf',
  volatility: '\u6ce2\u52a8',
  quality: '\u8d28\u91cf',
  growth: '\u6210\u957f',
  liquidity: '\u6d41\u52a8\u6027',
  leverage: '\u6760\u6746',
}

/** 行业因子标签 */
export const INDUSTRY_FACTOR_LABELS: Record<IndustryFactor, string> = {
  communication_services: '\u901a\u8baf\u670d\u52a1',
  consumer_discretionary: '\u975e\u5fc5\u9700\u6d88\u8d39',
  consumer_staples: '\u5fc5\u9700\u6d88\u8d39',
  energy: '\u80fd\u6e90',
  financials: '\u91d1\u878d',
  healthcare: '\u533b\u7597',
  industrials: '\u5de5\u4e1a',
  information_technology: '\u4fe1\u606f\u6280\u672f',
  materials: '\u6750\u6599',
  real_estate: '\u623f\u5730\u4ea7',
  utilities: '\u516c\u7528\u4e8b\u4e1a',
}

// ============ 风险分解类型 ============

/** 因子暴露 */
export interface FactorExposure {
  factor: string
  exposure: number      // 暴露系数
  tStat: number        // t统计量
  pValue: number       // p值
  isSignificant: boolean
  riskContribution: number  // 风险贡献 (%)
}

/** 风格因子暴露 */
export interface StyleFactorExposures {
  size: number
  value: number
  momentum: number
  volatility: number
  quality: number
  growth: number
  liquidity: number
  leverage: number
}

/** 风险分解结果 */
export interface RiskDecomposition {
  totalRisk: number           // 总风险 (年化波动率)

  // 风险来源分解
  riskContributions: {
    market: number            // 市场风险贡献 (%)
    style: number             // 风格风险贡献 (%)
    industry: number          // 行业风险贡献 (%)
    specific: number          // 特质风险贡献 (%)
  }

  // 详细风格风险贡献
  styleRiskDetails: Record<StyleFactor, number>

  // 详细行业风险贡献
  industryRiskDetails: Record<string, number>

  // 因子暴露
  factorExposures: {
    market: number            // 市场Beta
    style: StyleFactorExposures
    industry: Record<string, number>
  }

  // 统计指标
  rSquared: number           // 解释力度
  trackingError: number      // 跟踪误差
  activeRisk: number         // 主动风险
}

// ============ 压力测试类型 ============

/** 压力情景类型 */
export type ScenarioType = 'historical' | 'hypothetical' | 'custom'

/** 压力测试情景 */
export interface StressScenario {
  id: string
  name: string
  type: ScenarioType
  description: string

  // 冲击参数
  shocks: {
    marketReturn?: number           // 市场收益冲击
    volatilityMultiplier?: number   // 波动率乘数
    sectorShocks?: Record<string, number>  // 行业冲击
    factorShocks?: Record<string, number>  // 因子冲击
    liquidityShock?: number         // 流动性冲击
  }

  // 历史情景额外信息
  historicalPeriod?: {
    startDate: string
    endDate: string
    spyDrawdown: number
  }
}

/** 压力测试结果 */
export interface StressTestResult {
  scenario: StressScenario

  // 组合影响
  portfolioImpact: {
    expectedLoss: number          // 预期亏损金额
    expectedLossPercent: number   // 预期亏损百分比
    varImpact: number             // VaR变化
    maxDrawdown: number           // 最大回撤
    recoveryDays: number          // 预计恢复天数
    liquidationRisk: boolean      // 是否触发强平
  }

  // 各持仓影响
  positionImpacts: {
    symbol: string
    currentWeight: number
    expectedLoss: number
    lossPercent: number
    contribution: number          // 对组合亏损的贡献
  }[]

  // 风险指标变化
  riskMetricsChange: {
    volatilityBefore: number
    volatilityAfter: number
    varBefore: number
    varAfter: number
    betaBefore: number
    betaAfter: number
  }

  // 建议
  recommendations: string[]
}

/** 预置压力情景 */
export const PRESET_SCENARIOS: StressScenario[] = [
  {
    id: '2008_financial_crisis',
    name: '2008\u91d1\u878d\u5371\u673a',
    type: 'historical',
    description: '2008\u5e749-10\u6708\u5168\u7403\u91d1\u878d\u5371\u673a',
    shocks: {
      marketReturn: -0.50,
      volatilityMultiplier: 3.0,
      sectorShocks: {
        financials: -0.60,
        real_estate: -0.50,
      },
    },
    historicalPeriod: {
      startDate: '2008-09-01',
      endDate: '2009-03-31',
      spyDrawdown: -0.50,
    },
  },
  {
    id: '2011_euro_crisis',
    name: '2011\u6b27\u503a\u5371\u673a',
    type: 'historical',
    description: '2011\u5e747-10\u6708\u6b27\u6d32\u4e3b\u6743\u503a\u52a1\u5371\u673a',
    shocks: {
      marketReturn: -0.19,
      volatilityMultiplier: 2.0,
      sectorShocks: {
        financials: -0.30,
      },
    },
    historicalPeriod: {
      startDate: '2011-07-01',
      endDate: '2011-10-31',
      spyDrawdown: -0.19,
    },
  },
  {
    id: '2020_covid',
    name: '2020\u65b0\u51a0\u5d29\u76d8',
    type: 'historical',
    description: '2020\u5e742-3\u6708\u65b0\u51a0\u75ab\u60c5\u51b2\u51fb',
    shocks: {
      marketReturn: -0.34,
      volatilityMultiplier: 4.0,
      sectorShocks: {
        energy: -0.55,
        consumer_discretionary: -0.40,
      },
    },
    historicalPeriod: {
      startDate: '2020-02-19',
      endDate: '2020-03-23',
      spyDrawdown: -0.34,
    },
  },
  {
    id: '2022_rate_hike',
    name: '2022\u52a0\u606f\u5468\u671f',
    type: 'historical',
    description: '2022\u5e74\u7f8e\u8054\u50a8\u6fc0\u8fdb\u52a0\u606f',
    shocks: {
      marketReturn: -0.25,
      volatilityMultiplier: 1.8,
      factorShocks: {
        growth: -0.35,
        value: 0.10,
      },
    },
    historicalPeriod: {
      startDate: '2022-01-01',
      endDate: '2022-10-31',
      spyDrawdown: -0.25,
    },
  },
  {
    id: 'market_crash_20',
    name: '\u5e02\u573a\u4e0b\u8dcc20%',
    type: 'hypothetical',
    description: '\u5047\u8bbe\u5e02\u573a\u6574\u4f53\u4e0b\u8dcc20%',
    shocks: {
      marketReturn: -0.20,
      volatilityMultiplier: 2.0,
    },
  },
  {
    id: 'market_crash_30_vol',
    name: '\u5e02\u573a\u4e0b\u8dcc30%+\u6ce2\u52a8\u7387\u7ffb\u500d',
    type: 'hypothetical',
    description: '\u5e02\u573a\u4e0b\u8dcc30%\u4e14\u6ce2\u52a8\u7387\u7ffb\u500d',
    shocks: {
      marketReturn: -0.30,
      volatilityMultiplier: 2.0,
    },
  },
  {
    id: 'tech_crash',
    name: '\u79d1\u6280\u80a1\u5d29\u76d8',
    type: 'hypothetical',
    description: '\u79d1\u6280\u884c\u4e1a\u5355\u72ec\u5927\u8dcc40%',
    shocks: {
      marketReturn: -0.15,
      sectorShocks: {
        information_technology: -0.40,
        communication_services: -0.30,
      },
    },
  },
  {
    id: 'liquidity_crisis',
    name: '\u6d41\u52a8\u6027\u5371\u673a',
    type: 'hypothetical',
    description: '\u5e02\u573a\u6d41\u52a8\u6027\u67af\u7aed\uff0c\u6ed1\u70b9\u589e\u52a05\u500d',
    shocks: {
      marketReturn: -0.10,
      liquidityShock: 5.0,
    },
  },
]

// ============ 实时监控类型 ============

/** 风险警报级别 */
export type AlertLevel = 'info' | 'warning' | 'critical' | 'emergency'

/** 风险警报 */
export interface RiskAlert {
  id: string
  timestamp: string
  level: AlertLevel
  type: string
  message: string
  currentValue: number
  threshold: number
  acknowledged: boolean
}

/** 风险监控状态 */
export interface RiskMonitorStatus {
  // 当前风险指标
  currentMetrics: {
    drawdown: number           // 当前回撤
    drawdownLimit: number      // 回撤限制
    var95: number              // 95% VaR
    varLimit: number           // VaR限制
    volatility: number         // 当前波动率
    volatilityLimit: number    // 波动率限制
  }

  // 因子暴露状态
  factorExposureStatus: {
    market: { current: number; limit: number; status: 'normal' | 'warning' | 'breach' }
    maxIndustry: { industry: string; current: number; limit: number; status: 'normal' | 'warning' | 'breach' }
    maxStyle: { factor: string; current: number; limit: number; status: 'normal' | 'warning' | 'breach' }
  }

  // 活跃警报
  activeAlerts: RiskAlert[]

  // 综合风险评分 (0-100)
  riskScore: number
  riskLevel: 'low' | 'medium' | 'high' | 'critical'

  // 更新时间
  lastUpdated: string
}

/** 风险限制配置 */
export interface RiskLimits {
  maxDrawdown: number           // 最大回撤限制
  maxVar: number                // 最大VaR
  maxVolatility: number         // 最大波动率
  maxIndustryExposure: number   // 最大行业暴露
  maxStyleExposure: number      // 最大风格暴露
  maxSinglePosition: number     // 最大单一持仓
  maxBeta: number               // 最大Beta
}

/** 默认风险限制 */
export const DEFAULT_RISK_LIMITS: RiskLimits = {
  maxDrawdown: 0.15,            // 15%
  maxVar: 0.03,                 // 3%
  maxVolatility: 0.25,          // 25%
  maxIndustryExposure: 0.25,    // 25%
  maxStyleExposure: 0.5,        // 0.5 标准差
  maxSinglePosition: 0.10,      // 10%
  maxBeta: 1.5,                 // 1.5
}

// ============ 颜色配置 ============

/** 警报级别颜色 */
export const ALERT_LEVEL_COLORS: Record<AlertLevel, string> = {
  info: '#1890ff',
  warning: '#faad14',
  critical: '#ff4d4f',
  emergency: '#cf1322',
}

/** 风险等级颜色 */
export const RISK_LEVEL_COLORS: Record<string, string> = {
  low: '#52c41a',
  medium: '#faad14',
  high: '#ff4d4f',
  critical: '#cf1322',
}

/** 风险贡献颜色 */
export const RISK_CONTRIBUTION_COLORS = {
  market: '#1890ff',
  style: '#722ed1',
  industry: '#13c2c2',
  specific: '#faad14',
}
