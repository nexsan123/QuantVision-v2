/**
 * 实时交易流 Hook
 *
 * 管理 WebSocket 连接、订阅和交易事件
 */

import { useState, useEffect, useCallback, useRef } from 'react'
import type {
  TradingMode,
  TradingEvent,
  TradingStreamState,
  SubscriptionChannel,
  WebSocketMessage,
  WebSocketConfig,
  PriceData,
  PortfolioSummary,
  PositionSummary,
} from '@/types/trading'
import { DEFAULT_WS_CONFIG } from '@/types/trading'

interface UseTradingStreamOptions {
  config?: Partial<WebSocketConfig>
  autoConnect?: boolean
  maxEvents?: number
}

interface UseTradingStreamReturn {
  // 状态
  state: TradingStreamState
  prices: Map<string, PriceData>
  positions: PositionSummary[]
  portfolio: PortfolioSummary | null

  // 连接控制
  connect: () => void
  disconnect: () => void
  reconnect: () => void

  // 订阅管理
  subscribe: (channel: Omit<SubscriptionChannel, 'id' | 'active'>) => void
  unsubscribe: (channelId: string) => void

  // 模式切换
  setMode: (mode: TradingMode) => void

  // 事件管理
  clearEvents: () => void
}

export function useTradingStream(
  options: UseTradingStreamOptions = {}
): UseTradingStreamReturn {
  const {
    config: customConfig,
    autoConnect = false,
    maxEvents = 100,
  } = options

  const config: WebSocketConfig = {
    ...DEFAULT_WS_CONFIG,
    ...customConfig,
  }

  // WebSocket 引用
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const heartbeatTimerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  // 状态
  const [state, setState] = useState<TradingStreamState>({
    connectionStatus: 'disconnected',
    mode: config.mode,
    events: [],
    subscriptions: [],
    lastHeartbeat: null,
    reconnectAttempts: 0,
    error: null,
  })

  // 价格数据
  const [prices, setPrices] = useState<Map<string, PriceData>>(new Map())

  // 持仓数据
  const [positions, setPositions] = useState<PositionSummary[]>([])

  // 组合摘要
  const [portfolio, setPortfolio] = useState<PortfolioSummary | null>(null)

  // 添加事件
  const addEvent = useCallback((event: TradingEvent) => {
    setState((prev) => ({
      ...prev,
      events: [event, ...prev.events].slice(0, maxEvents),
    }))
  }, [maxEvents])

  // 处理价格更新
  const handlePriceUpdate = useCallback((event: TradingEvent) => {
    if (event.type !== 'price_update') return

    setPrices((prev) => {
      const newPrices = new Map(prev)
      const priceEvent = event as { symbol: string; price: number; previousPrice: number; change: number; changePercent: number }

      newPrices.set(priceEvent.symbol, {
        symbol: priceEvent.symbol,
        price: priceEvent.price,
        previousPrice: priceEvent.previousPrice,
        change: priceEvent.change,
        changePercent: priceEvent.changePercent,
        direction: priceEvent.change > 0 ? 'up' : priceEvent.change < 0 ? 'down' : 'neutral',
        updatedAt: event.timestamp,
        animating: true,
      })

      // 清除动画状态
      setTimeout(() => {
        setPrices((current) => {
          const updated = new Map(current)
          const existing = updated.get(priceEvent.symbol)
          if (existing) {
            updated.set(priceEvent.symbol, { ...existing, animating: false })
          }
          return updated
        })
      }, 500)

      return newPrices
    })
  }, [])

  // 处理持仓更新
  const handlePositionUpdate = useCallback((event: TradingEvent) => {
    if (event.type !== 'position_opened' && event.type !== 'position_closed' && event.type !== 'position_updated') return

    const posEvent = event as {
      symbol: string
      side: 'buy' | 'sell'
      quantity: number
      avgPrice: number
      currentPrice: number
      unrealizedPnl: number
    }

    setPositions((prev) => {
      const existing = prev.findIndex((p) => p.symbol === posEvent.symbol)
      const marketValue = posEvent.quantity * posEvent.currentPrice
      const unrealizedPnlPercent = ((posEvent.currentPrice - posEvent.avgPrice) / posEvent.avgPrice) * 100

      const newPosition: PositionSummary = {
        symbol: posEvent.symbol,
        side: posEvent.side,
        quantity: posEvent.quantity,
        avgPrice: posEvent.avgPrice,
        currentPrice: posEvent.currentPrice,
        marketValue,
        unrealizedPnl: posEvent.unrealizedPnl,
        unrealizedPnlPercent,
        dayChange: 0, // 需要从其他数据源获取
        dayChangePercent: 0,
      }

      if (event.type === 'position_closed') {
        return prev.filter((p) => p.symbol !== posEvent.symbol)
      }

      if (existing >= 0) {
        const updated = [...prev]
        updated[existing] = newPosition
        return updated
      }

      return [...prev, newPosition]
    })
  }, [])

  // 处理盈亏更新
  const handlePnLUpdate = useCallback((event: TradingEvent) => {
    if (event.type !== 'pnl_update') return

    const pnlEvent = event as {
      totalUnrealizedPnl: number
      totalRealizedPnl: number
      dailyPnl: number
      portfolioValue: number
      cashBalance: number
    }

    setPortfolio((prev) => ({
      totalValue: pnlEvent.portfolioValue,
      cashBalance: pnlEvent.cashBalance,
      marketValue: pnlEvent.portfolioValue - pnlEvent.cashBalance,
      unrealizedPnl: pnlEvent.totalUnrealizedPnl,
      realizedPnl: pnlEvent.totalRealizedPnl,
      dailyPnl: pnlEvent.dailyPnl,
      dailyPnlPercent: prev ? (pnlEvent.dailyPnl / (prev.totalValue - pnlEvent.dailyPnl)) * 100 : 0,
      positionCount: positions.length,
    }))
  }, [positions.length])

  // 处理 WebSocket 消息
  const handleMessage = useCallback((message: WebSocketMessage) => {
    if (message.type === 'heartbeat') {
      setState((prev) => ({
        ...prev,
        lastHeartbeat: new Date().toISOString(),
      }))
      return
    }

    if (message.type === 'error') {
      setState((prev) => ({
        ...prev,
        error: message.error || '未知错误',
      }))
      return
    }

    if (message.type === 'event' && message.payload) {
      const events = Array.isArray(message.payload) ? message.payload : [message.payload]

      events.forEach((event) => {
        addEvent(event)

        // 处理特定事件类型
        switch (event.type) {
          case 'price_update':
            handlePriceUpdate(event)
            break
          case 'position_opened':
          case 'position_closed':
          case 'position_updated':
            handlePositionUpdate(event)
            break
          case 'pnl_update':
            handlePnLUpdate(event)
            break
        }
      })
    }
  }, [addEvent, handlePriceUpdate, handlePositionUpdate, handlePnLUpdate])

  // 连接 WebSocket
  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return
    }

    setState((prev) => ({
      ...prev,
      connectionStatus: 'connecting',
      error: null,
    }))

    const wsUrl = `${config.url}?mode=${state.mode}`
    const ws = new WebSocket(wsUrl)

    ws.onopen = () => {
      setState((prev) => ({
        ...prev,
        connectionStatus: 'connected',
        reconnectAttempts: 0,
        error: null,
      }))

      // 启动心跳
      heartbeatTimerRef.current = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: 'heartbeat' }))
        }
      }, config.heartbeatInterval)

      // 重新订阅频道
      state.subscriptions.forEach((sub) => {
        if (sub.active) {
          ws.send(JSON.stringify({
            type: 'subscribe',
            channel: sub.type,
            symbols: sub.symbols,
          }))
        }
      })
    }

    ws.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data)
        handleMessage(message)
      } catch {
        console.error('Failed to parse WebSocket message:', event.data)
      }
    }

    ws.onerror = () => {
      setState((prev) => ({
        ...prev,
        connectionStatus: 'error',
        error: 'WebSocket 连接错误',
      }))
    }

    ws.onclose = () => {
      if (heartbeatTimerRef.current) {
        clearInterval(heartbeatTimerRef.current)
      }

      setState((prev) => {
        if (prev.reconnectAttempts < config.maxReconnectAttempts) {
          // 自动重连
          reconnectTimerRef.current = setTimeout(() => {
            connect()
          }, config.reconnectInterval)

          return {
            ...prev,
            connectionStatus: 'reconnecting',
            reconnectAttempts: prev.reconnectAttempts + 1,
          }
        }

        return {
          ...prev,
          connectionStatus: 'disconnected',
          error: '连接已断开，重连次数已用尽',
        }
      })
    }

    wsRef.current = ws
  }, [config, state.mode, state.subscriptions, handleMessage])

  // 断开连接
  const disconnect = useCallback(() => {
    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current)
    }
    if (heartbeatTimerRef.current) {
      clearInterval(heartbeatTimerRef.current)
    }

    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }

    setState((prev) => ({
      ...prev,
      connectionStatus: 'disconnected',
      reconnectAttempts: 0,
    }))
  }, [])

  // 重连
  const reconnect = useCallback(() => {
    disconnect()
    setTimeout(connect, 100)
  }, [disconnect, connect])

  // 订阅频道
  const subscribe = useCallback((channel: Omit<SubscriptionChannel, 'id' | 'active'>) => {
    const newChannel: SubscriptionChannel = {
      ...channel,
      id: `${channel.type}-${Date.now()}`,
      active: true,
    }

    setState((prev) => ({
      ...prev,
      subscriptions: [...prev.subscriptions, newChannel],
    }))

    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'subscribe',
        channel: channel.type,
        symbols: channel.symbols,
      }))
    }
  }, [])

  // 取消订阅
  const unsubscribe = useCallback((channelId: string) => {
    const channel = state.subscriptions.find((s) => s.id === channelId)

    if (channel && wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'unsubscribe',
        channel: channel.type,
        symbols: channel.symbols,
      }))
    }

    setState((prev) => ({
      ...prev,
      subscriptions: prev.subscriptions.filter((s) => s.id !== channelId),
    }))
  }, [state.subscriptions])

  // 切换模式
  const setMode = useCallback((mode: TradingMode) => {
    setState((prev) => ({
      ...prev,
      mode,
    }))

    // 重连以应用新模式
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      reconnect()
    }
  }, [reconnect])

  // 清除事件
  const clearEvents = useCallback(() => {
    setState((prev) => ({
      ...prev,
      events: [],
    }))
  }, [])

  // 自动连接
  useEffect(() => {
    if (autoConnect) {
      connect()
    }

    return () => {
      disconnect()
    }
  }, []) // 只在挂载时执行

  return {
    state,
    prices,
    positions,
    portfolio,
    connect,
    disconnect,
    reconnect,
    subscribe,
    unsubscribe,
    setMode,
    clearEvents,
  }
}

export default useTradingStream
