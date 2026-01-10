/**
 * 预警通知铃铛组件
 * PRD 4.14
 */
import { useState } from 'react'
import { Badge, Dropdown, Empty, Spin, Button } from 'antd'
import { BellOutlined, CheckOutlined } from '@ant-design/icons'
import {
  RiskAlert,
  ALERT_SEVERITY_CONFIG,
  ALERT_TYPE_CONFIG,
  formatAlertTime,
} from '../../types/alert'

interface AlertBellProps {
  alerts: RiskAlert[]
  unreadCount: number
  loading?: boolean
  onMarkRead?: (alertId: string) => void
  onMarkAllRead?: () => void
  onViewAll?: () => void
}

export default function AlertBell({
  alerts,
  unreadCount,
  loading = false,
  onMarkRead,
  onMarkAllRead,
  onViewAll,
}: AlertBellProps) {
  const [open, setOpen] = useState(false)

  // 渲染单个预警项
  const renderAlertItem = (alert: RiskAlert) => {
    const severityConfig = ALERT_SEVERITY_CONFIG[alert.severity]
    const typeConfig = ALERT_TYPE_CONFIG[alert.alertType]

    return (
      <div
        key={alert.alertId}
        className={`p-3 border-b border-gray-700 last:border-b-0 hover:bg-dark-hover transition-colors cursor-pointer ${
          !alert.isRead ? 'bg-blue-500/5' : ''
        }`}
        onClick={() => onMarkRead?.(alert.alertId)}
      >
        <div className="flex items-start gap-3">
          {/* 图标 */}
          <div
            className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0"
            style={{ backgroundColor: `${severityConfig.color}20` }}
          >
            <span className="text-sm">{typeConfig.icon}</span>
          </div>

          {/* 内容 */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <span className="font-medium text-white text-sm truncate">
                {alert.title}
              </span>
              {!alert.isRead && (
                <span className="w-2 h-2 rounded-full bg-blue-500 flex-shrink-0" />
              )}
            </div>
            <p className="text-gray-400 text-xs line-clamp-2">{alert.message}</p>
            <div className="flex items-center gap-2 mt-1">
              <span
                className="text-xs px-1.5 py-0.5 rounded"
                style={{
                  backgroundColor: `${severityConfig.color}20`,
                  color: severityConfig.color,
                }}
              >
                {typeConfig.label}
              </span>
              <span className="text-gray-500 text-xs">
                {formatAlertTime(alert.createdAt)}
              </span>
            </div>
          </div>
        </div>
      </div>
    )
  }

  // 下拉内容
  const dropdownContent = (
    <div className="bg-dark-card border border-gray-700 rounded-lg shadow-xl w-80 max-h-96 overflow-hidden">
      {/* 头部 */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-700">
        <div className="flex items-center gap-2">
          <span className="font-medium text-white">通知</span>
          {unreadCount > 0 && (
            <Badge count={unreadCount} size="small" />
          )}
        </div>
        {unreadCount > 0 && onMarkAllRead && (
          <Button
            type="text"
            size="small"
            icon={<CheckOutlined />}
            onClick={(e) => {
              e.stopPropagation()
              onMarkAllRead()
            }}
            className="text-gray-400 hover:text-white"
          >
            全部已读
          </Button>
        )}
      </div>

      {/* 预警列表 */}
      <div className="overflow-y-auto max-h-72">
        {loading ? (
          <div className="flex items-center justify-center py-8">
            <Spin />
          </div>
        ) : alerts.length > 0 ? (
          alerts.slice(0, 10).map(renderAlertItem)
        ) : (
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description="暂无通知"
            className="py-8"
          />
        )}
      </div>

      {/* 底部 */}
      {alerts.length > 0 && onViewAll && (
        <div className="border-t border-gray-700 px-4 py-2">
          <Button
            type="link"
            block
            onClick={() => {
              setOpen(false)
              onViewAll()
            }}
            className="text-blue-400"
          >
            查看全部通知
          </Button>
        </div>
      )}
    </div>
  )

  return (
    <Dropdown
      open={open}
      onOpenChange={setOpen}
      dropdownRender={() => dropdownContent}
      trigger={['click']}
      placement="bottomRight"
    >
      <div className="relative cursor-pointer p-2 rounded-lg hover:bg-dark-hover transition-colors">
        <Badge count={unreadCount} size="small" offset={[-2, 2]}>
          <BellOutlined className="text-xl text-gray-400 hover:text-white transition-colors" />
        </Badge>
      </div>
    </Dropdown>
  )
}
