/**
 * Phase 13: \u5f52\u56e0\u4e0e\u62a5\u8868 - \u7efc\u5408\u5f52\u56e0\u62a5\u544a\u7ec4\u4ef6
 */

import React, { useState, useCallback } from 'react'
import {
  Row, Col, DatePicker, Select, Button, Tabs, Space, Typography, message, Spin
} from 'antd'
import {
  DownloadOutlined, FileExcelOutlined, FilePdfOutlined, ReloadOutlined
} from '@ant-design/icons'
import dayjs from 'dayjs'
import type { Dayjs } from 'dayjs'
import { Card } from '@/components/ui'
import BrinsonChart from './BrinsonChart'
import FactorChart from './FactorChart'
import TCAPanel from './TCAPanel'
import type {
  ComprehensiveAttribution,
  AttributionReportType,
  ReportFormat,
  TimePeriod,
} from '@/types/attribution'
import { DEFAULT_PERIOD } from '@/types/attribution'

const { RangePicker } = DatePicker
const { Title, Text } = Typography

interface AttributionReportProps {
  portfolioId?: string
  portfolioName?: string
  onExport?: (format: ReportFormat) => void
}

/**
 * \u7efc\u5408\u5f52\u56e0\u62a5\u544a\u7ec4\u4ef6
 *
 * \u529f\u80fd:
 * - \u65f6\u95f4\u6bb5\u9009\u62e9
 * - \u62a5\u544a\u7c7b\u578b\u5207\u6362 (Brinson/\u56e0\u5b50/TCA/\u7efc\u5408)
 * - \u62a5\u8868\u5bfc\u51fa (PDF/Excel/JSON)
 * - \u6570\u636e\u5237\u65b0
 */
