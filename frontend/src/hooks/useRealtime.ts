/**
 * 实时数据 Hooks
 * Sprint 11: T23/T24 - 交易面板与持仓监控实时数据
 *
 * 提供后端实时数据的 React Hooks
 */

import { useState, useEffect, useCallback, useRef } from 'react'
import { realtimeApi, type RealtimeStatus, type PositionDetail, type OrderDetail } from '../services/backendApi'
import { backendWebSocket, type WebSocketEvent, type ConnectionStatus } from '../services/backendWebSocket'

// ==================== useRealtimeStatus ====================

interface UseRealtimeStatusOptions {
  autoRefresh?: boolean
  refreshInterval?: number  // 毫秒
}

export interface UseRealtimeStatusResult {
  status: RealtimeStatus | null
  loading: boolean
  error: Error | null
  refresh: () => Promise<void>
  wsConnected: boolean
}

/**
 * 实时状态 Hook
 */
export function useRealtimeStatus(options: UseRealtimeStatusOptions = {}): UseRealtimeStatusResult {
  const { autoRefresh = true, refreshInterval = 30000 } = options

  const [status, setStatus] = useState<RealtimeStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)
  const [wsConnected, setWsConnected] = useState(false)

  const refresh = useCallback(async () => {
    try {
      setLoading(true)
      const data = await realtimeApi.getStatus()
      setStatus(data)
      setError(null)
    } catch (err) {
      setError(err as Error)
    } finally {
      setLoading(false)
    }
  }, [])

  // 初始加载
  useEffect(() => {
    refresh()
  }, [refresh])

  // 自动刷新
  useEffect(() => {
    if (!autoRefresh) return

    const interval = setInterval(refresh, refreshInterval)
    return () => clearInterval(interval)
  }, [autoRefresh, refreshInterval, refresh])

  // WebSocket 连接
  useEffect(() => {
    const unsubscribe = backendWebSocket.onStatusChange((connStatus) => {
      setWsConnected(connStatus === 'connected')
    })

    // 连接 WebSocket
    backendWebSocket.connect().catch(console.error)

    return () => {
      unsubscribe()
    }
  }, [])

  // 监听 WebSocket 状态更新
  useEffect(() => {
    const unsubscribe = backendWebSocket.onEvent((event) => {
      if (event.type === 'status_update' || event.type === 'initial_status') {
        const statusEvent = event as {
          market: RealtimeStatus['market']
          account: RealtimeStatus['account']
          performance: RealtimeStatus['performance']
        }
        setStatus(prev => prev ? {
          ...prev,
          market: statusEvent.market,
          account: statusEvent.account,
          performance: statusEvent.performance,
        } : null)
      }
    })

    return () => unsubscribe()
  }, [])

  return { status, loading, error, refresh, wsConnected }
}

// ==================== useRealtimePositions ====================

interface UseRealtimePositionsOptions {
  autoRefresh?: boolean
  refreshInterval?: number
}

export interface UseRealtimePositionsResult {
  positions: PositionDetail[]
  loading: boolean
  error: Error | null
  refresh: () => Promise<void>
  closePosition: (symbol: string) => Promise<void>
  closeAllPositions: () => Promise<void>
  totalValue: number
  totalPnL: number
}

/**
 * 实时持仓 Hook
 */
