/**
 * 时间框架选择器组件
 * Sprint 6: T2 - 多时间框架支持
 */
import { memo } from 'react'
import { Segmented } from 'antd'
import type { TimeFrame } from './TradingViewChart'

interface TimeframeSelectorProps {
  value: TimeFrame
  onChange: (value: TimeFrame) => void
  size?: 'small' | 'middle' | 'large'
  disabled?: boolean
  compact?: boolean // 紧凑模式，只显示常用时间框架
}

// 完整时间框架选项
const FULL_TIMEFRAME_OPTIONS: { label: string; value: TimeFrame }[] = [
  { label: '1分', value: '1' },
  { label: '5分', value: '5' },
  { label: '15分', value: '15' },
  { label: '30分', value: '30' },
  { label: '1时', value: '60' },
  { label: '4时', value: '240' },
  { label: '日', value: 'D' },
  { label: '周', value: 'W' },
  { label: '月', value: 'M' },
]

// 紧凑模式选项 (日内交易常用)
const COMPACT_TIMEFRAME_OPTIONS: { label: string; value: TimeFrame }[] = [
  { label: '1分', value: '1' },
  { label: '5分', value: '5' },
  { label: '15分', value: '15' },
  { label: '1时', value: '60' },
  { label: '日', value: 'D' },
]

function TimeframeSelectorComponent({
  value,
  onChange,
  size = 'small',
  disabled = false,
  compact = false,
}: TimeframeSelectorProps) {
  const options = compact ? COMPACT_TIMEFRAME_OPTIONS : FULL_TIMEFRAME_OPTIONS

  return (
    <Segmented
      value={value}
      onChange={(val) => onChange(val as TimeFrame)}
      options={options}
      size={size}
      disabled={disabled}
      className="timeframe-selector"
      style={{
        backgroundColor: 'transparent',
      }}
    />
  )
}

export const TimeframeSelector = memo(TimeframeSelectorComponent)
export default TimeframeSelector
