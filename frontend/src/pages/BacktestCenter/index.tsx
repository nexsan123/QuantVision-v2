import { useState } from 'react'
import { Row, Col, DatePicker, Select, Button, Table, Tabs, Progress } from 'antd'
import { PlayCircleOutlined, DownloadOutlined } from '@ant-design/icons'
import { Card, NumberDisplay } from '@/components/ui'
import { ReturnChart, HeatmapChart } from '@/components/charts'
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
 * - 回测配置
 * - 结果展示
 * - 绩效归因
 */
export default function BacktestCenter() {
  const [running, setRunning] = useState(false)
  const [progress, setProgress] = useState(0)

  const handleRun = () => {
    setRunning(true)
    setProgress(0)
    const timer = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) {
          clearInterval(timer)
          setRunning(false)
          return 100
        }
        return prev + 10
      })
    }, 200)
  }

  return (
    <div className="space-y-6 animate-in">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">回测中心</h1>
        <div className="flex gap-2">
          <Button icon={<DownloadOutlined />}>导出报告</Button>
        </div>
      </div>

      {/* 回测配置 */}
      <Card title="回测配置">
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} sm={12} md={6}>
            <div className="text-sm text-gray-400 mb-2">策略</div>
            <Select defaultValue="strategy1" style={{ width: '100%' }}>
              <Select.Option value="strategy1">多因子动量策略</Select.Option>
              <Select.Option value="strategy2">价值投资策略</Select.Option>
            </Select>
          </Col>
          <Col xs={24} sm={12} md={8}>
            <div className="text-sm text-gray-400 mb-2">回测区间</div>
            <RangePicker
              defaultValue={[dayjs('2020-01-01'), dayjs('2024-06-30')]}
              style={{ width: '100%' }}
            />
          </Col>
          <Col xs={24} sm={12} md={4}>
            <div className="text-sm text-gray-400 mb-2">初始资金</div>
            <Select defaultValue="1000000" style={{ width: '100%' }}>
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
              block
            >
              {running ? '运行中...' : '运行回测'}
            </Button>
          </Col>
        </Row>
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
    </div>
  )
}
