/**
 * Phase 11: \u6570\u636e\u5c42\u5347\u7ea7 - \u5e02\u573a\u6570\u636e\u7c7b\u578b\u5b9a\u4e49
 *
 * \u5305\u542b:
 * - \u5206\u949f\u7ea7 K \u7ebf\u6570\u636e
 * - \u5b9e\u65f6\u884c\u60c5
 * - \u65e5\u5185\u56e0\u5b50
 * - \u6570\u636e\u6e90\u914d\u7f6e
 */

// ============ \u6570\u636e\u6e90\u7c7b\u578b ============

/** \u6570\u636e\u6e90\u7c7b\u578b */
export type DataSource = 'polygon' | 'alpaca' | 'iex' | 'yahoo'

/** \u6570\u636e\u9891\u7387 */
export type DataFrequency = '1min' | '5min' | '15min' | '30min' | '1hour' | '1day'

/** \u6570\u636e\u6e90\u72b6\u6001 */
export type DataSourceStatus = 'connected' | 'disconnected' | 'error' | 'rate_limited'

/** \u6570\u636e\u6e90\u914d\u7f6e */
export interface DataSourceConfig {
  source: DataSource
  apiKey?: string
  baseUrl?: string
  wsUrl?: string
  rateLimit: number  // \u6bcf\u5206\u949f\u8bf7\u6c42\u6570
  priority: number   // \u4f18\u5148\u7ea7 (\u8d8a\u5c0f\u8d8a\u9ad8)
  capabilities: {
    realtime: boolean
    historical: boolean
    intraday: boolean
    fundamentals: boolean
  }
}

/** \u6570\u636e\u6e90\u72b6\u6001\u4fe1\u606f */
export interface DataSourceInfo {
  source: DataSource
  status: DataSourceStatus
  lastSync: string | null
  requestsToday: number
  requestsLimit: number
  latencyMs: number
  errorMessage?: string
}

// ============ K\u7ebf\u6570\u636e\u7c7b\u578b ============

/** OHLCV K\u7ebf\u6570\u636e */
export interface OHLCVBar {
  symbol: string
  timestamp: string        // ISO 8601
  open: number
  high: number
  low: number
  close: number
  volume: number
  vwap?: number           // \u6210\u4ea4\u91cf\u52a0\u6743\u5e73\u5747\u4ef7
  trades?: number         // \u6210\u4ea4\u7b14\u6570
}

/** \u5206\u949f\u7ea7K\u7ebf (\u5e26\u989d\u5916\u5b57\u6bb5) */
export interface MinuteBar extends OHLCVBar {
  frequency: DataFrequency
  preMarket?: boolean     // \u662f\u5426\u76d8\u524d\u4ea4\u6613
  afterHours?: boolean    // \u662f\u5426\u76d8\u540e\u4ea4\u6613

  // \u65e5\u5185\u7edf\u8ba1
  dayOpen?: number        // \u5f53\u65e5\u5f00\u76d8\u4ef7
  dayHigh?: number        // \u5f53\u65e5\u6700\u9ad8
  dayLow?: number         // \u5f53\u65e5\u6700\u4f4e
  dayVolume?: number      // \u5f53\u65e5\u7d2f\u8ba1\u6210\u4ea4\u91cf
}

/** \u65e5\u7ebf\u6570\u636e */
export interface DailyBar extends OHLCVBar {
  adjClose?: number       // \u590d\u6743\u6536\u76d8\u4ef7
  dividend?: number       // \u5f53\u65e5\u80a1\u606f
  split?: number          // \u62c6\u80a1\u6bd4\u4f8b
}

// ============ \u5b9e\u65f6\u884c\u60c5\u7c7b\u578b ============

/** \u5b9e\u65f6\u62a5\u4ef7 */
export interface Quote {
  symbol: string
  timestamp: string
  bidPrice: number
  bidSize: number
  askPrice: number
  askSize: number
  lastPrice: number
  lastSize: number
  volume: number
}

/** \u5b9e\u65f6\u6210\u4ea4 */
export interface Trade {
  symbol: string
  timestamp: string
  price: number
  size: number
  exchange: string
  conditions?: string[]
}

/** Tick \u6570\u636e */
export interface TickData {
  symbol: string
  timestamp: string
  type: 'quote' | 'trade'
  data: Quote | Trade
}

