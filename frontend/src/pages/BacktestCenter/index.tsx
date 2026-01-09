import { useState, useEffect } from 'react'
import { Row, Col, DatePicker, Select, Button, Table, Tabs, Progress, Modal, message } from 'antd'
import { PlayCircleOutlined, DownloadOutlined, RocketOutlined, LineChartOutlined, ArrowLeftOutlined } from '@ant-design/icons'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { Card, NumberDisplay } from '@/components/ui'
import { ReturnChart, HeatmapChart } from '@/components/Chart'
import { getStrategies, getStrategy, updateBacktestResult, updateStrategy } from '@/services/strategyService'
import type { Strategy, BacktestSummary } from '@/types/strategy'
import dayjs from 'dayjs'

const { RangePicker } = DatePicker

// 模拟回测结果
const mockMetrics = {
  totalReturn: 0.4523,
  annualReturn: 0.1856,
  sharpe: 1.92,
  sortino: 2.45,
  maxDrawdown: -0.1234,
  winRate: 0.58,
  profitFactor: 1.85,
  calmar: 1.51,
}

const mockReturnData = {
  dates: ['2020-01', '2020-06', '2021-01', '2021-06', '2022-01', '2022-06', '2023-01', '2023-06', '2024-01', '2024-06'],
  strategy: [0, 0.08, 0.15, 0.22, 0.18, 0.25, 0.32, 0.38, 0.42, 0.45],
  benchmark: [0, 0.05, 0.10, 0.12, 0.08, 0.14, 0.18, 0.22, 0.26, 0.30],
}

const mockHeatmapData = {
  years: ['2024', '2023', '2022', '2021', '2020'],
  months: ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月'],
  values: [
    [0.02, 0.03, -0.01, 0.04, 0.02, 0.01, 0, 0, 0, 0, 0, 0],
    [0.03, -0.02, 0.04, 0.01, 0.03, -0.01, 0.02, 0.05, -0.02, 0.03, 0.02, 0.04],
    [-0.05, 0.02, -0.03, 0.01, -0.02, 0.04, 0.02, -0.01, 0.03, -0.04, 0.02, 0.01],
    [0.04, 0.03, 0.02, 0.05, 0.01, 0.03, 0.02, 0.04, -0.01, 0.02, 0.03, 0.05],
    [-0.08, 0.06, 0.04, 0.08, 0.03, 0.02, 0.01, 0.03, -0.02, 0.04, 0.05, 0.03],
  ],
}

const tradeColumns = [
  { title: '日期', dataIndex: 'date', key: 'date' },
  { title: '股票', dataIndex: 'symbol', key: 'symbol' },
  { title: '方向', dataIndex: 'side', key: 'side', render: (s: string) => (
    <span className={s === 'BUY' ? 'text-profit' : 'text-loss'}>{s}</span>
  )},
  { title: '数量', dataIndex: 'qty', key: 'qty', className: 'text-right font-mono' },
  { title: '价格', dataIndex: 'price', key: 'price', className: 'text-right font-mono', render: (p: number) => `$${p}` },
  { title: '盈亏', dataIndex: 'pnl', key: 'pnl', className: 'text-right', render: (v: number) => (
    <NumberDisplay value={v} type="currency" colorize showSign />
  )},
]

const mockTrades = [
  { key: 1, date: '2024-06-01', symbol: 'AAPL', side: 'BUY', qty: 100, price: 178.52, pnl: 1250 },
  { key: 2, date: '2024-05-15', symbol: 'MSFT', side: 'SELL', qty: 50, price: 420.15, pnl: 850 },
  { key: 3, date: '2024-05-01', symbol: 'GOOGL', side: 'BUY', qty: 30, price: 172.50, pnl: -320 },
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

  // 运行回测
  const handleRun = () => {
    if (!selectedStrategy) {
      message.warning('请先选择策略')
      return
    }

    setRunning(true)
    setProgress(0)
    setBacktestComplete(false)

    const timer = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) {
          clearInterval(timer)
          setRunning(false)
          setBacktestComplete(true)

          // 模拟保存回测结果
          const backtestResult: BacktestSummary = {
            backtestId: `bt-${Date.now()}`,
            annualReturn: mockMetrics.annualReturn,
            sharpeRatio: mockMetrics.sharpe,
            maxDrawdown: mockMetrics.maxDrawdown,
            winRate: mockMetrics.winRate,
            startDate: dateRange[0].format('YYYY-MM-DD'),
            endDate: dateRange[1].format('YYYY-MM-DD'),
            completedAt: new Date().toISOString(),
          }

          if (selectedStrategy) {
            // 保存回测结果并更新策略状态
            Promise.all([
              updateBacktestResult(selectedStrategy.id, backtestResult),
              // 如果策略是草稿状态，更新为已回测状态
              selectedStrategy.status === 'draft'
                ? updateStrategy(selectedStrategy.id, { status: 'backtest' })
                : Promise.resolve(null),
            ])
              .then(() => {
                message.success('回测完成!')
                // 更新本地状态
                setSelectedStrategy(prev =>
                  prev ? { ...prev, lastBacktest: backtestResult, status: prev.status === 'draft' ? 'backtest' : prev.status } : null
                )
                // 显示完成弹窗
                setShowCompleteModal(true)
              })
              .catch(() => {
                message.error('保存回测结果失败')
              })
          }

          return 100
        }
        return prev + 10
      })
    }, 200)
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
          { label: '总收益', value: mockMetrics.totalReturn, type: 'percent' as const },
          { label: '年化收益', value: mockMetrics.annualReturn, type: 'percent' as const },
          { label: '夏普比率', value: mockMetrics.sharpe, type: 'ratio' as const },
          { label: '索提诺', value: mockMetrics.sortino, type: 'ratio' as const },
          { label: '最大回撤', value: mockMetrics.maxDrawdown, type: 'percent' as const },
          { label: '胜率', value: mockMetrics.winRate, type: 'percent' as const },
          { label: '盈亏比', value: mockMetrics.profitFactor, type: 'ratio' as const },
          { label: 'Calmar', value: mockMetrics.calmar, type: 'ratio' as const },
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
                <ReturnChart data={mockReturnData} height={400} />
              </Card>
            ),
          },
          {
            key: 'heatmap',
            label: '月度收益',
            children: (
              <Card>
                <HeatmapChart data={mockHeatmapData} height={350} />
              </Card>
            ),
          },
          {
            key: 'trades',
            label: '交易记录',
            children: (
              <Card>
                <Table
                  dataSource={mockTrades}
                  columns={tradeColumns}
                  pagination={{ pageSize: 10 }}
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
              <div className={`text-2xl font-bold ${mockMetrics.annualReturn >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                {(mockMetrics.annualReturn * 100).toFixed(1)}%
              </div>
            </div>
            <div className="text-center p-4 rounded-lg bg-gray-800">
              <div className="text-gray-400 text-sm">夏普比率</div>
              <div className="text-2xl font-bold text-blue-400">
                {mockMetrics.sharpe.toFixed(2)}
              </div>
            </div>
            <div className="text-center p-4 rounded-lg bg-gray-800">
              <div className="text-gray-400 text-sm">最大回撤</div>
              <div className="text-2xl font-bold text-yellow-400">
                {(mockMetrics.maxDrawdown * 100).toFixed(1)}%
              </div>
            </div>
            <div className="text-center p-4 rounded-lg bg-gray-800">
              <div className="text-gray-400 text-sm">胜率</div>
              <div className="text-2xl font-bold text-purple-400">
                {(mockMetrics.winRate * 100).toFixed(0)}%
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
