/**
 * 持仓监控面板
 * Sprint 3 - F10: 实时持仓显示
 * Sprint 9 - T14: 集成 Alpaca 实时数据
 */
import { useState, useMemo } from 'react'
import { Progress, Tooltip, Spin, Button, message } from 'antd'
import { CaretUpOutlined, CaretDownOutlined, ReloadOutlined, CloseCircleOutlined } from '@ant-design/icons'
import { usePositions } from '../../hooks/useAccount'
import type { Position as AlpacaPosition } from '../../services/alpacaTrading'

interface PositionMonitorPanelProps {
  deploymentId: string
  onSymbolClick?: (symbol: string) => void
}

interface DisplayPosition {
  symbol: string
  qty: number
  avgPrice: number
  currentPrice: number
  pnl: number
  pnlPct: number
  weight: number
  dayChange: number
  dayChangePct: number
  side: 'long' | 'short'
  marketValue: number
}

// 转换 Alpaca 持仓到显示格式
function transformPosition(position: AlpacaPosition, totalValue: number): DisplayPosition {
  const qty = parseFloat(position.qty)
  const avgPrice = parseFloat(position.avg_entry_price)
  const currentPrice = parseFloat(position.current_price)
  const pnl = parseFloat(position.unrealized_pl)
  const pnlPct = parseFloat(position.unrealized_plpc)
  const marketValue = parseFloat(position.market_value)
  const dayChangePct = parseFloat(position.change_today)
  const lastPrice = parseFloat(position.lastday_price)
  const dayChange = currentPrice - lastPrice

  return {
    symbol: position.symbol,
    qty: Math.abs(qty),
    avgPrice,
    currentPrice,
    pnl,
    pnlPct,
    weight: totalValue > 0 ? Math.abs(marketValue) / totalValue : 0,
    dayChange,
    dayChangePct,
    side: position.side,
    marketValue: Math.abs(marketValue),
  }
}

