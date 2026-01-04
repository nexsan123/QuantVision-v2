/**
 * Phase 13: \u5f52\u56e0\u4e0e\u62a5\u8868 - \u7c7b\u578b\u5b9a\u4e49
 *
 * \u5305\u542b:
 * - Brinson \u5f52\u56e0\u6a21\u578b
 * - \u56e0\u5b50\u5f52\u56e0\u6a21\u578b
 * - TCA \u4ea4\u6613\u6210\u672c\u5206\u6790
 * - \u62a5\u8868\u7c7b\u578b
 */

// ============ \u57fa\u7840\u7c7b\u578b ============

// \u65f6\u95f4\u6bb5
export interface TimePeriod {
  start: string
  end: string
}

// \u884c\u4e1a\u5206\u7c7b
export type SectorType =
  | 'technology'
  | 'healthcare'
  | 'financials'
  | 'consumer_discretionary'
  | 'consumer_staples'
  | 'industrials'
  | 'energy'
  | 'materials'
  | 'utilities'
  | 'real_estate'
  | 'communication_services'

// \u884c\u4e1a\u6807\u7b7e
export const SECTOR_LABELS: Record<SectorType, string> = {
  technology: '\u79d1\u6280',
  healthcare: '\u533b\u7597\u4fdd\u5065',
  financials: '\u91d1\u878d',
  consumer_discretionary: '\u53ef\u9009\u6d88\u8d39',
  consumer_staples: '\u5fc5\u9700\u6d88\u8d39',
  industrials: '\u5de5\u4e1a',
  energy: '\u80fd\u6e90',
  materials: '\u539f\u6750\u6599',
  utilities: '\u516c\u7528\u4e8b\u4e1a',
  real_estate: '\u623f\u5730\u4ea7',
  communication_services: '\u901a\u4fe1\u670d\u52a1',
}

// ============ Brinson \u5f52\u56e0 ============

// Brinson \u5f52\u56e0\u7c7b\u578b
export type BrinsonEffectType = 'allocation' | 'selection' | 'interaction'

// \u884c\u4e1a\u5f52\u56e0\u660e\u7ec6
export interface SectorAttribution {
  sector: SectorType
  sectorName: string
  portfolioWeight: number      // \u7ec4\u5408\u6743\u91cd
  benchmarkWeight: number      // \u57fa\u51c6\u6743\u91cd
  activeWeight: number         // \u4e3b\u52a8\u6743\u91cd (w_p - w_b)
  portfolioReturn: number      // \u7ec4\u5408\u6536\u76ca
  benchmarkReturn: number      // \u57fa\u51c6\u6536\u76ca
  activeReturn: number         // \u4e3b\u52a8\u6536\u76ca (R_p - R_b)
  allocationEffect: number     // \u914d\u7f6e\u6548\u5e94
  selectionEffect: number      // \u9009\u80a1\u6548\u5e94
  interactionEffect: number    // \u4ea4\u4e92\u6548\u5e94
  totalEffect: number          // \u603b\u6548\u5e94
}

// Brinson \u5f52\u56e0\u7ed3\u679c
export interface BrinsonAttribution {
  period: TimePeriod
  portfolioReturn: number      // \u7ec4\u5408\u603b\u6536\u76ca
  benchmarkReturn: number      // \u57fa\u51c6\u603b\u6536\u76ca
  excessReturn: number         // \u8d85\u989d\u6536\u76ca

  // \u603b\u6548\u5e94
  totalAllocationEffect: number
  totalSelectionEffect: number
  totalInteractionEffect: number

  // \u884c\u4e1a\u660e\u7ec6
  sectorDetails: SectorAttribution[]

  // \u89e3\u8bfb
  interpretation: string
}

// Brinson \u5f52\u56e0\u8bf7\u6c42
export interface BrinsonAttributionRequest {
  portfolioId: string
  benchmarkId: string
  startDate: string
  endDate: string
  frequency?: 'daily' | 'weekly' | 'monthly'
}

// ============ \u56e0\u5b50\u5f52\u56e0 ============

// \u98ce\u9669\u56e0\u5b50\u7c7b\u578b
export type RiskFactorType =
  | 'market'
  | 'size'
  | 'value'
  | 'momentum'
  | 'quality'
  | 'volatility'
  | 'dividend'
  | 'growth'

