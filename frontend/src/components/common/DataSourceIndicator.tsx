/**
 * 数据源状态指示器
 *
 * 显示API数据源连接状态:
 * - 绿色: 真实数据 (Alpaca Live/Paper)
 * - 黄色: 降级到Mock数据
 * - 红色: 连接失败
 */

import { memo, useState, useEffect } from 'react'
import { Badge, Tooltip, Space, Tag, Popover, Button, Typography, Divider } from 'antd'
import {
  ApiOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  CloseCircleOutlined,
  ReloadOutlined,
  CloudServerOutlined,
  DatabaseOutlined,
  RobotOutlined,
} from '@ant-design/icons'

const { Text } = Typography

// ==================== 类型定义 ====================

export type DataSourceType = 'alpaca_live' | 'alpaca_paper' | 'polygon' | 'mock'

export interface DataSourceStatus {
  source: DataSourceType
  is_mock: boolean
  is_connected: boolean
  error_message?: string | null
  last_check: string
}

export interface DataSourcesState {
  account?: DataSourceStatus
  positions?: DataSourceStatus
  strategies?: DataSourceStatus
  pdt?: DataSourceStatus
  signals?: DataSourceStatus
  trades?: DataSourceStatus
  market_data?: DataSourceStatus
  overall_status?: 'connected' | 'degraded' | 'disconnected'
  connected_services?: number
  total_services?: number
}

// ==================== 配置 ====================

const sourceLabels: Record<DataSourceType, string> = {
  alpaca_live: 'Alpaca Live',
  alpaca_paper: 'Alpaca Paper',
  polygon: 'Polygon',
  mock: 'Mock Data',
}

const sourceIcons: Record<string, React.ReactNode> = {
  account: <DatabaseOutlined />,
  positions: <ApiOutlined />,
  strategies: <RobotOutlined />,
  pdt: <ExclamationCircleOutlined />,
  signals: <CloudServerOutlined />,
  trades: <DatabaseOutlined />,
  market_data: <CloudServerOutlined />,
}

// ==================== 单个数据源状态 ====================

interface SingleSourceStatusProps {
  name: string
  label: string
  status?: DataSourceStatus
}

function SingleSourceStatus({ name, label, status }: SingleSourceStatusProps) {
  if (!status) {
    return (
      <div className="flex items-center justify-between py-1">
        <Space size={4}>
          {sourceIcons[name] || <ApiOutlined />}
          <Text>{label}</Text>
        </Space>
        <Tag color="default">未知</Tag>
      </div>
    )
  }

  const getStatusTag = () => {
    if (status.is_mock) {
      return (
        <Tag color="warning" icon={<ExclamationCircleOutlined />}>
          Mock
        </Tag>
      )
    }
    if (status.is_connected) {
      return (
        <Tag color="success" icon={<CheckCircleOutlined />}>
          {sourceLabels[status.source]}
        </Tag>
      )
    }
    return (
      <Tag color="error" icon={<CloseCircleOutlined />}>
        断开
      </Tag>
    )
  }

  return (
    <div className="py-1">
      <div className="flex items-center justify-between">
        <Space size={4}>
          {sourceIcons[name] || <ApiOutlined />}
          <Text>{label}</Text>
        </Space>
        {getStatusTag()}
      </div>
      {status.error_message && (
        <Text type="secondary" className="text-xs block mt-1 pl-5">
          {status.error_message}
        </Text>
      )}
    </div>
  )
}

// ==================== 详细面板 ====================

interface DataSourceDetailPanelProps {
  sources: DataSourcesState
  onRefresh?: () => void
}

function DataSourceDetailPanel({ sources, onRefresh }: DataSourceDetailPanelProps) {
  const mockCount = Object.values(sources).filter(
    s => s && typeof s === 'object' && 'is_mock' in s && s.is_mock
  ).length
  const totalCount = Object.keys(sources).filter(k => k !== 'overall_status').length

  return (
    <div style={{ minWidth: 280 }}>
      <div className="flex items-center justify-between mb-3">
        <Text strong>数据源状态</Text>
        {onRefresh && (
          <Button
            type="text"
            size="small"
            icon={<ReloadOutlined />}
            onClick={onRefresh}
          >
            刷新
          </Button>
        )}
      </div>

      {mockCount > 0 && (
        <div
          className="mb-3 p-2 rounded"
          style={{ background: 'rgba(250, 173, 20, 0.1)', border: '1px solid rgba(250, 173, 20, 0.3)' }}
        >
          <Text type="warning" className="text-xs">
            <ExclamationCircleOutlined className="mr-1" />
            {mockCount}/{totalCount} 个数据源使用模拟数据
          </Text>
        </div>
      )}

      <div className="space-y-1">
        <SingleSourceStatus name="account" label="账户信息" status={sources.account} />
        <SingleSourceStatus name="positions" label="持仓数据" status={sources.positions} />
        <SingleSourceStatus name="strategies" label="策略部署" status={sources.strategies} />
        <SingleSourceStatus name="pdt" label="PDT规则" status={sources.pdt} />
        <SingleSourceStatus name="signals" label="信号雷达" status={sources.signals} />
        <SingleSourceStatus name="trades" label="交易记录" status={sources.trades} />
        {sources.market_data && (
          <SingleSourceStatus name="market_data" label="行情数据" status={sources.market_data} />
        )}
      </div>

      <Divider style={{ margin: '12px 0' }} />

      <div className="flex items-center justify-between">
        <Text type="secondary" className="text-xs">
          总体状态 ({sources.connected_services || 0}/{sources.total_services || 0})
        </Text>
        <Tag
          color={
            sources.overall_status === 'connected' ? 'success' :
            sources.overall_status === 'degraded' ? 'warning' : 'error'
          }
        >
          {sources.overall_status === 'connected' ? '正常' :
           sources.overall_status === 'degraded' ? '降级' : '断开'}
        </Tag>
      </div>
    </div>
  )
}

