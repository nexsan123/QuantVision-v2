/**
 * Phase 13: \u5f52\u56e0\u4e0e\u62a5\u8868 - \u56e0\u5b50\u5f52\u56e0\u56fe\u8868
 */

import React, { useMemo } from 'react'
import { Row, Col, Table, Typography, Tag, Progress, Statistic } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { Card } from '@/components/ui'
import type { FactorAttribution, FactorExposure } from '@/types/attribution'
import { FACTOR_LABELS } from '@/types/attribution'

const { Text, Title } = Typography

interface FactorChartProps {
  data: FactorAttribution
  loading?: boolean
}

/**
 * \u56e0\u5b50\u5f52\u56e0\u56fe\u8868\u7ec4\u4ef6
 *
 * \u5c55\u793a:
 * - \u6536\u76ca\u5206\u89e3 (\u56e0\u5b50\u6536\u76ca vs \u7279\u8d28\u6536\u76ca)
 * - \u56e0\u5b50\u66b4\u9732\u548c\u8d21\u732e
 * - \u98ce\u9669\u6307\u6807
 */
const FactorChart: React.FC<FactorChartProps> = ({ data, loading }) => {
  // \u56e0\u5b50\u8868\u683c\u5217
  const columns: ColumnsType<FactorExposure> = [
    {
      title: '\u56e0\u5b50',
      dataIndex: 'factorName',
      key: 'factor',
      width: 100,
      render: (name: string, record: FactorExposure) => (
        <Tag color="blue">{FACTOR_LABELS[record.factor] || name}</Tag>
      ),
    },
    {
      title: '\u66b4\u9732',
      dataIndex: 'exposure',
      key: 'exposure',
      width: 120,
      align: 'right',
      render: (v: number) => (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end' }}>
          <Progress
            percent={Math.min(Math.abs(v) * 50, 100)}
            strokeColor={v >= 0 ? '#1890ff' : '#ff4d4f'}
            showInfo={false}
            size="small"
            style={{ width: 60, marginRight: 8 }}
          />
          <Text type={v >= 0 ? undefined : 'danger'}>
            {v >= 0 ? '+' : ''}{v.toFixed(2)}
          </Text>
        </div>
      ),
    },
    {
      title: '\u56e0\u5b50\u6536\u76ca',
      dataIndex: 'factorReturn',
      key: 'factorReturn',
      width: 100,
      align: 'right',
      render: (v: number) => (
        <Text type={v >= 0 ? 'success' : 'danger'}>
          {v >= 0 ? '+' : ''}{(v * 100).toFixed(2)}%
        </Text>
      ),
    },
    {
      title: '\u8d21\u732e',
      dataIndex: 'contribution',
      key: 'contribution',
      width: 120,
      align: 'right',
      render: (v: number) => (
        <Text strong type={v >= 0 ? 'success' : 'danger'}>
          {v >= 0 ? '+' : ''}{(v * 100).toFixed(2)}%
        </Text>
      ),
    },
    {
      title: 't\u7edf\u8ba1\u91cf',
      dataIndex: 'tStat',
      key: 'tStat',
      width: 100,
      align: 'right',
      render: (v: number) => {
        const isSignificant = Math.abs(v) >= 2
        return (
          <Text type={isSignificant ? 'success' : 'secondary'}>
            {v.toFixed(2)}
            {isSignificant && ' *'}
          </Text>
        )
      },
    },
    {
      title: '\u663e\u8457\u6027',
      key: 'significance',
      width: 80,
      align: 'center',
      render: (_, record: FactorExposure) => {
        const t = Math.abs(record.tStat)
        if (t >= 2.58) return <Tag color="green">***</Tag>
        if (t >= 1.96) return <Tag color="blue">**</Tag>
        if (t >= 1.65) return <Tag color="orange">*</Tag>
        return <Tag>-</Tag>
      },
    },
  ]

  // \u6309\u8d21\u732e\u6392\u5e8f
  const sortedContributions = useMemo(() =>
    [...data.factorContributions].sort((a, b) => Math.abs(b.contribution) - Math.abs(a.contribution)),
    [data.factorContributions]
  )

  // \u8ba1\u7b97\u56e0\u5b50\u6536\u76ca\u5360\u6bd4
  const factorRatio = useMemo(() => {
    if (data.totalReturn === 0) return 0
    return Math.abs(data.totalFactorReturn / data.totalReturn) * 100
  }, [data])

  return (
    <div className="factor-chart">
      {/* \u6536\u76ca\u5206\u89e3 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card size="small">
            <Statistic
              title="\u603b\u6536\u76ca"
              value={data.totalReturn * 100}
              precision={2}
              suffix="%"
              valueStyle={{ color: data.totalReturn >= 0 ? '#3f8600' : '#cf1322' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small">
            <Statistic
              title="\u56e0\u5b50\u6536\u76ca"
              value={data.totalFactorReturn * 100}
              precision={2}
              suffix="%"
              valueStyle={{ color: data.totalFactorReturn >= 0 ? '#1890ff' : '#cf1322' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small">
            <Statistic
              title="\u7279\u8d28\u6536\u76ca (\u03b1)"
              value={data.specificReturn * 100}
              precision={2}
              suffix="%"
              valueStyle={{ color: data.specificReturn >= 0 ? '#52c41a' : '#cf1322' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small">
            <Statistic
              title="\u8d85\u989d\u6536\u76ca"
              value={data.activeReturn * 100}
              precision={2}
              suffix="%"
              valueStyle={{ color: data.activeReturn >= 0 ? '#722ed1' : '#cf1322' }}
            />
          </Card>
        </Col>
      </Row>

      {/* \u6536\u76ca\u6765\u6e90\u5206\u89e3 */}
      <Card title="\u6536\u76ca\u6765\u6e90\u5206\u89e3" size="small" style={{ marginBottom: 24 }}>
        <Row gutter={24} align="middle">
          <Col span={12}>
            <div style={{ textAlign: 'center' }}>
              <Progress
                type="circle"
                percent={Math.min(factorRatio, 100)}
                format={() => (
                  <div>
                    <div style={{ fontSize: 24, fontWeight: 'bold' }}>
                      {factorRatio.toFixed(0)}%
                    </div>
                    <div style={{ fontSize: 12, color: '#999' }}>\u56e0\u5b50\u89e3\u91ca</div>
                  </div>
                )}
                strokeColor={{
                  '0%': '#108ee9',
                  '100%': '#87d068',
                }}
                size={150}
              />
            </div>
          </Col>
          <Col span={12}>
            <div style={{ marginBottom: 16 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                <Text>\u56e0\u5b50\u6536\u76ca</Text>
                <Text strong>{(data.totalFactorReturn * 100).toFixed(2)}%</Text>
              </div>
              <Progress
                percent={Math.abs(data.totalFactorReturn * 100 * 5)}
                strokeColor="#1890ff"
                showInfo={false}
              />
            </div>
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                <Text>\u7279\u8d28\u6536\u76ca (\u9009\u80a1\u80fd\u529b)</Text>
                <Text strong>{(data.specificReturn * 100).toFixed(2)}%</Text>
              </div>
              <Progress
                percent={Math.abs(data.specificReturn * 100 * 5)}
                strokeColor="#52c41a"
                showInfo={false}
              />
            </div>
          </Col>
        </Row>

        {/* \u89e3\u8bfb */}
        {data.interpretation && (
          <div style={{ marginTop: 16, padding: 12, background: '#f5f5f5', borderRadius: 4 }}>
            <Text type="secondary">{data.interpretation}</Text>
          </div>
        )}
      </Card>

      {/* \u98ce\u9669\u6307\u6807 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={8}>
          <Card size="small">
            <Statistic
              title="\u4fe1\u606f\u6bd4\u7387 (IR)"
              value={data.informationRatio}
              precision={2}
              valueStyle={{
                color: data.informationRatio >= 0.5 ? '#3f8600' :
                       data.informationRatio >= 0 ? '#faad14' : '#cf1322'
              }}
            />
            <Text type="secondary" style={{ fontSize: 12 }}>
              {data.informationRatio >= 1 ? '\u4f18\u79c0' :
               data.informationRatio >= 0.5 ? '\u826f\u597d' :
               data.informationRatio >= 0 ? '\u4e00\u822c' : '\u8f83\u5dee'}
            </Text>
          </Card>
        </Col>
        <Col span={8}>
          <Card size="small">
            <Statistic
              title="\u8ddf\u8e2a\u8bef\u5dee"
              value={data.trackingError * 100}
              precision={2}
              suffix="%"
            />
            <Text type="secondary" style={{ fontSize: 12 }}>
              \u5e74\u5316\u6807\u51c6\u5dee
            </Text>
          </Card>
        </Col>
        <Col span={8}>
          <Card size="small">
            <Statistic
              title="\u4e3b\u52a8\u98ce\u9669"
              value={data.activeRisk * 100}
              precision={2}
              suffix="%"
            />
            <Text type="secondary" style={{ fontSize: 12 }}>
              \u5e74\u5316\u6ce2\u52a8\u7387
            </Text>
          </Card>
        </Col>
      </Row>

      {/* \u56e0\u5b50\u660e\u7ec6 */}
      <Card title="\u56e0\u5b50\u66b4\u9732\u4e0e\u8d21\u732e" size="small">
        <Table
          columns={columns}
          dataSource={sortedContributions}
          rowKey="factor"
          loading={loading}
          pagination={false}
          size="small"
        />
        <div style={{ marginTop: 12, color: '#999', fontSize: 12 }}>
          * p&lt;0.1, ** p&lt;0.05, *** p&lt;0.01
        </div>
      </Card>
    </div>
  )
}

export default FactorChart
