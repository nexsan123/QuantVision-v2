/**
 * 部署服务 - API 调用 + localStorage 持久化
 * Sprint 1 - F3: 部署数据持久化
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

// 是否使用 Mock 数据 (设置为 false 连接真实后端 API)
const USE_MOCK = false

// ==================== 默认部署数据 ====================

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
  {
    deploymentId: 'dep-003',
    strategyId: 'stg-003',
    strategyName: '均值回归策略',
    deploymentName: '均值回归-模拟盘',
    environment: 'paper',
    status: 'paused',
    strategyType: 'medium_term',
    config: {
      strategyId: 'stg-003',
      deploymentName: '均值回归-模拟盘',
      environment: 'paper',
      strategyType: 'medium_term',
      universeConfig: { mode: 'full', maxPositions: 20 },
      executionMode: 'auto',
      riskParams: {
        stopLoss: -0.06,
        takeProfit: 0.12,
        maxPositionPct: 0.10,
        maxDrawdown: -0.15,
      },
      capitalConfig: {
        totalCapital: 50000,
        initialPositionPct: 0.80,
        reserveCashPct: 0.20,
      },
      rebalanceFrequency: 'weekly',
      rebalanceTime: '09:30',
    },
    currentPnl: 1250.00,
    currentPnlPct: 0.025,
    totalTrades: 18,
    winRate: 0.56,
    createdAt: '2024-12-01T09:00:00Z',
    updatedAt: '2024-12-15T14:00:00Z',
    startedAt: '2024-12-01T09:30:00Z',
  },
]

// ==================== 初始化 localStorage ====================

function ensureInitialized(): void {
  if (!deploymentStorage.isInitialized() || deploymentStorage.getAll().length === 0) {
    deploymentStorage.save(DEFAULT_DEPLOYMENTS)
    console.log('[DeploymentService] Initialized with default deployments')
  }
}

// ==================== Mock 实现 (使用 localStorage) ====================

async function mockDelay(ms: number = 300): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms))
}

interface DeploymentFilterParams {
  strategyId?: string
  environment?: DeploymentEnvironment
  status?: DeploymentStatus
  page?: number
  pageSize?: number
}

async function mockGetDeployments(params: DeploymentFilterParams = {}): Promise<DeploymentListResponse> {
  await mockDelay()
  ensureInitialized()

  let filtered = [...deploymentStorage.getAll()]

  if (params.strategyId) {
    filtered = filtered.filter(d => d.strategyId === params.strategyId)
  }
  if (params.environment) {
    filtered = filtered.filter(d => d.environment === params.environment)
  }
  if (params.status) {
    filtered = filtered.filter(d => d.status === params.status)
  }

  // 按更新时间排序
  filtered.sort((a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime())

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

async function mockGetDeployment(id: string): Promise<Deployment | null> {
  await mockDelay()
  ensureInitialized()
  return deploymentStorage.getById(id)
}

async function mockGetDeploymentsByStrategy(strategyId: string): Promise<Deployment[]> {
  await mockDelay()
  ensureInitialized()
  return deploymentStorage.getByStrategyId(strategyId)
}

async function mockCreateDeployment(data: DeploymentCreateRequest): Promise<Deployment> {
  await mockDelay()
  ensureInitialized()

  const newDeployment: Deployment = {
    deploymentId: `dep-${Date.now()}`,
    strategyId: data.config.strategyId,
    strategyName: '', // 需要从策略服务获取
    deploymentName: data.config.deploymentName,
    environment: data.config.environment,
    status: data.autoStart ? 'running' : 'draft',
    strategyType: data.config.strategyType,
    config: data.config,
    currentPnl: 0,
    currentPnlPct: 0,
    totalTrades: 0,
    winRate: 0,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    startedAt: data.autoStart ? new Date().toISOString() : undefined,
  }

  deploymentStorage.add(newDeployment)
  return newDeployment
}

async function mockUpdateDeployment(id: string, data: DeploymentUpdateRequest): Promise<Deployment> {
  await mockDelay()
  ensureInitialized()

  const deployment = deploymentStorage.getById(id)
  if (!deployment) {
    throw new Error('部署不存在')
  }

  const updated = deploymentStorage.update(id, {
    ...data,
    config: {
      ...deployment.config,
      ...(data.deploymentName && { deploymentName: data.deploymentName }),
      ...(data.riskParams && { riskParams: data.riskParams }),
      ...(data.capitalConfig && { capitalConfig: data.capitalConfig }),
      ...(data.rebalanceFrequency && { rebalanceFrequency: data.rebalanceFrequency }),
      ...(data.rebalanceTime && { rebalanceTime: data.rebalanceTime }),
    },
  })

  if (!updated) {
    throw new Error('更新失败')
  }

  return updated
}

async function mockDeleteDeployment(id: string): Promise<void> {
  await mockDelay()
  ensureInitialized()
  deploymentStorage.delete(id)
}

async function mockUpdateDeploymentStatus(id: string, status: DeploymentStatus): Promise<Deployment> {
  await mockDelay()
  ensureInitialized()

  const updates: Partial<Deployment> = { status }
  if (status === 'running') {
    updates.startedAt = new Date().toISOString()
  }

  const updated = deploymentStorage.update(id, updates)
  if (!updated) {
    throw new Error('部署不存在')
  }

  return updated
}

async function mockSwitchEnvironment(id: string, environment: DeploymentEnvironment): Promise<Deployment> {
  await mockDelay()
  ensureInitialized()

  const deployment = deploymentStorage.getById(id)
  if (!deployment) {
    throw new Error('部署不存在')
  }

  const updated = deploymentStorage.update(id, {
    environment,
    status: 'draft', // 切换环境后需要重新启动
    config: { ...deployment.config, environment },
  })

  if (!updated) {
    throw new Error('更新失败')
  }

  return updated
}

// ==================== 公开 API ====================

/**
 * 获取部署列表
 */