export default function PositionMonitorPanel({ deploymentId: _deploymentId, onSymbolClick }: PositionMonitorPanelProps) {
  const { positions: alpacaPositions, loading, error, refresh, totalValue, totalPnL, closePosition, closeAllPositions } = usePositions()
  const [sortBy, setSortBy] = useState<'weight' | 'pnl' | 'dayChange'>('weight')
  const [closing, setClosing] = useState<string | null>(null)

  // 转换持仓数据
  const positions = useMemo(() => {
    return alpacaPositions.map(p => transformPosition(p, totalValue))
  }, [alpacaPositions, totalValue])

  // 排序
  const sortedPositions = [...positions].sort((a, b) => {
    if (sortBy === 'weight') return b.weight - a.weight
    if (sortBy === 'pnl') return b.pnl - a.pnl
    return b.dayChangePct - a.dayChangePct
  })

  // 平仓处理
  const handleClosePosition = async (symbol: string) => {
    setClosing(symbol)
    try {
      await closePosition(symbol)
      message.success(`${symbol} 已平仓`)
    } catch (err) {
      message.error(`平仓失败: ${(err as Error).message}`)
    } finally {
      setClosing(null)
    }
  }

  // 全部平仓
  const handleCloseAll = async () => {
    if (positions.length === 0) return
    try {
      await closeAllPositions()
      message.success('全部平仓成功')
    } catch (err) {
      message.error(`全部平仓失败: ${(err as Error).message}`)
    }
  }

  // 加载中
  if (loading && positions.length === 0) {
    return (
      <div className="h-full flex items-center justify-center">
        <Spin size="small" />
      </div>
    )
  }

  // 错误
  if (error && positions.length === 0) {
    return (
      <div className="h-full flex flex-col items-center justify-center text-gray-500">
        <div className="text-sm mb-2">加载失败</div>
        <Button size="small" onClick={refresh}>重试</Button>
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col">
      {/* 标题栏 */}
      <div className="px-3 py-2 border-b border-gray-800 flex items-center justify-between">
        <span className="text-sm font-medium text-white">持仓监控</span>
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-500">{positions.length} 只</span>
          <Button
            type="text"
            size="small"
            icon={<ReloadOutlined spin={loading} />}
            onClick={refresh}
            className="text-gray-400 hover:text-white"
          />
        </div>
      </div>

      {/* 汇总信息 */}
      <div className="px-3 py-2 border-b border-gray-800 bg-gray-900/30">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-xs text-gray-500">持仓市值</div>
            <div className="text-sm font-mono text-white">
              ${totalValue.toLocaleString(undefined, { minimumFractionDigits: 2 })}
            </div>
          </div>
          <div className="text-right">
            <div className="text-xs text-gray-500">持仓盈亏</div>
            <div className={`text-sm font-mono ${totalPnL >= 0 ? 'text-green-400' : 'text-red-400'}`}>
              {totalPnL >= 0 ? '+' : ''}${totalPnL.toFixed(2)}
            </div>
          </div>
        </div>
        {positions.length > 0 && (
          <div className="mt-2 flex justify-end">
            <Button
              size="small"
              danger
              onClick={handleCloseAll}
              className="text-xs"
            >
              全部平仓
            </Button>
          </div>
        )}
      </div>

      {/* 排序选项 */}
      <div className="px-3 py-1.5 border-b border-gray-800 flex gap-2">
        <SortButton label="权重" active={sortBy === 'weight'} onClick={() => setSortBy('weight')} />
        <SortButton label="盈亏" active={sortBy === 'pnl'} onClick={() => setSortBy('pnl')} />
        <SortButton label="今日" active={sortBy === 'dayChange'} onClick={() => setSortBy('dayChange')} />
      </div>

      {/* 持仓列表 */}
      <div className="flex-1 overflow-y-auto">
        {positions.length === 0 ? (
          <div className="h-full flex items-center justify-center text-gray-500 text-sm">
            暂无持仓
          </div>
        ) : (
          sortedPositions.map(position => (
            <PositionItem
              key={position.symbol}
              position={position}
              onClose={handleClosePosition}
              closing={closing === position.symbol}
              onSymbolClick={onSymbolClick}
            />
          ))
        )}
      </div>
    </div>
  )
}

function SortButton({ label, active, onClick }: { label: string; active: boolean; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className={`px-2 py-0.5 rounded text-xs transition-colors ${
        active
          ? 'bg-blue-600 text-white'
          : 'text-gray-400 hover:text-white'
      }`}
    >
      {label}
    </button>
  )
}

interface PositionItemProps {
  position: DisplayPosition
  onClose: (symbol: string) => void
  closing: boolean
  onSymbolClick?: (symbol: string) => void
}

function PositionItem({ position, onClose, closing, onSymbolClick }: PositionItemProps) {
  const isPositivePnl = position.pnl >= 0
  const isPositiveDay = position.dayChange >= 0

  return (
    <div className="px-3 py-2 border-b border-gray-800/50 hover:bg-gray-800/30 transition-colors group">
      {/* 第一行: 股票代码 + 当前价格 */}
      <div className="flex items-center justify-between mb-1">
        <div className="flex items-center gap-2">
          <button
            className="text-sm font-medium text-white hover:text-blue-400 transition-colors cursor-pointer"
            onClick={() => onSymbolClick?.(position.symbol)}
          >
            {position.symbol}
          </button>
          <span className={`text-xs px-1 rounded ${position.side === 'long' ? 'bg-green-900/50 text-green-400' : 'bg-red-900/50 text-red-400'}`}>
            {position.side === 'long' ? '多' : '空'}
          </span>
          <span className="text-xs text-gray-500">{position.qty}股</span>
        </div>
        <div className="flex items-center gap-1">
          {isPositiveDay ? (
            <CaretUpOutlined className="text-green-400 text-xs" />
          ) : (
            <CaretDownOutlined className="text-red-400 text-xs" />
          )}
          <span className="text-sm font-mono text-white">
            ${position.currentPrice.toFixed(2)}
          </span>
          <Tooltip title="平仓">
            <Button
              type="text"
              size="small"
              icon={<CloseCircleOutlined />}
              loading={closing}
              onClick={() => onClose(position.symbol)}
              className="text-gray-500 hover:text-red-400 opacity-0 group-hover:opacity-100 transition-opacity ml-1"
            />
          </Tooltip>
        </div>
      </div>

      {/* 第二行: 盈亏 + 权重条 */}
      <div className="flex items-center justify-between mb-1">
        <Tooltip title={`成本: $${position.avgPrice.toFixed(2)}`}>
          <span className={`text-xs font-mono ${isPositivePnl ? 'text-green-400' : 'text-red-400'}`}>
            {isPositivePnl ? '+' : ''}${position.pnl.toFixed(2)}
            <span className="text-gray-500 ml-1">
              ({(position.pnlPct * 100).toFixed(2)}%)
            </span>
          </span>
        </Tooltip>
        <span className={`text-xs font-mono ${isPositiveDay ? 'text-green-400' : 'text-red-400'}`}>
          今日 {isPositiveDay ? '+' : ''}{(position.dayChangePct * 100).toFixed(2)}%
        </span>
      </div>

      {/* 第三行: 权重进度条 */}
      <div className="flex items-center gap-2">
        <Progress
          percent={position.weight * 100}
          size="small"
          showInfo={false}
          strokeColor={position.weight > 0.2 ? '#faad14' : '#1890ff'}
          trailColor="#1f1f3a"
          className="flex-1"
        />
        <span className="text-xs text-gray-500 w-10 text-right">
          {(position.weight * 100).toFixed(1)}%
        </span>
      </div>
    </div>
  )
}
