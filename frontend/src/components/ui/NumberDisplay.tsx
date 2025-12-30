import { useMemo } from 'react'

interface NumberDisplayProps {
  value: number | null | undefined
  type?: 'currency' | 'percent' | 'number' | 'ratio'
  precision?: number
  showSign?: boolean
  colorize?: boolean
  size?: 'sm' | 'md' | 'lg' | 'xl'
  className?: string
  prefix?: string
  suffix?: string
}

const sizeStyles = {
  sm: 'text-sm',
  md: 'text-base',
  lg: 'text-lg',
  xl: 'text-2xl font-semibold',
}

/**
 * 数字显示组件
 *
 * 支持:
 * - 货币格式 (带$符号)
 * - 百分比格式
 * - 普通数字
 * - 比率
 * - 颜色化显示 (正值绿色, 负值红色)
 */
export function NumberDisplay({
  value,
  type = 'number',
  precision = 2,
  showSign = false,
  colorize = false,
  size = 'md',
  className = '',
  prefix = '',
  suffix = '',
}: NumberDisplayProps) {
  const formatted = useMemo(() => {
    if (value === null || value === undefined || isNaN(value)) {
      return '--'
    }

    let result = ''
    const absValue = Math.abs(value)

    switch (type) {
      case 'currency':
        result = `$${absValue.toLocaleString('en-US', {
          minimumFractionDigits: precision,
          maximumFractionDigits: precision,
        })}`
        break
      case 'percent':
        result = `${(absValue * 100).toFixed(precision)}%`
        break
      case 'ratio':
        result = absValue.toFixed(precision)
        break
      default:
        result = absValue.toLocaleString('en-US', {
          minimumFractionDigits: precision,
          maximumFractionDigits: precision,
        })
    }

    if (showSign && value > 0) {
      result = '+' + result
    } else if (value < 0) {
      result = '-' + result
    }

    return prefix + result + suffix
  }, [value, type, precision, showSign, prefix, suffix])

  const colorClass = useMemo(() => {
    if (!colorize || value === null || value === undefined) return ''
    if (value > 0) return 'text-profit'
    if (value < 0) return 'text-loss'
    return ''
  }, [colorize, value])

  return (
    <span
      className={`font-mono tabular-nums ${sizeStyles[size]} ${colorClass} ${className}`}
    >
      {formatted}
    </span>
  )
}

export default NumberDisplay
