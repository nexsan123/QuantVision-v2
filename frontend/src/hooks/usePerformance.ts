/**
 * 性能监控 Hooks
 * Sprint 13: T34 - 性能监控指标
 *
 * 提供:
 * - 页面性能监控
 * - 组件渲染性能
 * - API 调用性能
 * - 内存使用监控
 */

import { useState, useEffect, useCallback, useRef } from 'react'
import { logger } from '../utils/logger'

// ==================== 类型定义 ====================

interface PerformanceMetrics {
  // 页面加载指标
  pageLoad?: {
    domContentLoaded: number
    loadComplete: number
    firstPaint: number
    firstContentfulPaint: number
    largestContentfulPaint: number
  }
  // 内存使用
  memory?: {
    usedJSHeapSize: number
    totalJSHeapSize: number
    jsHeapSizeLimit: number
  }
  // 网络信息
  network?: {
    effectiveType: string
    downlink: number
    rtt: number
  }
}

interface RenderMetrics {
  componentName: string
  renderCount: number
  totalRenderTime: number
  averageRenderTime: number
  lastRenderTime: number
}

// ==================== 页面性能 Hook ====================

export function usePagePerformance(): PerformanceMetrics {
  const [metrics, setMetrics] = useState<PerformanceMetrics>({})

  useEffect(() => {
    const collectMetrics = () => {
      const perf = window.performance
      const navigation = perf.getEntriesByType('navigation')[0] as PerformanceNavigationTiming
      const paint = perf.getEntriesByType('paint')

      const newMetrics: PerformanceMetrics = {}

      // 页面加载指标
      if (navigation) {
        newMetrics.pageLoad = {
          domContentLoaded: navigation.domContentLoadedEventEnd - navigation.startTime,
          loadComplete: navigation.loadEventEnd - navigation.startTime,
          firstPaint: 0,
          firstContentfulPaint: 0,
          largestContentfulPaint: 0,
        }
      }

      // Paint 指标
      paint.forEach((entry) => {
        if (entry.name === 'first-paint' && newMetrics.pageLoad) {
          newMetrics.pageLoad.firstPaint = entry.startTime
        }
        if (entry.name === 'first-contentful-paint' && newMetrics.pageLoad) {
          newMetrics.pageLoad.firstContentfulPaint = entry.startTime
        }
      })

      // LCP
      const lcpObserver = new PerformanceObserver((list) => {
        const entries = list.getEntries()
        const lastEntry = entries[entries.length - 1]
        if (lastEntry && newMetrics.pageLoad) {
          newMetrics.pageLoad.largestContentfulPaint = lastEntry.startTime
          setMetrics((prev) => ({
            ...prev,
            pageLoad: {
              ...prev.pageLoad!,
              largestContentfulPaint: lastEntry.startTime,
            },
          }))
        }
      })

      try {
        lcpObserver.observe({ type: 'largest-contentful-paint', buffered: true })
      } catch {
        // 浏览器不支持
      }

      // 内存使用
      if ('memory' in performance) {
        const mem = (performance as any).memory
        newMetrics.memory = {
          usedJSHeapSize: mem.usedJSHeapSize,
          totalJSHeapSize: mem.totalJSHeapSize,
          jsHeapSizeLimit: mem.jsHeapSizeLimit,
        }
      }

      // 网络信息
      if ('connection' in navigator) {
        const conn = (navigator as any).connection
        newMetrics.network = {
          effectiveType: conn.effectiveType,
          downlink: conn.downlink,
          rtt: conn.rtt,
        }
      }

      setMetrics(newMetrics)

      // 记录到日志
      if (newMetrics.pageLoad) {
        logger.info('page_performance', {
          ...newMetrics.pageLoad,
          memory_used_mb: newMetrics.memory
            ? Math.round(newMetrics.memory.usedJSHeapSize / 1024 / 1024)
            : undefined,
        })
      }

      return () => {
        try {
          lcpObserver.disconnect()
        } catch {
          // ignore
        }
      }
    }

    // 等待页面完全加载
    if (document.readyState === 'complete') {
      collectMetrics()
    } else {
      window.addEventListener('load', collectMetrics)
      return () => window.removeEventListener('load', collectMetrics)
    }
  }, [])

  return metrics
}

// ==================== 组件渲染性能 Hook ====================

