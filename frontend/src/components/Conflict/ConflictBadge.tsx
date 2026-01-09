/**
 * 冲突提示角标组件
 * PRD 4.6 策略冲突检测
 */
import { Badge, Tooltip } from 'antd'
import { WarningOutlined } from '@ant-design/icons'
import { SEVERITY_CONFIG, ConflictSeverity } from '../../types/conflict'

interface ConflictBadgeProps {
  total: number
  critical: number
  warning: number
  onClick?: () => void
}

export default function ConflictBadge({
  total,
  critical,
  warning,
  onClick,
}: ConflictBadgeProps) {
  if (total === 0) return null

  // 确定显示颜色: 有严重冲突显示红色，有警告显示黄色
  const badgeColor = critical > 0 ? '#ef4444' : warning > 0 ? '#f59e0b' : '#3b82f6'

  return (
    <Tooltip
      title={
        <div className="text-sm">
          <div className="font-medium mb-1">待处理冲突: {total}</div>
          {critical > 0 && (
            <div className="flex items-center gap-1 text-red-400">
              <span className="w-2 h-2 rounded-full bg-red-400" />
              严重: {critical}
            </div>
          )}
          {warning > 0 && (
            <div className="flex items-center gap-1 text-yellow-400">
              <span className="w-2 h-2 rounded-full bg-yellow-400" />
              警告: {warning}
            </div>
          )}
        </div>
      }
    >
      <div
        className={`relative cursor-pointer p-2 rounded-lg hover:bg-gray-700/50 transition-colors ${
          critical > 0 ? 'animate-pulse' : ''
        }`}
        onClick={onClick}
      >
        <Badge count={total} size="small" color={badgeColor}>
          <WarningOutlined
            className="text-xl"
            style={{ color: badgeColor }}
          />
        </Badge>
      </div>
    </Tooltip>
  )
}

// 冲突状态标签
interface ConflictStatusTagProps {
  severity: ConflictSeverity
  count: number
}

export function ConflictStatusTag({ severity, count }: ConflictStatusTagProps) {
  const config = SEVERITY_CONFIG[severity]

  if (count === 0) return null

  return (
    <div
      className={`flex items-center gap-1 px-2 py-1 rounded text-xs ${config.bgColor}`}
      style={{ color: config.color }}
    >
      <WarningOutlined />
      <span>{count} {config.label}</span>
    </div>
  )
}

// 紧凑型冲突指示器
interface ConflictIndicatorProps {
  hasConflicts: boolean
  criticalCount: number
  onClick?: () => void
}

export function ConflictIndicator({
  hasConflicts,
  criticalCount,
  onClick,
}: ConflictIndicatorProps) {
  if (!hasConflicts) return null

  return (
    <Tooltip title={criticalCount > 0 ? `${criticalCount}个严重冲突待处理` : '有冲突待处理'}>
      <div
        className={`w-3 h-3 rounded-full cursor-pointer ${
          criticalCount > 0 ? 'bg-red-500 animate-pulse' : 'bg-yellow-500'
        }`}
        onClick={onClick}
      />
    </Tooltip>
  )
}
