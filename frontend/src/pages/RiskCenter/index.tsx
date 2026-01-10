import { useState, useEffect, useCallback } from 'react'
import { Row, Col, Progress, Alert, Tag, Button, Table, message, Spin } from 'antd'
import { WarningOutlined, CheckCircleOutlined, SyncOutlined, LoadingOutlined } from '@ant-design/icons'
import { Card, NumberDisplay } from '@/components/ui'
import { RiskRadarChart, PieChart } from '@/components/Chart'
import {
  getCircuitBreakerStatus,
  getRiskAlerts,
  getRiskScore,
  getRiskMonitorStatus,
  type CircuitBreakerStatus,
  type RiskAlert,
} from '@/services/riskService'

// 默认风险指标 (未加载时显示)
const defaultRiskMetrics = {
  var95: 0,
  var99: 0,
  cvar: 0,
  volatility: 0,
  beta: 1.0,
  maxDrawdown: 0,
  currentDrawdown: 0,
  sharpe: 0,
}

// 默认熔断器状态
const defaultCircuitBreaker: CircuitBreakerStatus & {
  triggers: {
    drawdown: { limit: number; current: number }
    dailyLoss: { limit: number; current: number }
    volatility: { limit: number; current: number }
  }
} = {
  state: 'CLOSED',
  isTripped: false,
  canTrade: true,
  triggerReason: null,
  triggeredAt: null,
  consecutiveLosses: 0,
  dailyPnl: 0,
  triggers: {
    drawdown: { limit: 0.10, current: 0 },
    dailyLoss: { limit: 0.03, current: 0 },
    volatility: { limit: 0.30, current: 0 },
  },
}

// 默认因子暴露 (这部分可能需要后端提供专门 API)
const defaultFactorExposure = {
  indicators: [
    { name: '市场', max: 2 },
    { name: '规模', max: 2 },
    { name: '价值', max: 2 },
    { name: '动量', max: 2 },
    { name: '质量', max: 2 },
    { name: '波动', max: 2 },
  ],
  values: [0, 0, 0, 0, 0, 0],
}

