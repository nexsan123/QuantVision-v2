/**
 * 冲突列表组件
 * PRD 4.6 策略冲突检测
 */
import { Tag, Button, Empty } from 'antd'
import {
  ExclamationCircleOutlined,
  ClockCircleOutlined,
  RightOutlined,
} from '@ant-design/icons'
import {
  ConflictDetail,
  CONFLICT_TYPE_CONFIG,
  SEVERITY_CONFIG,
  formatConflictTime,
  getRemainingTime,
} from '../../types/conflict'

interface ConflictListProps {
  conflicts: ConflictDetail[]
  onSelect: (conflict: ConflictDetail) => void
  loading?: boolean
}

export default function ConflictList({
  conflicts,
  onSelect,
  loading = false,
}: ConflictListProps) {
  if (conflicts.length === 0) {
    return (
      <Empty
        image={Empty.PRESENTED_IMAGE_SIMPLE}
        description="暂无待处理冲突"
        className="py-8"
      />
    )
  }

  return (
    <div className="space-y-3">
      {conflicts.map((conflict) => (
        <ConflictListItem
          key={conflict.conflict_id}
          conflict={conflict}
          onClick={() => onSelect(conflict)}
        />
      ))}
    </div>
  )
}

interface ConflictListItemProps {
  conflict: ConflictDetail
  onClick: () => void
}

function ConflictListItem({ conflict, onClick }: ConflictListItemProps) {
  const typeConfig = CONFLICT_TYPE_CONFIG[conflict.conflict_type]
  const severityConfig = SEVERITY_CONFIG[conflict.severity]

  return (
    <div
      className={`p-4 rounded-lg border cursor-pointer transition-all hover:border-gray-600 ${
        conflict.severity === 'critical'
          ? 'border-red-500/30 bg-red-500/5'
          : conflict.severity === 'warning'
          ? 'border-yellow-500/30 bg-yellow-500/5'
          : 'border-gray-700 bg-dark-card'
      }`}
      onClick={onClick}
    >
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-3">
          {/* 图标 */}
          <span className="text-2xl">{typeConfig.icon}</span>

          {/* 内容 */}
          <div>
            {/* 头部 */}
            <div className="flex items-center gap-2 mb-1">
              <span className="font-semibold text-white">
                {conflict.signal_a.symbol}
              </span>
              <Tag
                style={{
                  backgroundColor: `${severityConfig.color}20`,
                  color: severityConfig.color,
                  border: 'none',
                  fontSize: '11px',
                }}
              >
                {severityConfig.label}
              </Tag>
              <Tag color="default" className="text-xs">
                {typeConfig.label}
              </Tag>
            </div>

            {/* 描述 */}
            <p className="text-gray-400 text-sm mb-2">{conflict.description}</p>

            {/* 策略信息 */}
            <div className="flex items-center gap-4 text-xs text-gray-500">
              <span>{conflict.signal_a.strategy_name}</span>
              {conflict.signal_b && (
                <>
                  <span>vs</span>
                  <span>{conflict.signal_b.strategy_name}</span>
                </>
              )}
            </div>
          </div>
        </div>

        {/* 右侧 */}
        <div className="flex flex-col items-end gap-2">
          {/* 时间 */}
          <div className="flex items-center gap-1 text-gray-500 text-xs">
            <ClockCircleOutlined />
            {formatConflictTime(conflict.detected_at)}
          </div>

          {/* 剩余时间 */}
          {conflict.expires_at && (
            <div className="text-yellow-400 text-xs">
              剩余 {getRemainingTime(conflict.expires_at)}
            </div>
          )}

          {/* 箭头 */}
          <RightOutlined className="text-gray-600 mt-2" />
        </div>
      </div>
    </div>
  )
}

// 冲突摘要卡片
interface ConflictSummaryCardProps {
  total: number
  critical: number
  warning: number
  info: number
  onViewAll: () => void
}

export function ConflictSummaryCard({
  total,
  critical,
  warning,
  info,
  onViewAll,
}: ConflictSummaryCardProps) {
  return (
    <div className="bg-dark-card rounded-lg p-4">
      <div className="flex items-center justify-between mb-3">
        <h4 className="text-white font-medium flex items-center gap-2">
          <ExclamationCircleOutlined className="text-yellow-400" />
          待处理冲突
        </h4>
        <span className="text-2xl font-bold text-white">{total}</span>
      </div>

      <div className="flex items-center gap-4 mb-3">
        {critical > 0 && (
          <div className="flex items-center gap-1">
            <span
              className="w-2 h-2 rounded-full"
              style={{ backgroundColor: SEVERITY_CONFIG.critical.color }}
            />
            <span className="text-gray-400 text-sm">严重 {critical}</span>
          </div>
        )}
        {warning > 0 && (
          <div className="flex items-center gap-1">
            <span
              className="w-2 h-2 rounded-full"
              style={{ backgroundColor: SEVERITY_CONFIG.warning.color }}
            />
            <span className="text-gray-400 text-sm">警告 {warning}</span>
          </div>
        )}
        {info > 0 && (
          <div className="flex items-center gap-1">
            <span
              className="w-2 h-2 rounded-full"
              style={{ backgroundColor: SEVERITY_CONFIG.info.color }}
            />
            <span className="text-gray-400 text-sm">提示 {info}</span>
          </div>
        )}
      </div>

      <Button type="link" className="p-0 text-blue-400" onClick={onViewAll}>
        查看全部 →
      </Button>
    </div>
  )
}
