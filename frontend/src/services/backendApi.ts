/**
 * 后端 API 客户端
 * Sprint 11: 前端与后端实时服务集成
 *
 * 通过后端代理调用 Alpaca API，避免前端暴露 API 密钥
 */

// 获取后端 API 基础 URL
const getBaseUrl = (): string => {
  return import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
}

// 获取 WebSocket URL
export const getWsUrl = (): string => {
  return import.meta.env.VITE_WS_URL || 'ws://localhost:8000'
}

/**
 * 通用请求方法
 */
async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const baseUrl = getBaseUrl()

  const response = await fetch(`${baseUrl}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({
      detail: `HTTP ${response.status}`,
    }))
    throw new Error(error.detail || error.message || `Request failed: ${response.status}`)
  }

  if (response.status === 204) {
    return undefined as T
  }

  return response.json()
}

// ==================== 实时监控 API ====================

export interface RealtimeStatus {
  timestamp: string
  market: {
    is_open: boolean
    next_open: string
    next_close: string
  }
  account: {
    equity: number
    cash: number
    buying_power: number
    portfolio_value: number
  }
  performance: {
    daily_pnl: number
    daily_return_pct: number
    unrealized_pnl: number
    drawdown_pct: number
  }
  positions: {
    total: number
    long: number
    short: number
  }
  monitoring: {
    is_running: boolean
    peak_equity: number | null
  }
}

export interface PositionDetail {
  symbol: string
  side: 'long' | 'short'
  quantity: number
  avg_entry_price: number
  current_price: number
  market_value: number
  cost_basis: number
  unrealized_pnl: number
  unrealized_pnl_pct: number
  weight_pct: number
  exchange: string
}

export interface OrderDetail {
  id: string
  client_order_id: string
  symbol: string
  side: string
  type: string
  qty: number
  filled_qty: number
  filled_avg_price: number | null
  status: string
  time_in_force: string
  limit_price: number | null
  stop_price: number | null
  created_at: string
  filled_at: string | null
}

export interface MarketClock {
  timestamp: string
  is_open: boolean
  next_open: string
  next_close: string
}

/**
 * 实时监控 API
 */
export const realtimeApi = {
  /**
   * 获取实时状态
   */
  getStatus: (): Promise<RealtimeStatus> => {
    return request<RealtimeStatus>('/api/v1/realtime/status')
  },

  /**
   * 获取持仓详情
   */
  getPositions: (): Promise<PositionDetail[]> => {
    return request<PositionDetail[]>('/api/v1/realtime/positions')
  },

  /**
   * 获取订单列表
   */
  getOrders: (status: string = 'all', limit: number = 50): Promise<OrderDetail[]> => {
    return request<OrderDetail[]>(`/api/v1/realtime/orders?status=${status}&limit=${limit}`)
  },

  /**
   * 获取市场时钟
   */
  getClock: (): Promise<MarketClock> => {
    return request<MarketClock>('/api/v1/realtime/clock')
  },

  /**
   * 获取账户信息
   */
  getAccount: (): Promise<Record<string, unknown>> => {
    return request<Record<string, unknown>>('/api/v1/realtime/account')
  },

  /**
   * 启动实时监控
   */
  startMonitor: (): Promise<{ success: boolean; message: string }> => {
    return request('/api/v1/realtime/monitor/start', { method: 'POST' })
  },

  /**
   * 停止实时监控
   */
  stopMonitor: (): Promise<{ success: boolean; message: string }> => {
    return request('/api/v1/realtime/monitor/stop', { method: 'POST' })
  },

  /**
   * 提交订单
   */
  submitOrder: (params: {
    symbol: string
    qty: number
    side: 'buy' | 'sell'
    order_type?: string
    limit_price?: number
    stop_price?: number
  }): Promise<{ success: boolean; order: Record<string, unknown> }> => {
    const query = new URLSearchParams({
      symbol: params.symbol,
      qty: String(params.qty),
      side: params.side,
      order_type: params.order_type || 'market',
    })
    if (params.limit_price) query.set('limit_price', String(params.limit_price))
    if (params.stop_price) query.set('stop_price', String(params.stop_price))

    return request(`/api/v1/realtime/orders?${query}`, { method: 'POST' })
  },

  /**
   * 取消订单
   */
  cancelOrder: (orderId: string): Promise<{ success: boolean; message: string }> => {
    return request(`/api/v1/realtime/orders/${orderId}`, { method: 'DELETE' })
  },

  /**
   * 平仓
   */
  closePosition: (symbol: string): Promise<{ success: boolean; order: Record<string, unknown> }> => {
    return request(`/api/v1/realtime/positions/${symbol}`, { method: 'DELETE' })
  },

  /**
   * 全部平仓
   */
  closeAllPositions: (): Promise<{ success: boolean; orders_count: number; message: string }> => {
    return request('/api/v1/realtime/positions', { method: 'DELETE' })
  },
}

// ==================== 策略 API ====================

export interface StrategyConfig {
  universe?: Record<string, unknown>
  alpha?: Record<string, unknown>
  signal?: Record<string, unknown>
  risk?: Record<string, unknown>
  portfolio?: Record<string, unknown>
  execution?: Record<string, unknown>
  monitor?: Record<string, unknown>
}

export interface Strategy {
  id: string
  name: string
  description: string
  status: string
  created_at: string
  updated_at: string
  config: StrategyConfig
}

/**
 * 策略 API
 */
export const strategyApi = {
  /**
   * 获取策略列表
   */
  list: (status?: string, limit: number = 20, offset: number = 0): Promise<{
    total: number
    strategies: Strategy[]
  }> => {
    const params = new URLSearchParams({ limit: String(limit), offset: String(offset) })
    if (status) params.set('status', status)
    return request(`/api/v1/strategies/v2/?${params}`)
  },

  /**
   * 获取策略详情
   */
  get: (id: string): Promise<Strategy> => {
    return request(`/api/v1/strategies/v2/${id}`)
  },

  /**
   * 创建策略
   */
  create: (data: { name: string; description?: string; config: StrategyConfig }): Promise<Strategy> => {
    return request('/api/v1/strategies/v2/', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  },

  /**
   * 更新策略
   */
  update: (id: string, data: Partial<{ name: string; description: string; status: string } & StrategyConfig>): Promise<Strategy> => {
    return request(`/api/v1/strategies/v2/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    })
  },

  /**
   * 删除策略
   */
  delete: (id: string): Promise<{ message: string }> => {
    return request(`/api/v1/strategies/v2/${id}`, { method: 'DELETE' })
  },

  /**
   * 验证策略
   */
  validate: (id: string): Promise<{
    valid: boolean
    errors: string[]
    warnings: string[]
    can_backtest: boolean
    can_go_live: boolean
  }> => {
    return request(`/api/v1/strategies/v2/${id}/validate`, { method: 'POST' })
  },

  /**
   * 运行回测
   */
  runBacktest: (id: string, startDate: string, endDate: string, capital: number = 1000000): Promise<{
    task_id: string
    strategy_id: string
    status: string
  }> => {
    const params = new URLSearchParams({
      start_date: startDate,
      end_date: endDate,
      initial_capital: String(capital),
    })
    return request(`/api/v1/strategies/v2/${id}/run-backtest?${params}`, { method: 'POST' })
  },
}

