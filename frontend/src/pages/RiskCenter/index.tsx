import { Row, Col, Progress, Alert, Tag, Button, Table } from 'antd'
import { WarningOutlined, CheckCircleOutlined, SyncOutlined } from '@ant-design/icons'
import { Card, NumberDisplay } from '@/components/ui'
import { RiskRadarChart, PieChart } from '@/components/charts'

// 模拟风险数据
const mockRiskMetrics = {
  var95: -45678.90,
  var99: -68234.56,
  cvar: -78901.23,
  volatility: 0.182,
  beta: 1.15,
  maxDrawdown: -0.0856,
  currentDrawdown: -0.0234,
  sharpe: 1.85,
}

const mockCircuitBreaker = {
  state: 'CLOSED',
  dailyPnL: -8500,
  consecutiveLosses: 2,
  triggers: {
    drawdown: { limit: 0.10, current: 0.0234 },
    dailyLoss: { limit: 0.03, current: 0.0056 },
    volatility: { limit: 0.30, current: 0.182 },
  },
}

const mockFactorExposure = {
  indicators: [
    { name: '市场', max: 2 },
    { name: '规模', max: 2 },
    { name: '价值', max: 2 },
    { name: '动量', max: 2 },
    { name: '质量', max: 2 },
    { name: '波动', max: 2 },
  ],
  values: [1.15, 0.45, 0.82, 1.25, 0.68, -0.35],
}

const mockSectorExposure = [
  { name: '科技', value: 32.5 },
  { name: '医疗', value: 18.2 },
  { name: '金融', value: 15.8 },
  { name: '消费', value: 12.4 },
  { name: '工业', value: 10.6 },
  { name: '其他', value: 10.5 },
]

const mockAlerts = [
  { id: 1, level: 'warning', message: '组合波动率接近阈值', time: '15:30:00', metric: '波动率', value: 0.182 },
  { id: 2, level: 'info', message: '今日已触发2次止损', time: '14:22:15', metric: '止损次数', value: 2 },
]

/**
 * 风险中心页面
 *
 * 功能:
 * - VaR 监控
 * - 因子暴露
 * - 熔断器状态
 * - 风险警报
 */
