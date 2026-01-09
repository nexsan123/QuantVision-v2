/**
 * Hooks 统一导出
 * Sprint 7-8: 实时数据 + 交易 hooks
 * Sprint 11: 后端实时数据集成
 */

// 图表主题
export { default as useChartTheme } from './useChartTheme'

// 交易数据流
export { default as useTradingStream } from './useTradingStream'

// Sprint 7: 实时行情
export {
  useRealTimeQuote,
  useSingleQuote,
  default as useRealTimeQuoteDefault,
} from './useRealTimeQuote'
export type { RealTimeQuote } from './useRealTimeQuote'

// Sprint 7: 盘前扫描器
export {
  usePreMarketScanner,
  useGainers,
  useLosers,
  useHighVolume,
  default as usePreMarketScannerDefault,
} from './usePreMarketScanner'

// Sprint 8: 订单管理 (Alpaca 直连)
export {
  useOrders,
  useOrder,
  default as useOrdersDefault,
} from './useOrders'

// Sprint 8: 账户状态 (Alpaca 直连)
export {
  useAccount,
  usePositions,
  useMarketClock,
  useActivities,
  useTradingStatus,
  default as useAccountDefault,
} from './useAccount'

// Sprint 11: 后端实时数据 Hooks
export {
  useRealtimeStatus,
  useRealtimePositions,
  useRealtimeOrders,
  useMarketClock as useBackendMarketClock,
  useWebSocketConnection,
  useRealtimeEvents,
} from './useRealtime'
export type {
  UseRealtimeStatusResult,
  UseRealtimePositionsResult,
  UseRealtimeOrdersResult,
  UseMarketClockResult,
  UseWebSocketConnectionResult,
  UseRealtimeEventsResult,
} from './useRealtime'

// Sprint 12: 健康检查 Hooks
export {
  useBasicHealth,
  useDetailedHealth,
  useHealthMetrics,
  useConnectionCheck,
} from './useHealth'
export type {
  ComponentHealth,
  SystemMetrics,
  DetailedHealthResponse,
  BasicHealthResponse,
  HealthMetrics,
} from './useHealth'

// Sprint 13: 性能监控 Hooks
export {
  usePagePerformance,
  useRenderPerformance,
  useApiPerformance,
  useMemoryMonitor,
  useLongTaskMonitor,
} from './usePerformance'
export type {
  PerformanceMetrics,
  RenderMetrics,
  ApiCallMetrics,
  MemoryMetrics,
  LongTask,
} from './usePerformance'

// Sprint 13: 通知管理 Hooks
export {
  useRealtimeNotifications,
  useNotificationHistory,
  useNotificationRules,
  useNotificationStats,
} from './useNotifications'
export type {
  NotificationData,
  NotificationRecord,
  NotificationRule,
  NotificationStats,
  NotificationPriority,
  NotificationCategory,
  NotificationChannel,
} from './useNotifications'
