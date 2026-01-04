/**
 * Walk-Forward 验证配置组件
 * Phase 9: 回测引擎升级
 */
import { useState, useEffect } from 'react'
import {
  Form, InputNumber, Select, Switch, Button, Alert, Row, Col,
  Slider, Tooltip, Spin, message, Statistic
} from 'antd'
import {
  InfoCircleOutlined, PlayCircleOutlined, SettingOutlined,
  ExperimentOutlined, CheckCircleOutlined
} from '@ant-design/icons'
import { Card } from '@/components/ui'
import {
  WalkForwardConfig, WalkForwardResult, DEFAULT_WALK_FORWARD_CONFIG,
  ASSESSMENT_COLORS
} from '@/types/backtest'

const { Option } = Select

interface WalkForwardConfigProps {
  strategyId: string
  onRunValidation?: (config: WalkForwardConfig) => Promise<WalkForwardResult>
  onResult?: (result: WalkForwardResult) => void
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || ''

export default function WalkForwardConfigComponent({
  strategyId,
  onRunValidation,
  onResult
}: WalkForwardConfigProps) {
  const [config, setConfig] = useState<WalkForwardConfig>(DEFAULT_WALK_FORWARD_CONFIG)
  const [loading, setLoading] = useState(false)
  const [estimatedRounds, setEstimatedRounds] = useState<number | null>(null)
  const [dateRange, setDateRange] = useState({
    startDate: '2015-01-01',
    endDate: '2024-12-31'
  })

  useEffect(() => {
    const fetchEstimate = async () => {
      try {
        const params = new URLSearchParams({
          start_date: dateRange.startDate,
          end_date: dateRange.endDate,
          train_period: config.trainPeriod.toString(),
          test_period: config.testPeriod.toString(),
          step_size: config.stepSize.toString()
        })
        const response = await fetch(
          `${API_BASE_URL}/api/v1/backtests/advanced/estimate-rounds?${params}`
        )
        if (response.ok) {
          const data = await response.json()
          setEstimatedRounds(data.estimated_rounds)
        }
      } catch (error) {
        console.error('Failed to estimate rounds:', error)
      }
    }
    fetchEstimate()
  }, [config.trainPeriod, config.testPeriod, config.stepSize, dateRange])

  const updateConfig = <K extends keyof WalkForwardConfig>(
    field: K,
    value: WalkForwardConfig[K]
  ) => {
    setConfig(prev => ({ ...prev, [field]: value }))
  }

  const handleRunValidation = async () => {
    if (!strategyId) {
      message.error('\u8bf7\u5148\u9009\u62e9\u7b56\u7565')
      return
    }

    setLoading(true)
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/v1/backtests/advanced/walk-forward`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            strategy_id: strategyId,
            start_date: dateRange.startDate,
            end_date: dateRange.endDate,
            initial_capital: 1000000,
            config: {
              train_period: config.trainPeriod,
              test_period: config.testPeriod,
              step_size: config.stepSize,
              optimize_target: config.optimizeTarget,
              parameter_ranges: config.parameterRanges,
              min_train_samples: config.minTrainSamples,
              expanding_window: config.expandingWindow
            }
          })
        }
      )

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Validation failed')
      }

      const data = await response.json()
      message.success('Walk-Forward \u9a8c\u8bc1\u5b8c\u6210')
      onResult?.(data.result)
    } catch (error: any) {
      message.error('\u9a8c\u8bc1\u5931\u8d25: ' + error.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <Alert
        type="info"
        showIcon
        icon={<InfoCircleOutlined />}
        message={'\u4ec0\u4e48\u662f Walk-Forward \u9a8c\u8bc1\uff1f'}
        description={
          <div className="space-y-2 mt-2">
            <p>
              {'\u4f20\u7edf\u56de\u6d4b\u7528\u5168\u90e8\u6570\u636e\u4f18\u5316\u53c2\u6570\uff0c\u5bb9\u6613\u5bfc\u81f4'}<strong>{'\u8fc7\u62df\u5408'}</strong>{'——'}
              {'\u7b56\u7565\u53ea\u5728\u5386\u53f2\u6570\u636e\u4e0a\u8868\u73b0\u597d\uff0c\u5b9e\u76d8\u5374\u4e8f\u635f\u3002'}
            </p>
            <p>
              Walk-Forward {'\u9a8c\u8bc1\u6a21\u62df\u771f\u5b9e\u6295\u8d44\uff1a'}
              <span className="text-blue-400">{'\u7528\u8fc7\u53bb\u6570\u636e\u8bad\u7ec3\uff0c\u7528\u672a\u6765\u6570\u636e\u6d4b\u8bd5'}</span>{'。'}
              {'\u53ea\u6709'}<strong>{'\u6837\u672c\u5916'}</strong>{'\u8868\u73b0\u624d\u80fd\u53cd\u6620\u7b56\u7565\u7684\u771f\u5b9e\u80fd\u529b\u3002'}
            </p>
          </div>
        }
      />

      <Row gutter={24}>
        <Col span={16}>
          <Card title={<><SettingOutlined /> {'\u7a97\u53e3\u914d\u7f6e'}</>}>
            <Form layout="vertical">
              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item label={'\u5f00\u59cb\u65e5\u671f'}>
                    <input
                      type="date"
                      value={dateRange.startDate}
                      onChange={(e) => setDateRange(prev => ({ ...prev, startDate: e.target.value }))}
                      className="w-full p-2 bg-dark-hover border border-dark-border rounded"
                    />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item label={'\u7ed3\u675f\u65e5\u671f'}>
                    <input
                      type="date"
                      value={dateRange.endDate}
                      onChange={(e) => setDateRange(prev => ({ ...prev, endDate: e.target.value }))}
                      className="w-full p-2 bg-dark-hover border border-dark-border rounded"
                    />
                  </Form.Item>
                </Col>
              </Row>

              <Row gutter={16}>
                <Col span={8}>
                  <Form.Item
                    label={
                      <Tooltip title={'\u7528\u4e8e\u4f18\u5316\u53c2\u6570\u7684\u5386\u53f2\u6570\u636e\u957f\u5ea6'}>
                        {'\u8bad\u7ec3\u671f\u957f\u5ea6 (\u6708)'} <InfoCircleOutlined />
                      </Tooltip>
                    }
                  >
                    <InputNumber
                      value={config.trainPeriod}
                      onChange={(v) => updateConfig('trainPeriod', v || 36)}
                      min={12}
                      max={120}
                      className="w-full"
                    />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item
                    label={
                      <Tooltip title={'\u6837\u672c\u5916\u9a8c\u8bc1\u7684\u65f6\u95f4\u957f\u5ea6'}>
                        {'\u6d4b\u8bd5\u671f\u957f\u5ea6 (\u6708)'} <InfoCircleOutlined />
                      </Tooltip>
                    }
                  >
                    <InputNumber
                      value={config.testPeriod}
                      onChange={(v) => updateConfig('testPeriod', v || 12)}
                      min={1}
                      max={36}
                      className="w-full"
                    />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item
                    label={
                      <Tooltip title={'\u6bcf\u8f6e\u5411\u524d\u6eda\u52a8\u7684\u65f6\u95f4'}>
                        {'\u6eda\u52a8\u6b65\u957f (\u6708)'} <InfoCircleOutlined />
                      </Tooltip>
                    }
                  >
                    <InputNumber
                      value={config.stepSize}
                      onChange={(v) => updateConfig('stepSize', v || 12)}
                      min={1}
                      max={24}
                      className="w-full"
                    />
                  </Form.Item>
                </Col>
              </Row>

              <Form.Item label={'\u4f18\u5316\u76ee\u6807'}>
                <Select
                  value={config.optimizeTarget}
                  onChange={(v) => updateConfig('optimizeTarget', v)}
                >
                  <Option value="sharpe">{'\u590f\u666e\u6bd4\u7387 (\u63a8\u8350)'}</Option>
                  <Option value="returns">{'\u5e74\u5316\u6536\u76ca'}</Option>
                  <Option value="calmar">{'\u5361\u5c14\u739b\u6bd4\u7387'}</Option>
                  <Option value="sortino">{'\u7d22\u63d0\u8bfa\u6bd4\u7387'}</Option>
                </Select>
              </Form.Item>

              <div className="border-t border-dark-border pt-4 mt-4">
                <h4 className="text-sm text-gray-400 mb-4">{'\u9ad8\u7ea7\u9009\u9879'}</h4>
                <Row gutter={16}>
                  <Col span={12}>
                    <Form.Item
                      label={
                        <Tooltip title={'\u4f7f\u7528\u6269\u5c55\u7a97\u53e3\u65f6\uff0c\u8bad\u7ec3\u671f\u4f1a\u968f\u65f6\u95f4\u589e\u957f'}>
                          {'\u4f7f\u7528\u6269\u5c55\u7a97\u53e3'} <InfoCircleOutlined />
                        </Tooltip>
                      }
                    >
                      <Switch
                        checked={config.expandingWindow}
                        onChange={(v) => updateConfig('expandingWindow', v)}
                      />
                      <span className="ml-2 text-gray-500 text-sm">
                        {config.expandingWindow ? '\u662f' : '\u5426'}
                      </span>
                    </Form.Item>
                  </Col>
                  <Col span={12}>
                    <Form.Item label={'\u6700\u5c0f\u8bad\u7ec3\u6837\u672c\u6570'}>
                      <InputNumber
                        value={config.minTrainSamples}
                        onChange={(v) => updateConfig('minTrainSamples', v || 252)}
                        min={60}
                        max={1000}
                        className="w-full"
                      />
                    </Form.Item>
                  </Col>
                </Row>
              </div>
            </Form>
          </Card>
        </Col>

        <Col span={8}>
          <Card className="bg-dark-hover">
            <div className="text-center space-y-4">
              <ExperimentOutlined className="text-4xl text-primary-500" />
              <Statistic
                title={'\u9884\u4f30\u9a8c\u8bc1\u8f6e\u6570'}
                value={estimatedRounds ?? '-'}
                suffix={'\u8f6e'}
                valueStyle={{ color: estimatedRounds && estimatedRounds >= 2 ? '#52c41a' : '#ff4d4f' }}
              />
              {estimatedRounds !== null && estimatedRounds < 2 && (
                <Alert
                  type="warning"
                  message={'\u6570\u636e\u4e0d\u8db3'}
                  description={'\u81f3\u5c11\u9700\u89812\u8f6e\u9a8c\u8bc1\uff0c\u8bf7\u6269\u5927\u65e5\u671f\u8303\u56f4\u6216\u8c03\u6574\u7a97\u53e3\u914d\u7f6e'}
                  showIcon
                />
              )}
            </div>
          </Card>

          <Card className="mt-4">
            <h4 className="font-medium mb-3">{'\u5e38\u7528\u914d\u7f6e'}</h4>
            <div className="space-y-2 text-sm">
              <div
                className="p-2 bg-dark-hover rounded cursor-pointer hover:bg-dark-card transition"
                onClick={() => setConfig({
                  ...config,
                  trainPeriod: 36,
                  testPeriod: 12,
                  stepSize: 12
                })}
              >
                <span className="text-blue-400">{'\u6807\u51c6\u914d\u7f6e:'}</span> 3{'\u5e74\u8bad\u7ec3'} + 1{'\u5e74\u6d4b\u8bd5'}
              </div>
              <div
                className="p-2 bg-dark-hover rounded cursor-pointer hover:bg-dark-card transition"
                onClick={() => setConfig({
                  ...config,
                  trainPeriod: 24,
                  testPeriod: 6,
                  stepSize: 6
                })}
              >
                <span className="text-green-400">{'\u5feb\u901f\u9a8c\u8bc1:'}</span> 2{'\u5e74\u8bad\u7ec3'} + {'\u534a\u5e74\u6d4b\u8bd5'}
              </div>
              <div
                className="p-2 bg-dark-hover rounded cursor-pointer hover:bg-dark-card transition"
                onClick={() => setConfig({
                  ...config,
                  trainPeriod: 60,
                  testPeriod: 12,
                  stepSize: 12
                })}
              >
                <span className="text-yellow-400">{'\u957f\u671f\u7a33\u5b9a:'}</span> 5{'\u5e74\u8bad\u7ec3'} + 1{'\u5e74\u6d4b\u8bd5'}
              </div>
            </div>
          </Card>

          <Button
            type="primary"
            size="large"
            icon={loading ? <Spin size="small" /> : <PlayCircleOutlined />}
            onClick={handleRunValidation}
            disabled={loading || !estimatedRounds || estimatedRounds < 2}
            className="w-full mt-4"
          >
            {loading ? '\u9a8c\u8bc1\u4e2d...' : '\u5f00\u59cb Walk-Forward \u9a8c\u8bc1'}
          </Button>
        </Col>
      </Row>
    </div>
  )
}
