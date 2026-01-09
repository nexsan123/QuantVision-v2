/**
 * 盘前扫描类型定义
 * PRD 4.18.0 盘前扫描器
 */

/**
 * 盘前扫描筛选条件
 */
export interface PreMarketScanFilter {
  min_gap: number
  min_premarket_volume: number
  min_volatility: number
  min_liquidity: number
  has_news: boolean | null
  is_earnings_day: boolean | null
}

/**
 * 评分明细
 */
export interface ScoreBreakdown {
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

/**
 * 盘前扫描股票
 */
export interface PreMarketStock {
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
  score_breakdown: ScoreBreakdown
}

/**
 * 盘前扫描结果
 */
export interface PreMarketScanResult {
  scan_time: string
  strategy_id: string
  strategy_name: string
  filters_applied: PreMarketScanFilter
  total_matched: number
  stocks: PreMarketStock[]
  ai_suggestion?: string
}

/**
 * 日内监控列表
 */
export interface IntradayWatchlist {
  watchlist_id: string
  user_id: string
  strategy_id: string
  date: string
  symbols: string[]
  created_at: string
  is_confirmed: boolean
}

/**
 * 时间止损配置
 */
export interface TimeStopConfig {
  enabled: boolean
  time: string // HH:mm
}

/**
 * 止盈止损配置
 */
export interface StopLossConfig {
  stop_loss_type: 'atr' | 'fixed' | 'percentage' | 'technical'
  stop_loss_value: number
  take_profit_type: 'atr' | 'fixed' | 'percentage' | 'technical'
  take_profit_value: number
  time_stop_enabled: boolean
  time_stop_time: string
  trailing_stop_enabled: boolean
  trailing_trigger_pct: number
  trailing_distance_pct: number
}

/**
 * 日内交易记录
 */
export interface IntradayTrade {
  time: string
  symbol: string
  side: 'buy' | 'sell'
  quantity: number
  price: number
  stop_loss?: number
  take_profit?: number
  pnl?: number
  is_open: boolean
}

/**
 * 信号状态
 */
export interface SignalStatus {
  type: 'buy' | 'sell' | 'none'
  change: number
  change_pct: number
}

/**
 * 默认筛选条件
 */
export const DEFAULT_FILTERS: PreMarketScanFilter = {
  min_gap: 0.02,
  min_premarket_volume: 2.0,
  min_volatility: 0.03,
  min_liquidity: 5000000,
  has_news: null,
  is_earnings_day: null,
}

/**
 * 默认止盈止损配置
 */
export const DEFAULT_STOP_LOSS_CONFIG: StopLossConfig = {
  stop_loss_type: 'atr',
  stop_loss_value: 1.5,
  take_profit_type: 'atr',
  take_profit_value: 2.5,
  time_stop_enabled: true,
  time_stop_time: '15:55',
  trailing_stop_enabled: false,
  trailing_trigger_pct: 0.5,
  trailing_distance_pct: 0.3,
}

/**
 * 格式化Gap百分比
 */
export function formatGap(gap: number): string {
  const sign = gap >= 0 ? '+' : ''
  return `${sign}${(gap * 100).toFixed(1)}%`
}

/**
 * 获取评分星级
 */
export function getScoreStars(score: number): string {
  const stars = Math.ceil(score / 20)
  return '⭐'.repeat(Math.min(stars, 5))
}

/**
 * 获取评分颜色类
 */
export function getScoreColorClass(score: number): string {
  if (score >= 80) return 'text-green-400'
  if (score >= 60) return 'text-yellow-400'
  return 'text-gray-400'
}
