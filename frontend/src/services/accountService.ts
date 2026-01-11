/**
 * 账户服务
 * 账户总览、持仓、运行中策略 API
 *
 * 数据源: Alpaca API (Paper/Live)
 * 当API不可用时会降级到Mock数据，通过data_source字段标识
 */

import { apiGet } from './api'
import { DataSourceStatus } from '../components/common/DataSourceIndicator'

// ==================== 类型定义 ====================

export interface AccountInfo {
  total_value: number
  cash_balance: number
  buying_power: number
  portfolio_value: number
  day_pnl: number
  day_pnl_pct: number
  total_pnl: number
  total_pnl_pct: number
}

export interface Position {
  symbol: string
  quantity: number
  avg_cost: number
  current_price: number
  market_value: number
  pnl: number
  pnl_pct: number
  weight: number
}

export interface RunningStrategy {
  id: string
  name: string
  environment: 'paper' | 'live'
  status: 'running' | 'paused'
  pnl: number
  pnl_pct: number
  trades: number
  win_rate: number
  started_at: string
}

export interface AccountOverviewResponse {
  account: AccountInfo
  positions: Position[]
  running_strategies: RunningStrategy[]
  last_updated: string
  data_sources: {
    account: DataSourceStatus
    positions: DataSourceStatus
    strategies: DataSourceStatus
  }
}

export interface DataResponse<T> {
  data: T
  data_source: DataSourceStatus
}

export interface DataSourcesStatusResponse {
  account: DataSourceStatus
  positions: DataSourceStatus
  strategies: DataSourceStatus
  overall_status: 'connected' | 'degraded' | 'disconnected'
}

// ==================== API 调用 ====================

/**
 * 获取账户总览
 * 包含账户信息、持仓、运行策略及各数据源状态
 */
export async function getAccountOverview(): Promise<AccountOverviewResponse> {
  const response = await apiGet<AccountOverviewResponse>('/api/v1/account/overview')
  return response
}

/**
 * 获取账户信息（含数据源状态）
 */
export async function getAccountInfo(): Promise<DataResponse<AccountInfo>> {
  const response = await apiGet<DataResponse<AccountInfo>>('/api/v1/account/info')
  return response
}

/**
 * 获取持仓列表（含数据源状态）
 */
export async function getPositions(): Promise<DataResponse<Position[]>> {
  const response = await apiGet<DataResponse<Position[]>>('/api/v1/account/positions')
  return response
}

/**
 * 获取运行中策略（含数据源状态）
 */
export async function getRunningStrategies(): Promise<DataResponse<RunningStrategy[]>> {
  const response = await apiGet<DataResponse<RunningStrategy[]>>('/api/v1/account/strategies')
  return response
}

/**
 * 获取所有数据源状态
 */
export async function getDataSourcesStatus(): Promise<DataSourcesStatusResponse> {
  const response = await apiGet<DataSourcesStatusResponse>('/api/v1/account/data-sources')
  return response
}

// ==================== 辅助函数 ====================

/**
 * 检查是否有任何数据源使用Mock
 */
export function hasAnyMockData(response: AccountOverviewResponse): boolean {
  const { data_sources } = response
  return (
    data_sources.account?.is_mock ||
    data_sources.positions?.is_mock ||
    data_sources.strategies?.is_mock
  )
}

/**
 * 获取Mock数据源列表
 */
export function getMockDataSources(response: AccountOverviewResponse): string[] {
  const mockSources: string[] = []
  const { data_sources } = response

  if (data_sources.account?.is_mock) mockSources.push('账户信息')
  if (data_sources.positions?.is_mock) mockSources.push('持仓数据')
  if (data_sources.strategies?.is_mock) mockSources.push('运行策略')

  return mockSources
}

/**
 * 格式化数据源状态消息
 */
export function formatDataSourceMessage(response: AccountOverviewResponse): string | null {
  const mockSources = getMockDataSources(response)
  if (mockSources.length === 0) return null
  return `以下数据使用模拟数据: ${mockSources.join(', ')}`
}
