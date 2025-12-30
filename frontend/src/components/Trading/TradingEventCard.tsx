/**
 * 交易事件卡片组件
 *
 * 显示各类交易事件的可视化卡片
 */

import { memo } from 'react'
import { Tag, Tooltip } from 'antd'
import {
  ShoppingCartOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ExclamationCircleOutlined,
  WarningOutlined,
  DollarOutlined,
  RiseOutlined,
  FallOutlined,
  InfoCircleOutlined,
  StockOutlined,
} from '@ant-design/icons'
import { TradingEvent, OrderEvent, PositionEvent, PriceUpdateEvent, RiskAlertEvent, SystemMessageEvent } from '@/types/trading'
import { formatDistanceToNow } from 'date-fns'
import { zhCN } from 'date-fns/locale'

interface TradingEventCardProps {
  event: TradingEvent
  compact?: boolean
}

// 事件类型配置
const eventConfig: Record<string, { icon: React.ReactNode; color: string; label: string }> = {
  order_submitted: { icon: <ShoppingCartOutlined />, color: 'blue', label: '订单提交' },
  order_filled: { icon: <CheckCircleOutlined />, color: 'green', label: '订单成交' },
  order_partial_fill: { icon: <CheckCircleOutlined />, color: 'cyan', label: '部分成交' },
  order_cancelled: { icon: <CloseCircleOutlined />, color: 'default', label: '订单取消' },
  order_rejected: { icon: <CloseCircleOutlined />, color: 'red', label: '订单拒绝' },
  position_opened: { icon: <RiseOutlined />, color: 'green', label: '开仓' },
  position_closed: { icon: <FallOutlined />, color: 'orange', label: '平仓' },
  position_updated: { icon: <StockOutlined />, color: 'blue', label: '持仓更新' },
  price_update: { icon: <DollarOutlined />, color: 'purple', label: '价格更新' },
  pnl_update: { icon: <DollarOutlined />, color: 'gold', label: '盈亏更新' },
  risk_alert: { icon: <WarningOutlined />, color: 'red', label: '风险警报' },
  system_message: { icon: <InfoCircleOutlined />, color: 'default', label: '系统消息' },
}

function TradingEventCardComponent({ event, compact = false }: TradingEventCardProps) {
  const config = eventConfig[event.type] || { icon: <InfoCircleOutlined />, color: 'default', label: '未知事件' }

  const timeAgo = formatDistanceToNow(new Date(event.timestamp), {
    addSuffix: true,
    locale: zhCN,
  })

  if (compact) {
    return (
      <div className="flex items-center gap-2 py-1 px-2 hover:bg-dark-hover rounded transition-colors">
        <span className="text-base" style={{ color: getTagColor(config.color) }}>
          {config.icon}
        </span>
        <span className="text-sm text-gray-300 truncate flex-1">
          {getEventSummary(event)}
        </span>
        <span className="text-xs text-gray-500">{timeAgo}</span>
      </div>
    )
  }

  return (
    <div className="bg-dark-card border border-dark-border rounded-lg p-3 hover:border-gray-600 transition-colors">
      {/* 头部 */}
      <div className="flex items-center justify-between mb-2">
        <Tag color={config.color} icon={config.icon}>
          {config.label}
        </Tag>
        <Tooltip title={new Date(event.timestamp).toLocaleString('zh-CN')}>
          <span className="text-xs text-gray-500">{timeAgo}</span>
        </Tooltip>
      </div>

      {/* 内容 */}
      <div className="text-sm text-gray-200">
        {renderEventContent(event)}
      </div>
    </div>
  )
}

// 获取事件摘要
function getEventSummary(event: TradingEvent): string {
  switch (event.type) {
    case 'order_submitted':
    case 'order_filled':
    case 'order_partial_fill':
    case 'order_cancelled':
    case 'order_rejected': {
      const e = event as OrderEvent
      return `${e.side === 'buy' ? '买入' : '卖出'} ${e.symbol} ${e.quantity}股`
    }
    case 'position_opened':
    case 'position_closed':
    case 'position_updated': {
      const e = event as PositionEvent
      return `${e.symbol} ${e.quantity}股 @ $${e.currentPrice.toFixed(2)}`
    }
    case 'price_update': {
      const e = event as PriceUpdateEvent
      const direction = e.change >= 0 ? '+' : ''
      return `${e.symbol} $${e.price.toFixed(2)} (${direction}${e.changePercent.toFixed(2)}%)`
    }
    case 'risk_alert': {
      const e = event as RiskAlertEvent
      return e.title
    }
    case 'system_message': {
      const e = event as SystemMessageEvent
      return e.title
    }
    default:
      return '交易事件'
  }
}

// 渲染事件内容
function renderEventContent(event: TradingEvent): React.ReactNode {
  switch (event.type) {
    case 'order_submitted':
    case 'order_filled':
    case 'order_partial_fill':
    case 'order_cancelled':
    case 'order_rejected':
      return <OrderEventContent event={event as OrderEvent} />

    case 'position_opened':
    case 'position_closed':
    case 'position_updated':
      return <PositionEventContent event={event as PositionEvent} />

    case 'price_update':
      return <PriceEventContent event={event as PriceUpdateEvent} />

    case 'risk_alert':
      return <RiskAlertContent event={event as RiskAlertEvent} />

    case 'system_message':
      return <SystemMessageContent event={event as SystemMessageEvent} />

    default:
      return <div>未知事件类型</div>
  }
}

