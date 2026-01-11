/**
 * 部署服务 - API 调用 + localStorage 缓存
 *
 * 数据源: 后端 API (PostgreSQL)
 * 本地存储用于缓存，提升用户体验
 */

import { apiGet, apiPost, apiPut, apiDelete } from './api'
import { deploymentStorage } from './storageService'
import type {
  Deployment,
  DeploymentListResponse,
  DeploymentCreateRequest,
  DeploymentUpdateRequest,
  DeploymentStatus,
  DeploymentEnvironment,
} from '../types/deployment'

// ==================== 数据源状态 ====================

export interface DeploymentDataSource {
  source: 'api' | 'cache' | 'default'
  is_mock: boolean
  error_message?: string
  last_sync?: string
}

let currentDataSource: DeploymentDataSource = {
  source: 'api',
  is_mock: false,
}

export function getDeploymentDataSource(): DeploymentDataSource {
  return currentDataSource
}

// ==================== 默认部署数据 (仅用于演示/降级) ====================

const DEFAULT_DEPLOYMENTS: Deployment[] = [
  {
    deploymentId: 'dep-001',
    strategyId: 'stg-002',
    strategyName: '动量突破策略',
    deploymentName: '动量策略-模拟盘',
    environment: 'paper',
    status: 'running',
    strategyType: 'short_term',
    config: {
      strategyId: 'stg-002',
      deploymentName: '动量策略-模拟盘',
      environment: 'paper',
      strategyType: 'short_term',
      universeConfig: { mode: 'full', maxPositions: 10 },
      executionMode: 'auto',
      riskParams: {
        stopLoss: -0.05,
        takeProfit: 0.10,
        maxPositionPct: 0.10,
        maxDrawdown: -0.15,
      },
      capitalConfig: {
        totalCapital: 50000,
        initialPositionPct: 0.80,
        reserveCashPct: 0.20,
      },
      rebalanceFrequency: 'daily',
      rebalanceTime: '09:35',
    },
    currentPnl: 2345.67,
    currentPnlPct: 0.047,
    totalTrades: 28,
    winRate: 0.54,
    createdAt: '2024-12-18T11:00:00Z',
    updatedAt: '2024-12-20T09:30:00Z',
    startedAt: '2024-12-18T11:30:00Z',
  },
  {
    deploymentId: 'dep-002',
    strategyId: 'stg-003',
    strategyName: '均值回归策略',
    deploymentName: '均值回归-实盘1',
    environment: 'live',
    status: 'running',
    strategyType: 'medium_term',
    config: {
      strategyId: 'stg-003',
      deploymentName: '均值回归-实盘1',
      environment: 'live',
      strategyType: 'medium_term',
      universeConfig: { mode: 'full', maxPositions: 15 },
      executionMode: 'confirm',
      riskParams: {
        stopLoss: -0.08,
        takeProfit: 0.15,
        maxPositionPct: 0.08,
        maxDrawdown: -0.12,
      },
      capitalConfig: {
        totalCapital: 100000,
        initialPositionPct: 0.70,
        reserveCashPct: 0.30,
      },
      rebalanceFrequency: 'weekly',
      rebalanceTime: '09:30',
    },
    currentPnl: 8932.50,
    currentPnlPct: 0.089,
    totalTrades: 45,
    winRate: 0.62,
    createdAt: '2024-11-01T10:00:00Z',
    updatedAt: '2024-12-20T10:00:00Z',
    startedAt: '2024-11-01T10:30:00Z',
  },
]

// ==================== 缓存管理 ====================

function updateCache(deployments: Deployment[]): void {
  deploymentStorage.save(deployments)
}

function getFromCache(): Deployment[] {
  if (!deploymentStorage.isInitialized()) {
    return []
  }
  return deploymentStorage.getAll()
}

// ==================== 筛选参数接口 ====================

interface DeploymentFilterParams {
  strategyId?: string
  environment?: DeploymentEnvironment
  status?: DeploymentStatus
  page?: number
  pageSize?: number
}

// ==================== API 调用 ====================

/**
 * 获取部署列表
 */
export async function getDeployments(params: DeploymentFilterParams = {}): Promise<DeploymentListResponse> {
  try {
    const response = await apiGet<DeploymentListResponse>(
      '/api/v1/deployments',
      params as Record<string, string | number | boolean | undefined>
    )

    // 更新缓存
    if (response.items && response.items.length > 0) {
      updateCache(response.items)
    }

    currentDataSource = {
      source: 'api',
      is_mock: false,
      last_sync: new Date().toISOString(),
    }

    return response
  } catch (error) {
    console.warn('[DeploymentService] API failed, using cache/default:', error)

    // 尝试从缓存获取
    const cached = getFromCache()
    if (cached.length > 0) {
      // 应用过滤
      let filtered = [...cached]
      if (params.strategyId) {
        filtered = filtered.filter(d => d.strategyId === params.strategyId)
      }
      if (params.environment) {
        filtered = filtered.filter(d => d.environment === params.environment)
      }
      if (params.status) {
        filtered = filtered.filter(d => d.status === params.status)
      }

      currentDataSource = {
        source: 'cache',
        is_mock: true,
        error_message: 'Using cached data - API unavailable',
      }
      return { total: filtered.length, items: filtered }
    }

    // 使用默认数据
    currentDataSource = {
      source: 'default',
      is_mock: true,
      error_message: 'Using default demo data - API unavailable',
    }
    return { total: DEFAULT_DEPLOYMENTS.length, items: DEFAULT_DEPLOYMENTS }
  }
}

