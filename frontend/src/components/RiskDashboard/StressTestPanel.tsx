/**
 * Phase 10: \u98ce\u9669\u7cfb\u7edf\u5347\u7ea7 - \u538b\u529b\u6d4b\u8bd5\u9762\u677f
 *
 * \u529f\u80fd:
 * - \u663e\u793a\u9884\u7f6e\u538b\u529b\u60c5\u666f\u5217\u8868
 * - \u8fd0\u884c\u5355\u4e2a/\u6279\u91cf\u538b\u529b\u6d4b\u8bd5
 * - \u663e\u793a\u6d4b\u8bd5\u7ed3\u679c\u548c\u5efa\u8bae
 */

import { useState, useEffect } from 'react'
import {
  Row, Col, Button, Table, Tag, Alert, Spin, Modal, Descriptions,
  Tooltip, Progress, message
} from 'antd'
import {
  ThunderboltOutlined, ExperimentOutlined, WarningOutlined,
  InfoCircleOutlined, PlayCircleOutlined
} from '@ant-design/icons'
import { Card } from '@/components/ui'
import {
  StressScenario, StressTestResult, ScenarioType, PRESET_SCENARIOS
} from '@/types/risk'

interface StressTestPanelProps {
  holdings: Record<string, number>
  portfolioValue?: number
  onResultsChange?: (results: StressTestResult[]) => void
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || ''

export default function StressTestPanel({
  holdings,
  portfolioValue = 1000000,
  onResultsChange
}: StressTestPanelProps) {
  const [scenarios, setScenarios] = useState<StressScenario[]>(PRESET_SCENARIOS)
  const [results, setResults] = useState<StressTestResult[]>([])
  const [loading, setLoading] = useState(false)
  const [selectedResult, setSelectedResult] = useState<StressTestResult | null>(null)
  const [runningScenario, setRunningScenario] = useState<string | null>(null)

  // \u52a0\u8f7d\u60c5\u666f\u5217\u8868
  useEffect(() => {
    const fetchScenarios = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/v1/risk/advanced/scenarios`)
        if (response.ok) {
          const data = await response.json()
          setScenarios(data.scenarios)
        }
      } catch (err) {
        console.error('\u52a0\u8f7d\u60c5\u666f\u5931\u8d25:', err)
      }
    }
    fetchScenarios()
  }, [])

  // \u8fd0\u884c\u5355\u4e2a\u538b\u529b\u6d4b\u8bd5
  const runSingleTest = async (scenarioId: string) => {
    if (Object.keys(holdings).length === 0) {
      message.warning('\u8bf7\u5148\u8f93\u5165\u6301\u4ed3\u4fe1\u606f')
      return
    }

    setRunningScenario(scenarioId)
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/risk/advanced/stress-test/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          holdings,
          portfolio_value: portfolioValue,
          scenario_id: scenarioId
        })
      })

      if (!response.ok) {
        throw new Error('\u538b\u529b\u6d4b\u8bd5\u5931\u8d25')
      }

      const result = await response.json()

      // \u66f4\u65b0\u7ed3\u679c\u5217\u8868
      setResults(prev => {
        const filtered = prev.filter(r => r.scenario.id !== scenarioId)
        return [...filtered, result]
      })

      message.success(`${result.scenario.name} \u6d4b\u8bd5\u5b8c\u6210`)
    } catch (err: any) {
      message.error(err.message)
    } finally {
      setRunningScenario(null)
    }
  }

  // \u8fd0\u884c\u6279\u91cf\u538b\u529b\u6d4b\u8bd5
  const runBatchTest = async () => {
    if (Object.keys(holdings).length === 0) {
      message.warning('\u8bf7\u5148\u8f93\u5165\u6301\u4ed3\u4fe1\u606f')
      return
    }

    setLoading(true)
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/risk/advanced/stress-test/batch`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          holdings,
          portfolio_value: portfolioValue,
          scenario_ids: []  // \u7a7a = \u8fd0\u884c\u6240\u6709
        })
      })

      if (!response.ok) {
        throw new Error('\u6279\u91cf\u538b\u529b\u6d4b\u8bd5\u5931\u8d25')
      }

      const data = await response.json()
      setResults(data.results)
      onResultsChange?.(data.results)

      message.success(`\u5b8c\u6210 ${data.results.length} \u4e2a\u60c5\u666f\u7684\u538b\u529b\u6d4b\u8bd5`)
    } catch (err: any) {
      message.error(err.message)
    } finally {
      setLoading(false)
    }
  }

  const getScenarioTypeTag = (type: ScenarioType) => {
    switch (type) {
      case 'historical':
        return <Tag color="blue">{'\u5386\u53f2'}</Tag>
      case 'hypothetical':
        return <Tag color="purple">{'\u5047\u8bbe'}</Tag>
      case 'custom':
        return <Tag color="orange">{'\u81ea\u5b9a\u4e49'}</Tag>
    }
  }

  const getLossColor = (lossPercent: number) => {
    if (lossPercent > 0.30) return '#cf1322'
    if (lossPercent > 0.20) return '#ff4d4f'
    if (lossPercent > 0.10) return '#faad14'
    return '#52c41a'
  }

  const formatMoney = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value)
  }

  // \u6392\u5e8f\u7ed3\u679c\uff1a\u4e8f\u635f\u4ece\u5927\u5230\u5c0f
  const sortedResults = [...results].sort(
    (a, b) => b.portfolioImpact.expectedLossPercent - a.portfolioImpact.expectedLossPercent
  )

  return (
    <div className="space-y-4">
      {/* \u64cd\u4f5c\u680f */}
      <Card>
        <Row justify="space-between" align="middle">
          <Col>
            <span className="text-lg font-medium">
              <ThunderboltOutlined className="mr-2" />
              {'\u538b\u529b\u6d4b\u8bd5'}
            </span>
            <span className="ml-4 text-gray-500 text-sm">
              {'\u6a21\u62df\u6781\u7aef\u5e02\u573a\u60c5\u51b5\u4e0b\u7684\u7ec4\u5408\u8868\u73b0'}
            </span>
          </Col>
          <Col>
            <Button
              type="primary"
              icon={<PlayCircleOutlined />}
              onClick={runBatchTest}
              loading={loading}
            >
              {'\u8fd0\u884c\u6240\u6709\u60c5\u666f'}
            </Button>
          </Col>
        </Row>
      </Card>

      {/* \u6d4b\u8bd5\u7ed3\u679c\u6982\u89c8 */}
      {results.length > 0 && (
        <Card title={'\u6d4b\u8bd5\u7ed3\u679c\u6982\u89c8'}>
          <Row gutter={24}>
            <Col span={6}>
              <div className="text-center">
                <div className="text-3xl font-bold" style={{ color: getLossColor(
                  Math.max(...results.map(r => r.portfolioImpact.expectedLossPercent))
                )}}>
                  -{(Math.max(...results.map(r => r.portfolioImpact.expectedLossPercent)) * 100).toFixed(1)}%
                </div>
                <div className="text-gray-500 text-sm">{'\u6700\u5927\u4e8f\u635f'}</div>
              </div>
            </Col>
            <Col span={6}>
              <div className="text-center">
                <div className="text-3xl font-bold text-yellow-500">
                  -{(results.reduce((sum, r) => sum + r.portfolioImpact.expectedLossPercent, 0) / results.length * 100).toFixed(1)}%
                </div>
                <div className="text-gray-500 text-sm">{'\u5e73\u5747\u4e8f\u635f'}</div>
              </div>
            </Col>
            <Col span={6}>
              <div className="text-center">
                <div className="text-3xl font-bold text-red-500">
                  {results.filter(r => r.portfolioImpact.liquidationRisk).length}
                </div>
                <div className="text-gray-500 text-sm">{'\u5f3a\u5e73\u98ce\u9669\u60c5\u666f'}</div>
              </div>
            </Col>
            <Col span={6}>
              <div className="text-center">
                <div className="text-3xl font-bold">
                  {Math.max(...results.map(r => r.portfolioImpact.recoveryDays))}
                </div>
                <div className="text-gray-500 text-sm">{'\u6700\u957f\u6062\u590d\u5929\u6570'}</div>
              </div>
            </Col>
          </Row>
        </Card>
      )}

      {/* \u60c5\u666f\u5217\u8868\u548c\u7ed3\u679c */}
      <Row gutter={16}>
        {/* \u60c5\u666f\u5217\u8868 */}
        <Col span={10}>
          <Card title={'\u538b\u529b\u60c5\u666f\u5217\u8868'}>
            <Table
              dataSource={scenarios}
              rowKey="id"
              size="small"
              pagination={false}
              scroll={{ y: 400 }}
              columns={[
                {
                  title: '\u60c5\u666f',
                  dataIndex: 'name',
                  key: 'name',
                  render: (name, record) => (
                    <Tooltip title={record.description}>
                      <span>{name}</span>
                    </Tooltip>
                  )
                },
                {
                  title: '\u7c7b\u578b',
                  dataIndex: 'type',
                  key: 'type',
                  width: 70,
                  render: getScenarioTypeTag
                },
                {
                  title: '\u64cd\u4f5c',
                  key: 'action',
                  width: 80,
                  render: (_, record) => (
                    <Button
                      type="link"
                      size="small"
                      icon={runningScenario === record.id ? <Spin size="small" /> : <ExperimentOutlined />}
                      onClick={() => runSingleTest(record.id)}
                      disabled={runningScenario !== null}
                    >
                      {'\u6d4b\u8bd5'}
                    </Button>
                  )
                }
              ]}
            />
          </Card>
        </Col>

        {/* \u7ed3\u679c\u5217\u8868 */}
        <Col span={14}>
          <Card
            title={`\u6d4b\u8bd5\u7ed3\u679c (${results.length})`}
            extra={
              results.length > 0 && (
                <Button type="link" size="small" onClick={() => setResults([])}>
                  {'\u6e05\u7a7a'}
                </Button>
              )
            }
          >
            {results.length === 0 ? (
              <div className="text-center text-gray-500 py-12">
                <ExperimentOutlined className="text-4xl mb-2" />
                <div>{'\u8fd0\u884c\u538b\u529b\u6d4b\u8bd5\u4ee5\u67e5\u770b\u7ed3\u679c'}</div>
              </div>
            ) : (
              <Table
                dataSource={sortedResults}
                rowKey={(r) => r.scenario.id}
                size="small"
                pagination={false}
                scroll={{ y: 400 }}
                onRow={(record) => ({
                  onClick: () => setSelectedResult(record),
                  className: 'cursor-pointer hover:bg-dark-hover'
                })}
                columns={[
                  {
                    title: '\u60c5\u666f',
                    dataIndex: ['scenario', 'name'],
                    key: 'scenario',
                    ellipsis: true
                  },
                  {
                    title: '\u9884\u671f\u4e8f\u635f',
                    dataIndex: ['portfolioImpact', 'expectedLossPercent'],
                    key: 'loss',
                    width: 100,
                    align: 'right',
                    render: (value) => (
                      <span style={{ color: getLossColor(value) }}>
                        -{(value * 100).toFixed(1)}%
                      </span>
                    )
                  },
                  {
                    title: '\u4e8f\u635f\u91d1\u989d',
                    dataIndex: ['portfolioImpact', 'expectedLoss'],
                    key: 'lossAmount',
                    width: 100,
                    align: 'right',
                    render: (value) => (
                      <span className="text-red-500">
                        {formatMoney(-value)}
                      </span>
                    )
                  },
                  {
                    title: '\u98ce\u9669',
                    key: 'risk',
                    width: 70,
                    align: 'center',
                    render: (_, record) => (
                      record.portfolioImpact.liquidationRisk ? (
                        <Tag color="red">
                          <WarningOutlined /> {'\u5f3a\u5e73'}
                        </Tag>
                      ) : (
                        <Tag color="green">{'\u6b63\u5e38'}</Tag>
                      )
                    )
                  }
                ]}
              />
            )}
          </Card>
        </Col>
      </Row>

      {/* \u8be6\u7ec6\u7ed3\u679c\u5f39\u7a97 */}
      <Modal
        title={selectedResult ? `${selectedResult.scenario.name} - \u538b\u529b\u6d4b\u8bd5\u7ed3\u679c` : ''}
        open={!!selectedResult}
        onCancel={() => setSelectedResult(null)}
        footer={null}
        width={700}
      >
        {selectedResult && (
          <div className="space-y-4">
            {/* \u60c5\u666f\u4fe1\u606f */}
            <Descriptions title={'\u60c5\u666f\u4fe1\u606f'} column={2} size="small" bordered>
              <Descriptions.Item label={'\u7c7b\u578b'}>
                {getScenarioTypeTag(selectedResult.scenario.type)}
              </Descriptions.Item>
              <Descriptions.Item label={'\u63cf\u8ff0'}>
                {selectedResult.scenario.description}
              </Descriptions.Item>
              {selectedResult.scenario.historicalPeriod && (
                <>
                  <Descriptions.Item label={'\u5386\u53f2\u65f6\u6bb5'}>
                    {selectedResult.scenario.historicalPeriod.startDate} ~ {selectedResult.scenario.historicalPeriod.endDate}
                  </Descriptions.Item>
                  <Descriptions.Item label={'SPY \u56de\u64a4'}>
                    {(selectedResult.scenario.historicalPeriod.spyDrawdown * 100).toFixed(1)}%
                  </Descriptions.Item>
                </>
              )}
            </Descriptions>

            {/* \u7ec4\u5408\u5f71\u54cd */}
            <Descriptions title={'\u7ec4\u5408\u5f71\u54cd'} column={2} size="small" bordered>
              <Descriptions.Item label={'\u9884\u671f\u4e8f\u635f'}>
                <span className="text-red-500 text-lg font-bold">
                  -{(selectedResult.portfolioImpact.expectedLossPercent * 100).toFixed(2)}%
                </span>
              </Descriptions.Item>
              <Descriptions.Item label={'\u4e8f\u635f\u91d1\u989d'}>
                <span className="text-red-500">
                  {formatMoney(-selectedResult.portfolioImpact.expectedLoss)}
                </span>
              </Descriptions.Item>
              <Descriptions.Item label={'VaR \u5f71\u54cd'}>
                {(selectedResult.portfolioImpact.varImpact * 100).toFixed(2)}%
              </Descriptions.Item>
              <Descriptions.Item label={'\u6700\u5927\u56de\u64a4'}>
                {(selectedResult.portfolioImpact.maxDrawdown * 100).toFixed(2)}%
              </Descriptions.Item>
              <Descriptions.Item label={'\u9884\u8ba1\u6062\u590d\u5929\u6570'}>
                {selectedResult.portfolioImpact.recoveryDays} {'\u5929'}
              </Descriptions.Item>
              <Descriptions.Item label={'\u5f3a\u5e73\u98ce\u9669'}>
                {selectedResult.portfolioImpact.liquidationRisk ? (
                  <Tag color="red">{'\u662f'}</Tag>
                ) : (
                  <Tag color="green">{'\u5426'}</Tag>
                )}
              </Descriptions.Item>
            </Descriptions>

            {/* \u6301\u4ed3\u5f71\u54cd TOP5 */}
            {selectedResult.positionImpacts.length > 0 && (
              <Card title={'\u6301\u4ed3\u5f71\u54cd TOP5'} size="small">
                <Table
                  dataSource={selectedResult.positionImpacts.slice(0, 5)}
                  rowKey="symbol"
                  size="small"
                  pagination={false}
                  columns={[
                    { title: '\u80a1\u7968', dataIndex: 'symbol', key: 'symbol' },
                    {
                      title: '\u5f53\u524d\u6743\u91cd',
                      dataIndex: 'currentWeight',
                      key: 'weight',
                      render: (v) => `${(v * 100).toFixed(1)}%`
                    },
                    {
                      title: '\u4e8f\u635f',
                      dataIndex: 'lossPercent',
                      key: 'loss',
                      render: (v) => (
                        <span className="text-red-500">-{(v * 100).toFixed(1)}%</span>
                      )
                    },
                    {
                      title: '\u8d21\u732e',
                      dataIndex: 'contribution',
                      key: 'contrib',
                      render: (v) => `${(v * 100).toFixed(1)}%`
                    }
                  ]}
                />
              </Card>
            )}

            {/* \u5efa\u8bae */}
            {selectedResult.recommendations.length > 0 && (
              <Alert
                type="info"
                message={'\u98ce\u9669\u7ba1\u7406\u5efa\u8bae'}
                description={
                  <ul className="list-disc list-inside mt-2">
                    {selectedResult.recommendations.map((rec, i) => (
                      <li key={i}>{rec}</li>
                    ))}
                  </ul>
                }
                showIcon
                icon={<InfoCircleOutlined />}
              />
            )}
          </div>
        )}
      </Modal>
    </div>
  )
}
