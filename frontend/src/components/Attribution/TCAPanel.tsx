/**
 * Phase 13: \u5f52\u56e0\u4e0e\u62a5\u8868 - TCA \u5206\u6790\u9762\u677f
 */

import React, { useMemo } from 'react'
import { Row, Col, Table, Typography, Tag, Statistic, Tabs } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { Card } from '@/components/ui'
import type { StrategyTCA, TradeTCA, TradeCostBreakdown } from '@/types/attribution'

const { Text } = Typography

interface TCAPanelProps {
  data: StrategyTCA
  loading?: boolean
}

/**
 * TCA \u5206\u6790\u9762\u677f\u7ec4\u4ef6
 *
 * \u5c55\u793a:
 * - \u6210\u672c\u6c47\u603b
 * - \u6210\u672c\u5206\u89e3
 * - \u6309\u65f6\u6bb5/\u80a1\u7968\u5206\u7ec4
 * - \u4ea4\u6613\u660e\u7ec6
 */
const TCAPanel: React.FC<TCAPanelProps> = ({ data, loading }) => {
  // \u6210\u672c\u5206\u89e3\u6570\u636e
  const costBreakdown = useMemo(() => {
    const costs = data.totalCosts
    const total = costs.totalCost || 1
    return [
      { name: '\u4f63\u91d1', value: costs.commission, percent: costs.commission / total * 100, color: '#1890ff' },
      { name: '\u6ed1\u70b9', value: costs.slippage, percent: costs.slippage / total * 100, color: '#52c41a' },
      { name: '\u5e02\u573a\u51b2\u51fb', value: costs.marketImpact, percent: costs.marketImpact / total * 100, color: '#faad14' },
      { name: '\u65f6\u673a\u6210\u672c', value: costs.timingCost, percent: costs.timingCost / total * 100, color: '#eb2f96' },
      { name: '\u673a\u4f1a\u6210\u672c', value: costs.opportunityCost, percent: costs.opportunityCost / total * 100, color: '#722ed1' },
    ]
  }, [data.totalCosts])

  // \u4ea4\u6613\u8868\u683c\u5217
  const tradeColumns: ColumnsType<TradeTCA> = [
    {
      title: '\u4ea4\u6613ID',
      dataIndex: 'tradeId',
      key: 'tradeId',
      width: 100,
      render: (id: string) => <Text code>{id}</Text>,
    },
    {
      title: '\u80a1\u7968',
      dataIndex: 'symbol',
      key: 'symbol',
      width: 80,
      render: (symbol: string) => <Tag color="blue">{symbol}</Tag>,
    },
    {
      title: '\u65b9\u5411',
      dataIndex: 'side',
      key: 'side',
      width: 60,
      render: (side: string) => (
        <Tag color={side === 'buy' ? 'green' : 'red'}>
          {side === 'buy' ? '\u4e70\u5165' : '\u5356\u51fa'}
        </Tag>
      ),
    },
    {
      title: '\u6570\u91cf',
      dataIndex: 'quantity',
      key: 'quantity',
      width: 80,
      align: 'right',
      render: (v: number) => v.toLocaleString(),
    },
    {
      title: '\u51b3\u7b56\u4ef7',
      dataIndex: 'decisionPrice',
      key: 'decisionPrice',
      width: 90,
      align: 'right',
      render: (v: number) => `$${v.toFixed(2)}`,
    },
    {
      title: '\u6267\u884c\u4ef7',
      dataIndex: 'executionPrice',
      key: 'executionPrice',
      width: 90,
      align: 'right',
      render: (v: number) => `$${v.toFixed(2)}`,
    },
    {
      title: '\u6267\u884c\u7f3a\u53e3',
      dataIndex: 'implementationShortfallBps',
      key: 'shortfall',
      width: 100,
      align: 'right',
      render: (v: number) => (
        <Text type={v > 5 ? 'danger' : v > 2 ? 'warning' : 'success'}>
          {v.toFixed(1)} bps
        </Text>
      ),
    },
    {
      title: '\u603b\u6210\u672c',
      key: 'totalCost',
      width: 90,
      align: 'right',
      render: (_, record: TradeTCA) => `$${record.costs.totalCost.toFixed(2)}`,
    },
    {
      title: '\u6267\u884c\u65f6\u957f',
      dataIndex: 'executionDuration',
      key: 'duration',
      width: 90,
      align: 'right',
      render: (v: number) => {
        if (v < 60) return `${v.toFixed(0)}\u79d2`
        return `${(v / 60).toFixed(1)}\u5206`
      },
    },
  ]

  // \u6309\u65f6\u6bb5\u8868\u683c\u5217
  const timeColumns: ColumnsType<{ period: string; avgCostBps: number; trades: number }> = [
    {
      title: '\u65f6\u6bb5',
      dataIndex: 'period',
      key: 'period',
    },
    {
      title: '\u5e73\u5747\u6210\u672c',
      dataIndex: 'avgCostBps',
      key: 'avgCostBps',
      align: 'right',
      render: (v: number) => `${v.toFixed(2)} bps`,
    },
    {
      title: '\u4ea4\u6613\u6570',
      dataIndex: 'trades',
      key: 'trades',
      align: 'right',
    },
  ]

  // \u6309\u80a1\u7968\u8868\u683c\u5217
  const symbolColumns: ColumnsType<{ symbol: string; avgCostBps: number; trades: number; totalNotional: number }> = [
    {
      title: '\u80a1\u7968',
      dataIndex: 'symbol',
      key: 'symbol',
      render: (symbol: string) => <Tag color="blue">{symbol}</Tag>,
    },
    {
      title: '\u5e73\u5747\u6210\u672c',
      dataIndex: 'avgCostBps',
      key: 'avgCostBps',
      align: 'right',
      render: (v: number) => `${v.toFixed(2)} bps`,
    },
    {
      title: '\u4ea4\u6613\u6570',
      dataIndex: 'trades',
      key: 'trades',
      align: 'right',
    },
    {
      title: '\u4ea4\u6613\u989d',
      dataIndex: 'totalNotional',
      key: 'totalNotional',
      align: 'right',
      render: (v: number) => `$${(v / 1000).toFixed(0)}K`,
    },
  ]

  // \u6210\u672c\u5361\u7247\u7ec4\u4ef6
  const CostCard: React.FC<{ title: string; costs: TradeCostBreakdown | null }> = ({ title, costs }) => {
    if (!costs) return null
    return (
      <Card size="small" title={title}>
        <Row gutter={8}>
          <Col span={12}>
            <Statistic title="\u4f63\u91d1" value={costs.commission} precision={2} prefix="$" />
          </Col>
          <Col span={12}>
            <Statistic title="\u6ed1\u70b9" value={costs.slippage} precision={2} prefix="$" />
          </Col>
          <Col span={12}>
            <Statistic title="\u5e02\u573a\u51b2\u51fb" value={costs.marketImpact} precision={2} prefix="$" />
          </Col>
          <Col span={12}>
            <Statistic title="\u603b\u6210\u672c" value={costs.totalCost} precision={2} prefix="$" valueStyle={{ color: '#cf1322' }} />
          </Col>
        </Row>
      </Card>
    )
  }

  const tabItems = [
    {
      key: 'trades',
      label: '\u4ea4\u6613\u660e\u7ec6',
      children: (
        <Table
          columns={tradeColumns}
          dataSource={data.trades.slice(0, 50)}
          rowKey="tradeId"
          loading={loading}
          pagination={{ pageSize: 10 }}
          size="small"
          scroll={{ x: 900 }}
        />
      ),
    },
    {
      key: 'byTime',
      label: '\u6309\u65f6\u6bb5',
      children: (
        <Table
          columns={timeColumns}
          dataSource={data.byTimeOfDay}
          rowKey="period"
          loading={loading}
          pagination={false}
          size="small"
        />
      ),
    },
    {
      key: 'bySymbol',
      label: '\u6309\u80a1\u7968',
      children: (
        <Table
          columns={symbolColumns}
          dataSource={data.bySymbol}
          rowKey="symbol"
          loading={loading}
          pagination={false}
          size="small"
        />
      ),
    },
  ]

  return (
    <div className="tca-panel">
      {/* \u6c47\u603b\u7edf\u8ba1 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card size="small">
            <Statistic
              title="\u603b\u4ea4\u6613\u6570"
              value={data.totalTrades}
              suffix="\u7b14"
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small">
            <Statistic
              title="\u603b\u4ea4\u6613\u989d"
              value={data.totalNotional}
              precision={0}
              prefix="$"
              formatter={(value) => `${(Number(value) / 1000000).toFixed(2)}M`}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small">
            <Statistic
              title="\u603b\u6210\u672c"
              value={data.totalCosts.totalCost}
              precision={2}
              prefix="$"
              valueStyle={{ color: '#cf1322' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small">
            <Statistic
              title="\u5e73\u5747\u6210\u672c"
              value={data.avgCostBps}
              precision={2}
              suffix=" bps"
              valueStyle={{
                color: data.avgCostBps > 5 ? '#cf1322' :
                       data.avgCostBps > 2 ? '#faad14' : '#3f8600'
              }}
            />
          </Card>
        </Col>
      </Row>

      {/* \u6210\u672c\u5206\u89e3 */}
      <Card title="\u6210\u672c\u5206\u89e3" size="small" style={{ marginBottom: 24 }}>
        <Row gutter={16}>
          {costBreakdown.map((item) => (
            <Col span={4} key={item.name}>
              <div style={{ textAlign: 'center' }}>
                <div style={{ marginBottom: 8 }}>
                  <Text type="secondary">{item.name}</Text>
                </div>
                <div style={{ fontSize: 20, fontWeight: 'bold', color: item.color }}>
                  ${item.value.toFixed(0)}
                </div>
                <div style={{ fontSize: 12, color: '#999' }}>
                  {item.percent.toFixed(1)}%
                </div>
              </div>
            </Col>
          ))}
          <Col span={4}>
            <div style={{ textAlign: 'center' }}>
              <div style={{ marginBottom: 8 }}>
                <Text strong>\u603b\u8ba1</Text>
              </div>
              <div style={{ fontSize: 20, fontWeight: 'bold', color: '#cf1322' }}>
                ${data.totalCosts.totalCost.toFixed(0)}
              </div>
              <div style={{ fontSize: 12, color: '#999' }}>
                100%
              </div>
            </div>
          </Col>
        </Row>
      </Card>

      {/* \u4e70\u5356\u65b9\u5411\u5bf9\u6bd4 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={12}>
          <CostCard title="\u4e70\u5165\u6210\u672c" costs={data.buyCosts} />
        </Col>
        <Col span={12}>
          <CostCard title="\u5356\u51fa\u6210\u672c" costs={data.sellCosts} />
        </Col>
      </Row>

      {/* \u57fa\u51c6\u5bf9\u6bd4 */}
      <Card title="\u57fa\u51c6\u5bf9\u6bd4" size="small" style={{ marginBottom: 24 }}>
        <Row gutter={24}>
          <Col span={8}>
            <Statistic
              title="vs VWAP"
              value={data.vsBenchmark.vwapSlippage}
              precision={2}
              suffix=" bps"
              valueStyle={{ color: data.vsBenchmark.vwapSlippage > 0 ? '#cf1322' : '#3f8600' }}
            />
          </Col>
          <Col span={8}>
            <Statistic
              title="vs TWAP"
              value={data.vsBenchmark.twapSlippage}
              precision={2}
              suffix=" bps"
              valueStyle={{ color: data.vsBenchmark.twapSlippage > 0 ? '#cf1322' : '#3f8600' }}
            />
          </Col>
          <Col span={8}>
            <Statistic
              title="vs Arrival"
              value={data.vsBenchmark.arrivalSlippage}
              precision={2}
              suffix=" bps"
              valueStyle={{ color: data.vsBenchmark.arrivalSlippage > 0 ? '#cf1322' : '#3f8600' }}
            />
          </Col>
        </Row>
      </Card>

      {/* \u660e\u7ec6\u9009\u9879\u5361 */}
      <Card size="small">
        <Tabs items={tabItems} />
      </Card>
    </div>
  )
}

export default TCAPanel
