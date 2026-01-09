/**
 * 策略回放页面
 * PRD 4.17.1 整体布局
 *
 * 布局:
 * - 顶部: 导航栏 + 回放标识
 * - 上部: 回放控制条
 * - 中部: K线图 (TradingView回放模式) + 右侧面板
 * - 下部: 模拟持仓
 */
import { useState, useEffect, useCallback } from 'react'
import { Button, Table, message, Spin, Select, DatePicker } from 'antd'
import { ArrowLeftOutlined } from '@ant-design/icons'
import { useNavigate, useSearchParams } from 'react-router-dom'
import dayjs from 'dayjs'
import { getStrategies } from '../../services/strategyService'
import type { Strategy } from '../../types/strategy'

const { RangePicker } = DatePicker
import TradingViewChart from '../../components/Chart/TradingViewChart'
import {
  ReplayControlBar,
  FactorPanel,
  SignalEventLog,
  ReplayInsightPanel,
} from '../../components/Replay'
import {
  ReplayState,
  ReplayConfig,
  ReplaySpeed,
  FactorSnapshot,
  SignalEvent,
  SignalMarker,
  ReplayInsight,
  HistoricalBar,
  formatPercent,
} from '../../types/replay'

// 股票列表
const SYMBOL_OPTIONS = [
  { value: 'NVDA', label: 'NVDA - NVIDIA' },
  { value: 'AAPL', label: 'AAPL - Apple' },
  { value: 'TSLA', label: 'TSLA - Tesla' },
  { value: 'MSFT', label: 'MSFT - Microsoft' },
  { value: 'GOOGL', label: 'GOOGL - Alphabet' },
  { value: 'AMZN', label: 'AMZN - Amazon' },
  { value: 'META', label: 'META - Meta' },
]

