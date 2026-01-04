/**
 * Step 6: 执行层配置组件
 * 交易执行方式配置
 */
import { Form, Select, InputNumber, Switch, Row, Col, Alert, Radio } from 'antd'
import { InfoCircleOutlined, ExperimentOutlined, ThunderboltOutlined } from '@ant-design/icons'
import { Card } from '@/components/ui'
import {
  ExecutionConfig, SlippageModel, ExecutionAlgorithm,
  DEFAULT_EXECUTION_CONFIG
} from '@/types/strategy'

const { Option } = Select

interface StepExecutionProps {
  value: ExecutionConfig
  onChange: (config: ExecutionConfig) => void
}

const SLIPPAGE_MODELS: { value: SlippageModel; label: string; description: string }[] = [
  { value: 'fixed', label: '固定滑点', description: '每笔交易固定百分比滑点' },
  { value: 'volume_based', label: '成交量模型', description: '滑点与订单占成交量比例相关' },
  { value: 'sqrt', label: '平方根模型', description: '专业级模型，滑点与订单规模平方根成正比' },
]

const EXECUTION_ALGORITHMS: { value: ExecutionAlgorithm; label: string; description: string; icon: React.ReactNode }[] = [
  { value: 'market', label: '市价单', description: '立即成交，可能有较大滑点', icon: <ThunderboltOutlined /> },
  { value: 'twap', label: 'TWAP', description: '时间加权，分批执行降低冲击', icon: null },
  { value: 'vwap', label: 'VWAP', description: '成交量加权，跟随市场节奏', icon: null },
  { value: 'pov', label: 'POV', description: '参与率模式，控制市场占比', icon: null },
]

