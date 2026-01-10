/**
 * 回测服务 - 连接后端回测 API
 * Phase 4: 前后端集成
 */

import { apiGet, apiPost, apiDelete } from './api'

// ==================== 类型定义 ====================

export interface BacktestMetrics {
  totalReturn: number
  annualReturn: number
  volatility?: number
  maxDrawdown: number
  sharpe: number
  sortino: number
  calmar: number
  winRate: number
  profitFactor: number
  beta?: number
  alpha?: number
}

export interface BacktestConfig {
  startDate: string
  endDate: string
  initialCapital: number
  universe?: string[]
  universeId?: string
}

export interface BacktestResult {
  id: string
  name: string
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'
  progress: number
  config?: BacktestConfig
  metrics?: BacktestMetrics
  tradesCount?: number
  createdAt: string
  completedAt?: string
}

export interface BacktestTrade {
  timestamp: string
  symbol: string
  side: 'buy' | 'sell'
  quantity: number
  price: number
  commission: number
  pnl?: number
}

export interface BacktestPosition {
  symbol: string
  quantity: number
  marketValue: number
  weight: number
  pnl: number
  pnlPct: number
}

export interface BacktestCreateRequest {
  name: string
  strategyId?: string
  startDate: string
  endDate: string
  initialCapital: number
  universe?: string[]
  universeId?: string
}

// ==================== API 端点 ====================

const API_PREFIX = '/api/v1/backtests'

/**
 * 获取回测列表
 */
export async function getBacktests(params?: {
  status?: string
  page?: number
  pageSize?: number
}): Promise<{ backtests: BacktestResult[]; total: number }> {
  const queryParams = new URLSearchParams()
  if (params?.status) queryParams.append('status', params.status)
  if (params?.page) queryParams.append('page', String(params.page))
  if (params?.pageSize) queryParams.append('page_size', String(params.pageSize))

  const query = queryParams.toString()
  const url = query ? `${API_PREFIX}?${query}` : API_PREFIX

  const response = await apiGet<{
    backtests: Array<{
      id: string
      name: string
      status: string
      progress: number
      created_at: string
      completed_at?: string
    }>
    total: number
  }>(url)

  // 转换命名风格
  return {
    backtests: response.backtests.map(bt => ({
      id: bt.id,
      name: bt.name,
      status: bt.status as BacktestResult['status'],
      progress: bt.progress,
      createdAt: bt.created_at,
      completedAt: bt.completed_at,
    })),
    total: response.total,
  }
}

/**
 * 创建回测
 */
export async function createBacktest(request: BacktestCreateRequest): Promise<BacktestResult> {
  const response = await apiPost<{
    data: {
      id: string
      name: string
      status: string
      progress: number
      created_at: string
    }
    message: string
  }>(API_PREFIX, {
    name: request.name,
    strategy_id: request.strategyId,
    start_date: request.startDate,
    end_date: request.endDate,
    initial_capital: request.initialCapital,
    universe: request.universe,
    universe_id: request.universeId,
  })

  return {
    id: response.data.id,
    name: response.data.name,
    status: response.data.status as BacktestResult['status'],
    progress: response.data.progress,
    createdAt: response.data.created_at,
  }
}

/**
 * 获取回测详情
 */
export async function getBacktest(backtestId: string): Promise<BacktestResult> {
  const response = await apiGet<{
    data: {
      id: string
      name: string
      status: string
      config?: {
        start_date: string
        end_date: string
        initial_capital: number
      }
      metrics?: {
        total_return: number
        annual_return: number
        volatility: number
        max_drawdown: number
        sharpe_ratio: number
        sortino_ratio: number
        calmar_ratio: number
        win_rate: number
        profit_factor: number
        beta: number
        alpha: number
      }
      trades_count?: number
    }
  }>(`${API_PREFIX}/${backtestId}`)

  const bt = response.data

  return {
    id: bt.id,
    name: bt.name,
    status: bt.status as BacktestResult['status'],
    progress: bt.status === 'completed' ? 100 : 0,
    createdAt: '',
    config: bt.config ? {
      startDate: bt.config.start_date,
      endDate: bt.config.end_date,
      initialCapital: bt.config.initial_capital,
    } : undefined,
    metrics: bt.metrics ? {
      totalReturn: bt.metrics.total_return,
      annualReturn: bt.metrics.annual_return,
      volatility: bt.metrics.volatility,
      maxDrawdown: bt.metrics.max_drawdown,
      sharpe: bt.metrics.sharpe_ratio,
      sortino: bt.metrics.sortino_ratio,
      calmar: bt.metrics.calmar_ratio,
      winRate: bt.metrics.win_rate,
      profitFactor: bt.metrics.profit_factor,
      beta: bt.metrics.beta,
      alpha: bt.metrics.alpha,
    } : undefined,
    tradesCount: bt.trades_count,
  }
}

/**
 * 获取回测状态
 */
export async function getBacktestStatus(backtestId: string): Promise<{
  id: string
  status: string
  progress: number
}> {
  return apiGet(`${API_PREFIX}/${backtestId}/status`)
}

/**
 * 删除回测
 */
export async function deleteBacktest(backtestId: string): Promise<void> {
  await apiDelete(`${API_PREFIX}/${backtestId}`)
}

/**
 * 取消回测
 */
export async function cancelBacktest(backtestId: string): Promise<void> {
  await apiPost(`${API_PREFIX}/${backtestId}/cancel`, {})
}

/**
 * 获取回测交易记录
 */
export async function getBacktestTrades(
  backtestId: string,
  params?: { page?: number; pageSize?: number }
): Promise<{ trades: BacktestTrade[]; total: number }> {
  const queryParams = new URLSearchParams()
  if (params?.page) queryParams.append('page', String(params.page))
  if (params?.pageSize) queryParams.append('page_size', String(params.pageSize))

  const query = queryParams.toString()
  const url = query
    ? `${API_PREFIX}/${backtestId}/trades?${query}`
    : `${API_PREFIX}/${backtestId}/trades`

  const response = await apiGet<{
    trades: Array<{
      timestamp: string
      symbol: string
      side: string
      quantity: number
      price: number
      commission: number
    }>
    total: number
  }>(url)

  return {
    trades: response.trades.map(t => ({
      timestamp: t.timestamp,
      symbol: t.symbol,
      side: t.side as 'buy' | 'sell',
      quantity: t.quantity,
      price: t.price,
      commission: t.commission,
    })),
    total: response.total,
  }
}

/**
 * 获取回测持仓
 */
export async function getBacktestPositions(
  backtestId: string,
  asOf?: string
): Promise<{
  asOf: string
  positions: BacktestPosition[]
  cash: number
  totalValue: number
}> {
  const url = asOf
    ? `${API_PREFIX}/${backtestId}/positions?as_of=${asOf}`
    : `${API_PREFIX}/${backtestId}/positions`

  const response = await apiGet<{
    as_of: string
    positions: Array<{
      symbol: string
      quantity: number
      market_value: number
      weight: number
      pnl: number
      pnl_pct: number
    }>
    cash: number
    total_value: number
  }>(url)

  return {
    asOf: response.as_of,
    positions: response.positions.map(p => ({
      symbol: p.symbol,
      quantity: p.quantity,
      marketValue: p.market_value,
      weight: p.weight,
      pnl: p.pnl,
      pnlPct: p.pnl_pct,
    })),
    cash: response.cash,
    totalValue: response.total_value,
  }
}