export default function StrategyReplayPage() {
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()

  // 策略列表
  const [strategies, setStrategies] = useState<Strategy[]>([])
  const [strategiesLoading, setStrategiesLoading] = useState(true)

  // 回放状态
  const [loading, setLoading] = useState(false)
  const [state, setState] = useState<ReplayState | null>(null)
  const [snapshot, setSnapshot] = useState<FactorSnapshot | null>(null)
  const [events, setEvents] = useState<SignalEvent[]>([])
  const [signalMarkers, setSignalMarkers] = useState<SignalMarker[]>([])
  const [insight, setInsight] = useState<ReplayInsight | null>(null)
  const [_currentBar, _setCurrentBar] = useState<HistoricalBar | null>(null)

  // 从URL获取参数或使用默认值
  const strategyId = searchParams.get('strategyId') || ''
  const symbol = searchParams.get('symbol') || 'NVDA'
  const startDate = searchParams.get('startDate') || '2024-12-01'
  const endDate = searchParams.get('endDate') || '2024-12-31'

  // 加载策略列表
  useEffect(() => {
    setStrategiesLoading(true)
    getStrategies({})
      .then(result => {
        setStrategies(result.items)
        // 如果URL没有strategyId，默认选第一个
        if (!searchParams.get('strategyId') && result.items.length > 0) {
          setSearchParams({
            strategyId: result.items[0].id,
            symbol,
            startDate,
            endDate
          })
        }
      })
      .finally(() => setStrategiesLoading(false))
  }, [])

  // 处理策略切换
  const handleStrategyChange = (newStrategyId: string) => {
    setSearchParams({ strategyId: newStrategyId, symbol, startDate, endDate })
  }

  // 处理股票切换
  const handleSymbolChange = (newSymbol: string) => {
    setSearchParams({ strategyId, symbol: newSymbol, startDate, endDate })
  }

  // 处理日期范围切换
  const handleDateRangeChange = (dates: any) => {
    if (dates && dates[0] && dates[1]) {
      setSearchParams({
        strategyId,
        symbol,
        startDate: dates[0].format('YYYY-MM-DD'),
        endDate: dates[1].format('YYYY-MM-DD'),
      })
    }
  }

  // 初始化回放
  const initReplay = useCallback(async (config: Partial<ReplayConfig>) => {
    if (!strategyId) return // 等待策略ID

    setLoading(true)
    try {
      // 模拟API调用
      await new Promise((resolve) => setTimeout(resolve, 500))

      // 模拟初始化数据
      const mockState: ReplayState = {
        sessionId: `replay_${Date.now()}`,
        config: {
          strategyId: config.strategyId || strategyId,
          symbol: config.symbol || symbol,
          startDate: config.startDate || startDate,
          endDate: config.endDate || endDate,
          speed: config.speed || '1x',
        },
        status: 'idle',
        currentTime: '2024-12-01T09:30:00',
        currentBarIndex: 0,
        totalBars: 500,
        positionQuantity: 0,
        positionAvgCost: 0,
        cash: 100000,
        totalSignals: 8,
        executedSignals: 0,
        totalReturnPct: 0,
        benchmarkReturnPct: 0,
      }

      // 模拟信号标记
      const mockMarkers: SignalMarker[] = [
        { index: 50, time: '2024-12-05T10:30:00', type: 'buy' },
        { index: 120, time: '2024-12-10T14:15:00', type: 'sell' },
        { index: 200, time: '2024-12-16T11:00:00', type: 'buy' },
        { index: 280, time: '2024-12-20T15:30:00', type: 'sell' },
        { index: 350, time: '2024-12-24T10:45:00', type: 'buy' },
        { index: 420, time: '2024-12-28T13:00:00', type: 'sell' },
      ]

      setState(mockState)
      setSignalMarkers(mockMarkers)
      setEvents([])

      // 初始因子快照
      setSnapshot({
        timestamp: mockState.currentTime,
        factorValues: {
          RSI: 45.2,
          MACD: 0.0012,
          MACD_Signal: 0.0008,
          Volatility: 0.032,
          Volume_Ratio: 1.2,
          close: 520.5,
        },
        thresholds: {
          RSI: { value: 30, direction: 'below', passed: false },
          MACD: { value: 0, direction: 'above', passed: true },
          Volatility: { value: 0.03, direction: 'above', passed: true },
          Volume_Ratio: { value: 1.5, direction: 'above', passed: false },
        },
        overallSignal: 'hold',
        conditionsMet: 2,
        conditionsTotal: 4,
      })

      message.success('回放初始化完成')
    } finally {
      setLoading(false)
    }
  }, [strategyId, symbol, startDate, endDate])

  // 初始化
  useEffect(() => {
    initReplay({})
  }, [initReplay])

  // 播放控制
  const handlePlay = useCallback(async () => {
    if (!state) return
    setState({ ...state, status: 'playing' })

    // 模拟自动播放
    const interval = setInterval(() => {
      setState((prev) => {
        if (!prev || prev.status !== 'playing') {
          clearInterval(interval)
          return prev
        }
        if (prev.currentBarIndex >= prev.totalBars - 1) {
          clearInterval(interval)
          return { ...prev, status: 'paused' }
        }
        return {
          ...prev,
          currentBarIndex: prev.currentBarIndex + 1,
        }
      })
    }, 200)
  }, [state])

  const handlePause = useCallback(() => {
    if (!state) return
    setState({ ...state, status: 'paused' })
  }, [state])

  const handleStepForward = useCallback(() => {
    if (!state || state.currentBarIndex >= state.totalBars - 1) return

    const newIndex = state.currentBarIndex + 1
    setState({ ...state, currentBarIndex: newIndex })

    // 检查是否触发信号
    const marker = signalMarkers.find((m) => m.index === newIndex)
    if (marker) {
      const event: SignalEvent = {
        eventId: `evt_${Date.now()}`,
        timestamp: marker.time,
        eventType: marker.type === 'buy' ? 'buy_trigger' : 'sell_trigger',
        symbol: state.config.symbol,
        price: 520 + Math.random() * 10,
        description: `${marker.type === 'buy' ? '买入' : '卖出'}信号触发`,
        factorDetails: snapshot?.factorValues,
      }
      setEvents((prev) => [...prev, event])
    }

    // 更新因子快照
    setSnapshot((prev) =>
      prev
        ? {
            ...prev,
            factorValues: {
              ...prev.factorValues,
              RSI: 30 + Math.random() * 40,
              close: 520 + Math.random() * 10,
            },
          }
        : null
    )
  }, [state, signalMarkers, snapshot])

  const handleStepBackward = useCallback(() => {
    if (!state || state.currentBarIndex <= 0) return
    setState({ ...state, currentBarIndex: state.currentBarIndex - 1 })
  }, [state])

  const handleSeek = useCallback(
    (index: number) => {
      if (!state) return
      setState({ ...state, currentBarIndex: index })
    },
    [state]
  )

  const handleNextSignal = useCallback(() => {
    if (!state) return
    const next = signalMarkers.find((m) => m.index > state.currentBarIndex)
    if (next) {
      setState({ ...state, currentBarIndex: next.index })
    }
  }, [state, signalMarkers])

  const handleSpeedChange = useCallback(
    (speed: ReplaySpeed) => {
      if (!state) return
      setState({
        ...state,
        config: { ...state.config, speed },
      })
    },
    [state]
  )

  const handleConfigChange = useCallback(
    (config: Partial<ReplayConfig>) => {
      initReplay(config)
    },
    [initReplay]
  )

  const handleExport = useCallback(() => {
    message.info('导出功能开发中')
  }, [])

  const handleDetailReport = useCallback(() => {
    message.info('详细报告功能开发中')
  }, [])

  const handleSaveReplay = useCallback(() => {
    message.success('回放已保存')
  }, [])

  // 回放结束时生成洞察
  useEffect(() => {
    if (state && state.currentBarIndex >= state.totalBars - 1) {
      setInsight({
        totalSignals: 8,
        executionRate: 0.75,
        winRate: 0.625,
        alpha: 0.032,
        aiInsights: [
          '策略在此期间跑赢基准 3.2%',
          '买入信号在RSI超卖区表现优异',
          '建议在高波动期增加仓位控制',
        ],
        strategyReturn: 0.085,
        benchmarkReturn: 0.053,
      })
    }
  }, [state])

  // 持仓数据
  const positionColumns = [
    { title: '股票', dataIndex: 'symbol', key: 'symbol' },
    { title: '持仓', dataIndex: 'quantity', key: 'quantity' },
    {
      title: '成本',
      dataIndex: 'avgCost',
      key: 'avgCost',
      render: (v: number) => `$${v.toFixed(2)}`,
    },
    {
      title: '现价',
      dataIndex: 'currentPrice',
      key: 'currentPrice',
      render: (v: number) => `$${v.toFixed(2)}`,
    },
    {
      title: '盈亏',
      dataIndex: 'pnl',
      key: 'pnl',
      render: (v: number) => (
        <span className={v >= 0 ? 'text-green-400' : 'text-red-400'}>
          {formatPercent(v)}
        </span>
      ),
    },
  ]

  const positionData =
    state && state.positionQuantity > 0
      ? [
          {
            key: '1',
            symbol: state.config.symbol,
            quantity: `${state.positionQuantity}股`,
            avgCost: state.positionAvgCost,
            currentPrice: snapshot?.factorValues.close || 0,
            pnl: state.totalReturnPct,
          },
        ]
      : []

  return (
    <Spin spinning={loading}>
      <div className="h-screen flex flex-col bg-dark-bg">
        {/* 顶部导航 */}
        <header className="h-14 px-4 flex items-center justify-between border-b border-gray-700 bg-dark-card">
          <div className="flex items-center gap-4">
            <Button
              type="text"
              icon={<ArrowLeftOutlined />}
              onClick={() => navigate(-1)}
              className="text-gray-400 hover:text-white"
            >
              返回
            </Button>
            <div className="h-6 w-px bg-gray-700" />
            <div className="flex items-center gap-2">
              <span className="text-xl">🔄</span>
              <span className="text-white font-medium">策略回放</span>
            </div>

            {/* 策略选择器 */}
            <div className="flex items-center gap-2">
              <span className="text-gray-400 text-sm">策略:</span>
              <Select
                value={strategyId || undefined}
                onChange={handleStrategyChange}
                loading={strategiesLoading}
                style={{ width: 200 }}
                size="small"
                placeholder="选择策略"
                options={strategies.map(s => ({
                  value: s.id,
                  label: s.name,
                }))}
              />
            </div>

            {/* 股票选择器 */}
            <div className="flex items-center gap-2">
              <span className="text-gray-400 text-sm">股票:</span>
              <Select
                value={symbol}
                onChange={handleSymbolChange}
                style={{ width: 150 }}
                size="small"
                options={SYMBOL_OPTIONS}
              />
            </div>

            {/* 日期范围 */}
            <div className="flex items-center gap-2">
              <span className="text-gray-400 text-sm">日期:</span>
              <RangePicker
                value={[dayjs(startDate), dayjs(endDate)]}
                onChange={handleDateRangeChange}
                size="small"
                format="YYYY-MM-DD"
                allowClear={false}
              />
            </div>
          </div>

          <div className="flex items-center gap-3">
            <span className="px-2 py-1 bg-purple-900/50 text-purple-400 text-xs rounded">
              🟣 回放模式
            </span>
            <Button
              size="small"
              onClick={() => navigate('/my-strategies')}
            >
              退出回放
            </Button>
          </div>
        </header>

        {/* 回放控制条 */}
        <ReplayControlBar
          state={state}
          signalMarkers={signalMarkers}
          onPlay={handlePlay}
          onPause={handlePause}
          onStepForward={handleStepForward}
          onStepBackward={handleStepBackward}
          onSeek={handleSeek}
          onNextSignal={handleNextSignal}
          onSpeedChange={handleSpeedChange}
          onConfigChange={handleConfigChange}
        />

        {/* 主内容区 */}
        <div className="flex-1 flex overflow-hidden">
          {/* K线图区域 */}
          <div className="flex-1 flex flex-col">
            <div className="flex-1 relative">
              <TradingViewChart
                symbol={state?.config.symbol || 'NVDA'}
                interval="5"
                theme="dark"
              />

              {/* 回放进度覆盖层 */}
              {state && (
                <div className="absolute bottom-4 left-4 bg-black/70 px-3 py-2 rounded">
                  <div className="text-purple-400 text-sm">
                    Bar {state.currentBarIndex + 1} / {state.totalBars}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* 右侧面板 */}
          <div className="w-[320px] flex-shrink-0 border-l border-gray-700 flex flex-col overflow-y-auto">
            <div className="p-2 space-y-2">
              <FactorPanel snapshot={snapshot} />
              <SignalEventLog events={events} onExport={handleExport} />
              <ReplayInsightPanel
                insight={insight}
                onDetailReport={handleDetailReport}
                onSaveReplay={handleSaveReplay}
              />
            </div>
          </div>
        </div>

        {/* 模拟持仓区 */}
        <div className="border-t border-gray-700 bg-dark-card">
          <div className="px-4 py-2">
            <div className="flex items-center justify-between mb-2">
              <span className="text-white font-medium">模拟持仓</span>
              <span className="text-gray-400 text-sm">
                总资产: $
                {state
                  ? (
                      state.cash +
                      state.positionQuantity * (snapshot?.factorValues.close || 0)
                    ).toFixed(2)
                  : '100,000.00'}
              </span>
            </div>
            <Table
              columns={positionColumns}
              dataSource={positionData}
              size="small"
              pagination={false}
              locale={{
                emptyText: <span className="text-gray-500">暂无持仓</span>,
              }}
            />
          </div>
        </div>
      </div>
    </Spin>
  )
}
