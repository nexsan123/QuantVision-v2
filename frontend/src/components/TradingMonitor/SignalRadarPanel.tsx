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
import { useState, useEffect, useCallback } from 'react'
import { Tooltip, Badge } from 'antd'
import { SyncOutlined } from '@ant-design/icons'
import { getSimpleSignals, type SimpleSignal } from '../../services/signalRadarService'

interface SignalRadarPanelProps {
  strategyId: string
  deploymentId: string
  onSymbolClick?: (symbol: string) => void
}

// 信号状态类型
type SignalStatus = 'holding' | 'buy' | 'sell' | 'approaching' | 'watching'

type SignalItem = SimpleSignal

// 状态配置
const STATUS_CONFIG: Record<SignalStatus, { icon: string; label: string; color: string }> = {
  holding: { icon: '🔴', label: '持仓中', color: 'text-red-400' },
  buy: { icon: '🟢', label: '买入信号', color: 'text-green-400' },
  sell: { icon: '🟠', label: '卖出信号', color: 'text-orange-400' },
  approaching: { icon: '🟡', label: '接近信号', color: 'text-yellow-400' },
  watching: { icon: '⚪', label: '监控中', color: 'text-gray-400' },
}

export default function SignalRadarPanel({ strategyId, deploymentId, onSymbolClick }: SignalRadarPanelProps) {
  const [signals, setSignals] = useState<SignalItem[]>([])
  const [filter, setFilter] = useState<SignalStatus | 'all'>('all')
  const [refreshing, setRefreshing] = useState(false)

  const fetchSignals = useCallback(async () => {
    if (!strategyId) return

    setRefreshing(true)
    try {
      const data = await getSimpleSignals(strategyId, deploymentId)
      setSignals(data)
    } catch (err) {
      console.error('Failed to fetch signals:', err)
    } finally {
      setRefreshing(false)
    }
  }, [strategyId, deploymentId])

  useEffect(() => {
    fetchSignals()
  }, [fetchSignals])

  // 自动刷新 30秒
  useEffect(() => {
    const interval = setInterval(fetchSignals, 30000)
    return () => clearInterval(interval)
  }, [fetchSignals])

  const handleRefresh = async () => {
    setRefreshing(true)
    await fetchSignals()
    setRefreshing(false)
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
              <SignalItem key={signal.symbol} signal={signal} onSymbolClick={onSymbolClick} />
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

function SignalItem({ signal, onSymbolClick }: { signal: SignalItem; onSymbolClick?: (symbol: string) => void }) {
  const config = STATUS_CONFIG[signal.status]
  const isPositive = signal.change >= 0

  return (
    <Tooltip title={signal.message} placement="right">
      <div
        className="px-3 py-2 hover:bg-gray-800/50 cursor-pointer transition-colors border-b border-gray-800/50"
        onClick={() => onSymbolClick?.(signal.symbol)}
      >
        {/* 第一行: 状态 + 股票代码 + 价格 */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-sm">{config.icon}</span>
            <span className="text-sm font-medium text-white hover:text-blue-400">{signal.symbol}</span>
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
