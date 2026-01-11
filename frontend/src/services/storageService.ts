/**
 * localStorage 持久化服务
 * Sprint 1 - F1: 提供类型安全的本地存储操作
 *
 * 功能:
 * - 通用存储操作 (get/set/remove)
 * - 策略数据存储
 * - 部署数据存储
 * - 回测历史存储
 * - 用户设置存储
 */

import type { Strategy } from '../types/strategy'
import type { Deployment } from '../types/deployment'

// ==================== 存储键定义 ====================

const STORAGE_PREFIX = 'qv_'  // QuantVision 前缀

export const STORAGE_KEYS = {
  STRATEGIES: `${STORAGE_PREFIX}strategies`,
  DEPLOYMENTS: `${STORAGE_PREFIX}deployments`,
  USER_SETTINGS: `${STORAGE_PREFIX}settings`,
  BACKTEST_HISTORY: `${STORAGE_PREFIX}backtest_history`,
  INTRADAY_WATCHLIST: `${STORAGE_PREFIX}intraday_watchlist`,
} as const

// ==================== 通用存储操作 ====================

/**
 * 保存数据到 localStorage
 */
export function setItem<T>(key: string, value: T): boolean {
  try {
    const serialized = JSON.stringify(value)
    localStorage.setItem(key, serialized)
    return true
  } catch (error) {
    console.error(`[StorageService] Failed to save: ${key}`, error)
    return false
  }
}

/**
 * 从 localStorage 读取数据
 */
export function getItem<T>(key: string, defaultValue: T): T {
  try {
    const item = localStorage.getItem(key)
    if (item === null) {
      return defaultValue
    }
    return JSON.parse(item) as T
  } catch (error) {
    console.error(`[StorageService] Failed to read: ${key}`, error)
    return defaultValue
  }
}

/**
 * 从 localStorage 删除数据
 */
export function removeItem(key: string): void {
  try {
    localStorage.removeItem(key)
  } catch (error) {
    console.error(`[StorageService] Failed to remove: ${key}`, error)
  }
}

/**
 * 检查 key 是否存在
 */
export function hasItem(key: string): boolean {
  return localStorage.getItem(key) !== null
}

/**
 * 清除所有 QuantVision 数据
 */
export function clearAll(): void {
  Object.values(STORAGE_KEYS).forEach(key => {
    removeItem(key)
  })
}

// ==================== 策略存储操作 ====================

export const strategyStorage = {
  /**
   * 获取所有策略
   */
  getAll(): Strategy[] {
    return getItem<Strategy[]>(STORAGE_KEYS.STRATEGIES, [])
  },

  /**
   * 保存所有策略
   */
  save(strategies: Strategy[]): boolean {
    return setItem(STORAGE_KEYS.STRATEGIES, strategies)
  },

  /**
   * 获取单个策略
   */
  getById(id: string): Strategy | null {
    const strategies = this.getAll()
    return strategies.find(s => s.id === id) || null
  },

  /**
   * 添加策略
   */
  add(strategy: Strategy): boolean {
    const strategies = this.getAll()
    strategies.push(strategy)
    return this.save(strategies)
  },

  /**
   * 更新策略
   */
  update(id: string, updates: Partial<Strategy>): Strategy | null {
    const strategies = this.getAll()
    const index = strategies.findIndex(s => s.id === id)
    if (index === -1) return null

    strategies[index] = { ...strategies[index], ...updates, updatedAt: new Date().toISOString() }
    this.save(strategies)
    return strategies[index]
  },

  /**
   * 删除策略
   */
  delete(id: string): boolean {
    const strategies = this.getAll()
    const filtered = strategies.filter(s => s.id !== id)
    if (filtered.length === strategies.length) return false
    return this.save(filtered)
  },

  /**
   * 清除所有策略
   */
  clear(): void {
    removeItem(STORAGE_KEYS.STRATEGIES)
  },

  /**
   * 检查是否已初始化
   */
  isInitialized(): boolean {
    return hasItem(STORAGE_KEYS.STRATEGIES)
  },

  /**
   * 获取最后同步时间
   */
  getLastSync(): string | null {
    return getItem<string | null>('strategies_last_sync', null)
  },

  /**
   * 设置最后同步时间
   */
  setLastSync(time: string): void {
    setItem('strategies_last_sync', time)
  },
}

// ==================== 部署存储操作 ====================

