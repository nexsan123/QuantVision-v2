import { useState } from 'react'
import { Row, Col, Input, Select, InputNumber, Button, Table, Tag, Modal, Form } from 'antd'
import { PlusOutlined, SyncOutlined, CloseOutlined } from '@ant-design/icons'
import { Card, NumberDisplay } from '@/components/ui'

// 模拟持仓数据
const mockPositions = [
  { symbol: 'AAPL', qty: 100, avgPrice: 175.50, currentPrice: 178.52, pnl: 302, pnlPct: 0.0172, weight: 0.15 },
  { symbol: 'MSFT', qty: 50, avgPrice: 365.00, currentPrice: 372.15, pnl: 357.5, pnlPct: 0.0196, weight: 0.12 },
  { symbol: 'GOOGL', qty: 80, avgPrice: 140.00, currentPrice: 141.23, pnl: 98.4, pnlPct: 0.0088, weight: 0.10 },
  { symbol: 'NVDA', qty: 30, avgPrice: 480.00, currentPrice: 475.50, pnl: -135, pnlPct: -0.0094, weight: 0.08 },
]

const mockOrders = [
  { id: 'ORD001', symbol: 'AAPL', side: 'BUY', qty: 50, price: 178.00, status: 'pending', time: '15:28:32' },
  { id: 'ORD002', symbol: 'TSLA', side: 'SELL', qty: 20, price: 245.00, status: 'filled', time: '14:15:08' },
  { id: 'ORD003', symbol: 'AMZN', side: 'BUY', qty: 25, price: 185.50, status: 'cancelled', time: '11:42:55' },
]

const positionColumns = [
  { title: '股票', dataIndex: 'symbol', key: 'symbol', render: (s: string) => <span className="font-medium">{s}</span> },
  { title: '持仓', dataIndex: 'qty', key: 'qty', className: 'text-right font-mono' },
  { title: '成本', dataIndex: 'avgPrice', key: 'avgPrice', className: 'text-right font-mono', render: (p: number) => `$${p.toFixed(2)}` },
  { title: '现价', dataIndex: 'currentPrice', key: 'currentPrice', className: 'text-right font-mono', render: (p: number) => `$${p.toFixed(2)}` },
  { title: '盈亏', dataIndex: 'pnl', key: 'pnl', className: 'text-right', render: (v: number) => (
    <NumberDisplay value={v} type="currency" colorize showSign />
  )},
  { title: '盈亏%', dataIndex: 'pnlPct', key: 'pnlPct', className: 'text-right', render: (v: number) => (
    <NumberDisplay value={v} type="percent" colorize showSign />
  )},
  { title: '权重', dataIndex: 'weight', key: 'weight', className: 'text-right', render: (v: number) => (
    <span className="font-mono">{(v * 100).toFixed(1)}%</span>
  )},
  {
    title: '操作',
    key: 'action',
    render: () => (
      <Button size="small" danger>平仓</Button>
    ),
  },
]

const orderColumns = [
  { title: '订单号', dataIndex: 'id', key: 'id', className: 'font-mono text-gray-400' },
  { title: '股票', dataIndex: 'symbol', key: 'symbol' },
  { title: '方向', dataIndex: 'side', key: 'side', render: (s: string) => (
    <span className={s === 'BUY' ? 'text-profit' : 'text-loss'}>{s}</span>
  )},
  { title: '数量', dataIndex: 'qty', key: 'qty', className: 'text-right font-mono' },
  { title: '价格', dataIndex: 'price', key: 'price', className: 'text-right font-mono', render: (p: number) => `$${p.toFixed(2)}` },
  { title: '状态', dataIndex: 'status', key: 'status', render: (s: string) => {
    const colors: Record<string, string> = { pending: 'orange', filled: 'green', cancelled: 'gray' }
    const labels: Record<string, string> = { pending: '待成交', filled: '已成交', cancelled: '已取消' }
    return <Tag color={colors[s]}>{labels[s]}</Tag>
  }},
  { title: '时间', dataIndex: 'time', key: 'time', className: 'font-mono text-gray-400' },
  {
    title: '操作',
    key: 'action',
    render: (_: unknown, record: { status: string }) => (
      record.status === 'pending' ? (
        <Button size="small" icon={<CloseOutlined />} danger>取消</Button>
      ) : null
    ),
  },
]

/**
 * 交易执行页面
 *
 * 功能:
 * - 持仓管理
 * - 下单
 * - 订单管理
 */
export default function Trading() {
  const [orderModalOpen, setOrderModalOpen] = useState(false)
  const [form] = Form.useForm()

  const handleSubmitOrder = () => {
    form.validateFields().then(() => {
      setOrderModalOpen(false)
      form.resetFields()
    })
  }

  return (
    <div className="space-y-6 animate-in">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">交易执行</h1>
        <div className="flex gap-2">
          <Button icon={<SyncOutlined />}>同步持仓</Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setOrderModalOpen(true)}>
            新建订单
          </Button>
        </div>
      </div>

      {/* 账户概览 */}
      <Row gutter={[16, 16]}>
        <Col xs={12} md={6}>
          <Card padding="md">
            <div className="text-sm text-gray-500">账户净值</div>
            <div className="text-2xl font-bold font-mono mt-1">$1,523,456.78</div>
          </Card>
        </Col>
        <Col xs={12} md={6}>
          <Card padding="md">
            <div className="text-sm text-gray-500">今日盈亏</div>
            <NumberDisplay value={12345.67} type="currency" colorize showSign size="xl" className="mt-1" />
          </Card>
        </Col>
        <Col xs={12} md={6}>
          <Card padding="md">
            <div className="text-sm text-gray-500">可用资金</div>
            <div className="text-2xl font-bold font-mono mt-1">$325,432.10</div>
          </Card>
        </Col>
        <Col xs={12} md={6}>
          <Card padding="md">
            <div className="text-sm text-gray-500">持仓市值</div>
            <div className="text-2xl font-bold font-mono mt-1">$1,198,024.68</div>
          </Card>
        </Col>
      </Row>

      {/* 持仓列表 */}
      <Card title="当前持仓" subtitle="实时持仓明细">
        <Table
          dataSource={mockPositions}
          columns={positionColumns}
          rowKey="symbol"
          pagination={false}
        />
      </Card>

      {/* 订单管理 */}
      <Card title="订单管理" subtitle="今日订单">
        <Table
          dataSource={mockOrders}
          columns={orderColumns}
          rowKey="id"
          pagination={false}
        />
      </Card>

      {/* 下单弹窗 */}
      <Modal
        title="新建订单"
        open={orderModalOpen}
        onOk={handleSubmitOrder}
        onCancel={() => setOrderModalOpen(false)}
        okText="提交订单"
        cancelText="取消"
      >
        <Form form={form} layout="vertical" className="mt-4">
          <Form.Item label="股票代码" name="symbol" rules={[{ required: true }]}>
            <Input placeholder="输入股票代码" />
          </Form.Item>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item label="方向" name="side" initialValue="BUY">
                <Select>
                  <Select.Option value="BUY">买入</Select.Option>
                  <Select.Option value="SELL">卖出</Select.Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="订单类型" name="type" initialValue="limit">
                <Select>
                  <Select.Option value="market">市价单</Select.Option>
                  <Select.Option value="limit">限价单</Select.Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item label="数量" name="qty" rules={[{ required: true }]}>
                <InputNumber min={1} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="价格" name="price">
                <InputNumber min={0} step={0.01} style={{ width: '100%' }} prefix="$" />
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </Modal>
    </div>
  )
}
