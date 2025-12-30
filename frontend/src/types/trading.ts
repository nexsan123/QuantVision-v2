/**
 * 实时交易类型定义
 *
 * WebSocket 交易事件和状态类型
 */

// WebSocket 连接状态
export type ConnectionStatus = 'disconnected' | 'connecting' | 'connected' | 'error' | 'reconnecting'

// 交易模式
export type TradingMode = 'live' | 'paper'

// 交易事件类型
export type TradingEventType =
  | 'order_submitted'      // 订单提交
  | 'order_filled'         // 订单成交
  | 'order_partial_fill'   // 部分成交
  | 'order_cancelled'      // 订单取消
  | 'order_rejected'       // 订单拒绝
  | 'position_opened'      // 开仓
  | 'position_closed'      // 平仓
  | 'position_updated'     // 持仓更新
  | 'price_update'         // 价格更新
  | 'pnl_update'           // 盈亏更新
  | 'risk_alert'           // 风险警报
  | 'system_message'       // 系统消息

// 订单方向
export type OrderSide = 'buy' | 'sell'

// 订单类型
export type OrderType = 'market' | 'limit' | 'stop' | 'stop_limit'

// 订单状态
export type OrderStatus =
  | 'pending'
  | 'submitted'
  | 'accepted'
  | 'partial_fill'
  | 'filled'
  | 'cancelled'
  | 'rejected'
  | 'expired'

// 基础交易事件
export interface BaseTradingEvent {
  id: string
  type: TradingEventType
  timestamp: string
  symbol?: string
}

// 订单事件
export interface OrderEvent extends BaseTradingEvent {
  type: 'order_submitted' | 'order_filled' | 'order_partial_fill' | 'order_cancelled' | 'order_rejected'
  orderId: string
  symbol: string
  side: OrderSide
  orderType: OrderType
  quantity: number
  price?: number
  filledQuantity?: number
  filledPrice?: number
  status: OrderStatus
  message?: string
}

// 持仓事件
export interface PositionEvent extends BaseTradingEvent {
  type: 'position_opened' | 'position_closed' | 'position_updated'
  symbol: string
  quantity: number
  avgPrice: number
  currentPrice: number
  unrealizedPnl: number
  realizedPnl?: number
  side: OrderSide
}

// 价格更新事件
export interface PriceUpdateEvent extends BaseTradingEvent {
  type: 'price_update'
  symbol: string
  price: number
  previousPrice: number
  change: number
  changePercent: number
  volume: number
  bid?: number
  ask?: number
}

// 盈亏更新事件
export interface PnLUpdateEvent extends BaseTradingEvent {
  type: 'pnl_update'
  totalUnrealizedPnl: number
  totalRealizedPnl: number
  dailyPnl: number
  portfolioValue: number
  cashBalance: number
}

// 风险警报事件
export interface RiskAlertEvent extends BaseTradingEvent {
  type: 'risk_alert'
  level: 'info' | 'warning' | 'critical'
  title: string
  message: string
  metric?: string
  currentValue?: number
  threshold?: number
}

// 系统消息事件
export interface SystemMessageEvent extends BaseTradingEvent {
  type: 'system_message'
  level: 'info' | 'warning' | 'error' | 'success'
  title: string
  message: string
}

// 所有交易事件联合类型
export type TradingEvent =
  | OrderEvent
  | PositionEvent
  | PriceUpdateEvent
  | PnLUpdateEvent
  | RiskAlertEvent
  | SystemMessageEvent

// WebSocket 消息格式
export interface WebSocketMessage {
  type: 'event' | 'heartbeat' | 'subscribe' | 'unsubscribe' | 'error'
  payload?: TradingEvent | TradingEvent[]
  channel?: string
  error?: string
}

// 订阅频道
export interface SubscriptionChannel {
  id: string
  type: 'orders' | 'positions' | 'prices' | 'pnl' | 'alerts' | 'all'
  symbols?: string[]
  active: boolean
}

// 交易流状态
export interface TradingStreamState {
  connectionStatus: ConnectionStatus
  mode: TradingMode
  events: TradingEvent[]
  subscriptions: SubscriptionChannel[]
  lastHeartbeat: string | null
  reconnectAttempts: number
  error: string | null
}

// 价格数据 (带动画状态)
export interface PriceData {
  symbol: string
  price: number
  previousPrice: number
  change: number
  changePercent: number
  direction: 'up' | 'down' | 'neutral'
  updatedAt: string
  animating: boolean
}

// 持仓摘要
export interface PositionSummary {
  symbol: string
  side: OrderSide
  quantity: number
  avgPrice: number
  currentPrice: number
  marketValue: number
  unrealizedPnl: number
  unrealizedPnlPercent: number
  dayChange: number
  dayChangePercent: number
}

// 组合摘要
export interface PortfolioSummary {
  totalValue: number
  cashBalance: number
  marketValue: number
  unrealizedPnl: number
  realizedPnl: number
  dailyPnl: number
  dailyPnlPercent: number
  positionCount: number
}

// WebSocket 配置
export interface WebSocketConfig {
  url: string
  reconnectInterval: number
  maxReconnectAttempts: number
  heartbeatInterval: number
  mode: TradingMode
}

// 默认 WebSocket 配置
export const DEFAULT_WS_CONFIG: WebSocketConfig = {
  url: 'ws://localhost:8000/ws/trading',
  reconnectInterval: 3000,
  maxReconnectAttempts: 10,
  heartbeatInterval: 30000,
  mode: 'paper',
}