// ==================== 信号雷达 API ====================

export interface Signal {
  signal_id: string
  strategy_id: string
  symbol: string
  company_name: string
  signal_type: 'buy' | 'sell' | 'hold'
  signal_strength: 'strong' | 'medium' | 'weak'
  signal_score: number
  status: string
  current_price: number
  target_price: number | null
  stop_loss_price: number | null
  expected_return_pct: number | null
  signal_time: string
}

/**
 * 信号雷达 API
 */
export const signalApi = {
  /**
   * 获取策略信号
   */
  getSignals: (strategyId: string, options?: {
    signal_type?: string
    signal_strength?: string
    status?: string
    search?: string
    limit?: number
    offset?: number
  }): Promise<{
    total: number
    signals: Signal[]
    summary: { buy: number; sell: number; hold: number }
  }> => {
    const params = new URLSearchParams()
    if (options) {
      Object.entries(options).forEach(([key, value]) => {
        if (value !== undefined) params.set(key, String(value))
      })
    }
    return request(`/api/v1/signal-radar/${strategyId}?${params}`)
  },

  /**
   * 获取状态汇总
   */
  getStatusSummary: (strategyId: string): Promise<{
    strategy_id: string
    summary: {
      holding: number
      buy_signal: number
      sell_signal: number
      near_trigger: number
      monitoring: number
      excluded: number
    }
    updated_at: string
  }> => {
    return request(`/api/v1/signal-radar/${strategyId}/status-summary`)
  },

  /**
   * 刷新信号
   */
  refresh: (strategyId: string): Promise<{ success: boolean; message: string }> => {
    return request(`/api/v1/signal-radar/${strategyId}/refresh`, { method: 'POST' })
  },
}

