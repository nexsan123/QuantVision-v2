/**
 * 技术指标面板
 * Sprint 6: T3 - 技术指标配置
 */
import { useState, memo } from 'react'
import { Dropdown, Button, Checkbox, InputNumber, Space, Divider } from 'antd'
import { SettingOutlined, LineChartOutlined } from '@ant-design/icons'
import type { IndicatorConfig } from './TradingViewChart'

interface IndicatorPanelProps {
  indicators: IndicatorConfig[]
  onChange: (indicators: IndicatorConfig[]) => void
  disabled?: boolean
}

// 可用指标列表
const AVAILABLE_INDICATORS: IndicatorConfig[] = [
  { id: 'MASimple@tv-basicstudies', name: 'MA (移动平均)', inputs: { length: 20 } },
  { id: 'MAExp@tv-basicstudies', name: 'EMA (指数移动平均)', inputs: { length: 12 } },
  { id: 'RSI@tv-basicstudies', name: 'RSI (相对强弱)', inputs: { length: 14 } },
  { id: 'MACD@tv-basicstudies', name: 'MACD', inputs: { fast: 12, slow: 26, signal: 9 } },
  { id: 'BB@tv-basicstudies', name: 'Bollinger Bands', inputs: { length: 20, mult: 2 } },
  { id: 'VWAP@tv-basicstudies', name: 'VWAP', inputs: {} },
  { id: 'Volume@tv-basicstudies', name: '成交量', inputs: {} },
  { id: 'ATR@tv-basicstudies', name: 'ATR (真实波幅)', inputs: { length: 14 } },
  { id: 'Stochastic@tv-basicstudies', name: 'Stochastic (随机指标)', inputs: { k: 14, d: 3 } },
  { id: 'CCI@tv-basicstudies', name: 'CCI (商品通道)', inputs: { length: 20 } },
]

// 预设组合
const PRESET_COMBINATIONS: { name: string; indicators: IndicatorConfig[] }[] = [
  {
    name: '日内交易',
    indicators: [
      { id: 'MASimple@tv-basicstudies', name: 'MA 9', inputs: { length: 9 } },
      { id: 'MASimple@tv-basicstudies', name: 'MA 20', inputs: { length: 20 } },
      { id: 'VWAP@tv-basicstudies', name: 'VWAP', inputs: {} },
      { id: 'Volume@tv-basicstudies', name: '成交量', inputs: {} },
    ],
  },
  {
    name: '趋势跟踪',
    indicators: [
      { id: 'MASimple@tv-basicstudies', name: 'MA 20', inputs: { length: 20 } },
      { id: 'MASimple@tv-basicstudies', name: 'MA 50', inputs: { length: 50 } },
      { id: 'MACD@tv-basicstudies', name: 'MACD', inputs: {} },
      { id: 'RSI@tv-basicstudies', name: 'RSI', inputs: { length: 14 } },
    ],
  },
  {
    name: '动量分析',
    indicators: [
      { id: 'RSI@tv-basicstudies', name: 'RSI', inputs: { length: 14 } },
      { id: 'MACD@tv-basicstudies', name: 'MACD', inputs: {} },
      { id: 'Stochastic@tv-basicstudies', name: 'Stochastic', inputs: { k: 14, d: 3 } },
    ],
  },
  {
    name: '波动率',
    indicators: [
      { id: 'BB@tv-basicstudies', name: 'Bollinger Bands', inputs: { length: 20, mult: 2 } },
      { id: 'ATR@tv-basicstudies', name: 'ATR', inputs: { length: 14 } },
    ],
  },
]

function IndicatorPanelComponent({
  indicators,
  onChange,
  disabled = false,
}: IndicatorPanelProps) {
  const [showConfig, setShowConfig] = useState(false)

  // 检查指标是否已选中
  const isSelected = (indicatorId: string) => {
    return indicators.some((ind) => ind.id === indicatorId)
  }

  // 切换指标
  const toggleIndicator = (indicator: IndicatorConfig) => {
    if (isSelected(indicator.id)) {
      onChange(indicators.filter((ind) => ind.id !== indicator.id))
    } else {
      onChange([...indicators, indicator])
    }
  }

  // 应用预设
  const applyPreset = (preset: { name: string; indicators: IndicatorConfig[] }) => {
    onChange(preset.indicators)
  }

  // 下拉菜单内容
  const menuContent = (
    <div className="bg-dark-card border border-gray-700 rounded-lg p-4 min-w-[300px]">
      {/* 预设组合 */}
      <div className="mb-4">
        <div className="text-gray-400 text-xs mb-2">快速预设</div>
        <div className="flex flex-wrap gap-2">
          {PRESET_COMBINATIONS.map((preset) => (
            <Button
              key={preset.name}
              size="small"
              onClick={() => applyPreset(preset)}
              className="text-xs"
            >
              {preset.name}
            </Button>
          ))}
        </div>
      </div>

      <Divider className="my-3 border-gray-700" />

      {/* 指标列表 */}
      <div className="text-gray-400 text-xs mb-2">指标选择</div>
      <div className="max-h-[300px] overflow-y-auto">
        {AVAILABLE_INDICATORS.map((indicator) => (
          <div
            key={indicator.id}
            className="flex items-center justify-between py-2 hover:bg-gray-800/50 px-2 rounded"
          >
            <Checkbox
              checked={isSelected(indicator.id)}
              onChange={() => toggleIndicator(indicator)}
              disabled={disabled}
            >
              <span className="text-gray-200 text-sm">{indicator.name}</span>
            </Checkbox>
            {showConfig && indicator.inputs && Object.keys(indicator.inputs).length > 0 && (
              <Space size="small">
                {Object.entries(indicator.inputs).map(([key, value]) => (
                  <InputNumber
                    key={key}
                    size="small"
                    value={value as number}
                    min={1}
                    max={200}
                    style={{ width: 60 }}
                    disabled={disabled || !isSelected(indicator.id)}
                  />
                ))}
              </Space>
            )}
          </div>
        ))}
      </div>

      <Divider className="my-3 border-gray-700" />

      {/* 底部操作 */}
      <div className="flex items-center justify-between">
        <Button
          type="text"
          size="small"
          icon={<SettingOutlined />}
          onClick={() => setShowConfig(!showConfig)}
          className="text-gray-400"
        >
          {showConfig ? '隐藏参数' : '显示参数'}
        </Button>
        <Button
          type="text"
          size="small"
          onClick={() => onChange([])}
          disabled={disabled || indicators.length === 0}
          className="text-gray-400"
        >
          清空全部
        </Button>
      </div>
    </div>
  )

  return (
    <Dropdown
      dropdownRender={() => menuContent}
      trigger={['click']}
      placement="bottomRight"
      disabled={disabled}
    >
      <Button
        type="text"
        icon={<LineChartOutlined />}
        className="text-gray-400 hover:text-white"
      >
        指标 ({indicators.length})
      </Button>
    </Dropdown>
  )
}

export const IndicatorPanel = memo(IndicatorPanelComponent)
export default IndicatorPanel
