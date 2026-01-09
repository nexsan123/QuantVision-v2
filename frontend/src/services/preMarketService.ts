/**
 * 盘前扫描器数据服务
 * Sprint 7: T8 - 盘前扫描器数据源
 *
 * 集成 Polygon.io 数据用于盘前扫描
 */
import { polygonApi, type TickerSnapshot, type AggregateBar } from './polygonApi'

// 扫描器股票数据
export interface ScannerStock {
  symbol: string
  name: string
  price: number
  change: number
  changePercent: number
  volume: number
  avgVolume: number       // 平均成交量
  relativeVolume: number  // 相对成交量
  preMarketPrice: number
  preMarketChange: number
  preMarketChangePercent: number
  preMarketVolume: number
  gap: number             // 缺口
  gapPercent: number
  float?: number          // 流通股
  marketCap?: number
  high: number
  low: number
  prevClose: number
  sector?: string
  industry?: string
  // 技术指标
  rsi14?: number
  sma20?: number
  sma50?: number
  vwap?: number
  atr?: number
  // 附加信息
  hasNews: boolean
  hasEarnings: boolean
  timestamp: number
}

// 扫描过滤条件
export interface ScannerFilters {
  minPrice?: number
  maxPrice?: number
  minVolume?: number
  minRelativeVolume?: number
  minChange?: number
  maxChange?: number
  minGap?: number
  maxGap?: number
  minMarketCap?: number
  maxMarketCap?: number
  sectors?: string[]
}

// 扫描排序
export type ScannerSort = 'change' | 'volume' | 'relativeVolume' | 'gap' | 'price'

// 扫描结果
export interface ScannerResult {
  stocks: ScannerStock[]
  lastUpdate: number
  marketStatus: 'pre' | 'open' | 'after' | 'closed'
}

/**
 * 盘前扫描器服务类
 */
class PreMarketService {
  private cache: Map<string, { data: ScannerStock; timestamp: number }> = new Map()
  private cacheTimeout = 30000 // 30秒缓存

  /**
   * 获取市场状态
   */
  getMarketStatus(): 'pre' | 'open' | 'after' | 'closed' {
    const now = new Date()
    const nyTime = new Date(now.toLocaleString('en-US', { timeZone: 'America/New_York' }))
    const hours = nyTime.getHours()
    const minutes = nyTime.getMinutes()
    const day = nyTime.getDay()

    // 周末
    if (day === 0 || day === 6) {
      return 'closed'
    }

    const timeInMinutes = hours * 60 + minutes

    // 盘前: 4:00 - 9:30
    if (timeInMinutes >= 240 && timeInMinutes < 570) {
      return 'pre'
    }

    // 常规交易: 9:30 - 16:00
    if (timeInMinutes >= 570 && timeInMinutes < 960) {
      return 'open'
    }

    // 盘后: 16:00 - 20:00
    if (timeInMinutes >= 960 && timeInMinutes < 1200) {
      return 'after'
    }

    return 'closed'
  }

  /**
   * 获取涨幅榜
   */
  async getGainers(limit: number = 20): Promise<ScannerStock[]> {
    try {
      const snapshots = await polygonApi.getAllSnapshots('gainers')
      return this.transformSnapshots(snapshots.slice(0, limit))
    } catch (error) {
      console.error('[PreMarketService] Failed to get gainers:', error)
      return []
    }
  }

  /**
   * 获取跌幅榜
   */
  async getLosers(limit: number = 20): Promise<ScannerStock[]> {
    try {
      const snapshots = await polygonApi.getAllSnapshots('losers')
      return this.transformSnapshots(snapshots.slice(0, limit))
    } catch (error) {
      console.error('[PreMarketService] Failed to get losers:', error)
      return []
    }
  }

  /**
   * 获取指定股票列表的快照
   */
  async getStocksData(symbols: string[]): Promise<ScannerStock[]> {
    try {
      const snapshots = await polygonApi.getSnapshots(symbols)
      return this.transformSnapshots(snapshots)
    } catch (error) {
      console.error('[PreMarketService] Failed to get stocks data:', error)
      return []
    }
  }

  /**
   * 扫描盘前股票
   */
  async scanPreMarket(
    filters: ScannerFilters = {},
    sort: ScannerSort = 'change',
    limit: number = 50
  ): Promise<ScannerResult> {
    const marketStatus = this.getMarketStatus()

    try {
      // 获取涨幅榜和跌幅榜
      const [gainers, losers] = await Promise.all([
        this.getGainers(100),
        this.getLosers(100),
      ])

      // 合并并去重
      const allStocks = [...gainers, ...losers]
      const uniqueStocks = Array.from(
        new Map(allStocks.map(s => [s.symbol, s])).values()
      )

      // 应用过滤器
      let filtered = this.applyFilters(uniqueStocks, filters)

      // 排序
      filtered = this.sortStocks(filtered, sort)

      // 限制数量
      filtered = filtered.slice(0, limit)

      return {
        stocks: filtered,
        lastUpdate: Date.now(),
        marketStatus,
      }
    } catch (error) {
      console.error('[PreMarketService] Scan failed:', error)
      return {
        stocks: [],
        lastUpdate: Date.now(),
        marketStatus,
      }
    }
  }

