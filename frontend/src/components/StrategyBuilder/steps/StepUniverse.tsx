/**
 * Step 1: 投资池配置组件
 * 定义策略可交易的股票范围
 */
import { Form, Select, InputNumber, Row, Col, Alert, Statistic } from 'antd'
import { InfoCircleOutlined, BankOutlined } from '@ant-design/icons'
import { Card } from '@/components/ui'
import { UniverseConfig, BasePool, Sector, DEFAULT_UNIVERSE_CONFIG } from '@/types/strategy'
import { useMemo } from 'react'

const { Option } = Select

interface StepUniverseProps {
  value: UniverseConfig
  onChange: (config: UniverseConfig) => void
}

const BASE_POOLS: { value: BasePool; label: string; count: number }[] = [
  { value: 'SP500', label: 'S&P 500', count: 500 },
  { value: 'NASDAQ100', label: 'NASDAQ 100', count: 100 },
  { value: 'DOW30', label: 'Dow Jones 30', count: 30 },
  { value: 'RUSSELL1000', label: 'Russell 1000', count: 1000 },
  { value: 'RUSSELL2000', label: 'Russell 2000', count: 2000 },
]

const SECTORS: { value: Sector; label: string }[] = [
  { value: 'technology', label: '\u79d1\u6280' },
  { value: 'healthcare', label: '\u533b\u7597\u4fdd\u5065' },
  { value: 'financials', label: '\u91d1\u878d' },
  { value: 'consumer_discretionary', label: '\u975e\u5fc5\u9700\u6d88\u8d39' },
  { value: 'consumer_staples', label: '\u5fc5\u9700\u6d88\u8d39' },
  { value: 'industrials', label: '\u5de5\u4e1a' },
  { value: 'materials', label: '\u539f\u6750\u6599' },
  { value: 'energy', label: '\u80fd\u6e90' },
  { value: 'utilities', label: '\u516c\u7528\u4e8b\u4e1a' },
  { value: 'real_estate', label: '\u623f\u5730\u4ea7' },
  { value: 'communication_services', label: '\u901a\u4fe1\u670d\u52a1' },
]