export function useRealtimePositions(options: UseRealtimePositionsOptions = {}): UseRealtimePositionsResult {
  const { autoRefresh = true, refreshInterval = 10000 } = options

  const [positions, setPositions] = useState<PositionDetail[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  const refresh = useCallback(async () => {
    try {
      setLoading(true)
      const data = await realtimeApi.getPositions()
      setPositions(data)
      setError(null)
    } catch (err) {
      setError(err as Error)
    } finally {
      setLoading(false)
    }
  }, [])

  const closePosition = useCallback(async (symbol: string) => {
    await realtimeApi.closePosition(symbol)
    await refresh()
  }, [refresh])

  const closeAllPositions = useCallback(async () => {
    await realtimeApi.closeAllPositions()
    await refresh()
  }, [refresh])

  // 初始加载
  useEffect(() => {
    refresh()
  }, [refresh])

  // 自动刷新
  useEffect(() => {
    if (!autoRefresh) return

    const interval = setInterval(refresh, refreshInterval)
    return () => clearInterval(interval)
  }, [autoRefresh, refreshInterval, refresh])

  // 监听 WebSocket 持仓更新
  useEffect(() => {
    const unsubscribe = backendWebSocket.onEvent((event) => {
      if (event.type === 'positions_snapshot') {
        const snapshot = event as { positions: PositionDetail[] }
        setPositions(snapshot.positions)
      }
    })

    return () => unsubscribe()
  }, [])

  // 计算汇总
  const totalValue = positions.reduce((sum, p) => sum + Math.abs(p.market_value), 0)
  const totalPnL = positions.reduce((sum, p) => sum + p.unrealized_pnl, 0)

  return {
    positions,
    loading,
    error,
    refresh,
    closePosition,
    closeAllPositions,
    totalValue,
    totalPnL,
  }
}

// ==================== useRealtimeOrders ====================

interface UseRealtimeOrdersOptions {
  status?: 'open' | 'closed' | 'all'
  autoRefresh?: boolean
  refreshInterval?: number
}

export interface UseRealtimeOrdersResult {
  orders: OrderDetail[]
  openOrders: OrderDetail[]
  loading: boolean
  error: Error | null
  refresh: () => Promise<void>
  cancelOrder: (orderId: string) => Promise<void>
  cancelAllOrders: () => Promise<void>
}

/**
 * 实时订单 Hook
 */
export function useRealtimeOrders(options: UseRealtimeOrdersOptions = {}): UseRealtimeOrdersResult {
  const { status = 'all', autoRefresh = true, refreshInterval = 5000 } = options

  const [orders, setOrders] = useState<OrderDetail[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  const refresh = useCallback(async () => {
    try {
      setLoading(true)
      const data = await realtimeApi.getOrders(status)
      setOrders(data)
      setError(null)
    } catch (err) {
      setError(err as Error)
    } finally {
      setLoading(false)
    }
  }, [status])

  const cancelOrder = useCallback(async (orderId: string) => {
    await realtimeApi.cancelOrder(orderId)
    await refresh()
  }, [refresh])

  const cancelAllOrders = useCallback(async () => {
    // 取消所有 open 订单
    const openOrders = orders.filter(o =>
      ['new', 'pending_new', 'accepted', 'partially_filled'].includes(o.status)
    )
    await Promise.all(openOrders.map(o => realtimeApi.cancelOrder(o.id)))
    await refresh()
  }, [orders, refresh])

  // 初始加载
  useEffect(() => {
    refresh()
  }, [refresh])

  // 自动刷新
  useEffect(() => {
    if (!autoRefresh) return

    const interval = setInterval(refresh, refreshInterval)
    return () => clearInterval(interval)
  }, [autoRefresh, refreshInterval, refresh])

  // 监听 WebSocket 订单更新
  useEffect(() => {
    const unsubscribe = backendWebSocket.onEvent((event) => {
      if (event.type?.startsWith('order_')) {
        // 订单更新，刷新列表
        refresh()
      }
    })

    return () => unsubscribe()
  }, [refresh])

  // 计算 open 订单
  const openOrders = orders.filter(o =>
    ['new', 'pending_new', 'accepted', 'partially_filled'].includes(o.status)
  )

  return {
    orders,
    openOrders,
    loading,
    error,
    refresh,
    cancelOrder,
    cancelAllOrders,
  }
}

// ==================== useMarketClock ====================

export interface UseMarketClockResult {
  isOpen: boolean
  nextOpen: Date | null
  nextClose: Date | null
  loading: boolean
  error: Error | null
  refresh: () => Promise<void>
}

/**
 * 市场时钟 Hook
 */
export function useMarketClock(): UseMarketClockResult {
  const [isOpen, setIsOpen] = useState(false)
  const [nextOpen, setNextOpen] = useState<Date | null>(null)
  const [nextClose, setNextClose] = useState<Date | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  const refresh = useCallback(async () => {
    try {
      setLoading(true)
      const data = await realtimeApi.getClock()
      setIsOpen(data.is_open)
      setNextOpen(new Date(data.next_open))
      setNextClose(new Date(data.next_close))
      setError(null)
    } catch (err) {
      setError(err as Error)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    refresh()
    // 每分钟刷新
    const interval = setInterval(refresh, 60000)
    return () => clearInterval(interval)
  }, [refresh])

  return { isOpen, nextOpen, nextClose, loading, error, refresh }
}

// ==================== useWebSocketConnection ====================

export interface UseWebSocketConnectionResult {
  status: ConnectionStatus
  isConnected: boolean
  connect: () => Promise<void>
  disconnect: () => void
}

/**
 * WebSocket 连接 Hook
 */
export function useWebSocketConnection(): UseWebSocketConnectionResult {
  const [status, setStatus] = useState<ConnectionStatus>('disconnected')

  useEffect(() => {
    const unsubscribe = backendWebSocket.onStatusChange(setStatus)
    setStatus(backendWebSocket.getStatus())
    return () => unsubscribe()
  }, [])

  const connect = useCallback(async () => {
    await backendWebSocket.connect()
  }, [])

  const disconnect = useCallback(() => {
    backendWebSocket.disconnect()
  }, [])

  return {
    status,
    isConnected: status === 'connected',
    connect,
    disconnect,
  }
}

// ==================== useRealtimeEvents ====================

export interface UseRealtimeEventsResult {
  events: WebSocketEvent[]
  lastEvent: WebSocketEvent | null
  clearEvents: () => void
}

/**
 * 实时事件 Hook
 */
export function useRealtimeEvents(maxEvents: number = 50): UseRealtimeEventsResult {
  const [events, setEvents] = useState<WebSocketEvent[]>([])
  const [lastEvent, setLastEvent] = useState<WebSocketEvent | null>(null)

  useEffect(() => {
    const unsubscribe = backendWebSocket.onEvent((event) => {
      setLastEvent(event)
      setEvents(prev => {
        const newEvents = [event, ...prev]
        return newEvents.slice(0, maxEvents)
      })
    })

    return () => unsubscribe()
  }, [maxEvents])

  const clearEvents = useCallback(() => {
    setEvents([])
    setLastEvent(null)
  }, [])

  return { events, lastEvent, clearEvents }
}
