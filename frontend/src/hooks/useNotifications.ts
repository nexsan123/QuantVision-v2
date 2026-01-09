/**
 * 通知管理 Hooks
 * Sprint 13: T35 - 告警通知系统
 *
 * 提供:
 * - WebSocket 实时通知
 * - 通知历史
 * - 通知规则管理
 */

import { useState, useEffect, useCallback, useRef } from 'react'
import { notification as antdNotification } from 'antd'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000'

// ==================== 类型定义 ====================

type NotificationPriority = 'low' | 'medium' | 'high' | 'critical'
type NotificationCategory = 'trade' | 'risk' | 'system' | 'strategy' | 'market'
type NotificationChannel = 'websocket' | 'email' | 'webhook' | 'sms'

interface NotificationData {
  title: string
  message: string
  category: NotificationCategory
  priority: NotificationPriority
  data?: Record<string, unknown>
  action_url?: string
  timestamp: string
}

interface NotificationRecord {
  id: string
  title: string
  message: string
  category: NotificationCategory
  priority: NotificationPriority
  channels: NotificationChannel[]
  sent_at: string
  success: boolean
  error?: string
}

interface NotificationRule {
  id: string
  name: string
  enabled: boolean
  category: NotificationCategory
  min_priority: NotificationPriority
  channels: NotificationChannel[]
  rate_limit: number
  quiet_hours?: [number, number]
}

interface NotificationStats {
  total: number
  successful: number
  failed: number
  success_rate: number
  by_category: Record<string, number>
  by_priority: Record<string, number>
  active_rules: number
  ws_clients: number
}

// ==================== 实时通知 Hook ====================

interface UseRealtimeNotificationsOptions {
  enabled?: boolean
  showToast?: boolean
  onNotification?: (notification: NotificationData) => void
}

interface UseRealtimeNotificationsResult {
  notifications: NotificationData[]
  connected: boolean
  unreadCount: number
  markAllRead: () => void
  clear: () => void
}

export function useRealtimeNotifications(
  options: UseRealtimeNotificationsOptions = {}
): UseRealtimeNotificationsResult {
  const { enabled = true, showToast = true, onNotification } = options

  const [notifications, setNotifications] = useState<NotificationData[]>([])
  const [connected, setConnected] = useState(false)
  const [unreadCount, setUnreadCount] = useState(0)
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout>>()

  const connect = useCallback(() => {
    if (!enabled || wsRef.current?.readyState === WebSocket.OPEN) {
      return
    }

    try {
      const ws = new WebSocket(`${WS_URL}/ws/notifications`)

      ws.onopen = () => {
        setConnected(true)
        console.log('[Notifications] WebSocket connected')
      }

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data)

          if (message.type === 'notification') {
            const notification = message.data as NotificationData

            setNotifications((prev) => [notification, ...prev].slice(0, 100))
            setUnreadCount((prev) => prev + 1)

            // 调用回调
            onNotification?.(notification)

            // 显示 Toast
            if (showToast) {
              showNotificationToast(notification)
            }
          }
        } catch (err) {
          console.error('[Notifications] Parse error:', err)
        }
      }

      ws.onclose = () => {
        setConnected(false)
        console.log('[Notifications] WebSocket closed')

        // 重连
        reconnectTimeoutRef.current = setTimeout(connect, 5000)
      }

      ws.onerror = (err) => {
        console.error('[Notifications] WebSocket error:', err)
      }

      wsRef.current = ws
    } catch (err) {
      console.error('[Notifications] Connection failed:', err)
    }
  }, [enabled, showToast, onNotification])

  useEffect(() => {
    connect()

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [connect])

  const markAllRead = useCallback(() => {
    setUnreadCount(0)
  }, [])

  const clear = useCallback(() => {
    setNotifications([])
    setUnreadCount(0)
  }, [])

  return { notifications, connected, unreadCount, markAllRead, clear }
}

// ==================== 显示 Toast 通知 ====================

function showNotificationToast(notification: NotificationData) {
  const type = notification.priority === 'critical' ? 'error' :
               notification.priority === 'high' ? 'warning' :
               'info'

  antdNotification[type]({
    message: notification.title,
    description: notification.message,
    placement: 'topRight',
    duration: notification.priority === 'critical' ? 0 : 5,
  })
}