export default function StepExecution({ value = DEFAULT_EXECUTION_CONFIG, onChange }: StepExecutionProps) {
  const updateField = <K extends keyof ExecutionConfig>(field: K, fieldValue: ExecutionConfig[K]) => {
    onChange({ ...value, [field]: fieldValue })
  }

  return (
    <div className="space-y-6">
      {/* 教育提示 */}
      <Alert
        type="info"
        showIcon
        icon={<InfoCircleOutlined />}
        message="交易成本决定成败"
        description="许多看起来很好的策略，在考虑交易成本后就不赚钱了。专业机构花费大量精力优化执行，使用TWAP、VWAP等算法来降低市场冲击。"
      />

      <Row gutter={24}>
        <Col span={14}>
          {/* 成本配置 */}
          <Card title="交易成本配置">
            <Form layout="vertical">
              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item
                    label="手续费率 (%)"
                    tooltip="包括佣金、印花税等"
                  >
                    <InputNumber
                      value={value.commissionRate}
                      onChange={(v) => updateField('commissionRate', v || 0.1)}
                      min={0}
                      max={1}
                      step={0.01}
                      style={{ width: '100%' }}
                      addonAfter="%"
                    />
                    <div className="text-xs text-gray-500 mt-1">
                      美股一般 0.01-0.1%，A股约 0.1%
                    </div>
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    label="滑点估计 (%)"
                    tooltip="预期与目标价格的偏差"
                  >
                    <InputNumber
                      value={value.slippageRate}
                      onChange={(v) => updateField('slippageRate', v || 0.1)}
                      min={0}
                      max={2}
                      step={0.05}
                      style={{ width: '100%' }}
                      addonAfter="%"
                    />
                    <div className="text-xs text-gray-500 mt-1">
                      流动性好的股票约 0.05-0.1%
                    </div>
                  </Form.Item>
                </Col>
              </Row>

              <Form.Item label="滑点模型">
                <Select
                  value={value.slippageModel}
                  onChange={(v) => updateField('slippageModel', v)}
                >
                  {SLIPPAGE_MODELS.map(model => (
                    <Option key={model.value} value={model.value}>
                      <div>
                        <span className="font-medium">{model.label}</span>
                        <span className="text-gray-500 text-xs ml-2">{model.description}</span>
                      </div>
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Form>
          </Card>

          {/* 执行算法 */}
          <Card title="执行算法" className="mt-4">
            <Form layout="vertical">
              <Form.Item label="选择执行算法">
                <Radio.Group
                  value={value.algorithm}
                  onChange={(e) => updateField('algorithm', e.target.value)}
                  className="w-full"
                >
                  <div className="grid grid-cols-2 gap-3">
                    {EXECUTION_ALGORITHMS.map(algo => (
                      <Radio.Button
                        key={algo.value}
                        value={algo.value}
                        className="h-auto p-3 flex flex-col items-start"
                        style={{ height: 'auto' }}
                      >
                        <div className="font-medium">{algo.label}</div>
                        <div className="text-xs text-gray-500 mt-1">{algo.description}</div>
                      </Radio.Button>
                    ))}
                  </div>
                </Radio.Group>
              </Form.Item>
            </Form>
          </Card>

          {/* 交易模式 */}
          <Card title="交易模式" className="mt-4">
            <div className="flex items-center justify-between p-4 bg-dark-hover rounded-lg">
              <div>
                <div className="font-medium flex items-center gap-2">
                  <ExperimentOutlined className="text-yellow-400" />
                  模拟交易 (Paper Trading)
                </div>
                <div className="text-sm text-gray-500 mt-1">
                  使用虚拟资金测试策略，不产生真实交易
                </div>
              </div>
              <Switch
                checked={value.paperTrade}
                onChange={(v) => updateField('paperTrade', v)}
              />
            </div>

            {!value.paperTrade && (
              <Alert
                type="warning"
                message="实盘交易风险提示"
                description="您已关闭模拟交易。实盘交易将使用真实资金，请确保您了解相关风险。"
                className="mt-4"
                showIcon
              />
            )}
          </Card>
        </Col>

        <Col span={10}>
          {/* 执行算法详解 */}
          <Card title="执行算法详解">
            <div className="space-y-4 text-sm">
              <div className="p-3 bg-dark-hover rounded">
                <div className="font-medium text-blue-400 mb-1">市价单</div>
                <p className="text-gray-500">
                  最简单的执行方式，立即按当前市价成交。
                  适合小订单和流动性好的股票。
                </p>
                <div className="text-xs text-yellow-400 mt-2">
                  风险：大单可能导致较大滑点
                </div>
              </div>

              <div className="p-3 bg-dark-hover rounded">
                <div className="font-medium text-green-400 mb-1">TWAP (时间加权)</div>
                <p className="text-gray-500">
                  将大订单拆分成小单，在指定时间内均匀执行。
                  可以降低市场冲击。
                </p>
                <div className="text-xs text-green-400 mt-2">
                  适合：固定时间内完成交易
                </div>
              </div>

              <div className="p-3 bg-dark-hover rounded">
                <div className="font-medium text-purple-400 mb-1">VWAP (成交量加权)</div>
                <p className="text-gray-500">
                  跟随市场成交量节奏执行，在成交活跃时段执行更多。
                  目标是接近当天的成交量加权平均价。
                </p>
                <div className="text-xs text-purple-400 mt-2">
                  适合：追踪基准价格
                </div>
              </div>

              <div className="p-3 bg-dark-hover rounded">
                <div className="font-medium text-orange-400 mb-1">POV (成交量占比)</div>
                <p className="text-gray-500">
                  控制订单占市场总成交量的比例。
                  比如设置10%，意味着每100股成交中，我们贡献10股。
                </p>
                <div className="text-xs text-orange-400 mt-2">
                  适合：大订单隐藏意图
                </div>
              </div>
            </div>
          </Card>

          {/* 成本估算 */}
          <Card title="成本估算" className="mt-4">
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-500">单边总成本</span>
                <span>
                  {(value.commissionRate + value.slippageRate).toFixed(2)}%
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">双边总成本</span>
                <span>
                  {((value.commissionRate + value.slippageRate) * 2).toFixed(2)}%
                </span>
              </div>
              <div className="flex justify-between border-t border-dark-border pt-2 mt-2">
                <span className="text-gray-500">100%换手年成本</span>
                <span className="text-yellow-400">
                  {((value.commissionRate + value.slippageRate) * 2).toFixed(2)}%
                </span>
              </div>
            </div>
          </Card>
        </Col>
      </Row>
    </div>
  )
}
