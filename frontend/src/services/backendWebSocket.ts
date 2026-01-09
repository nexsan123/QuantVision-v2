/**
 * 后端 WebSocket 客户端
 * Sprint 11: T25 - WebSocket 客户端连接
 *
 * 连接后端 WebSocket 网关，接收实时数据推送
 */

import { getWsUrl } from './backendApi'

// ==================== 类型定义 ====================

export type ConnectionStatus = 'disconnected' | 'connecting' | 'connected' | 'error'

// 订单事件
export interface OrderEvent {
  id: string
  type: 'order_new' | 'order_fill' | 'order_partial_fill' | 'order_canceled' | 'order_rejected'
  timestamp: string
  orderId: string
  symbol: string
  side: 'buy' | 'sell'
  orderType: string
  quantity: number
  filledQuantity: number
  filledPrice: number
  status: string
  event: string
}

// 持仓快照
export interface PositionsSnapshot {
  id: string
  type: 'positions_snapshot'
  timestamp: string
  positions: Array<{
    symbol: string
    side: 'long' | 'short'
    quantity: number
    avg_entry_price: number
    current_price: number
    market_value: number
    unrealized_pnl: number
    unrealized_pnl_pct: number
    weight_pct: number
  }>
  count: number
}

// 状态更新
export interface StatusUpdate {
  id: string
  type: 'status_update' | 'initial_status'
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
}

// 风险预警
export interface RiskAlertEvent {
  id: string
  type: 'risk_alert'
  timestamp: string
  level: 'info' | 'warning' | 'critical'
  title: string
  message: string
  metric: string
  currentValue: number
  threshold: number
}

// 系统消息
export interface SystemMessage {
  id: string
  type: 'system_message'
  timestamp: string
  level: 'success' | 'info' | 'warning' | 'error'
  title: string
  message: string
}

// WebSocket 消息类型
export type WebSocketEvent =
  | OrderEvent
  | PositionsSnapshot
  | StatusUpdate
  | RiskAlertEvent
  | SystemMessage

// 回调类型
export type EventCallback = (event: WebSocketEvent) => void
export type StatusCallback = (status: ConnectionStatus) => void

/**
 * 后端 WebSocket 服务类
 */
class BackendWebSocketService {
  private ws: WebSocket | null = null
  private status: ConnectionStatus = 'disconnected'
  private reconnectAttempts = 0
  private maxReconnectAttempts = 10
  private reconnectInterval = 3000
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null
  private heartbeatTimer: ReturnType<typeof setInterval> | null = null
  private heartbeatInterval = 30000

  // 回调管理
  private eventCallbacks: Set<EventCallback> = new Set()
  private statusCallbacks: Set<StatusCallback> = new Set()

  // 订阅的频道
  private subscribedChannels: Set<string> = new Set(['all'])

  /**
   * 连接到后端 WebSocket
   */
  connect(mode: 'paper' | 'live' = 'paper'): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        resolve()
        return
      }

      this.setStatus('connecting')

      try {
        const wsUrl = `${getWsUrl()}/ws/alpaca?mode=${mode}`
        this.ws = new WebSocket(wsUrl)

        this.ws.onopen = () => {
          console.log('[Backend WS] Connected')
          this.setStatus('connected')
          this.reconnectAttempts = 0
          this.startHeartbeat()
          resolve()
        }

        this.ws.onmessage = (event) => {
          this.handleMessage(event.data)
        }

        this.ws.onerror = (error) => {
          console.error('[Backend WS] Error:', error)
          this.setStatus('error')
          reject(error)
        }

        this.ws.onclose = (event) => {
          console.log('[Backend WS] Disconnected:', event.code, event.reason)
          this.setStatus('disconnected')
          this.stopHeartbeat()
          this.handleReconnect()
        }

      } catch (error) {
        this.setStatus('error')
        reject(error)
      }
    })
  }

  /**
   * 断开连接
   */
  disconnect(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }

    this.stopHeartbeat()

    if (this.ws) {
      this.ws.close()
      this.ws = null
    }

    this.subscribedChannels.clear()
    this.subscribedChannels.add('all')
    this.setStatus('disconnected')
  }

  /**
   * 发送消息
   */
  private send(message: object): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message))
    }
  }

  /**
   * 处理接收到的消息
   */
  private handleMessage(data: string): void {
    try {
      const message = JSON.parse(data)

      if (message.type === 'heartbeat') {
        // 心跳响应，忽略
        return
      }

      if (message.type === 'event' && message.payload) {
        const event = message.payload as WebSocketEvent
        this.notifyEventCallbacks(event)
      }

    } catch (error) {
      console.error('[Backend WS] Parse error:', error)
    }
  }

  /**
   * 通知事件回调
   */
  private notifyEventCallbacks(event: WebSocketEvent): void {
    this.eventCallbacks.forEach(callback => {
      try {
        callback(event)
      } catch (error) {
        console.error('[Backend WS] Callback error:', error)
      }
    })
  }

  /**
   * 设置连接状态
   */
  private setStatus(status: ConnectionStatus): void {
    this.status = status
    this.statusCallbacks.forEach(cb => cb(status))
  }

  /**
   * 启动心跳
   */
  private startHeartbeat(): void {
    this.stopHeartbeat()
    this.heartbeatTimer = setInterval(() => {
      this.send({ type: 'heartbeat' })
    }, this.heartbeatInterval)
  }

  /**
   * 停止心跳
   */
  private stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer)
      this.heartbeatTimer = null
    }
  }

  /**
   * 处理重连
   */
  private handleReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('[Backend WS] Max reconnect attempts reached')
      return
    }

    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
    }

    this.reconnectAttempts++
    console.log(`[Backend WS] Reconnecting... (${this.reconnectAttempts})`)

    this.reconnectTimer = setTimeout(() => {
      this.connect().catch(console.error)
    }, this.reconnectInterval)
  }

  /**
   * 订阅频道
   */
  subscribe(channel: string): void {
    if (!this.subscribedChannels.has(channel)) {
      this.subscribedChannels.add(channel)
      this.send({
        type: 'subscribe',
        channel,
      })
    }
  }

  /**
   * 取消订阅
   */
  unsubscribe(channel: string): void {
    this.subscribedChannels.delete(channel)
    this.send({
      type: 'unsubscribe',
      channel,
    })
  }

  /**
   * 请求刷新持仓
   */
  refreshPositions(): void {
    this.send({ type: 'refresh_positions' })
  }

  /**
   * 请求刷新状态
   */
  refreshStatus(): void {
    this.send({ type: 'refresh_status' })
  }

  /**
   * 订阅事件
   */
  onEvent(callback: EventCallback): () => void {
    this.eventCallbacks.add(callback)
    return () => this.eventCallbacks.delete(callback)
  }

  /**
   * 监听连接状态
   */
  onStatusChange(callback: StatusCallback): () => void {
    this.statusCallbacks.add(callback)
    return () => this.statusCallbacks.delete(callback)
  }

  /**
   * 获取当前状态
   */
  getStatus(): ConnectionStatus {
    return this.status
  }

  /**
   * 是否已连接
   */
  isConnected(): boolean {
    return this.status === 'connected'
  }
}

// 单例实例
export const backendWebSocket = new BackendWebSocketService()

export default BackendWebSocketService
