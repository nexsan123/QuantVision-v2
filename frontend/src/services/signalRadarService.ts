/**
 * 信号雷达服务 - 连接后端 API
 * PRD 4.16.2: 信号雷达功能
 */

import { apiGet, apiPost } from './api'
import type {
  Signal,
  SignalType,
  SignalStrength,
  SignalStatus,
  SignalListResponse,
  StockSearchResult,
  StatusSummary,
} from '../types/signalRadar'

// ==================== API 端点 ====================

const API_PREFIX = '/api/v1/signal-radar'

// ==================== 响应转换 ====================

interface BackendSignal {
  signal_id: string
  strategy_id: string
  symbol: string
  company_name: string
  signal_type: string
  signal_strength: string
  signal_score: number
  status: string
  triggered_factors: Array<{
    factor_id: string
    factor_name: string
    current_value: number
    threshold: number
    direction: string
    near_trigger_pct: number
    is_satisfied: boolean
  }>
  current_price: string | number
  target_price?: string | number | null
  stop_loss_price?: string | number | null
  expected_return_pct?: number | null
  signal_time: string
  expires_at?: string | null
  is_holding: boolean
}

interface BackendSignalListResponse {
  total: number
  signals: BackendSignal[]
  summary: {
    buy: number
    sell: number
    hold: number
  }
}

interface BackendStockSearchResult {
  symbol: string
  company_name: string
  sector?: string
  current_price: string | number
  signal_status?: string
  signal_score?: number
}

interface BackendStatusSummary {
  holding: number
  buy_signal: number
  sell_signal: number
  near_trigger: number
  monitoring: number
  excluded: number
}

function transformSignal(s: BackendSignal): Signal {
  return {
    signalId: s.signal_id,
    strategyId: s.strategy_id,
    symbol: s.symbol,
    companyName: s.company_name,
    signalType: s.signal_type as SignalType,
    signalStrength: s.signal_strength as SignalStrength,
    signalScore: s.signal_score,
    status: s.status as SignalStatus,
    triggeredFactors: s.triggered_factors.map(f => ({
      factorId: f.factor_id,
      factorName: f.factor_name,
      currentValue: f.current_value,
      threshold: f.threshold,
      direction: f.direction as 'above' | 'below',
      nearTriggerPct: f.near_trigger_pct,
      isSatisfied: f.is_satisfied,
    })),
    currentPrice: typeof s.current_price === 'string' ? parseFloat(s.current_price) : s.current_price,
    targetPrice: s.target_price ? (typeof s.target_price === 'string' ? parseFloat(s.target_price) : s.target_price) : undefined,
    stopLossPrice: s.stop_loss_price ? (typeof s.stop_loss_price === 'string' ? parseFloat(s.stop_loss_price) : s.stop_loss_price) : undefined,
    expectedReturnPct: s.expected_return_pct ?? undefined,
    signalTime: s.signal_time,
    expiresAt: s.expires_at ?? undefined,
    isHolding: s.is_holding,
  }
}

// ==================== API 函数 ====================

/**
 * 获取策略信号列表
 */
export async function getSignals(
  strategyId: string,
  params?: {
    signalType?: SignalType
    signalStrength?: SignalStrength
    status?: SignalStatus
    search?: string
    limit?: number
    offset?: number
  }
): Promise<SignalListResponse> {
  const queryParams = new URLSearchParams()

  if (params?.signalType) queryParams.append('signal_type', params.signalType)
  if (params?.signalStrength) queryParams.append('signal_strength', params.signalStrength)
  if (params?.status) queryParams.append('status', params.status)
  if (params?.search) queryParams.append('search', params.search)
  if (params?.limit) queryParams.append('limit', String(params.limit))
  if (params?.offset) queryParams.append('offset', String(params.offset))

  const query = queryParams.toString()
  const url = query ? `${API_PREFIX}/${strategyId}?${query}` : `${API_PREFIX}/${strategyId}`

  const response = await apiGet<BackendSignalListResponse>(url)

  return {
    total: response.total,
    signals: response.signals.map(transformSignal),
    summary: response.summary,
  }
}

/**
 * 搜索股票
 */