  /**
   * 获取单个股票详细数据
   */
  async getStockDetail(symbol: string): Promise<ScannerStock | null> {
    // 检查缓存
    const cached = this.cache.get(symbol)
    if (cached && Date.now() - cached.timestamp < this.cacheTimeout) {
      return cached.data
    }

    try {
      const [snapshot, details] = await Promise.all([
        polygonApi.getSnapshot(symbol),
        polygonApi.getTickerDetails(symbol).catch(() => null),
      ])

      const stock = this.transformSnapshot(snapshot, details)

      // 更新缓存
      this.cache.set(symbol, { data: stock, timestamp: Date.now() })

      return stock
    } catch (error) {
      console.error(`[PreMarketService] Failed to get ${symbol}:`, error)
      return null
    }
  }

  /**
   * 获取历史数据用于计算指标
   */
  async getHistoricalData(
    symbol: string,
    days: number = 20
  ): Promise<AggregateBar[]> {
    const to = new Date().toISOString().split('T')[0]
    const from = new Date(Date.now() - days * 24 * 60 * 60 * 1000)
      .toISOString()
      .split('T')[0]

    try {
      const response = await polygonApi.getDailyBars(symbol, from, to)
      return response.results || []
    } catch (error) {
      console.error(`[PreMarketService] Failed to get history for ${symbol}:`, error)
      return []
    }
  }

  /**
   * 计算相对成交量
   */
  async calculateRelativeVolume(
    symbol: string,
    currentVolume: number
  ): Promise<number> {
    const bars = await this.getHistoricalData(symbol, 20)
    if (bars.length === 0) return 1

    const avgVolume = bars.reduce((sum, bar) => sum + bar.v, 0) / bars.length
    return avgVolume > 0 ? currentVolume / avgVolume : 1
  }

  /**
   * 转换快照数据
   */
  private transformSnapshots(
    snapshots: TickerSnapshot[],
  ): ScannerStock[] {
    return snapshots.map(s => this.transformSnapshot(s))
  }

  /**
   * 转换单个快照
   */
  private transformSnapshot(
    snapshot: TickerSnapshot,
    details?: { name?: string; market_cap?: number } | null
  ): ScannerStock {
    const prevClose = snapshot.prevDay?.c || 0
    const currentPrice = snapshot.day?.c || snapshot.min?.c || prevClose
    const change = currentPrice - prevClose
    const changePercent = prevClose > 0 ? (change / prevClose) * 100 : 0

    // 计算缺口 (开盘价相对昨收的差距)
    const openPrice = snapshot.day?.o || currentPrice
    const gap = openPrice - prevClose
    const gapPercent = prevClose > 0 ? (gap / prevClose) * 100 : 0

    return {
      symbol: snapshot.ticker,
      name: details?.name || snapshot.ticker,
      price: currentPrice,
      change,
      changePercent,
      volume: snapshot.day?.v || 0,
      avgVolume: 0, // 需要额外计算
      relativeVolume: 1, // 需要额外计算
      preMarketPrice: snapshot.min?.c || currentPrice,
      preMarketChange: change,
      preMarketChangePercent: changePercent,
      preMarketVolume: snapshot.min?.v || 0,
      gap,
      gapPercent,
      marketCap: details?.market_cap,
      high: snapshot.day?.h || currentPrice,
      low: snapshot.day?.l || currentPrice,
      prevClose,
      vwap: snapshot.day?.vw || snapshot.min?.vw,
      hasNews: false, // 需要新闻 API
      hasEarnings: false, // 需要财报日历 API
      timestamp: snapshot.updated || Date.now(),
    }
  }

  /**
   * 应用过滤器
   */
  private applyFilters(stocks: ScannerStock[], filters: ScannerFilters): ScannerStock[] {
    return stocks.filter(stock => {
      // 价格过滤
      if (filters.minPrice !== undefined && stock.price < filters.minPrice) return false
      if (filters.maxPrice !== undefined && stock.price > filters.maxPrice) return false

      // 成交量过滤
      if (filters.minVolume !== undefined && stock.volume < filters.minVolume) return false

      // 相对成交量过滤
      if (filters.minRelativeVolume !== undefined && stock.relativeVolume < filters.minRelativeVolume) return false

      // 涨跌幅过滤
      if (filters.minChange !== undefined && stock.changePercent < filters.minChange) return false
      if (filters.maxChange !== undefined && stock.changePercent > filters.maxChange) return false

      // 缺口过滤
      if (filters.minGap !== undefined && stock.gapPercent < filters.minGap) return false
      if (filters.maxGap !== undefined && stock.gapPercent > filters.maxGap) return false

      // 市值过滤
      if (filters.minMarketCap !== undefined && stock.marketCap !== undefined && stock.marketCap < filters.minMarketCap) return false
      if (filters.maxMarketCap !== undefined && stock.marketCap !== undefined && stock.marketCap > filters.maxMarketCap) return false

      // 行业过滤
      if (filters.sectors !== undefined && filters.sectors.length > 0) {
        if (!stock.sector || !filters.sectors.includes(stock.sector)) return false
      }

      return true
    })
  }

  /**
   * 排序股票
   */
  private sortStocks(stocks: ScannerStock[], sort: ScannerSort): ScannerStock[] {
    return [...stocks].sort((a, b) => {
      switch (sort) {
        case 'change':
          return Math.abs(b.changePercent) - Math.abs(a.changePercent)
        case 'volume':
          return b.volume - a.volume
        case 'relativeVolume':
          return b.relativeVolume - a.relativeVolume
        case 'gap':
          return Math.abs(b.gapPercent) - Math.abs(a.gapPercent)
        case 'price':
          return b.price - a.price
        default:
          return 0
      }
    })
  }

  /**
   * 清除缓存
   */
  clearCache(): void {
    this.cache.clear()
  }
}

// 默认实例
export const preMarketService = new PreMarketService()

export default PreMarketService
