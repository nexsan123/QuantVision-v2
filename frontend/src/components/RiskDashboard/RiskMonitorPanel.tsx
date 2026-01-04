/**
 * Phase 10: \u98ce\u9669\u7cfb\u7edf\u5347\u7ea7 - \u98ce\u9669\u76d1\u63a7\u9762\u677f
 *
 * \u5b9e\u65f6\u663e\u793a:
 * - \u5f53\u524d\u98ce\u9669\u6307\u6807 (\u56de\u64a4/VaR/\u6ce2\u52a8\u7387)
 * - \u56e0\u5b50\u66b4\u9732\u72b6\u6001
 * - \u6d3b\u8dc3\u8b66\u62a5
 * - \u7efc\u5408\u98ce\u9669\u8bc4\u5206
 */

import { useState, useEffect, useCallback } from 'react'
import { Row, Col, Progress, Tag, Alert, Badge, Statistic, Tooltip } from 'antd'
import {
  WarningOutlined, AlertOutlined, DashboardOutlined,
  ArrowUpOutlined, ArrowDownOutlined, SyncOutlined
} from '@ant-design/icons'
import { Card } from '@/components/ui'
import {
  RiskMonitorStatus, RiskAlert, AlertLevel,
  ALERT_LEVEL_COLORS, RISK_LEVEL_COLORS
} from '@/types/risk'

interface RiskMonitorPanelProps {
  portfolioId?: string
  refreshInterval?: number  // \u6beb\u79d2
  onAlertClick?: (alert: RiskAlert) => void
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || ''

export default function RiskMonitorPanel({
  portfolioId,
  refreshInterval = 30000,
  onAlertClick
}: RiskMonitorPanelProps) {
  const [status, setStatus] = useState<RiskMonitorStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null)

