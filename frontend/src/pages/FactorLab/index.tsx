import { useState } from 'react'
import { Row, Col, Input, Select, Button, Table, Tag } from 'antd'
import { PlayCircleOutlined, PlusOutlined } from '@ant-design/icons'
import { Card, NumberDisplay } from '@/components/ui'
import { FactorICChart, GroupReturnChart } from '@/components/Chart'

const { TextArea } = Input

// 模拟因子数据
const mockFactors = [
  { id: 1, name: 'momentum_20d', category: '动量', ic: 0.045, ir: 0.82, sharpe: 1.23, status: 'active' },
  { id: 2, name: 'value_pb', category: '价值', ic: 0.032, ir: 0.65, sharpe: 0.98, status: 'active' },
  { id: 3, name: 'volatility_60d', category: '风险', ic: -0.028, ir: 0.58, sharpe: 0.76, status: 'testing' },
  { id: 4, name: 'quality_roe', category: '质量', ic: 0.038, ir: 0.71, sharpe: 1.15, status: 'active' },
]

const mockICData = {
  dates: ['2024-01', '2024-02', '2024-03', '2024-04', '2024-05', '2024-06'],
  ic: [0.052, 0.038, 0.041, 0.055, 0.029, 0.048],
  icMean: 0.044,
}

const mockGroupData = {
  groups: ['G1', 'G2', 'G3', 'G4', 'G5', 'G6', 'G7', 'G8', 'G9', 'G10'],
  returns: [-0.08, -0.04, -0.02, 0.01, 0.03, 0.05, 0.07, 0.10, 0.14, 0.22],
}

const columns = [
  { title: '因子名称', dataIndex: 'name', key: 'name' },
  {
    title: '类别',
    dataIndex: 'category',
    key: 'category',
    render: (cat: string) => <Tag color="blue">{cat}</Tag>,
  },
  {
    title: 'IC均值',
    dataIndex: 'ic',
    key: 'ic',
    render: (v: number) => <NumberDisplay value={v} type="ratio" precision={3} colorize />,
  },
  {
    title: 'IR',
    dataIndex: 'ir',
    key: 'ir',
    render: (v: number) => <NumberDisplay value={v} type="ratio" precision={2} />,
  },
  {
    title: '夏普',
    dataIndex: 'sharpe',
    key: 'sharpe',
    render: (v: number) => <NumberDisplay value={v} type="ratio" precision={2} colorize />,
  },
  {
    title: '状态',
    dataIndex: 'status',
    key: 'status',
    render: (s: string) => (
      <Tag color={s === 'active' ? 'green' : 'orange'}>{s === 'active' ? '生效' : '测试'}</Tag>
    ),
  },
]

/**
 * 因子实验室页面
 *
 * 功能:
 * - 因子编辑器
 * - IC 分析
 * - 分组回测
 */
export default function FactorLab() {
  const [expression, setExpression] = useState('ts_rank(close / delay(close, 20) - 1, 60)')
  const [selectedFactor, setSelectedFactor] = useState<number | null>(1)

  return (
    <div className="space-y-6 animate-in">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">因子实验室</h1>
        <Button type="primary" icon={<PlusOutlined />}>
          新建因子
        </Button>
      </div>

      <Row gutter={[16, 16]}>
        {/* 因子编辑器 */}
        <Col xs={24} lg={12}>
          <Card title="因子编辑器" subtitle="使用算子表达式定义因子">
            <div className="space-y-4">
              <div>
                <label className="block text-sm text-gray-400 mb-2">因子名称</label>
                <Input placeholder="输入因子名称" defaultValue="momentum_custom" />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-2">因子表达式</label>
                <TextArea
                  rows={4}
                  value={expression}
                  onChange={(e) => setExpression(e.target.value)}
                  placeholder="输入因子表达式..."
                  className="font-mono"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-2">类别</label>
                <Select
                  defaultValue="momentum"
                  style={{ width: '100%' }}
                  options={[
                    { value: 'momentum', label: '动量' },
                    { value: 'value', label: '价值' },
                    { value: 'quality', label: '质量' },
                    { value: 'volatility', label: '波动' },
                    { value: 'liquidity', label: '流动性' },
                  ]}
                />
              </div>
              <Button type="primary" icon={<PlayCircleOutlined />} block>
                运行 IC 分析
              </Button>
            </div>
          </Card>
        </Col>

        {/* 算子参考 */}
        <Col xs={24} lg={12}>
          <Card title="算子参考" subtitle="可用算子列表">
            <div className="space-y-3 max-h-[350px] overflow-y-auto">
              {[
                { name: 'ts_rank', desc: '时序排名', example: 'ts_rank(x, 20)' },
                { name: 'ts_zscore', desc: '时序标准化', example: 'ts_zscore(x, 60)' },
                { name: 'ts_mean', desc: '移动平均', example: 'ts_mean(x, 20)' },
                { name: 'ts_std', desc: '移动标准差', example: 'ts_std(x, 20)' },
                { name: 'ts_corr', desc: '滚动相关', example: 'ts_corr(x, y, 60)' },
                { name: 'cs_rank', desc: '截面排名', example: 'cs_rank(x)' },
                { name: 'cs_zscore', desc: '截面标准化', example: 'cs_zscore(x)' },
                { name: 'delay', desc: '滞后', example: 'delay(x, 1)' },
                { name: 'delta', desc: '差分', example: 'delta(x, 5)' },
              ].map((op) => (
                <div
                  key={op.name}
                  className="p-3 bg-dark-hover rounded-lg cursor-pointer hover:bg-dark-border transition-colors"
                  onClick={() => setExpression((prev) => prev + ` ${op.name}()`)}
                >
                  <div className="flex justify-between items-center">
                    <span className="font-mono text-primary-400">{op.name}</span>
                    <span className="text-sm text-gray-500">{op.desc}</span>
                  </div>
                  <code className="text-xs text-gray-400 mt-1 block">{op.example}</code>
                </div>
              ))}
            </div>
          </Card>
        </Col>
      </Row>

      {/* 因子列表 */}
      <Card title="因子库" subtitle="已创建的因子">
        <Table
          dataSource={mockFactors}
          columns={columns}
          rowKey="id"
          pagination={false}
          onRow={(record) => ({
            onClick: () => setSelectedFactor(record.id),
            className: selectedFactor === record.id ? 'bg-dark-hover' : '',
          })}
        />
      </Card>

      {/* IC 分析 */}
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={12}>
          <Card title="IC 时序" subtitle="因子预测能力">
            <FactorICChart data={mockICData} />
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="分组回测" subtitle="多空组合收益">
            <GroupReturnChart data={mockGroupData} />
          </Card>
        </Col>
      </Row>
    </div>
  )
}
