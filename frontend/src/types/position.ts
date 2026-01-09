/**
 * 持仓类型定义
 * PRD 4.18 分策略持仓管理
 */

/**
 * 策略持仓
 */
export interface StrategyPosition {
  position_id: string
  user_id: string
  account_id: string
  strategy_id: string | null
  strategy_name: string | null

  symbol: string
  quantity: number
  avg_cost: number
  current_price: number
  market_value: number

  unrealized_pnl: number
  unrealized_pnl_pct: number
  realized_pnl: number

  stop_loss?: number
  take_profit?: number

  beta?: number
  volatility?: number

  created_at: string
  updated_at: string
}

/**
 * 持仓来源
 */
export interface PositionSource {
  strategy_id: string | null
  strategy_name: string
  quantity: number
  avg_cost: number
  pnl: number
  pnl_pct: number
}

/**
 * 同股票汇总持仓
 */
export interface ConsolidatedPosition {
  symbol: string
  total_quantity: number
  weighted_avg_cost: number
  current_price: number
  total_market_value: number
  total_unrealized_pnl: number
  total_unrealized_pnl_pct: number
  sources: PositionSource[]
  concentration_pct: number
}

/**
 * 持仓分组
 */
export interface PositionGroup {
  strategy_id: string | null
  strategy_name: string
  positions: StrategyPosition[]
  total_market_value: number
  total_unrealized_pnl: number
  total_unrealized_pnl_pct: number
  position_count: number
}

/**
 * 账户持仓汇总
 */
export interface AccountPositionSummary {
  account_id: string
  total_market_value: number
  total_cash: number
  total_equity: number
  total_unrealized_pnl: number
  total_unrealized_pnl_pct: number
  groups: PositionGroup[]
  consolidated: ConsolidatedPosition[]
  concentration_warnings: string[]
  portfolio_beta?: number
  updated_at: string
}

/**
 * 卖出请求
 */
export interface SellPositionRequest {
  position_id: string
  quantity: number
  order_type?: 'market' | 'limit'
  limit_price?: number
}

/**
 * 卖出响应
 */
export interface SellPositionResponse {
  success: boolean
  order_id?: string
  message: string
}

/**
 * 视图模式
 */
export type PositionViewMode = 'strategy' | 'symbol'

/**
 * 格式化盈亏
 */
export function formatPnL(pnl: number, showSign = true): string {
  const sign = showSign && pnl >= 0 ? '+' : ''
  return `${sign}$${pnl.toLocaleString(undefined, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`
}

/**
 * 格式化盈亏百分比
 */
export function formatPnLPct(pct: number, showSign = true): string {
  const sign = showSign && pct >= 0 ? '+' : ''
  return `${sign}${pct.toFixed(2)}%`
}

/**
 * 格式化货币
 */
export function formatCurrency(value: number): string {
  return `$${value.toLocaleString(undefined, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`
}

/**
 * 获取盈亏颜色类
 */
export function getPnLColorClass(pnl: number): string {
  return pnl >= 0 ? 'text-green-400' : 'text-red-400'
}
