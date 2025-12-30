/**
 * 价格行情组件
 *
 * 带动画效果的实时价格显示
 */

import { memo, useEffect, useState } from 'react'
import { RiseOutlined, FallOutlined, MinusOutlined } from '@ant-design/icons'
import { PriceData } from '@/types/trading'

interface PriceTickerProps {
  data: PriceData
  size?: 'small' | 'medium' | 'large'
  showChange?: boolean
  showPercent?: boolean
}

function PriceTickerComponent({
  data,
  size = 'medium',
  showChange = true,
  showPercent = true,
}: PriceTickerProps) {
  const [flash, setFlash] = useState(false)

  // 价格变化动画
  useEffect(() => {
    if (data.animating) {
      setFlash(true)
      const timer = setTimeout(() => setFlash(false), 300)
      return () => clearTimeout(timer)
    }
  }, [data.animating, data.price])

  const isUp = data.direction === 'up'
  const isDown = data.direction === 'down'

  // 尺寸配置
  const sizeConfig = {
    small: {
      price: 'text-sm',
      change: 'text-xs',
      icon: 'text-xs',
    },
    medium: {
      price: 'text-base',
      change: 'text-sm',
      icon: 'text-sm',
    },
    large: {
      price: 'text-xl font-bold',
      change: 'text-base',
      icon: 'text-base',
    },
  }

  const config = sizeConfig[size]

  // 颜色配置
  const colorClass = isUp
    ? 'text-green-400'
    : isDown
    ? 'text-red-400'
    : 'text-gray-400'

  // 背景闪烁
  const flashClass = flash
    ? isUp
      ? 'bg-green-900/30'
      : isDown
      ? 'bg-red-900/30'
      : ''
    : ''

  // 方向图标
  const DirectionIcon = isUp
    ? RiseOutlined
    : isDown
    ? FallOutlined
    : MinusOutlined

  return (
    <div
      className={`
        inline-flex items-center gap-2 px-2 py-1 rounded transition-all duration-300
        ${flashClass}
      `}
    >
      {/* 股票代码 */}
      <span className={`font-medium text-gray-200 ${config.price}`}>
        {data.symbol}
      </span>

      {/* 价格 */}
      <span className={`font-mono ${config.price} ${colorClass}`}>
        ${data.price.toFixed(2)}
      </span>

      {/* 涨跌幅 */}
      {(showChange || showPercent) && (
        <span className={`flex items-center gap-1 ${config.change} ${colorClass}`}>
          <DirectionIcon className={config.icon} />
          {showChange && (
            <span>
              {isUp ? '+' : ''}{data.change.toFixed(2)}
            </span>
          )}
          {showPercent && (
            <span>
              ({isUp ? '+' : ''}{data.changePercent.toFixed(2)}%)
            </span>
          )}
        </span>
      )}
    </div>
  )
}

export const PriceTicker = memo(PriceTickerComponent)

// 价格网格组件
interface PriceGridProps {
  prices: Map<string, PriceData>
  maxItems?: number
}

function PriceGridComponent({ prices, maxItems = 10 }: PriceGridProps) {
  const priceList = Array.from(prices.values())
    .sort((a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime())
    .slice(0, maxItems)

  if (priceList.length === 0) {
    return (
      <div className="text-center text-gray-500 py-4">
        暂无价格数据
      </div>
    )
  }

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2">
      {priceList.map((price) => (
        <div
          key={price.symbol}
          className="bg-dark-card border border-dark-border rounded-lg p-3"
        >
          <PriceTicker data={price} size="medium" />
        </div>
      ))}
    </div>
  )
}

export const PriceGrid = memo(PriceGridComponent)
export default PriceTicker
