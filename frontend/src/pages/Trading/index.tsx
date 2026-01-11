/**
 * 实时交易监控页面
 * Sprint 3 重构: PRD 4.16 三栏布局
 * UI 优化: 性能优化 - React.memo + useCallback + useMemo
 *
 * 布局设计:
 * - 左侧 280px: 部署列表 + 信号雷达
 * - 中间 flex: TradingView 图表
 * - 右侧 288px: 持仓监控 + 订单管理
 */
import { useState, useEffect, useCallback, useMemo, memo } from 'react'
import { Button, Spin } from 'antd'
import { ExpandOutlined, CompressOutlined, SettingOutlined } from '@ant-design/icons'
import EnvironmentSwitch, { TradingEnvironment } from '@/components/common/EnvironmentSwitch'
import { PanelErrorBoundary } from '@/components/common/ErrorBoundary'
import DeploymentListPanel from '@/components/TradingMonitor/DeploymentListPanel'
import SignalRadarPanel from '@/components/TradingMonitor/SignalRadarPanel'
import PositionMonitorPanel from '@/components/TradingMonitor/PositionMonitorPanel'
import OrderPanel from '@/components/TradingMonitor/OrderPanel'
import { TradingViewChart, TimeframeSelector, IndicatorPanel } from '@/components/Chart'
import type { TimeFrame, IndicatorConfig } from '@/components/Chart'
import { StockSearch } from '@/components/Trading/StockSearch'
import { getDeployments } from '@/services/deploymentService'
import type { Deployment } from '@/types/deployment'

// 默认指标配置 - 移到组件外避免重新创建
const DEFAULT_INDICATORS: IndicatorConfig[] = [
  { id: 'MASimple@tv-basicstudies', name: 'MA 20', inputs: { length: 20 } },
  { id: 'RSI@tv-basicstudies', name: 'RSI', inputs: { length: 14 } },
  { id: 'MACD@tv-basicstudies', name: 'MACD' },
]

// 左侧面板 - 使用 memo 防止不必要的重渲染
interface LeftPanelProps {
  collapsed: boolean
  deployments: Deployment[]
  selectedId?: string
  onSelect: (deployment: Deployment) => void
  strategyId: string
  deploymentId: string
  onToggle: () => void
  onSymbolSelect: (symbol: string) => void
}

const LeftPanel = memo(function LeftPanel({
  collapsed,
  deployments,
  selectedId,
  onSelect,
  strategyId,
  deploymentId,
  onToggle,
  onSymbolSelect,
}: LeftPanelProps) {
  const width = collapsed ? 48 : 280

  return (
    <aside
      className="flex-shrink-0 border-r border-gray-800 bg-[#12122a] transition-all duration-300 flex flex-col"
      style={{ width }}
    >
      {collapsed ? (
        <div className="flex-1 flex flex-col items-center pt-4 gap-4">
          <Button
            type="text"
            icon={<ExpandOutlined />}
            onClick={onToggle}
            className="text-gray-400"
          />
        </div>
      ) : (
        <>
          <div className="h-[45%] border-b border-gray-800 overflow-hidden">
            <PanelErrorBoundary title="部署列表">
              <DeploymentListPanel
                deployments={deployments}
                selectedId={selectedId}
                onSelect={onSelect}
              />
            </PanelErrorBoundary>
          </div>
          <div className="flex-1 overflow-hidden">
            <PanelErrorBoundary title="信号雷达">
              <SignalRadarPanel
                strategyId={strategyId}
                deploymentId={deploymentId}
                onSymbolClick={onSymbolSelect}
              />
            </PanelErrorBoundary>
          </div>
        </>
      )}
    </aside>
  )
})

// 右侧面板 - 使用 memo 防止不必要的重渲染
interface RightPanelProps {
  collapsed: boolean
  deploymentId: string
  onToggle: () => void
  onSymbolSelect: (symbol: string) => void
}

