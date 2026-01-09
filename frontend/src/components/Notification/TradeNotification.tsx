/**
 * 成交通知组件
 * Sprint 9: T16 - 实时成交通知
 *
 * 使用 Alpaca WebSocket 接收成交通知并显示
 */
import { useEffect, useCallback, useRef } from 'react'
import { notification, Button } from 'antd'
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  ExclamationCircleOutlined,
  InfoCircleOutlined,
} from '@ant-design/icons'
import { alpacaWebSocket, type TradeUpdate, type TradeUpdateEvent } from '../../services/alpacaWebSocket'
import { alpacaAuth } from '../../services/alpacaAuth'

// 通知配置
interface NotificationConfig {
  enabled: boolean
  sound: boolean
  showFills: boolean
  showCancels: boolean
  showRejects: boolean
  duration: number // 秒，0 表示不自动关闭
}

const DEFAULT_CONFIG: NotificationConfig = {
  enabled: true,
  sound: true,
  showFills: true,
  showCancels: true,
  showRejects: true,
  duration: 5,
}

// 事件类型配置
const EVENT_CONFIG: Record<TradeUpdateEvent, {
  title: string
  type: 'success' | 'error' | 'warning' | 'info'
  icon: React.ReactNode
  show: keyof NotificationConfig
}> = {
  fill: { title: '订单成交', type: 'success', icon: <CheckCircleOutlined />, show: 'showFills' },
  partial_fill: { title: '部分成交', type: 'info', icon: <InfoCircleOutlined />, show: 'showFills' },
  new: { title: '订单已提交', type: 'info', icon: <InfoCircleOutlined />, show: 'showFills' },
  canceled: { title: '订单已取消', type: 'warning', icon: <ExclamationCircleOutlined />, show: 'showCancels' },
  expired: { title: '订单已过期', type: 'warning', icon: <ExclamationCircleOutlined />, show: 'showCancels' },
  done_for_day: { title: '当日结束', type: 'info', icon: <InfoCircleOutlined />, show: 'showCancels' },
  replaced: { title: '订单已替换', type: 'info', icon: <InfoCircleOutlined />, show: 'showCancels' },
  rejected: { title: '订单被拒绝', type: 'error', icon: <CloseCircleOutlined />, show: 'showRejects' },
  pending_new: { title: '订单待确认', type: 'info', icon: <InfoCircleOutlined />, show: 'showFills' },
  stopped: { title: '订单已停止', type: 'warning', icon: <ExclamationCircleOutlined />, show: 'showRejects' },
  pending_cancel: { title: '取消中', type: 'info', icon: <InfoCircleOutlined />, show: 'showCancels' },
  pending_replace: { title: '替换中', type: 'info', icon: <InfoCircleOutlined />, show: 'showCancels' },
  calculated: { title: '订单已计算', type: 'info', icon: <InfoCircleOutlined />, show: 'showFills' },
  suspended: { title: '订单已暂停', type: 'warning', icon: <ExclamationCircleOutlined />, show: 'showRejects' },
  order_replace_rejected: { title: '替换被拒绝', type: 'error', icon: <CloseCircleOutlined />, show: 'showRejects' },
  order_cancel_rejected: { title: '取消被拒绝', type: 'error', icon: <CloseCircleOutlined />, show: 'showRejects' },
}

// 音效
const playSound = (type: 'success' | 'error' | 'warning' | 'info') => {
  // 可以在这里添加音效播放逻辑
  // 例如使用 Web Audio API 或 Audio 元素
  if (type === 'success') {
    // 成交音效
  } else if (type === 'error') {
    // 错误音效
  }
}

interface TradeNotificationProviderProps {
  config?: Partial<NotificationConfig>
  onTradeUpdate?: (update: TradeUpdate) => void
  children?: React.ReactNode
}

/**
 * 成交通知 Provider
 */