/** \u5b9e\u65f6\u884c\u60c5\u5feb\u7167 */
export interface MarketSnapshot {
  symbol: string
  timestamp: string

  // \u4ef7\u683c
  lastPrice: number
  change: number
  changePercent: number

  // \u5f53\u65e5\u7edf\u8ba1
  open: number
  high: number
  low: number
  close: number
  previousClose: number
  volume: number

  // \u62a5\u4ef7
  bidPrice: number
  bidSize: number
  askPrice: number
  askSize: number

  // \u884d\u751f\u6307\u6807
  vwap?: number
  averageVolume?: number   // 20\u65e5\u5e73\u5747\u6210\u4ea4\u91cf
  relativeVolume?: number  // \u76f8\u5bf9\u6210\u4ea4\u91cf
}

// ============ \u65e5\u5185\u56e0\u5b50\u7c7b\u578b ============

/** \u65e5\u5185\u56e0\u5b50\u7c7b\u578b */
export type IntradayFactorType =
  | 'relative_volume'      // \u76f8\u5bf9\u6210\u4ea4\u91cf
  | 'vwap_deviation'       // VWAP\u504f\u79bb
  | 'buy_pressure'         // \u4e70\u538b
  | 'price_momentum_5min'  // 5\u5206\u949f\u52a8\u91cf
  | 'price_momentum_15min' // 15\u5206\u949f\u52a8\u91cf
  | 'intraday_volatility'  // \u65e5\u5185\u6ce2\u52a8
  | 'spread_ratio'         // \u4e70\u5356\u4ef7\u5dee\u6bd4
  | 'order_imbalance'      // \u8ba2\u5355\u4e0d\u5e73\u8861

/** \u65e5\u5185\u56e0\u5b50\u5b9a\u4e49 */
export interface IntradayFactorDefinition {
  id: IntradayFactorType
  name: string
  description: string
  expression: string
  interpretation: string
  lookbackPeriod: number   // \u56de\u770b\u5468\u671f (\u5206\u949f)
  updateFrequency: DataFrequency
}

/** \u65e5\u5185\u56e0\u5b50\u503c */
export interface IntradayFactorValue {
  symbol: string
  timestamp: string
  factorId: IntradayFactorType
  value: number
  zscore?: number          // \u6807\u51c6\u5316\u503c
  percentile?: number      // \u767e\u5206\u4f4d
}

/** \u65e5\u5185\u56e0\u5b50\u5feb\u7167 */
export interface IntradayFactorSnapshot {
  symbol: string
  timestamp: string
  factors: Record<IntradayFactorType, number>
}