// \u56e0\u5b50\u6807\u7b7e
export const FACTOR_LABELS: Record<RiskFactorType, string> = {
  market: '\u5e02\u573a',
  size: '\u89c4\u6a21',
  value: '\u4ef7\u503c',
  momentum: '\u52a8\u91cf',
  quality: '\u8d28\u91cf',
  volatility: '\u6ce2\u52a8',
  dividend: '\u80a1\u606f',
  growth: '\u6210\u957f',
}

// \u56e0\u5b50\u66b4\u9732
export interface FactorExposure {
  factor: RiskFactorType
  factorName: string
  exposure: number             // \u56e0\u5b50\u66b4\u9732
  factorReturn: number         // \u56e0\u5b50\u6536\u76ca
  contribution: number         // \u6536\u76ca\u8d21\u732e
  tStat: number                // t\u7edf\u8ba1\u91cf
}

// \u56e0\u5b50\u5f52\u56e0\u7ed3\u679c
export interface FactorAttribution {
  period: TimePeriod
  totalReturn: number          // \u603b\u6536\u76ca
  benchmarkReturn: number      // \u57fa\u51c6\u6536\u76ca
  activeReturn: number         // \u8d85\u989d\u6536\u76ca

  // \u56e0\u5b50\u8d21\u732e
  factorContributions: FactorExposure[]

  // \u6c47\u603b
  totalFactorReturn: number    // \u56e0\u5b50\u603b\u6536\u76ca
  specificReturn: number       // \u7279\u8d28\u6536\u76ca (\u9009\u80a1\u80fd\u529b)

  // \u98ce\u9669\u6307\u6807
  informationRatio: number     // \u4fe1\u606f\u6bd4\u7387
  trackingError: number        // \u8ddf\u8e2a\u8bef\u5dee
  activeRisk: number           // \u4e3b\u52a8\u98ce\u9669

  // \u89e3\u8bfb
  interpretation: string
}

// \u56e0\u5b50\u5f52\u56e0\u8bf7\u6c42
export interface FactorAttributionRequest {
  portfolioId: string
  benchmarkId?: string
  startDate: string
  endDate: string
  factors?: RiskFactorType[]
}

// ============ TCA \u4ea4\u6613\u6210\u672c\u5206\u6790 ============

// \u4ea4\u6613\u6210\u672c\u7ec4\u6210
export interface TradeCostBreakdown {
  commission: number           // \u4f63\u91d1
  slippage: number             // \u6ed1\u70b9
  marketImpact: number         // \u5e02\u573a\u51b2\u51fb
  timingCost: number           // \u65f6\u673a\u6210\u672c
  opportunityCost: number      // \u673a\u4f1a\u6210\u672c
  totalCost: number            // \u603b\u6210\u672c
}

// \u5355\u7b14\u4ea4\u6613 TCA
export interface TradeTCA {
  tradeId: string
  symbol: string
  side: 'buy' | 'sell'
  quantity: number

  // \u4ef7\u683c
  decisionPrice: number        // \u51b3\u7b56\u4ef7\u683c
  arrivalPrice: number         // \u5230\u8fbe\u4ef7\u683c
  executionPrice: number       // \u6267\u884c\u4ef7\u683c
  benchmarkPrice: number       // \u57fa\u51c6\u4ef7\u683c (VWAP/TWAP)

  // \u6210\u672c
  implementationShortfall: number       // \u6267\u884c\u7f3a\u53e3
  implementationShortfallBps: number    // \u6267\u884c\u7f3a\u53e3 (\u57fa\u70b9)
  costs: TradeCostBreakdown

  // \u65f6\u95f4
  decisionTime: string
  executionTime: string
  executionDuration: number    // \u6267\u884c\u65f6\u957f (\u79d2)

  // \u5e02\u573a\u6761\u4ef6
  marketVolatility: number
  volumeParticipation: number  // \u6210\u4ea4\u91cf\u5360\u6bd4
}

// \u7b56\u7565 TCA \u6c47\u603b
export interface StrategyTCA {
  period: TimePeriod
  totalTrades: number
  totalVolume: number
  totalNotional: number

