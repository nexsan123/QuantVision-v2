/**
 * Alpaca WebSocket 服务
 * Sprint 9: T13 - 实时订单和交易更新
 *
 * 支持的数据流:
 * - trade_updates: 订单状态更新
 * - account_updates: 账户更新 (余额、持仓等)
 */
import { alpacaAuth } from './alpacaAuth'

// WebSocket URLs
const ALPACA_STREAM_PAPER = 'wss://paper-api.alpaca.markets/stream'
const ALPACA_STREAM_LIVE = 'wss://api.alpaca.markets/stream'

// ==================== 类型定义 ====================

// 连接状态
export type ConnectionStatus = 'disconnected' | 'connecting' | 'connected' | 'authenticated' | 'error'

// 订单更新事件
export type TradeUpdateEvent =
  | 'new'
  | 'fill'
  | 'partial_fill'
  | 'canceled'
  | 'expired'
  | 'done_for_day'
  | 'replaced'
  | 'rejected'
  | 'pending_new'
  | 'stopped'
  | 'pending_cancel'
  | 'pending_replace'
  | 'calculated'
  | 'suspended'
  | 'order_replace_rejected'
  | 'order_cancel_rejected'

// 订单数据
export interface TradeUpdateOrder {
  id: string
  client_order_id: string
  created_at: string
  updated_at: string
  submitted_at: string
  filled_at: string | null
  expired_at: string | null
  canceled_at: string | null
  failed_at: string | null
  asset_id: string
  symbol: string
  asset_class: string
  qty: string
  filled_qty: string
  filled_avg_price: string | null
  order_type: string
  type: string
  side: 'buy' | 'sell'
  time_in_force: string
  limit_price: string | null
  stop_price: string | null
  status: string
  extended_hours: boolean
}

// 交易更新消息
export interface TradeUpdate {
  event: TradeUpdateEvent
  timestamp: string
  order: TradeUpdateOrder
  position_qty?: string
  price?: string
  qty?: string
  execution_id?: string
}

// 账户更新消息
export interface AccountUpdate {
  id: string
  created_at: string
  updated_at: string
  deleted_at: string | null
  status: string
  currency: string
  cash: string
  cash_withdrawable: string
}

// 回调类型
export type TradeUpdateCallback = (update: TradeUpdate) => void
export type AccountUpdateCallback = (update: AccountUpdate) => void
export type StatusCallback = (status: ConnectionStatus) => void

/**
 * Alpaca WebSocket 服务类
 */
class AlpacaWebSocketService {
  private ws: WebSocket | null = null
  private status: ConnectionStatus = 'disconnected'
  private reconnectAttempts = 0
  private maxReconnectAttempts = 10
  private reconnectInterval = 3000
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null
  private heartbeatTimer: ReturnType<typeof setInterval> | null = null

  // 回调管理
  private tradeUpdateCallbacks: Set<TradeUpdateCallback> = new Set()
  private accountUpdateCallbacks: Set<AccountUpdateCallback> = new Set()
  private statusCallbacks: Set<StatusCallback> = new Set()

  // 订阅的频道
  private subscribedStreams: Set<string> = new Set()

  /**
   * 获取 WebSocket URL
   */
  private getWebSocketUrl(): string {
    const env = alpacaAuth.getEnvironment()
    return env === 'live' ? ALPACA_STREAM_LIVE : ALPACA_STREAM_PAPER
  }

  /**
   * 连接到 Alpaca WebSocket
   */
  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      if (!alpacaAuth.isAuthenticated()) {
        reject(new Error('Not authenticated'))
        return
      }

      if (this.ws?.readyState === WebSocket.OPEN) {
        resolve()
        return
      }

      this.setStatus('connecting')

