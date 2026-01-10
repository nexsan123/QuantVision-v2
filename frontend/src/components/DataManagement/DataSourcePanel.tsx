/**
 * Phase 11: \u6570\u636e\u5c42\u5347\u7ea7 - \u6570\u636e\u6e90\u7ba1\u7406\u9762\u677f
 *
 * \u663e\u793a:
 * - \u6570\u636e\u6e90\u72b6\u6001
 * - \u540c\u6b65\u8fdb\u5ea6
 * - \u6570\u636e\u8d28\u91cf\u6307\u6807
 */

import { useState, useEffect, useCallback } from 'react'
import {
  Row, Col, Table, Tag, Button, Progress, Statistic, message
} from 'antd'
import {
  CloudServerOutlined, SyncOutlined, CheckCircleOutlined,
  ExclamationCircleOutlined, ClockCircleOutlined, DatabaseOutlined
} from '@ant-design/icons'
import { Card } from '@/components/ui'
import {
  DataSource, DataSourceStatus, DataFrequency,
  DATA_SOURCE_LABELS, FREQUENCY_LABELS
} from '@/types/marketData'

interface DataSourceInfo {
  source: DataSource
  status: DataSourceStatus
  lastSync: string | null
  requestsToday: number
  requestsLimit: number
  latencyMs: number
  errorMessage?: string
}