// 默认行业暴露 (这部分可能需要后端提供专门 API)
const defaultSectorExposure = [
  { name: '暂无数据', value: 100 },
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
  // 加载状态
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)

  // 风险数据状态
  const [riskMetrics, setRiskMetrics] = useState(defaultRiskMetrics)
  const [circuitBreaker, setCircuitBreaker] = useState(defaultCircuitBreaker)
  const [alerts, setAlerts] = useState<RiskAlert[]>([])
  // TODO: 因子暴露和行业暴露需要后端额外 API 支持
  const [factorExposure, /* setFactorExposure */] = useState(defaultFactorExposure)
  const [sectorExposure, /* setSectorExposure */] = useState(defaultSectorExposure)

  // 加载数据
  const loadData = useCallback(async (showRefreshing = false) => {
    if (showRefreshing) setRefreshing(true)
    else setLoading(true)

    try {
      // 并行请求多个 API
      const [cbStatus, alertsData, scoreData, monitorStatus] = await Promise.all([
        getCircuitBreakerStatus().catch(() => null),
        getRiskAlerts({ sinceHours: 24 }).catch(() => []),
        getRiskScore().catch(() => null),
        getRiskMonitorStatus().catch(() => null),
      ])

      // 更新熔断器状态
      if (cbStatus) {
        setCircuitBreaker(prev => ({
          ...prev,
          ...cbStatus,
        }))
      }

      // 更新警报
      setAlerts(alertsData)

      // 更新风险指标 (从 score 和 monitor 中提取)
      if (scoreData && monitorStatus) {
        setRiskMetrics(prev => ({
          ...prev,
          currentDrawdown: scoreData.currentDrawdown,
          volatility: monitorStatus.currentVolatility,
        }))

        // 更新熔断器触发器当前值
        setCircuitBreaker(prev => ({
          ...prev,
          triggers: {
            ...prev.triggers,
            drawdown: { ...prev.triggers.drawdown, current: Math.abs(scoreData.currentDrawdown) },
            volatility: { ...prev.triggers.volatility, current: monitorStatus.currentVolatility },
          },
        }))
      }

      // TODO: 因子暴露和行业暴露需要后端额外 API 支持
      // 目前保持默认值

    } catch (err) {
      console.error('加载风险数据失败:', err)
      message.error('加载风险数据失败')
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [])

  // 初始加载
  useEffect(() => {
    loadData()
  }, [loadData])

  // 处理刷新
  const handleRefresh = () => {
    loadData(true)
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Spin indicator={<LoadingOutlined style={{ fontSize: 48 }} spin />} />
      </div>
    )
  }

  return (
    <div className="space-y-6 animate-in">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">风险中心</h1>
        <Button icon={<SyncOutlined spin={refreshing} />} onClick={handleRefresh} loading={refreshing}>
          刷新数据
        </Button>
      </div>

      {/* 风险警报 */}
      {alerts.length > 0 ? alerts.map((alert, index) => (
        <Alert
          key={index}
          type={alert.level === 'critical' || alert.level === 'emergency' ? 'error' : alert.level}
          message={
            <div className="flex justify-between items-center">
              <span>{alert.message}</span>
              <span className="text-gray-500 text-sm">{alert.timestamp?.split('T')[1]?.substring(0, 8) || ''}</span>
            </div>
          }
          showIcon
        />
      )) : (
        <Alert type="success" message="暂无风险警报" showIcon />
      )}

      {/* 风险指标 */}
      <Row gutter={[16, 16]}>
        <Col xs={12} md={6}>
          <Card padding="md">
            <div className="text-sm text-gray-500">VaR (95%)</div>
            <NumberDisplay value={riskMetrics.var95} type="currency" colorize size="xl" className="mt-1" />
          </Card>
        </Col>
        <Col xs={12} md={6}>
          <Card padding="md">
            <div className="text-sm text-gray-500">VaR (99%)</div>
            <NumberDisplay value={riskMetrics.var99} type="currency" colorize size="xl" className="mt-1" />
          </Card>
        </Col>
        <Col xs={12} md={6}>
          <Card padding="md">
            <div className="text-sm text-gray-500">CVaR</div>
            <NumberDisplay value={riskMetrics.cvar} type="currency" colorize size="xl" className="mt-1" />
          </Card>
        </Col>
        <Col xs={12} md={6}>
          <Card padding="md">
            <div className="text-sm text-gray-500">波动率 (年化)</div>
            <NumberDisplay value={riskMetrics.volatility} type="percent" size="xl" className="mt-1" />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]}>
        {/* 熔断器状态 */}
        <Col xs={24} lg={12}>
          <Card title="熔断器状态" extra={
            <Tag color={circuitBreaker.state === 'CLOSED' ? 'green' : 'red'} icon={
              circuitBreaker.state === 'CLOSED' ? <CheckCircleOutlined /> : <WarningOutlined />
            }>
              {circuitBreaker.state === 'CLOSED' ? '正常交易' : '熔断中'}
            </Tag>
          }>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-gray-400">回撤</span>
                  <span className="font-mono">
                    {(circuitBreaker.triggers.drawdown.current * 100).toFixed(2)}% / {(circuitBreaker.triggers.drawdown.limit * 100).toFixed(0)}%
                  </span>
                </div>
                <Progress
                  percent={circuitBreaker.triggers.drawdown.limit > 0 ? (circuitBreaker.triggers.drawdown.current / circuitBreaker.triggers.drawdown.limit) * 100 : 0}
                  showInfo={false}
                  strokeColor={circuitBreaker.triggers.drawdown.current > circuitBreaker.triggers.drawdown.limit * 0.8 ? '#ef4444' : '#3b82f6'}
                />
              </div>
              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-gray-400">日亏损</span>
                  <span className="font-mono">
                    {(circuitBreaker.triggers.dailyLoss.current * 100).toFixed(2)}% / {(circuitBreaker.triggers.dailyLoss.limit * 100).toFixed(0)}%
                  </span>
                </div>
                <Progress
                  percent={circuitBreaker.triggers.dailyLoss.limit > 0 ? (circuitBreaker.triggers.dailyLoss.current / circuitBreaker.triggers.dailyLoss.limit) * 100 : 0}
                  showInfo={false}
                  strokeColor={circuitBreaker.triggers.dailyLoss.current > circuitBreaker.triggers.dailyLoss.limit * 0.8 ? '#ef4444' : '#3b82f6'}
                />
              </div>
              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-gray-400">波动率</span>
                  <span className="font-mono">
                    {(circuitBreaker.triggers.volatility.current * 100).toFixed(1)}% / {(circuitBreaker.triggers.volatility.limit * 100).toFixed(0)}%
                  </span>
                </div>
                <Progress
                  percent={circuitBreaker.triggers.volatility.limit > 0 ? (circuitBreaker.triggers.volatility.current / circuitBreaker.triggers.volatility.limit) * 100 : 0}
                  showInfo={false}
                  strokeColor={circuitBreaker.triggers.volatility.current > circuitBreaker.triggers.volatility.limit * 0.8 ? '#ef4444' : '#3b82f6'}
                />
              </div>
              <div className="pt-4 border-t border-dark-border flex justify-between text-sm">
                <span className="text-gray-400">今日盈亏</span>
                <NumberDisplay value={circuitBreaker.dailyPnl} type="currency" colorize showSign />
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-400">连续亏损次数</span>
                <span className="font-mono">{circuitBreaker.consecutiveLosses}</span>
              </div>
            </div>
          </Card>
        </Col>

        {/* 因子暴露 */}
        <Col xs={24} lg={12}>
          <Card title="因子暴露" subtitle="多因子风险分解">
            <RiskRadarChart data={factorExposure} height={300} />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]}>
        {/* 行业暴露 */}
        <Col xs={24} lg={12}>
          <Card title="行业暴露" subtitle="按市值占比">
            <PieChart data={sectorExposure} height={300} />
          </Card>
        </Col>

        {/* 风险指标详情 */}
        <Col xs={24} lg={12}>
          <Card title="风险指标详情">
            <Table
              dataSource={[
                { key: 1, metric: 'Beta', value: riskMetrics.beta, benchmark: 1.0, status: 'normal' },
                { key: 2, metric: '最大回撤', value: riskMetrics.maxDrawdown, benchmark: -0.15, status: 'normal' },
                { key: 3, metric: '当前回撤', value: riskMetrics.currentDrawdown, benchmark: -0.05, status: 'normal' },
                { key: 4, metric: '夏普比率', value: riskMetrics.sharpe, benchmark: 1.5, status: 'good' },
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
