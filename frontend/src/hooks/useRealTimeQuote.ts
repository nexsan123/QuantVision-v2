/**
 * 实时报价 Hook
 * Sprint 7: T6 - 实时行情数据订阅
 *
 * 使用 Polygon.io WebSocket 获取实时报价
 */
import { useState, useEffect, useCallback, useRef } from 'react'
import {
  getPolygonWebSocket,
  type PolygonTrade,
  type PolygonQuote,
  type PolygonAggregate,
  type ConnectionStatus,
} from '../services/polygonWebSocket'

// 实时报价数据
export interface RealTimeQuote {
  symbol: string
  price: number           // 最新价格
  change: number          // 涨跌额
  changePercent: number   // 涨跌幅
  bid: number             // 买入价
  bidSize: number         // 买入量
  ask: number             // 卖出价
  askSize: number         // 卖出量
  volume: number          // 成交量
  high: number            // 最高价
  low: number             // 最低价
  open: number            // 开盘价
  prevClose: number       // 昨收价
  timestamp: number       // 时间戳
  isRealTime: boolean     // 是否实时数据
}

// Hook 选项
interface UseRealTimeQuoteOptions {
  // 是否自动连接
  autoConnect?: boolean
  // 是否订阅交易数据
  subscribeTrades?: boolean
  // 是否订阅报价数据
  subscribeQuotes?: boolean
  // 是否订阅分钟聚合
  subscribeMinuteAgg?: boolean
  // 更新节流 (毫秒)
  throttleMs?: number
}

// Hook 返回值
interface UseRealTimeQuoteResult {
  quotes: Map<string, RealTimeQuote>
  getQuote: (symbol: string) => RealTimeQuote | undefined
  status: ConnectionStatus
  error: Error | null
  connect: () => Promise<void>
  disconnect: () => void
  subscribe: (symbols: string[]) => void
  unsubscribe: (symbols: string[]) => void
}

/**
 * 实时报价 Hook
 */
