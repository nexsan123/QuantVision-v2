/**
 * 金融级 UI 组件库
 * UI 优化 Phase 2: 专业金融数据展示组件
 *
 * 组件列表:
 * - PriceTicker: 实时价格行情器
 * - PortfolioCard: 组合信息卡片
 * - MarketStatus: 市场状态指示器
 * - PnLDisplay: 盈亏显示组件
 * - TrendIndicator: 趋势指示器
 * - RiskBadge: 风险等级徽章
 */

import { memo, useMemo } from 'react'
import { Tooltip, Progress } from 'antd'
import {
  CaretUpOutlined,
  CaretDownOutlined,
  MinusOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
} from '@ant-design/icons'

// ==================== 价格行情器 ====================

interface PriceTickerProps {
  symbol: string
  price: number
  change: number
  changePercent: number
  volume?: number
  high?: number
  low?: number
  previousClose?: number
  compact?: boolean
  onClick?: () => void
}

export const PriceTicker = memo(function PriceTicker({
  symbol,
  price,
  change,
  changePercent,
  volume,
  high,
  low,
  previousClose,
  compact = false,
  onClick,
}: PriceTickerProps) {
  const isPositive = change >= 0
  const colorClass = isPositive ? 'text-green-400' : 'text-red-400'
  const bgClass = isPositive ? 'bg-green-900/20' : 'bg-red-900/20'
  const borderClass = isPositive ? 'border-green-800/50' : 'border-red-800/50'

  if (compact) {
    return (
      <div
        className={`flex items-center gap-2 px-2 py-1 rounded ${bgClass} cursor-pointer hover:brightness-110 transition-all`}
        onClick={onClick}
      >
        <span className="font-medium text-white text-sm">{symbol}</span>
        <span className="font-mono text-sm text-white">${price.toFixed(2)}</span>
        <span className={`text-xs font-mono ${colorClass}`}>
          {isPositive ? '+' : ''}{changePercent.toFixed(2)}%
        </span>
      </div>
    )
  }

  return (
    <div
      className={`p-3 rounded-lg border ${borderClass} ${bgClass} cursor-pointer hover:brightness-110 transition-all`}
      onClick={onClick}
    >
      {/* 第一行: 代码 + 价格 */}
      <div className="flex items-center justify-between mb-2">
        <span className="font-bold text-white text-lg">{symbol}</span>
        <div className="text-right">
          <span className="font-mono text-xl text-white">${price.toFixed(2)}</span>
        </div>
      </div>

      {/* 第二行: 涨跌 */}
      <div className="flex items-center justify-between mb-2">
        <div className={`flex items-center gap-1 ${colorClass}`}>
          {isPositive ? <CaretUpOutlined /> : <CaretDownOutlined />}
          <span className="font-mono">
            {isPositive ? '+' : ''}{change.toFixed(2)}
          </span>
          <span className="font-mono">
            ({isPositive ? '+' : ''}{changePercent.toFixed(2)}%)
          </span>
        </div>
        {previousClose && (
          <Tooltip title="前收盘价">
            <span className="text-gray-500 text-xs font-mono">
              前: ${previousClose.toFixed(2)}
            </span>
          </Tooltip>
        )}
      </div>

      {/* 第三行: 高低点 + 成交量 */}
      {(high || low || volume) && (
        <div className="flex items-center justify-between text-xs text-gray-400">
          <div className="flex gap-3">
            {high && (
              <span>
                高 <span className="text-green-400 font-mono">${high.toFixed(2)}</span>
              </span>
            )}
            {low && (
              <span>
                低 <span className="text-red-400 font-mono">${low.toFixed(2)}</span>
              </span>
            )}
          </div>
          {volume && (
            <span>
              量 <span className="text-white font-mono">{formatVolume(volume)}</span>
            </span>
          )}
        </div>
      )}
    </div>
  )
})

// ==================== 组合信息卡片 ====================

interface PortfolioCardProps {
  title: string
  value: number
  change?: number
  changePercent?: number
  subtitle?: string
  icon?: React.ReactNode
  trend?: 'up' | 'down' | 'neutral'
  loading?: boolean
}

