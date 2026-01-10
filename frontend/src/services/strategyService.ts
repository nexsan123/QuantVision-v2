/**
 * 策略服务 - API 调用 + localStorage 持久化
 * Sprint 1 - F2: 策略数据持久化
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

// 是否使用 Mock 数据 (设置为 false 连接真实后端 API)
const USE_MOCK = false

// ==================== 默认策略数据 ====================

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
  {
    id: 'stg-004',
    name: '多因子选股策略',
    description: '综合动量、价值、质量因子的多因子策略',
    status: 'backtest',
    source: 'custom',
    config: {
      name: '多因子选股策略',
      description: '综合动量、价值、质量因子的多因子策略',
      status: 'backtest',
    } as StrategyConfig,
    deploymentCount: 0,
    createdBy: 'user-001',
    createdAt: '2024-12-18T16:00:00Z',
    updatedAt: '2024-12-20T10:00:00Z',
    tags: ['多因子'],
    isFavorite: false,
  },
]

// ==================== 初始化 localStorage ====================

function ensureInitialized(): void {
  if (!strategyStorage.isInitialized() || strategyStorage.getAll().length === 0) {
    strategyStorage.save(DEFAULT_STRATEGIES)
    console.log('[StrategyService] Initialized with default strategies')
  }
}

// ==================== Mock 实现 (使用 localStorage) ====================

async function mockDelay(ms: number = 300): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms))
}

async function mockGetStrategies(params: StrategyFilterParams): Promise<StrategyListResponse> {
  await mockDelay()
  ensureInitialized()

  let filtered = [...strategyStorage.getAll()]

  if (params.status) {
    filtered = filtered.filter(s => s.status === params.status)
  }
  if (params.source) {
    filtered = filtered.filter(s => s.source === params.source)
  }
  if (params.isFavorite !== undefined) {
    filtered = filtered.filter(s => s.isFavorite === params.isFavorite)
  }
  if (params.search) {
    const search = params.search.toLowerCase()
    filtered = filtered.filter(
      s =>
        s.name.toLowerCase().includes(search) ||
        s.description.toLowerCase().includes(search)
    )
  }
  if (params.tags && params.tags.length > 0) {
    filtered = filtered.filter(s =>
      params.tags!.some(tag => s.tags?.includes(tag))
    )
  }

  // 排序
  const sortBy = params.sortBy || 'updatedAt'
  const sortOrder = params.sortOrder || 'desc'
  filtered.sort((a, b) => {
    let aVal: string | number = a[sortBy as keyof Strategy] as string | number
    let bVal: string | number = b[sortBy as keyof Strategy] as string | number

    if (sortBy === 'lastBacktest') {
      aVal = a.lastBacktest?.completedAt || ''
      bVal = b.lastBacktest?.completedAt || ''
    }

    if (aVal < bVal) return sortOrder === 'asc' ? -1 : 1
    if (aVal > bVal) return sortOrder === 'asc' ? 1 : -1
    return 0
  })

  // 分页
  const page = params.page || 1
  const pageSize = params.pageSize || 10
  const start = (page - 1) * pageSize
  const items = filtered.slice(start, start + pageSize)

  return {
    total: filtered.length,
    items,
  }
}

async function mockGetStrategy(id: string): Promise<Strategy | null> {
  await mockDelay()
  ensureInitialized()
  return strategyStorage.getById(id)
}

async function mockCreateStrategy(data: StrategyCreateRequest): Promise<Strategy> {
  await mockDelay()
  ensureInitialized()

  const newStrategy: Strategy = {
    id: `stg-${Date.now()}`,
    name: data.name,
    description: data.description || '',
    status: 'draft',
    source: data.source || 'custom',
    templateId: data.templateId,
    config: data.config as StrategyConfig,
    deploymentCount: 0,
    createdBy: 'user-001',
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    tags: data.tags,
    isFavorite: false,
  }

  // 保存到 localStorage
  const strategies = strategyStorage.getAll()
  strategies.unshift(newStrategy)
  strategyStorage.save(strategies)

  return newStrategy
}

async function mockUpdateStrategy(id: string, data: StrategyUpdateRequest): Promise<Strategy> {
  await mockDelay()
  ensureInitialized()

  const strategies = strategyStorage.getAll()
  const index = strategies.findIndex(s => s.id === id)
  if (index === -1) {
    throw new Error('策略不存在')
  }

  const updated: Strategy = {
    ...strategies[index],
    ...data,
    config: data.config
      ? { ...strategies[index].config, ...data.config }
      : strategies[index].config,
    updatedAt: new Date().toISOString(),
  }

  strategies[index] = updated
  strategyStorage.save(strategies)
  return updated
}

async function mockDeleteStrategy(id: string): Promise<void> {
  await mockDelay()
  ensureInitialized()
  strategyStorage.delete(id)
}

async function mockUpdateBacktestResult(id: string, result: BacktestSummary): Promise<Strategy> {
  await mockDelay()
  ensureInitialized()

  const strategies = strategyStorage.getAll()
  const index = strategies.findIndex(s => s.id === id)
  if (index === -1) {
    throw new Error('策略不存在')
  }

  strategies[index] = {
    ...strategies[index],
    lastBacktest: result,
    updatedAt: new Date().toISOString(),
  }

  strategyStorage.save(strategies)
  return strategies[index]
}

// ==================== 公开 API ====================

/**
 * 获取策略列表
 */
export async function getStrategies(params: StrategyFilterParams = {}): Promise<StrategyListResponse> {
  if (USE_MOCK) {
    return mockGetStrategies(params)
  }
  return apiGet<StrategyListResponse>('/api/v1/strategies/v2/', params as Record<string, string | number | boolean | undefined>)
}

/**
 * 获取单个策略
 */
export async function getStrategy(id: string): Promise<Strategy | null> {
  if (USE_MOCK) {
    return mockGetStrategy(id)
  }
  return apiGet<Strategy>(`/api/v1/strategies/v2/${id}`)
}

/**
 * 创建策略
 */
export async function createStrategy(data: StrategyCreateRequest): Promise<Strategy> {
  if (USE_MOCK) {
    return mockCreateStrategy(data)
  }
  return apiPost<Strategy>('/api/v1/strategies/v2/', data)
}

/**
 * 更新策略
 */
export async function updateStrategy(id: string, data: StrategyUpdateRequest): Promise<Strategy> {
  if (USE_MOCK) {
    return mockUpdateStrategy(id, data)
  }
  return apiPut<Strategy>(`/api/v1/strategies/v2/${id}`, data)
}

/**
 * 删除策略
 */
export async function deleteStrategy(id: string): Promise<void> {
  if (USE_MOCK) {
    return mockDeleteStrategy(id)
  }
  return apiDelete(`/api/v1/strategies/v2/${id}`)
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
  if (USE_MOCK) {
    return mockUpdateBacktestResult(id, result)
  }
  return apiPost<Strategy>(`/api/v1/strategies/v2/${id}/backtest-result`, result)
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
