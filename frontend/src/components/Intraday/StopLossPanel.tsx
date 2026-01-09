/**
 * 止盈止损面板组件
 * PRD 4.18.1 日内交易专用视图
 */
import { useState, useMemo } from 'react'
import {
  InputNumber,
  Select,
  Switch,
  Button,
  Tooltip,
  Divider,
} from 'antd'
import {
  SafetyOutlined,
  ClockCircleOutlined,
  RiseOutlined,
} from '@ant-design/icons'
import { StopLossConfig, DEFAULT_STOP_LOSS_CONFIG } from '../../types/preMarket'

interface Position {
  symbol: string
  quantity: number
  entry_price: number
  current_price: number
  pnl: number
  pnl_pct: number
}

interface StopLossPanelProps {
  position: Position
  atr?: number
  onUpdate: (config: StopLossConfig) => void
}

export default function StopLossPanel({
  position,
  atr = 0.68,
  onUpdate,
}: StopLossPanelProps) {
  const [config, setConfig] = useState<StopLossConfig>(DEFAULT_STOP_LOSS_CONFIG)

  // 计算止损价格
  const stopLossPrice = useMemo(() => {
    return calculatePrice('stop', config, position.entry_price, atr)
  }, [config.stop_loss_type, config.stop_loss_value, position.entry_price, atr])

  // 计算止盈价格
  const takeProfitPrice = useMemo(() => {
    return calculatePrice('profit', config, position.entry_price, atr)
  }, [config.take_profit_type, config.take_profit_value, position.entry_price, atr])

  // 计算盈亏比
  const riskRewardRatio = useMemo(() => {
    const risk = position.entry_price - stopLossPrice
    const reward = takeProfitPrice - position.entry_price
    return risk > 0 ? (reward / risk).toFixed(1) : '0'
  }, [stopLossPrice, takeProfitPrice, position.entry_price])

  const handleUpdate = (updates: Partial<StopLossConfig>) => {
    const newConfig = { ...config, ...updates }
    setConfig(newConfig)
  }

  const handleApply = () => {
    onUpdate(config)
  }

  return (
    <div className="bg-dark-card rounded-lg overflow-hidden">
      {/* 头部 */}
      <div className="px-4 py-3 border-b border-gray-700 flex items-center gap-2">
        <SafetyOutlined className="text-xl text-blue-400" />
        <span className="text-white font-medium">止盈止损设置</span>
      </div>

      {/* 持仓信息 */}
      <div className="px-4 py-3 border-b border-gray-700 bg-gray-800/30">
        <div className="flex justify-between text-sm mb-1">
          <span className="text-gray-400">
            {position.symbol} {position.quantity}股 @${position.entry_price.toFixed(2)}
          </span>
        </div>
        <div className={`text-sm ${position.pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
          浮盈: {position.pnl >= 0 ? '+' : ''}${position.pnl.toFixed(2)}
          ({position.pnl_pct.toFixed(2)}%)
        </div>
      </div>

      <div className="p-4 space-y-4">
        {/* 止损设置 */}
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className="text-red-400">🛑</span>
            <span className="text-white text-sm font-medium">止损</span>
          </div>

          <div className="grid grid-cols-2 gap-2 mb-2">
            <Select
              value={config.stop_loss_type}
              onChange={(v) => handleUpdate({ stop_loss_type: v as any })}
              size="small"
              options={[
                { value: 'atr', label: 'ATR动态' },
                { value: 'fixed', label: '固定价格' },
                { value: 'percentage', label: '百分比' },
              ]}
            />
            {config.stop_loss_type === 'atr' && (
              <Select
                value={config.stop_loss_value}
                onChange={(v) => handleUpdate({ stop_loss_value: v })}
                size="small"
                options={[
                  { value: 1.0, label: '1.0x ATR' },
                  { value: 1.5, label: '1.5x ATR' },
                  { value: 2.0, label: '2.0x ATR' },
                  { value: 2.5, label: '2.5x ATR' },
                ]}
              />
            )}
            {config.stop_loss_type === 'percentage' && (
              <InputNumber
                value={config.stop_loss_value}
                onChange={(v) => handleUpdate({ stop_loss_value: v || 1 })}
                size="small"
                min={0.1}
                max={10}
                step={0.1}
                suffix="%"
                style={{ width: '100%' }}
              />
            )}
          </div>

          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-400">止损价:</span>
            <span className="text-white font-mono">${stopLossPrice.toFixed(2)}</span>
          </div>
          {config.stop_loss_type === 'atr' && (
            <div className="text-gray-500 text-xs mt-1">
              当前ATR: ${atr.toFixed(2)}
            </div>
          )}
        </div>

        <Divider className="my-2" style={{ borderColor: '#374151' }} />

        {/* 止盈设置 */}
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className="text-green-400">🎯</span>
            <span className="text-white text-sm font-medium">止盈</span>
          </div>

          <div className="grid grid-cols-2 gap-2 mb-2">
            <Select
              value={config.take_profit_type}
              onChange={(v) => handleUpdate({ take_profit_type: v as any })}
              size="small"
              options={[
                { value: 'atr', label: 'ATR动态' },
                { value: 'fixed', label: '固定价格' },
                { value: 'percentage', label: '百分比' },
              ]}
            />
            {config.take_profit_type === 'atr' && (
              <Select
                value={config.take_profit_value}
                onChange={(v) => handleUpdate({ take_profit_value: v })}
                size="small"
                options={[
                  { value: 1.5, label: '1.5x ATR' },
                  { value: 2.0, label: '2.0x ATR' },
                  { value: 2.5, label: '2.5x ATR' },
                  { value: 3.0, label: '3.0x ATR' },
                ]}
              />
            )}
            {config.take_profit_type === 'percentage' && (
              <InputNumber
                value={config.take_profit_value}
                onChange={(v) => handleUpdate({ take_profit_value: v || 1 })}
                size="small"
                min={0.1}
                max={20}
                step={0.1}
                suffix="%"
                style={{ width: '100%' }}
              />
            )}
          </div>

          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-400">止盈价:</span>
            <span className="text-white font-mono">${takeProfitPrice.toFixed(2)}</span>
          </div>
          <div className="text-blue-400 text-xs mt-1">
            盈亏比: 1:{riskRewardRatio}
          </div>
        </div>

        <Divider className="my-2" style={{ borderColor: '#374151' }} />

        {/* 时间止损 */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <ClockCircleOutlined className="text-yellow-400" />
              <span className="text-white text-sm font-medium">时间止损</span>
            </div>
            <Switch
              checked={config.time_stop_enabled}
              onChange={(v) => handleUpdate({ time_stop_enabled: v })}
              size="small"
            />
          </div>

          {config.time_stop_enabled && (
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <span className="text-gray-400 text-sm">平仓时间:</span>
                <Select
                  value={config.time_stop_time}
                  onChange={(v) => handleUpdate({ time_stop_time: v })}
                  size="small"
                  style={{ width: 160 }}
                  options={[
                    { value: '15:45', label: '15:45 (收盘前15分钟)' },
                    { value: '15:50', label: '15:50 (收盘前10分钟)' },
                    { value: '15:55', label: '15:55 (收盘前5分钟)' },
                  ]}
                />
              </div>
              <div className="text-yellow-400/70 text-xs">
                ⚠️ 到达时间后自动市价平仓
              </div>
            </div>
          )}
        </div>

        <Divider className="my-2" style={{ borderColor: '#374151' }} />

        {/* 移动止损 */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <RiseOutlined className="text-purple-400" />
              <span className="text-white text-sm font-medium">移动止损</span>
            </div>
            <Switch
              checked={config.trailing_stop_enabled}
              onChange={(v) => handleUpdate({ trailing_stop_enabled: v })}
              size="small"
            />
          </div>

          {config.trailing_stop_enabled && (
            <div className="grid grid-cols-2 gap-2">
              <div>
                <div className="text-gray-400 text-xs mb-1">触发条件</div>
                <InputNumber
                  value={config.trailing_trigger_pct}
                  onChange={(v) => handleUpdate({ trailing_trigger_pct: v || 0.5 })}
                  size="small"
                  min={0.1}
                  max={5}
                  step={0.1}
                  suffix="%"
                  style={{ width: '100%' }}
                />
              </div>
              <div>
                <div className="text-gray-400 text-xs mb-1">跟踪距离</div>
                <InputNumber
                  value={config.trailing_distance_pct}
                  onChange={(v) => handleUpdate({ trailing_distance_pct: v || 0.3 })}
                  size="small"
                  min={0.1}
                  max={3}
                  step={0.1}
                  suffix="%"
                  style={{ width: '100%' }}
                />
              </div>
            </div>
          )}
        </div>

        {/* 应用按钮 */}
        <Button type="primary" block onClick={handleApply}>
          应用止盈止损设置
        </Button>
      </div>
    </div>
  )
}

function calculatePrice(
  type: 'stop' | 'profit',
  config: StopLossConfig,
  entryPrice: number,
  atr: number
): number {
  const isStop = type === 'stop'
  const configType = isStop ? config.stop_loss_type : config.take_profit_type
  const configValue = isStop ? config.stop_loss_value : config.take_profit_value
  const direction = isStop ? -1 : 1

  switch (configType) {
    case 'atr':
      return entryPrice + direction * configValue * atr
    case 'percentage':
      return entryPrice * (1 + direction * configValue / 100)
    case 'fixed':
      return configValue
    default:
      return entryPrice
  }
}
