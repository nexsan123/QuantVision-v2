/**
 * 策略服务 - API 调用 + localStorage 缓存
 *
 * 数据源: 后端 API (PostgreSQL)
 * 本地存储用于缓存，提升用户体验
 */

import { apiGet, apiPost, apiPut, apiDelete } from './api'
import { strategyStorage } from './storageService'
import type {
  Strategy,
  StrategyListResponse,
  StrategyCreateRequest,
  StrategyUpdateRequest,
  StrategyFilterParams,
  StrategyConfig,
  BacktestSummary,
} from '../types/strategy'

// ==================== 数据源状态 ====================

export interface StrategyDataSource {
  source: 'api' | 'cache' | 'default'
  is_mock: boolean
  error_message?: string
  last_sync?: string
}

let currentDataSource: StrategyDataSource = {
  source: 'api',
  is_mock: false,
}

export function getStrategyDataSource(): StrategyDataSource {
  return currentDataSource
}

// ==================== 默认策略数据 (仅用于演示/降级) ====================

const DEFAULT_STRATEGIES: Strategy[] = [
  {
    id: 'stg-001',
    name: '价值投资策略',
    description: '基于PE、PB等估值因子的价值投资策略',
    status: 'draft',
    source: 'custom',
    config: {
      name: '价值投资策略',
      description: '基于PE、PB等估值因子的价值投资策略',
      status: 'draft',
    } as StrategyConfig,
    deploymentCount: 0,
    createdBy: 'user-001',
    createdAt: '2024-12-10T10:00:00Z',
    updatedAt: '2024-12-15T14:30:00Z',
    tags: ['价值', '长期'],
    isFavorite: true,
    lastBacktest: {
      backtestId: 'bt-001',
      annualReturn: 0.156,
      sharpeRatio: 1.32,
      maxDrawdown: -0.082,
      winRate: 0.58,
      startDate: '2022-01-01',
      endDate: '2024-12-01',
      completedAt: '2024-12-14T16:00:00Z',
    },
  },
  {
    id: 'stg-002',
    name: '动量突破策略',
    description: '基于价格动量和成交量的短线策略',
    status: 'paper',
    source: 'template',
    templateId: 'tpl-momentum',
    config: {
      name: '动量突破策略',
      description: '基于价格动量和成交量的短线策略',
      status: 'paper',
    } as StrategyConfig,
    deploymentCount: 1,
    createdBy: 'user-001',
    createdAt: '2024-11-20T09:00:00Z',
    updatedAt: '2024-12-18T11:00:00Z',
    tags: ['动量', '短线'],
    isFavorite: false,
    lastBacktest: {
      backtestId: 'bt-002',
      annualReturn: 0.234,
      sharpeRatio: 1.56,
      maxDrawdown: -0.125,
      winRate: 0.52,
      startDate: '2023-01-01',
      endDate: '2024-12-01',
      completedAt: '2024-12-17T10:00:00Z',
    },
  },
  {
    id: 'stg-003',
    name: '均值回归策略',
    description: '基于RSI超买超卖的均值回归策略',
    status: 'live',
    source: 'custom',
    config: {
      name: '均值回归策略',
      description: '基于RSI超买超卖的均值回归策略',
      status: 'live',
    } as StrategyConfig,
    deploymentCount: 2,
    createdBy: 'user-001',
    createdAt: '2024-10-15T08:00:00Z',
    updatedAt: '2024-12-20T09:30:00Z',
    tags: ['均值回归', '中线'],
    isFavorite: true,
    lastBacktest: {
      backtestId: 'bt-003',
      annualReturn: 0.189,
      sharpeRatio: 1.45,
      maxDrawdown: -0.098,
      winRate: 0.62,
      startDate: '2021-01-01',
      endDate: '2024-12-01',
      completedAt: '2024-12-10T15:00:00Z',
    },
  },
]

// ==================== 缓存管理 ====================

function updateCache(strategies: Strategy[]): void {
  strategyStorage.save(strategies)
}

function getFromCache(): Strategy[] {
  if (!strategyStorage.isInitialized()) {
    return []
  }
  return strategyStorage.getAll()
}

// ==================== API 调用 ====================

/**
 * 获取策略列表
 */