export const PortfolioCard = memo(function PortfolioCard({
  title,
  value,
  change,
  changePercent,
  subtitle,
  icon,
  trend,
  loading = false,
}: PortfolioCardProps) {
  const trendColors = useMemo(() => {
    if (trend === 'up' || (change && change > 0)) {
      return { text: 'text-green-400', bg: 'bg-green-900/20', icon: <CaretUpOutlined /> }
    }
    if (trend === 'down' || (change && change < 0)) {
      return { text: 'text-red-400', bg: 'bg-red-900/20', icon: <CaretDownOutlined /> }
    }
    return { text: 'text-gray-400', bg: 'bg-gray-800/50', icon: <MinusOutlined /> }
  }, [trend, change])

  if (loading) {
    return (
      <div className="p-4 rounded-lg bg-[#1a1a28] border border-gray-800 animate-pulse">
        <div className="h-4 w-20 bg-gray-700 rounded mb-3" />
        <div className="h-8 w-32 bg-gray-700 rounded mb-2" />
        <div className="h-3 w-24 bg-gray-700 rounded" />
      </div>
    )
  }

  return (
    <div className="p-4 rounded-lg bg-[#1a1a28] border border-gray-800 hover:border-gray-700 transition-colors">
      {/* 标题行 */}
      <div className="flex items-center justify-between mb-2">
        <span className="text-gray-400 text-sm">{title}</span>
        {icon && <span className="text-gray-500">{icon}</span>}
      </div>

      {/* 数值 */}
      <div className="flex items-baseline gap-2 mb-1">
        <span className="text-2xl font-bold text-white font-mono">
          ${formatLargeNumber(value)}
        </span>
        {(change !== undefined || changePercent !== undefined) && (
          <span className={`flex items-center text-sm font-mono ${trendColors.text}`}>
            {trendColors.icon}
            {change !== undefined && (
              <span>{change >= 0 ? '+' : ''}{formatLargeNumber(change)}</span>
            )}
            {changePercent !== undefined && (
              <span className="ml-1">({changePercent >= 0 ? '+' : ''}{changePercent.toFixed(2)}%)</span>
            )}
          </span>
        )}
      </div>

      {/* 副标题 */}
      {subtitle && (
        <div className="text-xs text-gray-500">{subtitle}</div>
      )}
    </div>
  )
})

// ==================== 市场状态指示器 ====================

interface MarketStatusProps {
  isOpen: boolean
  nextOpen?: string
  nextClose?: string
  showTime?: boolean
}

