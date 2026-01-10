/**
 * 持仓面板组件
 * PRD 4.18 分策略持仓管理
 */
import { useState } from 'react'
import { Button, Modal, InputNumber, Tooltip, Tag, Divider, message } from 'antd'
import {
  SwapOutlined,
  WarningOutlined,
  StockOutlined,
} from '@ant-design/icons'
import {
  AccountPositionSummary,
  PositionGroup,
  ConsolidatedPosition,
  StrategyPosition,
  PositionViewMode,
  formatPnL,
  formatPnLPct,
  formatCurrency,
  getPnLColorClass,
} from '../../types/position'

interface PositionPanelProps {
  summary: AccountPositionSummary
  onSellPosition: (positionId: string, quantity: number) => Promise<void>
  loading?: boolean
}

export default function PositionPanel({
  summary,
  onSellPosition,
  loading: _loading = false,
}: PositionPanelProps) {
  const [viewMode, setViewMode] = useState<PositionViewMode>('strategy')
  const [sellModalVisible, setSellModalVisible] = useState(false)
  const [selectedPosition, setSelectedPosition] = useState<StrategyPosition | null>(null)
  const [sellQuantity, setSellQuantity] = useState(0)
  const [selling, setSelling] = useState(false)

  // 打开卖出弹窗
  const openSellModal = (position: StrategyPosition) => {
    setSelectedPosition(position)
    setSellQuantity(position.quantity)
    setSellModalVisible(true)
  }

  // 确认卖出
  const handleSell = async () => {
    if (!selectedPosition || sellQuantity <= 0) return

    setSelling(true)
    try {
      await onSellPosition(selectedPosition.position_id, sellQuantity)
      message.success(`已卖出 ${sellQuantity} 股 ${selectedPosition.symbol}`)
      setSellModalVisible(false)
    } catch (error: any) {
      message.error(error.message || '卖出失败')
    } finally {
      setSelling(false)
    }
  }

  return (
    <div className="bg-dark-card rounded-lg overflow-hidden">
      {/* 头部 */}
      <div className="px-4 py-3 border-b border-gray-700 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <StockOutlined className="text-xl text-blue-400" />
          <span className="text-white font-medium text-lg">持仓管理</span>
        </div>

        {/* 视图切换 */}
        <div className="flex items-center gap-1 bg-gray-800 rounded-lg p-1">
          <button
            className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
              viewMode === 'strategy'
                ? 'bg-blue-600 text-white'
                : 'text-gray-400 hover:text-white'
            }`}
            onClick={() => setViewMode('strategy')}
          >
            按策略
          </button>
          <button
            className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
              viewMode === 'symbol'
                ? 'bg-blue-600 text-white'
                : 'text-gray-400 hover:text-white'
            }`}
            onClick={() => setViewMode('symbol')}
          >
            按股票
          </button>
        </div>
      </div>

      {/* 账户汇总 */}
      <div className="px-4 py-3 border-b border-gray-700">
        <div className="grid grid-cols-4 gap-4">
          <div>
            <div className="text-gray-500 text-xs mb-1">总市值</div>
            <div className="text-white text-lg font-mono">
              {formatCurrency(summary.total_market_value)}
            </div>
          </div>
          <div>
            <div className="text-gray-500 text-xs mb-1">现金</div>
            <div className="text-white text-lg font-mono">
              {formatCurrency(summary.total_cash)}
            </div>
          </div>
          <div>
            <div className="text-gray-500 text-xs mb-1">总权益</div>
            <div className="text-white text-lg font-mono">
              {formatCurrency(summary.total_equity)}
            </div>
          </div>
          <div>
            <div className="text-gray-500 text-xs mb-1">浮动盈亏</div>
            <div className={`text-lg font-mono ${getPnLColorClass(summary.total_unrealized_pnl)}`}>
              {formatPnL(summary.total_unrealized_pnl)}
              <span className="text-sm ml-1">
                ({formatPnLPct(summary.total_unrealized_pnl_pct)})
              </span>
            </div>
          </div>
        </div>

        {/* 组合 Beta */}
        {summary.portfolio_beta && (
          <div className="mt-2 flex items-center gap-2">
            <span className="text-gray-500 text-xs">组合Beta:</span>
            <span className="text-white text-sm font-mono">{summary.portfolio_beta}</span>
          </div>
        )}
      </div>

      {/* 集中度警告 */}
      {summary.concentration_warnings.length > 0 && (
        <div className="px-4 py-2 border-b border-gray-700 bg-yellow-500/5">
          {summary.concentration_warnings.map((warning, i) => (
            <div key={i} className="flex items-center gap-2 text-yellow-400 text-sm py-1">
              <WarningOutlined />
              <span>{warning}</span>
            </div>
          ))}
        </div>
      )}

      {/* 持仓列表 */}
      <div className="max-h-96 overflow-y-auto">
        {viewMode === 'strategy' ? (
          <StrategyView
            groups={summary.groups}
            onSellPosition={openSellModal}
          />
        ) : (
          <SymbolView positions={summary.consolidated} />
        )}
      </div>

      {/* 卖出弹窗 */}
      <Modal
        title={`卖出 ${selectedPosition?.symbol}`}
        open={sellModalVisible}
        onCancel={() => setSellModalVisible(false)}
        onOk={handleSell}
        okText="确认卖出"
        cancelText="取消"
        okButtonProps={{
          loading: selling,
          danger: true,
        }}
      >
        {selectedPosition && (
          <div className="space-y-4 py-2">
            <div className="flex justify-between text-gray-400">
              <span>策略</span>
              <span className="text-white">
                {selectedPosition.strategy_name || '手动交易'}
              </span>
            </div>
            <div className="flex justify-between text-gray-400">
              <span>持仓数量</span>
              <span className="text-white">{selectedPosition.quantity} 股</span>
            </div>
            <div className="flex justify-between text-gray-400">
              <span>当前价格</span>
              <span className="text-white">
                ${selectedPosition.current_price.toFixed(2)}
              </span>
            </div>
            <Divider className="my-3" />
            <div>
              <div className="text-gray-400 mb-2">卖出数量</div>
              <InputNumber
                value={sellQuantity}
                onChange={(v) => setSellQuantity(v || 0)}
                min={1}
                max={selectedPosition.quantity}
                style={{ width: '100%' }}
                size="large"
              />
              <div className="flex gap-2 mt-2">
                {[25, 50, 75, 100].map((pct) => (
                  <button
                    key={pct}
                    className="flex-1 py-1 rounded bg-gray-700 text-gray-300 text-sm hover:bg-gray-600"
                    onClick={() =>
                      setSellQuantity(Math.floor(selectedPosition.quantity * pct / 100))
                    }
                  >
                    {pct}%
                  </button>
                ))}
              </div>
            </div>
            <div className="flex justify-between text-gray-400 pt-2">
              <span>预估金额</span>
              <span className="text-white text-lg">
                ${(sellQuantity * selectedPosition.current_price).toLocaleString(
                  undefined,
                  { minimumFractionDigits: 2, maximumFractionDigits: 2 }
                )}
              </span>
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}

// 策略视图
function StrategyView({
  groups,
  onSellPosition,
}: {
  groups: PositionGroup[]
  onSellPosition: (position: StrategyPosition) => void
}) {
  return (
    <div className="divide-y divide-gray-800">
      {groups.map((group) => (
        <div key={group.strategy_id || 'manual'} className="p-3">
          {/* 策略头部 */}
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <Tag color={group.strategy_id ? 'blue' : 'default'}>
                {group.strategy_name}
              </Tag>
              <span className="text-gray-500 text-xs">
                {group.position_count} 个持仓
              </span>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-gray-400 text-sm">
                {formatCurrency(group.total_market_value)}
              </span>
              <span
                className={`text-sm font-medium ${getPnLColorClass(group.total_unrealized_pnl)}`}
              >
                {formatPnL(group.total_unrealized_pnl)}
              </span>
            </div>
          </div>

          {/* 持仓列表 */}
          <div className="space-y-1">
            {group.positions.map((pos) => (
              <div
                key={pos.position_id}
                className="flex items-center justify-between py-2 px-2 rounded hover:bg-gray-800/50"
              >
                <div className="flex items-center gap-3">
                  <span className="text-white font-medium w-16">{pos.symbol}</span>
                  <span className="text-gray-400 text-sm">{pos.quantity}股</span>
                </div>
                <div className="flex items-center gap-4">
                  <div className="text-right">
                    <div className="text-white text-sm">
                      ${pos.current_price.toFixed(2)}
                    </div>
                    <div className="text-gray-500 text-xs">
                      成本 ${pos.avg_cost.toFixed(2)}
                    </div>
                  </div>
                  <div className={`text-right w-24 ${getPnLColorClass(pos.unrealized_pnl)}`}>
                    <div className="text-sm font-medium">
                      {formatPnL(pos.unrealized_pnl)}
                    </div>
                    <div className="text-xs">
                      {formatPnLPct(pos.unrealized_pnl_pct)}
                    </div>
                  </div>
                  <Button
                    size="small"
                    danger
                    onClick={() => onSellPosition(pos)}
                  >
                    卖出
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}

      {groups.length === 0 && (
        <div className="p-8 text-center text-gray-500">
          暂无持仓
        </div>
      )}
    </div>
  )
}

// 股票视图
function SymbolView({ positions }: { positions: ConsolidatedPosition[] }) {
  const [expandedSymbol, setExpandedSymbol] = useState<string | null>(null)

  return (
    <div className="divide-y divide-gray-800">
      {positions.map((pos) => (
        <div key={pos.symbol} className="p-3">
          {/* 股票头部 */}
          <div
            className="flex items-center justify-between cursor-pointer hover:bg-gray-800/30 -mx-3 px-3 py-1 rounded"
            onClick={() =>
              setExpandedSymbol(expandedSymbol === pos.symbol ? null : pos.symbol)
            }
          >
            <div className="flex items-center gap-3">
              <span className="text-white font-semibold text-lg">{pos.symbol}</span>
              <span className="text-gray-400">{pos.total_quantity}股</span>
              {pos.concentration_pct > 20 && (
                <Tooltip title={`占比 ${pos.concentration_pct.toFixed(1)}%`}>
                  <WarningOutlined className="text-yellow-400" />
                </Tooltip>
              )}
            </div>
            <div className="flex items-center gap-4">
              <div className="text-right">
                <div className="text-white">${pos.current_price.toFixed(2)}</div>
                <div className="text-gray-500 text-xs">
                  均价 ${pos.weighted_avg_cost.toFixed(2)}
                </div>
              </div>
              <div className={`text-right w-28 ${getPnLColorClass(pos.total_unrealized_pnl)}`}>
                <div className="font-medium">{formatPnL(pos.total_unrealized_pnl)}</div>
                <div className="text-sm">{formatPnLPct(pos.total_unrealized_pnl_pct)}</div>
              </div>
              <div className="text-gray-500 text-sm">
                占 {pos.concentration_pct.toFixed(1)}%
              </div>
              <SwapOutlined
                className={`text-gray-500 transition-transform ${
                  expandedSymbol === pos.symbol ? 'rotate-90' : ''
                }`}
              />
            </div>
          </div>

          {/* 来源分解 */}
          {expandedSymbol === pos.symbol && (
            <div className="mt-2 ml-4 space-y-1">
              {pos.sources.map((source, i) => (
                <div
                  key={i}
                  className="flex items-center justify-between py-1.5 px-2 rounded bg-gray-800/30"
                >
                  <div className="flex items-center gap-2">
                    <Tag className="text-xs" color={source.strategy_id ? 'blue' : 'default'}>
                      {source.strategy_name}
                    </Tag>
                    <span className="text-gray-400 text-sm">{source.quantity}股</span>
                  </div>
                  <div className={`text-sm ${getPnLColorClass(source.pnl)}`}>
                    {formatPnL(source.pnl)}
                    <span className="text-gray-500 ml-1">
                      ({formatPnLPct(source.pnl_pct)})
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      ))}

      {positions.length === 0 && (
        <div className="p-8 text-center text-gray-500">
          暂无持仓
        </div>
      )}
    </div>
  )
}