export function TradeNotificationProvider({
  config: userConfig,
  onTradeUpdate,
  children,
}: TradeNotificationProviderProps) {
  const config = { ...DEFAULT_CONFIG, ...userConfig }
  const connectedRef = useRef(false)

  const handleTradeUpdate = useCallback((update: TradeUpdate) => {
    // 调用外部回调
    onTradeUpdate?.(update)

    // 检查是否启用通知
    if (!config.enabled) return

    // 获取事件配置
    const eventConfig = EVENT_CONFIG[update.event]
    if (!eventConfig) return

    // 检查是否显示此类型的通知
    const showKey = eventConfig.show
    if (!config[showKey]) return

    // 构建通知内容
    const { order } = update
    const side = order.side === 'buy' ? '买入' : '卖出'
    const qty = parseFloat(order.qty)
    const filledQty = parseFloat(order.filled_qty)
    const avgPrice = order.filled_avg_price ? parseFloat(order.filled_avg_price) : null

    let description = `${side} ${order.symbol} ${qty}股`

    if (update.event === 'fill' || update.event === 'partial_fill') {
      if (avgPrice) {
        description += ` @ $${avgPrice.toFixed(2)}`
      }
      if (update.event === 'partial_fill') {
        description += ` (${filledQty}/${qty})`
      }
    }

    // 播放音效
    if (config.sound) {
      playSound(eventConfig.type)
    }

    // 显示通知
    notification[eventConfig.type]({
      message: eventConfig.title,
      description,
      icon: eventConfig.icon,
      duration: config.duration,
      placement: 'topRight',
      className: 'trade-notification',
    })
  }, [config, onTradeUpdate])

  // 连接 WebSocket 并订阅
  useEffect(() => {
    if (!alpacaAuth.isAuthenticated()) {
      return
    }

    const connect = async () => {
      if (connectedRef.current) return

      try {
        await alpacaWebSocket.connect()
        connectedRef.current = true
      } catch (error) {
        console.error('[TradeNotification] Failed to connect:', error)
      }
    }

    connect()

    const unsubscribe = alpacaWebSocket.subscribeTradeUpdates(handleTradeUpdate)

    return () => {
      unsubscribe()
    }
  }, [handleTradeUpdate])

  return <>{children}</>
}

/**
 * 成交通知 Hook
 */
export function useTradeNotifications(
  config?: Partial<NotificationConfig>,
  onTradeUpdate?: (update: TradeUpdate) => void
) {
  const mergedConfig = { ...DEFAULT_CONFIG, ...config }

  useEffect(() => {
    if (!alpacaAuth.isAuthenticated()) {
      return
    }

    const handleUpdate = (update: TradeUpdate) => {
      onTradeUpdate?.(update)

      if (!mergedConfig.enabled) return

      const eventConfig = EVENT_CONFIG[update.event]
      if (!eventConfig) return

      const showKey = eventConfig.show
      if (!mergedConfig[showKey]) return

      const { order } = update
      const side = order.side === 'buy' ? '买入' : '卖出'
      const qty = parseFloat(order.qty)
      const avgPrice = order.filled_avg_price ? parseFloat(order.filled_avg_price) : null

      let description = `${side} ${order.symbol} ${qty}股`
      if (avgPrice) {
        description += ` @ $${avgPrice.toFixed(2)}`
      }

      notification[eventConfig.type]({
        message: eventConfig.title,
        description,
        icon: eventConfig.icon,
        duration: mergedConfig.duration,
        placement: 'topRight',
      })
    }

    alpacaWebSocket.connect().catch(console.error)
    const unsubscribe = alpacaWebSocket.subscribeTradeUpdates(handleUpdate)

    return () => {
      unsubscribe()
    }
  }, [mergedConfig, onTradeUpdate])
}

/**
 * 手动显示成交通知
 */
export function showTradeNotification(
  type: 'success' | 'error' | 'warning' | 'info',
  title: string,
  description: string,
  options?: {
    duration?: number
    onClose?: () => void
  }
) {
  notification[type]({
    message: title,
    description,
    duration: options?.duration ?? 5,
    placement: 'topRight',
    onClose: options?.onClose,
  })
}

/**
 * 成交通知测试按钮 (开发用)
 */
export function TradeNotificationTest() {
  const testNotifications = () => {
    showTradeNotification('success', '订单成交', '买入 NVDA 100股 @ $520.50')
    setTimeout(() => {
      showTradeNotification('info', '部分成交', '买入 AAPL 50/100股 @ $178.25')
    }, 1000)
    setTimeout(() => {
      showTradeNotification('warning', '订单已取消', '卖出 TSLA 30股')
    }, 2000)
    setTimeout(() => {
      showTradeNotification('error', '订单被拒绝', '买入 GME 1000股 - 购买力不足')
    }, 3000)
  }

  return (
    <Button onClick={testNotifications} size="small">
      测试成交通知
    </Button>
  )
}

export default TradeNotificationProvider