export const MarketStatus = memo(function MarketStatus({
  isOpen,
  nextOpen,
  nextClose,
  showTime = true,
}: MarketStatusProps) {
  const statusConfig = useMemo(() => {
    if (isOpen) {
      return {
        text: '交易中',
        color: 'text-green-400',
        bgColor: 'bg-green-900/30',
        borderColor: 'border-green-800/50',
        icon: <CheckCircleOutlined className="text-green-400" />,
        pulse: true,
      }
    }
    return {
      text: '已休市',
      color: 'text-gray-400',
      bgColor: 'bg-gray-800/30',
      borderColor: 'border-gray-700/50',
      icon: <ClockCircleOutlined className="text-gray-400" />,
      pulse: false,
    }
  }, [isOpen])

  return (
    <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full border ${statusConfig.borderColor} ${statusConfig.bgColor}`}>
      <div className="flex items-center gap-1.5">
        {statusConfig.pulse && (
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75" />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500" />
          </span>
        )}
        {!statusConfig.pulse && statusConfig.icon}
        <span className={`text-sm font-medium ${statusConfig.color}`}>
          {statusConfig.text}
        </span>
      </div>
      {showTime && (
        <Tooltip title={isOpen ? `休市时间: ${nextClose}` : `开盘时间: ${nextOpen}`}>
          <span className="text-xs text-gray-500">
            {isOpen ? nextClose : nextOpen}
          </span>
        </Tooltip>
      )}
    </div>
  )
})

// ==================== 盈亏显示组件 ====================

interface PnLDisplayProps {
  value: number
  percent?: number
  size?: 'sm' | 'md' | 'lg' | 'xl'
  showIcon?: boolean
  showBackground?: boolean
  label?: string
}

export const PnLDisplay = memo(function PnLDisplay({
  value,
  percent,
  size = 'md',
  showIcon = true,
  showBackground = false,
  label,
}: PnLDisplayProps) {
  const isPositive = value >= 0
  const colorClass = isPositive ? 'text-green-400' : 'text-red-400'
  const bgClass = showBackground
    ? isPositive ? 'bg-green-900/20 px-2 py-1 rounded' : 'bg-red-900/20 px-2 py-1 rounded'
    : ''

  const sizeClasses = {
    sm: 'text-sm',
    md: 'text-base',
    lg: 'text-lg',
    xl: 'text-2xl font-bold',
  }

  return (
    <div className={`flex flex-col ${bgClass}`}>
      {label && <span className="text-xs text-gray-500 mb-0.5">{label}</span>}
      <div className={`flex items-center gap-1 ${colorClass} ${sizeClasses[size]}`}>
        {showIcon && (
          isPositive ? <CaretUpOutlined className="text-xs" /> : <CaretDownOutlined className="text-xs" />
        )}
        <span className="font-mono">
          {isPositive ? '+' : ''}${Math.abs(value).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
        </span>
        {percent !== undefined && (
          <span className="text-xs opacity-75">
            ({isPositive ? '+' : ''}{percent.toFixed(2)}%)
          </span>
        )}
      </div>
    </div>
  )
})

// ==================== 趋势指示器 ====================

interface TrendIndicatorProps {
  value: number
  periods?: number
  label?: string
  showBar?: boolean
}

export const TrendIndicator = memo(function TrendIndicator({
  value,
  periods = 5,
  label,
  showBar = true,
}: TrendIndicatorProps) {
  const strength = useMemo(() => {
    const absValue = Math.abs(value)
    if (absValue >= 3) return { level: 'strong', bars: 5 }
    if (absValue >= 2) return { level: 'moderate', bars: 4 }
    if (absValue >= 1) return { level: 'mild', bars: 3 }
    if (absValue >= 0.5) return { level: 'weak', bars: 2 }
    return { level: 'flat', bars: 1 }
  }, [value])

  const isPositive = value >= 0
  const colorClass = isPositive ? 'bg-green-500' : 'bg-red-500'
  const textColor = isPositive ? 'text-green-400' : 'text-red-400'

  return (
    <div className="flex items-center gap-2">
      {label && <span className="text-xs text-gray-500">{label}</span>}
      <div className={`flex items-center gap-0.5 ${textColor}`}>
        {isPositive ? <CaretUpOutlined /> : <CaretDownOutlined />}
        <span className="text-xs font-medium">{value.toFixed(2)}%</span>
      </div>
      {showBar && (
        <div className="flex items-end gap-0.5 h-4">
          {Array.from({ length: periods }).map((_, i) => (
            <div
              key={i}
              className={`w-1 rounded-sm transition-all ${
                i < strength.bars ? colorClass : 'bg-gray-700'
              }`}
              style={{ height: `${(i + 1) * 20}%` }}
            />
          ))}
        </div>
      )}
    </div>
  )
})

// ==================== 风险等级徽章 ====================

interface RiskBadgeProps {
  level: 'low' | 'medium' | 'high' | 'critical'
  showIcon?: boolean
  size?: 'sm' | 'md'
}

export const RiskBadge = memo(function RiskBadge({
  level,
  showIcon = true,
  size = 'md',
}: RiskBadgeProps) {
  const config = useMemo(() => {
    switch (level) {
      case 'low':
        return { text: '低风险', color: 'text-green-400', bg: 'bg-green-900/30', border: 'border-green-800/50' }
      case 'medium':
        return { text: '中风险', color: 'text-yellow-400', bg: 'bg-yellow-900/30', border: 'border-yellow-800/50' }
      case 'high':
        return { text: '高风险', color: 'text-orange-400', bg: 'bg-orange-900/30', border: 'border-orange-800/50' }
      case 'critical':
        return { text: '极高风险', color: 'text-red-400', bg: 'bg-red-900/30', border: 'border-red-800/50' }
    }
  }, [level])

  const sizeClass = size === 'sm' ? 'text-xs px-1.5 py-0.5' : 'text-sm px-2 py-1'

  return (
    <span className={`inline-flex items-center gap-1 rounded-full border ${config.border} ${config.bg} ${config.color} ${sizeClass}`}>
      {showIcon && <ExclamationCircleOutlined className="text-xs" />}
      {config.text}
    </span>
  )
})

// ==================== 权重进度条 ====================

interface WeightBarProps {
  value: number
  max?: number
  threshold?: number
  showValue?: boolean
  size?: 'sm' | 'md'
}

export const WeightBar = memo(function WeightBar({
  value,
  max = 100,
  threshold = 20,
  showValue = true,
  size = 'md',
}: WeightBarProps) {
  const percent = Math.min((value / max) * 100, 100)
  const isWarning = percent > threshold

  return (
    <div className="flex items-center gap-2">
      <Progress
        percent={percent}
        size="small"
        showInfo={false}
        strokeColor={isWarning ? '#faad14' : '#1890ff'}
        trailColor="#1f1f3a"
        className={size === 'sm' ? 'w-16' : 'w-24'}
      />
      {showValue && (
        <span className={`font-mono ${size === 'sm' ? 'text-xs' : 'text-sm'} ${isWarning ? 'text-yellow-400' : 'text-gray-400'}`}>
          {value.toFixed(1)}%
        </span>
      )}
    </div>
  )
})

// ==================== 工具函数 ====================

function formatLargeNumber(num: number): string {
  const absNum = Math.abs(num)
  if (absNum >= 1e9) return (num / 1e9).toFixed(2) + 'B'
  if (absNum >= 1e6) return (num / 1e6).toFixed(2) + 'M'
  if (absNum >= 1e3) return (num / 1e3).toFixed(2) + 'K'
  return num.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function formatVolume(vol: number): string {
  if (vol >= 1e9) return (vol / 1e9).toFixed(1) + 'B'
  if (vol >= 1e6) return (vol / 1e6).toFixed(1) + 'M'
  if (vol >= 1e3) return (vol / 1e3).toFixed(1) + 'K'
  return vol.toString()
}

// ==================== 导出 ====================

export default {
  PriceTicker,
  PortfolioCard,
  MarketStatus,
  PnLDisplay,
  TrendIndicator,
  RiskBadge,
  WeightBar,
}
