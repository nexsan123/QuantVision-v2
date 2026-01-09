/**
 * 信号雷达面板
 * PRD 4.16.2
 */
import { useState, useEffect, useCallback } from 'react'
import { Card, Input, Select, Button, Badge, Spin, Empty, message } from 'antd'
import { SearchOutlined, ReloadOutlined, FilterOutlined } from '@ant-design/icons'
import SignalList from './SignalList'
import {
  Signal,
  SignalType,
  SignalStrength,
  SignalListResponse,
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
      // TODO: 调用实际API
      // const params = new URLSearchParams();
      // if (signalTypeFilter) params.append('signal_type', signalTypeFilter);
      // if (strengthFilter) params.append('signal_strength', strengthFilter);
      // if (searchText) params.append('search', searchText);
      // const response = await fetch(`/api/v1/signal-radar/${strategyId}?${params}`);
      // const data: SignalListResponse = await response.json();
      // setSignals(data.signals);
      // setSummary(data.summary);

      // 模拟数据
      await new Promise(resolve => setTimeout(resolve, 500))

      const mockSignals: Signal[] = [
        {
          signalId: '1',
          strategyId,
          symbol: 'AAPL',
          companyName: 'Apple Inc.',
          signalType: 'buy',
          signalStrength: 'strong',
          signalScore: 85,
          status: 'buy_signal',
          triggeredFactors: [
            { factorId: 'pe', factorName: '市盈率', currentValue: 22.5, threshold: 25, direction: 'below', nearTriggerPct: 100, isSatisfied: true },
            { factorId: 'momentum', factorName: '动量', currentValue: 0.08, threshold: 0.05, direction: 'above', nearTriggerPct: 100, isSatisfied: true },
          ],
          currentPrice: 185.50,
          targetPrice: 205.00,
          stopLossPrice: 175.00,
          expectedReturnPct: 0.105,
          signalTime: new Date().toISOString(),
          isHolding: false,
        },
        {
          signalId: '2',
          strategyId,
          symbol: 'MSFT',
          companyName: 'Microsoft Corp.',
          signalType: 'buy',
          signalStrength: 'medium',
          signalScore: 72,
          status: 'near_trigger',
          triggeredFactors: [
            { factorId: 'pe', factorName: '市盈率', currentValue: 28.5, threshold: 30, direction: 'below', nearTriggerPct: 85, isSatisfied: false },
          ],
          currentPrice: 378.20,
          targetPrice: 420.00,
          stopLossPrice: 360.00,
          expectedReturnPct: 0.11,
          signalTime: new Date().toISOString(),
          isHolding: false,
        },
        {
          signalId: '3',
          strategyId,
          symbol: 'GOOGL',
          companyName: 'Alphabet Inc.',
          signalType: 'sell',
          signalStrength: 'strong',
          signalScore: 90,
          status: 'sell_signal',
          triggeredFactors: [],
          currentPrice: 142.80,
          stopLossPrice: 135.00,
          signalTime: new Date().toISOString(),
          isHolding: true,
        },
        {
          signalId: '4',
          strategyId,
          symbol: 'NVDA',
          companyName: 'NVIDIA Corp.',
          signalType: 'hold',
          signalStrength: 'medium',
          signalScore: 65,
          status: 'holding',
          triggeredFactors: [],
          currentPrice: 495.60,
          signalTime: new Date().toISOString(),
          isHolding: true,
        },
        {
          signalId: '5',
          strategyId,
          symbol: 'TSLA',
          companyName: 'Tesla Inc.',
          signalType: 'buy',
          signalStrength: 'weak',
          signalScore: 55,
          status: 'monitoring',
          triggeredFactors: [],
          currentPrice: 248.50,
          signalTime: new Date().toISOString(),
          isHolding: false,
        },
      ]

      // 应用筛选
      let filtered = mockSignals
      if (signalTypeFilter) {
        filtered = filtered.filter(s => s.signalType === signalTypeFilter)
      }
      if (strengthFilter) {
        filtered = filtered.filter(s => s.signalStrength === strengthFilter)
      }
      if (searchText) {
        const search = searchText.toLowerCase()
        filtered = filtered.filter(
          s => s.symbol.toLowerCase().includes(search) ||
               s.companyName.toLowerCase().includes(search)
        )
      }

      setSignals(filtered)
      setSummary({
        buy: mockSignals.filter(s => s.signalType === 'buy').length,
        sell: mockSignals.filter(s => s.signalType === 'sell').length,
        hold: mockSignals.filter(s => s.signalType === 'hold').length,
      })
    } catch {
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