export function useRealTimeQuote(
  initialSymbols: string[] = [],
  options: UseRealTimeQuoteOptions = {}
): UseRealTimeQuoteResult {
  const {
    autoConnect = true,
    subscribeTrades = true,
    subscribeQuotes = true,
    subscribeMinuteAgg = false,
    throttleMs = 100,
  } = options

  const [quotes, setQuotes] = useState<Map<string, RealTimeQuote>>(new Map())
  const [status, setStatus] = useState<ConnectionStatus>('disconnected')
  const [error, setError] = useState<Error | null>(null)

  const wsRef = useRef(getPolygonWebSocket())
  const symbolsRef = useRef<Set<string>>(new Set(initialSymbols))
  const unsubscribersRef = useRef<(() => void)[]>([])
  const lastUpdateRef = useRef<Map<string, number>>(new Map())

  // 更新报价 (带节流)
  const updateQuote = useCallback((symbol: string, update: Partial<RealTimeQuote>) => {
    const now = Date.now()
    const lastUpdate = lastUpdateRef.current.get(symbol) || 0

    if (now - lastUpdate < throttleMs) {
      return
    }

    lastUpdateRef.current.set(symbol, now)

    setQuotes(prev => {
      const newQuotes = new Map(prev)
      const existing = newQuotes.get(symbol) || createEmptyQuote(symbol)

      const updated: RealTimeQuote = {
        ...existing,
        ...update,
        timestamp: now,
        isRealTime: true,
      }

      // 计算涨跌
      if (updated.prevClose > 0 && updated.price > 0) {
        updated.change = updated.price - updated.prevClose
        updated.changePercent = (updated.change / updated.prevClose) * 100
      }

      newQuotes.set(symbol, updated)
      return newQuotes
    })
  }, [throttleMs])

  // 处理交易数据
  const handleTrade = useCallback((trade: PolygonTrade) => {
    updateQuote(trade.sym, {
      price: trade.p,
      volume: trade.s, // 累加成交量需要服务端支持
    })
  }, [updateQuote])

  // 处理报价数据
  const handleQuote = useCallback((quote: PolygonQuote) => {
    updateQuote(quote.sym, {
      bid: quote.bp,
      bidSize: quote.bs,
      ask: quote.ap,
      askSize: quote.as,
      // 使用中间价作为价格估算
      price: (quote.bp + quote.ap) / 2,
    })
  }, [updateQuote])

  // 处理聚合数据
  const handleAggregate = useCallback((agg: PolygonAggregate) => {
    updateQuote(agg.sym, {
      open: agg.o,
      high: agg.h,
      low: agg.l,
      price: agg.c,
      volume: agg.v,
    })
  }, [updateQuote])

  // 订阅股票
  const subscribe = useCallback((symbols: string[]) => {
    symbols.forEach(s => symbolsRef.current.add(s))

    const ws = wsRef.current

    if (subscribeTrades) {
      const unsub = ws.subscribeTrades(symbols, handleTrade)
      unsubscribersRef.current.push(unsub)
    }

    if (subscribeQuotes) {
      const unsub = ws.subscribeQuotes(symbols, handleQuote)
      unsubscribersRef.current.push(unsub)
    }

    if (subscribeMinuteAgg) {
      const unsub = ws.subscribeMinuteAggregates(symbols, handleAggregate)
      unsubscribersRef.current.push(unsub)
    }
  }, [subscribeTrades, subscribeQuotes, subscribeMinuteAgg, handleTrade, handleQuote, handleAggregate])

  // 取消订阅
  const unsubscribe = useCallback((symbols: string[]) => {
    symbols.forEach(s => symbolsRef.current.delete(s))

    // 清理报价数据
    setQuotes(prev => {
      const newQuotes = new Map(prev)
      symbols.forEach(s => newQuotes.delete(s))
      return newQuotes
    })
  }, [])

  // 连接
  const connect = useCallback(async () => {
    try {
      setError(null)
      await wsRef.current.connect()

      // 订阅初始股票
      if (symbolsRef.current.size > 0) {
        subscribe(Array.from(symbolsRef.current))
      }
    } catch (err) {
      setError(err as Error)
      throw err
    }
  }, [subscribe])

  // 断开连接
  const disconnect = useCallback(() => {
    // 清理所有订阅
    unsubscribersRef.current.forEach(unsub => unsub())
    unsubscribersRef.current = []

    wsRef.current.disconnect()
  }, [])

  // 获取单个报价
  const getQuote = useCallback((symbol: string): RealTimeQuote | undefined => {
    return quotes.get(symbol)
  }, [quotes])

  // 监听状态变化
  useEffect(() => {
    const ws = wsRef.current
    const unsubStatus = ws.onStatusChange(setStatus)

    return () => {
      unsubStatus()
    }
  }, [])

  // 自动连接
  useEffect(() => {
    if (autoConnect) {
      connect().catch(console.error)
    }

    return () => {
      disconnect()
    }
  }, [autoConnect, connect, disconnect])

  // 初始股票变化时重新订阅
  useEffect(() => {
    if (status === 'authenticated' && initialSymbols.length > 0) {
      subscribe(initialSymbols)
    }
  }, [status, initialSymbols, subscribe])

  return {
    quotes,
    getQuote,
    status,
    error,
    connect,
    disconnect,
    subscribe,
    unsubscribe,
  }
}

/**
 * 单个股票实时报价 Hook
 */
export function useSingleQuote(
  symbol: string,
  options: Omit<UseRealTimeQuoteOptions, 'throttleMs'> = {}
): RealTimeQuote | null {
  const { quotes, status } = useRealTimeQuote([symbol], options)
  return quotes.get(symbol) || null
}

/**
 * 创建空报价对象
 */
function createEmptyQuote(symbol: string): RealTimeQuote {
  return {
    symbol,
    price: 0,
    change: 0,
    changePercent: 0,
    bid: 0,
    bidSize: 0,
    ask: 0,
    askSize: 0,
    volume: 0,
    high: 0,
    low: 0,
    open: 0,
    prevClose: 0,
    timestamp: 0,
    isRealTime: false,
  }
}

export default useRealTimeQuote
