/**
 * Step 4: 风险层配置组件 (新增)
 * 设置风险约束和暴露限制
 */
import { Form, InputNumber, Switch, Row, Col, Alert, Table, Tag, Tooltip } from 'antd'
import { InfoCircleOutlined, LockOutlined, WarningOutlined } from '@ant-design/icons'
import { Card } from '@/components/ui'
import {
  RiskConfig, CircuitBreakerLevel, DEFAULT_RISK_CONFIG, DEFAULT_CIRCUIT_BREAKERS
} from '@/types/strategy'

interface StepRiskProps {
  value: RiskConfig
  onChange: (config: RiskConfig) => void
}

const ACTION_LABELS: Record<CircuitBreakerLevel['action'], { label: string; color: string }> = {
  notify: { label: '发送通知', color: 'blue' },
  pause_new: { label: '暂停开新仓', color: 'orange' },
  full_stop: { label: '策略暂停', color: 'red' },
}

export default function StepRisk({ value = DEFAULT_RISK_CONFIG, onChange }: StepRiskProps) {
  const updateField = <K extends keyof RiskConfig>(field: K, fieldValue: RiskConfig[K]) => {
    onChange({ ...value, [field]: fieldValue })
  }

  const circuitBreakerColumns = [
    {
      title: '级别',
      dataIndex: 'level',
      width: 80,
      render: (level: number) => (
        <Tag color={level === 1 ? 'green' : level === 2 ? 'orange' : 'red'}>
          Level {level}
        </Tag>
      ),
    },
    {
      title: '触发条件',
      key: 'trigger',
      render: (_: unknown, record: CircuitBreakerLevel) => (
        <span>
          {record.triggerType === 'daily_loss' ? '日亏损' : '回撤'} &gt; {record.threshold}%
        </span>
      ),
    },
    {
      title: '动作',
      dataIndex: 'action',
      render: (action: CircuitBreakerLevel['action']) => (
        <Tag color={ACTION_LABELS[action].color}>
          {ACTION_LABELS[action].label}
        </Tag>
      ),
    },
    {
      title: '',
      width: 50,
      render: () => (
        <Tooltip title="熔断规则不可修改">
          <LockOutlined className="text-gray-500" />
        </Tooltip>
      ),
    },
  ]

  return (
    <div className="space-y-6">
      {/* 核心提示 */}
      <Alert
        type="warning"
        showIcon
        icon={<WarningOutlined />}
        message="风险控制是长期盈利的前提"
        description={
          <div>
            <p>机构投资者的核心理念：<strong>先学会不亏钱</strong></p>
            <ul className="mt-2 space-y-1 text-sm">
              <li>机构：单股最大 2-5%，行业暴露严格限制</li>
              <li>散户：单股常常 10-20%，这是非常危险的</li>
            </ul>
          </div>
        }
      />

      <Row gutter={24}>
        <Col span={14}>
          {/* 仓位约束 */}
          <Card title="仓位约束">
            <Form layout="vertical">
              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item
                    label="最大单股仓位 (%)"
                    required
                    tooltip="单只股票的最大持仓占比"
                  >
                    <InputNumber
                      value={value.maxSinglePosition}
                      onChange={(v) => updateField('maxSinglePosition', v || 5)}
                      min={1}
                      max={50}
                      style={{ width: '100%' }}
                      addonAfter="%"
                    />
                    <div className="text-xs mt-1">
                      <span className="text-green-400">建议: </span>
                      <span className="text-gray-500">机构级 2-5%</span>
                    </div>
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    label="最大行业仓位 (%)"
                    required
                    tooltip="单个行业的最大持仓占比"
                  >
                    <InputNumber
                      value={value.maxIndustryPosition}
                      onChange={(v) => updateField('maxIndustryPosition', v || 20)}
                      min={5}
                      max={100}
                      style={{ width: '100%' }}
                      addonAfter="%"
                    />
                    <div className="text-xs mt-1">
                      <span className="text-green-400">建议: </span>
                      <span className="text-gray-500">15-25%</span>
                    </div>
                  </Form.Item>
                </Col>
              </Row>

              <Form.Item
                label="最大回撤 (%)"
                required
                tooltip="组合从最高点的最大跌幅"
              >
                <InputNumber
                  value={value.maxDrawdown}
                  onChange={(v) => updateField('maxDrawdown', v || 15)}
                  min={5}
                  max={50}
                  style={{ width: '100%' }}
                  addonAfter="%"
                />
                <div className="text-xs mt-1">
                  <span className="text-yellow-400">警告: </span>
                  <span className="text-gray-500">超过15%触发Level 3熔断</span>
                </div>
              </Form.Item>
            </Form>
          </Card>

          {/* 高级风险指标 */}
          <Card title="高级风险指标 (可选)" className="mt-4">
            <Form layout="vertical">
              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item
                    label="最大波动率 (%)"
                    tooltip="组合的年化波动率上限"
                  >
                    <InputNumber
                      value={value.maxVolatility}
                      onChange={(v) => updateField('maxVolatility', v || undefined)}
                      min={5}
                      max={100}
                      style={{ width: '100%' }}
                      placeholder="不限制"
                      addonAfter="%"
                    />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    label="最大VaR (%)"
                    tooltip="每日最大风险价值 (95%置信度)"
                  >
                    <InputNumber
                      value={value.maxVaR}
                      onChange={(v) => updateField('maxVaR', v || undefined)}
                      min={1}
                      max={20}
                      style={{ width: '100%' }}
                      placeholder="不限制"
                      addonAfter="%"
                    />
                  </Form.Item>
                </Col>
              </Row>

              <Form.Item label="启用实时风险监控">
                <Switch
                  checked={value.enableRiskMonitor}
                  onChange={(v) => updateField('enableRiskMonitor', v)}
                />
                <span className="ml-2 text-gray-500">
                  {value.enableRiskMonitor ? '已启用' : '未启用'}
                </span>
              </Form.Item>
            </Form>
          </Card>
        </Col>

        <Col span={10}>
          {/* 熔断规则 - 不可修改 */}
          <Card
            title={
              <span>
                <LockOutlined className="mr-2" />
                熔断规则（系统强制）
              </span>
            }
          >
            <Alert
              type="info"
              showIcon
              icon={<InfoCircleOutlined />}
              message="熔断规则不可关闭"
              description="这是保护您资金安全的最后一道防线"
              className="mb-4"
            />

            <Table
              dataSource={DEFAULT_CIRCUIT_BREAKERS}
              columns={circuitBreakerColumns}
              rowKey="level"
              size="small"
              pagination={false}
            />

            <div className="mt-4 p-3 bg-dark-hover rounded text-sm">
              <div className="font-medium mb-2">熔断机制说明</div>
              <ul className="space-y-1 text-gray-400">
                <li><Tag color="green">Level 1</Tag> 日亏损&gt;3% → 发送告警通知</li>
                <li><Tag color="orange">Level 2</Tag> 日亏损&gt;5% → 暂停开新仓</li>
                <li><Tag color="red">Level 3</Tag> 回撤&gt;15% → 策略完全暂停，需人工确认恢复</li>
              </ul>
            </div>
          </Card>

          {/* 风险对比 */}
          <Card title="风险配置对比" className="mt-4">
            <div className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-500">保守型</span>
                <span>单股2%, 行业15%, 回撤10%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">平衡型</span>
                <span>单股5%, 行业20%, 回撤15%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">激进型</span>
                <span>单股10%, 行业30%, 回撤25%</span>
              </div>
              <div className="flex justify-between border-t border-dark-border pt-2">
                <span className="text-primary-500">您的配置</span>
                <span className="text-primary-500">
                  单股{value.maxSinglePosition}%, 行业{value.maxIndustryPosition}%, 回撤{value.maxDrawdown}%
                </span>
              </div>
            </div>
          </Card>
        </Col>
      </Row>
    </div>
  )
}