const RightPanel = memo(function RightPanel({
  collapsed,
  deploymentId,
  onToggle,
  onSymbolSelect,
}: RightPanelProps) {
  const width = collapsed ? 48 : 288

  return (
    <aside
      className="flex-shrink-0 border-l border-gray-800 bg-[#12122a] transition-all duration-300 flex flex-col"
      style={{ width }}
    >
      {collapsed ? (
        <div className="flex-1 flex flex-col items-center pt-4 gap-4">
          <Button
            type="text"
            icon={<ExpandOutlined />}
            onClick={onToggle}
            className="text-gray-400"
          />
        </div>
      ) : (
        <>
          <div className="h-[55%] border-b border-gray-800 overflow-hidden">
            <PanelErrorBoundary title="持仓监控">
              <PositionMonitorPanel
                deploymentId={deploymentId}
                onSymbolClick={onSymbolSelect}
              />
            </PanelErrorBoundary>
          </div>
          <div className="flex-1 overflow-hidden">
            <PanelErrorBoundary title="订单管理">
              <OrderPanel deploymentId={deploymentId} />
            </PanelErrorBoundary>
          </div>
        </>
      )}
    </aside>
  )
})

// 图表工具栏 - 使用 memo
interface ChartToolbarProps {
  symbol: string
  timeframe: TimeFrame
  strategyName?: string
  indicators: IndicatorConfig[]
  onTimeframeChange: (tf: TimeFrame) => void
  onIndicatorsChange: (indicators: IndicatorConfig[]) => void
}

const ChartToolbar = memo(function ChartToolbar({
  symbol,
  timeframe,
  strategyName,
  indicators,
  onTimeframeChange,
  onIndicatorsChange,
}: ChartToolbarProps) {
  return (
    <div className="h-10 px-4 flex items-center justify-between border-b border-gray-800 bg-[#12122a] flex-shrink-0">
      <div className="flex items-center gap-4">
        <span className="text-white font-medium">{symbol}</span>
        <TimeframeSelector
          value={timeframe}
          onChange={onTimeframeChange}
          compact
        />
      </div>
      <div className="flex items-center gap-2">
        <IndicatorPanel
          indicators={indicators}
          onChange={onIndicatorsChange}
        />
        {strategyName && (
          <span className="text-gray-500 text-xs">
            策略: {strategyName}
          </span>
        )}
      </div>
    </div>
  )
})