/**
 * 获取单个部署
 */
export async function getDeployment(id: string): Promise<Deployment | null> {
  try {
    const deployment = await apiGet<Deployment>(`/api/v1/deployments/${id}`)
    currentDataSource = { source: 'api', is_mock: false }
    return deployment
  } catch (error) {
    console.warn(`[DeploymentService] Failed to get deployment ${id}:`, error)

    // 从缓存查找
    const cached = getFromCache()
    const found = cached.find(d => d.deploymentId === id)
    if (found) {
      currentDataSource = { source: 'cache', is_mock: true }
      return found
    }

    // 从默认数据查找
    const defaultFound = DEFAULT_DEPLOYMENTS.find(d => d.deploymentId === id)
    if (defaultFound) {
      currentDataSource = { source: 'default', is_mock: true }
      return defaultFound
    }

    return null
  }
}

/**
 * 按策略ID获取部署列表
 */
export async function getDeploymentsByStrategy(strategyId: string): Promise<Deployment[]> {
  const response = await getDeployments({ strategyId })
  return response.items
}

/**
 * 创建部署
 */
export async function createDeployment(data: DeploymentCreateRequest): Promise<Deployment> {
  try {
    const deployment = await apiPost<Deployment>('/api/v1/deployments', data)
    currentDataSource = { source: 'api', is_mock: false }

    // 更新缓存
    const cached = getFromCache()
    cached.unshift(deployment)
    updateCache(cached)

    return deployment
  } catch (error) {
    console.error('[DeploymentService] Failed to create deployment:', error)
    throw new Error('无法创建部署，请检查网络连接')
  }
}

/**
 * 更新部署
 */
export async function updateDeployment(id: string, data: DeploymentUpdateRequest): Promise<Deployment> {
  try {
    const deployment = await apiPut<Deployment>(`/api/v1/deployments/${id}`, data)
    currentDataSource = { source: 'api', is_mock: false }

    // 更新缓存
    const cached = getFromCache()
    const index = cached.findIndex(d => d.deploymentId === id)
    if (index !== -1) {
      cached[index] = deployment
      updateCache(cached)
    }

    return deployment
  } catch (error) {
    console.error('[DeploymentService] Failed to update deployment:', error)
    throw new Error('无法更新部署，请检查网络连接')
  }
}

/**
 * 删除部署
 */
export async function deleteDeployment(id: string): Promise<void> {
  try {
    await apiDelete(`/api/v1/deployments/${id}`)
    currentDataSource = { source: 'api', is_mock: false }

    // 更新缓存
    deploymentStorage.delete(id)
  } catch (error) {
    console.error('[DeploymentService] Failed to delete deployment:', error)
    throw new Error('无法删除部署，请检查网络连接')
  }
}

/**
 * 启动部署
 */
export async function startDeployment(id: string): Promise<Deployment> {
  try {
    const deployment = await apiPost<Deployment>(`/api/v1/deployments/${id}/start`, {})
    currentDataSource = { source: 'api', is_mock: false }
    return deployment
  } catch (error) {
    console.error('[DeploymentService] Failed to start deployment:', error)
    throw new Error('无法启动部署')
  }
}

/**
 * 暂停部署
 */
export async function pauseDeployment(id: string): Promise<Deployment> {
  try {
    const deployment = await apiPost<Deployment>(`/api/v1/deployments/${id}/pause`, {})
    currentDataSource = { source: 'api', is_mock: false }
    return deployment
  } catch (error) {
    console.error('[DeploymentService] Failed to pause deployment:', error)
    throw new Error('无法暂停部署')
  }
}

/**
 * 停止部署
 */
export async function stopDeployment(id: string): Promise<Deployment> {
  try {
    const deployment = await apiPost<Deployment>(`/api/v1/deployments/${id}/stop`, {})
    currentDataSource = { source: 'api', is_mock: false }
    return deployment
  } catch (error) {
    console.error('[DeploymentService] Failed to stop deployment:', error)
    throw new Error('无法停止部署')
  }
}

/**
 * 切换部署环境
 */
export async function switchDeploymentEnvironment(id: string, environment: DeploymentEnvironment): Promise<Deployment> {
  try {
    const deployment = await apiPost<Deployment>(`/api/v1/deployments/${id}/switch-env`, { environment })
    currentDataSource = { source: 'api', is_mock: false }
    return deployment
  } catch (error) {
    console.error('[DeploymentService] Failed to switch environment:', error)
    throw new Error('无法切换部署环境')
  }
}

/**
 * 获取策略的活跃部署数量
 */
export async function getActiveDeploymentCount(strategyId: string): Promise<number> {
  const deployments = await getDeploymentsByStrategy(strategyId)
  return deployments.filter(d => d.status === 'running').length
}

/**
 * 复制部署配置
 */
export async function duplicateDeployment(id: string, newName: string): Promise<Deployment> {
  const original = await getDeployment(id)
  if (!original) {
    throw new Error('原部署不存在')
  }

  return createDeployment({
    config: {
      ...original.config,
      deploymentName: newName,
    },
    autoStart: false,
  })
}
