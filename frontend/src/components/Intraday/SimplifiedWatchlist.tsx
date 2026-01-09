/**
 * 简化监控列表组件
 * PRD 4.18.1 日内交易专用视图
 * 宽度仅100px，简化版
 */
import { PlusOutlined } from '@ant-design/icons'
import { SignalStatus } from '../../types/preMarket'

interface SimplifiedWatchlistProps {
  symbols: string[]
  currentSymbol: string
  onSelect: (symbol: string) => void
  signals: Record<string, SignalStatus>
}

export default function SimplifiedWatchlist({
  symbols,
  currentSymbol,
  onSelect,
  signals,
}: SimplifiedWatchlistProps) {
  return (
    <div className="h-full flex flex-col bg-dark-card border-r border-gray-700">
      {/* 头部 */}
      <div className="px-2 py-3 border-b border-gray-700">
        <div className="text-gray-400 text-xs text-center">今日监控</div>
      </div>

      {/* 股票列表 */}
      <div className="flex-1 overflow-y-auto">
        {symbols.map((symbol) => {
          const signal = signals[symbol] || { type: 'none', change: 0, change_pct: 0 }
          const isActive = symbol === currentSymbol
          const changeClass = signal.change_pct >= 0 ? 'text-green-400' : 'text-red-400'

          return (
            <div
              key={symbol}
              className={`px-2 py-2 cursor-pointer border-l-2 transition-colors ${
                isActive
                  ? 'bg-blue-900/30 border-blue-500'
                  : 'border-transparent hover:bg-gray-800/50'
              }`}
              onClick={() => onSelect(symbol)}
            >
              {/* 股票代码 + 信号 */}
              <div className="flex items-center justify-between">
                <span className="text-white text-sm font-medium">{symbol}</span>
                {signal.type === 'buy' && <span className="text-xs">🟢</span>}
                {signal.type === 'sell' && <span className="text-xs">🟠</span>}
              </div>

              {/* 涨跌幅 */}
              <div className={`text-xs ${changeClass}`}>
                {signal.change_pct >= 0 ? '+' : ''}
                {signal.change_pct.toFixed(2)}%
              </div>
            </div>
          )
        })}
      </div>

      {/* 添加按钮 */}
      <div className="p-2 border-t border-gray-700">
        <button className="w-full py-1.5 rounded text-xs text-gray-400 hover:text-white hover:bg-gray-700 transition-colors flex items-center justify-center gap-1">
          <PlusOutlined className="text-xs" />
          <span>添加</span>
        </button>
      </div>
    </div>
  )
}
