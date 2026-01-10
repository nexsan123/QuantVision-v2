/**
 * 服务统一导出
 * Sprint 11: 服务层整合
 */

// Sprint 7: Polygon 行情服务
export { getPolygonWebSocket, PolygonWebSocketService } from './polygonWebSocket'
export { polygonApi } from './polygonApi'
export { preMarketService } from './preMarketService'

// Sprint 8: Alpaca 直连服务 (前端直接调用 Alpaca)
export { alpacaAuth } from './alpacaAuth'
export { alpacaTrading } from './alpacaTrading'
export { alpacaWebSocket } from './alpacaWebSocket'

// Sprint 11: 后端 API 服务 (通过后端代理)
export {
  realtimeApi,
  strategyApi,
  signalApi,
  alertApi,
  healthApi,
  getWsUrl,
} from './backendApi'
export type {
  RealtimeStatus,
  PositionDetail,
  OrderDetail,
  MarketClock,
  Strategy,
  StrategyConfig,
  Signal,
  RiskAlert,
  AlertConfig,
} from './backendApi'

// Sprint 11: 后端 WebSocket 服务
export { backendWebSocket } from './backendWebSocket'
export type {
  ConnectionStatus,
  OrderEvent,
  PositionsSnapshot,
  StatusUpdate,
  RiskAlertEvent,
  SystemMessage,
  WebSocketEvent,
} from './backendWebSocket'
