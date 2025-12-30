/**
 * Trading 组件导出
 *
 * 实时交易 UI 组件模块
 */

export { TradingEventCard } from './TradingEventCard'
export { ConnectionStatus } from './ConnectionStatus'
export { TradingModeToggle } from './TradingModeToggle'
export { PriceTicker, PriceGrid } from './PriceTicker'

// 类型重导出
export type {
  ConnectionStatus as ConnectionStatusType,
  TradingMode,
  TradingEvent,
  TradingEventType,
  OrderEvent,
  PositionEvent,
  PriceUpdateEvent,
  PnLUpdateEvent,
  RiskAlertEvent,
  SystemMessageEvent,
  PriceData,
  PositionSummary,
  PortfolioSummary,
  TradingStreamState,
  SubscriptionChannel,
  WebSocketConfig,
} from '@/types/trading'

export { DEFAULT_WS_CONFIG } from '@/types/trading'
