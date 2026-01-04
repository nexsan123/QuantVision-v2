/**
 * Phase 12: \u6267\u884c\u5c42\u5347\u7ea7 - \u4ea4\u6613\u7c7b\u578b\u5b9a\u4e49
 *
 * \u5305\u542b:
 * - \u5238\u5546\u63a5\u53e3\u7c7b\u578b
 * - \u8ba2\u5355\u7ba1\u7406\u7c7b\u578b
 * - \u6ed1\u70b9\u6a21\u578b\u7c7b\u578b
 * - WebSocket \u4ea4\u6613\u4e8b\u4ef6\u7c7b\u578b
 */

// ============ \u5238\u5546\u7c7b\u578b ============

// \u652f\u6301\u7684\u5238\u5546
export type BrokerType = 'alpaca' | 'interactive_brokers' | 'paper'

// \u5238\u5546\u8fde\u63a5\u72b6\u6001
export type BrokerConnectionStatus = 'disconnected' | 'connecting' | 'connected' | 'error' | 'maintenance'

// \u5238\u5546\u914d\u7f6e
export interface BrokerConfig {
  broker: BrokerType
  apiKey?: string
  secretKey?: string
  paperTrading: boolean
  baseUrl?: string
}

// \u5238\u5546\u8d26\u6237\u4fe1\u606f
export interface BrokerAccount {
  id: string
  broker: BrokerType
  accountNumber: string
  status: 'active' | 'inactive' | 'restricted'
  currency: string
  buyingPower: number
  cash: number
  portfolioValue: number
  equity: number
  lastEquity: number
  longMarketValue: number
  shortMarketValue: number
  initialMargin: number
  maintenanceMargin: number
  daytradeCount: number
  patternDayTrader: boolean
  tradingBlocked: boolean
  transfersBlocked: boolean
  accountBlocked: boolean
  createdAt: string
  paperTrading: boolean
}

// \u5238\u5546\u6301\u4ed3
export interface BrokerPosition {
  symbol: string
  quantity: number
  side: 'long' | 'short'
  avgEntryPrice: number
  marketValue: number
  currentPrice: number
  unrealizedPnl: number
  unrealizedPnlPercent: number
  costBasis: number
  assetClass: string
  exchange: string
}

// WebSocket \u8fde\u63a5\u72b6\u6001
export type ConnectionStatus = 'disconnected' | 'connecting' | 'connected' | 'error' | 'reconnecting'

// \u4ea4\u6613\u6a21\u5f0f
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

// \u9ed8\u8ba4 WebSocket \u914d\u7f6e
export const DEFAULT_WS_CONFIG: WebSocketConfig = {
  url: 'ws://localhost:8000/ws/trading',
  reconnectInterval: 3000,
  maxReconnectAttempts: 10,
  heartbeatInterval: 30000,
  mode: 'paper',
}

// ============ \u6ed1\u70b9\u6a21\u578b\u7c7b\u578b ============

// \u6ed1\u70b9\u6a21\u578b\u7c7b\u578b
export type SlippageModelType = 'fixed' | 'volume_based' | 'sqrt' | 'almgren_chriss'

// Almgren-Chriss \u6ed1\u70b9\u6a21\u578b\u53c2\u6570
export interface AlmgrenChrissParams {
  eta: number           // \u4e34\u65f6\u51b2\u51fb\u7cfb\u6570 (0.1-0.5)
  gamma: number         // \u6c38\u4e45\u51b2\u51fb\u7cfb\u6570 (0.01-0.05)
  sigma: number         // \u65e5\u6ce2\u52a8\u7387
  spreadBps: number     // \u4e70\u5356\u4ef7\u5dee (\u57fa\u70b9)
}

// \u6ed1\u70b9\u8ba1\u7b97\u7ed3\u679c
export interface SlippageResult {
  totalSlippage: number       // \u603b\u6ed1\u70b9
  fixedCost: number           // \u56fa\u5b9a\u6210\u672c (spread/2)
  temporaryImpact: number     // \u4e34\u65f6\u51b2\u51fb
  permanentImpact: number     // \u6c38\u4e45\u51b2\u51fb
  slippageBps: number         // \u6ed1\u70b9 (\u57fa\u70b9)
  slippagePercent: number     // \u6ed1\u70b9 (\u767e\u5206\u6bd4)
}

// \u6ed1\u70b9\u914d\u7f6e
export interface SlippageConfig {
  modelType: SlippageModelType
  fixedRate?: number          // \u56fa\u5b9a\u6ed1\u70b9\u7387
  almgrenChriss?: AlmgrenChrissParams
}

// ============ \u589e\u5f3a\u7684\u8ba2\u5355\u7c7b\u578b ============

// \u6267\u884c\u7b97\u6cd5
export type ExecutionAlgorithm = 'market' | 'twap' | 'vwap' | 'pov' | 'is'

