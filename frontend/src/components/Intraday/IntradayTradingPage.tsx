/**
 * 日内交易页面
 * PRD 4.18.1 日内交易专用视图
 * 三栏布局: 简化监控列表 | TradingView图表 | 止盈止损+交易记录
 */
import { useState, useEffect } from 'react'
import { Button, message } from 'antd'
import { ArrowLeftOutlined } from '@ant-design/icons'
import SimplifiedWatchlist from './SimplifiedWatchlist'
import StopLossPanel from './StopLossPanel'
import IntradayTradeLog from './IntradayTradeLog'
import TradingViewChart from '../Chart/TradingViewChart'
import QuickTradePanel from '../Trade/QuickTradePanel'
import {
  SignalStatus,
  StopLossConfig,
  IntradayTrade,
  DEFAULT_STOP_LOSS_CONFIG,
} from '../../types/preMarket'

interface IntradayTradingPageProps {
  watchlistSymbols: string[]
  strategyId: string
  onBack: () => void
}

// PDT 规则配置 (模拟数据)
interface PDTStatus {
  remainingTrades: number
  resetDate: string
  isWarning: boolean
}

export default function IntradayTradingPage({
  watchlistSymbols,
  strategyId: _strategyId,
  onBack,
}: IntradayTradingPageProps) {
  const [currentSymbol, setCurrentSymbol] = useState(watchlistSymbols[0] || 'NVDA')
  const [signals, setSignals] = useState<Record<string, SignalStatus>>({})
  const [trades, setTrades] = useState<IntradayTrade[]>([])
  const [loading, setLoading] = useState(false)
  const [stopLossConfig, setStopLossConfig] = useState<StopLossConfig>(
    DEFAULT_STOP_LOSS_CONFIG
  )

  // PDT 规则状态 (模拟)
  const [pdtStatus] = useState<PDTStatus>({
    remainingTrades: 2,
    resetDate: '周三',
    isWarning: true,
  })

  // 模拟实时信号更新
  useEffect(() => {
    const mockSignals: Record<string, SignalStatus> = {}
    watchlistSymbols.forEach((symbol) => {
      const change = (Math.random() - 0.5) * 10
      mockSignals[symbol] = {
        type: change > 2 ? 'buy' : change < -2 ? 'sell' : 'none',
        change: change,
        change_pct: change,
      }
    })
    setSignals(mockSignals)

    // 模拟交易记录
    setTrades([
      {
        time: new Date(Date.now() - 3600000).toISOString(),
        symbol: 'NVDA',
        side: 'buy',
        quantity: 100,
        price: 520.5,
        stop_loss: 515.0,
        take_profit: 530.0,
        is_open: true,
      },
      {
        time: new Date(Date.now() - 7200000).toISOString(),
        symbol: 'TSLA',
        side: 'buy',
        quantity: 50,
        price: 248.0,
        stop_loss: 245.0,
        take_profit: 255.0,
        pnl: 125.0,
        is_open: false,
      },
    ])
  }, [watchlistSymbols])

  // 处理止盈止损配置更新
  const handleStopLossUpdate = (config: StopLossConfig) => {
    setStopLossConfig(config)
    message.success('止盈止损设置已更新')
  }

  // 处理买入
  const handleBuy = async (quantity: number, _orderType: string, price?: number) => {
    setLoading(true)
    try {
      await new Promise((resolve) => setTimeout(resolve, 500))

      const newTrade: IntradayTrade = {
        time: new Date().toISOString(),
        symbol: currentSymbol,
        side: 'buy',
        quantity,
        price: price || 522.3,
        stop_loss: stopLossConfig.stop_loss_value,
        take_profit: stopLossConfig.take_profit_value,
        is_open: true,
      }

      setTrades((prev) => [newTrade, ...prev])
      message.success(`买入 ${currentSymbol} ${quantity}股 成功`)
    } catch {
      message.error('买入失败')
    } finally {
      setLoading(false)
    }
  }

  // 处理卖出
  const handleSell = async (quantity: number, _orderType: string, price?: number) => {
    setLoading(true)
    try {
      await new Promise((resolve) => setTimeout(resolve, 500))

      const newTrade: IntradayTrade = {
        time: new Date().toISOString(),
        symbol: currentSymbol,
        side: 'sell',
        quantity,
        price: price || 522.3,
        stop_loss: undefined,
        take_profit: undefined,
        is_open: false,
        pnl: (price || 522.3 - 520.5) * quantity,
      }

      setTrades((prev) => [newTrade, ...prev])
      message.success(`卖出 ${currentSymbol} ${quantity}股 成功`)
    } catch {
      message.error('卖出失败')
    } finally {
      setLoading(false)
    }
  }

  // 模拟当前持仓
  const currentPosition = trades.find(
    (t) => t.symbol === currentSymbol && t.is_open
  )
    ? {
        symbol: currentSymbol,
        quantity: 100,
        entry_price: 520.5,
        current_price: 522.3,
        pnl: 180.0,
        pnl_pct: 0.35,
      }
    : null

  return (
    <div className="h-screen flex flex-col bg-dark-bg">
      {/* 顶部栏 */}
      <div className="h-12 px-4 flex items-center justify-between border-b border-gray-700 bg-dark-card">
        <div className="flex items-center gap-4">
          <Button
            type="text"
            icon={<ArrowLeftOutlined />}
            onClick={onBack}
            className="text-gray-400 hover:text-white"
          >
            返回扫描器
          </Button>
          <div className="h-6 w-px bg-gray-700" />
          <div className="flex items-center gap-2">
            <span className="text-2xl">📈</span>
            <span className="text-white font-medium">日内交易模式</span>
          </div>
        </div>
        <div className="flex items-center gap-4">
          {/* PDT 规则警告 */}
          {pdtStatus.isWarning && (
            <div className="flex items-center gap-2 px-3 py-1 rounded bg-yellow-500/20 border border-yellow-500/30">
              <span className="text-yellow-400 text-sm font-medium">⚠️ PDT 规则限制</span>
              <span className="text-yellow-300 text-sm">
                今日剩余: <span className="font-bold">{pdtStatus.remainingTrades}</span> 次
              </span>
              <span className="text-yellow-400/60 text-xs">
                重置: {pdtStatus.resetDate}
              </span>
            </div>
          )}

          <div className="text-sm">
            <span className="text-gray-400">当前股票: </span>
            <span className="text-white font-medium">{currentSymbol}</span>
          </div>
          <div className="text-sm">
            <span className="text-gray-400">监控: </span>
            <span className="text-blue-400">{watchlistSymbols.length}只</span>
          </div>
        </div>
      </div>

      {/* 主体三栏布局 */}
      <div className="flex-1 flex overflow-hidden">
        {/* 左侧: 简化监控列表 */}
        <div className="w-[100px] flex-shrink-0">
          <SimplifiedWatchlist
            symbols={watchlistSymbols}
            currentSymbol={currentSymbol}
            onSelect={setCurrentSymbol}
            signals={signals}
          />
        </div>

        {/* 中间: 双TradingView图表 (1min + 5min) */}
        <div className="flex-1 flex flex-col border-l border-r border-gray-700">
          {/* 上半部: 5分钟图 (主图) */}
          <div className="flex-1 relative border-b border-gray-700">
            <div className="absolute top-2 left-2 z-10 bg-gray-900/80 px-2 py-1 rounded text-xs text-gray-400">
              5min
            </div>
            <TradingViewChart
              symbol={currentSymbol}
              interval="5"
              theme="dark"
            />
          </div>

          {/* 下半部: 1分钟图 (细节) */}
          <div className="h-[200px] relative">
            <div className="absolute top-2 left-2 z-10 bg-gray-900/80 px-2 py-1 rounded text-xs text-gray-400">
              1min
            </div>
            <TradingViewChart
              symbol={currentSymbol}
              interval="1"
              theme="dark"
              height={200}
            />
          </div>

          {/* 快速交易面板 */}
          <div className="h-[140px] border-t border-gray-700">
            <QuickTradePanel
              symbol={currentSymbol}
              price={522.3}
              onBuy={handleBuy}
              onSell={handleSell}
              loading={loading}
              position={currentPosition ? {
                quantity: currentPosition.quantity,
                avgCost: currentPosition.entry_price,
                pnl: currentPosition.pnl,
                pnlPct: currentPosition.pnl_pct,
              } : undefined}
              pdtWarning={pdtStatus.isWarning ? `今日剩余日内交易: ${pdtStatus.remainingTrades} 次` : undefined}
            />
          </div>
        </div>

        {/* 右侧: 止盈止损 + 交易记录 */}
        <div className="w-[320px] flex-shrink-0 flex flex-col overflow-hidden">
          {/* 止盈止损面板 */}
          <div className="flex-shrink-0">
            {currentPosition ? (
              <StopLossPanel
                position={currentPosition}
                atr={0.68}
                onUpdate={handleStopLossUpdate}
              />
            ) : (
              <div className="bg-dark-card p-4">
                <div className="text-gray-500 text-center py-8">
                  <div className="text-3xl mb-2">📊</div>
                  <div>暂无 {currentSymbol} 持仓</div>
                  <div className="text-xs mt-1">买入后可设置止盈止损</div>
                </div>
              </div>
            )}
          </div>

          {/* 今日交易记录 */}
          <div className="flex-1 overflow-hidden mt-2">
            <IntradayTradeLog trades={trades} loading={loading} />
          </div>
        </div>
      </div>

      {/* 底部状态栏 */}
      <div className="h-8 px-4 flex items-center justify-between border-t border-gray-700 bg-dark-card text-xs">
        <div className="flex items-center gap-4">
          <span className="text-green-400">● 市场开放</span>
          <span className="text-gray-400">
            {new Date().toLocaleTimeString()} EST
          </span>
        </div>
        <div className="flex items-center gap-4">
          {stopLossConfig.time_stop_enabled && (
            <span className="text-yellow-400">
              ⏰ 时间止损: {stopLossConfig.time_stop_time}
            </span>
          )}
          {stopLossConfig.trailing_stop_enabled && (
            <span className="text-purple-400">
              📈 移动止损已启用
            </span>
          )}
        </div>
      </div>
    </div>
  )
}
