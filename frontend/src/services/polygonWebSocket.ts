/**
 * Polygon.io WebSocket 服务
 * Sprint 7: T5 - 实时行情数据推送
 *
 * 支持的数据类型:
 * - T.* : 实时交易 (Trades)
 * - Q.* : 实时报价 (Quotes)
 * - A.* : 秒级聚合 (Second Aggregates)
 * - AM.* : 分钟级聚合 (Minute Aggregates)
 */

// 消息类型
export type PolygonMessageType = 'T' | 'Q' | 'A' | 'AM'

// 交易数据
export interface PolygonTrade {
  ev: 'T'           // 事件类型
  sym: string       // 股票代码
  p: number         // 价格
  s: number         // 数量
  t: number         // 时间戳 (毫秒)
  c: number[]       // 交易条件
  x: number         // 交易所 ID
}

// 报价数据
export interface PolygonQuote {
  ev: 'Q'           // 事件类型
  sym: string       // 股票代码
  bp: number        // 买入价
  bs: number        // 买入量
  ap: number        // 卖出价
  as: number        // 卖出量
  t: number         // 时间戳
  x: number         // 交易所 ID
}

// 聚合数据 (秒/分钟)
export interface PolygonAggregate {
  ev: 'A' | 'AM'    // 事件类型
  sym: string       // 股票代码
  o: number         // 开盘价
  h: number         // 最高价
  l: number         // 最低价
  c: number         // 收盘价
  v: number         // 成交量
  vw: number        // 成交量加权平均价
  s: number         // 开始时间戳
  e: number         // 结束时间戳
  a: number         // 平均成交价
  n: number         // 交易笔数
}

// 状态消息
export interface PolygonStatus {
  ev: 'status'
  status: 'connected' | 'auth_success' | 'auth_failed' | 'success' | 'error'
  message: string
}

// 所有消息类型
export type PolygonMessage = PolygonTrade | PolygonQuote | PolygonAggregate | PolygonStatus

// 订阅回调
export type PolygonCallback<T> = (data: T) => void

// 连接状态
export type ConnectionStatus = 'disconnected' | 'connecting' | 'connected' | 'authenticated' | 'error'

// WebSocket 服务配置
interface PolygonWebSocketConfig {
  apiKey: string
  cluster?: 'stocks' | 'options' | 'forex' | 'crypto'
  reconnectInterval?: number
  maxReconnectAttempts?: number
}

/**
 * Polygon WebSocket 服务类
 */
export class PolygonWebSocketService {
  private ws: WebSocket | null = null
  private config: PolygonWebSocketConfig
  private status: ConnectionStatus = 'disconnected'
  private reconnectAttempts = 0
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null

  // 订阅管理
  private subscriptions: Map<string, Set<PolygonCallback<PolygonMessage>>> = new Map()
  private pendingSubscriptions: Set<string> = new Set()

  // 状态监听
  private statusListeners: Set<(status: ConnectionStatus) => void> = new Set()

  constructor(config: PolygonWebSocketConfig) {
    this.config = {
      cluster: 'stocks',
      reconnectInterval: 3000,
      maxReconnectAttempts: 10,
      ...config,
    }
  }

  /**
   * 获取 WebSocket URL
   */
  private getWebSocketUrl(): string {
    const cluster = this.config.cluster || 'stocks'
    return `wss://socket.polygon.io/${cluster}`
  }

