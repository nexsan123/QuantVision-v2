/**
 * Phase 9: 回测引擎升级 - 类型定义
 *
 * 包含:
 * - Walk-Forward 验证
 * - 过拟合检测
 * - 偏差检测
 */

// ============================================================
// Walk-Forward 验证
// ============================================================

/** Walk-Forward 配置 */
export interface WalkForwardConfig {
  /** 训练期长度 (月) */
  trainPeriod: number
  /** 测试期长度 (月) */
  testPeriod: number
  /** 滚动步长 (月) */
  stepSize: number
  /** 优化目标 */
  optimizeTarget: 'sharpe' | 'returns' | 'calmar' | 'sortino'
  /** 参数优化范围: [min, max, step] */
  parameterRanges: Record<string, [number, number, number]>
  /** 最小训练样本数 */
  minTrainSamples: number
  /** 是否使用扩展窗口 (vs 滚动窗口) */
  expandingWindow: boolean
}

/** 回测指标 (简化版) */
export interface BacktestMetrics {
  totalReturn: number
  annualReturn: number
  volatility: number
  maxDrawdown: number
  sharpeRatio: number
  sortinoRatio: number
  calmarRatio: number
  winRate: number
  profitFactor: number
  beta: number
  alpha: number
}

/** Walk-Forward 单轮结果 */
export interface WalkForwardRound {
  roundNumber: number
  trainStart: string
  trainEnd: string
  testStart: string
  testEnd: string
  optimizedParams: Record<string, number>
  inSampleMetrics: BacktestMetrics
  outOfSampleMetrics: BacktestMetrics
  /** 样本内外夏普比 */
  stabilityRatio: number
}

/** Walk-Forward 汇总结果 */
export interface WalkForwardResult {
  /** 配置 */
  config: WalkForwardConfig
  /** 各轮结果 */
  rounds: WalkForwardRound[]
  /** 汇总指标 */
  aggregatedMetrics: {
    /** 样本外夏普 */
    oosSharpe: number
    /** 样本外年化收益 */
    oosReturns: number
    /** 样本外最大回撤 */
    oosMaxDrawdown: number
    /** 稳定性比率 (OOS/IS 夏普平均) */
    stabilityRatio: number
    /** 样本外胜率 */
    oosWinRate: number
  }
  /** 过拟合概率 (0-100) */
  overfitProbability: number
  /** 综合评估 */
  assessment: 'excellent' | 'good' | 'moderate' | 'poor' | 'overfit'
  /** 建议 */
  recommendations: string[]
  /** 样本外权益曲线 */
  oosEquityCurve: { date: string; value: number }[]
}

// ============================================================
// 过拟合检测
// ============================================================

/** 参数敏感性分析 */
export interface ParameterSensitivity {
  parameter: string
  parameterLabel: string
  /** 敏感度得分 (0-1, 越高越敏感) */
  sensitivityScore: number
  /** 最优范围 */
  optimalRange: [number, number]
  /** 当前值 */
  currentValue: number
  /** 敏感性曲线 */
  curve: { paramValue: number; sharpe: number; returns: number }[]
  /** 评估 */
  verdict: 'stable' | 'moderate' | 'sensitive'
}

/** 样本内外对比 */
export interface InOutSampleComparison {
  inSampleSharpe: number
  outSampleSharpe: number
  inSampleReturns: number
  outSampleReturns: number
  stabilityRatio: number
  verdict: 'robust' | 'moderate' | 'likely_overfit'
}

/** Deflated Sharpe Ratio */
export interface DeflatedSharpeRatio {
  /** 原始夏普 */
  originalSharpe: number
  /** 调整后夏普 */
  deflatedSharpe: number
  /** 试验次数 */
  trialsCount: number
  /** 调整系数 */
  adjustmentFactor: number
  /** p值 */
  pValue: number
  /** 是否显著 */
  significant: boolean
}

/** 夏普比率上限检验 */
export interface SharpeUpperBound {
  observedSharpe: number
  theoreticalUpperBound: number
  exceedsProbability: number
  verdict: 'acceptable' | 'suspicious' | 'likely_overfit'
}

/** 过拟合检测结果 */
export interface OverfitDetectionResult {
  /** 参数敏感性分析 */
  parameterSensitivity: ParameterSensitivity[]
  /** 样本内外对比 */
  inOutSampleComparison: InOutSampleComparison
  /** Deflated Sharpe Ratio */
  deflatedSharpeRatio: DeflatedSharpeRatio
  /** 夏普上限检验 */
  sharpeUpperBound: SharpeUpperBound
  /** 综合评估 */
  overallAssessment: {
    /** 过拟合概率 (0-100) */
    overfitProbability: number
    /** 置信度 */
    confidence: 'high' | 'medium' | 'low'
    /** 风险等级 */
    riskLevel: 'low' | 'moderate' | 'high' | 'critical'
    /** 建议 */
    recommendations: string[]
    /** 详细说明 */
    explanation: string
  }
}

