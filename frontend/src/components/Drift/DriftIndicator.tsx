/**
 * 漂移指示器组件
 * PRD 4.8 实盘vs回测差异监控
 *
 * 用于在策略卡片等处显示漂移状态
 */
import { Tooltip } from 'antd'
import { DriftSeverity, DRIFT_SEVERITY_CONFIG } from '../../types/drift'

interface DriftIndicatorProps {
  severity: DriftSeverity
  score: number
  onClick?: () => void
  showScore?: boolean
  size?: 'small' | 'default'
}

export default function DriftIndicator({
  severity,
  score,
  onClick,
  showScore = false,
  size = 'default',
}: DriftIndicatorProps) {
  const config = DRIFT_SEVERITY_CONFIG[severity]

  // 正常状态不显示
  if (severity === 'normal') {
    return null
  }

  const sizeClasses = {
    small: 'px-1.5 py-0.5 text-xs',
    default: 'px-2 py-1 text-sm',
  }

  return (
    <Tooltip title={`漂移评分: ${score.toFixed(0)}`}>
      <div
        className={`inline-flex items-center gap-1 rounded cursor-pointer hover:opacity-80 transition-opacity ${sizeClasses[size]}`}
        style={{
          backgroundColor: `${config.color}20`,
          color: config.color,
        }}
        onClick={onClick}
      >
        <span>{config.icon}</span>
        <span>漂移{config.text}</span>
        {showScore && <span className="font-mono">({score.toFixed(0)})</span>}
      </div>
    </Tooltip>
  )
}

/**
 * 漂移评分徽章
 * 用于更紧凑的场景
 */
interface DriftScoreBadgeProps {
  score: number
  onClick?: () => void
}

export function DriftScoreBadge({ score, onClick }: DriftScoreBadgeProps) {
  let severity: DriftSeverity = 'normal'
  if (score >= 70) {
    severity = 'critical'
  } else if (score >= 40) {
    severity = 'warning'
  }

  const config = DRIFT_SEVERITY_CONFIG[severity]

  return (
    <Tooltip title={`漂移评分: ${score.toFixed(0)} - ${config.text}`}>
      <div
        className="w-8 h-8 rounded-full flex items-center justify-center cursor-pointer hover:opacity-80 transition-opacity font-mono text-xs font-bold"
        style={{
          backgroundColor: `${config.color}20`,
          color: config.color,
        }}
        onClick={onClick}
      >
        {score.toFixed(0)}
      </div>
    </Tooltip>
  )
}

/**
 * 漂移状态标签
 * 用于表格等场景
 */
interface DriftStatusTagProps {
  severity: DriftSeverity
  score?: number
}

export function DriftStatusTag({ severity, score }: DriftStatusTagProps) {
  const config = DRIFT_SEVERITY_CONFIG[severity]

  return (
    <span
      className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs"
      style={{
        backgroundColor: `${config.color}20`,
        color: config.color,
      }}
    >
      {config.icon}
      {config.text}
      {score !== undefined && <span className="font-mono">({score.toFixed(0)})</span>}
    </span>
  )
}
