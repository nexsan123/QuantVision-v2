/**
 * Step 2: 因子层配置组件
 * 选择和配置用于生成信号的因子
 */
import { useState } from 'react'
import { Form, Select, Tag, Row, Col, Alert, Button, InputNumber, Empty } from 'antd'
import { DeleteOutlined, InfoCircleOutlined, RobotOutlined } from '@ant-design/icons'
import { Card } from '@/components/ui'
import {
  AlphaConfig, FactorSelection, CombineMethod, NormalizeType, NeutralizeType,
  FactorCategory, DEFAULT_ALPHA_CONFIG
} from '@/types/strategy'

const { Option } = Select

interface StepAlphaProps {
  value: AlphaConfig
  onChange: (config: AlphaConfig) => void
  onAskAI?: (question: string) => void
}

const FACTOR_LIBRARY: {
  id: string
  name: string
  expression: string
  category: FactorCategory
  description: string
  ic: number
  ir: number
}[] = [
  { id: 'momentum_5d', name: '5\u65e5\u52a8\u91cf', expression: 'close / delay(close, 5) - 1', category: 'momentum', description: '\u8fc7\u53bb5\u5929\u7684\u6da8\u8dcc\u5e45', ic: 0.032, ir: 0.65 },
  { id: 'momentum_20d', name: '20\u65e5\u52a8\u91cf', expression: 'close / delay(close, 20) - 1', category: 'momentum', description: '\u8fc7\u53bb20\u5929\u7684\u6da8\u8dcc\u5e45', ic: 0.045, ir: 0.82 },
  { id: 'momentum_60d', name: '60\u65e5\u52a8\u91cf', expression: 'close / delay(close, 60) - 1', category: 'momentum', description: '\u8fc7\u53bb60\u5929\u7684\u6da8\u8dcc\u5e45', ic: 0.038, ir: 0.75 },
  { id: 'value_pb', name: 'PB\u4f30\u503c', expression: '1 / pb_ratio', category: 'value', description: '\u5e02\u51c0\u7387\u5012\u6570\uff0c\u8d8a\u4f4e\u8d8a\u4fbf\u5b9c', ic: 0.032, ir: 0.68 },
  { id: 'value_pe', name: 'PE\u4f30\u503c', expression: '1 / pe_ratio', category: 'value', description: '\u5e02\u76c8\u7387\u5012\u6570\uff0c\u8d8a\u4f4e\u8d8a\u4fbf\u5b9c', ic: 0.028, ir: 0.58 },
  { id: 'value_ev_ebitda', name: 'EV/EBITDA', expression: '1 / ev_ebitda', category: 'value', description: '\u4f01\u4e1a\u4ef7\u503c/EBITDA', ic: 0.035, ir: 0.72 },
  { id: 'quality_roe', name: 'ROE\u8d28\u91cf', expression: 'roe', category: 'quality', description: '\u51c0\u8d44\u4ea7\u6536\u76ca\u7387', ic: 0.038, ir: 0.78 },
  { id: 'quality_roa', name: 'ROA\u8d28\u91cf', expression: 'roa', category: 'quality', description: '\u603b\u8d44\u4ea7\u6536\u76ca\u7387', ic: 0.033, ir: 0.70 },
  { id: 'quality_gpm', name: '\u6bdb\u5229\u7387', expression: 'gross_margin', category: 'quality', description: '\u6bdb\u5229\u6da6/\u8425\u6536', ic: 0.029, ir: 0.62 },
  { id: 'volatility_20d', name: '20\u65e5\u6ce2\u52a8\u7387', expression: 'std(returns, 20)', category: 'volatility', description: '\u8fc7\u53bb20\u5929\u6536\u76ca\u7387\u6807\u51c6\u5dee', ic: -0.025, ir: -0.52 },
  { id: 'volatility_60d', name: '60\u65e5\u6ce2\u52a8\u7387', expression: 'std(returns, 60)', category: 'volatility', description: '\u8fc7\u53bb60\u5929\u6536\u76ca\u7387\u6807\u51c6\u5dee', ic: -0.028, ir: -0.58 },
  { id: 'size_market_cap', name: '\u5e02\u503c\u56e0\u5b50', expression: 'log(market_cap)', category: 'size', description: '\u5e02\u503c\u5bf9\u6570', ic: 0.022, ir: 0.45 },
  { id: 'growth_revenue', name: '\u8425\u6536\u589e\u957f', expression: 'revenue_growth_yoy', category: 'growth', description: '\u8425\u6536\u540c\u6bd4\u589e\u957f\u7387', ic: 0.030, ir: 0.62 },
  { id: 'growth_earnings', name: '\u76c8\u5229\u589e\u957f', expression: 'earnings_growth_yoy', category: 'growth', description: '\u76c8\u5229\u540c\u6bd4\u589e\u957f\u7387', ic: 0.028, ir: 0.58 },
]

