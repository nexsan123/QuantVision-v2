import { useState } from 'react'
import { Steps, Button, Form, Input, Select, InputNumber, Switch, Row, Col, Tag } from 'antd'
import { Card } from '@/components/ui'

const { Option } = Select

const steps = [
  { title: '基本信息', description: '策略名称与类型' },
  { title: '因子选择', description: '选择因子组合' },
  { title: '股票池', description: '筛选条件' },
  { title: '约束设置', description: '仓位与风控' },
  { title: '确认', description: '预览与保存' },
]

const availableFactors = [
  { name: 'momentum_20d', category: '动量', ic: 0.045 },
  { name: 'value_pb', category: '价值', ic: 0.032 },
  { name: 'quality_roe', category: '质量', ic: 0.038 },
  { name: 'volatility_60d', category: '风险', ic: -0.028 },
  { name: 'size', category: '规模', ic: 0.025 },
]

/**
 * 策略构建器页面
 *
 * 5步向导流程:
 * 1. 基本信息
 * 2. 因子选择
 * 3. 股票池筛选
 * 4. 约束设置
 * 5. 确认保存
 */
export default function StrategyBuilder() {
  const [current, setCurrent] = useState(0)
  const [form] = Form.useForm()
  const [selectedFactors, setSelectedFactors] = useState<string[]>(['momentum_20d', 'value_pb'])

  const next = () => setCurrent(current + 1)
  const prev = () => setCurrent(current - 1)

  const renderStep = () => {
    switch (current) {
      case 0:
        return (
          <div className="space-y-6">
            <Form.Item label="策略名称" name="name" rules={[{ required: true }]}>
              <Input placeholder="输入策略名称" />
            </Form.Item>
            <Form.Item label="策略类型" name="type" initialValue="factor">
              <Select>
                <Option value="factor">因子策略</Option>
                <Option value="momentum">动量策略</Option>
                <Option value="mean_reversion">均值回归</Option>
              </Select>
            </Form.Item>
            <Form.Item label="调仓频率" name="rebalance" initialValue="monthly">
              <Select>
                <Option value="daily">每日</Option>
                <Option value="weekly">每周</Option>
                <Option value="monthly">每月</Option>
                <Option value="quarterly">每季</Option>
              </Select>
            </Form.Item>
            <Form.Item label="策略描述" name="description">
              <Input.TextArea rows={3} placeholder="描述策略逻辑..." />
            </Form.Item>
          </div>
        )

      case 1:
        return (
          <div className="space-y-4">
            <div className="text-gray-400 mb-4">选择要使用的因子 (可多选)</div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {availableFactors.map((factor) => (
                <div
                  key={factor.name}
                  onClick={() => {
                    if (selectedFactors.includes(factor.name)) {
                      setSelectedFactors(selectedFactors.filter((f) => f !== factor.name))
                    } else {
                      setSelectedFactors([...selectedFactors, factor.name])
                    }
                  }}
                  className={`
                    p-4 rounded-lg border cursor-pointer transition-all
                    ${
                      selectedFactors.includes(factor.name)
                        ? 'border-primary-500 bg-primary-500/10'
                        : 'border-dark-border hover:border-gray-600'
                    }
                  `}
                >
                  <div className="flex justify-between items-start">
                    <div>
                      <span className="font-medium">{factor.name}</span>
                      <Tag color="blue" className="ml-2">
                        {factor.category}
                      </Tag>
                    </div>
                    <span className={factor.ic >= 0 ? 'text-profit' : 'text-loss'}>
                      IC: {factor.ic.toFixed(3)}
                    </span>
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-4 p-4 bg-dark-hover rounded-lg">
              <div className="text-sm text-gray-400">已选择 {selectedFactors.length} 个因子</div>
              <div className="flex gap-2 mt-2">
                {selectedFactors.map((f) => (
                  <Tag key={f} color="blue" closable onClose={() => setSelectedFactors(selectedFactors.filter((x) => x !== f))}>
                    {f}
                  </Tag>
                ))}
              </div>
            </div>
          </div>
        )

      case 2:
        return (
          <div className="space-y-6">
            <Form.Item label="基础股票池" name="universe" initialValue="SP500">
              <Select>
                <Option value="SP500">S&P 500</Option>
                <Option value="NASDAQ100">NASDAQ 100</Option>
                <Option value="DOW30">Dow 30</Option>
                <Option value="RUSSELL2000">Russell 2000</Option>
              </Select>
            </Form.Item>
            <Row gutter={16}>
              <Col span={12}>
                <Form.Item label="最低价格 ($)" name="minPrice">
                  <InputNumber min={0} style={{ width: '100%' }} placeholder="无限制" />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item label="最低市值 (M)" name="minMarketCap">
                  <InputNumber min={0} style={{ width: '100%' }} placeholder="无限制" />
                </Form.Item>
              </Col>
            </Row>
            <Form.Item label="排除行业" name="excludeSectors">
              <Select mode="multiple" placeholder="选择要排除的行业">
                <Option value="financials">金融</Option>
                <Option value="utilities">公用事业</Option>
                <Option value="real_estate">房地产</Option>
              </Select>
            </Form.Item>
          </div>
        )

      case 3:
        return (
          <div className="space-y-6">
            <Row gutter={16}>
              <Col span={12}>
                <Form.Item label="最大单只持仓 (%)" name="maxPosition" initialValue={10}>
                  <InputNumber min={1} max={100} style={{ width: '100%' }} />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item label="最大行业权重 (%)" name="maxSector" initialValue={30}>
                  <InputNumber min={5} max={100} style={{ width: '100%' }} />
                </Form.Item>
              </Col>
            </Row>
            <Row gutter={16}>
              <Col span={12}>
                <Form.Item label="持仓数量范围" name="holdings">
                  <div className="flex gap-2 items-center">
                    <InputNumber min={5} defaultValue={20} style={{ width: '100%' }} />
                    <span className="text-gray-500">-</span>
                    <InputNumber min={10} defaultValue={50} style={{ width: '100%' }} />
                  </div>
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item label="最大换手率 (%)" name="maxTurnover" initialValue={100}>
                  <InputNumber min={0} max={500} style={{ width: '100%' }} />
                </Form.Item>
              </Col>
            </Row>
            <Form.Item label="仅做多" name="longOnly" valuePropName="checked" initialValue={true}>
              <Switch />
            </Form.Item>
          </div>
        )

      case 4:
        return (
          <div className="space-y-6">
            <div className="text-lg font-medium mb-4">策略配置预览</div>
            <div className="grid grid-cols-2 gap-4">
              <div className="p-4 bg-dark-hover rounded-lg">
                <div className="text-gray-400 text-sm">策略名称</div>
                <div className="font-medium mt-1">多因子动量策略</div>
              </div>
              <div className="p-4 bg-dark-hover rounded-lg">
                <div className="text-gray-400 text-sm">策略类型</div>
                <div className="font-medium mt-1">因子策略</div>
              </div>
              <div className="p-4 bg-dark-hover rounded-lg">
                <div className="text-gray-400 text-sm">调仓频率</div>
                <div className="font-medium mt-1">每月</div>
              </div>
              <div className="p-4 bg-dark-hover rounded-lg">
                <div className="text-gray-400 text-sm">股票池</div>
                <div className="font-medium mt-1">S&P 500</div>
              </div>
              <div className="p-4 bg-dark-hover rounded-lg col-span-2">
                <div className="text-gray-400 text-sm">选用因子</div>
                <div className="flex gap-2 mt-2">
                  {selectedFactors.map((f) => (
                    <Tag key={f} color="blue">{f}</Tag>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )

      default:
        return null
    }
  }

  return (
    <div className="space-y-6 animate-in">
      <h1 className="text-2xl font-bold">策略构建器</h1>

      <Card>
        <Steps current={current} items={steps} className="mb-8" />

        <Form form={form} layout="vertical" className="max-w-2xl mx-auto">
          {renderStep()}

          <div className="flex justify-between mt-8 pt-6 border-t border-dark-border">
            {current > 0 && (
              <Button onClick={prev}>
                上一步
              </Button>
            )}
            {current < steps.length - 1 && (
              <Button type="primary" onClick={next} className="ml-auto">
                下一步
              </Button>
            )}
            {current === steps.length - 1 && (
              <Button type="primary" className="ml-auto">
                保存策略
              </Button>
            )}
          </div>
        </Form>
      </Card>
    </div>
  )
}
