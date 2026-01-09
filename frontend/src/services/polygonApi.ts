/**
 * Polygon.io REST API 服务
 * Sprint 7: T7 - 历史数据 API
 *
 * 提供历史 K 线、快照、技术指标等数据
 */

// API 配置
const POLYGON_BASE_URL = 'https://api.polygon.io'
const API_KEY = import.meta.env.VITE_POLYGON_API_KEY || 'demo'

// 时间跨度类型
export type Timespan = 'second' | 'minute' | 'hour' | 'day' | 'week' | 'month' | 'quarter' | 'year'

// K 线数据
export interface AggregateBar {
  o: number   // 开盘价
  h: number   // 最高价
  l: number   // 最低价
  c: number   // 收盘价
  v: number   // 成交量
  vw: number  // 成交量加权平均价
  t: number   // 时间戳 (毫秒)
  n: number   // 交易笔数
}

// 聚合响应
export interface AggregatesResponse {
  ticker: string
  adjusted: boolean
  queryCount: number
  resultsCount: number
  status: string
  request_id: string
  results: AggregateBar[]
}

// 股票快照
export interface TickerSnapshot {
  ticker: string
  todaysChange: number
  todaysChangePerc: number
  updated: number
  day: {
    o: number
    h: number
    l: number
    c: number
    v: number
    vw: number
  }
  min: {
    av: number
    t: number
    n: number
    o: number
    h: number
    l: number
    c: number
    v: number
    vw: number
  }
  prevDay: {
    o: number
    h: number
    l: number
    c: number
    v: number
    vw: number
  }
}

// 快照响应
export interface SnapshotResponse {
  status: string
  request_id: string
  tickers: TickerSnapshot[]
}

// 股票详情
export interface TickerDetails {
  ticker: string
  name: string
  market: string
  locale: string
  type: string
  currency_name: string
  active: boolean
  cik?: string
  composite_figi?: string
  share_class_figi?: string
  market_cap?: number
  phone_number?: string
  address?: {
    address1?: string
    city?: string
    state?: string
    postal_code?: string
  }
  description?: string
  homepage_url?: string
  total_employees?: number
  list_date?: string
  branding?: {
    icon_url?: string
    logo_url?: string
  }
  share_class_shares_outstanding?: number
  weighted_shares_outstanding?: number
}

// 技术指标 - SMA
export interface SMAResult {
  timestamp: number
  value: number
}

export interface SMAResponse {
  status: string
  request_id: string
  results: {
    values: SMAResult[]
    underlying: {
      aggregates: AggregateBar[]
    }
  }
}

// 技术指标 - RSI
export interface RSIResult {
  timestamp: number
  value: number
}

export interface RSIResponse {
  status: string
  request_id: string
  results: {
    values: RSIResult[]
    underlying: {
      aggregates: AggregateBar[]
    }
  }
}

// 技术指标 - MACD
export interface MACDResult {
  timestamp: number
  value: number
  signal: number
  histogram: number
}

export interface MACDResponse {
  status: string
  request_id: string
  results: {
    values: MACDResult[]
    underlying: {
      aggregates: AggregateBar[]
    }
  }
}

/**
 * Polygon REST API 服务类
 */
class PolygonApiService {
  private baseUrl: string
  private apiKey: string

  constructor(apiKey?: string) {
    this.baseUrl = POLYGON_BASE_URL
    this.apiKey = apiKey || API_KEY
  }

