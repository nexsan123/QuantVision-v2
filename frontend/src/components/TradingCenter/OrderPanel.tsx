/**
 * Phase 12: \u6267\u884c\u5c42\u5347\u7ea7 - \u8ba2\u5355\u9762\u677f
 *
 * \u529f\u80fd:
 * - \u8ba2\u5355\u63d0\u4ea4
 * - \u6ed1\u70b9\u4f30\u7b97
 * - \u8ba2\u5355\u5217\u8868
 */

import { useState, useEffect, useCallback } from 'react'
import {
  Form, Input, InputNumber, Select, Button, Table, Tag, Space,
  Popconfirm, message, Row, Col, Statistic
} from 'antd'
import {
  ShoppingCartOutlined, SendOutlined,
  InfoCircleOutlined
} from '@ant-design/icons'
import { Card } from '@/components/ui'
import {
  OrderSide, OrderType, OrderStatus, OrderResponse, SlippageResult,
  CreateOrderRequest
} from '@/types/trading'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || ''

interface OrderFormData {
  symbol: string
  side: OrderSide
  quantity: number
  orderType: OrderType
  limitPrice?: number
  stopPrice?: number
}

export default function OrderPanel() {
  const [form] = Form.useForm<OrderFormData>()
  const [orders, setOrders] = useState<OrderResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [slippageEstimate, setSlippageEstimate] = useState<SlippageResult | null>(null)

  const fetchOrders = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/trading/orders?limit=50`)
      if (response.ok) {
        const data = await response.json()
        setOrders(data.orders || [])
      }
    } catch (err) {
      console.error('\u52a0\u8f7d\u8ba2\u5355\u5931\u8d25:', err)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchOrders()
    const interval = setInterval(fetchOrders, 5000)
    return () => clearInterval(interval)
  }, [fetchOrders])

  const estimateSlippage = async (values: OrderFormData) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/trading/slippage/estimate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          symbol: values.symbol,
          side: values.side,
          quantity: values.quantity,
          price: values.limitPrice || 100,
          daily_volume: 1000000,
        }),
      })
      if (response.ok) {
        const data = await response.json()
        setSlippageEstimate(data)
      }
    } catch (err) {
      console.error('\u6ed1\u70b9\u4f30\u7b97\u5931\u8d25:', err)
    }
  }

  const handleSubmit = async (values: OrderFormData) => {
    setSubmitting(true)
    try {
      const request: CreateOrderRequest = {
        symbol: values.symbol.toUpperCase(),
        side: values.side,
        quantity: values.quantity,
        orderType: values.orderType,
        limitPrice: values.limitPrice,
        stopPrice: values.stopPrice,
      }

      const response = await fetch(`${API_BASE_URL}/api/v1/trading/orders`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          symbol: request.symbol,
          side: request.side,
          quantity: request.quantity,
          order_type: request.orderType,
          limit_price: request.limitPrice,
          stop_price: request.stopPrice,
        }),
      })

      const data = await response.json()
      if (data.success) {
        message.success('\u8ba2\u5355\u5df2\u63d0\u4ea4')
        form.resetFields()
        setSlippageEstimate(null)
        fetchOrders()
      } else {
        message.error(data.error || '\u8ba2\u5355\u63d0\u4ea4\u5931\u8d25')
      }
    } catch (err) {
      message.error('\u8ba2\u5355\u63d0\u4ea4\u5931\u8d25')
    } finally {
      setSubmitting(false)
    }
  }

  const handleCancel = async (orderId: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/trading/orders/${orderId}`, {
        method: 'DELETE',
      })
      const data = await response.json()
      if (data.success) {
        message.success('\u8ba2\u5355\u5df2\u53d6\u6d88')
        fetchOrders()
      } else {
        message.error(data.error || '\u53d6\u6d88\u5931\u8d25')
      }
    } catch (err) {
      message.error('\u53d6\u6d88\u5931\u8d25')
    }
  }

  const getStatusTag = (status: OrderStatus) => {
    const config: Record<OrderStatus, { color: string; text: string }> = {
      pending: { color: 'default', text: '\u5f85\u53d1\u9001' },
      submitted: { color: 'blue', text: '\u5df2\u63d0\u4ea4' },
      accepted: { color: 'cyan', text: '\u5df2\u63a5\u53d7' },
      partial_fill: { color: 'orange', text: '\u90e8\u5206\u6210\u4ea4' },
      filled: { color: 'green', text: '\u5df2\u6210\u4ea4' },
      cancelled: { color: 'default', text: '\u5df2\u53d6\u6d88' },
      rejected: { color: 'red', text: '\u5df2\u62d2\u7edd' },
      expired: { color: 'default', text: '\u5df2\u8fc7\u671f' },
    }
    const { color, text } = config[status] || { color: 'default', text: status }
    return <Tag color={color}>{text}</Tag>
  }

  const columns = [
    {
      title: '\u80a1\u7968',
      dataIndex: 'symbol',
      key: 'symbol',
      width: 100,
    },
    {
      title: '\u65b9\u5411',
      dataIndex: 'side',
      key: 'side',
      width: 80,
      render: (side: OrderSide) => (
        <Tag color={side === 'buy' ? 'green' : 'red'}>
          {side === 'buy' ? '\u4e70\u5165' : '\u5356\u51fa'}
        </Tag>
      ),
    },
    {
      title: '\u6570\u91cf',
      dataIndex: 'quantity',
      key: 'quantity',
      width: 100,
      render: (qty: number, record: OrderResponse) => (
        <span>
          {record.filledQuantity}/{qty}
        </span>
      ),
    },
    {
      title: '\u7c7b\u578b',
      dataIndex: 'orderType',
      key: 'orderType',
      width: 80,
      render: (type: OrderType) => {
        const labels: Record<OrderType, string> = {
          market: '\u5e02\u4ef7',
          limit: '\u9650\u4ef7',
          stop: '\u6b62\u635f',
          stop_limit: '\u6b62\u635f\u9650\u4ef7',
        }
        return labels[type] || type
      },
    },
    {
      title: '\u72b6\u6001',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: getStatusTag,
    },
    {
      title: '\u4ef7\u683c',
      key: 'price',
      width: 120,
      render: (_: unknown, record: OrderResponse) => {
        if (record.filledAvgPrice) {
          return `$${record.filledAvgPrice.toFixed(2)}`
        }
        if (record.limitPrice) {
          return `$${record.limitPrice.toFixed(2)} (\u9650)`
        }
        return '\u5e02\u4ef7'
      },
    },
    {
      title: '\u65f6\u95f4',
      dataIndex: 'createdAt',
      key: 'createdAt',
      width: 150,
      render: (time: string) => new Date(time).toLocaleString(),
    },
    {
      title: '\u64cd\u4f5c',
      key: 'action',
      width: 80,
      render: (_: unknown, record: OrderResponse) => {
        const canCancel = ['pending', 'submitted', 'accepted', 'partial_fill'].includes(record.status)
        if (!canCancel) return null
        return (
          <Popconfirm
            title={'\u786e\u5b9a\u53d6\u6d88\u8be5\u8ba2\u5355\uff1f'}
            onConfirm={() => handleCancel(record.id)}
          >
            <Button type="link" danger size="small">
              {'\u53d6\u6d88'}
            </Button>
          </Popconfirm>
        )
      },
    },
  ]

  return (
    <div className="space-y-4">
      {/* \u8ba2\u5355\u8868\u5355 */}
      <Card
        title={
          <Space>
            <ShoppingCartOutlined />
            {'\u63d0\u4ea4\u8ba2\u5355'}
          </Space>
        }
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
          onValuesChange={(_, values) => {
            if (values.symbol && values.quantity && values.side) {
              estimateSlippage(values)
            }
          }}
          initialValues={{
            side: 'buy',
            orderType: 'market',
            quantity: 100,
          }}
        >
          <Row gutter={16}>
            <Col span={6}>
              <Form.Item
                name="symbol"
                label={'\u80a1\u7968\u4ee3\u7801'}
                rules={[{ required: true, message: '\u8bf7\u8f93\u5165\u80a1\u7968\u4ee3\u7801' }]}
              >
                <Input placeholder="AAPL" style={{ textTransform: 'uppercase' }} />
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item
                name="side"
                label={'\u65b9\u5411'}
                rules={[{ required: true }]}
              >
                <Select>
                  <Select.Option value="buy">{'\u4e70\u5165'}</Select.Option>
                  <Select.Option value="sell">{'\u5356\u51fa'}</Select.Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item
                name="quantity"
                label={'\u6570\u91cf'}
                rules={[{ required: true, min: 1, type: 'number' }]}
              >
                <InputNumber min={1} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item
                name="orderType"
                label={'\u8ba2\u5355\u7c7b\u578b'}
                rules={[{ required: true }]}
              >
                <Select>
                  <Select.Option value="market">{'\u5e02\u4ef7\u5355'}</Select.Option>
                  <Select.Option value="limit">{'\u9650\u4ef7\u5355'}</Select.Option>
                  <Select.Option value="stop">{'\u6b62\u635f\u5355'}</Select.Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={6}>
              <Form.Item
                noStyle
                shouldUpdate={(prev, curr) => prev.orderType !== curr.orderType}
              >
                {({ getFieldValue }) =>
                  ['limit', 'stop_limit'].includes(getFieldValue('orderType')) && (
                    <Form.Item
                      name="limitPrice"
                      label={'\u9650\u4ef7'}
                      rules={[{ required: true, type: 'number', min: 0.01 }]}
                    >
                      <InputNumber min={0.01} precision={2} prefix="$" style={{ width: '100%' }} />
                    </Form.Item>
                  )
                }
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item
                noStyle
                shouldUpdate={(prev, curr) => prev.orderType !== curr.orderType}
              >
                {({ getFieldValue }) =>
                  ['stop', 'stop_limit'].includes(getFieldValue('orderType')) && (
                    <Form.Item
                      name="stopPrice"
                      label={'\u6b62\u635f\u4ef7'}
                      rules={[{ required: true, type: 'number', min: 0.01 }]}
                    >
                      <InputNumber min={0.01} precision={2} prefix="$" style={{ width: '100%' }} />
                    </Form.Item>
                  )
                }
              </Form.Item>
            </Col>
          </Row>

          {/* \u6ed1\u70b9\u4f30\u7b97 */}
          {slippageEstimate && (
            <div className="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg mb-4">
              <div className="flex items-center gap-2 mb-2">
                <InfoCircleOutlined />
                <span className="font-medium">{'\u6ed1\u70b9\u4f30\u7b97 (Almgren-Chriss \u6a21\u578b)'}</span>
              </div>
              <Row gutter={16}>
                <Col span={6}>
                  <Statistic
                    title={'\u603b\u6ed1\u70b9'}
                    value={slippageEstimate.slippageBps}
                    precision={2}
                    suffix="bps"
                  />
                </Col>
                <Col span={6}>
                  <Statistic
                    title={'\u56fa\u5b9a\u6210\u672c'}
                    value={slippageEstimate.fixedCost}
                    precision={4}
                    prefix="$"
                  />
                </Col>
                <Col span={6}>
                  <Statistic
                    title={'\u4e34\u65f6\u51b2\u51fb'}
                    value={slippageEstimate.temporaryImpact}
                    precision={4}
                    prefix="$"
                  />
                </Col>
                <Col span={6}>
                  <Statistic
                    title={'\u6c38\u4e45\u51b2\u51fb'}
                    value={slippageEstimate.permanentImpact}
                    precision={4}
                    prefix="$"
                  />
                </Col>
              </Row>
            </div>
          )}

          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              loading={submitting}
              icon={<SendOutlined />}
            >
              {'\u63d0\u4ea4\u8ba2\u5355'}
            </Button>
          </Form.Item>
        </Form>
      </Card>

      {/* \u8ba2\u5355\u5217\u8868 */}
      <Card title={'\u8ba2\u5355\u5217\u8868'}>
        <Table
          dataSource={orders}
          columns={columns}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 10 }}
          size="small"
        />
      </Card>
    </div>
  )
}
