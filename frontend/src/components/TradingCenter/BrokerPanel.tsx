/**
 * Phase 12: \u6267\u884c\u5c42\u5347\u7ea7 - \u5238\u5546\u8fde\u63a5\u9762\u677f
 *
 * \u663e\u793a:
 * - \u5238\u5546\u8fde\u63a5\u72b6\u6001
 * - \u8d26\u6237\u4fe1\u606f\u6982\u89c8
 * - \u5e02\u573a\u72b6\u6001
 */

import { useState, useEffect, useCallback } from 'react'
import {
  Row, Col, Tag, Switch, Statistic, Space, Alert, message
} from 'antd'
import {
  ApiOutlined, CheckCircleOutlined, CloseCircleOutlined,
  LoadingOutlined, DollarOutlined, StockOutlined, BankOutlined
} from '@ant-design/icons'
import { Card } from '@/components/ui'
import {
  BrokerType, BrokerConnectionStatus,
  BROKER_LABELS
} from '@/types/trading'

interface BrokerStatus {
  broker: BrokerType
  status: BrokerConnectionStatus
  paperTrading: boolean
  account: {
    equity: number
    buyingPower: number
    cash: number
    dayPnl: number
    dayPnlPercent: number
  } | null
  marketStatus: 'open' | 'closed' | 'pre_market' | 'after_hours'
  lastUpdate: string
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || ''

export default function BrokerPanel() {
  const [status, setStatus] = useState<BrokerStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [connecting, setConnecting] = useState(false)

  const fetchStatus = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/trading/status`)
      if (response.ok) {
        const data = await response.json()
        setStatus(data)
      }
    } catch (err) {
      console.error('\u52a0\u8f7d\u5238\u5546\u72b6\u6001\u5931\u8d25:', err)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchStatus()
    const interval = setInterval(fetchStatus, 10000)
    return () => clearInterval(interval)
  }, [fetchStatus])

  const handleTogglePaperTrading = async (enabled: boolean) => {
    setConnecting(true)
    try {
      const endpoint = enabled ? '/api/v1/trading/paper/enable' : '/api/v1/trading/paper/disable'
      const response = await fetch(`${API_BASE_URL}${endpoint}`, { method: 'POST' })
      if (response.ok) {
        message.success(enabled ? 'Paper Trading \u5df2\u542f\u7528' : '\u5df2\u5207\u6362\u5230\u5b9e\u76d8')
        fetchStatus()
      }
    } catch (err) {
      message.error('\u5207\u6362\u5931\u8d25')
    } finally {
      setConnecting(false)
    }
  }

  const getStatusIcon = (status: BrokerConnectionStatus) => {
    switch (status) {
      case 'connected':
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />
      case 'connecting':
        return <LoadingOutlined style={{ color: '#1890ff' }} />
      case 'error':
        return <CloseCircleOutlined style={{ color: '#ff4d4f' }} />
      default:
        return <CloseCircleOutlined style={{ color: '#d9d9d9' }} />
    }
  }

  const getMarketStatusTag = (marketStatus: string) => {
    switch (marketStatus) {
      case 'open':
        return <Tag color="green">{'\u5f00\u5e02'}</Tag>
      case 'pre_market':
        return <Tag color="blue">{'\u76d8\u524d'}</Tag>
      case 'after_hours':
        return <Tag color="orange">{'\u76d8\u540e'}</Tag>
      default:
        return <Tag>{'\u4f11\u5e02'}</Tag>
    }
  }

  if (loading) {
    return (
      <Card>
        <div className="flex justify-center items-center h-32">
          <LoadingOutlined style={{ fontSize: 24 }} />
        </div>
      </Card>
    )
  }

  return (
    <div className="space-y-4">
      {/* \u5238\u5546\u8fde\u63a5\u72b6\u6001 */}
      <Card
        title={
          <Space>
            <ApiOutlined />
            {'\u5238\u5546\u8fde\u63a5'}
          </Space>
        }
        extra={
          <Space>
            <span className="text-gray-500 text-sm">Paper Trading</span>
            <Switch
              checked={status?.paperTrading}
              onChange={handleTogglePaperTrading}
              loading={connecting}
            />
          </Space>
        }
      >
        <Row gutter={24}>
          <Col span={8}>
            <div className="flex items-center gap-3">
              {getStatusIcon(status?.status || 'disconnected')}
              <div>
                <div className="text-lg font-medium">
                  {BROKER_LABELS[status?.broker || 'paper']}
                </div>
                <div className="text-gray-500 text-sm">
                  {status?.status === 'connected' ? '\u5df2\u8fde\u63a5' : '\u672a\u8fde\u63a5'}
                </div>
              </div>
            </div>
          </Col>
          <Col span={8}>
            <div className="flex items-center gap-3">
              <StockOutlined style={{ fontSize: 24, color: '#1890ff' }} />
              <div>
                <div className="text-lg font-medium">{'\u5e02\u573a\u72b6\u6001'}</div>
                <div>{getMarketStatusTag(status?.marketStatus || 'closed')}</div>
              </div>
            </div>
          </Col>
          <Col span={8}>
            <div className="flex items-center gap-3">
              <BankOutlined style={{ fontSize: 24, color: '#faad14' }} />
              <div>
                <div className="text-lg font-medium">{'\u4ea4\u6613\u6a21\u5f0f'}</div>
                <Tag color={status?.paperTrading ? 'blue' : 'green'}>
                  {status?.paperTrading ? '\u6a21\u62df\u76d8' : '\u5b9e\u76d8'}
                </Tag>
              </div>
            </div>
          </Col>
        </Row>
      </Card>

      {/* \u8d26\u6237\u6982\u89c8 */}
      {status?.account && (
        <Row gutter={16}>
          <Col span={6}>
            <Card>
              <Statistic
                title={'\u8d26\u6237\u51c0\u503c'}
                value={status.account.equity}
                precision={2}
                prefix={<DollarOutlined />}
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title={'\u8d2d\u4e70\u529b'}
                value={status.account.buyingPower}
                precision={2}
                prefix="$"
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title={'\u73b0\u91d1'}
                value={status.account.cash}
                precision={2}
                prefix="$"
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title={'\u4eca\u65e5\u76c8\u4e8f'}
                value={status.account.dayPnl}
                precision={2}
                prefix="$"
                suffix={
                  <span className="text-sm">
                    ({status.account.dayPnlPercent >= 0 ? '+' : ''}{status.account.dayPnlPercent.toFixed(2)}%)
                  </span>
                }
                valueStyle={{
                  color: status.account.dayPnl >= 0 ? '#52c41a' : '#ff4d4f'
                }}
              />
            </Card>
          </Col>
        </Row>
      )}

      {/* Paper Trading \u63d0\u793a */}
      {status?.paperTrading && (
        <Alert
          type="info"
          showIcon
          message="Paper Trading \u6a21\u5f0f"
          description={'\u5f53\u524d\u4e3a\u6a21\u62df\u4ea4\u6613\u6a21\u5f0f\uff0c\u6240\u6709\u4ea4\u6613\u4e0d\u4f1a\u5f71\u54cd\u5b9e\u9645\u8d44\u91d1\u3002'}
        />
      )}
    </div>
  )
}
