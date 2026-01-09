/**
 * Alpaca 交易 API 服务
 * Sprint 8: T10 - 交易 API 服务
 *
 * 提供订单管理、持仓查询、账户信息等功能
 */
import { alpacaAuth, type AlpacaAccount } from './alpacaAuth'

// ==================== 订单类型定义 ====================

// 订单方向
export type OrderSide = 'buy' | 'sell'

// 订单类型
export type OrderType = 'market' | 'limit' | 'stop' | 'stop_limit' | 'trailing_stop'

// 订单有效期
export type TimeInForce = 'day' | 'gtc' | 'opg' | 'cls' | 'ioc' | 'fok'

// 订单状态
export type OrderStatus =
  | 'new'
  | 'partially_filled'
  | 'filled'
  | 'done_for_day'
  | 'canceled'
  | 'expired'
  | 'replaced'
  | 'pending_cancel'
  | 'pending_replace'
  | 'pending_new'
  | 'accepted'
  | 'accepted_without_block'
  | 'stopped'
  | 'rejected'
  | 'suspended'
  | 'calculated'

// 订单类别
export type OrderClass = 'simple' | 'bracket' | 'oco' | 'oto'

// 订单请求
export interface OrderRequest {
  symbol: string
  qty?: number
  notional?: number  // 金额下单
  side: OrderSide
  type: OrderType
  time_in_force: TimeInForce
  limit_price?: number
  stop_price?: number
  trail_price?: number
  trail_percent?: number
  extended_hours?: boolean
  client_order_id?: string
  order_class?: OrderClass
  take_profit?: {
    limit_price: number
  }
  stop_loss?: {
    stop_price: number
    limit_price?: number
  }
}

// 订单响应
export interface Order {
  id: string
  client_order_id: string
  created_at: string
  updated_at: string
  submitted_at: string
  filled_at: string | null
  expired_at: string | null
  canceled_at: string | null
  failed_at: string | null
  replaced_at: string | null
  replaced_by: string | null
  replaces: string | null
  asset_id: string
  symbol: string
  asset_class: string
  notional: string | null
  qty: string
  filled_qty: string
  filled_avg_price: string | null
  order_class: OrderClass
  order_type: OrderType
  type: OrderType
  side: OrderSide
  time_in_force: TimeInForce
  limit_price: string | null
  stop_price: string | null
  status: OrderStatus
  extended_hours: boolean
  legs: Order[] | null
  trail_percent: string | null
  trail_price: string | null
  hwm: string | null
}

// 持仓
export interface Position {
  asset_id: string
  symbol: string
  exchange: string
  asset_class: string
  avg_entry_price: string
  qty: string
  qty_available: string
  side: 'long' | 'short'
  market_value: string
  cost_basis: string
  unrealized_pl: string
  unrealized_plpc: string
  unrealized_intraday_pl: string
  unrealized_intraday_plpc: string
  current_price: string
  lastday_price: string
  change_today: string
}

// 资产
export interface Asset {
  id: string
  class: string
  exchange: string
  symbol: string
  name: string
  status: 'active' | 'inactive'
  tradable: boolean
  marginable: boolean
  shortable: boolean
  easy_to_borrow: boolean
  fractionable: boolean
}

// 市场时钟
export interface Clock {
  timestamp: string
  is_open: boolean
  next_open: string
  next_close: string
}

// 日历
export interface Calendar {
  date: string
  open: string
  close: string
}

// 订单查询参数
export interface OrdersQuery {
  status?: 'open' | 'closed' | 'all'
  limit?: number
  after?: string
  until?: string
  direction?: 'asc' | 'desc'
  nested?: boolean
  symbols?: string
}

/**
 * Alpaca 交易服务类
 */
class AlpacaTradingService {
  /**
   * 发送 API 请求
   */
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const baseUrl = alpacaAuth.getBaseUrl()
    const headers = alpacaAuth.getAuthHeaders()

