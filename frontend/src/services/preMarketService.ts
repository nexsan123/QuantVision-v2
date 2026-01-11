/**
 * 盘前扫描服务 - 连接后端 API
 * PRD 4.18.0 盘前扫描器
 */

import { apiGet, apiPost } from './api'
import type {
  PreMarketScanResult,
  PreMarketScanFilter,
  PreMarketStock,
} from '../types/preMarket'

// ==================== 类型定义 (用于 Hook) ====================

export interface ScannerStock {
  symbol: string
  name: string
  price: number
  change: number
  changePercent: number
  volume: number
  avgVolume: number
  relativeVolume: number
  preMarketPrice: number
  preMarketChange: number
  preMarketChangePercent: number
  preMarketVolume: number
  gap: number
  gapPercent: number
  marketCap: number
  high: number
  low: number
  prevClose: number
  vwap: number
  hasNews: boolean
  hasEarnings: boolean
  timestamp: number
}

export interface ScannerFilters {
  minChange?: number
  maxChange?: number
  minVolume?: number
  maxVolume?: number
  minMarketCap?: number
  maxMarketCap?: number
  minRelativeVolume?: number
}

export type ScannerSort = 'change' | 'volume' | 'relativeVolume' | 'gap' | 'marketCap'

export interface ScannerResult {
  stocks: ScannerStock[]
  marketStatus: 'pre' | 'open' | 'after' | 'closed'
  lastUpdate: number
}

// ==================== preMarketService 对象 ====================

export const preMarketService = {
  getMarketStatus(): 'pre' | 'open' | 'after' | 'closed' {
    const now = new Date()
    const hour = now.getHours()
    const minute = now.getMinutes()
    const time = hour * 60 + minute
    const day = now.getDay()

    // 周末市场关闭
    if (day === 0 || day === 6) return 'closed'

    // 美东时间 (简化处理)
    if (time < 4 * 60) return 'closed'        // 4:00 之前
    if (time < 9 * 60 + 30) return 'pre'      // 4:00 - 9:30 盘前
    if (time < 16 * 60) return 'open'         // 9:30 - 16:00 开盘
    if (time < 20 * 60) return 'after'        // 16:00 - 20:00 盘后
    return 'closed'
  },

  async scanPreMarket(
    filters: ScannerFilters,
    sort: ScannerSort,
    limit: number
  ): Promise<ScannerResult> {
    // 调用后端 API
    const params = new URLSearchParams()
    if (filters.minChange !== undefined) params.append('min_change', String(filters.minChange))
    if (filters.maxChange !== undefined) params.append('max_change', String(filters.maxChange))
    if (filters.minVolume !== undefined) params.append('min_volume', String(filters.minVolume))
    params.append('sort', sort)
    params.append('limit', String(limit))

    try {
      const response = await apiGet<{ stocks: ScannerStock[]; timestamp: number }>(
        `/api/v1/intraday/scanner?${params}`
      )
      return {
        stocks: response.stocks || [],
        marketStatus: preMarketService.getMarketStatus(),
        lastUpdate: response.timestamp || Date.now(),
      }
    } catch {
      return {
        stocks: [],
        marketStatus: preMarketService.getMarketStatus(),
        lastUpdate: Date.now(),
      }
    }
  },
}

// ==================== API 端点 ====================

const API_PREFIX = '/api/v1/intraday'

// ==================== 响应转换 ====================

interface BackendPreMarketStock {
  symbol: string
  name: string
  gap: number
  gap_direction: 'up' | 'down'
  premarket_price: number
  premarket_volume: number
  premarket_volume_ratio: number
  prev_close: number
  prev_volume: number
  volatility: number
  avg_daily_volume: number
  avg_daily_value: number
  has_news: boolean
  news_headline?: string
  is_earnings_day: boolean
  score: number
  score_breakdown: {
    gap: number
    volume: number
    volatility: number
    news: number
    weights: {
      gap: number
      volume: number
      volatility: number
      news: number
    }
  }
}

interface BackendPreMarketScanResult {
  scan_time: string
  strategy_id: string
  strategy_name: string
  filters_applied: PreMarketScanFilter
  total_matched: number
  stocks: BackendPreMarketStock[]
  ai_suggestion?: string
}