/** \u9884\u7f6e\u65e5\u5185\u56e0\u5b50\u5b9a\u4e49 */
export const INTRADAY_FACTORS: IntradayFactorDefinition[] = [
  {
    id: 'relative_volume',
    name: '\u76f8\u5bf9\u6210\u4ea4\u91cf',
    description: '\u5f53\u524d10\u5206\u949f\u6210\u4ea4\u91cf / \u8fc7\u53bb20\u5929\u540c\u65f6\u6bb5\u5e73\u5747\u6210\u4ea4\u91cf',
    expression: 'volume_10min / avg(volume_10min, 20)',
    interpretation: '>2.0 \u663e\u8457\u653e\u91cf, <0.5 \u663e\u8457\u7f29\u91cf',
    lookbackPeriod: 10,
    updateFrequency: '1min',
  },
  {
    id: 'vwap_deviation',
    name: 'VWAP\u504f\u79bb',
    description: '\u5f53\u524d\u4ef7\u683c\u76f8\u5bf9VWAP\u7684\u504f\u79bb\u7a0b\u5ea6',
    expression: '(close - vwap) / vwap',
    interpretation: '>0 \u4e70\u538b\u5f3a, <0 \u5356\u538b\u5f3a',
    lookbackPeriod: 0,
    updateFrequency: '1min',
  },
  {
    id: 'buy_pressure',
    name: '\u4e70\u5356\u538b\u529b',
    description: '\u4e3b\u52a8\u4e70\u5165\u91cf\u5360\u6bd4',
    expression: 'buy_volume / (buy_volume + sell_volume)',
    interpretation: '>0.6 \u4e70\u538b\u5f3a, <0.4 \u5356\u538b\u5f3a',
    lookbackPeriod: 10,
    updateFrequency: '1min',
  },
  {
    id: 'price_momentum_5min',
    name: '5\u5206\u949f\u52a8\u91cf',
    description: '5\u5206\u949f\u4ef7\u683c\u53d8\u5316\u7387',
    expression: 'close / delay(close, 5) - 1',
    interpretation: '\u6b63\u503c\u8868\u793a\u4e0a\u6da8\u52a8\u91cf',
    lookbackPeriod: 5,
    updateFrequency: '1min',
  },
  {
    id: 'price_momentum_15min',
    name: '15\u5206\u949f\u52a8\u91cf',
    description: '15\u5206\u949f\u4ef7\u683c\u53d8\u5316\u7387',
    expression: 'close / delay(close, 15) - 1',
    interpretation: '\u6b63\u503c\u8868\u793a\u4e0a\u6da8\u52a8\u91cf',
    lookbackPeriod: 15,
    updateFrequency: '1min',
  },
  {
    id: 'intraday_volatility',
    name: '\u65e5\u5185\u6ce2\u52a8',
    description: '\u5f53\u65e5\u4ef7\u683c\u6ce2\u52a8\u7387',
    expression: 'std(returns_1min, today) * sqrt(390)',
    interpretation: '\u5e74\u5316\u65e5\u5185\u6ce2\u52a8\u7387',
    lookbackPeriod: 390,
    updateFrequency: '5min',
  },
  {
    id: 'spread_ratio',
    name: '\u4e70\u5356\u4ef7\u5dee\u6bd4',
    description: '\u4e70\u5356\u4ef7\u5dee\u5360\u4e2d\u95f4\u4ef7\u6bd4\u4f8b',
    expression: '(ask - bid) / ((ask + bid) / 2)',
    interpretation: '\u8d8a\u5927\u8868\u793a\u6d41\u52a8\u6027\u8d8a\u5dee',
    lookbackPeriod: 0,
    updateFrequency: '1min',
  },
  {
    id: 'order_imbalance',
    name: '\u8ba2\u5355\u4e0d\u5e73\u8861',
    description: '\u4e70\u5356\u76d8\u53e3\u4e0d\u5e73\u8861\u5ea6',
    expression: '(bid_size - ask_size) / (bid_size + ask_size)',
    interpretation: '>0 \u4e70\u76d8\u5f3a, <0 \u5356\u76d8\u5f3a',
    lookbackPeriod: 0,
    updateFrequency: '1min',
  },
]

// ============ \u6570\u636e\u8bf7\u6c42/\u54cd\u5e94\u7c7b\u578b ============

/** \u5386\u53f2\u6570\u636e\u8bf7\u6c42 */
export interface HistoricalDataRequest {
  symbols: string[]
  frequency: DataFrequency
  startDate: string
  endDate: string
  adjustedPrice?: boolean  // \u662f\u5426\u590d\u6743
  includePrePost?: boolean // \u5305\u542b\u76d8\u524d\u76d8\u540e
}

/** \u5386\u53f2\u6570\u636e\u54cd\u5e94 */
export interface HistoricalDataResponse {
  symbol: string
  frequency: DataFrequency
  bars: OHLCVBar[]
  totalCount: number
  dataSource: DataSource
}

/** \u5b9e\u65f6\u8ba2\u9605\u8bf7\u6c42 */
export interface StreamSubscription {
  symbols: string[]
  dataTypes: ('quotes' | 'trades' | 'bars')[]
  frequency?: DataFrequency
}

/** \u6570\u636e\u540c\u6b65\u72b6\u6001 */
export interface DataSyncStatus {
  symbol: string
  lastSyncTime: string
  oldestData: string
  newestData: string
  totalBars: number
  frequency: DataFrequency
  status: 'synced' | 'syncing' | 'error' | 'stale'
  progress?: number
}

// ============ \u6570\u636e\u8d28\u91cf\u7c7b\u578b ============