export async function searchStocks(
  query: string,
  strategyId?: string,
  limit: number = 20
): Promise<StockSearchResult[]> {
  const params = new URLSearchParams()
  params.append('query', query)
  if (strategyId) params.append('strategy_id', strategyId)
  params.append('limit', String(limit))

  const response = await apiGet<{ results: BackendStockSearchResult[] }>(
    `${API_PREFIX}/stocks/search?${params}`
  )

  return response.results.map(r => ({
    symbol: r.symbol,
    companyName: r.company_name,
    sector: r.sector,
    currentPrice: typeof r.current_price === 'string' ? parseFloat(r.current_price) : r.current_price,
    signalStatus: r.signal_status as SignalStatus | undefined,
    signalScore: r.signal_score,
  }))
}

/**
 * 获取历史信号
 */
export async function getSignalHistory(
  strategyId: string,
  params?: {
    symbol?: string
    limit?: number
  }
): Promise<{ total: number; signals: Signal[] }> {
  const queryParams = new URLSearchParams()
  if (params?.symbol) queryParams.append('symbol', params.symbol)
  if (params?.limit) queryParams.append('limit', String(params.limit))

  const query = queryParams.toString()
  const url = query
    ? `${API_PREFIX}/${strategyId}/history?${query}`
    : `${API_PREFIX}/${strategyId}/history`

  const response = await apiGet<{ total: number; signals: BackendSignal[] }>(url)

  return {
    total: response.total,
    signals: response.signals.map(transformSignal),
  }
}

/**
 * 获取状态分布统计
 */
export async function getStatusSummary(strategyId: string): Promise<StatusSummary> {
  const response = await apiGet<{
    strategy_id: string
    summary: BackendStatusSummary
    updated_at: string
  }>(`${API_PREFIX}/${strategyId}/status-summary`)

  return {
    holding: response.summary.holding,
    buySignal: response.summary.buy_signal,
    sellSignal: response.summary.sell_signal,
    nearTrigger: response.summary.near_trigger,
    monitoring: response.summary.monitoring,
    excluded: response.summary.excluded,
  }
}

/**
 * 刷新策略信号
 */
export async function refreshSignals(strategyId: string): Promise<boolean> {
  const response = await apiPost<{ success: boolean; message: string }>(
    `${API_PREFIX}/${strategyId}/refresh`,
    {}
  )
  return response.success
}

// ==================== 简化类型 (用于 Trading 页面) ====================

export interface SimpleSignal {
  symbol: string
  status: 'holding' | 'buy' | 'sell' | 'approaching' | 'watching'
  price: number
  change: number
  changePct: number
  signalStrength?: number
  message?: string
}

/**
 * 获取简化的信号列表 (用于 Trading 页面的信号雷达面板)
 */
export async function getSimpleSignals(
  strategyId: string,
  _deploymentId?: string
): Promise<SimpleSignal[]> {
  if (!strategyId) return []

  try {
    const response = await getSignals(strategyId, { limit: 50 })

    // 转换为简化格式
    return response.signals.map(s => ({
      symbol: s.symbol,
      status: mapStatus(s.status),
      price: s.currentPrice,
      change: 0, // TODO: 从行情数据获取
      changePct: 0,
      signalStrength: s.signalScore,
      message: getSignalMessage(s),
    }))
  } catch (error) {
    console.error('Failed to get simple signals:', error)
    return []
  }
}

function mapStatus(status: SignalStatus): SimpleSignal['status'] {
  switch (status) {
    case 'holding': return 'holding'
    case 'buy_signal': return 'buy'
    case 'sell_signal': return 'sell'
    case 'near_trigger': return 'approaching'
    default: return 'watching'
  }
}

function getSignalMessage(signal: Signal): string | undefined {
  if (signal.status === 'buy_signal' && signal.triggeredFactors.length > 0) {
    const satisfied = signal.triggeredFactors.filter(f => f.isSatisfied)
    if (satisfied.length > 0) {
      return satisfied.map(f => f.factorName).join(', ')
    }
  }
  if (signal.status === 'near_trigger') {
    return '接近买入点'
  }
  if (signal.status === 'sell_signal') {
    return '触发卖出信号'
  }
  return undefined
}
