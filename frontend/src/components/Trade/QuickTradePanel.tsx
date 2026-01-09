/**
 * 快速交易面板组件
 * PRD 4.16 实时交易监控界面
 */
import { useState, useEffect } from 'react'
import {
  InputNumber,
  Button,
  Radio,
  message,
  Divider,
} from 'antd'
import {
  ThunderboltOutlined,
  DollarOutlined,
  WarningOutlined,
} from '@ant-design/icons'

interface PositionInfo {
  quantity: number
  avgCost: number
  pnl: number
  pnlPct: number
}

interface QuickTradePanelProps {
  symbol: string
  price: number
  position?: PositionInfo
  onBuy: (quantity: number, orderType: string, price?: number) => Promise<void>
  onSell: (quantity: number, orderType: string, price?: number) => Promise<void>
  loading?: boolean
  pdtWarning?: string
}

// 快速数量选项
const QUICK_QUANTITIES = [100, 500, 1000, 2000]
// 卖出百分比选项
const SELL_PERCENTAGES = [25, 50, 75, 100]

export default function QuickTradePanel({
  symbol,
  price,
  position,
  onBuy,
  onSell,
  loading = false,
  pdtWarning,
}: QuickTradePanelProps) {
  const [activeTab, setActiveTab] = useState<'buy' | 'sell'>('buy')
  const [quantity, setQuantity] = useState(100)
  const [orderType, setOrderType] = useState<'market' | 'limit'>('market')
  const [limitPrice, setLimitPrice] = useState(price)
  const [submitting, setSubmitting] = useState(false)

  // 价格变化时更新限价
  useEffect(() => {
    if (orderType === 'limit') {
      setLimitPrice(price)
    }
  }, [price, orderType])

  // 计算预估金额
  const estimatedAmount = quantity * (orderType === 'limit' ? limitPrice : price)

  // 提交订单
  const handleSubmit = async () => {
    if (quantity <= 0) {
      message.warning('请输入有效数量')
      return
    }

    setSubmitting(true)
    try {
      if (activeTab === 'buy') {
        await onBuy(
          quantity,
          orderType,
          orderType === 'limit' ? limitPrice : undefined
        )
        message.success('买入订单已提交')
      } else {
        await onSell(
          quantity,
          orderType,
          orderType === 'limit' ? limitPrice : undefined
        )
        message.success('卖出订单已提交')
      }
    } catch (error: any) {
      message.error(error.message || '订单提交失败')
    } finally {
      setSubmitting(false)
    }
  }

  // 按百分比设置卖出数量
  const handleSellPercentage = (pct: number) => {
    if (position) {
      setQuantity(Math.floor(position.quantity * pct / 100))
    }
  }

  return (
    <div className="bg-dark-card rounded-lg overflow-hidden">
      {/* 头部 */}
      <div className="px-4 py-3 border-b border-gray-700 flex items-center gap-2">
        <ThunderboltOutlined className="text-xl text-yellow-400" />
        <span className="text-white font-medium">快速交易</span>
      </div>

      {/* 股票信息 */}
      <div className="px-4 py-3 border-b border-gray-700">
        <div className="flex items-center justify-between">
          <span className="text-white font-semibold text-lg">{symbol}</span>
          <span className="text-white text-xl font-mono">${price.toFixed(2)}</span>
        </div>
      </div>

      {/* 买入/卖出切换 */}
      <div className="flex border-b border-gray-700">
        <button
          className={`flex-1 py-3 text-center font-medium transition-colors ${
            activeTab === 'buy'
              ? 'bg-green-600 text-white'
              : 'text-gray-400 hover:text-white hover:bg-gray-800'
          }`}
          onClick={() => setActiveTab('buy')}
        >
          买入
        </button>
        <button
          className={`flex-1 py-3 text-center font-medium transition-colors ${
            activeTab === 'sell'
              ? 'bg-red-600 text-white'
              : 'text-gray-400 hover:text-white hover:bg-gray-800'
          } ${!position ? 'opacity-50 cursor-not-allowed' : ''}`}
          onClick={() => position && setActiveTab('sell')}
          disabled={!position}
        >
          卖出
        </button>
      </div>

      <div className="p-4 space-y-4">
        {/* PDT 警告 */}
        {pdtWarning && (
          <div className="flex items-center gap-2 p-3 rounded-lg bg-yellow-500/10 border border-yellow-500/30">
            <WarningOutlined className="text-yellow-400" />
            <span className="text-yellow-400 text-sm">{pdtWarning}</span>
          </div>
        )}

        {/* 订单类型 */}
        <div>
          <div className="text-gray-400 text-sm mb-2">订单类型</div>
          <Radio.Group
            value={orderType}
            onChange={(e) => setOrderType(e.target.value)}
            className="w-full"
          >
            <div className="grid grid-cols-2 gap-2">
              <Radio.Button
                value="market"
                className="text-center"
                style={{ width: '100%' }}
              >
                市价
              </Radio.Button>
              <Radio.Button
                value="limit"
                className="text-center"
                style={{ width: '100%' }}
              >
                限价
              </Radio.Button>
            </div>
          </Radio.Group>
        </div>

        {/* 限价输入 */}
        {orderType === 'limit' && (
          <div>
            <div className="text-gray-400 text-sm mb-2">限价</div>
            <InputNumber
              value={limitPrice}
              onChange={(v) => setLimitPrice(v || price)}
              min={0.01}
              step={0.01}
              precision={2}
              prefix={<DollarOutlined className="text-gray-500" />}
              style={{ width: '100%' }}
              size="large"
            />
          </div>
        )}

        {/* 数量选择 */}
        <div>
          <div className="text-gray-400 text-sm mb-2">数量</div>

          {activeTab === 'buy' ? (
            <div className="grid grid-cols-4 gap-2 mb-2">
              {QUICK_QUANTITIES.map((q) => (
                <button
                  key={q}
                  className={`py-2 rounded text-sm font-medium transition-colors ${
                    quantity === q
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                  }`}
                  onClick={() => setQuantity(q)}
                >
                  {q}
                </button>
              ))}
            </div>
          ) : (
            <div className="grid grid-cols-4 gap-2 mb-2">
              {SELL_PERCENTAGES.map((pct) => (
                <button
                  key={pct}
                  className="py-2 rounded text-sm font-medium bg-gray-700 text-gray-300 hover:bg-gray-600 transition-colors"
                  onClick={() => handleSellPercentage(pct)}
                >
                  {pct}%
                </button>
              ))}
            </div>
          )}

          <InputNumber
            value={quantity}
            onChange={(v) => setQuantity(v || 0)}
            min={1}
            max={activeTab === 'sell' && position ? position.quantity : 1000000}
            style={{ width: '100%' }}
            size="large"
          />
        </div>

        <Divider className="my-3" style={{ borderColor: '#374151' }} />

        {/* 预估金额 */}
        <div className="flex items-center justify-between">
          <span className="text-gray-400">预估金额</span>
          <span className="text-white text-lg font-mono">
            ${estimatedAmount.toLocaleString(undefined, {
              minimumFractionDigits: 2,
              maximumFractionDigits: 2,
            })}
          </span>
        </div>

        {/* 持仓信息 */}
        {position && (
          <div className="p-3 rounded-lg bg-gray-800/50">
            <div className="flex items-center justify-between mb-1">
              <span className="text-gray-400 text-sm">当前持仓</span>
              <span className="text-white">{position.quantity} 股</span>
            </div>
            <div className="flex items-center justify-between mb-1">
              <span className="text-gray-400 text-sm">成本价</span>
              <span className="text-white">${position.avgCost.toFixed(2)}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-400 text-sm">浮动盈亏</span>
              <span
                className={`font-medium ${
                  position.pnl >= 0 ? 'text-green-400' : 'text-red-400'
                }`}
              >
                {position.pnl >= 0 ? '+' : ''}${position.pnl.toFixed(2)}
                <span className="text-sm ml-1">
                  ({position.pnlPct >= 0 ? '+' : ''}{position.pnlPct.toFixed(2)}%)
                </span>
              </span>
            </div>
          </div>
        )}

        {/* 提交按钮 */}
        <Button
          type="primary"
          size="large"
          block
          loading={submitting || loading}
          disabled={quantity <= 0}
          onClick={handleSubmit}
          className={
            activeTab === 'buy'
              ? 'bg-green-600 hover:bg-green-500 border-green-600'
              : 'bg-red-600 hover:bg-red-500 border-red-600'
          }
        >
          {submitting
            ? '处理中...'
            : activeTab === 'buy'
              ? '确认买入'
              : '确认卖出'}
        </Button>
      </div>
    </div>
  )
}