interface SyncStatus {
  symbol: string
  lastSyncTime: string | null
  totalBars: number
  frequency: DataFrequency
  status: 'synced' | 'syncing' | 'error' | 'stale'
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || ''

export default function DataSourcePanel() {
  const [sources, setSources] = useState<DataSourceInfo[]>([])
  const [syncStatuses, setSyncStatuses] = useState<SyncStatus[]>([])
  const [loading, setLoading] = useState(true)
  const [syncing, setSyncing] = useState(false)

  const fetchSources = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/market-data/sources`)
      if (response.ok) {
        const data = await response.json()
        setSources(data.sources)
      }
    } catch (err) {
      console.error('\u52a0\u8f7d\u6570\u636e\u6e90\u5931\u8d25:', err)
    }
  }, [])

  const fetchSyncStatus = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/market-data/sync/status`)
      if (response.ok) {
        const data = await response.json()
        setSyncStatuses(data.symbols)
      }
    } catch (err) {
      console.error('\u52a0\u8f7d\u540c\u6b65\u72b6\u6001\u5931\u8d25:', err)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchSources()
    fetchSyncStatus()
    const interval = setInterval(() => {
      fetchSources()
      fetchSyncStatus()
    }, 30000)
    return () => clearInterval(interval)
  }, [fetchSources, fetchSyncStatus])

  const handleSync = async (symbols: string[], frequency: DataFrequency) => {
    setSyncing(true)
    try {
      const today = new Date().toISOString().split('T')[0]
      const oneYearAgo = new Date(Date.now() - 365 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]

      const response = await fetch(
        `${API_BASE_URL}/api/v1/market-data/sync?` +
        `start_date=${oneYearAgo}&end_date=${today}&frequency=${frequency}`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(symbols)
        }
      )

      if (response.ok) {
        const result = await response.json()
        message.success(`\u540c\u6b65\u5b8c\u6210: ${result.success_count} \u6210\u529f, ${result.failed_count} \u5931\u8d25`)
        fetchSyncStatus()
      } else {
        throw new Error('\u540c\u6b65\u5931\u8d25')
      }
    } catch (err: any) {
      message.error(err.message)
    } finally {
      setSyncing(false)
    }
  }

  const getStatusTag = (status: DataSourceStatus) => {
    switch (status) {
      case 'connected':
        return <Tag color="green"><CheckCircleOutlined /> {'\u5df2\u8fde\u63a5'}</Tag>
      case 'disconnected':
        return <Tag color="default">{'\u672a\u8fde\u63a5'}</Tag>
      case 'error':
        return <Tag color="red"><ExclamationCircleOutlined /> {'\u9519\u8bef'}</Tag>
      case 'rate_limited':
        return <Tag color="orange"><ClockCircleOutlined /> {'\u9650\u6d41'}</Tag>
    }
  }

  const getSyncStatusTag = (status: string) => {
    switch (status) {
      case 'synced':
        return <Tag color="green">{'\u5df2\u540c\u6b65'}</Tag>
      case 'syncing':
        return <Tag color="blue"><SyncOutlined spin /> {'\u540c\u6b65\u4e2d'}</Tag>
      case 'error':
        return <Tag color="red">{'\u9519\u8bef'}</Tag>
      case 'stale':
        return <Tag color="orange">{'\u8fc7\u65f6'}</Tag>
      default:
        return <Tag>{status}</Tag>
    }
  }

  return (
    <div className="space-y-4">
      {/* \u6570\u636e\u6e90\u72b6\u6001 */}
      <Card
        title={
          <span>
            <CloudServerOutlined className="mr-2" />
            {'\u6570\u636e\u6e90\u72b6\u6001'}
          </span>
        }
      >
        <Row gutter={24}>
          {sources.map((source) => (
            <Col span={6} key={source.source}>
              <Card className="bg-dark-hover">
                <div className="flex justify-between items-start mb-2">
                  <span className="font-medium">{DATA_SOURCE_LABELS[source.source]}</span>
                  {getStatusTag(source.status)}
                </div>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between text-gray-500">
                    <span>{'\u5ef6\u8fdf'}</span>
                    <span>{source.latencyMs.toFixed(0)}ms</span>
                  </div>
                  <div className="flex justify-between text-gray-500">
                    <span>{'\u4eca\u65e5\u8bf7\u6c42'}</span>
                    <span>{source.requestsToday} / {source.requestsLimit}</span>
                  </div>
                  <Progress
                    percent={(source.requestsToday / source.requestsLimit) * 100}
                    showInfo={false}
                    strokeColor={{
                      '0%': '#52c41a',
                      '80%': '#faad14',
                      '100%': '#ff4d4f',
                    }}
                    size="small"
                  />
                </div>
              </Card>
            </Col>
          ))}
        </Row>
      </Card>

      {/* \u540c\u6b65\u7edf\u8ba1 */}
      <Row gutter={16}>
        <Col span={6}>
          <Card>
            <Statistic
              title={'\u5df2\u540c\u6b65\u80a1\u7968'}
              value={syncStatuses.filter(s => s.status === 'synced').length}
              suffix={`/ ${syncStatuses.length}`}
              prefix={<DatabaseOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title={'\u540c\u6b65\u4e2d'}
              value={syncStatuses.filter(s => s.status === 'syncing').length}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title={'\u540c\u6b65\u9519\u8bef'}
              value={syncStatuses.filter(s => s.status === 'error').length}
              valueStyle={{ color: '#ff4d4f' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title={'\u603b K \u7ebf\u6570'}
              value={syncStatuses.reduce((sum, s) => sum + s.totalBars, 0)}
              suffix={'\u6761'}
            />
          </Card>
        </Col>
      </Row>

      {/* \u540c\u6b65\u5217\u8868 */}
      <Card
        title={'\u6570\u636e\u540c\u6b65\u72b6\u6001'}
        extra={
          <Button
            type="primary"
            icon={<SyncOutlined spin={syncing} />}
            onClick={() => handleSync(['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META'], '1day')}
            loading={syncing}
          >
            {'\u540c\u6b65\u6837\u672c\u6570\u636e'}
          </Button>
        }
      >
        <Table
          dataSource={syncStatuses}
          rowKey="symbol"
          loading={loading}
          pagination={{ pageSize: 10 }}
          columns={[
            {
              title: '\u80a1\u7968',
              dataIndex: 'symbol',
              key: 'symbol',
              sorter: (a, b) => a.symbol.localeCompare(b.symbol),
            },
            {
              title: '\u9891\u7387',
              dataIndex: 'frequency',
              key: 'frequency',
              render: (freq: DataFrequency) => FREQUENCY_LABELS[freq] || freq,
            },
            {
              title: '\u72b6\u6001',
              dataIndex: 'status',
              key: 'status',
              render: getSyncStatusTag,
              filters: [
                { text: '\u5df2\u540c\u6b65', value: 'synced' },
                { text: '\u540c\u6b65\u4e2d', value: 'syncing' },
                { text: '\u9519\u8bef', value: 'error' },
                { text: '\u8fc7\u65f6', value: 'stale' },
              ],
              onFilter: (value, record) => record.status === value,
            },
            {
              title: 'K\u7ebf\u6570',
              dataIndex: 'totalBars',
              key: 'totalBars',
              sorter: (a, b) => a.totalBars - b.totalBars,
              render: (val: number) => val.toLocaleString(),
            },
            {
              title: '\u6700\u540e\u540c\u6b65',
              dataIndex: 'lastSyncTime',
              key: 'lastSyncTime',
              render: (time: string | null) => time ? new Date(time).toLocaleString() : '-',
            },
          ]}
        />
      </Card>
    </div>
  )
}