// 主组件
export default function Trading() {
  // 布局状态
  const [leftCollapsed, setLeftCollapsed] = useState(false)
  const [rightCollapsed, setRightCollapsed] = useState(false)

  // 环境状态
  const [tradingEnv, setTradingEnv] = useState<TradingEnvironment>('paper')

  // 图表状态
  const [currentSymbol, setCurrentSymbol] = useState('NVDA')
  const [timeframe, setTimeframe] = useState<TimeFrame>('15')
  const [indicators, setIndicators] = useState<IndicatorConfig[]>(DEFAULT_INDICATORS)

  // 部署数据
  const [deployments, setDeployments] = useState<Deployment[]>([])
  const [selectedDeployment, setSelectedDeployment] = useState<Deployment | null>(null)
  const [loading, setLoading] = useState(true)

  // 加载部署列表
  useEffect(() => {
    let mounted = true
    setLoading(true)

    getDeployments({ status: 'running' })
      .then(result => {
        if (!mounted) return
        setDeployments(result.items)
        if (result.items.length > 0) {
          setSelectedDeployment(result.items[0])
        }
      })
      .finally(() => {
        if (mounted) setLoading(false)
      })

    return () => { mounted = false }
  }, [])

  // 环境切换条件 (模拟数据)
  const paperDays = 45
  const winRate = 52.5

  // 使用 useCallback 缓存回调函数
  const handleEnvChange = useCallback(async (env: TradingEnvironment): Promise<boolean> => {
    setTradingEnv(env)
    return true
  }, [])

  const handleDeploymentSelect = useCallback((deployment: Deployment) => {
    setSelectedDeployment(deployment)
  }, [])

  const handleLeftToggle = useCallback(() => {
    setLeftCollapsed(prev => !prev)
  }, [])

  const handleRightToggle = useCallback(() => {
    setRightCollapsed(prev => !prev)
  }, [])

  const handleTimeframeChange = useCallback((tf: TimeFrame) => {
    setTimeframe(tf)
  }, [])

  const handleIndicatorsChange = useCallback((newIndicators: IndicatorConfig[]) => {
    setIndicators(newIndicators)
  }, [])

  const handleSymbolChange = useCallback((symbol: string) => {
    setCurrentSymbol(symbol)
  }, [])

  // 使用 useMemo 缓存计算值
  const strategyId = useMemo(() => selectedDeployment?.strategyId || '', [selectedDeployment?.strategyId])
  const deploymentId = useMemo(() => selectedDeployment?.deploymentId || '', [selectedDeployment?.deploymentId])
  const selectedId = useMemo(() => selectedDeployment?.deploymentId, [selectedDeployment?.deploymentId])
  const strategyName = useMemo(() => selectedDeployment?.strategyName, [selectedDeployment?.strategyName])

  if (loading) {
    return (
      <div className="h-screen flex items-center justify-center bg-[#0a0a1a]">
        <Spin size="large" tip="加载中..." />
      </div>
    )
  }

  return (
    <div className="h-screen flex flex-col bg-[#0a0a1a] overflow-hidden">
      {/* 顶部工具栏 */}
      <header className="h-12 px-4 flex items-center justify-between border-b border-gray-800 bg-[#12122a] flex-shrink-0">
        <div className="flex items-center gap-4">
          <h1 className="text-lg font-bold text-white">实时交易监控</h1>

          {/* 全局搜索框 */}
          <StockSearch
            value={currentSymbol}
            onSelect={handleSymbolChange}
          />

          <EnvironmentSwitch
            currentEnv={tradingEnv}
            onEnvChange={handleEnvChange}
            paperDays={paperDays}
            winRate={winRate}
          />
          {selectedDeployment && (
            <span className="text-gray-400 text-sm">
              当前: <span className="text-white">{selectedDeployment.strategyName}</span>
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <Button
            type="text"
            icon={leftCollapsed ? <ExpandOutlined /> : <CompressOutlined />}
            onClick={handleLeftToggle}
            className="text-gray-400"
          />
          <Button
            type="text"
            icon={rightCollapsed ? <ExpandOutlined /> : <CompressOutlined />}
            onClick={handleRightToggle}
            className="text-gray-400"
          />
          <Button type="text" icon={<SettingOutlined />} className="text-gray-400" />
        </div>
      </header>

      {/* 三栏主体 */}
      <div className="flex-1 flex overflow-hidden">
        {/* 左侧面板 */}
        <LeftPanel
          collapsed={leftCollapsed}
          deployments={deployments}
          selectedId={selectedId}
          onSelect={handleDeploymentSelect}
          strategyId={strategyId}
          deploymentId={deploymentId}
          onToggle={handleLeftToggle}
          onSymbolSelect={handleSymbolChange}
        />

        {/* 中间: 图表区域 */}
        <main className="flex-1 flex flex-col bg-[#0a0a1a] overflow-hidden">
          {/* 图表工具栏 */}
          <ChartToolbar
            symbol={currentSymbol}
            timeframe={timeframe}
            strategyName={strategyName}
            indicators={indicators}
            onTimeframeChange={handleTimeframeChange}
            onIndicatorsChange={handleIndicatorsChange}
          />

          {/* TradingView 图表 */}
          <div className="flex-1 m-2 rounded-lg overflow-hidden bg-[#12122a]">
            <PanelErrorBoundary title="图表">
              <TradingViewChart
                symbol={currentSymbol}
                interval={timeframe}
                theme="dark"
                indicators={indicators}
                onSymbolChange={handleSymbolChange}
                onIntervalChange={handleTimeframeChange}
              />
            </PanelErrorBoundary>
          </div>
        </main>

        {/* 右侧面板 */}
        <RightPanel
          collapsed={rightCollapsed}
          deploymentId={deploymentId}
          onToggle={handleRightToggle}
          onSymbolSelect={handleSymbolChange}
        />
      </div>
    </div>
  )
}