      try {
        this.ws = new WebSocket(this.getWebSocketUrl())

        this.ws.onopen = () => {
          console.log('[Alpaca WS] Connected')
          this.setStatus('connected')
          this.authenticate()
        }

        this.ws.onmessage = (event) => {
          this.handleMessage(event.data)
        }

        this.ws.onerror = (error) => {
          console.error('[Alpaca WS] Error:', error)
          this.setStatus('error')
          reject(error)
        }

        this.ws.onclose = (event) => {
          console.log('[Alpaca WS] Disconnected:', event.code, event.reason)
          this.setStatus('disconnected')
          this.stopHeartbeat()
          this.handleReconnect()
        }

        // 等待认证成功
        const authTimeout = setTimeout(() => {
          if (this.status !== 'authenticated') {
            reject(new Error('Authentication timeout'))
          }
        }, 10000)

        const checkAuth = () => {
          if (this.status === 'authenticated') {
            clearTimeout(authTimeout)
            resolve()
          } else if (this.status === 'error') {
            clearTimeout(authTimeout)
            reject(new Error('Connection failed'))
          } else {
            setTimeout(checkAuth, 100)
          }
        }
        checkAuth()

      } catch (error) {
        this.setStatus('error')
        reject(error)
      }
    })
  }

  /**
   * 发送认证消息
   */
  private authenticate(): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) return

    const credentials = alpacaAuth.getAuthHeaders()

    this.send({
      action: 'auth',
      key: credentials['APCA-API-KEY-ID'] || '',
      secret: credentials['APCA-API-SECRET-KEY'] || '',
    })
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

      // 处理不同类型的消息
      if (message.stream === 'authorization') {
        this.handleAuthMessage(message)
      } else if (message.stream === 'listening') {
        console.log('[Alpaca WS] Listening to:', message.data.streams)
      } else if (message.stream === 'trade_updates') {
        this.handleTradeUpdate(message.data)
      } else if (message.stream === 'account_updates') {
        this.handleAccountUpdate(message.data)
      }
    } catch (error) {
      console.error('[Alpaca WS] Parse error:', error)
    }
  }

  /**
   * 处理认证消息
   */
  private handleAuthMessage(message: { data: { status: string; action: string } }): void {
    if (message.data.status === 'authorized') {
      console.log('[Alpaca WS] Authenticated')
      this.setStatus('authenticated')
      this.reconnectAttempts = 0
      this.startHeartbeat()
      // 重新订阅之前的频道
      this.resubscribe()
    } else {
      console.error('[Alpaca WS] Authentication failed')
      this.setStatus('error')
    }
  }

  /**
   * 处理交易更新
   */
  private handleTradeUpdate(data: TradeUpdate): void {
    console.log('[Alpaca WS] Trade update:', data.event, data.order.symbol)
    this.tradeUpdateCallbacks.forEach(cb => cb(data))
  }

  /**
   * 处理账户更新
   */
  private handleAccountUpdate(data: AccountUpdate): void {
    console.log('[Alpaca WS] Account update')
    this.accountUpdateCallbacks.forEach(cb => cb(data))
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
    // Alpaca 不需要心跳，但我们可以定期检查连接
    this.heartbeatTimer = setInterval(() => {
      if (this.ws?.readyState !== WebSocket.OPEN) {
        console.log('[Alpaca WS] Connection lost, reconnecting...')
        this.handleReconnect()
      }
    }, 30000)
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
      console.error('[Alpaca WS] Max reconnect attempts reached')
      return
    }

    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
    }

    this.reconnectAttempts++
    console.log(`[Alpaca WS] Reconnecting... (${this.reconnectAttempts})`)

    this.reconnectTimer = setTimeout(() => {
      this.connect().catch(console.error)
    }, this.reconnectInterval)
  }

  /**
   * 重新订阅
   */
  private resubscribe(): void {
    if (this.subscribedStreams.size > 0) {
      this.send({
        action: 'listen',
        data: {
          streams: Array.from(this.subscribedStreams),
        },
      })
    }
  }

  /**
   * 订阅交易更新
   */
  subscribeTradeUpdates(callback: TradeUpdateCallback): () => void {
    this.tradeUpdateCallbacks.add(callback)

    if (!this.subscribedStreams.has('trade_updates')) {
      this.subscribedStreams.add('trade_updates')
      if (this.status === 'authenticated') {
        this.send({
          action: 'listen',
          data: {
            streams: ['trade_updates'],
          },
        })
      }
    }

    return () => {
      this.tradeUpdateCallbacks.delete(callback)
    }
  }

  /**
   * 订阅账户更新
   */
  subscribeAccountUpdates(callback: AccountUpdateCallback): () => void {
    this.accountUpdateCallbacks.add(callback)

    if (!this.subscribedStreams.has('account_updates')) {
      this.subscribedStreams.add('account_updates')
      if (this.status === 'authenticated') {
        this.send({
          action: 'listen',
          data: {
            streams: ['account_updates'],
          },
        })
      }
    }

    return () => {
      this.accountUpdateCallbacks.delete(callback)
    }
  }

  /**
   * 订阅所有更新
   */
  subscribeAll(
    onTradeUpdate: TradeUpdateCallback,
    onAccountUpdate?: AccountUpdateCallback
  ): () => void {
    const unsub1 = this.subscribeTradeUpdates(onTradeUpdate)
    const unsub2 = onAccountUpdate ? this.subscribeAccountUpdates(onAccountUpdate) : () => {}

    return () => {
      unsub1()
      unsub2()
    }
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

    this.subscribedStreams.clear()
    this.tradeUpdateCallbacks.clear()
    this.accountUpdateCallbacks.clear()
    this.setStatus('disconnected')
  }
}

// 单例实例
export const alpacaWebSocket = new AlpacaWebSocketService()

export default AlpacaWebSocketService
