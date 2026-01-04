/**
 * Phase 12: \u6267\u884c\u5c42\u5347\u7ea7 - \u6301\u4ed3\u8868\u683c
 *
 * \u663e\u793a:
 * - \u5f53\u524d\u6301\u4ed3
 * - \u672a\u5b9e\u73b0\u76c8\u4e8f
 * - \u6301\u4ed3\u5206\u5e03
 */

import { useState, useEffect, useCallback } from 'react'
import { Table, Tag, Progress, Tooltip, Space, Empty, Statistic, Row, Col } from 'antd'
import {
  RiseOutlined, FallOutlined, StockOutlined, DollarOutlined
} from '@ant-design/icons'
import { Card } from '@/components/ui'
import { BrokerPosition } from '@/types/trading'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || ''

export default function PositionsTable() {
  const [positions, setPositions] = useState<BrokerPosition[]>([])
  const [loading, setLoading] = useState(true)
  const [totalValue, setTotalValue] = useState(0)
  const [totalPnl, setTotalPnl] = useState(0)

  const fetchPositions = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/trading/positions`)
      if (response.ok) {
        const data = await response.json()
        if (data.success) {
          setPositions(data.positions || [])
          setTotalValue(data.total_value || 0)
          setTotalPnl(data.unrealized_pnl || 0)
        }
      }
    } catch (err) {
      console.error('\u52a0\u8f7d\u6301\u4ed3\u5931\u8d25:', err)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchPositions()
    const interval = setInterval(fetchPositions, 10000)
    return () => clearInterval(interval)
  }, [fetchPositions])

  const columns = [
    {
      title: '\u80a1\u7968',
      dataIndex: 'symbol',
      key: 'symbol',
      width: 100,
      render: (symbol: string) => (
        <span className="font-medium">{symbol}</span>
      ),
    },
    {
      title: '\u65b9\u5411',
      dataIndex: 'side',
      key: 'side',
      width: 80,
      render: (side: string) => (
        <Tag color={side === 'long' ? 'green' : 'red'}>
          {side === 'long' ? '\u591a\u5934' : '\u7a7a\u5934'}
        </Tag>
      ),
    },
    {
      title: '\u6570\u91cf',
      dataIndex: 'quantity',
      key: 'quantity',
      width: 100,
      align: 'right' as const,
      render: (qty: number) => qty.toLocaleString(),
    },
    {
      title: '\u6210\u672c\u4ef7',
      dataIndex: 'avgEntryPrice',
      key: 'avgEntryPrice',
      width: 100,
      align: 'right' as const,
      render: (price: number) => `$${price.toFixed(2)}`,
    },
    {
      title: '\u73b0\u4ef7',
      dataIndex: 'currentPrice',
      key: 'currentPrice',
      width: 100,
      align: 'right' as const,
      render: (price: number, record: BrokerPosition) => {
        const isUp = price >= record.avgEntryPrice
        return (
          <span style={{ color: isUp ? '#52c41a' : '#ff4d4f' }}>
            ${price.toFixed(2)}
          </span>
        )
      },
    },
    {
      title: '\u5e02\u503c',
      dataIndex: 'marketValue',
      key: 'marketValue',
      width: 120,
      align: 'right' as const,
      render: (value: number) => `$${value.toLocaleString(undefined, { minimumFractionDigits: 2 })}`,
    },
    {
      title: '\u672a\u5b9e\u73b0\u76c8\u4e8f',
      key: 'unrealizedPnl',
      width: 150,
      align: 'right' as const,
      render: (_: unknown, record: BrokerPosition) => {
        const isProfit = record.unrealizedPnl >= 0
        return (
          <Space>
            <span style={{ color: isProfit ? '#52c41a' : '#ff4d4f' }}>
              {isProfit ? '+' : ''}{record.unrealizedPnl.toFixed(2)}
            </span>
            <Tag color={isProfit ? 'green' : 'red'}>
              {isProfit ? '+' : ''}{record.unrealizedPnlPercent.toFixed(2)}%
            </Tag>
          </Space>
        )
      },
    },
    {
      title: '\u5360\u6bd4',
      key: 'weight',
      width: 120,
      render: (_: unknown, record: BrokerPosition) => {
        const weight = totalValue > 0 ? (record.marketValue / totalValue) * 100 : 0
        return (
          <Tooltip title={`${weight.toFixed(2)}%`}>
            <Progress
              percent={weight}
              showInfo={false}
              strokeColor="#1890ff"
              trailColor="#f0f0f0"
              size="small"
            />
          </Tooltip>
        )
      },
    },
  ]

  if (!loading && positions.length === 0) {
    return (
      <Card
        title={
          <Space>
            <StockOutlined />
            {'\u5f53\u524d\u6301\u4ed3'}
          </Space>
        }
      >
        <Empty description={'\u6682\u65e0\u6301\u4ed3'} />
      </Card>
    )
  }

  return (
    <div className="space-y-4">
      {/* \u6301\u4ed3\u6982\u89c8 */}
      <Row gutter={16}>
        <Col span={6}>
          <Card>
            <Statistic
              title={'\u6301\u4ed3\u6570\u91cf'}
              value={positions.length}
              suffix={'\u53ea'}
              prefix={<StockOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title={'\u6301\u4ed3\u5e02\u503c'}
              value={totalValue}
              precision={2}
              prefix={<DollarOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title={'\u672a\u5b9e\u73b0\u76c8\u4e8f'}
              value={totalPnl}
              precision={2}
              prefix={totalPnl >= 0 ? <RiseOutlined /> : <FallOutlined />}
              valueStyle={{ color: totalPnl >= 0 ? '#52c41a' : '#ff4d4f' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title={'\u6536\u76ca\u7387'}
              value={totalValue > 0 ? (totalPnl / (totalValue - totalPnl)) * 100 : 0}
              precision={2}
              suffix="%"
              valueStyle={{ color: totalPnl >= 0 ? '#52c41a' : '#ff4d4f' }}
            />
          </Card>
        </Col>
      </Row>

      {/* \u6301\u4ed3\u8868\u683c */}
      <Card
        title={
          <Space>
            <StockOutlined />
            {'\u6301\u4ed3\u660e\u7ec6'}
          </Space>
        }
      >
        <Table
          dataSource={positions}
          columns={columns}
          rowKey="symbol"
          loading={loading}
          pagination={false}
          size="small"
        />
      </Card>
    </div>
  )
}
