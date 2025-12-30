/**
 * 连接状态指示器
 *
 * 显示 WebSocket 连接状态
 */

import { memo } from 'react'
import { Badge, Tooltip, Space } from 'antd'
import {
  WifiOutlined,
  DisconnectOutlined,
  LoadingOutlined,
  ExclamationCircleOutlined,
  SyncOutlined,
} from '@ant-design/icons'
import { ConnectionStatus as ConnectionStatusType } from '@/types/trading'

interface ConnectionStatusProps {
  status: ConnectionStatusType
  reconnectAttempts?: number
  lastHeartbeat?: string | null
  showLabel?: boolean
}

const statusConfig: Record<
  ConnectionStatusType,
  {
    icon: React.ReactNode
    color: 'success' | 'processing' | 'default' | 'error' | 'warning'
    label: string
    description: string
  }
> = {
  connected: {
    icon: <WifiOutlined />,
    color: 'success',
    label: '已连接',
    description: '实时数据流连接正常',
  },
  connecting: {
    icon: <LoadingOutlined spin />,
    color: 'processing',
    label: '连接中',
    description: '正在建立连接...',
  },
  disconnected: {
    icon: <DisconnectOutlined />,
    color: 'default',
    label: '未连接',
    description: '未连接到服务器',
  },
  error: {
    icon: <ExclamationCircleOutlined />,
    color: 'error',
    label: '连接错误',
    description: '连接发生错误',
  },
  reconnecting: {
    icon: <SyncOutlined spin />,
    color: 'warning',
    label: '重连中',
    description: '正在尝试重新连接...',
  },
}

function ConnectionStatusComponent({
  status,
  reconnectAttempts = 0,
  lastHeartbeat,
  showLabel = true,
}: ConnectionStatusProps) {
  const config = statusConfig[status]

  const tooltipContent = (
    <div className="text-xs">
      <div>{config.description}</div>
      {status === 'reconnecting' && (
        <div className="mt-1">重连次数: {reconnectAttempts}</div>
      )}
      {lastHeartbeat && (
        <div className="mt-1">
          最后心跳: {new Date(lastHeartbeat).toLocaleTimeString('zh-CN')}
        </div>
      )}
    </div>
  )

  return (
    <Tooltip title={tooltipContent}>
      <Space size={4} className="cursor-default">
        <Badge status={config.color} />
        <span className="text-sm" style={{ color: getStatusColor(config.color) }}>
          {config.icon}
        </span>
        {showLabel && (
          <span className="text-sm text-gray-400">{config.label}</span>
        )}
      </Space>
    </Tooltip>
  )
}

function getStatusColor(status: string): string {
  const colors: Record<string, string> = {
    success: '#52c41a',
    processing: '#1890ff',
    default: '#8c8c8c',
    error: '#ff4d4f',
    warning: '#faad14',
  }
  return colors[status] || colors.default
}

export const ConnectionStatus = memo(ConnectionStatusComponent)
export default ConnectionStatus