// ============================================================
// 偏差检测
// ============================================================

/** 前视偏差问题 */
export interface LookaheadBiasIssue {
  field: string
  description: string
  severity: 'high' | 'medium' | 'low'
  location: string
  suggestion: string
}

/** 前视偏差检测 */
export interface LookaheadBiasDetection {
  detected: boolean
  issues: LookaheadBiasIssue[]
  riskScore: number
}

/** 幸存者偏差检测 */
export interface SurvivorshipBiasDetection {
  detected: boolean
  /** 使用的已退市股票 */
  delistedStocksUsed: string[]
  /** 退市股票数量 */
  delistedCount: number
  /** 对收益的影响估计 (百分比) */
  impactEstimate: number
  /** 建议 */
  recommendation: string
}

/** 数据窥探偏差 */
export interface DataSnoopingBias {
  /** 测试过的策略/参数组合数量 */
  trialsCount: number
  /** 原始 p 值 */
  originalPValue: number
  /** 调整后 p 值 (Bonferroni/FDR) */
  adjustedPValue: number
  /** 多重检验调整方法 */
  adjustmentMethod: 'bonferroni' | 'holm' | 'fdr'
  /** 是否仍显著 */
  stillSignificant: boolean
}

/** 偏差检测结果 */
export interface BiasDetectionResult {
  /** 前视偏差 */
  lookaheadBias: LookaheadBiasDetection
  /** 幸存者偏差 */
  survivorshipBias: SurvivorshipBiasDetection
  /** 数据窥探偏差 */
  dataSnoopingBias: DataSnoopingBias
  /** 综合评估 */
  overallAssessment: {
    totalIssues: number
    criticalIssues: number
    riskLevel: 'clean' | 'minor' | 'moderate' | 'severe'
    recommendations: string[]
  }
}

// ============================================================
// 高级回测请求/响应
// ============================================================

/** Walk-Forward 验证请求 */
export interface WalkForwardRequest {
  strategyId: string
  startDate: string
  endDate: string
  initialCapital: number
  config: WalkForwardConfig
}

/** 参数敏感性分析请求 */
export interface SensitivityAnalysisRequest {
  strategyId: string
  startDate: string
  endDate: string
  initialCapital: number
  /** 要分析的参数 */
  parameters: {
    name: string
    range: [number, number]
    steps: number
  }[]
}

/** 过拟合检测请求 */
export interface OverfitDetectionRequest {
  strategyId: string
  startDate: string
  endDate: string
  initialCapital: number
  /** 样本内占比 */
  inSampleRatio: number
  /** 历史试验次数 (用于DSR计算) */
  historicalTrials?: number
}

/** 偏差检测请求 */
export interface BiasDetectionRequest {
  strategyId: string
  startDate: string
  endDate: string
  /** 检测类型 */
  detectionTypes: ('lookahead' | 'survivorship' | 'snooping')[]
}

// ============================================================
// 默认配置
// ============================================================

export const DEFAULT_WALK_FORWARD_CONFIG: WalkForwardConfig = {
  trainPeriod: 36,
  testPeriod: 12,
  stepSize: 12,
  optimizeTarget: 'sharpe',
  parameterRanges: {
    lookbackPeriod: [10, 60, 10],
    holdingCount: [10, 50, 10],
    stopLoss: [5, 20, 5],
  },
  minTrainSamples: 252,
  expandingWindow: false,
}

/** 过拟合风险等级颜色 */
export const OVERFIT_RISK_COLORS: Record<string, string> = {
  low: '#52c41a',
  moderate: '#faad14',
  high: '#ff7a45',
  critical: '#f5222d',
}

/** 偏差严重程度颜色 */
export const BIAS_SEVERITY_COLORS: Record<string, string> = {
  clean: '#52c41a',
  minor: '#1890ff',
  moderate: '#faad14',
  severe: '#f5222d',
}

/** 评估等级颜色 */
export const ASSESSMENT_COLORS: Record<string, string> = {
  excellent: '#52c41a',
  good: '#73d13d',
  moderate: '#faad14',
  poor: '#ff7a45',
  overfit: '#f5222d',
}