function transformStock(s: BackendPreMarketStock): PreMarketStock {
  return {
    symbol: s.symbol,
    name: s.name,
    gap: s.gap,
    gap_direction: s.gap_direction,
    premarket_price: s.premarket_price,
    premarket_volume: s.premarket_volume,
    premarket_volume_ratio: s.premarket_volume_ratio,
    prev_close: s.prev_close,
    prev_volume: s.prev_volume,
    volatility: s.volatility,
    avg_daily_volume: s.avg_daily_volume,
    avg_daily_value: s.avg_daily_value,
    has_news: s.has_news,
    news_headline: s.news_headline,
    is_earnings_day: s.is_earnings_day,
    score: s.score,
    score_breakdown: s.score_breakdown,
  }
}

// ==================== API 函数 ====================

/**
 * 盘前扫描
 */
export async function scanPreMarket(
  strategyId: string,
  filters?: Partial<PreMarketScanFilter>
): Promise<PreMarketScanResult> {
  const params = new URLSearchParams()
  params.append('strategy_id', strategyId)

  if (filters?.min_gap !== undefined) params.append('min_gap', String(filters.min_gap))
  if (filters?.min_premarket_volume !== undefined) params.append('min_premarket_volume', String(filters.min_premarket_volume))
  if (filters?.min_volatility !== undefined) params.append('min_volatility', String(filters.min_volatility))
  if (filters?.min_liquidity !== undefined) params.append('min_liquidity', String(filters.min_liquidity))
  if (filters?.has_news !== undefined && filters.has_news !== null) params.append('has_news', String(filters.has_news))
  if (filters?.is_earnings_day !== undefined && filters.is_earnings_day !== null) params.append('is_earnings_day', String(filters.is_earnings_day))

  const response = await apiGet<BackendPreMarketScanResult>(
    `${API_PREFIX}/pre-market-scanner?${params}`
  )

  return {
    scan_time: response.scan_time,
    strategy_id: response.strategy_id,
    strategy_name: response.strategy_name,
    filters_applied: response.filters_applied,
    total_matched: response.total_matched,
    stocks: response.stocks.map(transformStock),
    ai_suggestion: response.ai_suggestion,
  }
}

/**
 * 确认监控列表
 */
export interface CreateWatchlistRequest {
  strategy_id: string
  symbols: string[]
}

export interface IntradayWatchlist {
  id: string
  date: string
  strategy_id: string
  symbols: string[]
  created_at: string
}

export async function createWatchlist(
  request: CreateWatchlistRequest
): Promise<IntradayWatchlist> {
  return apiPost<IntradayWatchlist>(`${API_PREFIX}/watchlist`, request)
}

/**
 * 获取今日监控列表
 */
export async function getTodayWatchlist(
  strategyId: string
): Promise<IntradayWatchlist | null> {
  try {
    return await apiGet<IntradayWatchlist>(
      `${API_PREFIX}/watchlist?strategy_id=${strategyId}`
    )
  } catch {
    return null
  }
}

/**
 * 获取监控列表历史
 */
export async function getWatchlistHistory(
  strategyId: string,
  limit: number = 10
): Promise<IntradayWatchlist[]> {
  return apiGet<IntradayWatchlist[]>(
    `${API_PREFIX}/watchlist/history?strategy_id=${strategyId}&limit=${limit}`
  )
}

/**
 * 获取市场状态
 */
export interface MarketStatus {
  status: 'pre_market' | 'market_open' | 'after_hours' | 'market_closed'
  statusText: string
  currentTime: string
  nextOpen: string
  nextClose: string
}

export async function getMarketStatus(): Promise<MarketStatus> {
  const response = await apiGet<{
    status: string
    status_text: string
    current_time: string
    next_open: string
    next_close: string
  }>(`${API_PREFIX}/market-status`)

  return {
    status: response.status as MarketStatus['status'],
    statusText: response.status_text,
    currentTime: response.current_time,
    nextOpen: response.next_open,
    nextClose: response.next_close,
  }
}