export async function getDeployments(params: DeploymentFilterParams = {}): Promise<DeploymentListResponse> {
  if (USE_MOCK) {
    return mockGetDeployments(params)
  }
  return apiGet<DeploymentListResponse>('/api/v1/deployments', params as Record<string, string | number | boolean | undefined>)
}

/**
 * 获取单个部署
 */
export async function getDeployment(id: string): Promise<Deployment | null> {
  if (USE_MOCK) {
    return mockGetDeployment(id)
  }
  return apiGet<Deployment>(`/api/v1/deployments/${id}`)
}

/**
 * 按策略ID获取部署列表
 */
export async function getDeploymentsByStrategy(strategyId: string): Promise<Deployment[]> {
  if (USE_MOCK) {
    return mockGetDeploymentsByStrategy(strategyId)
  }
  const response = await apiGet<DeploymentListResponse>('/api/v1/deployments', { strategyId })
  return response.items
}

/**
 * 创建部署
 */
export async function createDeployment(data: DeploymentCreateRequest): Promise<Deployment> {
  if (USE_MOCK) {
    return mockCreateDeployment(data)
  }
  return apiPost<Deployment>('/api/v1/deployments', data)
}

/**
 * 更新部署
 */
export async function updateDeployment(id: string, data: DeploymentUpdateRequest): Promise<Deployment> {
  if (USE_MOCK) {
    return mockUpdateDeployment(id, data)
  }
  return apiPut<Deployment>(`/api/v1/deployments/${id}`, data)
}

/**
 * 删除部署
 */
export async function deleteDeployment(id: string): Promise<void> {
  if (USE_MOCK) {
    return mockDeleteDeployment(id)
  }
  return apiDelete(`/api/v1/deployments/${id}`)
}

/**
 * 启动部署
 */
export async function startDeployment(id: string): Promise<Deployment> {
  if (USE_MOCK) {
    return mockUpdateDeploymentStatus(id, 'running')
  }
  return apiPost<Deployment>(`/api/v1/deployments/${id}/start`, {})
}

/**
 * 暂停部署
 */
export async function pauseDeployment(id: string): Promise<Deployment> {
  if (USE_MOCK) {
    return mockUpdateDeploymentStatus(id, 'paused')
  }
  return apiPost<Deployment>(`/api/v1/deployments/${id}/pause`, {})
}

/**
 * 停止部署
 */
export async function stopDeployment(id: string): Promise<Deployment> {
  if (USE_MOCK) {
    return mockUpdateDeploymentStatus(id, 'stopped')
  }
  return apiPost<Deployment>(`/api/v1/deployments/${id}/stop`, {})
}

/**
 * 切换部署环境
 */
export async function switchDeploymentEnvironment(id: string, environment: DeploymentEnvironment): Promise<Deployment> {
  if (USE_MOCK) {
    return mockSwitchEnvironment(id, environment)
  }
  return apiPost<Deployment>(`/api/v1/deployments/${id}/switch-env`, { environment })
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
