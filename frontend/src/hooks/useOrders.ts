/**
 * 订单管理 Hook
 * Sprint 8: T11 - 订单管理 Hook
 *
 * 提供订单查询、提交、取消等功能
 */
import { useState, useEffect, useCallback, useRef } from 'react'
import {
  alpacaTrading,
  type Order,
  type OrderRequest,
  type OrdersQuery,
  type OrderSide,
} from '../services/alpacaTrading'

// Hook 选项
interface UseOrdersOptions {
  // 自动刷新间隔 (毫秒)，0 表示不自动刷新
  refreshInterval?: number
  // 初始查询参数
  initialQuery?: OrdersQuery
  // 是否自动加载
  autoLoad?: boolean
}

// Hook 返回值
interface UseOrdersResult {
  // 订单列表
  orders: Order[]
  // 开仓订单
  openOrders: Order[]
  // 已成交订单
  filledOrders: Order[]

  // 状态
  loading: boolean
  submitting: boolean
  error: Error | null

  // 操作
  refresh: () => Promise<void>
  submitOrder: (order: OrderRequest) => Promise<Order>
  cancelOrder: (orderId: string) => Promise<void>
  cancelAllOrders: () => Promise<void>
  replaceOrder: (orderId: string, changes: Partial<OrderRequest>) => Promise<Order>

  // 快捷方法
  marketBuy: (symbol: string, qty: number) => Promise<Order>
  marketSell: (symbol: string, qty: number) => Promise<Order>
  limitBuy: (symbol: string, qty: number, price: number) => Promise<Order>
  limitSell: (symbol: string, qty: number, price: number) => Promise<Order>
  bracketOrder: (symbol: string, qty: number, side: OrderSide, takeProfit: number, stopLoss: number) => Promise<Order>
}

/**
 * 订单管理 Hook
 */
