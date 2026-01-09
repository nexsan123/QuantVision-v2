/**
 * 信号雷达面板
 * Sprint 3 - F9: 实时交易信号监控
 *
 * 状态指示器:
 * - 🔴 持仓中
 * - 🟢 买入信号
 * - 🟠 卖出信号
 * - 🟡 接近信号
 * - ⚪ 监控中
 */
import { useState, useEffect } from 'react'
import { Tooltip, Badge } from 'antd'
import { SyncOutlined } from '@ant-design/icons'

interface SignalRadarPanelProps {
  strategyId: string
  deploymentId: string
}

// 信号状态类型
type SignalStatus = 'holding' | 'buy' | 'sell' | 'approaching' | 'watching'

interface SignalItem {
  symbol: string
  status: SignalStatus
  price: number
  change: number
  changePct: number
  signalStrength?: number // 信号强度 0-100
  message?: string
}

// 状态配置
const STATUS_CONFIG: Record<SignalStatus, { icon: string; label: string; color: string }> = {
  holding: { icon: '🔴', label: '持仓中', color: 'text-red-400' },
  buy: { icon: '🟢', label: '买入信号', color: 'text-green-400' },
  sell: { icon: '🟠', label: '卖出信号', color: 'text-orange-400' },
  approaching: { icon: '🟡', label: '接近信号', color: 'text-yellow-400' },
  watching: { icon: '⚪', label: '监控中', color: 'text-gray-400' },
}

// 模拟信号数据
const mockSignals: SignalItem[] = [
  { symbol: 'AAPL', status: 'holding', price: 178.52, change: 2.35, changePct: 0.0133, signalStrength: 85 },
  { symbol: 'NVDA', status: 'buy', price: 475.50, change: 12.80, changePct: 0.0277, signalStrength: 92, message: 'RSI超卖反弹' },
  { symbol: 'TSLA', status: 'sell', price: 245.30, change: -8.20, changePct: -0.0323, signalStrength: 78, message: '突破止损线' },
  { symbol: 'MSFT', status: 'approaching', price: 372.15, change: 1.85, changePct: 0.0050, signalStrength: 65, message: '接近买入点' },
  { symbol: 'GOOGL', status: 'watching', price: 141.23, change: 0.45, changePct: 0.0032 },
  { symbol: 'META', status: 'watching', price: 325.80, change: -1.20, changePct: -0.0037 },
  { symbol: 'AMZN', status: 'holding', price: 185.60, change: 3.40, changePct: 0.0187, signalStrength: 70 },
  { symbol: 'AMD', status: 'approaching', price: 145.20, change: 4.50, changePct: 0.0320, signalStrength: 58, message: '动量增强中' },
]

export default function SignalRadarPanel({ strategyId, deploymentId }: SignalRadarPanelProps) {
  const [signals, setSignals] = useState<SignalItem[]>([])
  const [filter, setFilter] = useState<SignalStatus | 'all'>('all')
  const [refreshing, setRefreshing] = useState(false)

  useEffect(() => {
    // 模拟加载信号数据
    setSignals(mockSignals)
  }, [strategyId, deploymentId])

  const handleRefresh = () => {
    setRefreshing(true)
    setTimeout(() => {
      setSignals([...mockSignals].sort(() => Math.random() - 0.5))
      setRefreshing(false)
    }, 500)
  }

  // 按状态筛选
  const filteredSignals = filter === 'all'
    ? signals
    : signals.filter(s => s.status === filter)

  // 按状态分组统计
  const statusCounts = signals.reduce((acc, s) => {
    acc[s.status] = (acc[s.status] || 0) + 1
    return acc
  }, {} as Record<SignalStatus, number>)

  return (
    <div className="h-full flex flex-col">
      {/* 标题栏 */}
      <div className="px-3 py-2 border-b border-gray-800 flex items-center justify-between">
        <span className="text-sm font-medium text-white">信号雷达</span>
        <button
          onClick={handleRefresh}
          className="text-gray-400 hover:text-white transition-colors"
          disabled={refreshing}
        >
          <SyncOutlined spin={refreshing} />
        </button>
      </div>

      {/* 状态筛选器 */}
      <div className="px-2 py-2 flex flex-wrap gap-1 border-b border-gray-800">
        <FilterChip
          label="全部"
          count={signals.length}
          active={filter === 'all'}
          onClick={() => setFilter('all')}
        />
        {(Object.keys(STATUS_CONFIG) as SignalStatus[]).map(status => (
          <FilterChip
            key={status}
            label={STATUS_CONFIG[status].icon}
            count={statusCounts[status] || 0}
            active={filter === status}
            onClick={() => setFilter(status)}
          />
        ))}
      </div>

      {/* 信号列表 */}
      <div className="flex-1 overflow-y-auto">
        {filteredSignals.length === 0 ? (
          <div className="p-4 text-center text-gray-500 text-sm">
            暂无信号
          </div>
        ) : (
          <div className="py-1">
            {filteredSignals.map(signal => (
              <SignalItem key={signal.symbol} signal={signal} />
            ))}
          </div>
        )}
      </div>

      {/* 图例 */}
      <div className="px-3 py-2 border-t border-gray-800 flex flex-wrap gap-2 text-xs">
        {(Object.keys(STATUS_CONFIG) as SignalStatus[]).map(status => (
          <span key={status} className="text-gray-500">
            {STATUS_CONFIG[status].icon} {STATUS_CONFIG[status].label}
          </span>
        ))}
      </div>
    </div>
  )
}

function FilterChip({
  label,
  count,
  active,
  onClick,
}: {
  label: string
  count: number
  active: boolean
  onClick: () => void
}) {
  return (
    <button
      onClick={onClick}
      className={`px-2 py-0.5 rounded text-xs transition-colors ${
        active
          ? 'bg-blue-600 text-white'
          : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
      }`}
    >
      {label} {count > 0 && <span className="ml-0.5">{count}</span>}
    </button>
  )
}

function SignalItem({ signal }: { signal: SignalItem }) {
  const config = STATUS_CONFIG[signal.status]
  const isPositive = signal.change >= 0

  return (
    <Tooltip title={signal.message} placement="right">
      <div className="px-3 py-2 hover:bg-gray-800/50 cursor-pointer transition-colors border-b border-gray-800/50">
        {/* 第一行: 状态 + 股票代码 + 价格 */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-sm">{config.icon}</span>
            <span className="text-sm font-medium text-white">{signal.symbol}</span>
            {signal.signalStrength && signal.status !== 'watching' && (
              <Badge
                count={signal.signalStrength}
                style={{
                  backgroundColor: signal.signalStrength >= 80 ? '#52c41a' : '#faad14',
                  fontSize: '10px',
                }}
              />
            )}
          </div>
          <span className="text-sm font-mono text-white">
            ${signal.price.toFixed(2)}
          </span>
        </div>

        {/* 第二行: 信号说明 + 涨跌幅 */}
        <div className="flex items-center justify-between mt-1">
          <span className={`text-xs ${config.color}`}>
            {signal.message || config.label}
          </span>
          <span
            className={`text-xs font-mono ${
              isPositive ? 'text-green-400' : 'text-red-400'
            }`}
          >
            {isPositive ? '+' : ''}{signal.change.toFixed(2)}
            <span className="text-gray-500 ml-1">
              ({(signal.changePct * 100).toFixed(2)}%)
            </span>
          </span>
        </div>
      </div>
    </Tooltip>
  )
}