  /**
   * 连接到 Polygon WebSocket
   */
  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        resolve()
        return
      }

      this.setStatus('connecting')

      try {
        this.ws = new WebSocket(this.getWebSocketUrl())

        this.ws.onopen = () => {
          console.log('[Polygon WS] Connected')
          this.setStatus('connected')
          this.authenticate()
        }

        this.ws.onmessage = (event) => {
          this.handleMessage(event.data)
        }

        this.ws.onerror = (error) => {
          console.error('[Polygon WS] Error:', error)
          this.setStatus('error')
          reject(error)
        }

        this.ws.onclose = () => {
          console.log('[Polygon WS] Disconnected')
          this.setStatus('disconnected')
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

    this.ws.send(JSON.stringify({
      action: 'auth',
      params: this.config.apiKey,
    }))
  }

  /**
   * 处理接收到的消息
   */
  private handleMessage(data: string): void {
    try {
      const messages = JSON.parse(data) as PolygonMessage[]

      for (const msg of messages) {
        // 处理状态消息
        if ('status' in msg && msg.ev === 'status') {
          this.handleStatusMessage(msg)
          continue
        }

        // 处理数据消息
        if ('sym' in msg) {
          const symbol = msg.sym
          const key = `${msg.ev}.${symbol}`

          // 通知订阅者
          const callbacks = this.subscriptions.get(key)
          if (callbacks) {
            callbacks.forEach(cb => cb(msg))
          }

          // 通知通配符订阅者
          const wildcardCallbacks = this.subscriptions.get(`${msg.ev}.*`)
          if (wildcardCallbacks) {
            wildcardCallbacks.forEach(cb => cb(msg))
          }
        }
      }
    } catch (error) {
      console.error('[Polygon WS] Parse error:', error)
    }
  }

  /**
   * 处理状态消息
   */
  private handleStatusMessage(msg: PolygonStatus): void {
    console.log('[Polygon WS] Status:', msg.status, msg.message)

    if (msg.status === 'auth_success') {
      this.setStatus('authenticated')
      this.reconnectAttempts = 0
      // 重新订阅之前的频道
      this.resubscribe()
    } else if (msg.status === 'auth_failed') {
      this.setStatus('error')
      console.error('[Polygon WS] Authentication failed:', msg.message)
    }
  }

  /**
   * 设置连接状态
   */
  private setStatus(status: ConnectionStatus): void {
    this.status = status
    this.statusListeners.forEach(listener => listener(status))
  }

  /**
   * 处理重连
   */
  private handleReconnect(): void {
    if (this.reconnectAttempts >= (this.config.maxReconnectAttempts || 10)) {
      console.error('[Polygon WS] Max reconnect attempts reached')
      return
    }

    this.reconnectAttempts++
    console.log(`[Polygon WS] Reconnecting... (${this.reconnectAttempts})`)

    this.reconnectTimer = setTimeout(() => {
      this.connect().catch(console.error)
    }, this.config.reconnectInterval || 3000)
  }

  /**
   * 重新订阅
   */
  private resubscribe(): void {
    const channels = Array.from(this.subscriptions.keys())
    if (channels.length > 0) {
      this.sendSubscribe(channels)
    }
  }

  /**
   * 发送订阅请求
   */
  private sendSubscribe(channels: string[]): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      channels.forEach(ch => this.pendingSubscriptions.add(ch))
      return
    }

    this.ws.send(JSON.stringify({
      action: 'subscribe',
      params: channels.join(','),
    }))
  }

  /**
   * 发送取消订阅请求
   */
  private sendUnsubscribe(channels: string[]): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) return

    this.ws.send(JSON.stringify({
      action: 'unsubscribe',
      params: channels.join(','),
    }))
  }

  /**
   * 订阅股票实时交易
   */
  subscribeTrades(symbols: string[], callback: PolygonCallback<PolygonTrade>): () => void {
    const channels = symbols.map(s => `T.${s}`)
    return this.subscribe(channels, callback as PolygonCallback<PolygonMessage>)
  }

  /**
   * 订阅股票实时报价
   */
  subscribeQuotes(symbols: string[], callback: PolygonCallback<PolygonQuote>): () => void {
    const channels = symbols.map(s => `Q.${s}`)
    return this.subscribe(channels, callback as PolygonCallback<PolygonMessage>)
  }

  /**
   * 订阅分钟聚合数据
   */
  subscribeMinuteAggregates(symbols: string[], callback: PolygonCallback<PolygonAggregate>): () => void {
    const channels = symbols.map(s => `AM.${s}`)
    return this.subscribe(channels, callback as PolygonCallback<PolygonMessage>)
  }

  /**
   * 订阅秒聚合数据
   */
  subscribeSecondAggregates(symbols: string[], callback: PolygonCallback<PolygonAggregate>): () => void {
    const channels = symbols.map(s => `A.${s}`)
    return this.subscribe(channels, callback as PolygonCallback<PolygonMessage>)
  }

  /**
   * 通用订阅方法
   */
  subscribe(channels: string[], callback: PolygonCallback<PolygonMessage>): () => void {
    const newChannels: string[] = []

    channels.forEach(channel => {
      if (!this.subscriptions.has(channel)) {
        this.subscriptions.set(channel, new Set())
        newChannels.push(channel)
      }
      this.subscriptions.get(channel)!.add(callback)
    })

    if (newChannels.length > 0) {
      this.sendSubscribe(newChannels)
    }

    // 返回取消订阅函数
    return () => {
      const emptyChannels: string[] = []

      channels.forEach(channel => {
        const callbacks = this.subscriptions.get(channel)
        if (callbacks) {
          callbacks.delete(callback)
          if (callbacks.size === 0) {
            this.subscriptions.delete(channel)
            emptyChannels.push(channel)
          }
        }
      })

      if (emptyChannels.length > 0) {
        this.sendUnsubscribe(emptyChannels)
      }
    }
  }

  /**
   * 监听连接状态
   */
  onStatusChange(listener: (status: ConnectionStatus) => void): () => void {
    this.statusListeners.add(listener)
    return () => this.statusListeners.delete(listener)
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

    if (this.ws) {
      this.ws.close()
      this.ws = null
    }

    this.subscriptions.clear()
    this.pendingSubscriptions.clear()
    this.setStatus('disconnected')
  }
}

// 单例实例 (使用环境变量中的 API Key)
let instance: PolygonWebSocketService | null = null

export function getPolygonWebSocket(): PolygonWebSocketService {
  if (!instance) {
    const apiKey = import.meta.env.VITE_POLYGON_API_KEY || 'demo'
    instance = new PolygonWebSocketService({ apiKey })
  }
  return instance
}

export default PolygonWebSocketService