/** \u6570\u636e\u8d28\u91cf\u95ee\u9898\u7c7b\u578b */
export type DataQualityIssueType =
  | 'missing_data'      // \u7f3a\u5931\u6570\u636e
  | 'outlier'           // \u5f02\u5e38\u503c
  | 'stale_data'        // \u8fc7\u65f6\u6570\u636e
  | 'invalid_ohlc'      // \u65e0\u6548OHLC
  | 'zero_volume'       // \u96f6\u6210\u4ea4\u91cf
  | 'price_gap'         // \u4ef7\u683c\u8df3\u7a7a
  | 'duplicate'         // \u91cd\u590d\u6570\u636e

/** \u6570\u636e\u8d28\u91cf\u95ee\u9898 */
export interface DataQualityIssue {
  id: string
  symbol: string
  timestamp: string
  issueType: DataQualityIssueType
  severity: 'low' | 'medium' | 'high'
  description: string
  affectedFields: string[]
  resolved: boolean
  resolvedAt?: string
}

/** \u6570\u636e\u8d28\u91cf\u62a5\u544a */
export interface DataQualityReport {
  reportDate: string
  symbolsChecked: number
  barsChecked: number
  issuesFound: number
  issuesByType: Record<DataQualityIssueType, number>
  issuesBySeverity: {
    low: number
    medium: number
    high: number
  }
  overallScore: number  // 0-100
  issues: DataQualityIssue[]
}

// ============ \u914d\u7f6e\u5e38\u91cf ============

/** \u6570\u636e\u6e90\u914d\u7f6e\u9884\u8bbe */
export const DATA_SOURCE_CONFIGS: Record<DataSource, Omit<DataSourceConfig, 'apiKey'>> = {
  polygon: {
    source: 'polygon',
    baseUrl: 'https://api.polygon.io',
    wsUrl: 'wss://socket.polygon.io',
    rateLimit: 100,
    priority: 1,
    capabilities: {
      realtime: true,
      historical: true,
      intraday: true,
      fundamentals: true,
    },
  },
  alpaca: {
    source: 'alpaca',
    baseUrl: 'https://data.alpaca.markets',
    wsUrl: 'wss://stream.data.alpaca.markets',
    rateLimit: 200,
    priority: 2,
    capabilities: {
      realtime: true,
      historical: true,
      intraday: true,
      fundamentals: false,
    },
  },
  iex: {
    source: 'iex',
    baseUrl: 'https://cloud.iexapis.com',
    wsUrl: 'wss://cloud-sse.iexapis.com',
    rateLimit: 100,
    priority: 3,
    capabilities: {
      realtime: false,  // 15\u5206\u949f\u5ef6\u8fdf
      historical: true,
      intraday: true,
      fundamentals: true,
    },
  },
  yahoo: {
    source: 'yahoo',
    baseUrl: 'https://query1.finance.yahoo.com',
    rateLimit: 60,
    priority: 4,
    capabilities: {
      realtime: false,
      historical: true,
      intraday: false,
      fundamentals: true,
    },
  },
}

/** \u6570\u636e\u9891\u7387\u6807\u7b7e */
export const FREQUENCY_LABELS: Record<DataFrequency, string> = {
  '1min': '1\u5206\u949f',
  '5min': '5\u5206\u949f',
  '15min': '15\u5206\u949f',
  '30min': '30\u5206\u949f',
  '1hour': '1\u5c0f\u65f6',
  '1day': '\u65e5\u7ebf',
}

/** \u6570\u636e\u6e90\u6807\u7b7e */
export const DATA_SOURCE_LABELS: Record<DataSource, string> = {
  polygon: 'Polygon.io',
  alpaca: 'Alpaca',
  iex: 'IEX Cloud',
  yahoo: 'Yahoo Finance',
}

/** \u6570\u636e\u8d28\u91cf\u95ee\u9898\u6807\u7b7e */
export const DATA_QUALITY_ISSUE_LABELS: Record<DataQualityIssueType, string> = {
  missing_data: '\u7f3a\u5931\u6570\u636e',
  outlier: '\u5f02\u5e38\u503c',
  stale_data: '\u8fc7\u65f6\u6570\u636e',
  invalid_ohlc: '\u65e0\u6548OHLC',
  zero_volume: '\u96f6\u6210\u4ea4\u91cf',
  price_gap: '\u4ef7\u683c\u8df3\u7a7a',
  duplicate: '\u91cd\u590d\u6570\u636e',
}