// 订单事件内容
function OrderEventContent({ event }: { event: OrderEvent }) {
  const sideClass = event.side === 'buy' ? 'text-green-400' : 'text-red-400'

  return (
    <div className="space-y-1">
      <div className="flex items-center gap-2">
        <span className={`font-medium ${sideClass}`}>
          {event.side === 'buy' ? '买入' : '卖出'}
        </span>
        <span className="font-bold text-gray-100">{event.symbol}</span>
      </div>
      <div className="grid grid-cols-2 gap-x-4 text-xs text-gray-400">
        <div>数量: {event.quantity}</div>
        <div>类型: {getOrderTypeLabel(event.orderType)}</div>
        {event.price && <div>价格: ${event.price.toFixed(2)}</div>}
        {event.filledQuantity && (
          <div>已成交: {event.filledQuantity} @ ${event.filledPrice?.toFixed(2)}</div>
        )}
      </div>
      {event.message && (
        <div className="text-xs text-gray-500 mt-1">{event.message}</div>
      )}
    </div>
  )
}

// 持仓事件内容
function PositionEventContent({ event }: { event: PositionEvent }) {
  const pnlClass = event.unrealizedPnl >= 0 ? 'text-green-400' : 'text-red-400'
  const pnlSign = event.unrealizedPnl >= 0 ? '+' : ''

  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between">
        <span className="font-bold text-gray-100">{event.symbol}</span>
        <span className={pnlClass}>
          {pnlSign}${event.unrealizedPnl.toFixed(2)}
        </span>
      </div>
      <div className="grid grid-cols-2 gap-x-4 text-xs text-gray-400">
        <div>持仓: {event.quantity}股</div>
        <div>均价: ${event.avgPrice.toFixed(2)}</div>
        <div>现价: ${event.currentPrice.toFixed(2)}</div>
        <div>方向: {event.side === 'buy' ? '多头' : '空头'}</div>
      </div>
    </div>
  )
}

// 价格事件内容
function PriceEventContent({ event }: { event: PriceUpdateEvent }) {
  const isUp = event.change >= 0
  const changeClass = isUp ? 'text-green-400' : 'text-red-400'
  const ChangeIcon = isUp ? RiseOutlined : FallOutlined

  return (
    <div className="flex items-center justify-between">
      <div>
        <span className="font-bold text-gray-100">{event.symbol}</span>
        <span className="text-lg ml-2">${event.price.toFixed(2)}</span>
      </div>
      <div className={`flex items-center gap-1 ${changeClass}`}>
        <ChangeIcon />
        <span>{isUp ? '+' : ''}{event.change.toFixed(2)}</span>
        <span>({isUp ? '+' : ''}{event.changePercent.toFixed(2)}%)</span>
      </div>
    </div>
  )
}

// 风险警报内容
function RiskAlertContent({ event }: { event: RiskAlertEvent }) {
  const levelConfig = {
    info: { color: 'text-blue-400', bg: 'bg-blue-900/20' },
    warning: { color: 'text-yellow-400', bg: 'bg-yellow-900/20' },
    critical: { color: 'text-red-400', bg: 'bg-red-900/20' },
  }

  const config = levelConfig[event.level]

  return (
    <div className={`p-2 rounded ${config.bg}`}>
      <div className={`font-medium ${config.color}`}>
        <ExclamationCircleOutlined className="mr-1" />
        {event.title}
      </div>
      <div className="text-xs text-gray-400 mt-1">{event.message}</div>
      {event.metric && (
        <div className="text-xs text-gray-500 mt-1">
          {event.metric}: {event.currentValue} (阈值: {event.threshold})
        </div>
      )}
    </div>
  )
}

// 系统消息内容
function SystemMessageContent({ event }: { event: SystemMessageEvent }) {
  const levelConfig = {
    info: 'text-blue-400',
    warning: 'text-yellow-400',
    error: 'text-red-400',
    success: 'text-green-400',
  }

  return (
    <div>
      <div className={`font-medium ${levelConfig[event.level]}`}>{event.title}</div>
      <div className="text-xs text-gray-400 mt-1">{event.message}</div>
    </div>
  )
}

// 获取订单类型标签
function getOrderTypeLabel(type: string): string {
  const labels: Record<string, string> = {
    market: '市价',
    limit: '限价',
    stop: '止损',
    stop_limit: '止损限价',
  }
  return labels[type] || type
}

// 获取 Tag 颜色
function getTagColor(color: string): string {
  const colors: Record<string, string> = {
    blue: '#1890ff',
    green: '#52c41a',
    red: '#ff4d4f',
    orange: '#fa8c16',
    cyan: '#13c2c2',
    purple: '#722ed1',
    gold: '#faad14',
    default: '#8c8c8c',
  }
  return colors[color] || colors.default
}

export const TradingEventCard = memo(TradingEventCardComponent)
export default TradingEventCard
