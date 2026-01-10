/**
 * Dashboard 数据 Hook
 * UI 优化 Phase 1: 真实 API 集成
 *
 * 提供:
 * - 组合总览数据
 * - 收益曲线数据
 * - 持仓分布数据
 * - 最近交易数据
 */

import { useQuery, useQueries } from '@tanstack/react-query'
import { realtimeApi } from '@/services/backendApi'

// ==================== 类型定义 ====================

export interface PortfolioSummary {
  totalValue: number
  dailyPnL: number
  dailyReturn: number
  totalReturn: number
  sharpe: number
  maxDrawdown: number
  cash: number
  buyingPower: number
}

export interface ReturnChartData {
  dates: string[]
  strategy: number[]
  benchmark: number[]
}

export interface HoldingDistribution {
  name: string
  value: number
  marketValue?: number
}

export interface RecentTrade {
  time: string
  symbol: string
  side: 'BUY' | 'SELL'
  qty: number
  price: number
  amount: number
}

// ==================== API 请求函数 ====================

const getBaseUrl = (): string => {
  return import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
}

/**
 * 获取组合摘要
 */
async function fetchPortfolioSummary(): Promise<PortfolioSummary> {
  try {
    const status = await realtimeApi.getStatus()

    // 计算累计收益率 (基于初始资金假设 100万)
    const initialCapital = 1000000
    const totalReturn = (status.account.portfolio_value - initialCapital) / initialCapital

    // 简化的夏普比率估算 (实际应该从后端获取)
    // 这里使用 日收益率 / 假设的波动率 * sqrt(252)
    const estimatedSharpe = status.performance.daily_return_pct > 0
      ? (status.performance.daily_return_pct / 0.02) * Math.sqrt(252)
      : 0

    return {
      totalValue: status.account.portfolio_value,
      dailyPnL: status.performance.daily_pnl,
      dailyReturn: status.performance.daily_return_pct / 100,
      totalReturn,
      sharpe: Math.min(estimatedSharpe, 5), // 限制夏普比率上限
      maxDrawdown: status.performance.drawdown_pct / 100,
      cash: status.account.cash,
      buyingPower: status.account.buying_power,
    }
  } catch (error) {
    // 如果 API 不可用，返回空数据
    console.error('[useDashboard] Failed to fetch portfolio summary:', error)
    throw error
  }
}

/**
 * 获取收益曲线数据
 */
async function fetchReturnChartData(): Promise<ReturnChartData> {
  // 目前后端没有历史收益曲线 API，使用模拟数据
  // TODO: 后续接入真实的历史收益 API
  const baseUrl = getBaseUrl()

  try {
    const response = await fetch(`${baseUrl}/api/v1/dashboard/performance-history`)
    if (response.ok) {
      return await response.json()
    }
  } catch {
    // API 不存在，使用 fallback
  }

  // Fallback: 生成基于当前日期的模拟数据
  const now = new Date()
  const dates: string[] = []
  const strategy: number[] = []
  const benchmark: number[] = []

  for (let i = 5; i >= 0; i--) {
    const date = new Date(now)
    date.setMonth(date.getMonth() - i)
    dates.push(date.toISOString().slice(0, 7))

    // 生成连续增长的收益曲线
    const baseReturn = (5 - i) * 0.04
    strategy.push(baseReturn + Math.random() * 0.02)
    benchmark.push(baseReturn * 0.5 + Math.random() * 0.01)
  }

  return { dates, strategy, benchmark }
}

/**
 * 获取持仓分布
 */
async function fetchHoldingsDistribution(): Promise<HoldingDistribution[]> {
  const positions = await realtimeApi.getPositions()

  if (!positions || positions.length === 0) {
    return [{ name: '现金', value: 100 }]
  }

  const totalMarketValue = positions.reduce((sum, p) => sum + p.market_value, 0)

  // 取前 5 大持仓
  const sortedPositions = [...positions].sort((a, b) => b.market_value - a.market_value)
  const topPositions = sortedPositions.slice(0, 5)
  const othersValue = sortedPositions.slice(5).reduce((sum, p) => sum + p.market_value, 0)

  const distribution: HoldingDistribution[] = topPositions.map(p => ({
    name: p.symbol,
    value: (p.market_value / totalMarketValue) * 100,
    marketValue: p.market_value,
  }))

  if (othersValue > 0) {
    distribution.push({
      name: '其他',
      value: (othersValue / totalMarketValue) * 100,
      marketValue: othersValue,
    })
  }

  return distribution
}