  const fetchStatus = useCallback(async () => {
    try {
      const params = new URLSearchParams()
      if (portfolioId) params.append('portfolio_id', portfolioId)

      const response = await fetch(
        `${API_BASE_URL}/api/v1/risk/advanced/monitor/status?${params}`
      )

      if (!response.ok) {
        throw new Error('\u83b7\u53d6\u76d1\u63a7\u72b6\u6001\u5931\u8d25')
      }

      const data = await response.json()
      setStatus(data)
      setLastUpdate(new Date())
      setError(null)
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [portfolioId])

  useEffect(() => {
    fetchStatus()
    const interval = setInterval(fetchStatus, refreshInterval)
    return () => clearInterval(interval)
  }, [fetchStatus, refreshInterval])

  if (loading && !status) {
    return (
      <Card>
        <div className="flex items-center justify-center h-48">
          <SyncOutlined spin className="text-2xl text-primary-500" />
        </div>
      </Card>
    )
  }

  if (error && !status) {
    return (
      <Alert
        type="error"
        message={'\u52a0\u8f7d\u5931\u8d25'}
        description={error}
        showIcon
      />
    )
  }

  if (!status) return null

  const getRiskLevelColor = (level: string) => {
    return RISK_LEVEL_COLORS[level] || '#666'
  }

  const getAlertLevelColor = (level: AlertLevel) => {
    return ALERT_LEVEL_COLORS[level] || '#666'
  }

  const getStatusColor = (status: 'normal' | 'warning' | 'breach') => {
    switch (status) {
      case 'normal': return '#52c41a'
      case 'warning': return '#faad14'
      case 'breach': return '#ff4d4f'
      default: return '#666'
    }
  }

  const formatPercent = (value: number) => {
    return `${(value * 100).toFixed(2)}%`
  }

  return (
    <div className="space-y-4">
      {/* \u7efc\u5408\u98ce\u9669\u8bc4\u5206 */}
      <Card
        title={
          <span>
            <DashboardOutlined className="mr-2" />
            {'\u7efc\u5408\u98ce\u9669\u8bc4\u4f30'}
          </span>
        }
        extra={
          <span className="text-gray-500 text-sm">
            {'\u66f4\u65b0: '}{lastUpdate?.toLocaleTimeString() || '-'}
          </span>
        }
      >
        <Row gutter={24} align="middle">
          <Col span={8}>
            <div className="text-center">
              <Progress
                type="dashboard"
                percent={status.riskScore}
                strokeColor={{
                  '0%': '#52c41a',
                  '50%': '#faad14',
                  '100%': '#ff4d4f',
                }}
                format={(percent) => (
                  <div>
                    <div className="text-2xl font-bold">{percent}</div>
                    <div className="text-xs text-gray-500">{'\u98ce\u9669\u5206'}</div>
                  </div>
                )}
              />
            </div>
          </Col>
          <Col span={8}>
            <div className="text-center">
              <Tag
                color={getRiskLevelColor(status.riskLevel)}
                className="text-lg px-4 py-1"
              >
                {status.riskLevel === 'low' && '\u4f4e\u98ce\u9669'}
                {status.riskLevel === 'medium' && '\u4e2d\u98ce\u9669'}
                {status.riskLevel === 'high' && '\u9ad8\u98ce\u9669'}
                {status.riskLevel === 'critical' && '\u4e25\u91cd\u98ce\u9669'}
              </Tag>
              <div className="mt-2 text-gray-500 text-sm">
                {status.activeAlerts.length > 0 ? (
                  <span className="text-red-500">
                    <WarningOutlined className="mr-1" />
                    {status.activeAlerts.length} {'\u4e2a\u6d3b\u8dc3\u8b66\u62a5'}
                  </span>
                ) : (
                  <span className="text-green-500">{'\u65e0\u6d3b\u8dc3\u8b66\u62a5'}</span>
                )}
              </div>
            </div>
          </Col>
          <Col span={8}>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">{'\u5e02\u573a Beta'}</span>
                <span style={{ color: getStatusColor(status.factorExposureStatus.market.status) }}>
                  {status.factorExposureStatus.market.current.toFixed(2)}
                </span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">{'\u6700\u5927\u884c\u4e1a\u66b4\u9732'}</span>
                <span style={{ color: getStatusColor(status.factorExposureStatus.maxIndustry.status) }}>
                  {formatPercent(status.factorExposureStatus.maxIndustry.current)}
                </span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">{'\u6700\u5927\u98ce\u683c\u66b4\u9732'}</span>
                <span style={{ color: getStatusColor(status.factorExposureStatus.maxStyle.status) }}>
                  {status.factorExposureStatus.maxStyle.current.toFixed(2)}
                </span>
              </div>
            </div>
          </Col>
        </Row>
      </Card>

      {/* \u5f53\u524d\u98ce\u9669\u6307\u6807 */}
      <Card title={'\u5f53\u524d\u98ce\u9669\u6307\u6807'}>
        <Row gutter={24}>
          <Col span={8}>
            <Statistic
              title={'\u5f53\u524d\u56de\u64a4'}
              value={status.currentMetrics.drawdown * 100}
              precision={2}
              suffix="%"
              valueStyle={{
                color: status.currentMetrics.drawdown > status.currentMetrics.drawdownLimit * 0.8
                  ? '#ff4d4f'
                  : status.currentMetrics.drawdown > status.currentMetrics.drawdownLimit * 0.5
                    ? '#faad14'
                    : '#52c41a'
              }}
              prefix={<ArrowDownOutlined />}
            />
            <Progress
              percent={(status.currentMetrics.drawdown / status.currentMetrics.drawdownLimit) * 100}
              showInfo={false}
              strokeColor={{
                '0%': '#52c41a',
                '80%': '#faad14',
                '100%': '#ff4d4f',
              }}
              size="small"
            />
            <div className="text-xs text-gray-500 mt-1">
              {'\u9650\u5236: '}{formatPercent(status.currentMetrics.drawdownLimit)}
            </div>
          </Col>

          <Col span={8}>
            <Statistic
              title={'95% VaR'}
              value={status.currentMetrics.var95 * 100}
              precision={2}
              suffix="%"
              valueStyle={{
                color: status.currentMetrics.var95 > status.currentMetrics.varLimit * 0.8
                  ? '#ff4d4f'
                  : status.currentMetrics.var95 > status.currentMetrics.varLimit * 0.5
                    ? '#faad14'
                    : '#52c41a'
              }}
            />
            <Progress
              percent={(status.currentMetrics.var95 / status.currentMetrics.varLimit) * 100}
              showInfo={false}
              strokeColor={{
                '0%': '#52c41a',
                '80%': '#faad14',
                '100%': '#ff4d4f',
              }}
              size="small"
            />
            <div className="text-xs text-gray-500 mt-1">
              {'\u9650\u5236: '}{formatPercent(status.currentMetrics.varLimit)}
            </div>
          </Col>

          <Col span={8}>
            <Statistic
              title={'\u6ce2\u52a8\u7387 (\u5e74\u5316)'}
              value={status.currentMetrics.volatility * 100}
              precision={2}
              suffix="%"
              valueStyle={{
                color: status.currentMetrics.volatility > status.currentMetrics.volatilityLimit * 0.8
                  ? '#ff4d4f'
                  : status.currentMetrics.volatility > status.currentMetrics.volatilityLimit * 0.5
                    ? '#faad14'
                    : '#52c41a'
              }}
            />
            <Progress
              percent={(status.currentMetrics.volatility / status.currentMetrics.volatilityLimit) * 100}
              showInfo={false}
              strokeColor={{
                '0%': '#52c41a',
                '80%': '#faad14',
                '100%': '#ff4d4f',
              }}
              size="small"
            />
            <div className="text-xs text-gray-500 mt-1">
              {'\u9650\u5236: '}{formatPercent(status.currentMetrics.volatilityLimit)}
            </div>
          </Col>
        </Row>
      </Card>

      {/* \u6d3b\u8dc3\u8b66\u62a5 */}
      {status.activeAlerts.length > 0 && (
        <Card
          title={
            <span className="text-red-500">
              <AlertOutlined className="mr-2" />
              {'\u6d3b\u8dc3\u8b66\u62a5'} ({status.activeAlerts.length})
            </span>
          }
        >
          <div className="space-y-2">
            {status.activeAlerts.map((alert) => (
              <Alert
                key={alert.id}
                type={
                  alert.level === 'emergency' || alert.level === 'critical'
                    ? 'error'
                    : alert.level === 'warning'
                      ? 'warning'
                      : 'info'
                }
                message={
                  <div className="flex justify-between items-center">
                    <span>{alert.message}</span>
                    <Tag color={getAlertLevelColor(alert.level)}>
                      {alert.level.toUpperCase()}
                    </Tag>
                  </div>
                }
                description={
                  <div className="text-sm text-gray-500">
                    {'\u5f53\u524d\u503c: '}{alert.currentValue.toFixed(4)} | {'\u9608\u503c: '}{alert.threshold.toFixed(4)}
                    <span className="ml-4">
                      {new Date(alert.timestamp).toLocaleString()}
                    </span>
                  </div>
                }
                showIcon
                onClick={() => onAlertClick?.(alert)}
                className="cursor-pointer hover:bg-dark-hover transition"
              />
            ))}
          </div>
        </Card>
      )}
    </div>
  )
}