// ==================== 风险预警 API ====================

export interface RiskAlert {
  alert_id: string
  user_id: string
  strategy_id: string | null
  alert_type: string
  severity: 'info' | 'warning' | 'critical'
  title: string
  message: string
  details: Record<string, unknown>
  is_read: boolean
  created_at: string
}

export interface AlertConfig {
  user_id: string
  enabled: boolean
  daily_loss_threshold: number
  max_drawdown_threshold: number
  concentration_threshold: number
  vix_threshold: number
  email_enabled: boolean
  email_address: string
  quiet_hours_start: number | null
  quiet_hours_end: number | null
}

/**
 * 风险预警 API
 */
export const alertApi = {
  /**
   * 获取预警列表
   */
  list: (unreadOnly: boolean = false, alertType?: string, limit: number = 50): Promise<{
    total: number
    alerts: RiskAlert[]
    unread_count: number
  }> => {
    const params = new URLSearchParams({
      unread_only: String(unreadOnly),
      limit: String(limit),
    })
    if (alertType) params.set('alert_type', alertType)
    return request(`/api/v1/alerts/?${params}`)
  },

  /**
   * 获取未读数量
   */
  getUnreadCount: (): Promise<{ count: number }> => {
    return request('/api/v1/alerts/unread-count')
  },

  /**
   * 标记为已读
   */
  markAsRead: (alertId: string): Promise<{ success: boolean }> => {
    return request(`/api/v1/alerts/${alertId}/read`, { method: 'POST' })
  },

  /**
   * 全部标记已读
   */
  markAllAsRead: (): Promise<{ success: boolean; count: number }> => {
    return request('/api/v1/alerts/mark-all-read', { method: 'POST' })
  },

  /**
   * 获取预警配置
   */
  getConfig: (): Promise<AlertConfig> => {
    return request('/api/v1/alerts/config')
  },

  /**
   * 更新预警配置
   */
  updateConfig: (config: Partial<AlertConfig>): Promise<AlertConfig> => {
    return request('/api/v1/alerts/config', {
      method: 'PUT',
      body: JSON.stringify(config),
    })
  },

  /**
   * 发送测试邮件
   */
  testEmail: (): Promise<{ success: boolean; message: string }> => {
    return request('/api/v1/alerts/test-email', { method: 'POST' })
  },
}

// ==================== 健康检查 API ====================

/**
 * 健康检查 API
 */
export const healthApi = {
  /**
   * 检查后端健康状态
   */
  check: async (): Promise<boolean> => {
    try {
      await request('/api/v1/health')
      return true
    } catch {
      return false
    }
  },
}

// 导出所有 API
export default {
  realtime: realtimeApi,
  strategy: strategyApi,
  signal: signalApi,
  alert: alertApi,
  health: healthApi,
  getWsUrl,
}