export function useRenderPerformance(componentName: string): RenderMetrics {
  const renderCount = useRef(0)
  const totalRenderTime = useRef(0)
  const lastRenderStart = useRef(performance.now())

  const [metrics, setMetrics] = useState<RenderMetrics>({
    componentName,
    renderCount: 0,
    totalRenderTime: 0,
    averageRenderTime: 0,
    lastRenderTime: 0,
  })

  useEffect(() => {
    const renderTime = performance.now() - lastRenderStart.current
    renderCount.current += 1
    totalRenderTime.current += renderTime

    const newMetrics: RenderMetrics = {
      componentName,
      renderCount: renderCount.current,
      totalRenderTime: totalRenderTime.current,
      averageRenderTime: totalRenderTime.current / renderCount.current,
      lastRenderTime: renderTime,
    }

    setMetrics(newMetrics)

    // 渲染过慢时记录警告
    if (renderTime > 16) { // 超过一帧 (60fps = 16.67ms)
      logger.warn('slow_render', {
        component: componentName,
        render_time_ms: renderTime.toFixed(2),
        render_count: renderCount.current,
      })
    }

    // 更新开始时间
    lastRenderStart.current = performance.now()
  })

  return metrics
}

// ==================== API 调用性能 Hook ====================

interface ApiCallMetrics {
  url: string
  method: string
  duration: number
  status: number
  success: boolean
}

interface UseApiPerformanceResult {
  calls: ApiCallMetrics[]
  averageResponseTime: number
  successRate: number
  track: (url: string, method: string, duration: number, status: number) => void
  clear: () => void
}

export function useApiPerformance(maxCalls: number = 100): UseApiPerformanceResult {
  const [calls, setCalls] = useState<ApiCallMetrics[]>([])

  const track = useCallback((
    url: string,
    method: string,
    duration: number,
    status: number,
  ) => {
    const call: ApiCallMetrics = {
      url,
      method,
      duration,
      status,
      success: status >= 200 && status < 400,
    }

    setCalls((prev) => [...prev.slice(-maxCalls + 1), call])

    // 记录慢请求
    if (duration > 3000) {
      logger.warn('slow_api_call', {
        url,
        method,
        duration_ms: duration.toFixed(2),
        status,
      })
    }
  }, [maxCalls])

  const clear = useCallback(() => {
    setCalls([])
  }, [])

  const averageResponseTime = calls.length > 0
    ? calls.reduce((sum, c) => sum + c.duration, 0) / calls.length
    : 0

  const successRate = calls.length > 0
    ? (calls.filter((c) => c.success).length / calls.length) * 100
    : 100

  return { calls, averageResponseTime, successRate, track, clear }
}

// ==================== 内存监控 Hook ====================

interface MemoryMetrics {
  usedMB: number
  totalMB: number
  limitMB: number
  usagePercent: number
}

export function useMemoryMonitor(intervalMs: number = 5000): MemoryMetrics | null {
  const [memory, setMemory] = useState<MemoryMetrics | null>(null)

  useEffect(() => {
    if (!('memory' in performance)) {
      return
    }

    const collect = () => {
      const mem = (performance as any).memory
      const metrics: MemoryMetrics = {
        usedMB: Math.round(mem.usedJSHeapSize / 1024 / 1024),
        totalMB: Math.round(mem.totalJSHeapSize / 1024 / 1024),
        limitMB: Math.round(mem.jsHeapSizeLimit / 1024 / 1024),
        usagePercent: Math.round((mem.usedJSHeapSize / mem.jsHeapSizeLimit) * 100),
      }
      setMemory(metrics)

      // 内存使用过高时警告
      if (metrics.usagePercent > 80) {
        logger.warn('high_memory_usage', {
          used_mb: metrics.usedMB,
          limit_mb: metrics.limitMB,
          usage_percent: metrics.usagePercent,
        })
      }
    }

    collect()
    const interval = setInterval(collect, intervalMs)
    return () => clearInterval(interval)
  }, [intervalMs])

  return memory
}

// ==================== 长任务监控 Hook ====================

interface LongTask {
  duration: number
  startTime: number
  name: string
}

export function useLongTaskMonitor(): LongTask[] {
  const [tasks, setTasks] = useState<LongTask[]>([])

  useEffect(() => {
    if (!('PerformanceObserver' in window)) {
      return
    }

    try {
      const observer = new PerformanceObserver((list) => {
        const entries = list.getEntries()
        const newTasks: LongTask[] = entries.map((entry) => ({
          duration: entry.duration,
          startTime: entry.startTime,
          name: entry.name,
        }))

        setTasks((prev) => [...prev.slice(-50), ...newTasks])

        // 记录长任务
        newTasks.forEach((task) => {
          if (task.duration > 50) {
            logger.warn('long_task_detected', {
              duration_ms: task.duration.toFixed(2),
              name: task.name,
            })
          }
        })
      })

      observer.observe({ type: 'longtask', buffered: true })
      return () => observer.disconnect()
    } catch {
      // 浏览器不支持
      return
    }
  }, [])

  return tasks
}

// ==================== 导出 ====================

export type {
  PerformanceMetrics,
  RenderMetrics,
  ApiCallMetrics,
  MemoryMetrics,
  LongTask,
}