// ==================== 通知历史 Hook ====================

interface UseNotificationHistoryOptions {
  category?: NotificationCategory
  limit?: number
  pollInterval?: number
}

interface UseNotificationHistoryResult {
  records: NotificationRecord[]
  loading: boolean
  error: Error | null
  refetch: () => Promise<void>
}

export function useNotificationHistory(
  options: UseNotificationHistoryOptions = {}
): UseNotificationHistoryResult {
  const { category, limit = 50, pollInterval = 0 } = options

  const [records, setRecords] = useState<NotificationRecord[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  const fetchHistory = useCallback(async () => {
    try {
      const params = new URLSearchParams()
      if (category) params.set('category', category)
      params.set('limit', String(limit))

      const response = await fetch(
        `${API_BASE}/api/v1/notifications/history?${params}`
      )

      if (!response.ok) throw new Error(`HTTP ${response.status}`)

      const data = await response.json()
      setRecords(data.records)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Unknown error'))
    } finally {
      setLoading(false)
    }
  }, [category, limit])

  useEffect(() => {
    fetchHistory()

    if (pollInterval > 0) {
      const interval = setInterval(fetchHistory, pollInterval)
      return () => clearInterval(interval)
    }
  }, [fetchHistory, pollInterval])

  return { records, loading, error, refetch: fetchHistory }
}

// ==================== 通知规则 Hook ====================

interface UseNotificationRulesResult {
  rules: NotificationRule[]
  loading: boolean
  error: Error | null
  toggleRule: (ruleId: string) => Promise<void>
  updateRule: (ruleId: string, updates: Partial<NotificationRule>) => Promise<void>
  refetch: () => Promise<void>
}

export function useNotificationRules(): UseNotificationRulesResult {
  const [rules, setRules] = useState<NotificationRule[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  const fetchRules = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/api/v1/notifications/rules`)

      if (!response.ok) throw new Error(`HTTP ${response.status}`)

      const data = await response.json()
      setRules(data.rules)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Unknown error'))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchRules()
  }, [fetchRules])

  const toggleRule = useCallback(async (ruleId: string) => {
    try {
      const response = await fetch(
        `${API_BASE}/api/v1/notifications/rules/${ruleId}/toggle`,
        { method: 'POST' }
      )

      if (!response.ok) throw new Error(`HTTP ${response.status}`)

      const data = await response.json()

      setRules((prev) =>
        prev.map((rule) =>
          rule.id === ruleId ? { ...rule, enabled: data.enabled } : rule
        )
      )
    } catch (err) {
      console.error('Toggle rule failed:', err)
    }
  }, [])

  const updateRule = useCallback(async (
    ruleId: string,
    updates: Partial<NotificationRule>
  ) => {
    try {
      const response = await fetch(
        `${API_BASE}/api/v1/notifications/rules/${ruleId}`,
        {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(updates),
        }
      )

      if (!response.ok) throw new Error(`HTTP ${response.status}`)

      await fetchRules()
    } catch (err) {
      console.error('Update rule failed:', err)
    }
  }, [fetchRules])

  return { rules, loading, error, toggleRule, updateRule, refetch: fetchRules }
}

// ==================== 通知统计 Hook ====================

export function useNotificationStats(): {
  stats: NotificationStats | null
  loading: boolean
} {
  const [stats, setStats] = useState<NotificationStats | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const response = await fetch(`${API_BASE}/api/v1/notifications/stats`)
        if (response.ok) {
          const data = await response.json()
          setStats(data)
        }
      } catch {
        // ignore
      } finally {
        setLoading(false)
      }
    }

    fetchStats()
    const interval = setInterval(fetchStats, 30000)
    return () => clearInterval(interval)
  }, [])

  return { stats, loading }
}

// ==================== 导出 ====================

export type {
  NotificationData,
  NotificationRecord,
  NotificationRule,
  NotificationStats,
  NotificationPriority,
  NotificationCategory,
  NotificationChannel,
}
