/**
 * Phase 10: \u98ce\u9669\u7cfb\u7edf\u5347\u7ea7 - \u98ce\u9669\u5206\u89e3\u56fe\u8868
 *
 * \u663e\u793a:
 * - \u98ce\u9669\u6765\u6e90\u5206\u89e3 (\u5e02\u573a/\u98ce\u683c/\u884c\u4e1a/\u7279\u8d28)
 * - \u98ce\u683c\u56e0\u5b50\u66b4\u9732
 * - \u884c\u4e1a\u56e0\u5b50\u66b4\u9732
 */

import { useMemo } from 'react'
import { Row, Col, Statistic, Table, Tag, Tooltip } from 'antd'
import {
  PieChartOutlined, BarChartOutlined, InfoCircleOutlined
} from '@ant-design/icons'
import { Card } from '@/components/ui'
import {
  RiskDecomposition, StyleFactor, STYLE_FACTOR_LABELS,
  INDUSTRY_FACTOR_LABELS, RISK_CONTRIBUTION_COLORS
} from '@/types/risk'

interface RiskDecompositionChartProps {
  data: RiskDecomposition
}

export default function RiskDecompositionChart({ data }: RiskDecompositionChartProps) {
  // \u98ce\u9669\u6765\u6e90\u6570\u636e
  const riskSourceData = useMemo(() => [
    { name: '\u5e02\u573a\u98ce\u9669', value: data.riskContributions.market, color: RISK_CONTRIBUTION_COLORS.market },
    { name: '\u98ce\u683c\u98ce\u9669', value: data.riskContributions.style, color: RISK_CONTRIBUTION_COLORS.style },
    { name: '\u884c\u4e1a\u98ce\u9669', value: data.riskContributions.industry, color: RISK_CONTRIBUTION_COLORS.industry },
    { name: '\u7279\u8d28\u98ce\u9669', value: data.riskContributions.specific, color: RISK_CONTRIBUTION_COLORS.specific },
  ], [data.riskContributions])

  // \u98ce\u683c\u56e0\u5b50\u6570\u636e
  const styleFactorData = useMemo(() => {
    const factors = Object.entries(data.factorExposures.style) as [StyleFactor, number][]
    return factors.map(([factor, exposure]) => ({
      factor,
      label: STYLE_FACTOR_LABELS[factor] || factor,
      exposure,
      riskContrib: data.styleRiskDetails[factor] || 0,
    })).sort((a, b) => Math.abs(b.exposure) - Math.abs(a.exposure))
  }, [data.factorExposures.style, data.styleRiskDetails])

  // \u884c\u4e1a\u56e0\u5b50\u6570\u636e
  const industryData = useMemo(() => {
    return Object.entries(data.factorExposures.industry)
      .map(([industry, exposure]) => ({
        industry,
        label: INDUSTRY_FACTOR_LABELS[industry as keyof typeof INDUSTRY_FACTOR_LABELS] || industry,
        exposure,
        riskContrib: data.industryRiskDetails[industry] || 0,
      }))
      .filter(d => Math.abs(d.exposure) > 0.01)
      .sort((a, b) => Math.abs(b.exposure) - Math.abs(a.exposure))
  }, [data.factorExposures.industry, data.industryRiskDetails])

  const getExposureColor = (exposure: number) => {
    if (exposure > 0.3) return '#52c41a'
    if (exposure < -0.3) return '#ff4d4f'
    return '#faad14'
  }

  return (
    <div className="space-y-4">
      {/* \u6458\u8981\u6307\u6807 */}
      <Card>
        <Row gutter={24}>
          <Col span={6}>
            <Statistic
              title={'\u603b\u98ce\u9669 (\u5e74\u5316\u6ce2\u52a8\u7387)'}
              value={data.totalRisk * 100}
              precision={2}
              suffix="%"
              valueStyle={{
                color: data.totalRisk > 0.25 ? '#ff4d4f' : data.totalRisk > 0.15 ? '#faad14' : '#52c41a'
              }}
            />
          </Col>
          <Col span={6}>
            <Statistic
              title={
                <Tooltip title={'\u56e0\u5b50\u6a21\u578b\u5bf9\u7ec4\u5408\u6536\u76ca\u7684\u89e3\u91ca\u529b\u5ea6'}>
                  {'R\u00b2 \u89e3\u91ca\u529b\u5ea6'} <InfoCircleOutlined />
                </Tooltip>
              }
              value={data.rSquared * 100}
              precision={1}
              suffix="%"
            />
          </Col>
          <Col span={6}>
            <Statistic
              title={
                <Tooltip title={'\u7ec4\u5408\u4e0e\u57fa\u51c6\u7684\u504f\u79bb\u7a0b\u5ea6'}>
                  {'\u8ddf\u8e2a\u8bef\u5dee'} <InfoCircleOutlined />
                </Tooltip>
              }
              value={data.trackingError * 100}
              precision={2}
              suffix="%"
            />
          </Col>
          <Col span={6}>
            <Statistic
              title={'\u5e02\u573a Beta'}
              value={data.factorExposures.market}
              precision={2}
              valueStyle={{
                color: data.factorExposures.market > 1.2 ? '#ff4d4f' :
                  data.factorExposures.market < 0.8 ? '#1890ff' : '#52c41a'
              }}
            />
          </Col>
        </Row>
      </Card>

      <Row gutter={16}>
        {/* \u98ce\u9669\u6765\u6e90\u5206\u89e3 */}
        <Col span={12}>
          <Card
            title={
              <span>
                <PieChartOutlined className="mr-2" />
                {'\u98ce\u9669\u6765\u6e90\u5206\u89e3'}
              </span>
            }
          >
            <div className="space-y-3">
              {riskSourceData.map((item) => (
                <div key={item.name} className="flex items-center">
                  <div className="w-20 text-sm text-gray-500">{item.name}</div>
                  <div className="flex-1 mx-3">
                    <div
                      className="h-6 rounded"
                      style={{
                        width: `${Math.min(item.value, 100)}%`,
                        backgroundColor: item.color,
                      }}
                    />
                  </div>
                  <div className="w-16 text-right font-medium">
                    {item.value.toFixed(1)}%
                  </div>
                </div>
              ))}
            </div>

            <div className="mt-4 pt-4 border-t border-dark-border">
              <div className="text-sm text-gray-500">
                <InfoCircleOutlined className="mr-1" />
                {'\u98ce\u9669\u8d21\u732e\u603b\u548c\u4e3a 100%\uff0c\u663e\u793a\u5404\u7c7b\u98ce\u9669\u5bf9\u7ec4\u5408\u603b\u98ce\u9669\u7684\u8d21\u732e'}
              </div>
            </div>
          </Card>
        </Col>

        {/* \u98ce\u683c\u56e0\u5b50\u66b4\u9732 */}
        <Col span={12}>
          <Card
            title={
              <span>
                <BarChartOutlined className="mr-2" />
                {'\u98ce\u683c\u56e0\u5b50\u66b4\u9732'}
              </span>
            }
          >
            <div className="space-y-2">
              {styleFactorData.map((item) => (
                <div key={item.factor} className="flex items-center">
                  <div className="w-16 text-sm">{item.label}</div>
                  <div className="flex-1 mx-2 h-4 bg-dark-hover rounded overflow-hidden relative">
                    <div className="absolute inset-y-0 left-1/2 w-px bg-gray-600" />
                    <div
                      className="absolute inset-y-0 h-full transition-all"
                      style={{
                        backgroundColor: getExposureColor(item.exposure),
                        left: item.exposure >= 0 ? '50%' : `${50 + item.exposure * 50}%`,
                        width: `${Math.abs(item.exposure) * 50}%`,
                      }}
                    />
                  </div>
                  <div className="w-12 text-right text-sm" style={{ color: getExposureColor(item.exposure) }}>
                    {item.exposure > 0 ? '+' : ''}{item.exposure.toFixed(2)}
                  </div>
                </div>
              ))}
            </div>

            <div className="mt-4 pt-4 border-t border-dark-border text-sm text-gray-500">
              <span className="text-green-500">{'\u6b63\u503c'}</span>{' = \u8d85\u914d\uff0c'}
              <span className="text-red-500">{'\u8d1f\u503c'}</span>{' = \u4f4e\u914d\uff0c'}
              <span className="text-yellow-500">{'\u4e2d\u6027'}</span>{' = \u8fd1\u4f3c\u5e02\u573a'}
            </div>
          </Card>
        </Col>
      </Row>

      {/* \u884c\u4e1a\u66b4\u9732\u8868\u683c */}
      <Card
        title={'\u884c\u4e1a\u56e0\u5b50\u66b4\u9732'}
      >
        <Table
          dataSource={industryData}
          rowKey="industry"
          pagination={false}
          size="small"
          columns={[
            {
              title: '\u884c\u4e1a',
              dataIndex: 'label',
              key: 'label',
            },
            {
              title: '\u66b4\u9732\u7cfb\u6570',
              dataIndex: 'exposure',
              key: 'exposure',
              align: 'right',
              render: (value: number) => (
                <span style={{ color: getExposureColor(value) }}>
                  {value > 0 ? '+' : ''}{value.toFixed(3)}
                </span>
              ),
            },
            {
              title: '\u98ce\u9669\u8d21\u732e',
              dataIndex: 'riskContrib',
              key: 'riskContrib',
              align: 'right',
              render: (value: number) => `${value.toFixed(1)}%`,
            },
            {
              title: '\u72b6\u6001',
              key: 'status',
              align: 'center',
              render: (_, record) => {
                const absExposure = Math.abs(record.exposure)
                if (absExposure > 0.2) {
                  return <Tag color="red">{'\u8d85\u914d'}</Tag>
                } else if (absExposure > 0.1) {
                  return <Tag color="orange">{'\u504f\u79bb'}</Tag>
                }
                return <Tag color="green">{'\u6b63\u5e38'}</Tag>
              },
            },
          ]}
        />
      </Card>
    </div>
  )
}
