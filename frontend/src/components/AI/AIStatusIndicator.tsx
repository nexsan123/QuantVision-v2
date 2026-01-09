/**
 * AI 状态指示器组件
 * PRD 4.2
 */
import { useState } from 'react'
import { Tooltip, Button, Dropdown, MenuProps, Spin } from 'antd'
import { SyncOutlined, ExclamationCircleOutlined } from '@ant-design/icons'
import {
  AIConnectionStatus,
  AI_STATUS_CONFIG,
  formatLatency,
} from '../../types/ai'

interface AIStatusIndicatorProps {
  status: AIConnectionStatus
  onReconnect?: () => Promise<void>
  compact?: boolean
}

export default function AIStatusIndicator({
  status,
  onReconnect,
  compact = false,
}: AIStatusIndicatorProps) {
  const [reconnecting, setReconnecting] = useState(false)
  const config = AI_STATUS_CONFIG[status.status]

  const handleReconnect = async () => {
    if (!onReconnect || !status.canReconnect) return
    setReconnecting(true)
    try {
      await onReconnect()
    } finally {
      setReconnecting(false)
    }
  }

  // 下拉菜单内容
  const menuItems: MenuProps['items'] = [
    {
      key: 'status',
      label: (
        <div className="py-2">
          <div className="flex items-center gap-2 mb-2">
            <span style={{ color: config.color }}>{config.icon}</span>
            <span className="text-white font-medium">{config.text}</span>
          </div>
          <div className="text-gray-500 text-xs space-y-1">
            <div>模型: {status.modelName}</div>
            {status.latencyMs !== undefined && (
              <div>延迟: {formatLatency(status.latencyMs)}</div>
            )}
            {status.lastHeartbeat && (
              <div>
                最后心跳: {new Date(status.lastHeartbeat).toLocaleTimeString()}
              </div>
            )}
          </div>
        </div>
      ),
      disabled: true,
    },
    { type: 'divider' },
    {
      key: 'reconnect',
      label: (
        <div className="flex items-center gap-2">
          <SyncOutlined spin={reconnecting} />
          <span>{reconnecting ? '重连中...' : '重新连接'}</span>
        </div>
      ),
      disabled: !status.canReconnect || reconnecting || status.isConnected,
      onClick: handleReconnect,
    },
  ]

  // 紧凑模式 (仅图标)
  if (compact) {
    return (
      <Tooltip title={config.text}>
        <div
          className="flex items-center justify-center w-8 h-8 rounded-full cursor-pointer hover:bg-dark-hover transition-colors"
          style={{ backgroundColor: `${config.color}20` }}
        >
          <span className="text-sm">{config.icon}</span>
        </div>
      </Tooltip>
    )
  }

  return (
    <Dropdown menu={{ items: menuItems }} trigger={['click']} placement="bottomRight">
      <div
        className={`flex items-center gap-2 px-3 py-1.5 rounded-lg cursor-pointer hover:opacity-80 transition-opacity ${config.bgColor}`}
      >
        {status.status === 'connecting' ? (
          <Spin size="small" />
        ) : (
          <span>{config.icon}</span>
        )}
        <span className="text-sm" style={{ color: config.color }}>
          {config.text}
        </span>
        {status.isConnected && status.latencyMs !== undefined && (
          <span className="text-gray-500 text-xs">
            ({formatLatency(status.latencyMs)})
          </span>
        )}
        {status.errorMessage && (
          <Tooltip title={status.errorMessage}>
            <ExclamationCircleOutlined className="text-red-400" />
          </Tooltip>
        )}
      </div>
    </Dropdown>
  )
}
