/**
 * Phase 13: \u5f52\u56e0\u4e0e\u62a5\u8868 - Brinson \u5f52\u56e0\u56fe\u8868
 */

import React, { useMemo } from 'react'
import { Row, Col, Table, Typography, Tooltip, Progress } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { Card } from '@/components/ui'
import type { BrinsonAttribution, SectorAttribution } from '@/types/attribution'
import { SECTOR_LABELS } from '@/types/attribution'

const { Text, Title } = Typography

interface BrinsonChartProps {
  data: BrinsonAttribution
  loading?: boolean
}

/**
 * Brinson \u5f52\u56e0\u56fe\u8868\u7ec4\u4ef6
 *
 * \u5c55\u793a:
 * - \u6536\u76ca\u6982\u89c8
 * - \u6548\u5e94\u5206\u89e3 (\u914d\u7f6e/\u9009\u80a1/\u4ea4\u4e92)
 * - \u884c\u4e1a\u660e\u7ec6\u8868\u683c
 */
const BrinsonChart: React.FC<BrinsonChartProps> = ({ data, loading }) => {
  // \u6548\u5e94\u5206\u89e3\u6570\u636e
  const effectsData = useMemo(() => [
    {
      name: '\u914d\u7f6e\u6548\u5e94',
      value: data.totalAllocationEffect,
      color: '#1890ff',
      description: '\u884c\u4e1a\u914d\u7f6e\u51b3\u7b56\u7684\u8d21\u732e',
    },
    {
      name: '\u9009\u80a1\u6548\u5e94',
      value: data.totalSelectionEffect,
      color: '#52c41a',
      description: '\u884c\u4e1a\u5185\u80a1\u7968\u9009\u62e9\u7684\u8d21\u732e',
    },
    {
      name: '\u4ea4\u4e92\u6548\u5e94',
      value: data.totalInteractionEffect,
      color: '#faad14',
      description: '\u914d\u7f6e\u4e0e\u9009\u80a1\u7684\u4ea4\u4e92\u4f5c\u7528',
    },
  ], [data])

  // \u884c\u4e1a\u660e\u7ec6\u8868\u683c\u5217
  const columns: ColumnsType<SectorAttribution> = [
    {
      title: '\u884c\u4e1a',
      dataIndex: 'sectorName',
      key: 'sector',
      width: 120,
      render: (name: string, record: SectorAttribution) => (
        <Tooltip title={SECTOR_LABELS[record.sector] || record.sector}>
          <Text strong>{name}</Text>
        </Tooltip>
      ),
    },
    {
      title: '\u7ec4\u5408\u6743\u91cd',
      dataIndex: 'portfolioWeight',
      key: 'portfolioWeight',
      width: 100,
      align: 'right',
      render: (v: number) => `${(v * 100).toFixed(1)}%`,
    },
    {
      title: '\u57fa\u51c6\u6743\u91cd',
      dataIndex: 'benchmarkWeight',
      key: 'benchmarkWeight',
      width: 100,
      align: 'right',
      render: (v: number) => `${(v * 100).toFixed(1)}%`,
    },
    {
      title: '\u4e3b\u52a8\u6743\u91cd',
      dataIndex: 'activeWeight',
      key: 'activeWeight',
      width: 100,
      align: 'right',
      render: (v: number) => (
        <Text type={v >= 0 ? 'success' : 'danger'}>
          {v >= 0 ? '+' : ''}{(v * 100).toFixed(1)}%
        </Text>
      ),
    },
    {
      title: '\u914d\u7f6e\u6548\u5e94',
      dataIndex: 'allocationEffect',
      key: 'allocationEffect',
      width: 100,
      align: 'right',
      render: (v: number) => (
        <Text type={v >= 0 ? 'success' : 'danger'}>
          {v >= 0 ? '+' : ''}{(v * 100).toFixed(2)}%
        </Text>
      ),
    },
    {
      title: '\u9009\u80a1\u6548\u5e94',
      dataIndex: 'selectionEffect',
      key: 'selectionEffect',
      width: 100,
      align: 'right',
      render: (v: number) => (
        <Text type={v >= 0 ? 'success' : 'danger'}>
          {v >= 0 ? '+' : ''}{(v * 100).toFixed(2)}%
        </Text>
      ),
    },
    {
      title: '\u603b\u6548\u5e94',
      dataIndex: 'totalEffect',
      key: 'totalEffect',
      width: 100,
      align: 'right',
      render: (v: number) => (
        <Text strong type={v >= 0 ? 'success' : 'danger'}>
          {v >= 0 ? '+' : ''}{(v * 100).toFixed(2)}%
        </Text>
      ),
    },
  ]

  // \u6309\u603b\u6548\u5e94\u6392\u5e8f
  const sortedSectorDetails = useMemo(() =>
    [...data.sectorDetails].sort((a, b) => Math.abs(b.totalEffect) - Math.abs(a.totalEffect)),
    [data.sectorDetails]
  )

  return (
    <div className="brinson-chart">
      {/* \u6536\u76ca\u6982\u89c8 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={8}>
          <Card size="small">
            <Text type="secondary">\u7ec4\u5408\u6536\u76ca</Text>
            <Title level={3} style={{ margin: '8px 0 0' }}>
              {(data.portfolioReturn * 100).toFixed(2)}%
            </Title>
          </Card>
        </Col>
        <Col span={8}>
          <Card size="small">
            <Text type="secondary">\u57fa\u51c6\u6536\u76ca</Text>
            <Title level={3} style={{ margin: '8px 0 0' }}>
              {(data.benchmarkReturn * 100).toFixed(2)}%
            </Title>
          </Card>
        </Col>
        <Col span={8}>
          <Card size="small">
            <Text type="secondary">\u8d85\u989d\u6536\u76ca</Text>
            <Title
              level={3}
              type={data.excessReturn >= 0 ? 'success' : 'danger'}
              style={{ margin: '8px 0 0' }}
            >
              {data.excessReturn >= 0 ? '+' : ''}{(data.excessReturn * 100).toFixed(2)}%
            </Title>
          </Card>
        </Col>
      </Row>

      {/* \u6548\u5e94\u5206\u89e3 */}
      <Card title="Brinson \u6548\u5e94\u5206\u89e3" size="small" style={{ marginBottom: 24 }}>
        <Row gutter={24}>
          {effectsData.map((effect) => (
            <Col span={8} key={effect.name}>
              <div style={{ marginBottom: 16 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                  <Tooltip title={effect.description}>
                    <Text>{effect.name}</Text>
                  </Tooltip>
                  <Text
                    strong
                    type={effect.value >= 0 ? 'success' : 'danger'}
                  >
                    {effect.value >= 0 ? '+' : ''}{(effect.value * 100).toFixed(2)}%
                  </Text>
                </div>
                <Progress
                  percent={Math.min(Math.abs(effect.value * 100) * 10, 100)}
                  strokeColor={effect.value >= 0 ? effect.color : '#ff4d4f'}
                  showInfo={false}
                  size="small"
                />
              </div>
            </Col>
          ))}
        </Row>

        {/* \u89e3\u8bfb */}
        {data.interpretation && (
          <div style={{ marginTop: 16, padding: 12, background: '#f5f5f5', borderRadius: 4 }}>
            <Text type="secondary">{data.interpretation}</Text>
          </div>
        )}
      </Card>

      {/* \u884c\u4e1a\u660e\u7ec6 */}
      <Card title="\u884c\u4e1a\u5f52\u56e0\u660e\u7ec6" size="small">
        <Table
          columns={columns}
          dataSource={sortedSectorDetails}
          rowKey="sector"
          loading={loading}
          pagination={false}
          size="small"
          scroll={{ x: 800 }}
        />
      </Card>
    </div>
  )
}

export default BrinsonChart
