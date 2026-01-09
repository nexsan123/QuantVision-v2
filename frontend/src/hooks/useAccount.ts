/**
 * 账户状态 Hook
 * Sprint 8: T12 - 账户状态 Hook
 *
 * 提供账户信息、持仓、交易活动等功能
 */
import { useState, useEffect, useCallback, useRef, useMemo } from 'react'
import { alpacaAuth, type AlpacaAccount } from '../services/alpacaAuth'
import { alpacaTrading, type Position, type Clock } from '../services/alpacaTrading'

// ==================== 账户 Hook ====================

interface UseAccountOptions {
  refreshInterval?: number
  autoLoad?: boolean
}

interface UseAccountResult {
  account: AlpacaAccount | null
  loading: boolean
  error: Error | null
  refresh: () => Promise<void>

  // 计算属性
  buyingPower: number
  cash: number
  portfolioValue: number
  equity: number
  dayTradeCount: number
  isPDT: boolean
  isRestricted: boolean

  // 环境
  environment: 'paper' | 'live'
  isAuthenticated: boolean
}

/**
 * 账户信息 Hook
 */
export function useAccount(options: UseAccountOptions = {}): UseAccountResult {
  const { refreshInterval = 30000, autoLoad = true } = options

  const [account, setAccount] = useState<AlpacaAccount | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const refresh = useCallback(async () => {
    if (!alpacaAuth.isAuthenticated()) {
      setError(new Error('Not authenticated'))
      return
    }

    setLoading(true)
    setError(null)

    try {
      const result = await alpacaTrading.getAccount()
      setAccount(result)
    } catch (err) {
      console.error('[useAccount] Refresh failed:', err)
      setError(err as Error)
    } finally {
      setLoading(false)
    }
  }, [])

  // 计算属性
  const buyingPower = useMemo(() => parseFloat(account?.buying_power || '0'), [account])
  const cash = useMemo(() => parseFloat(account?.cash || '0'), [account])
  const portfolioValue = useMemo(() => parseFloat(account?.portfolio_value || '0'), [account])
  const equity = useMemo(() => parseFloat(account?.equity || '0'), [account])
  const dayTradeCount = useMemo(() => account?.daytrade_count || 0, [account])
  const isPDT = useMemo(() => account?.pattern_day_trader || false, [account])
  const isRestricted = useMemo(() =>
    account?.trading_blocked || account?.account_blocked || account?.transfers_blocked || false,
    [account]
  )

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
    account,
    loading,
    error,
    refresh,
    buyingPower,
    cash,
    portfolioValue,
    equity,
    dayTradeCount,
    isPDT,
    isRestricted,
    environment: alpacaAuth.getEnvironment(),
    isAuthenticated: alpacaAuth.isAuthenticated(),
  }
}

// ==================== 持仓 Hook ====================

interface UsePositionsOptions {
  refreshInterval?: number
  autoLoad?: boolean
}

interface UsePositionsResult {
  positions: Position[]
  loading: boolean
  error: Error | null
  refresh: () => Promise<void>
  closePosition: (symbol: string, qty?: number) => Promise<void>
  closeAllPositions: () => Promise<void>

  // 计算属性
  totalValue: number
  totalPnL: number
  totalPnLPercent: number
  longPositions: Position[]
  shortPositions: Position[]
}

/**
 * 持仓信息 Hook
 */
export function usePositions(options: UsePositionsOptions = {}): UsePositionsResult {
  const { refreshInterval = 5000, autoLoad = true } = options

  const [positions, setPositions] = useState<Position[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const refresh = useCallback(async () => {
    if (!alpacaAuth.isAuthenticated()) {
      return
    }

    setLoading(true)
    setError(null)

    try {
      const result = await alpacaTrading.getPositions()
      setPositions(result)
    } catch (err) {
      console.error('[usePositions] Refresh failed:', err)
      setError(err as Error)
    } finally {
      setLoading(false)
    }
  }, [])

  const closePosition = useCallback(async (symbol: string, qty?: number) => {
    try {
      await alpacaTrading.closePosition(symbol, qty)
      await refresh()
    } catch (err) {
      console.error('[usePositions] Close failed:', err)
      setError(err as Error)
      throw err
    }
  }, [refresh])

  const closeAllPositions = useCallback(async () => {
    try {
      await alpacaTrading.closeAllPositions(true)
      await refresh()
    } catch (err) {
      console.error('[usePositions] Close all failed:', err)
      setError(err as Error)
      throw err
    }
  }, [refresh])

  // 计算属性
  const totalValue = useMemo(() =>
    positions.reduce((sum, p) => sum + parseFloat(p.market_value), 0),
    [positions]
  )

  const totalPnL = useMemo(() =>
    positions.reduce((sum, p) => sum + parseFloat(p.unrealized_pl), 0),
    [positions]
  )

  const totalCost = useMemo(() =>
    positions.reduce((sum, p) => sum + parseFloat(p.cost_basis), 0),
    [positions]
  )

  const totalPnLPercent = useMemo(() =>
    totalCost > 0 ? (totalPnL / totalCost) * 100 : 0,
    [totalPnL, totalCost]
  )

  const longPositions = useMemo(() =>
    positions.filter(p => p.side === 'long'),
    [positions]
  )

  const shortPositions = useMemo(() =>
    positions.filter(p => p.side === 'short'),
    [positions]
  )

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
    positions,
    loading,
    error,
    refresh,
    closePosition,
    closeAllPositions,
    totalValue,
    totalPnL,
    totalPnLPercent,
    longPositions,
    shortPositions,
  }
}