const CATEGORY_COLORS: Record<FactorCategory, string> = {
  momentum: 'blue',
  value: 'green',
  quality: 'purple',
  volatility: 'red',
  size: 'orange',
  growth: 'cyan',
  technical: 'magenta',
  fundamental: 'gold',
  custom: 'default',
}

const CATEGORY_LABELS: Record<FactorCategory, string> = {
  momentum: '\u52a8\u91cf',
  value: '\u4ef7\u503c',
  quality: '\u8d28\u91cf',
  volatility: '\u6ce2\u52a8',
  size: '\u89c4\u6a21',
  growth: '\u6210\u957f',
  technical: '\u6280\u672f',
  fundamental: '\u57fa\u672c\u9762',
  custom: '\u81ea\u5b9a\u4e49',
}

export default function StepAlpha({ value = DEFAULT_ALPHA_CONFIG, onChange, onAskAI }: StepAlphaProps) {
  const [selectedCategory, setSelectedCategory] = useState<FactorCategory | 'all'>('all')

  const filteredFactors = selectedCategory === 'all'
    ? FACTOR_LIBRARY
    : FACTOR_LIBRARY.filter(f => f.category === selectedCategory)

  const updateField = <K extends keyof AlphaConfig>(field: K, fieldValue: AlphaConfig[K]) => {
    onChange({ ...value, [field]: fieldValue })
  }

  const addFactor = (factorId: string) => {
    const factor = FACTOR_LIBRARY.find(f => f.id === factorId)
    if (!factor || value.factors.some(f => f.factorId === factorId)) return

    const newFactor: FactorSelection = {
      factorId: factor.id,
      expression: factor.expression,
      direction: factor.ic >= 0 ? 1 : -1,
      lookbackPeriod: parseInt(factor.id.match(/\d+/)?.[0] || '20'),
    }
    updateField('factors', [...value.factors, newFactor])
  }

  const removeFactor = (factorId: string) => {
    updateField('factors', value.factors.filter(f => f.factorId !== factorId))
  }

  const updateFactorWeight = (factorId: string, weight: number) => {
    updateField('factors', value.factors.map(f =>
      f.factorId === factorId ? { ...f, weight } : f
    ))
  }

  return (
    <div className="space-y-6">
      <Alert
        type="info"
        showIcon
        icon={<InfoCircleOutlined />}
        message={'\u4ec0\u4e48\u662f\u56e0\u5b50\uff1f'}
        description={'\u56e0\u5b50\u662f\u91cf\u5316\u6295\u8d44\u7684\u6838\u5fc3\uff0c\u662f\u9884\u6d4b\u80a1\u7968\u672a\u6765\u6536\u76ca\u7684\u6307\u6807\u3002\u597d\u7684\u56e0\u5b50\u5e94\u8be5\u6709\u6301\u7eed\u7684\u9884\u6d4b\u80fd\u529b\uff08IC\uff09\u548c\u7a33\u5b9a\u6027\uff08IR\uff09\u3002\u5e38\u89c1\u56e0\u5b50\u5305\u62ec\u52a8\u91cf\uff08\u6da8\u52bf\u5ef6\u7eed\uff09\u3001\u4ef7\u503c\uff08\u4f4e\u4f30\u80a1\u7968\uff09\u3001\u8d28\u91cf\uff08\u76c8\u5229\u80fd\u529b\u5f3a\uff09\u7b49\u3002'}
      />

      <Row gutter={24}>
        <Col span={14}>
          <Card title={'\u56e0\u5b50\u5e93'} extra={
            <Button
              type="link"
              icon={<RobotOutlined />}
              onClick={() => onAskAI?.('\u63a8\u8350\u9002\u5408\u6211\u7684\u56e0\u5b50\u7ec4\u5408')}
            >
              AI{'\u63a8\u8350'}
            </Button>
          }>
            <div className="flex gap-2 mb-4 flex-wrap">
              <Tag
                color={selectedCategory === 'all' ? 'blue' : 'default'}
                className="cursor-pointer"
                onClick={() => setSelectedCategory('all')}
              >
                {'\u5168\u90e8'}
              </Tag>
              {(Object.keys(CATEGORY_LABELS) as FactorCategory[]).map(cat => (
                <Tag
                  key={cat}
                  color={selectedCategory === cat ? CATEGORY_COLORS[cat] : 'default'}
                  className="cursor-pointer"
                  onClick={() => setSelectedCategory(cat)}
                >
                  {CATEGORY_LABELS[cat]}
                </Tag>
              ))}
            </div>

            <div className="grid grid-cols-2 gap-3 max-h-96 overflow-y-auto">
              {filteredFactors.map(factor => {
                const isSelected = value.factors.some(f => f.factorId === factor.id)
                return (
                  <div
                    key={factor.id}
                    onClick={() => isSelected ? removeFactor(factor.id) : addFactor(factor.id)}
                    className={`
                      p-3 rounded-lg border cursor-pointer transition-all
                      ${isSelected
                        ? 'border-primary-500 bg-primary-500/10'
                        : 'border-dark-border hover:border-gray-600'
                      }
                    `}
                  >
                    <div className="flex justify-between items-start mb-2">
                      <div>
                        <span className="font-medium">{factor.name}</span>
                        <Tag color={CATEGORY_COLORS[factor.category]} className="ml-2 text-xs">
                          {CATEGORY_LABELS[factor.category]}
                        </Tag>
                      </div>
                    </div>
                    <div className="text-xs text-gray-500 mb-2">{factor.description}</div>
                    <div className="flex justify-between text-xs">
                      <span className={factor.ic >= 0 ? 'text-profit' : 'text-loss'}>
                        IC: {factor.ic.toFixed(3)}
                      </span>
                      <span className="text-gray-400">IR: {factor.ir.toFixed(2)}</span>
                    </div>
                  </div>
                )
              })}
            </div>
          </Card>
        </Col>

        <Col span={10}>
          <Card title={'\u5df2\u9009\u56e0\u5b50 (' + value.factors.length + ')'}>
            {value.factors.length === 0 ? (
              <Empty description={'\u4ece\u5de6\u4fa7\u9009\u62e9\u56e0\u5b50'} />
            ) : (
              <div className="space-y-3 max-h-48 overflow-y-auto">
                {value.factors.map(factor => {
                  const factorInfo = FACTOR_LIBRARY.find(f => f.id === factor.factorId)
                  return (
                    <div
                      key={factor.factorId}
                      className="flex items-center justify-between p-2 bg-dark-hover rounded"
                    >
                      <div className="flex items-center gap-2">
                        <Tag color={CATEGORY_COLORS[factorInfo?.category || 'custom']}>
                          {factorInfo?.name || factor.factorId}
                        </Tag>
                        <span className="text-xs text-gray-500">
                          {factor.direction === 1 ? '\u6b63\u5411' : '\u53cd\u5411'}
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        {value.combineMethod === 'custom_weight' && (
                          <InputNumber
                            size="small"
                            value={factor.weight || 1}
                            onChange={(v) => updateFactorWeight(factor.factorId, v || 1)}
                            min={0}
                            max={10}
                            step={0.1}
                            style={{ width: 60 }}
                          />
                        )}
                        <Button
                          type="text"
                          danger
                          size="small"
                          icon={<DeleteOutlined />}
                          onClick={() => removeFactor(factor.factorId)}
                        />
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </Card>

          <Card title={'\u56e0\u5b50\u7ec4\u5408\u914d\u7f6e'} className="mt-4">
            <Form layout="vertical">
              <Form.Item label={'\u7ec4\u5408\u65b9\u5f0f'}>
                <Select
                  value={value.combineMethod}
                  onChange={(v) => updateField('combineMethod', v)}
                >
                  <Option value="equal_weight">{'\u7b49\u6743\u91cd'}</Option>
                  <Option value="ic_weight">IC{'\u52a0\u6743'}</Option>
                  <Option value="ir_weight">IR{'\u52a0\u6743'}</Option>
                  <Option value="custom_weight">{'\u81ea\u5b9a\u4e49\u6743\u91cd'}</Option>
                </Select>
              </Form.Item>

              <Form.Item label={'\u6807\u51c6\u5316\u65b9\u5f0f'}>
                <Select
                  value={value.normalize}
                  onChange={(v) => updateField('normalize', v)}
                >
                  <Option value="zscore">Z-Score ({'\u5747\u503c'}0{'\uff0c\u6807\u51c6\u5dee'}1)</Option>
                  <Option value="rank">{'\u6392\u540d'} (0-1)</Option>
                  <Option value="percentile">{'\u767e\u5206\u4f4d'}</Option>
                  <Option value="minmax">Min-Max</Option>
                </Select>
              </Form.Item>

              <Form.Item label={'\u4e2d\u6027\u5316\u5904\u7406'}>
                <Select
                  value={value.neutralize}
                  onChange={(v) => updateField('neutralize', v)}
                >
                  <Option value="sector">{'\u884c\u4e1a\u4e2d\u6027'}</Option>
                  <Option value="market_cap">{'\u5e02\u503c\u4e2d\u6027'}</Option>
                  <Option value="both">{'\u884c\u4e1a+\u5e02\u503c\u4e2d\u6027'}</Option>
                  <Option value="none">{'\u4e0d\u4e2d\u6027\u5316'}</Option>
                </Select>
                <div className="text-xs text-gray-500 mt-1">
                  {'\u4e2d\u6027\u5316\u53ef\u4ee5\u53bb\u9664\u884c\u4e1a/\u89c4\u6a21\u7684\u5f71\u54cd\uff0c\u8ba9\u56e0\u5b50\u66f4\u7eaf\u7cb9'}
                </div>
              </Form.Item>
            </Form>
          </Card>
        </Col>
      </Row>
    </div>
  )
}