  // \u6c47\u603b\u6210\u672c
  totalCosts: TradeCostBreakdown
  avgCostBps: number           // \u5e73\u5747\u6210\u672c (\u57fa\u70b9)

  // \u6309\u65b9\u5411
  buyCosts: TradeCostBreakdown
  sellCosts: TradeCostBreakdown

  // \u6309\u65f6\u6bb5
  byTimeOfDay: {
    period: string
    avgCostBps: number
    trades: number
  }[]

  // \u6309\u80a1\u7968
  bySymbol: {
    symbol: string
    avgCostBps: number
    trades: number
    totalNotional: number
  }[]

  // \u57fa\u51c6\u5bf9\u6bd4
  vsBenchmark: {
    vwapSlippage: number
    twapSlippage: number
    arrivalSlippage: number
  }

  trades: TradeTCA[]
}

// TCA \u8bf7\u6c42
export interface TCARequest {
  portfolioId?: string
  strategyId?: string
  startDate: string
  endDate: string
  symbols?: string[]
  benchmark?: 'vwap' | 'twap' | 'arrival'
}

// ============ \u7efc\u5408\u5f52\u56e0\u62a5\u544a ============

// \u5f52\u56e0\u62a5\u544a\u7c7b\u578b
export type AttributionReportType = 'brinson' | 'factor' | 'tca' | 'comprehensive'

// \u7efc\u5408\u5f52\u56e0\u62a5\u544a
export interface ComprehensiveAttribution {
  period: TimePeriod
  portfolioId: string
  portfolioName: string
  benchmarkId: string
  benchmarkName: string

  // \u6536\u76ca\u6982\u89c8
  summary: {
    portfolioReturn: number
    benchmarkReturn: number
    excessReturn: number
    informationRatio: number
    trackingError: number
    sharpeRatio: number
    maxDrawdown: number
  }

  // Brinson \u5f52\u56e0
  brinson: BrinsonAttribution

  // \u56e0\u5b50\u5f52\u56e0
  factor: FactorAttribution

  // TCA
  tca: StrategyTCA

  // \u65f6\u5e8f\u6570\u636e
  timeSeries: {
    dates: string[]
    portfolioValues: number[]
    benchmarkValues: number[]
    excessReturns: number[]
    drawdowns: number[]
  }

  // \u62a5\u544a\u751f\u6210\u65f6\u95f4
  generatedAt: string
}

// \u62a5\u544a\u5bfc\u51fa\u683c\u5f0f
export type ReportFormat = 'pdf' | 'excel' | 'json'

// \u62a5\u544a\u5bfc\u51fa\u8bf7\u6c42
export interface ExportReportRequest {
  reportType: AttributionReportType
  portfolioId: string
  startDate: string
  endDate: string
  format: ReportFormat
  includeCharts?: boolean
  language?: 'zh' | 'en'
}

// ============ \u56fe\u8868\u6570\u636e ============

// \u6536\u76ca\u5206\u89e3\u56fe
export interface ReturnDecompositionChart {
  labels: string[]
  values: number[]
  colors: string[]
}

// \u5f52\u56e0\u65f6\u5e8f\u56fe
export interface AttributionTimeSeriesChart {
  dates: string[]
  allocation: number[]
  selection: number[]
  interaction: number[]
  total: number[]
}

// \u56e0\u5b50\u8d21\u732e\u56fe
export interface FactorContributionChart {
  factors: string[]
  contributions: number[]
  exposures: number[]
}

// TCA \u6210\u672c\u5206\u89e3\u56fe
export interface TCABreakdownChart {
  categories: string[]
  costs: number[]
}

// ============ \u7ec4\u4ef6\u72b6\u6001 ============

// \u5f52\u56e0\u9875\u9762\u72b6\u6001
export interface AttributionPageState {
  selectedReport: AttributionReportType
  period: TimePeriod
  portfolioId: string | null
  benchmarkId: string | null
  brinson: BrinsonAttribution | null
  factor: FactorAttribution | null
  tca: StrategyTCA | null
  isLoading: boolean
  error: string | null
}

// \u9ed8\u8ba4\u65f6\u95f4\u6bb5 (\u8fc7\u53bb1\u5e74)
export const DEFAULT_PERIOD: TimePeriod = {
  start: new Date(Date.now() - 365 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
  end: new Date().toISOString().split('T')[0],
}
