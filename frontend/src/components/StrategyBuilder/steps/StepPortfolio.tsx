/**
 * Step 5: 组合层配置组件
 * 仓位分配和权重优化
 */
import { Form, Select, InputNumber, Switch, Row, Col, Alert, Slider } from 'antd'
import { InfoCircleOutlined } from '@ant-design/icons'
import { Card } from '@/components/ui'
import {
  PortfolioConfig, WeightOptimizer, RebalanceFrequency,
  DEFAULT_PORTFOLIO_CONFIG
} from '@/types/strategy'

const { Option } = Select

interface StepPortfolioProps {
  value: PortfolioConfig
  onChange: (config: PortfolioConfig) => void
}

const WEIGHT_OPTIMIZERS: { value: WeightOptimizer; label: string; description: string }[] = [
  { value: 'equal_weight', label: '等权重', description: '每只股票相同权重，简单但有效' },
  { value: 'market_cap', label: '市值加权', description: '按市值分配权重，大盘股权重更高' },
  { value: 'factor_score', label: '因子得分加权', description: '因子得分越高，权重越大' },
  { value: 'min_variance', label: '最小方差', description: '数学优化，追求最低波动' },
  { value: 'max_sharpe', label: '最大夏普', description: '数学优化，追求最高风险调整收益' },
  { value: 'risk_parity', label: '风险平价', description: '每只股票贡献相同风险' },
]

const REBALANCE_FREQUENCIES: { value: RebalanceFrequency; label: string; turnover: string }[] = [
  { value: 'daily', label: '每日调仓', turnover: '极高换手' },
  { value: 'weekly', label: '每周调仓', turnover: '高换手' },
  { value: 'biweekly', label: '双周调仓', turnover: '中高换手' },
  { value: 'monthly', label: '每月调仓', turnover: '中等换手' },
  { value: 'quarterly', label: '每季调仓', turnover: '低换手' },
]