export default function RiskCenter() {
  return (
    <div className="space-y-6 animate-in">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">风险中心</h1>
        <Button icon={<SyncOutlined />}>刷新数据</Button>
      </div>

      {/* 风险警报 */}
      {mockAlerts.map((alert) => (
        <Alert
          key={alert.id}
          type={alert.level as 'warning' | 'info'}
          message={
            <div className="flex justify-between items-center">
              <span>{alert.message}</span>
              <span className="text-gray-500 text-sm">{alert.time}</span>
            </div>
          }
          showIcon
        />
      ))}

      {/* 风险指标 */}
      <Row gutter={[16, 16]}>
        <Col xs={12} md={6}>
          <Card padding="md">
            <div className="text-sm text-gray-500">VaR (95%)</div>
            <NumberDisplay value={mockRiskMetrics.var95} type="currency" colorize size="xl" className="mt-1" />
          </Card>
        </Col>
        <Col xs={12} md={6}>
          <Card padding="md">
            <div className="text-sm text-gray-500">VaR (99%)</div>
            <NumberDisplay value={mockRiskMetrics.var99} type="currency" colorize size="xl" className="mt-1" />
          </Card>
        </Col>
        <Col xs={12} md={6}>
          <Card padding="md">
            <div className="text-sm text-gray-500">CVaR</div>
            <NumberDisplay value={mockRiskMetrics.cvar} type="currency" colorize size="xl" className="mt-1" />
          </Card>
        </Col>
        <Col xs={12} md={6}>
          <Card padding="md">
            <div className="text-sm text-gray-500">波动率 (年化)</div>
            <NumberDisplay value={mockRiskMetrics.volatility} type="percent" size="xl" className="mt-1" />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]}>
        {/* 熔断器状态 */}
        <Col xs={24} lg={12}>
          <Card title="熔断器状态" extra={
            <Tag color={mockCircuitBreaker.state === 'CLOSED' ? 'green' : 'red'} icon={
              mockCircuitBreaker.state === 'CLOSED' ? <CheckCircleOutlined /> : <WarningOutlined />
            }>
              {mockCircuitBreaker.state === 'CLOSED' ? '正常交易' : '熔断中'}
            </Tag>
          }>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-gray-400">回撤</span>
                  <span className="font-mono">
                    {(mockCircuitBreaker.triggers.drawdown.current * 100).toFixed(2)}% / {(mockCircuitBreaker.triggers.drawdown.limit * 100).toFixed(0)}%
                  </span>
                </div>
                <Progress
                  percent={(mockCircuitBreaker.triggers.drawdown.current / mockCircuitBreaker.triggers.drawdown.limit) * 100}
                  showInfo={false}
                  strokeColor={mockCircuitBreaker.triggers.drawdown.current > mockCircuitBreaker.triggers.drawdown.limit * 0.8 ? '#ef4444' : '#3b82f6'}
                />
              </div>
              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-gray-400">日亏损</span>
                  <span className="font-mono">
                    {(mockCircuitBreaker.triggers.dailyLoss.current * 100).toFixed(2)}% / {(mockCircuitBreaker.triggers.dailyLoss.limit * 100).toFixed(0)}%
                  </span>
                </div>
                <Progress
                  percent={(mockCircuitBreaker.triggers.dailyLoss.current / mockCircuitBreaker.triggers.dailyLoss.limit) * 100}
                  showInfo={false}
                  strokeColor={mockCircuitBreaker.triggers.dailyLoss.current > mockCircuitBreaker.triggers.dailyLoss.limit * 0.8 ? '#ef4444' : '#3b82f6'}
                />
              </div>
              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-gray-400">波动率</span>
                  <span className="font-mono">
                    {(mockCircuitBreaker.triggers.volatility.current * 100).toFixed(1)}% / {(mockCircuitBreaker.triggers.volatility.limit * 100).toFixed(0)}%
                  </span>
                </div>
                <Progress
                  percent={(mockCircuitBreaker.triggers.volatility.current / mockCircuitBreaker.triggers.volatility.limit) * 100}
                  showInfo={false}
                  strokeColor={mockCircuitBreaker.triggers.volatility.current > mockCircuitBreaker.triggers.volatility.limit * 0.8 ? '#ef4444' : '#3b82f6'}
                />
              </div>
              <div className="pt-4 border-t border-dark-border flex justify-between text-sm">
                <span className="text-gray-400">今日盈亏</span>
                <NumberDisplay value={mockCircuitBreaker.dailyPnL} type="currency" colorize showSign />
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-400">连续亏损次数</span>
                <span className="font-mono">{mockCircuitBreaker.consecutiveLosses}</span>
              </div>
            </div>
          </Card>
        </Col>

        {/* 因子暴露 */}
        <Col xs={24} lg={12}>
          <Card title="因子暴露" subtitle="多因子风险分解">
            <RiskRadarChart data={mockFactorExposure} height={300} />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]}>
        {/* 行业暴露 */}
        <Col xs={24} lg={12}>
          <Card title="行业暴露" subtitle="按市值占比">
            <PieChart data={mockSectorExposure} height={300} />
          </Card>
        </Col>

        {/* 风险指标详情 */}
        <Col xs={24} lg={12}>
          <Card title="风险指标详情">
            <Table
              dataSource={[
                { key: 1, metric: 'Beta', value: mockRiskMetrics.beta, benchmark: 1.0, status: 'normal' },
                { key: 2, metric: '最大回撤', value: mockRiskMetrics.maxDrawdown, benchmark: -0.15, status: 'normal' },
                { key: 3, metric: '当前回撤', value: mockRiskMetrics.currentDrawdown, benchmark: -0.05, status: 'normal' },
                { key: 4, metric: '夏普比率', value: mockRiskMetrics.sharpe, benchmark: 1.5, status: 'good' },
              ]}
              columns={[
                { title: '指标', dataIndex: 'metric', key: 'metric' },
                { title: '当前值', dataIndex: 'value', key: 'value', render: (v: number) => (
                  <NumberDisplay value={v} type={Math.abs(v) < 10 ? 'ratio' : 'percent'} precision={2} />
                )},
                { title: '基准', dataIndex: 'benchmark', key: 'benchmark', render: (v: number) => (
                  <span className="text-gray-500 font-mono">{v}</span>
                )},
                { title: '状态', dataIndex: 'status', key: 'status', render: (s: string) => (
                  <Tag color={s === 'good' ? 'green' : s === 'warning' ? 'orange' : 'blue'}>
                    {s === 'good' ? '优秀' : s === 'warning' ? '警告' : '正常'}
                  </Tag>
                )},
              ]}
              pagination={false}
              size="small"
            />
          </Card>
        </Col>
      </Row>
    </div>
  )
}
