/**
 * Step 3: 信号层配置组件 (新增)
 * 定义入场和出场的具体规则
 */
import { Form, Select, InputNumber, Switch, Row, Col, Alert, Button, Table, Tag, Space } from 'antd'
import { PlusOutlined, DeleteOutlined, InfoCircleOutlined, WarningOutlined } from '@ant-design/icons'
import { Card } from '@/components/ui'
import {
  SignalConfig, SignalRule, RuleField, RuleOperator,
  DEFAULT_SIGNAL_CONFIG
} from '@/types/strategy'

const { Option } = Select

interface StepSignalProps {
  value: SignalConfig
  onChange: (config: SignalConfig) => void
}

const RULE_FIELDS: { value: RuleField; label: string; description: string }[] = [
  { value: 'factor_rank', label: '因子排名', description: '股票在因子中的排名位置' },
  { value: 'factor_score', label: '因子得分', description: '标准化后的因子得分' },
  { value: 'holding_pnl', label: '持仓盈亏', description: '当前持仓的盈亏百分比' },
  { value: 'holding_days', label: '持仓天数', description: '当前持仓的持有天数' },
  { value: 'price_change', label: '价格变化', description: '股票价格的变化百分比' },
  { value: 'volume_change', label: '成交量变化', description: '成交量的变化百分比' },
]

const OPERATORS: { value: RuleOperator; label: string; symbol: string }[] = [
  { value: 'gt', label: '大于', symbol: '>' },
  { value: 'gte', label: '大于等于', symbol: '>=' },
  { value: 'lt', label: '小于', symbol: '<' },
  { value: 'lte', label: '小于等于', symbol: '<=' },
  { value: 'eq', label: '等于', symbol: '=' },
]