export default function StepPortfolio({ value = DEFAULT_PORTFOLIO_CONFIG, onChange }: StepPortfolioProps) {
  const updateField = <K extends keyof PortfolioConfig>(field: K, fieldValue: PortfolioConfig[K]) => {
    onChange({ ...value, [field]: fieldValue })
  }

  return (
    <div className="space-y-6">
      {/* 教育提示 */}
      <Alert
        type="info"
        showIcon
        icon={<InfoCircleOutlined />}
        message="组合构建的重要性"
        description="选好股票后，每只买多少？这个问题同样重要。研究表明，权重优化可以显著提升策略的风险调整收益。但过度优化也可能导致过拟合。"
      />

      <Row gutter={24}>
        <Col span={14}>
          {/* 权重优化 */}
          <Card title="权重优化方法">
            <Form layout="vertical">
              <Form.Item label="优化方法">
                <Select
                  value={value.optimizer}
                  onChange={(v) => updateField('optimizer', v)}
                  size="large"
                >
                  {WEIGHT_OPTIMIZERS.map(opt => (
                    <Option key={opt.value} value={opt.value}>
                      <div>
                        <span className="font-medium">{opt.label}</span>
                        <span className="text-gray-500 text-xs ml-2">{opt.description}</span>
                      </div>
                    </Option>
                  ))}
                </Select>
              </Form.Item>

              <Form.Item label="调仓频率">
                <Select
                  value={value.rebalanceFrequency}
                  onChange={(v) => updateField('rebalanceFrequency', v)}
                >
                  {REBALANCE_FREQUENCIES.map(freq => (
                    <Option key={freq.value} value={freq.value}>
                      <div className="flex justify-between items-center" style={{ width: 200 }}>
                        <span>{freq.label}</span>
                        <span className="text-gray-500 text-xs">{freq.turnover}</span>
                      </div>
                    </Option>
                  ))}
                </Select>
                <div className="text-xs text-gray-500 mt-1">
                  调仓越频繁，换手率越高，交易成本也越高
                </div>
              </Form.Item>
            </Form>
          </Card>

          {/* 持仓约束 */}
          <Card title="持仓约束" className="mt-4">
            <Form layout="vertical">
              <Form.Item label="持仓数量范围">
                <Row gutter={16}>
                  <Col span={12}>
                    <InputNumber
                      value={value.minHoldings}
                      onChange={(v) => updateField('minHoldings', v || 10)}
                      min={5}
                      max={value.maxHoldings}
                      style={{ width: '100%' }}
                      addonBefore="最少"
                      addonAfter="只"
                    />
                  </Col>
                  <Col span={12}>
                    <InputNumber
                      value={value.maxHoldings}
                      onChange={(v) => updateField('maxHoldings', v || 50)}
                      min={value.minHoldings}
                      max={200}
                      style={{ width: '100%' }}
                      addonBefore="最多"
                      addonAfter="只"
                    />
                  </Col>
                </Row>
              </Form.Item>

              <Form.Item label={`最大换手率: ${value.maxTurnover}%`}>
                <Slider
                  value={value.maxTurnover}
                  onChange={(v) => updateField('maxTurnover', v)}
                  min={0}
                  max={500}
                  marks={{
                    0: '0%',
                    100: '100%',
                    200: '200%',
                    500: '500%'
                  }}
                />
                <div className="text-xs text-gray-500 mt-1">
                  100% 换手率意味着每次调仓全部替换持仓
                </div>
              </Form.Item>

              <Form.Item label={`现金比例: ${value.cashRatio}%`}>
                <Slider
                  value={value.cashRatio}
                  onChange={(v) => updateField('cashRatio', v)}
                  min={0}
                  max={50}
                  marks={{
                    0: '0%',
                    10: '10%',
                    25: '25%',
                    50: '50%'
                  }}
                />
                <div className="text-xs text-gray-500 mt-1">
                  保留一定现金可以降低波动，也便于应对赎回
                </div>
              </Form.Item>

              <Form.Item label="仅做多">
                <Switch
                  checked={value.longOnly}
                  onChange={(v) => updateField('longOnly', v)}
                />
                <span className="ml-2 text-gray-500">
                  {value.longOnly ? '只买入，不做空' : '可以做空'}
                </span>
              </Form.Item>
            </Form>
          </Card>
        </Col>

        <Col span={10}>
          {/* 优化方法说明 */}
          <Card title="优化方法详解">
            <div className="space-y-4 text-sm">
              <div className="p-3 bg-dark-hover rounded">
                <div className="font-medium text-blue-400 mb-1">等权重 (推荐新手)</div>
                <p className="text-gray-500">
                  最简单的方法，每只股票分配相同权重。研究表明，等权重组合往往能跑赢市值加权指数。
                </p>
              </div>

              <div className="p-3 bg-dark-hover rounded">
                <div className="font-medium text-green-400 mb-1">因子得分加权</div>
                <p className="text-gray-500">
                  信号越强的股票权重越大。直觉上合理，但可能放大因子风险。
                </p>
              </div>

              <div className="p-3 bg-dark-hover rounded">
                <div className="font-medium text-purple-400 mb-1">最小方差优化</div>
                <p className="text-gray-500">
                  数学优化找到波动率最低的权重组合。适合风险厌恶型投资者。
                </p>
              </div>

              <div className="p-3 bg-dark-hover rounded">
                <div className="font-medium text-yellow-400 mb-1">风险平价</div>
                <p className="text-gray-500">
                  让每只股票对组合风险的贡献相等。桥水基金全天候策略的核心思想。
                </p>
              </div>
            </div>
          </Card>

          {/* 换手率影响 */}
          <Card title="换手率与成本" className="mt-4">
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-500">预估年换手率</span>
                <span>
                  {value.rebalanceFrequency === 'daily' ? '5000%+' :
                   value.rebalanceFrequency === 'weekly' ? '1000%' :
                   value.rebalanceFrequency === 'monthly' ? '300%' : '100%'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">假设交易成本 0.1%</span>
                <span className="text-yellow-400">
                  年成本约
                  {value.rebalanceFrequency === 'daily' ? '5%+' :
                   value.rebalanceFrequency === 'weekly' ? '1%' :
                   value.rebalanceFrequency === 'monthly' ? '0.3%' : '0.1%'}
                </span>
              </div>
            </div>
          </Card>
        </Col>
      </Row>
    </div>
  )
}