export const deploymentStorage = {
  /**
   * 获取所有部署
   */
  getAll(): Deployment[] {
    return getItem<Deployment[]>(STORAGE_KEYS.DEPLOYMENTS, [])
  },

  /**
   * 保存所有部署
   */
  save(deployments: Deployment[]): boolean {
    return setItem(STORAGE_KEYS.DEPLOYMENTS, deployments)
  },

  /**
   * 获取单个部署
   */
  getById(id: string): Deployment | null {
    const deployments = this.getAll()
    return deployments.find(d => d.deploymentId === id) || null
  },

  /**
   * 按策略ID获取部署
   */
  getByStrategyId(strategyId: string): Deployment[] {
    const deployments = this.getAll()
    return deployments.filter(d => d.strategyId === strategyId)
  },

  /**
   * 添加部署
   */
  add(deployment: Deployment): boolean {
    const deployments = this.getAll()
    deployments.push(deployment)
    return this.save(deployments)
  },

  /**
   * 更新部署
   */
  update(id: string, updates: Partial<Deployment>): Deployment | null {
    const deployments = this.getAll()
    const index = deployments.findIndex(d => d.deploymentId === id)
    if (index === -1) return null

    deployments[index] = { ...deployments[index], ...updates, updatedAt: new Date().toISOString() }
    this.save(deployments)
    return deployments[index]
  },

  /**
   * 删除部署
   */
  delete(id: string): boolean {
    const deployments = this.getAll()
    const filtered = deployments.filter(d => d.deploymentId !== id)
    if (filtered.length === deployments.length) return false
    return this.save(filtered)
  },

  /**
   * 清除所有部署
   */
  clear(): void {
    removeItem(STORAGE_KEYS.DEPLOYMENTS)
  },

  /**
   * 检查是否已初始化
   */
  isInitialized(): boolean {
    return hasItem(STORAGE_KEYS.DEPLOYMENTS)
  },
}

// ==================== 日内交易监控列表 ====================

export const intradayStorage = {
  /**
   * 获取监控列表
   */
  getWatchlist(): string[] {
    return getItem<string[]>(STORAGE_KEYS.INTRADAY_WATCHLIST, [])
  },

  /**
   * 保存监控列表
   */
  saveWatchlist(symbols: string[]): boolean {
    return setItem(STORAGE_KEYS.INTRADAY_WATCHLIST, symbols)
  },

  /**
   * 清除监控列表
   */
  clearWatchlist(): void {
    removeItem(STORAGE_KEYS.INTRADAY_WATCHLIST)
  },
}

// ==================== 用户设置 ====================

export interface UserSettings {
  theme: 'dark' | 'light'
  defaultEnvironment: 'paper' | 'live'
  defaultTimeframe: string
  notifications: boolean
}

const DEFAULT_SETTINGS: UserSettings = {
  theme: 'dark',
  defaultEnvironment: 'paper',
  defaultTimeframe: '1D',
  notifications: true,
}

export const settingsStorage = {
  get(): UserSettings {
    return getItem<UserSettings>(STORAGE_KEYS.USER_SETTINGS, DEFAULT_SETTINGS)
  },

  save(settings: Partial<UserSettings>): boolean {
    const current = this.get()
    return setItem(STORAGE_KEYS.USER_SETTINGS, { ...current, ...settings })
  },

  reset(): void {
    setItem(STORAGE_KEYS.USER_SETTINGS, DEFAULT_SETTINGS)
  },
}

// ==================== 初始化函数 ====================

/**
 * 初始化存储 (首次使用时填充默认数据)
 */
export function initializeStorage(
  defaultStrategies: Strategy[],
  defaultDeployments: Deployment[]
): void {
  // 只有在没有数据时才初始化
  if (!strategyStorage.isInitialized() || strategyStorage.getAll().length === 0) {
    strategyStorage.save(defaultStrategies)
    console.log('[StorageService] Initialized strategies with default data')
  }

  if (!deploymentStorage.isInitialized() || deploymentStorage.getAll().length === 0) {
    deploymentStorage.save(defaultDeployments)
    console.log('[StorageService] Initialized deployments with default data')
  }
}

/**
 * 获取存储统计信息
 */
export function getStorageStats(): {
  strategiesCount: number
  deploymentsCount: number
  totalSize: string
} {
  const strategies = strategyStorage.getAll()
  const deployments = deploymentStorage.getAll()

  let totalSize = 0
  Object.values(STORAGE_KEYS).forEach(key => {
    const item = localStorage.getItem(key)
    if (item) totalSize += item.length
  })

  return {
    strategiesCount: strategies.length,
    deploymentsCount: deployments.length,
    totalSize: `${(totalSize / 1024).toFixed(2)} KB`,
  }
}