    const response = await fetch(`${baseUrl}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...headers,
        ...options.headers,
      },
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: `HTTP ${response.status}` }))
      throw new Error(error.message || `Request failed: ${response.status}`)
    }

    // 204 No Content
    if (response.status === 204) {
      return undefined as T
    }

    return response.json()
  }

  // ==================== 账户 ====================

  /**
   * 获取账户信息
   */
  async getAccount(): Promise<AlpacaAccount> {
    return this.request<AlpacaAccount>('/v2/account')
  }

  /**
   * 获取账户配置
   */
  async getAccountConfigurations(): Promise<{
    dtbp_check: string
    fractional_trading: boolean
    max_margin_multiplier: string
    no_shorting: boolean
    pdt_check: string
    suspend_trade: boolean
    trade_confirm_email: string
  }> {
    return this.request('/v2/account/configurations')
  }

  /**
   * 更新账户配置
   */
  async updateAccountConfigurations(config: {
    dtbp_check?: string
    fractional_trading?: boolean
    no_shorting?: boolean
    suspend_trade?: boolean
    trade_confirm_email?: string
  }): Promise<void> {
    return this.request('/v2/account/configurations', {
      method: 'PATCH',
      body: JSON.stringify(config),
    })
  }

  // ==================== 订单 ====================

  /**
   * 提交订单
   */
  async submitOrder(order: OrderRequest): Promise<Order> {
    return this.request<Order>('/v2/orders', {
      method: 'POST',
      body: JSON.stringify(order),
    })
  }

  /**
   * 市价买入
   */
  async marketBuy(symbol: string, qty: number, options: Partial<OrderRequest> = {}): Promise<Order> {
    return this.submitOrder({
      symbol,
      qty,
      side: 'buy',
      type: 'market',
      time_in_force: 'day',
      ...options,
    })
  }

  /**
   * 市价卖出
   */
  async marketSell(symbol: string, qty: number, options: Partial<OrderRequest> = {}): Promise<Order> {
    return this.submitOrder({
      symbol,
      qty,
      side: 'sell',
      type: 'market',
      time_in_force: 'day',
      ...options,
    })
  }

  /**
   * 限价买入
   */
  async limitBuy(symbol: string, qty: number, limitPrice: number, options: Partial<OrderRequest> = {}): Promise<Order> {
    return this.submitOrder({
      symbol,
      qty,
      side: 'buy',
      type: 'limit',
      time_in_force: 'day',
      limit_price: limitPrice,
      ...options,
    })
  }

  /**
   * 限价卖出
   */
  async limitSell(symbol: string, qty: number, limitPrice: number, options: Partial<OrderRequest> = {}): Promise<Order> {
    return this.submitOrder({
      symbol,
      qty,
      side: 'sell',
      type: 'limit',
      time_in_force: 'day',
      limit_price: limitPrice,
      ...options,
    })
  }

  /**
   * 止损单
   */
  async stopOrder(symbol: string, qty: number, stopPrice: number, side: OrderSide, options: Partial<OrderRequest> = {}): Promise<Order> {
    return this.submitOrder({
      symbol,
      qty,
      side,
      type: 'stop',
      time_in_force: 'day',
      stop_price: stopPrice,
      ...options,
    })
  }

  /**
   * 止损限价单
   */
  async stopLimitOrder(
    symbol: string,
    qty: number,
    stopPrice: number,
    limitPrice: number,
    side: OrderSide,
    options: Partial<OrderRequest> = {}
  ): Promise<Order> {
    return this.submitOrder({
      symbol,
      qty,
      side,
      type: 'stop_limit',
      time_in_force: 'day',
      stop_price: stopPrice,
      limit_price: limitPrice,
      ...options,
    })
  }

  /**
   * 括号订单 (带止盈止损)
   */
  async bracketOrder(
    symbol: string,
    qty: number,
    side: OrderSide,
    takeProfitPrice: number,
    stopLossPrice: number,
    options: Partial<OrderRequest> = {}
  ): Promise<Order> {
    return this.submitOrder({
      symbol,
      qty,
      side,
      type: 'market',
      time_in_force: 'day',
      order_class: 'bracket',
      take_profit: { limit_price: takeProfitPrice },
      stop_loss: { stop_price: stopLossPrice },
      ...options,
    })
  }

  /**
   * 获取订单列表
   */
  async getOrders(query: OrdersQuery = {}): Promise<Order[]> {
    const params = new URLSearchParams()
    Object.entries(query).forEach(([key, value]) => {
      if (value !== undefined) {
        params.set(key, String(value))
      }
    })

    const queryString = params.toString()
    return this.request<Order[]>(`/v2/orders${queryString ? `?${queryString}` : ''}`)
  }

  /**
   * 获取单个订单
   */
  async getOrder(orderId: string): Promise<Order> {
    return this.request<Order>(`/v2/orders/${orderId}`)
  }

  /**
   * 通过客户端 ID 获取订单
   */
  async getOrderByClientId(clientOrderId: string): Promise<Order> {
    return this.request<Order>(`/v2/orders:by_client_order_id?client_order_id=${clientOrderId}`)
  }

  /**
   * 取消订单
   */
  async cancelOrder(orderId: string): Promise<void> {
    return this.request<void>(`/v2/orders/${orderId}`, {
      method: 'DELETE',
    })
  }

  /**
   * 取消所有订单
   */
  async cancelAllOrders(): Promise<{ id: string; status: number; body: unknown }[]> {
    return this.request('/v2/orders', {
      method: 'DELETE',
    })
  }

  /**
   * 替换/修改订单
   */
  async replaceOrder(
    orderId: string,
    changes: {
      qty?: number
      time_in_force?: TimeInForce
      limit_price?: number
      stop_price?: number
      trail?: number
      client_order_id?: string
    }
  ): Promise<Order> {
    return this.request<Order>(`/v2/orders/${orderId}`, {
      method: 'PATCH',
      body: JSON.stringify(changes),
    })
  }

  // ==================== 持仓 ====================

  /**
   * 获取所有持仓
   */
  async getPositions(): Promise<Position[]> {
    return this.request<Position[]>('/v2/positions')
  }

  /**
   * 获取单个持仓
   */
  async getPosition(symbol: string): Promise<Position> {
    return this.request<Position>(`/v2/positions/${symbol}`)
  }

  /**
   * 平仓
   */
  async closePosition(symbol: string, qty?: number, percentage?: number): Promise<Order> {
    const params = new URLSearchParams()
    if (qty !== undefined) params.set('qty', String(qty))
    if (percentage !== undefined) params.set('percentage', String(percentage))

    const queryString = params.toString()
    return this.request<Order>(`/v2/positions/${symbol}${queryString ? `?${queryString}` : ''}`, {
      method: 'DELETE',
    })
  }

  /**
   * 全部平仓
   */
  async closeAllPositions(cancelOrders: boolean = false): Promise<{ symbol: string; status: number; body: unknown }[]> {
    return this.request(`/v2/positions?cancel_orders=${cancelOrders}`, {
      method: 'DELETE',
    })
  }

  // ==================== 资产 ====================

  /**
   * 获取资产列表
   */
  async getAssets(status?: 'active' | 'inactive', assetClass?: string): Promise<Asset[]> {
    const params = new URLSearchParams()
    if (status) params.set('status', status)
    if (assetClass) params.set('asset_class', assetClass)

    const queryString = params.toString()
    return this.request<Asset[]>(`/v2/assets${queryString ? `?${queryString}` : ''}`)
  }

  /**
   * 获取单个资产
   */
  async getAsset(symbolOrId: string): Promise<Asset> {
    return this.request<Asset>(`/v2/assets/${symbolOrId}`)
  }

  // ==================== 市场 ====================

  /**
   * 获取市场时钟
   */
  async getClock(): Promise<Clock> {
    return this.request<Clock>('/v2/clock')
  }

  /**
   * 获取交易日历
   */
  async getCalendar(start?: string, end?: string): Promise<Calendar[]> {
    const params = new URLSearchParams()
    if (start) params.set('start', start)
    if (end) params.set('end', end)

    const queryString = params.toString()
    return this.request<Calendar[]>(`/v2/calendar${queryString ? `?${queryString}` : ''}`)
  }

  // ==================== 活动/历史 ====================

  /**
   * 获取账户活动
   */
  async getAccountActivities(
    activityTypes?: string[],
    options: {
      after?: string
      until?: string
      direction?: 'asc' | 'desc'
      date?: string
      page_size?: number
      page_token?: string
    } = {}
  ): Promise<{
    id: string
    activity_type: string
    transaction_time: string
    symbol?: string
    side?: string
    qty?: string
    price?: string
    net_amount?: string
  }[]> {
    const params = new URLSearchParams()
    if (activityTypes?.length) params.set('activity_types', activityTypes.join(','))
    Object.entries(options).forEach(([key, value]) => {
      if (value !== undefined) params.set(key, String(value))
    })

    const queryString = params.toString()
    return this.request(`/v2/account/activities${queryString ? `?${queryString}` : ''}`)
  }
}

// 单例实例
export const alpacaTrading = new AlpacaTradingService()

export default AlpacaTradingService