export async function getStrategies(params: StrategyFilterParams = {}): Promise<StrategyListResponse> {
  try {
    const response = await apiGet<{ total: number; strategies: Strategy[] }>(
      "/api/v1/strategies/v2/",
      params as Record<string, string | number | boolean | undefined>
    )

    const result = {
      total: response.total,
      items: response.strategies || [],
    }

    // 更新缓存
    if (result.items.length > 0) {
      updateCache(result.items)
    }

    currentDataSource = {
      source: 'api',
      is_mock: false,
      last_sync: new Date().toISOString(),
    }

    return result
  } catch (error) {
    console.warn('[StrategyService] API failed, using cache/default:', error)

    // 尝试从缓存获取
    const cached = getFromCache()
    if (cached.length > 0) {
      currentDataSource = {
        source: 'cache',
        is_mock: true,
        error_message: 'Using cached data - API unavailable',
        last_sync: strategyStorage.getLastSync() || undefined,
      }
      return { total: cached.length, items: cached }
    }

    // 使用默认数据
    currentDataSource = {
      source: 'default',
      is_mock: true,
      error_message: 'Using default demo data - API unavailable',
    }
    return { total: DEFAULT_STRATEGIES.length, items: DEFAULT_STRATEGIES }
  }
}

/**
 * 获取单个策略
 */
export async function getStrategy(id: string): Promise<Strategy | null> {
  try {
    const strategy = await apiGet<Strategy>(`/api/v1/strategies/v2/${id}`)
    currentDataSource = { source: 'api', is_mock: false }
    return strategy
  } catch (error) {
    console.warn(`[StrategyService] Failed to get strategy ${id}:`, error)

    // 从缓存查找
    const cached = getFromCache()
    const found = cached.find(s => s.id === id)
    if (found) {
      currentDataSource = { source: 'cache', is_mock: true }
      return found
    }

    // 从默认数据查找
    const defaultFound = DEFAULT_STRATEGIES.find(s => s.id === id)
    if (defaultFound) {
      currentDataSource = { source: 'default', is_mock: true }
      return defaultFound
    }

    return null
  }
}

/**
 * 创建策略
 */
export async function createStrategy(data: StrategyCreateRequest): Promise<Strategy> {
  try {
    const strategy = await apiPost<Strategy>('/api/v1/strategies/v2/', data)
    currentDataSource = { source: 'api', is_mock: false }

    // 更新缓存
    const cached = getFromCache()
    cached.unshift(strategy)
    updateCache(cached)

    return strategy
  } catch (error) {
    console.error('[StrategyService] Failed to create strategy:', error)
    throw new Error('无法创建策略，请检查网络连接')
  }
}

/**
 * 更新策略
 */
export async function updateStrategy(id: string, data: StrategyUpdateRequest): Promise<Strategy> {
  try {
    const strategy = await apiPut<Strategy>(`/api/v1/strategies/v2/${id}`, data)
    currentDataSource = { source: 'api', is_mock: false }

    // 更新缓存
    const cached = getFromCache()
    const index = cached.findIndex(s => s.id === id)
    if (index !== -1) {
      cached[index] = strategy
      updateCache(cached)
    }

    return strategy
  } catch (error) {
    console.error('[StrategyService] Failed to update strategy:', error)
    throw new Error('无法更新策略，请检查网络连接')
  }
}

/**
 * 删除策略
 */
export async function deleteStrategy(id: string): Promise<void> {
  try {
    await apiDelete(`/api/v1/strategies/v2/${id}`)
    currentDataSource = { source: 'api', is_mock: false }

    // 更新缓存
    strategyStorage.delete(id)
  } catch (error) {
    console.error('[StrategyService] Failed to delete strategy:', error)
    throw new Error('无法删除策略，请检查网络连接')
  }
}

/**
 * 切换收藏状态
 */
export async function toggleFavorite(id: string): Promise<Strategy> {
  const strategy = await getStrategy(id)
  if (!strategy) {
    throw new Error('策略不存在')
  }
  return updateStrategy(id, { isFavorite: !strategy.isFavorite })
}

/**
 * 更新回测结果
 */
export async function updateBacktestResult(id: string, result: BacktestSummary): Promise<Strategy> {
  try {
    const strategy = await apiPost<Strategy>(`/api/v1/strategies/v2/${id}/backtest-result`, result)
    currentDataSource = { source: 'api', is_mock: false }
    return strategy
  } catch (error) {
    console.error('[StrategyService] Failed to update backtest result:', error)
    throw new Error('无法更新回测结果')
  }
}

/**
 * 复制策略
 */
export async function duplicateStrategy(id: string, newName: string): Promise<Strategy> {
  const original = await getStrategy(id)
  if (!original) {
    throw new Error('原策略不存在')
  }

  return createStrategy({
    name: newName,
    description: original.description,
    source: 'custom',
    config: original.config,
    tags: original.tags,
  })
}