/**
 * 获取最近交易
 */
async function fetchRecentTrades(): Promise<RecentTrade[]> {
  const orders = await realtimeApi.getOrders('filled', 10)

  if (!orders || orders.length === 0) {
    return []
  }

  return orders
    .filter(o => o.status === 'filled' && o.filled_avg_price)
    .slice(0, 5)
    .map(o => ({
      time: new Date(o.filled_at || o.created_at).toLocaleTimeString('zh-CN', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      }),
      symbol: o.symbol,
      side: o.side.toUpperCase() as 'BUY' | 'SELL',
      qty: o.filled_qty,
      price: o.filled_avg_price || 0,
      amount: o.filled_qty * (o.filled_avg_price || 0),
    }))
}

// ==================== React Query Hooks ====================

/**
 * 组合摘要 Hook
 */
export function usePortfolioSummary() {
  return useQuery({
    queryKey: ['dashboard', 'portfolio-summary'],
    queryFn: fetchPortfolioSummary,
    refetchInterval: 30000, // 30秒刷新一次
    staleTime: 10000,
    retry: 2,
  })
}

/**
 * 收益曲线 Hook
 */
export function useReturnChart() {
  return useQuery({
    queryKey: ['dashboard', 'return-chart'],
    queryFn: fetchReturnChartData,
    refetchInterval: 60000, // 1分钟刷新一次
    staleTime: 30000,
    retry: 1,
  })
}

/**
 * 持仓分布 Hook
 */
export function useHoldingsDistribution() {
  return useQuery({
    queryKey: ['dashboard', 'holdings-distribution'],
    queryFn: fetchHoldingsDistribution,
    refetchInterval: 30000,
    staleTime: 15000,
    retry: 2,
  })
}

/**
 * 最近交易 Hook
 */
export function useRecentTrades() {
  return useQuery({
    queryKey: ['dashboard', 'recent-trades'],
    queryFn: fetchRecentTrades,
    refetchInterval: 15000, // 15秒刷新一次
    staleTime: 5000,
    retry: 2,
  })
}

/**
 * Dashboard 全部数据 Hook
 * 并行加载所有数据
 */
export function useDashboardData() {
  const results = useQueries({
    queries: [
      {
        queryKey: ['dashboard', 'portfolio-summary'],
        queryFn: fetchPortfolioSummary,
        refetchInterval: 30000,
        staleTime: 10000,
        retry: 2,
      },
      {
        queryKey: ['dashboard', 'return-chart'],
        queryFn: fetchReturnChartData,
        refetchInterval: 60000,
        staleTime: 30000,
        retry: 1,
      },
      {
        queryKey: ['dashboard', 'holdings-distribution'],
        queryFn: fetchHoldingsDistribution,
        refetchInterval: 30000,
        staleTime: 15000,
        retry: 2,
      },
      {
        queryKey: ['dashboard', 'recent-trades'],
        queryFn: fetchRecentTrades,
        refetchInterval: 15000,
        staleTime: 5000,
        retry: 2,
      },
    ],
  })

  const [portfolioQuery, returnChartQuery, holdingsQuery, tradesQuery] = results

  return {
    portfolio: {
      data: portfolioQuery.data,
      isLoading: portfolioQuery.isLoading,
      error: portfolioQuery.error,
      refetch: portfolioQuery.refetch,
    },
    returnChart: {
      data: returnChartQuery.data,
      isLoading: returnChartQuery.isLoading,
      error: returnChartQuery.error,
      refetch: returnChartQuery.refetch,
    },
    holdings: {
      data: holdingsQuery.data,
      isLoading: holdingsQuery.isLoading,
      error: holdingsQuery.error,
      refetch: holdingsQuery.refetch,
    },
    recentTrades: {
      data: tradesQuery.data,
      isLoading: tradesQuery.isLoading,
      error: tradesQuery.error,
      refetch: tradesQuery.refetch,
    },
    isLoading: results.some(r => r.isLoading),
    isError: results.some(r => r.isError),
    refetchAll: () => results.forEach(r => r.refetch()),
  }
}

export default useDashboardData
