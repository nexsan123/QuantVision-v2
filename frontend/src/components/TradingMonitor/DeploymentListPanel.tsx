/**
 * 部署列表面板
 * Sprint 3 - F11: 显示运行中的策略部署
 */
import { Badge, Tooltip } from 'antd'
import { PlayCircleOutlined, PauseCircleOutlined } from '@ant-design/icons'
import type { Deployment } from '@/types/deployment'

interface DeploymentListPanelProps {
  deployments: Deployment[]
  selectedId?: string
  onSelect: (deployment: Deployment) => void
}

export default function DeploymentListPanel({
  deployments,
  selectedId,
  onSelect,
}: DeploymentListPanelProps) {
  return (
    <div className="h-full flex flex-col">
      {/* 标题 */}
      <div className="px-3 py-2 border-b border-gray-800 flex items-center justify-between">
        <span className="text-sm font-medium text-white">运行中的策略</span>
        <Badge count={deployments.length} style={{ backgroundColor: '#52c41a' }} />
      </div>

      {/* 部署列表 */}
      <div className="flex-1 overflow-y-auto">
        {deployments.length === 0 ? (
          <div className="p-4 text-center text-gray-500 text-sm">
            暂无运行中的策略
          </div>
        ) : (
          <div className="py-1">
            {deployments.map(deployment => (
              <DeploymentItem
                key={deployment.deploymentId}
                deployment={deployment}
                isSelected={deployment.deploymentId === selectedId}
                onClick={() => onSelect(deployment)}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

interface DeploymentItemProps {
  deployment: Deployment
  isSelected: boolean
  onClick: () => void
}

function DeploymentItem({ deployment, isSelected, onClick }: DeploymentItemProps) {
  const isRunning = deployment.status === 'running'
  const isPaper = deployment.environment === 'paper'

  return (
    <div
      className={`px-3 py-2 cursor-pointer transition-colors ${
        isSelected
          ? 'bg-blue-900/30 border-l-2 border-blue-500'
          : 'hover:bg-gray-800/50 border-l-2 border-transparent'
      }`}
      onClick={onClick}
    >
      {/* 策略名 + 状态 */}
      <div className="flex items-center justify-between mb-1">
        <span className="text-sm font-medium text-white truncate flex-1">
          {deployment.strategyName}
        </span>
        <Tooltip title={isRunning ? '运行中' : '已暂停'}>
          {isRunning ? (
            <PlayCircleOutlined className="text-green-400 text-sm" />
          ) : (
            <PauseCircleOutlined className="text-yellow-400 text-sm" />
          )}
        </Tooltip>
      </div>

      {/* 部署名 + 环境 */}
      <div className="flex items-center justify-between">
        <span className="text-xs text-gray-500 truncate">
          {deployment.deploymentName}
        </span>
        <span
          className={`text-xs px-1.5 py-0.5 rounded ${
            isPaper
              ? 'bg-blue-900/50 text-blue-400'
              : 'bg-green-900/50 text-green-400'
          }`}
        >
          {isPaper ? '模拟' : '实盘'}
        </span>
      </div>

      {/* 盈亏 */}
      <div className="flex items-center justify-between mt-1">
        <span className="text-xs text-gray-500">今日盈亏</span>
        <span
          className={`text-xs font-mono ${
            deployment.currentPnl >= 0 ? 'text-green-400' : 'text-red-400'
          }`}
        >
          {deployment.currentPnl >= 0 ? '+' : ''}
          ${deployment.currentPnl.toFixed(2)}
          <span className="text-gray-500 ml-1">
            ({(deployment.currentPnlPct * 100).toFixed(2)}%)
          </span>
        </span>
      </div>
    </div>
  )
}
