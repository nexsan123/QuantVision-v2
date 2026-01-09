/**
 * 订单管理面板
 * Sprint 3: 实时订单监控
 * Sprint 9 - T15: 集成 Alpaca 实时数据
 */
import { useState, useMemo } from 'react'
import { Tag, Button, Tooltip, Empty, Spin, message } from 'antd'
import { CloseOutlined, SyncOutlined } from '@ant-design/icons'
import { useOrders } from '../../hooks/useOrders'
import type { Order as AlpacaOrder, OrderStatus as AlpacaOrderStatus } from '../../services/alpacaTrading'

interface OrderPanelProps {
  deploymentId: string
}

type DisplayOrderStatus = 'pending' | 'partial' | 'filled' | 'cancelled' | 'rejected'
type OrderSide = 'BUY' | 'SELL'

interface DisplayOrder {
  id: string
  symbol: string
  side: OrderSide
  qty: number
  filledQty: number
  price: number
  avgPrice?: number
  status: DisplayOrderStatus
  time: string
  type: 'market' | 'limit' | 'stop' | 'stop_limit'
}

// 订单状态配置
const STATUS_CONFIG: Record<DisplayOrderStatus, { label: string; color: string }> = {
  pending: { label: '待成交', color: 'orange' },
  partial: { label: '部分成交', color: 'blue' },
  filled: { label: '已成交', color: 'green' },
  cancelled: { label: '已取消', color: 'default' },
  rejected: { label: '已拒绝', color: 'red' },
}

// 状态映射
function mapOrderStatus(status: AlpacaOrderStatus): DisplayOrderStatus {
  switch (status) {
    case 'new':
    case 'pending_new':
    case 'accepted':
    case 'accepted_without_block':
      return 'pending'
    case 'partially_filled':
      return 'partial'
    case 'filled':
      return 'filled'
    case 'canceled':
    case 'expired':
    case 'done_for_day':
    case 'replaced':
    case 'pending_cancel':
    case 'pending_replace':
      return 'cancelled'
    case 'rejected':
    case 'stopped':
    case 'suspended':
      return 'rejected'
    default:
      return 'pending'
  }
}

// 转换 Alpaca 订单到显示格式
function transformOrder(order: AlpacaOrder): DisplayOrder {
  const qty = parseFloat(order.qty)
  const filledQty = parseFloat(order.filled_qty)
  const avgPrice = order.filled_avg_price ? parseFloat(order.filled_avg_price) : undefined
  const limitPrice = order.limit_price ? parseFloat(order.limit_price) : 0
  const stopPrice = order.stop_price ? parseFloat(order.stop_price) : 0

  return {
    id: order.id,
    symbol: order.symbol,
    side: order.side === 'buy' ? 'BUY' : 'SELL',
    qty,
    filledQty,
    price: limitPrice || stopPrice,
    avgPrice,
    status: mapOrderStatus(order.status),
    time: new Date(order.created_at).toLocaleTimeString('en-US', { hour12: false }),
    type: order.type as 'market' | 'limit' | 'stop' | 'stop_limit',
  }
}

