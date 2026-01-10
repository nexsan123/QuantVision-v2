import { useState, useEffect, useCallback, useRef } from 'react'
import { Row, Col, DatePicker, Select, Button, Table, Tabs, Progress, Modal, message } from 'antd'
import { PlayCircleOutlined, DownloadOutlined, RocketOutlined, LineChartOutlined, ArrowLeftOutlined } from '@ant-design/icons'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { Card, NumberDisplay } from '@/components/ui'
import { ReturnChart, HeatmapChart } from '@/components/Chart'
import { getStrategies, getStrategy, updateBacktestResult, updateStrategy } from '@/services/strategyService'
import {
  createBacktest,
  getBacktest,
  getBacktestStatus,
  getBacktestTrades,
  type BacktestMetrics,
  type BacktestTrade,
} from '@/services/backtestService'
import type { Strategy, BacktestSummary } from '@/types/strategy'
import dayjs from 'dayjs'

const { RangePicker } = DatePicker

// 默认空指标 (回测完成前显示)
const emptyMetrics: BacktestMetrics = {
  totalReturn: 0,
  annualReturn: 0,
  sharpe: 0,
  sortino: 0,
  maxDrawdown: 0,
  winRate: 0,
  profitFactor: 0,
  calmar: 0,
}

// 默认收益曲线数据
const emptyReturnData = {
  dates: [] as string[],
  strategy: [] as number[],
  benchmark: [] as number[],
}

// 默认热力图数据
const emptyHeatmapData = {
  years: [] as string[],
  months: ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月'],
  values: [] as number[][],
}

const tradeColumns = [
  { title: '日期', dataIndex: 'timestamp', key: 'timestamp', render: (t: string) => t?.split('T')[0] || '-' },
  { title: '股票', dataIndex: 'symbol', key: 'symbol' },
  { title: '方向', dataIndex: 'side', key: 'side', render: (s: string) => (
    <span className={s === 'buy' ? 'text-profit' : 'text-loss'}>{s?.toUpperCase()}</span>
  )},
  { title: '数量', dataIndex: 'quantity', key: 'quantity', className: 'text-right font-mono' },
  { title: '价格', dataIndex: 'price', key: 'price', className: 'text-right font-mono', render: (p: number) => `$${p?.toFixed(2) || '-'}` },
  { title: '盈亏', dataIndex: 'pnl', key: 'pnl', className: 'text-right', render: (v: number | undefined) => (
    v !== undefined ? <NumberDisplay value={v} type="currency" colorize showSign /> : '-'
  )},
]

/**
 * 回测中心页面
 *
 * 功能:
 * - 回测配置 (策略选择、时间范围、初始资金)
 * - 结果展示 (绩效指标、收益曲线、月度热力图)
 * - 回测完成后引导下一步操作
 */