export default function StepSignal({ value = DEFAULT_SIGNAL_CONFIG, onChange }: StepSignalProps) {
  const updateField = <K extends keyof SignalConfig>(field: K, fieldValue: SignalConfig[K]) => {
    onChange({ ...value, [field]: fieldValue })
  }

  const addRule = (type: 'entry' | 'exit') => {
    const newRule: SignalRule = {
      id: `${type}_${Date.now()}`,
      name: type === 'entry' ? '新入场规则' : '新出场规则',
      field: type === 'entry' ? 'factor_rank' : 'holding_pnl',
      operator: type === 'entry' ? 'lte' : 'gt',
      threshold: type === 'entry' ? 20 : 50,
      enabled: true,
    }

    if (type === 'entry') {
      updateField('entryRules', [...value.entryRules, newRule])
    } else {
      updateField('exitRules', [...value.exitRules, newRule])
    }
  }

  const removeRule = (type: 'entry' | 'exit', ruleId: string) => {
    if (type === 'entry') {
      updateField('entryRules', value.entryRules.filter(r => r.id !== ruleId))
    } else {
      updateField('exitRules', value.exitRules.filter(r => r.id !== ruleId))
    }
  }

  const updateRule = (type: 'entry' | 'exit', ruleId: string, updates: Partial<SignalRule>) => {
    const rules = type === 'entry' ? value.entryRules : value.exitRules
    const updatedRules = rules.map(r => r.id === ruleId ? { ...r, ...updates } : r)

    if (type === 'entry') {
      updateField('entryRules', updatedRules)
    } else {
      updateField('exitRules', updatedRules)
    }
  }

  const ruleColumns = (type: 'entry' | 'exit') => [
    {
      title: '条件',
      key: 'condition',
      render: (_: unknown, record: SignalRule) => (
        <Space>
          <Select
            value={record.field}
            onChange={(v) => updateRule(type, record.id, { field: v })}
            style={{ width: 120 }}
            size="small"
          >
            {RULE_FIELDS.map(f => (
              <Option key={f.value} value={f.value}>{f.label}</Option>
            ))}
          </Select>
          <Select
            value={record.operator}
            onChange={(v) => updateRule(type, record.id, { operator: v })}
            style={{ width: 90 }}
            size="small"
          >
            {OPERATORS.map(op => (
              <Option key={op.value} value={op.value}>{op.symbol} {op.label}</Option>
            ))}
          </Select>
          <InputNumber
            value={record.threshold}
            onChange={(v) => updateRule(type, record.id, { threshold: v || 0 })}
            style={{ width: 80 }}
            size="small"
          />
        </Space>
      ),
    },
    {
      title: '启用',
      dataIndex: 'enabled',
      width: 80,
      render: (enabled: boolean, record: SignalRule) => (
        <Switch
          checked={enabled}
          onChange={(v) => updateRule(type, record.id, { enabled: v })}
          size="small"
        />
      ),
    },
    {
      title: '操作',
      width: 60,
      render: (_: unknown, record: SignalRule) => (
        <Button
          type="text"
          danger
          size="small"
          icon={<DeleteOutlined />}
          onClick={() => removeRule(type, record.id)}
        />
      ),
    },
  ]

  return (
    <div className="space-y-6">
      {/* 教育提示 */}
      <Alert
        type="info"
        showIcon
        icon={<InfoCircleOutlined />}
        message="为什么需要信号层？"
        description="有了选股逻辑（因子），还需要明确买卖规则。因子得分只是一个数字，你需要定义：得分多高才买入？什么情况下卖出？止损怎么设？这些规则会直接影响策略的收益和风险。"
      />

      <Row gutter={24}>
        <Col span={12}>
          {/* 基础配置 */}
          <Card title="基础配置">
            <Form layout="vertical">
              <Form.Item label="信号类型">
                <Select
                  value={value.signalType}
                  onChange={(v) => updateField('signalType', v)}
                >
                  <Option value="long_only">仅做多 (Long Only)</Option>
                  <Option value="long_short">多空对冲 (Long-Short)</Option>
                </Select>
                <div className="text-xs text-gray-500 mt-1">
                  {value.signalType === 'long_only'
                    ? '只买入看好的股票，适合普通投资者'
                    : '买入看好的，做空看空的，适合专业投资者'
                  }
                </div>
              </Form.Item>

              <Form.Item label="目标持仓数">
                <InputNumber
                  value={value.targetPositions}
                  onChange={(v) => updateField('targetPositions', v || 20)}
                  min={5}
                  max={100}
                  style={{ width: '100%' }}
                  addonAfter="只"
                />
                <div className="text-xs text-gray-500 mt-1">
                  持仓越分散风险越低，但管理难度增加
                </div>
              </Form.Item>
            </Form>
          </Card>

          {/* 止损止盈 - 突出显示 */}
          <Card
            title={
              <span className="text-red-400">
                <WarningOutlined className="mr-2" />
                止损止盈（重要）
              </span>
            }
            className="mt-4 border-red-500/30"
          >
            <Form layout="vertical">
              <Form.Item
                label="止损阈值 (%)"
                required
                tooltip="当持仓亏损超过此值时强制卖出"
              >
                <InputNumber
                  value={value.stopLoss}
                  onChange={(v) => updateField('stopLoss', v || 15)}
                  min={5}
                  max={50}
                  style={{ width: '100%' }}
                  addonAfter="%"
                />
                <div className="text-xs text-red-400 mt-1">
                  这是必填项！没有止损的策略是危险的
                </div>
              </Form.Item>

              <Form.Item label="止盈阈值 (%)">
                <InputNumber
                  value={value.takeProfit}
                  onChange={(v) => updateField('takeProfit', v || undefined)}
                  min={10}
                  max={200}
                  style={{ width: '100%' }}
                  placeholder="可选"
                  addonAfter="%"
                />
                <div className="text-xs text-gray-500 mt-1">
                  达到目标收益时可以选择锁定利润
                </div>
              </Form.Item>
            </Form>
          </Card>
        </Col>

        <Col span={12}>
          {/* 入场规则 */}
          <Card
            title={
              <span>
                入场规则
                <Tag color="green" className="ml-2">AND逻辑</Tag>
              </span>
            }
            extra={
              <Button
                type="link"
                size="small"
                icon={<PlusOutlined />}
                onClick={() => addRule('entry')}
              >
                添加规则
              </Button>
            }
          >
            <div className="text-xs text-gray-500 mb-3">
              满足所有入场规则时买入
            </div>
            <Table
              dataSource={value.entryRules}
              columns={ruleColumns('entry')}
              rowKey="id"
              size="small"
              pagination={false}
            />
          </Card>

          {/* 出场规则 */}
          <Card
            title={
              <span>
                出场规则
                <Tag color="orange" className="ml-2">OR逻辑</Tag>
              </span>
            }
            extra={
              <Button
                type="link"
                size="small"
                icon={<PlusOutlined />}
                onClick={() => addRule('exit')}
              >
                添加规则
              </Button>
            }
            className="mt-4"
          >
            <div className="text-xs text-gray-500 mb-3">
              满足任一出场规则时卖出
            </div>
            <Table
              dataSource={value.exitRules}
              columns={ruleColumns('exit')}
              rowKey="id"
              size="small"
              pagination={false}
            />
          </Card>
        </Col>
      </Row>
    </div>
  )
}