export default function StepUniverse({ value = DEFAULT_UNIVERSE_CONFIG, onChange }: StepUniverseProps) {
  const estimatedCount = useMemo(() => {
    const baseCount = BASE_POOLS.find(p => p.value === value.basePool)?.count || 500
    let filtered = baseCount

    if (value.marketCap.min && value.marketCap.min > 10) {
      filtered = Math.floor(filtered * 0.7)
    }

    if (value.avgVolume > 500) {
      filtered = Math.floor(filtered * 0.8)
    }

    filtered = Math.floor(filtered * (1 - value.excludeSectors.length * 0.09))

    return Math.max(filtered, 10)
  }, [value])

  const updateField = <K extends keyof UniverseConfig>(field: K, fieldValue: UniverseConfig[K]) => {
    onChange({ ...value, [field]: fieldValue })
  }

  return (
    <div className="space-y-6">
      <Alert
        type="info"
        showIcon
        icon={<InfoCircleOutlined />}
        message={'\u4e3a\u4ec0\u4e48\u8981\u9009\u62e9\u6295\u8d44\u6c60\uff1f'}
        description={'\u4e13\u4e1a\u6295\u8d44\u8005\u4e0d\u4f1a\u968f\u4fbf\u4e70\u80a1\u7968\u3002\u4ed6\u4eec\u9996\u5148\u786e\u5b9a\u4e00\u4e2a\u201c\u53ef\u6295\u8d44\u8303\u56f4\u201d\uff0c\u6392\u9664\u6d41\u52a8\u6027\u5dee\u3001\u5e02\u503c\u592a\u5c0f\u3001\u6216\u81ea\u5df1\u4e0d\u4e86\u89e3\u7684\u80a1\u7968\u3002\u8fd9\u6837\u53ef\u4ee5\u964d\u4f4e\u6267\u884c\u98ce\u9669\uff0c\u786e\u4fdd\u7b56\u7565\u53ef\u884c\u3002'}
      />

      <Row gutter={24}>
        <Col span={16}>
          <Card>
            <Form layout="vertical">
              <Form.Item label={'\u57fa\u7840\u80a1\u7968\u6c60'} required>
                <Select
                  value={value.basePool}
                  onChange={(v) => updateField('basePool', v)}
                  size="large"
                >
                  {BASE_POOLS.map(pool => (
                    <Option key={pool.value} value={pool.value}>
                      <div className="flex justify-between items-center">
                        <span>{pool.label}</span>
                        <span className="text-gray-500 text-sm">{pool.count} {'\u53ea'}</span>
                      </div>
                    </Option>
                  ))}
                </Select>
              </Form.Item>

              <Form.Item label={'\u5e02\u503c\u8303\u56f4 (\u4ebf\u7f8e\u5143)'}>
                <Row gutter={16}>
                  <Col span={12}>
                    <InputNumber
                      placeholder={'\u6700\u5c0f\u5e02\u503c'}
                      value={value.marketCap.min}
                      onChange={(v) => updateField('marketCap', { ...value.marketCap, min: v })}
                      min={0}
                      style={{ width: '100%' }}
                      addonAfter={'\u4ebf'}
                    />
                  </Col>
                  <Col span={12}>
                    <InputNumber
                      placeholder={'\u6700\u5927\u5e02\u503c (\u4e0d\u9650)'}
                      value={value.marketCap.max}
                      onChange={(v) => updateField('marketCap', { ...value.marketCap, max: v })}
                      min={0}
                      style={{ width: '100%' }}
                      addonAfter={'\u4ebf'}
                    />
                  </Col>
                </Row>
                <div className="text-xs text-gray-500 mt-1">
                  {'\u5e02\u503c\u8d8a\u5927\u8d8a\u7a33\u5b9a\uff0c\u4f46\u589e\u957f\u7a7a\u95f4\u53ef\u80fd\u6709\u9650'}
                </div>
              </Form.Item>

              <Form.Item label={'\u65e5\u5747\u6210\u4ea4\u989d\u4e0b\u9650 (\u4e07\u7f8e\u5143)'}>
                <InputNumber
                  value={value.avgVolume}
                  onChange={(v) => updateField('avgVolume', v || 500)}
                  min={0}
                  style={{ width: '100%' }}
                  addonAfter={'\u4e07'}
                />
                <div className="text-xs text-gray-500 mt-1">
                  <span className="text-yellow-500">{'\u5efa\u8bae:'}</span> {'\u4f4e\u4e8e100\u4e07\u7684\u80a1\u7968\u53ef\u80fd\u96be\u4ee5\u4e70\u5356'}
                </div>
              </Form.Item>

              <Form.Item label={'\u6700\u77ed\u4e0a\u5e02\u65f6\u95f4 (\u5e74)'}>
                <InputNumber
                  value={value.listingAge}
                  onChange={(v) => updateField('listingAge', v || 1)}
                  min={0}
                  max={20}
                  style={{ width: '100%' }}
                  addonAfter={'\u5e74'}
                />
                <div className="text-xs text-gray-500 mt-1">
                  {'\u65b0\u4e0a\u5e02\u80a1\u7968\u6570\u636e\u4e0d\u8db3\uff0c\u53ef\u80fd\u5f71\u54cd\u56e0\u5b50\u8ba1\u7b97'}
                </div>
              </Form.Item>

              <Form.Item label={'\u6392\u9664\u884c\u4e1a'}>
                <Select
                  mode="multiple"
                  value={value.excludeSectors}
                  onChange={(v) => updateField('excludeSectors', v)}
                  placeholder={'\u9009\u62e9\u8981\u6392\u9664\u7684\u884c\u4e1a'}
                >
                  {SECTORS.map(sector => (
                    <Option key={sector.value} value={sector.value}>
                      {sector.label}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Form>
          </Card>
        </Col>

        <Col span={8}>
          <Card className="bg-dark-hover">
            <div className="text-center">
              <BankOutlined className="text-4xl text-primary-500 mb-4" />
              <Statistic
                title={'\u9884\u4f30\u7b26\u5408\u6761\u4ef6\u80a1\u7968'}
                value={estimatedCount}
                suffix={'\u53ea'}
                valueStyle={{ color: '#1890ff' }}
              />
              <div className="text-xs text-gray-500 mt-4">
                {'\u57fa\u4e8e\u5f53\u524d\u7b5b\u9009\u6761\u4ef6\u7684\u4f30\u7b97\u503c'}
              </div>
            </div>
          </Card>

          <Card className="mt-4">
            <h4 className="font-medium mb-2">{'\u5e38\u89c1\u914d\u7f6e\u5efa\u8bae'}</h4>
            <div className="space-y-2 text-sm text-gray-400">
              <div>
                <span className="text-blue-400">{'\u7a33\u5065\u578b:'}</span> S&P 500, {'\u5e02\u503c'}&gt;100{'\u4ebf'}
              </div>
              <div>
                <span className="text-green-400">{'\u6210\u957f\u578b:'}</span> NASDAQ 100, {'\u5e02\u503c'}&gt;10{'\u4ebf'}
              </div>
              <div>
                <span className="text-yellow-400">{'\u5c0f\u76d8\u80a1:'}</span> Russell 2000, {'\u5e02\u503c'}1-50{'\u4ebf'}
              </div>
            </div>
          </Card>
        </Col>
      </Row>
    </div>
  )
}