export default function OrderPanel({ deploymentId: _deploymentId }: OrderPanelProps) {
  const { orders: alpacaOrders, openOrders, loading, error, refresh, cancelOrder, cancelAllOrders } = useOrders()
  const [filter, setFilter] = useState<'all' | 'active' | 'completed'>('all')
  const [cancelling, setCancelling] = useState<string | null>(null)

  // 转换订单数据
  const orders = useMemo(() => {
    return alpacaOrders.map(transformOrder)
  }, [alpacaOrders])

  const handleCancelOrder = async (orderId: string) => {
    setCancelling(orderId)
    try {
      await cancelOrder(orderId)
      message.success('订单已取消')
    } catch (err) {
      message.error(`取消失败: ${(err as Error).message}`)
    } finally {
      setCancelling(null)
    }
  }

  const handleCancelAll = async () => {
    if (openOrders.length === 0) return
    try {
      await cancelAllOrders()
      message.success('已取消所有订单')
    } catch (err) {
      message.error(`取消失败: ${(err as Error).message}`)
    }
  }

  // 筛选订单
  const filteredOrders = orders.filter(order => {
    if (filter === 'all') return true
    if (filter === 'active') return order.status === 'pending' || order.status === 'partial'
    return order.status === 'filled' || order.status === 'cancelled' || order.status === 'rejected'
  })

  const activeCount = openOrders.length

  // 加载中
  if (loading && orders.length === 0) {
    return (
      <div className="h-full flex items-center justify-center">
        <Spin size="small" />
      </div>
    )
  }

  // 错误
  if (error && orders.length === 0) {
    return (
      <div className="h-full flex flex-col items-center justify-center text-gray-500">
        <div className="text-sm mb-2">加载失败</div>
        <Button size="small" onClick={refresh}>重试</Button>
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col">
      {/* 标题栏 */}
      <div className="px-3 py-2 border-b border-gray-800 flex items-center justify-between">
        <span className="text-sm font-medium text-white">订单管理</span>
        <div className="flex items-center gap-2">
          {activeCount > 0 && (
            <Tooltip title="取消所有待成交订单">
              <button
                onClick={handleCancelAll}
                className="text-xs px-1.5 py-0.5 rounded bg-orange-900/50 text-orange-400 hover:bg-orange-800/50 transition-colors"
              >
                {activeCount} 待成交
              </button>
            </Tooltip>
          )}
          <button
            onClick={refresh}
            className="text-gray-400 hover:text-white transition-colors"
            disabled={loading}
          >
            <SyncOutlined spin={loading} />
          </button>
        </div>
      </div>

      {/* 筛选器 */}
      <div className="px-3 py-1.5 border-b border-gray-800 flex gap-2">
        <FilterButton label="全部" active={filter === 'all'} onClick={() => setFilter('all')} />
        <FilterButton label="进行中" active={filter === 'active'} onClick={() => setFilter('active')} />
        <FilterButton label="已完成" active={filter === 'completed'} onClick={() => setFilter('completed')} />
      </div>

      {/* 订单列表 */}
      <div className="flex-1 overflow-y-auto">
        {filteredOrders.length === 0 ? (
          <div className="p-4">
            <Empty description="暂无订单" image={Empty.PRESENTED_IMAGE_SIMPLE} />
          </div>
        ) : (
          <div>
            {filteredOrders.map(order => (
              <OrderItem
                key={order.id}
                order={order}
                onCancel={() => handleCancelOrder(order.id)}
                cancelling={cancelling === order.id}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function FilterButton({ label, active, onClick }: { label: string; active: boolean; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className={`px-2 py-0.5 rounded text-xs transition-colors ${
        active
          ? 'bg-blue-600 text-white'
          : 'text-gray-400 hover:text-white'
      }`}
    >
      {label}
    </button>
  )
}

interface OrderItemProps {
  order: DisplayOrder
  onCancel: () => void
  cancelling: boolean
}

function OrderItem({ order, onCancel, cancelling }: OrderItemProps) {
  const statusConfig = STATUS_CONFIG[order.status]
  const isBuy = order.side === 'BUY'
  const canCancel = order.status === 'pending' || order.status === 'partial'

  const getOrderTypeLabel = (type: string) => {
    switch (type) {
      case 'market': return '市价'
      case 'limit': return '限价'
      case 'stop': return '止损'
      case 'stop_limit': return '止损限价'
      default: return type
    }
  }

  return (
    <div className="px-3 py-2 border-b border-gray-800/50 hover:bg-gray-800/30 transition-colors">
      {/* 第一行: 方向 + 股票 + 状态 */}
      <div className="flex items-center justify-between mb-1">
        <div className="flex items-center gap-2">
          <span className={`text-xs font-medium ${isBuy ? 'text-green-400' : 'text-red-400'}`}>
            {isBuy ? '买入' : '卖出'}
          </span>
          <span className="text-sm font-medium text-white">{order.symbol}</span>
          <Tag color={statusConfig.color} className="text-xs">
            {statusConfig.label}
          </Tag>
        </div>
        <span className="text-xs text-gray-500 font-mono">{order.time}</span>
      </div>

      {/* 第二行: 数量 + 价格 */}
      <div className="flex items-center justify-between mb-1">
        <div className="text-xs text-gray-400">
          {order.filledQty > 0 && order.filledQty < order.qty ? (
            <span>
              <span className="text-white">{order.filledQty}</span>
              <span className="text-gray-500">/{order.qty} 股</span>
            </span>
          ) : (
            <span>{order.qty} 股</span>
          )}
          <span className="mx-2">·</span>
          <span>{getOrderTypeLabel(order.type)}</span>
        </div>
        <div className="text-xs font-mono">
          {order.type === 'market' ? (
            order.avgPrice ? (
              <span className="text-white">成交 ${order.avgPrice.toFixed(2)}</span>
            ) : (
              <span className="text-gray-500">市价单</span>
            )
          ) : (
            <Tooltip title={order.avgPrice ? `成交均价: $${order.avgPrice.toFixed(2)}` : undefined}>
              <span className="text-white">${order.price.toFixed(2)}</span>
            </Tooltip>
          )}
        </div>
      </div>

      {/* 第三行: 操作按钮 */}
      {canCancel && (
        <div className="flex justify-end">
          <Button
            type="text"
            size="small"
            danger
            icon={<CloseOutlined />}
            onClick={onCancel}
            loading={cancelling}
            className="text-xs"
          >
            取消
          </Button>
        </div>
      )}
    </div>
  )
}