// ==================== 主组件 ====================

interface DataSourceIndicatorProps {
  sources: DataSourcesState
  onRefresh?: () => void
  showLabel?: boolean
  size?: 'small' | 'default'
}

function DataSourceIndicatorComponent({
  sources,
  onRefresh,
  showLabel = true,
  size = 'default',
}: DataSourceIndicatorProps) {
  // 计算总体状态
  const hasMock = Object.values(sources).some(
    s => s && typeof s === 'object' && 'is_mock' in s && s.is_mock
  )
  const hasError = Object.values(sources).some(
    s => s && typeof s === 'object' && 'is_connected' in s && !s.is_connected && !s.is_mock
  )

  const overallStatus = hasError ? 'error' : hasMock ? 'warning' : 'success'

  const getStatusConfig = () => {
    switch (overallStatus) {
      case 'success':
        return {
          color: '#52c41a',
          badge: 'success' as const,
          label: '实时数据',
          icon: <CheckCircleOutlined />,
        }
      case 'warning':
        return {
          color: '#faad14',
          badge: 'warning' as const,
          label: 'Mock模式',
          icon: <ExclamationCircleOutlined />,
        }
      case 'error':
        return {
          color: '#ff4d4f',
          badge: 'error' as const,
          label: '连接失败',
          icon: <CloseCircleOutlined />,
        }
    }
  }

  const config = getStatusConfig()

  return (
    <Popover
      content={<DataSourceDetailPanel sources={sources} onRefresh={onRefresh} />}
      trigger="click"
      placement="bottomRight"
    >
      <div
        className="cursor-pointer flex items-center gap-1 px-2 py-1 rounded transition-colors hover:bg-white/5"
        style={{ minHeight: size === 'small' ? 24 : 32 }}
      >
        <Badge status={config.badge} />
        <span style={{ color: config.color, fontSize: size === 'small' ? 12 : 14 }}>
          {config.icon}
        </span>
        {showLabel && (
          <span
            className="text-gray-400"
            style={{ fontSize: size === 'small' ? 11 : 12 }}
          >
            {config.label}
          </span>
        )}
      </div>
    </Popover>
  )
}

// ==================== 简化指示器 (仅图标) ====================

interface SimpleDataSourceBadgeProps {
  isMock: boolean
  source?: DataSourceType
  tooltip?: string
}

export function SimpleDataSourceBadge({ isMock, source, tooltip }: SimpleDataSourceBadgeProps) {
  const content = (
    <Space size={4}>
      <Badge status={isMock ? 'warning' : 'success'} />
      <span style={{ color: isMock ? '#faad14' : '#52c41a', fontSize: 12 }}>
        {isMock ? <ExclamationCircleOutlined /> : <CheckCircleOutlined />}
      </span>
      <span className="text-xs text-gray-400">
        {isMock ? 'Mock' : sourceLabels[source || 'mock']}
      </span>
    </Space>
  )

  if (tooltip) {
    return <Tooltip title={tooltip}>{content}</Tooltip>
  }
  return content
}

// ==================== Hook: 获取数据源状态 ====================

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export function useDataSourceStatus() {
  const [sources, setSources] = useState<DataSourcesState>({})
  const [loading, setLoading] = useState(false)

  const fetchStatus = async () => {
    setLoading(true)
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/account/data-sources`)
      if (response.ok) {
        const data = await response.json()
        setSources(data)
      }
    } catch (error) {
      console.error('Failed to fetch data source status:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchStatus()
    // 每30秒检查一次
    const interval = setInterval(fetchStatus, 30000)
    return () => clearInterval(interval)
  }, [])

  return { sources, loading, refresh: fetchStatus }
}

export const DataSourceIndicator = memo(DataSourceIndicatorComponent)
export default DataSourceIndicator
