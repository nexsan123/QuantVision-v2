/**
 * 交易模式切换组件
 *
 * 实盘/模拟交易切换
 */

import { memo } from 'react'
import { Switch, Tag, Popconfirm } from 'antd'
import { ThunderboltOutlined, ExperimentOutlined } from '@ant-design/icons'
import { TradingMode } from '@/types/trading'

interface TradingModeToggleProps {
  mode: TradingMode
  onChange: (mode: TradingMode) => void
  disabled?: boolean
  showConfirm?: boolean
}

function TradingModeToggleComponent({
  mode,
  onChange,
  disabled = false,
  showConfirm = true,
}: TradingModeToggleProps) {
  const isLive = mode === 'live'

  const handleChange = (checked: boolean) => {
    onChange(checked ? 'live' : 'paper')
  }

  const toggle = (
    <div className="flex items-center gap-3">
      {/* Paper Trading 标签 */}
      <Tag
        icon={<ExperimentOutlined />}
        color={!isLive ? 'blue' : 'default'}
        className={`transition-opacity ${isLive ? 'opacity-50' : ''}`}
      >
        模拟交易
      </Tag>

      {/* 切换开关 */}
      <Switch
        checked={isLive}
        onChange={showConfirm ? undefined : handleChange}
        disabled={disabled}
        className={isLive ? '!bg-red-500' : '!bg-blue-500'}
      />

      {/* Live Trading 标签 */}
      <Tag
        icon={<ThunderboltOutlined />}
        color={isLive ? 'red' : 'default'}
        className={`transition-opacity ${!isLive ? 'opacity-50' : ''}`}
      >
        实盘交易
      </Tag>
    </div>
  )

  if (showConfirm && !isLive) {
    return (
      <Popconfirm
        title="切换到实盘交易"
        description={
          <div className="max-w-xs">
            <p className="text-red-400 font-medium">⚠️ 警告：实盘交易涉及真实资金</p>
            <p className="text-gray-400 text-xs mt-1">
              切换到实盘模式后，所有交易操作将使用真实资金执行。
              请确保您了解相关风险。
            </p>
          </div>
        }
        onConfirm={() => handleChange(true)}
        okText="确认切换"
        cancelText="取消"
        okButtonProps={{ danger: true }}
      >
        {toggle}
      </Popconfirm>
    )
  }

  if (showConfirm && isLive) {
    return (
      <Popconfirm
        title="切换到模拟交易"
        description="切换后将使用模拟账户进行交易，不会影响真实资金。"
        onConfirm={() => handleChange(false)}
        okText="确认切换"
        cancelText="取消"
      >
        {toggle}
      </Popconfirm>
    )
  }

  return toggle
}

export const TradingModeToggle = memo(TradingModeToggleComponent)
export default TradingModeToggle
