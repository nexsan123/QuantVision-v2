/**
 * 日内交易入口页面
 * Sprint 4 - F15: 管理盘前扫描 → 日内交易的流程
 *
 * 流程:
 * 1. 盘前阶段: 显示扫描器，用户选择监控列表
 * 2. 确认后: 保存到 localStorage，切换到交易界面
 * 3. 交易界面: 双图表布局 + 快捷下单
 */
import { useState, useEffect } from 'react'
import { PreMarketScanner, IntradayTradingPage } from '../../components/Intraday'
import { intradayStorage } from '../../services/storageService'

type ViewMode = 'scanner' | 'trading'

export default function Intraday() {
  const [viewMode, setViewMode] = useState<ViewMode>('scanner')
  const [watchlistSymbols, setWatchlistSymbols] = useState<string[]>([])
  const [strategyId] = useState('default-intraday')

  // 检查是否有已保存的监控列表
  useEffect(() => {
    const savedWatchlist = intradayStorage.getWatchlist()
    if (savedWatchlist.length > 0) {
      setWatchlistSymbols(savedWatchlist)
      // 如果有保存的监控列表，询问是否直接进入交易
      // 这里简化处理：有保存数据时默认显示扫描器让用户确认
    }
  }, [])

  // 确认监控列表，进入交易界面
  const handleConfirmWatchlist = (symbols: string[]) => {
    setWatchlistSymbols(symbols)
    setViewMode('trading')
  }

  // 返回扫描器
  const handleBackToScanner = () => {
    setViewMode('scanner')
  }

  // 根据当前模式渲染对应组件
  if (viewMode === 'trading' && watchlistSymbols.length > 0) {
    return (
      <IntradayTradingPage
        watchlistSymbols={watchlistSymbols}
        strategyId={strategyId}
        onBack={handleBackToScanner}
      />
    )
  }

  // 盘前扫描器视图
  return (
    <div className="min-h-screen bg-dark-bg p-6">
      <PreMarketScanner
        strategyId={strategyId}
        onConfirmWatchlist={handleConfirmWatchlist}
      />
    </div>
  )
}