// TWAP \u53c2\u6570
export interface TWAPParams {
  durationMinutes: number     // \u6267\u884c\u65f6\u957f (\u5206\u949f)
  intervalSeconds: number     // \u4e0b\u5355\u95f4\u9694 (\u79d2)
}

// VWAP \u53c2\u6570
export interface VWAPParams {
  startTime: string           // \u5f00\u59cb\u65f6\u95f4
  endTime: string             // \u7ed3\u675f\u65f6\u95f4
  participationRate: number   // \u53c2\u4e0e\u7387
}

// POV \u53c2\u6570
export interface POVParams {
  targetRate: number          // \u76ee\u6807\u53c2\u4e0e\u7387 (0-1)
  maxRate: number             // \u6700\u5927\u53c2\u4e0e\u7387
}

// \u6267\u884c\u7b97\u6cd5\u914d\u7f6e
export interface ExecutionConfig {
  algorithm: ExecutionAlgorithm
  twap?: TWAPParams
  vwap?: VWAPParams
  pov?: POVParams
}

// \u8ba2\u5355\u521b\u5efa\u8bf7\u6c42
export interface CreateOrderRequest {
  symbol: string
  side: OrderSide
  quantity: number
  orderType: OrderType
  limitPrice?: number
  stopPrice?: number
  timeInForce?: 'day' | 'gtc' | 'ioc' | 'fok'
  extendedHours?: boolean
  clientOrderId?: string
  execution?: ExecutionConfig
}

// \u8ba2\u5355\u54cd\u5e94
export interface OrderResponse {
  id: string
  clientOrderId: string
  symbol: string
  side: OrderSide
  quantity: number
  filledQuantity: number
  orderType: OrderType
  status: OrderStatus
  limitPrice?: number
  stopPrice?: number
  filledAvgPrice?: number
  createdAt: string
  updatedAt: string
  submittedAt?: string
  filledAt?: string
  cancelledAt?: string
  expiredAt?: string
  broker: BrokerType
  brokerOrderId?: string
  commission: number
  slippage: number
}

// ============ \u4ea4\u6613\u4e2d\u5fc3\u72b6\u6001 ============

// \u4ea4\u6613\u4e2d\u5fc3\u72b6\u6001
export interface TradingCenterState {
  broker: BrokerType
  connectionStatus: BrokerConnectionStatus
  mode: TradingMode
  account: BrokerAccount | null
  positions: BrokerPosition[]
  orders: OrderResponse[]
  recentTrades: OrderResponse[]
  slippageConfig: SlippageConfig
  isLoading: boolean
  error: string | null
}

// \u4ea4\u6613\u7edf\u8ba1
export interface TradingStats {
  totalTrades: number
  winningTrades: number
  losingTrades: number
  winRate: number
  totalPnl: number
  totalCommission: number
  totalSlippage: number
  avgSlippageBps: number
  avgTradeSize: number
  largestWin: number
  largestLoss: number
}

// \u4ea4\u6613\u6210\u672c\u5206\u6790 (TCA)
export interface TradeCostAnalysis {
  symbol: string
  executionPrice: number
  arrivalPrice: number
  benchmarkPrice: number
  implementationShortfall: number
  implementationShortfallBps: number
  commission: number
  slippage: number
  marketImpact: number
  timingCost: number
  opportunityCost: number
}

// \u5238\u5546\u72b6\u6001\u6458\u8981
export interface BrokerStatusSummary {
  broker: BrokerType
  status: BrokerConnectionStatus
  paperTrading: boolean
  account: {
    equity: number
    buyingPower: number
    cash: number
    dayPnl: number
    dayPnlPercent: number
  } | null
  marketStatus: 'open' | 'closed' | 'pre_market' | 'after_hours'
  lastUpdate: string
}

// \u5238\u5546\u6807\u7b7e
export const BROKER_LABELS: Record<BrokerType, string> = {
  alpaca: 'Alpaca',
  interactive_brokers: 'Interactive Brokers',
  paper: '\u6a21\u62df\u4ea4\u6613',
}

// \u6ed1\u70b9\u6a21\u578b\u6807\u7b7e
export const SLIPPAGE_MODEL_LABELS: Record<SlippageModelType, string> = {
  fixed: '\u56fa\u5b9a\u6bd4\u4f8b',
  volume_based: '\u6210\u4ea4\u91cf\u76f8\u5173',
  sqrt: '\u5e73\u65b9\u6839\u6a21\u578b',
  almgren_chriss: 'Almgren-Chriss',
}

// \u6267\u884c\u7b97\u6cd5\u6807\u7b7e
export const EXECUTION_ALGO_LABELS: Record<ExecutionAlgorithm, string> = {
  market: '\u5e02\u4ef7\u5355',
  twap: 'TWAP (\u65f6\u95f4\u52a0\u6743)',
  vwap: 'VWAP (\u6210\u4ea4\u91cf\u52a0\u6743)',
  pov: 'POV (\u53c2\u4e0e\u7387)',
  is: 'IS (\u6267\u884c\u7f3a\u53e3\u6700\u5c0f\u5316)',
}
