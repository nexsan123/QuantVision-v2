/**
 * 信号雷达面板
 * PRD 4.16.2
 */
import { useState, useEffect, useCallback } from 'react'
import { Card, Input, Select, Button, Badge, Spin, Empty, message } from 'antd'
import { SearchOutlined, ReloadOutlined } from '@ant-design/icons'
import SignalList from './SignalList'
import { getSignals } from '../../services/signalRadarService'
import {
  Signal,
  SignalType,
  SignalStrength,
  SIGNAL_TYPE_CONFIG,
} from '../../types/signalRadar'

interface SignalRadarProps {
  strategyId: string
  onSignalClick?: (signal: Signal) => void
}

export default function SignalRadar({ strategyId, onSignalClick }: SignalRadarProps) {
  const [loading, setLoading] = useState(false)
  const [signals, setSignals] = useState<Signal[]>([])
  const [summary, setSummary] = useState({ buy: 0, sell: 0, hold: 0 })
  const [searchText, setSearchText] = useState('')
  const [signalTypeFilter, setSignalTypeFilter] = useState<SignalType | ''>('')
  const [strengthFilter, setStrengthFilter] = useState<SignalStrength | ''>('')

  const fetchSignals = useCallback(async () => {
    if (!strategyId) return

    setLoading(true)
    try {
      // 调用真实 API
      const response = await getSignals(strategyId, {
        signalType: signalTypeFilter || undefined,
        signalStrength: strengthFilter || undefined,
        search: searchText || undefined,
        limit: 50,
      })

      setSignals(response.signals)
      setSummary(response.summary)
    } catch (err) {
      console.error('获取信号失败:', err)
      message.error('获取信号失败')
    } finally {
      setLoading(false)
    }
  }, [strategyId, signalTypeFilter, strengthFilter, searchText])

  useEffect(() => {
    fetchSignals()
  }, [fetchSignals])

  // 自动刷新
  useEffect(() => {
    const interval = setInterval(fetchSignals, 30000) // 30秒刷新
    return () => clearInterval(interval)
  }, [fetchSignals])

  const handleRefresh = () => {
    fetchSignals()
    message.success('信号已刷新')
  }

  return (
    <Card
      className="!bg-dark-card h-full flex flex-col"
      title={
        <div className="flex items-center gap-2">
          <span className="text-lg">🎯 信号雷达</span>
        </div>
      }
      extra={
        <Button
          icon={<ReloadOutlined spin={loading} />}
          onClick={handleRefresh}
          size="small"
        >
          刷新
        </Button>
      }
    >
      {/* 筛选栏 */}
      <div className="flex flex-wrap gap-2 mb-4">
        <Input
          placeholder="搜索股票..."
          prefix={<SearchOutlined className="text-gray-500" />}
          value={searchText}
          onChange={e => setSearchText(e.target.value)}
          className="w-40"
          allowClear
          size="small"
        />
        <Select
          placeholder="信号类型"
          value={signalTypeFilter || undefined}
          onChange={v => setSignalTypeFilter(v || '')}
          allowClear
          className="w-24"
          size="small"
          options={Object.entries(SIGNAL_TYPE_CONFIG).map(([key, config]) => ({
            value: key,
            label: `${config.icon} ${config.label}`,
          }))}
        />
        <Select
          placeholder="强度"
          value={strengthFilter || undefined}
          onChange={v => setStrengthFilter(v || '')}
          allowClear
          className="w-20"
          size="small"
          options={[
            { value: 'strong', label: '⭐⭐⭐ 强' },
            { value: 'medium', label: '⭐⭐ 中' },
            { value: 'weak', label: '⭐ 弱' },
          ]}
        />
      </div>

      {/* 统计标签 */}
      <div className="flex gap-3 mb-4">
        <Badge
          count={summary.buy}
          showZero
          color="green"
          className="cursor-pointer"
          onClick={() => setSignalTypeFilter(signalTypeFilter === 'buy' ? '' : 'buy')}
        >
          <div className={`px-3 py-1 rounded text-sm ${signalTypeFilter === 'buy' ? 'bg-green-500/20 text-green-400' : 'bg-dark-hover'}`}>
            📈 买入
          </div>
        </Badge>
        <Badge
          count={summary.sell}
          showZero
          color="red"
          className="cursor-pointer"
          onClick={() => setSignalTypeFilter(signalTypeFilter === 'sell' ? '' : 'sell')}
        >
          <div className={`px-3 py-1 rounded text-sm ${signalTypeFilter === 'sell' ? 'bg-red-500/20 text-red-400' : 'bg-dark-hover'}`}>
            📉 卖出
          </div>
        </Badge>
        <Badge
          count={summary.hold}
          showZero
          color="blue"
          className="cursor-pointer"
          onClick={() => setSignalTypeFilter(signalTypeFilter === 'hold' ? '' : 'hold')}
        >
          <div className={`px-3 py-1 rounded text-sm ${signalTypeFilter === 'hold' ? 'bg-blue-500/20 text-blue-400' : 'bg-dark-hover'}`}>
            ⏸️ 持有
          </div>
        </Badge>
      </div>

      {/* 信号列表 */}
      <div className="flex-1 overflow-auto">
        {loading ? (
          <div className="flex items-center justify-center h-40">
            <Spin />
          </div>
        ) : signals.length === 0 ? (
          <Empty description="暂无信号" />
        ) : (
          <SignalList signals={signals} onSignalClick={onSignalClick} />
        )}
      </div>
    </Card>
  )
}