const AttributionReport: React.FC<AttributionReportProps> = ({
  portfolioId = 'demo-portfolio',
  portfolioName = '\u6f14\u793a\u7ec4\u5408',
  onExport,
}) => {
  // \u72b6\u6001
  const [loading, setLoading] = useState(false)
  const [reportType, setReportType] = useState<AttributionReportType>('comprehensive')
  const [period, setPeriod] = useState<TimePeriod>(DEFAULT_PERIOD)
  const [data, setData] = useState<ComprehensiveAttribution | null>(null)

  // \u52a0\u8f7d\u6570\u636e
  const loadData = useCallback(async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams({
        benchmark_id: 'SPY',
        start_date: period.start,
        end_date: period.end,
        include_brinson: 'true',
        include_factor: 'true',
        include_tca: 'true',
      })

      const response = await fetch(
        `/api/v1/attribution/comprehensive/${portfolioId}?${params}`
      )

      if (!response.ok) {
        throw new Error('\u52a0\u8f7d\u5931\u8d25')
      }

      const result = await response.json()
      if (result.success) {
        setData(result.data)
      } else {
        throw new Error(result.error || '\u52a0\u8f7d\u5931\u8d25')
      }
    } catch (error) {
      message.error(`\u52a0\u8f7d\u5f52\u56e0\u6570\u636e\u5931\u8d25: ${error}`)
      // \u4f7f\u7528\u6a21\u62df\u6570\u636e
      setData(generateMockData())
    } finally {
      setLoading(false)
    }
  }, [portfolioId, period])

  // \u5bfc\u51fa\u62a5\u8868
  const handleExport = useCallback(async (format: ReportFormat) => {
    if (onExport) {
      onExport(format)
      return
    }

    try {
      const response = await fetch('/api/v1/attribution/export', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          report_type: reportType,
          portfolio_id: portfolioId,
          start_date: period.start,
          end_date: period.end,
          format,
          include_charts: true,
          language: 'zh',
        }),
      })

      if (!response.ok) {
        throw new Error('\u5bfc\u51fa\u5931\u8d25')
      }

      // \u4e0b\u8f7d\u6587\u4ef6
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `attribution_report_${portfolioId}.${format}`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      window.URL.revokeObjectURL(url)

      message.success('\u62a5\u8868\u5bfc\u51fa\u6210\u529f')
    } catch (error) {
      message.error(`\u5bfc\u51fa\u5931\u8d25: ${error}`)
    }
  }, [reportType, portfolioId, period, onExport])

  // \u65e5\u671f\u8303\u56f4\u53d8\u5316
  const handleDateChange = useCallback((dates: [Dayjs | null, Dayjs | null] | null) => {
    if (dates && dates[0] && dates[1]) {
      setPeriod({
        start: dates[0].format('YYYY-MM-DD'),
        end: dates[1].format('YYYY-MM-DD'),
      })
    }
  }, [])

  // \u751f\u6210\u6a21\u62df\u6570\u636e
  const generateMockData = (): ComprehensiveAttribution => {
    return {
      period,
      portfolioId,
      portfolioName,
      benchmarkId: 'SPY',
      benchmarkName: 'S&P 500',
      summary: {
        portfolioReturn: 0.156,
        benchmarkReturn: 0.124,
        excessReturn: 0.032,
        informationRatio: 0.85,
        trackingError: 0.038,
        sharpeRatio: 1.24,
        maxDrawdown: -0.12,
      },
      brinson: {
        period,
        portfolioReturn: 0.156,
        benchmarkReturn: 0.124,
        excessReturn: 0.032,
        totalAllocationEffect: 0.012,
        totalSelectionEffect: 0.018,
        totalInteractionEffect: 0.002,
        sectorDetails: [
          {
            sector: 'technology',
            sectorName: '\u79d1\u6280',
            portfolioWeight: 0.32,
            benchmarkWeight: 0.28,
            activeWeight: 0.04,
            portfolioReturn: 0.22,
            benchmarkReturn: 0.18,
            activeReturn: 0.04,
            allocationEffect: 0.008,
            selectionEffect: 0.011,
            interactionEffect: 0.002,
            totalEffect: 0.021,
          },
          {
            sector: 'healthcare',
            sectorName: '\u533b\u7597\u4fdd\u5065',
            portfolioWeight: 0.15,
            benchmarkWeight: 0.13,
            activeWeight: 0.02,
            portfolioReturn: 0.12,
            benchmarkReturn: 0.10,
            activeReturn: 0.02,
            allocationEffect: 0.002,
            selectionEffect: 0.003,
            interactionEffect: 0.001,
            totalEffect: 0.006,
          },
          {
            sector: 'financials',
            sectorName: '\u91d1\u878d',
            portfolioWeight: 0.10,
            benchmarkWeight: 0.12,
            activeWeight: -0.02,
            portfolioReturn: 0.08,
            benchmarkReturn: 0.09,
            activeReturn: -0.01,
            allocationEffect: 0.001,
            selectionEffect: -0.001,
            interactionEffect: 0.000,
            totalEffect: 0.000,
          },
        ],
        interpretation: '\u7ec4\u5408\u6536\u76ca 15.6%\uff0c\u57fa\u51c6\u6536\u76ca 12.4%\uff0c\u8d85\u989d\u6536\u76ca +3.2%\u3002\u9009\u80a1\u6548\u5e94(1.8%)\u8d21\u732e\u8f83\u5927\uff0c\u8d21\u732e\u6700\u5927\u7684\u884c\u4e1a\u662f\u79d1\u6280(2.1%)\u3002',
      },
      factor: {
        period,
        totalReturn: 0.156,
        benchmarkReturn: 0.124,
        activeReturn: 0.032,
        factorContributions: [
          { factor: 'market', factorName: '\u5e02\u573a', exposure: 1.05, factorReturn: 0.08, contribution: 0.084, tStat: 8.5 },
          { factor: 'size', factorName: '\u89c4\u6a21', exposure: 0.25, factorReturn: 0.02, contribution: 0.005, tStat: 2.1 },
          { factor: 'value', factorName: '\u4ef7\u503c', exposure: -0.15, factorReturn: 0.03, contribution: -0.0045, tStat: -1.8 },
          { factor: 'momentum', factorName: '\u52a8\u91cf', exposure: 0.35, factorReturn: 0.04, contribution: 0.014, tStat: 3.2 },
          { factor: 'quality', factorName: '\u8d28\u91cf', exposure: 0.20, factorReturn: 0.02, contribution: 0.004, tStat: 1.5 },
        ],
        totalFactorReturn: 0.103,
        specificReturn: 0.053,
        informationRatio: 0.85,
        trackingError: 0.038,
        activeRisk: 0.156,
        interpretation: '\u7ec4\u5408\u603b\u6536\u76ca 15.6%\uff0c\u5176\u4e2d\u56e0\u5b50\u8d21\u732e 10.3%\uff0c\u7279\u8d28\u6536\u76ca(\u9009\u80a1\u80fd\u529b) 5.3%\u3002\u8d21\u732e\u6700\u5927\u7684\u56e0\u5b50\u662f\u5e02\u573a(\u66b4\u97321.05\uff0c\u8d21\u732e8.4%)\u3002',
      },
      tca: {
        period,
        totalTrades: 50,
        totalVolume: 25000,
        totalNotional: 4500000,
        totalCosts: {
          commission: 225,
          slippage: 450,
          marketImpact: 180,
          timingCost: 90,
          opportunityCost: 45,
          totalCost: 990,
        },
        avgCostBps: 2.2,
        buyCosts: {
          commission: 120,
          slippage: 250,
          marketImpact: 100,
          timingCost: 50,
          opportunityCost: 25,
          totalCost: 545,
        },
        sellCosts: {
          commission: 105,
          slippage: 200,
          marketImpact: 80,
          timingCost: 40,
          opportunityCost: 20,
          totalCost: 445,
        },
        byTimeOfDay: [
          { period: '09:30-10:00', avgCostBps: 3.5, trades: 8 },
          { period: '10:00-11:00', avgCostBps: 2.1, trades: 12 },
          { period: '11:00-12:00', avgCostBps: 1.8, trades: 10 },
          { period: '14:00-15:00', avgCostBps: 2.0, trades: 12 },
          { period: '15:00-16:00', avgCostBps: 2.8, trades: 8 },
        ],
        bySymbol: [
          { symbol: 'AAPL', avgCostBps: 1.8, trades: 12, totalNotional: 1200000 },
          { symbol: 'MSFT', avgCostBps: 2.0, trades: 10, totalNotional: 1000000 },
          { symbol: 'GOOGL', avgCostBps: 2.5, trades: 8, totalNotional: 800000 },
          { symbol: 'AMZN', avgCostBps: 2.2, trades: 12, totalNotional: 900000 },
          { symbol: 'NVDA', avgCostBps: 3.0, trades: 8, totalNotional: 600000 },
        ],
        vsBenchmark: {
          vwapSlippage: 1.5,
          twapSlippage: 1.2,
          arrivalSlippage: 2.0,
        },
        trades: [],
      },
      timeSeries: {
        dates: [],
        portfolioValues: [],
        benchmarkValues: [],
        excessReturns: [],
        drawdowns: [],
      },
      generatedAt: new Date().toISOString(),
    }
  }

  // \u521d\u59cb\u52a0\u8f7d
  React.useEffect(() => {
    loadData()
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  // Tabs \u5185\u5bb9
  const tabItems = [
    {
      key: 'comprehensive',
      label: '\u7efc\u5408\u62a5\u544a',
      children: data ? (
        <div>
          {/* \u6458\u8981\u5361\u7247 */}
          <Card title="\u6536\u76ca\u6458\u8981" size="small" style={{ marginBottom: 24 }}>
            <Row gutter={16}>
              <Col span={4}>
                <div style={{ textAlign: 'center' }}>
                  <Text type="secondary">\u7ec4\u5408\u6536\u76ca</Text>
                  <Title level={4} style={{ margin: '8px 0 0' }}>
                    {(data.summary.portfolioReturn * 100).toFixed(2)}%
                  </Title>
                </div>
              </Col>
              <Col span={4}>
                <div style={{ textAlign: 'center' }}>
                  <Text type="secondary">\u57fa\u51c6\u6536\u76ca</Text>
                  <Title level={4} style={{ margin: '8px 0 0' }}>
                    {(data.summary.benchmarkReturn * 100).toFixed(2)}%
                  </Title>
                </div>
              </Col>
              <Col span={4}>
                <div style={{ textAlign: 'center' }}>
                  <Text type="secondary">\u8d85\u989d\u6536\u76ca</Text>
                  <Title
                    level={4}
                    type={data.summary.excessReturn >= 0 ? 'success' : 'danger'}
                    style={{ margin: '8px 0 0' }}
                  >
                    {data.summary.excessReturn >= 0 ? '+' : ''}
                    {(data.summary.excessReturn * 100).toFixed(2)}%
                  </Title>
                </div>
              </Col>
              <Col span={4}>
                <div style={{ textAlign: 'center' }}>
                  <Text type="secondary">\u4fe1\u606f\u6bd4\u7387</Text>
                  <Title level={4} style={{ margin: '8px 0 0' }}>
                    {data.summary.informationRatio.toFixed(2)}
                  </Title>
                </div>
              </Col>
              <Col span={4}>
                <div style={{ textAlign: 'center' }}>
                  <Text type="secondary">\u590f\u666e\u6bd4\u7387</Text>
                  <Title level={4} style={{ margin: '8px 0 0' }}>
                    {data.summary.sharpeRatio.toFixed(2)}
                  </Title>
                </div>
              </Col>
              <Col span={4}>
                <div style={{ textAlign: 'center' }}>
                  <Text type="secondary">\u6700\u5927\u56de\u64a4</Text>
                  <Title level={4} type="danger" style={{ margin: '8px 0 0' }}>
                    {(data.summary.maxDrawdown * 100).toFixed(2)}%
                  </Title>
                </div>
              </Col>
            </Row>
          </Card>

          {/* Brinson \u7b80\u8981 */}
          {data.brinson && (
            <Card title="Brinson \u5f52\u56e0\u7b80\u8981" size="small" style={{ marginBottom: 24 }}>
              <Row gutter={24}>
                <Col span={8}>
                  <Text type="secondary">\u914d\u7f6e\u6548\u5e94</Text>
                  <Title level={4} type={data.brinson.totalAllocationEffect >= 0 ? 'success' : 'danger'}>
                    {data.brinson.totalAllocationEffect >= 0 ? '+' : ''}
                    {(data.brinson.totalAllocationEffect * 100).toFixed(2)}%
                  </Title>
                </Col>
                <Col span={8}>
                  <Text type="secondary">\u9009\u80a1\u6548\u5e94</Text>
                  <Title level={4} type={data.brinson.totalSelectionEffect >= 0 ? 'success' : 'danger'}>
                    {data.brinson.totalSelectionEffect >= 0 ? '+' : ''}
                    {(data.brinson.totalSelectionEffect * 100).toFixed(2)}%
                  </Title>
                </Col>
                <Col span={8}>
                  <Text type="secondary">\u4ea4\u4e92\u6548\u5e94</Text>
                  <Title level={4} type={data.brinson.totalInteractionEffect >= 0 ? 'success' : 'danger'}>
                    {data.brinson.totalInteractionEffect >= 0 ? '+' : ''}
                    {(data.brinson.totalInteractionEffect * 100).toFixed(2)}%
                  </Title>
                </Col>
              </Row>
            </Card>
          )}

          {/* \u56e0\u5b50\u7b80\u8981 */}
          {data.factor && (
            <Card title="\u56e0\u5b50\u5f52\u56e0\u7b80\u8981" size="small" style={{ marginBottom: 24 }}>
              <Row gutter={24}>
                <Col span={8}>
                  <Text type="secondary">\u56e0\u5b50\u6536\u76ca</Text>
                  <Title level={4}>
                    {(data.factor.totalFactorReturn * 100).toFixed(2)}%
                  </Title>
                </Col>
                <Col span={8}>
                  <Text type="secondary">\u7279\u8d28\u6536\u76ca (Alpha)</Text>
                  <Title level={4} type={data.factor.specificReturn >= 0 ? 'success' : 'danger'}>
                    {data.factor.specificReturn >= 0 ? '+' : ''}
                    {(data.factor.specificReturn * 100).toFixed(2)}%
                  </Title>
                </Col>
                <Col span={8}>
                  <Text type="secondary">\u8ddf\u8e2a\u8bef\u5dee</Text>
                  <Title level={4}>
                    {(data.factor.trackingError * 100).toFixed(2)}%
                  </Title>
                </Col>
              </Row>
            </Card>
          )}

          {/* TCA \u7b80\u8981 */}
          {data.tca && (
            <Card title="TCA \u7b80\u8981" size="small">
              <Row gutter={24}>
                <Col span={6}>
                  <Text type="secondary">\u603b\u4ea4\u6613\u6570</Text>
                  <Title level={4}>{data.tca.totalTrades}</Title>
                </Col>
                <Col span={6}>
                  <Text type="secondary">\u603b\u4ea4\u6613\u989d</Text>
                  <Title level={4}>${(data.tca.totalNotional / 1000000).toFixed(2)}M</Title>
                </Col>
                <Col span={6}>
                  <Text type="secondary">\u603b\u6210\u672c</Text>
                  <Title level={4} type="danger">${data.tca.totalCosts.totalCost.toFixed(0)}</Title>
                </Col>
                <Col span={6}>
                  <Text type="secondary">\u5e73\u5747\u6210\u672c</Text>
                  <Title level={4}>{data.tca.avgCostBps.toFixed(2)} bps</Title>
                </Col>
              </Row>
            </Card>
          )}
        </div>
      ) : null,
    },
    {
      key: 'brinson',
      label: 'Brinson \u5f52\u56e0',
      children: data?.brinson ? (
        <BrinsonChart data={data.brinson} loading={loading} />
      ) : null,
    },
    {
      key: 'factor',
      label: '\u56e0\u5b50\u5f52\u56e0',
      children: data?.factor ? (
        <FactorChart data={data.factor} loading={loading} />
      ) : null,
    },
    {
      key: 'tca',
      label: 'TCA \u5206\u6790',
      children: data?.tca ? (
        <TCAPanel data={data.tca} loading={loading} />
      ) : null,
    },
  ]

  return (
    <div className="attribution-report">
      {/* \u5de5\u5177\u680f */}
      <Card size="small" style={{ marginBottom: 16 }}>
        <Row justify="space-between" align="middle">
          <Col>
            <Space>
              <RangePicker
                value={[dayjs(period.start), dayjs(period.end)]}
                onChange={handleDateChange}
                format="YYYY-MM-DD"
              />
              <Select
                value={reportType}
                onChange={setReportType}
                style={{ width: 140 }}
                options={[
                  { value: 'comprehensive', label: '\u7efc\u5408\u62a5\u544a' },
                  { value: 'brinson', label: 'Brinson \u5f52\u56e0' },
                  { value: 'factor', label: '\u56e0\u5b50\u5f52\u56e0' },
                  { value: 'tca', label: 'TCA \u5206\u6790' },
                ]}
              />
              <Button
                icon={<ReloadOutlined />}
                onClick={loadData}
                loading={loading}
              >
                \u5237\u65b0
              </Button>
            </Space>
          </Col>
          <Col>
            <Space>
              <Button
                icon={<FilePdfOutlined />}
                onClick={() => handleExport('pdf')}
              >
                \u5bfc\u51fa PDF
              </Button>
              <Button
                icon={<FileExcelOutlined />}
                onClick={() => handleExport('excel')}
              >
                \u5bfc\u51fa Excel
              </Button>
              <Button
                icon={<DownloadOutlined />}
                onClick={() => handleExport('json')}
              >
                \u5bfc\u51fa JSON
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* \u62a5\u544a\u5185\u5bb9 */}
      <Spin spinning={loading}>
        <Tabs
          activeKey={reportType}
          onChange={(key) => setReportType(key as AttributionReportType)}
          items={tabItems}
        />
      </Spin>
    </div>
  )
}

export default AttributionReport
