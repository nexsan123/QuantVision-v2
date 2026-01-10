/**
 * 信号列表组件
 * PRD 4.16.2
 */
import { useState } from 'react'
import { Tag, Button, Tooltip, Progress } from 'antd'
import {
  ShoppingCartOutlined,
  InfoCircleOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined,
} from '@ant-design/icons'
import {
  Signal,
  FactorTrigger,
  SIGNAL_TYPE_CONFIG,
  SIGNAL_STRENGTH_CONFIG,
  SIGNAL_STATUS_CONFIG,
  renderStars,
  formatPrice,
  formatPercent,
} from '../../types/signalRadar'

interface SignalListProps {
  signals: Signal[]
  onSignalClick?: (signal: Signal) => void
  onQuickOrder?: (signal: Signal) => void
}

export default function SignalList({
  signals,
  onSignalClick,
  onQuickOrder,
}: SignalListProps) {
  const [expandedKeys, setExpandedKeys] = useState<string[]>([])

  const renderFactorProgress = (factor: FactorTrigger) => {
    const pct = Math.min(100, factor.nearTriggerPct)
    let status: 'success' | 'active' | 'normal' | 'exception' = 'normal'
    if (factor.isSatisfied) {
      status = 'success'
    } else if (pct >= 80) {
      status = 'active'
    }

    return (
      <div key={factor.factorId} className="mb-2">
        <div className="flex justify-between text-xs mb-1">
          <span className="text-gray-400">{factor.factorName}</span>
          <span className="text-gray-300">
            {factor.currentValue.toFixed(2)} / {factor.threshold}
            <span className="text-gray-500 ml-1">
              ({factor.direction === 'below' ? '<' : '>'})
            </span>
          </span>
        </div>
        <Progress
          percent={pct}
          size="small"
          status={status}
          showInfo={false}
          strokeColor={factor.isSatisfied ? '#52c41a' : pct >= 80 ? '#faad14' : '#1890ff'}
        />
        <div className="text-right text-xs text-gray-500">
          {pct.toFixed(0)}%
          {factor.isSatisfied && <Tag color="green" className="ml-1 text-xs">已满足</Tag>}
          {!factor.isSatisfied && pct >= 80 && <Tag color="orange" className="ml-1 text-xs">接近</Tag>}
        </div>
      </div>
    )
  }

  const renderSignalCard = (signal: Signal) => {
    const typeConfig = SIGNAL_TYPE_CONFIG[signal.signalType]
    const strengthConfig = SIGNAL_STRENGTH_CONFIG[signal.signalStrength]
    const statusConfig = SIGNAL_STATUS_CONFIG[signal.status]

    return (
      <div
        className="bg-dark-hover rounded-lg p-3 mb-2 cursor-pointer hover:bg-dark-border transition-colors"
        onClick={() => onSignalClick?.(signal)}
      >
        {/* 头部: 股票信息 */}
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <span className="text-white font-bold">{signal.symbol}</span>
            <span className="text-gray-500 text-sm">{signal.companyName}</span>
            {signal.isHolding && (
              <Tag color="red" className="text-xs">持仓</Tag>
            )}
          </div>
          <div className="flex items-center gap-2">
            <Tooltip title={statusConfig.label}>
              <span>{statusConfig.emoji}</span>
            </Tooltip>
            <Tag color={typeConfig.color}>
              {typeConfig.icon} {typeConfig.label}
            </Tag>
          </div>
        </div>

        {/* 中部: 价格和评分 */}
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-4">
            <div>
              <div className="text-xs text-gray-500">当前价</div>
              <div className="text-white">{formatPrice(signal.currentPrice)}</div>
            </div>
            {signal.targetPrice && (
              <div>
                <div className="text-xs text-gray-500">目标价</div>
                <div className="text-green-400 flex items-center gap-1">
                  <ArrowUpOutlined className="text-xs" />
                  {formatPrice(signal.targetPrice)}
                </div>
              </div>
            )}
            {signal.stopLossPrice && (
              <div>
                <div className="text-xs text-gray-500">止损价</div>
                <div className="text-red-400 flex items-center gap-1">
                  <ArrowDownOutlined className="text-xs" />
                  {formatPrice(signal.stopLossPrice)}
                </div>
              </div>
            )}
          </div>
          <div className="text-right">
            <div className="flex items-center gap-1 justify-end">
              <span className="text-yellow-400">{renderStars(strengthConfig.stars)}</span>
              <span className="text-gray-500 text-xs">{strengthConfig.label}</span>
            </div>
            <div className="text-2xl font-bold text-white">{signal.signalScore}</div>
            <div className="text-xs text-gray-500">信号评分</div>
          </div>
        </div>

        {/* 预期收益 */}
        {signal.expectedReturnPct && (
          <div className="flex items-center justify-between text-sm mb-2">
            <span className="text-gray-500">预期收益</span>
            <span className={signal.expectedReturnPct >= 0 ? 'text-green-400' : 'text-red-400'}>
              {formatPercent(signal.expectedReturnPct)}
            </span>
          </div>
        )}

        {/* 操作按钮 */}
        <div className="flex gap-2 mt-3">
          {signal.signalType === 'buy' && !signal.isHolding && (
            <Button
              type="primary"
              size="small"
              icon={<ShoppingCartOutlined />}
              onClick={(e) => {
                e.stopPropagation()
                onQuickOrder?.(signal)
              }}
              className="flex-1"
            >
              快速下单
            </Button>
          )}
          {signal.signalType === 'sell' && signal.isHolding && (
            <Button
              danger
              size="small"
              icon={<ShoppingCartOutlined />}
              onClick={(e) => {
                e.stopPropagation()
                onQuickOrder?.(signal)
              }}
              className="flex-1"
            >
              卖出
            </Button>
          )}
          <Tooltip title="查看详情">
            <Button
              size="small"
              icon={<InfoCircleOutlined />}
              onClick={(e) => {
                e.stopPropagation()
                const newKeys = expandedKeys.includes(signal.signalId)
                  ? expandedKeys.filter(k => k !== signal.signalId)
                  : [...expandedKeys, signal.signalId]
                setExpandedKeys(newKeys)
              }}
            />
          </Tooltip>
        </div>
      </div>
    )
  }

  const renderExpandedContent = (signal: Signal) => (
    <div className="bg-dark-bg rounded p-3 mt-2">
      <div className="text-sm text-gray-400 mb-2">因子触发详情</div>
      {signal.triggeredFactors.length > 0 ? (
        signal.triggeredFactors.map(renderFactorProgress)
      ) : (
        <div className="text-gray-500 text-sm">暂无因子数据</div>
      )}
      <div className="mt-3 pt-3 border-t border-dark-border">
        <div className="flex justify-between text-xs text-gray-500">
          <span>信号时间</span>
          <span>{new Date(signal.signalTime).toLocaleString('zh-CN')}</span>
        </div>
        {signal.expiresAt && (
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>过期时间</span>
            <span>{new Date(signal.expiresAt).toLocaleString('zh-CN')}</span>
          </div>
        )}
      </div>
    </div>
  )

  return (
    <div className="space-y-2">
      {signals.map(signal => (
        <div key={signal.signalId}>
          {renderSignalCard(signal)}
          {expandedKeys.includes(signal.signalId) && renderExpandedContent(signal)}
        </div>
      ))}
    </div>
  )
}
