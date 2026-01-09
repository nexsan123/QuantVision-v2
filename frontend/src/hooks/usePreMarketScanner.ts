/**
 * 盘前扫描器 Hook
 * Sprint 7: 集成 Polygon.io 盘前数据
 */
import { useState, useEffect, useCallback, useRef } from 'react'
import {
  preMarketService,
  type ScannerStock,
  type ScannerFilters,
  type ScannerSort,
  type ScannerResult,
} from '../services/preMarketService'

// Hook 选项
interface UsePreMarketScannerOptions {
  // 自动刷新间隔 (毫秒)，0 表示不自动刷新
  refreshInterval?: number
  // 初始过滤器
  initialFilters?: ScannerFilters
  // 初始排序
  initialSort?: ScannerSort
  // 初始数量限制
  initialLimit?: number
  // 是否使用模拟数据 (当 API 不可用时)
  useMockData?: boolean
}

// Hook 返回值
interface UsePreMarketScannerResult {
  // 数据
  stocks: ScannerStock[]
  marketStatus: 'pre' | 'open' | 'after' | 'closed'
  lastUpdate: number

  // 状态
  loading: boolean
  error: Error | null

  // 操作
  refresh: () => Promise<void>
  setFilters: (filters: ScannerFilters) => void
  setSort: (sort: ScannerSort) => void
  setLimit: (limit: number) => void

  // 当前配置
  filters: ScannerFilters
  sort: ScannerSort
  limit: number
}

// 模拟数据生成
function generateMockStocks(count: number): ScannerStock[] {
  const symbols = ['NVDA', 'AAPL', 'TSLA', 'AMD', 'GOOGL', 'MSFT', 'META', 'AMZN', 'NFLX', 'COIN']
  const stocks: ScannerStock[] = []

  for (let i = 0; i < count; i++) {
    const symbol = symbols[i % symbols.length]
    const basePrice = 100 + Math.random() * 400
    const change = (Math.random() - 0.3) * 20
    const changePercent = (change / basePrice) * 100

    stocks.push({
      symbol: `${symbol}${i >= symbols.length ? i : ''}`,
      name: `${symbol} Inc.`,
      price: basePrice + change,
      change,
      changePercent,
      volume: Math.floor(Math.random() * 10000000),
      avgVolume: Math.floor(Math.random() * 5000000),
      relativeVolume: 0.5 + Math.random() * 3,
      preMarketPrice: basePrice + change * 0.8,
      preMarketChange: change * 0.8,
      preMarketChangePercent: changePercent * 0.8,
      preMarketVolume: Math.floor(Math.random() * 1000000),
      gap: change * 0.5,
      gapPercent: changePercent * 0.5,
      marketCap: Math.floor(Math.random() * 500) * 1000000000,
      high: basePrice + change + Math.random() * 5,
      low: basePrice + change - Math.random() * 5,
      prevClose: basePrice,
      vwap: basePrice + change * 0.9,
      hasNews: Math.random() > 0.7,
      hasEarnings: Math.random() > 0.9,
      timestamp: Date.now(),
    })
  }

  return stocks.sort((a, b) => Math.abs(b.changePercent) - Math.abs(a.changePercent))
}

/**
 * 盘前扫描器 Hook
 */
export function usePreMarketScanner(
  options: UsePreMarketScannerOptions = {}
): UsePreMarketScannerResult {
  const {
    refreshInterval = 30000, // 默认30秒刷新
    initialFilters = {},
    initialSort = 'change',
    initialLimit = 50,
    useMockData = true, // 默认使用模拟数据
  } = options

  const [stocks, setStocks] = useState<ScannerStock[]>([])
  const [marketStatus, setMarketStatus] = useState<'pre' | 'open' | 'after' | 'closed'>('closed')
  const [lastUpdate, setLastUpdate] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  const [filters, setFilters] = useState<ScannerFilters>(initialFilters)
  const [sort, setSort] = useState<ScannerSort>(initialSort)
  const [limit, setLimit] = useState(initialLimit)

  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  // 刷新数据
  const refresh = useCallback(async () => {
    setLoading(true)
    setError(null)

    try {
      if (useMockData) {
        // 使用模拟数据
        const mockStocks = generateMockStocks(limit)
        setStocks(mockStocks)
        setMarketStatus(preMarketService.getMarketStatus())
        setLastUpdate(Date.now())
      } else {
        // 使用真实 API
        const result: ScannerResult = await preMarketService.scanPreMarket(
          filters,
          sort,
          limit
        )
        setStocks(result.stocks)
        setMarketStatus(result.marketStatus)
        setLastUpdate(result.lastUpdate)
      }
    } catch (err) {
      console.error('[usePreMarketScanner] Refresh failed:', err)
      setError(err as Error)

      // 失败时回退到模拟数据
      if (useMockData) {
        const mockStocks = generateMockStocks(limit)
        setStocks(mockStocks)
        setMarketStatus(preMarketService.getMarketStatus())
        setLastUpdate(Date.now())
      }
    } finally {
      setLoading(false)
    }
  }, [filters, sort, limit, useMockData])

  // 初始加载
  useEffect(() => {
    refresh()
  }, [refresh])

  // 自动刷新
  useEffect(() => {
    if (refreshInterval > 0) {
      intervalRef.current = setInterval(refresh, refreshInterval)
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
      }
    }
  }, [refreshInterval, refresh])

  return {
    stocks,
    marketStatus,
    lastUpdate,
    loading,
    error,
    refresh,
    setFilters,
    setSort,
    setLimit,
    filters,
    sort,
    limit,
  }
}

/**
 * 获取涨幅榜 Hook
 */
export function useGainers(limit: number = 10, refreshInterval: number = 30000) {
  return usePreMarketScanner({
    initialSort: 'change',
    initialLimit: limit,
    refreshInterval,
    initialFilters: { minChange: 0 },
  })
}

/**
 * 获取跌幅榜 Hook
 */
export function useLosers(limit: number = 10, refreshInterval: number = 30000) {
  return usePreMarketScanner({
    initialSort: 'change',
    initialLimit: limit,
    refreshInterval,
    initialFilters: { maxChange: 0 },
  })
}

/**
 * 获取高成交量股票 Hook
 */
export function useHighVolume(limit: number = 10, refreshInterval: number = 30000) {
  return usePreMarketScanner({
    initialSort: 'volume',
    initialLimit: limit,
    refreshInterval,
    initialFilters: { minVolume: 1000000 },
  })
}

export default usePreMarketScanner