export function useOrders(options: UseOrdersOptions = {}): UseOrdersResult {
  const {
    refreshInterval = 5000,
    initialQuery = { status: 'all', limit: 100 },
    autoLoad = true,
  } = options

  const [orders, setOrders] = useState<Order[]>([])
  const [loading, setLoading] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  const queryRef = useRef<OrdersQuery>(initialQuery)
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  // 筛选开仓订单
  const openOrders = orders.filter(o =>
    ['new', 'partially_filled', 'pending_new', 'accepted'].includes(o.status)
  )

  // 筛选已成交订单
  const filledOrders = orders.filter(o => o.status === 'filled')

  // 刷新订单列表
  const refresh = useCallback(async () => {
    setLoading(true)
    setError(null)

    try {
      const result = await alpacaTrading.getOrders(queryRef.current)
      setOrders(result)
    } catch (err) {
      console.error('[useOrders] Refresh failed:', err)
      setError(err as Error)
    } finally {
      setLoading(false)
    }
  }, [])

  // 提交订单
  const submitOrder = useCallback(async (order: OrderRequest): Promise<Order> => {
    setSubmitting(true)
    setError(null)

    try {
      const result = await alpacaTrading.submitOrder(order)
      // 刷新订单列表
      await refresh()
      return result
    } catch (err) {
      console.error('[useOrders] Submit failed:', err)
      setError(err as Error)
      throw err
    } finally {
      setSubmitting(false)
    }
  }, [refresh])

  // 取消订单
  const cancelOrder = useCallback(async (orderId: string): Promise<void> => {
    setError(null)

    try {
      await alpacaTrading.cancelOrder(orderId)
      // 更新本地状态
      setOrders(prev => prev.map(o =>
        o.id === orderId ? { ...o, status: 'canceled' as const } : o
      ))
    } catch (err) {
      console.error('[useOrders] Cancel failed:', err)
      setError(err as Error)
      throw err
    }
  }, [])

  // 取消所有订单
  const cancelAllOrders = useCallback(async (): Promise<void> => {
    setError(null)

    try {
      await alpacaTrading.cancelAllOrders()
      // 刷新订单列表
      await refresh()
    } catch (err) {
      console.error('[useOrders] Cancel all failed:', err)
      setError(err as Error)
      throw err
    }
  }, [refresh])

  // 修改订单
  const replaceOrder = useCallback(async (
    orderId: string,
    changes: Partial<OrderRequest>
  ): Promise<Order> => {
    setError(null)

    try {
      const result = await alpacaTrading.replaceOrder(orderId, {
        qty: changes.qty,
        time_in_force: changes.time_in_force,
        limit_price: changes.limit_price,
        stop_price: changes.stop_price,
      })
      // 刷新订单列表
      await refresh()
      return result
    } catch (err) {
      console.error('[useOrders] Replace failed:', err)
      setError(err as Error)
      throw err
    }
  }, [refresh])

  // 快捷方法: 市价买入
  const marketBuy = useCallback(async (symbol: string, qty: number): Promise<Order> => {
    return submitOrder({
      symbol,
      qty,
      side: 'buy',
      type: 'market',
      time_in_force: 'day',
    })
  }, [submitOrder])

  // 快捷方法: 市价卖出
  const marketSell = useCallback(async (symbol: string, qty: number): Promise<Order> => {
    return submitOrder({
      symbol,
      qty,
      side: 'sell',
      type: 'market',
      time_in_force: 'day',
    })
  }, [submitOrder])

  // 快捷方法: 限价买入
  const limitBuy = useCallback(async (symbol: string, qty: number, price: number): Promise<Order> => {
    return submitOrder({
      symbol,
      qty,
      side: 'buy',
      type: 'limit',
      time_in_force: 'day',
      limit_price: price,
    })
  }, [submitOrder])

  // 快捷方法: 限价卖出
  const limitSell = useCallback(async (symbol: string, qty: number, price: number): Promise<Order> => {
    return submitOrder({
      symbol,
      qty,
      side: 'sell',
      type: 'limit',
      time_in_force: 'day',
      limit_price: price,
    })
  }, [submitOrder])

  // 快捷方法: 括号订单
  const bracketOrder = useCallback(async (
    symbol: string,
    qty: number,
    side: OrderSide,
    takeProfit: number,
    stopLoss: number
  ): Promise<Order> => {
    return submitOrder({
      symbol,
      qty,
      side,
      type: 'market',
      time_in_force: 'day',
      order_class: 'bracket',
      take_profit: { limit_price: takeProfit },
      stop_loss: { stop_price: stopLoss },
    })
  }, [submitOrder])

  // 初始加载
  useEffect(() => {
    if (autoLoad) {
      refresh()
    }
  }, [autoLoad, refresh])

  // 自动刷新
  useEffect(() => {
    if (refreshInterval > 0) {
      intervalRef.current = setInterval(refresh, refreshInterval)
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
      }
    }
  }, [refreshInterval, refresh])

  return {
    orders,
    openOrders,
    filledOrders,
    loading,
    submitting,
    error,
    refresh,
    submitOrder,
    cancelOrder,
    cancelAllOrders,
    replaceOrder,
    marketBuy,
    marketSell,
    limitBuy,
    limitSell,
    bracketOrder,
  }
}

/**
 * 单个订单状态 Hook
 */
export function useOrder(orderId: string): {
  order: Order | null
  loading: boolean
  error: Error | null
  refresh: () => Promise<void>
} {
  const [order, setOrder] = useState<Order | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  const refresh = useCallback(async () => {
    if (!orderId) return

    setLoading(true)
    setError(null)

    try {
      const result = await alpacaTrading.getOrder(orderId)
      setOrder(result)
    } catch (err) {
      console.error('[useOrder] Failed:', err)
      setError(err as Error)
    } finally {
      setLoading(false)
    }
  }, [orderId])

  useEffect(() => {
    refresh()
  }, [refresh])

  return { order, loading, error, refresh }
}

export default useOrders