export default function BacktestCenter() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const strategyIdFromUrl = searchParams.get('strategyId')

  // 策略列表和选中的策略
  const [strategies, setStrategies] = useState<Strategy[]>([])
  const [selectedStrategyId, setSelectedStrategyId] = useState<string | null>(strategyIdFromUrl)
  const [selectedStrategy, setSelectedStrategy] = useState<Strategy | null>(null)
  const [loadingStrategies, setLoadingStrategies] = useState(true)

  // 回测配置
  const [dateRange, setDateRange] = useState<[dayjs.Dayjs, dayjs.Dayjs]>([
    dayjs('2022-01-01'),
    dayjs('2024-12-31'),
  ])
  const [initialCapital, setInitialCapital] = useState('1000000')

  // 回测状态
  const [running, setRunning] = useState(false)
  const [progress, setProgress] = useState(0)
  const [backtestComplete, setBacktestComplete] = useState(false)
  const [showCompleteModal, setShowCompleteModal] = useState(false)
  const [, setCurrentBacktestId] = useState<string | null>(null)
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null)

  // 回测结果数据 (从API获取)
  const [metrics, setMetrics] = useState<BacktestMetrics>(emptyMetrics)
  // TODO: 后端需要提供收益曲线和热力图数据的 API
  const [returnData, /* setReturnData */] = useState(emptyReturnData)
  const [heatmapData, /* setHeatmapData */] = useState(emptyHeatmapData)
  const [trades, setTrades] = useState<(BacktestTrade & { key: string })[]>([])
  const [tradesLoading, setTradesLoading] = useState(false)

  // 清理轮询
  const stopPolling = useCallback(() => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current)
      pollingRef.current = null
    }
  }, [])

  useEffect(() => {
    return () => stopPolling()
  }, [stopPolling])

  // 加载策略列表
  useEffect(() => {
    setLoadingStrategies(true)
    getStrategies({ pageSize: 100 })
      .then(result => {
        setStrategies(result.items)
        // 如果URL有strategyId，选中该策略
        if (strategyIdFromUrl) {
          const found = result.items.find(s => s.id === strategyIdFromUrl)
          if (found) {
            setSelectedStrategy(found)
          }
        }
      })
      .catch(() => {
        message.error('加载策略列表失败')
      })
      .finally(() => {
        setLoadingStrategies(false)
      })
  }, [strategyIdFromUrl])

  // 选择策略
  const handleStrategyChange = async (strategyId: string) => {
    setSelectedStrategyId(strategyId)
    const strategy = strategies.find(s => s.id === strategyId)
    if (strategy) {
      setSelectedStrategy(strategy)
    } else {
      const loaded = await getStrategy(strategyId)
      setSelectedStrategy(loaded)
    }
    // 更新URL
    navigate(`/backtest?strategyId=${strategyId}`, { replace: true })
    // 重置回测状态
    setBacktestComplete(false)
    setProgress(0)
  }

  // 加载回测结果详情
  const loadBacktestResult = useCallback(async (backtestId: string) => {
    try {
      // 获取回测详情 (含指标)
      const result = await getBacktest(backtestId)
      if (result.metrics) {
        setMetrics(result.metrics)
      }

      // 获取交易记录
      setTradesLoading(true)
      const tradesResult = await getBacktestTrades(backtestId, { pageSize: 100 })
      setTrades(tradesResult.trades.map((t, i) => ({ ...t, key: `${i}` })))
      setTradesLoading(false)

      // TODO: 后端需要提供收益曲线和月度热力图数据
      // 暂时保持空数据，等待后端 API 扩展
    } catch (err) {
      console.error('加载回测结果失败:', err)
    }
  }, [])

  // 运行回测
  const handleRun = async () => {
    if (!selectedStrategy) {
      message.warning('请先选择策略')
      return
    }

    setRunning(true)
    setProgress(0)
    setBacktestComplete(false)
    setMetrics(emptyMetrics)
    setTrades([])
    stopPolling()

    try {
      // 调用后端创建回测
      const backtest = await createBacktest({
        name: `${selectedStrategy.name} - ${dayjs().format('YYYY-MM-DD HH:mm')}`,
        strategyId: selectedStrategy.id,
        startDate: dateRange[0].format('YYYY-MM-DD'),
        endDate: dateRange[1].format('YYYY-MM-DD'),
        initialCapital: parseInt(initialCapital),
      })

      setCurrentBacktestId(backtest.id)

      // 轮询回测状态
      pollingRef.current = setInterval(async () => {
        try {
          const status = await getBacktestStatus(backtest.id)
          setProgress(status.progress)

          if (status.status === 'completed') {
            stopPolling()
            setRunning(false)
            setBacktestComplete(true)

            // 加载完整回测结果
            await loadBacktestResult(backtest.id)

            // 获取最新指标更新策略
            const finalResult = await getBacktest(backtest.id)
            const backtestSummary: BacktestSummary = {
              backtestId: backtest.id,
              annualReturn: finalResult.metrics?.annualReturn || 0,
              sharpeRatio: finalResult.metrics?.sharpe || 0,
              maxDrawdown: finalResult.metrics?.maxDrawdown || 0,
              winRate: finalResult.metrics?.winRate || 0,
              startDate: dateRange[0].format('YYYY-MM-DD'),
              endDate: dateRange[1].format('YYYY-MM-DD'),
              completedAt: finalResult.completedAt || new Date().toISOString(),
            }

            // 保存回测结果并更新策略状态
            await Promise.all([
              updateBacktestResult(selectedStrategy.id, backtestSummary),
              selectedStrategy.status === 'draft'
                ? updateStrategy(selectedStrategy.id, { status: 'backtest' })
                : Promise.resolve(null),
            ])

            message.success('回测完成!')
            setSelectedStrategy(prev =>
              prev ? { ...prev, lastBacktest: backtestSummary, status: prev.status === 'draft' ? 'backtest' : prev.status } : null
            )
            setShowCompleteModal(true)

          } else if (status.status === 'failed') {
            stopPolling()
            setRunning(false)
            message.error('回测失败，请检查策略配置')
          } else if (status.status === 'cancelled') {
            stopPolling()
            setRunning(false)
            message.warning('回测已取消')
          }
        } catch (err) {
          console.error('轮询回测状态失败:', err)
        }
      }, 1000) // 每秒轮询一次

    } catch (err) {
      setRunning(false)
      message.error('启动回测失败，请稍后重试')
      console.error('创建回测失败:', err)
    }
  }

  // 处理部署策略
  const handleDeploy = () => {
    setShowCompleteModal(false)
    navigate(`/my-strategies?deploy=${selectedStrategyId}`)
  }

  // 处理查看详情/继续优化
  const handleContinueOptimize = () => {
    setShowCompleteModal(false)
    navigate(`/strategy?id=${selectedStrategyId}`)
  }

  return (
    <div className="space-y-6 animate-in">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button
            type="text"
            icon={<ArrowLeftOutlined />}
            onClick={() => navigate('/my-strategies')}
          >
            返回我的策略
          </Button>
          <h1 className="text-2xl font-bold">回测中心</h1>
        </div>
        <div className="flex gap-2">
          <Button icon={<DownloadOutlined />} disabled={!backtestComplete}>导出报告</Button>
        </div>
      </div>

      {/* 回测配置 */}
      <Card title="回测配置">
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} sm={12} md={6}>
            <div className="text-sm text-gray-400 mb-2">策略</div>
            <Select
              value={selectedStrategyId || undefined}
              onChange={handleStrategyChange}
              style={{ width: '100%' }}
              placeholder="选择要回测的策略"
              loading={loadingStrategies}
              showSearch
              optionFilterProp="children"
            >
              {strategies.map(s => (
                <Select.Option key={s.id} value={s.id}>
                  {s.name}
                  {s.lastBacktest && (
                    <span className="text-gray-500 ml-2 text-xs">
                      (已回测)
                    </span>
                  )}
                </Select.Option>
              ))}
            </Select>
            {strategies.length === 0 && !loadingStrategies && (
              <div className="text-xs text-gray-500 mt-1">
                暂无策略，<a onClick={() => navigate('/strategy')} className="text-blue-400">去创建</a>
              </div>
            )}
          </Col>
          <Col xs={24} sm={12} md={8}>
            <div className="text-sm text-gray-400 mb-2">回测区间</div>
            <RangePicker
              value={dateRange}
              onChange={(dates) => {
                if (dates && dates[0] && dates[1]) {
                  setDateRange([dates[0], dates[1]])
                }
              }}
              style={{ width: '100%' }}
            />
          </Col>
          <Col xs={24} sm={12} md={4}>
            <div className="text-sm text-gray-400 mb-2">初始资金</div>
            <Select value={initialCapital} onChange={setInitialCapital} style={{ width: '100%' }}>
              <Select.Option value="100000">$100,000</Select.Option>
              <Select.Option value="1000000">$1,000,000</Select.Option>
              <Select.Option value="10000000">$10,000,000</Select.Option>
            </Select>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <div className="text-sm text-gray-400 mb-2">&nbsp;</div>
            <Button
              type="primary"
              icon={<PlayCircleOutlined />}
              onClick={handleRun}
              loading={running}
              disabled={!selectedStrategy}
              block
            >
              {running ? '运行中...' : '运行回测'}
            </Button>
          </Col>
        </Row>

        {/* 选中策略的信息 */}
        {selectedStrategy && (
          <div className="mt-4 p-3 rounded bg-gray-800/50 text-sm">
            <div className="flex items-center justify-between">
              <div>
                <span className="text-gray-400">策略: </span>
                <span className="text-white font-medium">{selectedStrategy.name}</span>
                <span className="text-gray-500 ml-3">{selectedStrategy.description}</span>
              </div>
              {selectedStrategy.lastBacktest && (
                <div className="text-gray-400">
                  上次回测: {new Date(selectedStrategy.lastBacktest.completedAt).toLocaleDateString()}
                  <span className={`ml-2 ${selectedStrategy.lastBacktest.annualReturn >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                    {(selectedStrategy.lastBacktest.annualReturn * 100).toFixed(1)}% 年化
                  </span>
                </div>
              )}
            </div>
          </div>
        )}

        {running && (
          <div className="mt-4">
            <Progress percent={progress} status="active" />
          </div>
        )}
      </Card>

      {/* 绩效指标 */}
      <Row gutter={[16, 16]}>
        {[
          { label: '总收益', value: metrics.totalReturn, type: 'percent' as const },
          { label: '年化收益', value: metrics.annualReturn, type: 'percent' as const },
          { label: '夏普比率', value: metrics.sharpe, type: 'ratio' as const },
          { label: '索提诺', value: metrics.sortino, type: 'ratio' as const },
          { label: '最大回撤', value: metrics.maxDrawdown, type: 'percent' as const },
          { label: '胜率', value: metrics.winRate, type: 'percent' as const },
          { label: '盈亏比', value: metrics.profitFactor, type: 'ratio' as const },
          { label: 'Calmar', value: metrics.calmar, type: 'ratio' as const },
        ].map((m) => (
          <Col xs={12} sm={8} md={6} lg={3} key={m.label}>
            <Card padding="md" className="text-center">
              <div className="text-xs text-gray-500 mb-1">{m.label}</div>
              <NumberDisplay value={m.value} type={m.type} colorize size="lg" />
            </Card>
          </Col>
        ))}
      </Row>

      {/* 结果展示 */}
      <Tabs
        defaultActiveKey="chart"
        items={[
          {
            key: 'chart',
            label: '收益曲线',
            children: (
              <Card>
                {returnData.dates.length > 0 ? (
                  <ReturnChart data={returnData} height={400} />
                ) : (
                  <div className="h-[400px] flex items-center justify-center text-gray-500">
                    {backtestComplete ? '收益曲线数据待后端API支持' : '运行回测后显示收益曲线'}
                  </div>
                )}
              </Card>
            ),
          },
          {
            key: 'heatmap',
            label: '月度收益',
            children: (
              <Card>
                {heatmapData.years.length > 0 ? (
                  <HeatmapChart data={heatmapData} height={350} />
                ) : (
                  <div className="h-[350px] flex items-center justify-center text-gray-500">
                    {backtestComplete ? '热力图数据待后端API支持' : '运行回测后显示月度收益'}
                  </div>
                )}
              </Card>
            ),
          },
          {
            key: 'trades',
            label: '交易记录',
            children: (
              <Card>
                <Table
                  dataSource={trades}
                  columns={tradeColumns}
                  pagination={{ pageSize: 10 }}
                  loading={tradesLoading}
                  locale={{ emptyText: backtestComplete ? '暂无交易记录' : '运行回测后显示交易记录' }}
                />
              </Card>
            ),
          },
        ]}
      />

      {/* 回测完成弹窗 */}
      <Modal
        title={
          <div className="flex items-center gap-2">
            <span className="text-2xl">&#127881;</span>
            <span>回测完成</span>
          </div>
        }
        open={showCompleteModal}
        onCancel={() => setShowCompleteModal(false)}
        footer={null}
        width={500}
      >
        <div className="py-4">
          {/* 回测结果摘要 */}
          <div className="grid grid-cols-2 gap-4 mb-6">
            <div className="text-center p-4 rounded-lg bg-gray-800">
              <div className="text-gray-400 text-sm">年化收益</div>
              <div className={`text-2xl font-bold ${metrics.annualReturn >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                {(metrics.annualReturn * 100).toFixed(1)}%
              </div>
            </div>
            <div className="text-center p-4 rounded-lg bg-gray-800">
              <div className="text-gray-400 text-sm">夏普比率</div>
              <div className="text-2xl font-bold text-blue-400">
                {metrics.sharpe.toFixed(2)}
              </div>
            </div>
            <div className="text-center p-4 rounded-lg bg-gray-800">
              <div className="text-gray-400 text-sm">最大回撤</div>
              <div className="text-2xl font-bold text-yellow-400">
                {(metrics.maxDrawdown * 100).toFixed(1)}%
              </div>
            </div>
            <div className="text-center p-4 rounded-lg bg-gray-800">
              <div className="text-gray-400 text-sm">胜率</div>
              <div className="text-2xl font-bold text-purple-400">
                {(metrics.winRate * 100).toFixed(0)}%
              </div>
            </div>
          </div>

          {/* 下一步操作 */}
          <div className="text-gray-400 text-sm mb-3">接下来您可以:</div>
          <div className="space-y-3">
            <Button
              type="primary"
              icon={<RocketOutlined />}
              block
              size="large"
              onClick={handleDeploy}
            >
              部署到模拟盘
            </Button>
            <Button
              icon={<LineChartOutlined />}
              block
              onClick={handleContinueOptimize}
            >
              继续优化策略
            </Button>
            <Button
              type="text"
              block
              onClick={() => setShowCompleteModal(false)}
            >
              稍后再说
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
