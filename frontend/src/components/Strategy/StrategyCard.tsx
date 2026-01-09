/**
 * 策略卡片组件
 */
import { Card, Tag, Progress, Button, Dropdown } from 'antd'
import {
  PlayCircleOutlined,
  PauseCircleOutlined,
  SettingOutlined,
  MoreOutlined,
} from '@ant-design/icons'
import type { MenuProps } from 'antd'
import {
  Deployment,
  STATUS_CONFIG,
  ENV_CONFIG,
  STRATEGY_TYPE_CONFIG,
} from '../../types/deployment'
import { DriftIndicator } from '../Drift'
import { DriftSummary } from '../../types/drift'

interface StrategyCardProps {
  deployment: Deployment
  driftSummary?: DriftSummary
  onStart?: () => void
  onPause?: () => void
  onEdit?: () => void
  onDetail?: () => void
  onDelete?: () => void
  onSwitchEnv?: () => void
  onViewDrift?: () => void
}

export default function StrategyCard({
  deployment,
  driftSummary,
  onStart,
  onPause,
  onEdit,
  onDetail,
  onDelete,
  onSwitchEnv,
  onViewDrift,
}: StrategyCardProps) {
  const statusConfig = STATUS_CONFIG[deployment.status]
  const envConfig = ENV_CONFIG[deployment.environment]
  const isProfitable = deployment.currentPnl >= 0

  const menuItems: MenuProps['items'] = [
    {
      key: 'signals',
      label: '查看信号',
    },
    {
      key: 'history',
      label: '交易历史',
    },
    {
      key: 'switch',
      label: deployment.environment === 'paper' ? '切换到实盘' : '切换到模拟盘',
      onClick: () => onSwitchEnv?.(),
    },
    { type: 'divider' },
    {
      key: 'delete',
      label: '删除',
      danger: true,
      onClick: () => onDelete?.(),
    },
  ]

  return (
    <Card
      className="!bg-dark-card hover:border-blue-500/50 cursor-pointer transition-all duration-200"
      onClick={onDetail}
      hoverable
    >
      {/* 头部 */}
      <div className="flex justify-between items-start mb-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <h3 className="text-lg font-bold text-white truncate">
              {deployment.strategyName}
            </h3>
            {/* 漂移指示器 */}
            {driftSummary && driftSummary.hasReport && driftSummary.overallSeverity !== 'normal' && (
              <div onClick={(e) => e.stopPropagation()}>
                <DriftIndicator
                  severity={driftSummary.overallSeverity}
                  score={driftSummary.driftScore}
                  size="small"
                  onClick={onViewDrift}
                />
              </div>
            )}
          </div>
          <p className="text-sm text-gray-400 truncate">{deployment.deploymentName}</p>
        </div>
        <div className="flex gap-2 flex-shrink-0 ml-2">
          <Tag color={envConfig.color}>{envConfig.label}</Tag>
          <Tag color={statusConfig.color}>{statusConfig.label}</Tag>
        </div>
      </div>

      {/* 收益 */}
      <div className="mb-4">
        <div
          className={`text-2xl font-bold font-mono ${
            isProfitable ? 'text-green-400' : 'text-red-400'
          }`}
        >
          {isProfitable ? '+' : ''}${deployment.currentPnl.toFixed(2)}
          <span className="text-sm ml-2">
            ({isProfitable ? '+' : ''}
            {(deployment.currentPnlPct * 100).toFixed(2)}%)
          </span>
        </div>
      </div>

      {/* 统计 */}
      <div className="grid grid-cols-3 gap-4 mb-4">
        <div>
          <div className="text-xs text-gray-500">交易次数</div>
          <div className="text-lg font-medium">{deployment.totalTrades}</div>
        </div>
        <div>
          <div className="text-xs text-gray-500">胜率</div>
          <div
            className={`text-lg font-medium ${
              deployment.winRate >= 0.5 ? 'text-green-400' : 'text-yellow-400'
            }`}
          >
            {(deployment.winRate * 100).toFixed(1)}%
          </div>
        </div>
        <div>
          <div className="text-xs text-gray-500">类型</div>
          <div className="text-sm">{STRATEGY_TYPE_CONFIG[deployment.strategyType].label}</div>
        </div>
      </div>

      {/* 胜率进度条 */}
      <Progress
        percent={deployment.winRate * 100}
        showInfo={false}
        strokeColor={deployment.winRate >= 0.5 ? '#22c55e' : '#eab308'}
        trailColor="#374151"
        size="small"
      />

      {/* 操作按钮 */}
      <div className="flex justify-between mt-4 pt-4 border-t border-dark-border">
        <div className="space-x-2">
          {deployment.status === 'running' ? (
            <Button
              icon={<PauseCircleOutlined />}
              size="small"
              onClick={e => {
                e.stopPropagation()
                onPause?.()
              }}
            >
              暂停
            </Button>
          ) : (
            <Button
              icon={<PlayCircleOutlined />}
              size="small"
              type="primary"
              onClick={e => {
                e.stopPropagation()
                onStart?.()
              }}
            >
              启动
            </Button>
          )}
        </div>
        <div className="space-x-2">
          <Button
            icon={<SettingOutlined />}
            size="small"
            onClick={e => {
              e.stopPropagation()
              onEdit?.()
            }}
          />
          <Dropdown menu={{ items: menuItems }} trigger={['click']}>
            <Button
              icon={<MoreOutlined />}
              size="small"
              onClick={e => e.stopPropagation()}
            />
          </Dropdown>
        </div>
      </div>
    </Card>
  )
}