  /**
   * 发送 GET 请求
   */
  private async get<T>(endpoint: string, params: Record<string, string | number | boolean> = {}): Promise<T> {
    const url = new URL(`${this.baseUrl}${endpoint}`)

    // 添加 API Key
    url.searchParams.set('apiKey', this.apiKey)

    // 添加其他参数
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        url.searchParams.set(key, String(value))
      }
    })

    const response = await fetch(url.toString())

    if (!response.ok) {
      const error = await response.json().catch(() => ({}))
      throw new Error(error.message || `HTTP ${response.status}`)
    }

    return response.json()
  }

  /**
   * 获取历史 K 线数据
   *
   * @param ticker 股票代码
   * @param multiplier 时间倍数 (e.g., 1, 5, 15)
   * @param timespan 时间跨度 (minute, hour, day, etc.)
   * @param from 开始日期 (YYYY-MM-DD)
   * @param to 结束日期 (YYYY-MM-DD)
   * @param options 额外选项
   */
  async getAggregates(
    ticker: string,
    multiplier: number,
    timespan: Timespan,
    from: string,
    to: string,
    options: {
      adjusted?: boolean
      sort?: 'asc' | 'desc'
      limit?: number
    } = {}
  ): Promise<AggregatesResponse> {
    const { adjusted = true, sort = 'asc', limit = 5000 } = options

    return this.get<AggregatesResponse>(
      `/v2/aggs/ticker/${ticker}/range/${multiplier}/${timespan}/${from}/${to}`,
      { adjusted, sort, limit }
    )
  }

  /**
   * 获取日 K 线 (快捷方法)
   */
  async getDailyBars(
    ticker: string,
    from: string,
    to: string,
    options: { adjusted?: boolean; limit?: number } = {}
  ): Promise<AggregatesResponse> {
    return this.getAggregates(ticker, 1, 'day', from, to, options)
  }

  /**
   * 获取分钟 K 线 (快捷方法)
   */
  async getMinuteBars(
    ticker: string,
    from: string,
    to: string,
    multiplier: number = 1,
    options: { adjusted?: boolean; limit?: number } = {}
  ): Promise<AggregatesResponse> {
    return this.getAggregates(ticker, multiplier, 'minute', from, to, options)
  }

  /**
   * 获取单个股票快照
   */
  async getSnapshot(ticker: string): Promise<TickerSnapshot> {
    const response = await this.get<{ ticker: TickerSnapshot }>(
      `/v2/snapshot/locale/us/markets/stocks/tickers/${ticker}`
    )
    return response.ticker
  }

  /**
   * 获取多个股票快照
   */
  async getSnapshots(tickers: string[]): Promise<TickerSnapshot[]> {
    const response = await this.get<SnapshotResponse>(
      `/v2/snapshot/locale/us/markets/stocks/tickers`,
      { tickers: tickers.join(',') }
    )
    return response.tickers
  }

  /**
   * 获取所有股票快照 (涨幅榜/跌幅榜)
   */
  async getAllSnapshots(direction: 'gainers' | 'losers' = 'gainers'): Promise<TickerSnapshot[]> {
    const response = await this.get<SnapshotResponse>(
      `/v2/snapshot/locale/us/markets/stocks/${direction}`
    )
    return response.tickers
  }

  /**
   * 获取股票详情
   */
  async getTickerDetails(ticker: string): Promise<TickerDetails> {
    const response = await this.get<{ results: TickerDetails }>(
      `/v3/reference/tickers/${ticker}`
    )
    return response.results
  }

  /**
   * 搜索股票
   */
  async searchTickers(
    query: string,
    options: {
      market?: 'stocks' | 'crypto' | 'fx'
      active?: boolean
      limit?: number
    } = {}
  ): Promise<TickerDetails[]> {
    const { market = 'stocks', active = true, limit = 20 } = options

    const response = await this.get<{ results: TickerDetails[] }>(
      '/v3/reference/tickers',
      { search: query, market, active, limit }
    )
    return response.results || []
  }

  /**
   * 获取 SMA (简单移动平均)
   */
  async getSMA(
    ticker: string,
    options: {
      timespan?: Timespan
      window?: number
      series_type?: 'close' | 'open' | 'high' | 'low'
      order?: 'asc' | 'desc'
      limit?: number
    } = {}
  ): Promise<SMAResponse> {
    const {
      timespan = 'day',
      window = 20,
      series_type = 'close',
      order = 'desc',
      limit = 100,
    } = options

    return this.get<SMAResponse>(
      `/v1/indicators/sma/${ticker}`,
      { timespan, window, series_type, order, limit }
    )
  }

  /**
   * 获取 RSI (相对强弱指数)
   */
  async getRSI(
    ticker: string,
    options: {
      timespan?: Timespan
      window?: number
      series_type?: 'close' | 'open' | 'high' | 'low'
      order?: 'asc' | 'desc'
      limit?: number
    } = {}
  ): Promise<RSIResponse> {
    const {
      timespan = 'day',
      window = 14,
      series_type = 'close',
      order = 'desc',
      limit = 100,
    } = options

    return this.get<RSIResponse>(
      `/v1/indicators/rsi/${ticker}`,
      { timespan, window, series_type, order, limit }
    )
  }

  /**
   * 获取 MACD
   */
  async getMACD(
    ticker: string,
    options: {
      timespan?: Timespan
      short_window?: number
      long_window?: number
      signal_window?: number
      series_type?: 'close' | 'open' | 'high' | 'low'
      order?: 'asc' | 'desc'
      limit?: number
    } = {}
  ): Promise<MACDResponse> {
    const {
      timespan = 'day',
      short_window = 12,
      long_window = 26,
      signal_window = 9,
      series_type = 'close',
      order = 'desc',
      limit = 100,
    } = options

    return this.get<MACDResponse>(
      `/v1/indicators/macd/${ticker}`,
      { timespan, short_window, long_window, signal_window, series_type, order, limit }
    )
  }

  /**
   * 获取前一交易日数据
   */
  async getPreviousClose(ticker: string): Promise<AggregateBar | null> {
    const response = await this.get<{ results: AggregateBar[] }>(
      `/v2/aggs/ticker/${ticker}/prev`
    )
    return response.results?.[0] || null
  }

  /**
   * 获取分组日 K 线 (多股票)
   */
  async getGroupedDaily(date: string): Promise<AggregatesResponse> {
    return this.get<AggregatesResponse>(
      `/v2/aggs/grouped/locale/us/market/stocks/${date}`,
      { adjusted: true }
    )
  }
}

// 默认实例
export const polygonApi = new PolygonApiService()

// 导出类以支持自定义实例
export default PolygonApiService