// ==================== 市场时钟 Hook ====================

interface UseMarketClockResult {
  clock: Clock | null
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
  const [clock, setClock] = useState<Clock | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  const refresh = useCallback(async () => {
    setLoading(true)
    setError(null)

    try {
      const result = await alpacaTrading.getClock()
      setClock(result)
    } catch (err) {
      console.error('[useMarketClock] Failed:', err)
      setError(err as Error)
    } finally {
      setLoading(false)
    }
  }, [])

  // 计算属性
  const isOpen = useMemo(() => clock?.is_open || false, [clock])
  const nextOpen = useMemo(() => clock?.next_open ? new Date(clock.next_open) : null, [clock])
  const nextClose = useMemo(() => clock?.next_close ? new Date(clock.next_close) : null, [clock])

  // 初始加载
  useEffect(() => {
    refresh()
    // 每分钟刷新一次
    const interval = setInterval(refresh, 60000)
    return () => clearInterval(interval)
  }, [refresh])

  return {
    clock,
    isOpen,
    nextOpen,
    nextClose,
    loading,
    error,
    refresh,
  }
}

// ==================== 交易活动 Hook ====================

interface UseActivitiesOptions {
  activityTypes?: string[]
  limit?: number
  autoLoad?: boolean
}

interface Activity {
  id: string
  activity_type: string
  transaction_time: string
  symbol?: string
  side?: string
  qty?: string
  price?: string
  net_amount?: string
}

interface UseActivitiesResult {
  activities: Activity[]
  loading: boolean
  error: Error | null
  refresh: () => Promise<void>
  loadMore: () => Promise<void>
  hasMore: boolean
}

/**
 * 交易活动 Hook
 */
export function useActivities(options: UseActivitiesOptions = {}): UseActivitiesResult {
  const { activityTypes, limit = 50, autoLoad = true } = options

  const [activities, setActivities] = useState<Activity[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)
  const [pageToken, setPageToken] = useState<string | undefined>()
  const [hasMore, setHasMore] = useState(true)

  const refresh = useCallback(async () => {
    setLoading(true)
    setError(null)

    try {
      const result = await alpacaTrading.getAccountActivities(activityTypes, {
        page_size: limit,
      })
      setActivities(result)
      setHasMore(result.length >= limit)
      setPageToken(result.length > 0 ? result[result.length - 1].id : undefined)
    } catch (err) {
      console.error('[useActivities] Failed:', err)
      setError(err as Error)
    } finally {
      setLoading(false)
    }
  }, [activityTypes, limit])

  const loadMore = useCallback(async () => {
    if (!hasMore || loading) return

    setLoading(true)
    setError(null)

    try {
      const result = await alpacaTrading.getAccountActivities(activityTypes, {
        page_size: limit,
        page_token: pageToken,
      })
      setActivities(prev => [...prev, ...result])
      setHasMore(result.length >= limit)
      setPageToken(result.length > 0 ? result[result.length - 1].id : undefined)
    } catch (err) {
      console.error('[useActivities] Load more failed:', err)
      setError(err as Error)
    } finally {
      setLoading(false)
    }
  }, [activityTypes, limit, pageToken, hasMore, loading])

  // 初始加载
  useEffect(() => {
    if (autoLoad) {
      refresh()
    }
  }, [autoLoad, refresh])

  return {
    activities,
    loading,
    error,
    refresh,
    loadMore,
    hasMore,
  }
}

// ==================== 综合交易状态 Hook ====================

interface UseTradingStatusResult {
  // 账户
  account: AlpacaAccount | null
  buyingPower: number
  cash: number
  equity: number

  // 持仓
  positions: Position[]
  totalPnL: number
  totalPnLPercent: number

  // 市场
  isMarketOpen: boolean
  nextOpen: Date | null
  nextClose: Date | null

  // 状态
  loading: boolean
  error: Error | null
  isAuthenticated: boolean
  environment: 'paper' | 'live'

  // 操作
  refresh: () => Promise<void>
}

/**
 * 综合交易状态 Hook
 */
export function useTradingStatus(): UseTradingStatusResult {
  const accountData = useAccount({ refreshInterval: 30000 })
  const positionsData = usePositions({ refreshInterval: 5000 })
  const clockData = useMarketClock()

  const refresh = useCallback(async () => {
    await Promise.all([
      accountData.refresh(),
      positionsData.refresh(),
      clockData.refresh(),
    ])
  }, [accountData, positionsData, clockData])

  return {
    account: accountData.account,
    buyingPower: accountData.buyingPower,
    cash: accountData.cash,
    equity: accountData.equity,
    positions: positionsData.positions,
    totalPnL: positionsData.totalPnL,
    totalPnLPercent: positionsData.totalPnLPercent,
    isMarketOpen: clockData.isOpen,
    nextOpen: clockData.nextOpen,
    nextClose: clockData.nextClose,
    loading: accountData.loading || positionsData.loading || clockData.loading,
    error: accountData.error || positionsData.error || clockData.error,
    isAuthenticated: accountData.isAuthenticated,
    environment: accountData.environment,
    refresh,
  }
}

export default useAccount
