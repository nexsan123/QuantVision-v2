/**
 * 健康检查 Hooks
 * Sprint 12: T31 - 健康检查端点
 *
 * 提供系统健康状态监控
 */

import { useState, useEffect, useCallback } from 'react'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

// ==================== 类型定义 ====================

interface ComponentHealth {
  status: 'healthy' | 'unhealthy' | 'unconfigured' | 'degraded'
  latency_ms?: number
  error?: string
  message?: string
  [key: string]: unknown
}

interface SystemMetrics {
  cpu_percent: number
  memory: {
    total_gb: number
    used_gb: number
    percent: number
  }
  disk: {
    total_gb: number
    used_gb: number
    percent: number
  }
}

interface DetailedHealthResponse {
  status: 'healthy' | 'unhealthy' | 'degraded'
  version: string
  environment: string
  timestamp: string
  uptime_seconds: number
  uptime_human: string
  python_version: string
  components: {
    database: ComponentHealth
    redis: ComponentHealth
    alpaca: ComponentHealth
    s3_storage: ComponentHealth
    system: SystemMetrics
  }
}

interface BasicHealthResponse {
  status: 'healthy' | 'unhealthy' | 'degraded'
  version: string
  timestamp: string
  components: Record<string, string>
}

interface HealthMetrics {
  app_uptime_seconds: number
  cpu_usage_percent: number
  memory_usage_percent: number
  disk_usage_percent: number
}

// ==================== 基本健康检查 Hook ====================

interface UseBasicHealthOptions {
  pollInterval?: number // 轮询间隔 (毫秒)
  enabled?: boolean
}

interface UseBasicHealthResult {
  health: BasicHealthResponse | null
  loading: boolean
  error: Error | null
  refetch: () => Promise<void>
}

/**
 * 基本健康检查
 */
export function useBasicHealth(options: UseBasicHealthOptions = {}): UseBasicHealthResult {
  const { pollInterval = 0, enabled = true } = options

  const [health, setHealth] = useState<BasicHealthResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  const fetchHealth = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/api/v1/health`)

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }

      const data = await response.json()
      setHealth(data)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Unknown error'))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    if (!enabled) return

    fetchHealth()

    if (pollInterval > 0) {
      const interval = setInterval(fetchHealth, pollInterval)
      return () => clearInterval(interval)
    }
  }, [enabled, pollInterval, fetchHealth])

  return { health, loading, error, refetch: fetchHealth }
}

// ==================== 详细健康检查 Hook ====================

interface UseDetailedHealthOptions {
  pollInterval?: number
  enabled?: boolean
}

interface UseDetailedHealthResult {
  health: DetailedHealthResponse | null
  loading: boolean
  error: Error | null
  refetch: () => Promise<void>
  isHealthy: boolean
  isDegraded: boolean
}

/**
 * 详细健康检查
 */
export function useDetailedHealth(options: UseDetailedHealthOptions = {}): UseDetailedHealthResult {
  const { pollInterval = 0, enabled = true } = options

  const [health, setHealth] = useState<DetailedHealthResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  const fetchHealth = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/api/v1/health/detailed`)

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }

      const data = await response.json()
      setHealth(data)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Unknown error'))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    if (!enabled) return

    fetchHealth()

    if (pollInterval > 0) {
      const interval = setInterval(fetchHealth, pollInterval)
      return () => clearInterval(interval)
    }
  }, [enabled, pollInterval, fetchHealth])

  const isHealthy = health?.status === 'healthy'
  const isDegraded = health?.status === 'degraded'

  return { health, loading, error, refetch: fetchHealth, isHealthy, isDegraded }
}

// ==================== 系统指标 Hook ====================

interface UseHealthMetricsOptions {
  pollInterval?: number
  enabled?: boolean
}

interface UseHealthMetricsResult {
  metrics: HealthMetrics | null
  loading: boolean
  error: Error | null
}

/**
 * 系统指标监控
 */
export function useHealthMetrics(options: UseHealthMetricsOptions = {}): UseHealthMetricsResult {
  const { pollInterval = 5000, enabled = true } = options

  const [metrics, setMetrics] = useState<HealthMetrics | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  useEffect(() => {
    if (!enabled) return

    const fetchMetrics = async () => {
      try {
        const response = await fetch(`${API_BASE}/api/v1/health/metrics`)

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`)
        }

        const data = await response.json()
        setMetrics(data)
        setError(null)
      } catch (err) {
        setError(err instanceof Error ? err : new Error('Unknown error'))
      } finally {
        setLoading(false)
      }
    }

    fetchMetrics()

    if (pollInterval > 0) {
      const interval = setInterval(fetchMetrics, pollInterval)
      return () => clearInterval(interval)
    }
  }, [enabled, pollInterval])

  return { metrics, loading, error }
}

// ==================== 连接检查 Hook ====================

interface UseConnectionCheckResult {
  isConnected: boolean
  checking: boolean
  lastCheck: Date | null
  check: () => Promise<boolean>
}

/**
 * 后端连接检查
 */
export function useConnectionCheck(): UseConnectionCheckResult {
  const [isConnected, setIsConnected] = useState(false)
  const [checking, setChecking] = useState(true)
  const [lastCheck, setLastCheck] = useState<Date | null>(null)

  const check = useCallback(async (): Promise<boolean> => {
    setChecking(true)

    try {
      const response = await fetch(`${API_BASE}/api/v1/health/live`, {
        method: 'GET',
        signal: AbortSignal.timeout(5000),
      })

      const connected = response.ok
      setIsConnected(connected)
      setLastCheck(new Date())
      return connected
    } catch {
      setIsConnected(false)
      setLastCheck(new Date())
      return false
    } finally {
      setChecking(false)
    }
  }, [])

  useEffect(() => {
    check()

    // 每 30 秒检查一次连接
    const interval = setInterval(check, 30000)
    return () => clearInterval(interval)
  }, [check])

  return { isConnected, checking, lastCheck, check }
}

// ==================== 导出 ====================

export type {
  ComponentHealth,
  SystemMetrics,
  DetailedHealthResponse,
  BasicHealthResponse,
  HealthMetrics,
}
