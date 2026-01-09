/**
 * 信号覆盖层组件
 * PRD 4.16 实时交易监控界面
 * 在图表上绘制交易信号、止盈止损线等
 */
import { useMemo } from 'react'

// 交易信号类型
export interface TradeSignal {
  type: 'buy' | 'sell'
  price: number
  time: number // Unix timestamp
  strength: number // 0-100
  reason: string
}

// 持仓信息
export interface PositionInfo {
  entryPrice: number
  quantity: number
  stopLoss?: number
  takeProfit?: number
}

interface SignalOverlayProps {
  signals: TradeSignal[]
  position?: PositionInfo
  chartHeight: number
  chartWidth: number
  priceRange: { min: number; max: number }
  timeRange: { start: number; end: number }
}

export default function SignalOverlay({
  signals,
  position,
  chartHeight,
  chartWidth,
  priceRange,
  timeRange,
}: SignalOverlayProps) {
  // 价格转 Y 坐标
  const priceToY = useMemo(() => {
    return (price: number) => {
      const { min, max } = priceRange
      if (max === min) return chartHeight / 2
      return chartHeight - ((price - min) / (max - min)) * chartHeight
    }
  }, [priceRange, chartHeight])

  // 时间转 X 坐标
  const timeToX = useMemo(() => {
    return (time: number) => {
      const { start, end } = timeRange
      if (end === start) return chartWidth / 2
      return ((time - start) / (end - start)) * chartWidth
    }
  }, [timeRange, chartWidth])

  return (
    <svg
      className="signal-overlay pointer-events-none"
      width={chartWidth}
      height={chartHeight}
      style={{ position: 'absolute', top: 0, left: 0 }}
    >
      <defs>
        {/* 止盈渐变 */}
        <linearGradient id="takeProfitGradient" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stopColor="#22c55e" stopOpacity="0.1" />
          <stop offset="50%" stopColor="#22c55e" stopOpacity="0.3" />
          <stop offset="100%" stopColor="#22c55e" stopOpacity="0.1" />
        </linearGradient>
        {/* 止损渐变 */}
        <linearGradient id="stopLossGradient" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stopColor="#ef4444" stopOpacity="0.1" />
          <stop offset="50%" stopColor="#ef4444" stopOpacity="0.3" />
          <stop offset="100%" stopColor="#ef4444" stopOpacity="0.1" />
        </linearGradient>
      </defs>

      {/* 止盈线 */}
      {position?.takeProfit && (
        <g className="take-profit-line">
          <line
            x1={0}
            y1={priceToY(position.takeProfit)}
            x2={chartWidth}
            y2={priceToY(position.takeProfit)}
            stroke="#22c55e"
            strokeWidth={2}
            strokeDasharray="8 4"
          />
          <rect
            x={chartWidth - 120}
            y={priceToY(position.takeProfit) - 12}
            width={115}
            height={24}
            rx={4}
            fill="rgba(34, 197, 94, 0.2)"
          />
          <text
            x={chartWidth - 115}
            y={priceToY(position.takeProfit) + 4}
            fill="#22c55e"
            fontSize={12}
            fontFamily="monospace"
          >
            🎯 止盈 ${position.takeProfit.toFixed(2)}
          </text>
        </g>
      )}

      {/* 止损线 */}
      {position?.stopLoss && (
        <g className="stop-loss-line">
          <line
            x1={0}
            y1={priceToY(position.stopLoss)}
            x2={chartWidth}
            y2={priceToY(position.stopLoss)}
            stroke="#ef4444"
            strokeWidth={2}
            strokeDasharray="8 4"
          />
          <rect
            x={chartWidth - 120}
            y={priceToY(position.stopLoss) - 12}
            width={115}
            height={24}
            rx={4}
            fill="rgba(239, 68, 68, 0.2)"
          />
          <text
            x={chartWidth - 115}
            y={priceToY(position.stopLoss) + 4}
            fill="#ef4444"
            fontSize={12}
            fontFamily="monospace"
          >
            🛑 止损 ${position.stopLoss.toFixed(2)}
          </text>
        </g>
      )}

      {/* 入场价线 */}
      {position?.entryPrice && (
        <g className="entry-price-line">
          <line
            x1={0}
            y1={priceToY(position.entryPrice)}
            x2={chartWidth}
            y2={priceToY(position.entryPrice)}
            stroke="#3b82f6"
            strokeWidth={1}
            strokeDasharray="4 4"
          />
          <rect
            x={chartWidth - 110}
            y={priceToY(position.entryPrice) - 12}
            width={105}
            height={24}
            rx={4}
            fill="rgba(59, 130, 246, 0.2)"
          />
          <text
            x={chartWidth - 105}
            y={priceToY(position.entryPrice) + 4}
            fill="#3b82f6"
            fontSize={12}
            fontFamily="monospace"
          >
            入场 ${position.entryPrice.toFixed(2)}
          </text>
        </g>
      )}

      {/* 交易信号标记 */}
      {signals.map((signal, i) => {
        const x = timeToX(signal.time)
        const y = priceToY(signal.price)

        return (
          <g
            key={i}
            className={`signal-marker signal-${signal.type}`}
            transform={`translate(${x}, ${y})`}
          >
            {signal.type === 'buy' ? (
              // 买入信号 - 绿色上三角
              <>
                <polygon
                  points="0,-14 10,6 -10,6"
                  fill="#22c55e"
                  stroke="#fff"
                  strokeWidth={1}
                />
                <circle
                  cx={0}
                  cy={-14}
                  r={3}
                  fill="#fff"
                />
              </>
            ) : (
              // 卖出信号 - 红色下三角
              <>
                <polygon
                  points="0,14 10,-6 -10,-6"
                  fill="#ef4444"
                  stroke="#fff"
                  strokeWidth={1}
                />
                <circle
                  cx={0}
                  cy={14}
                  r={3}
                  fill="#fff"
                />
              </>
            )}

            {/* 信号强度指示 */}
            {signal.strength >= 80 && (
              <circle
                cx={0}
                cy={signal.type === 'buy' ? -20 : 20}
                r={4}
                fill="#fbbf24"
              >
                <animate
                  attributeName="opacity"
                  values="1;0.5;1"
                  dur="1s"
                  repeatCount="indefinite"
                />
              </circle>
            )}

            {/* 悬停提示 */}
            <title>
              {signal.type === 'buy' ? '买入信号' : '卖出信号'}: ${signal.price.toFixed(2)}
              {'\n'}强度: {signal.strength}%
              {'\n'}原因: {signal.reason}
            </title>
          </g>
        )
      })}

      {/* 持仓标记 */}
      {position && (
        <g className="position-marker">
          <circle
            cx={chartWidth - 30}
            cy={priceToY(position.entryPrice)}
            r={10}
            fill="#3b82f6"
            stroke="#fff"
            strokeWidth={2}
          />
          <text
            x={chartWidth - 30}
            y={priceToY(position.entryPrice) + 4}
            fill="#fff"
            fontSize={10}
            textAnchor="middle"
          >
            P
          </text>
        </g>
      )}
    </svg>
  )
}
