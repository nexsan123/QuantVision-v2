/**
 * 工作流节点组件
 *
 * 自定义 React Flow 节点，支持不同类型的节点渲染
 */

import { memo } from 'react'
import { Handle, Position, NodeProps } from 'reactflow'
import {
  DatabaseOutlined,
  FunctionOutlined,
  FilterOutlined,
  SortAscendingOutlined,
  ThunderboltOutlined,
  PieChartOutlined,
  ExportOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
} from '@ant-design/icons'
import { WorkflowNodeData, WorkflowNodeType, NODE_COLORS } from '@/types/workflow'

const iconMap: Record<WorkflowNodeType, React.ReactNode> = {
  universe: <DatabaseOutlined />,
  factor: <FunctionOutlined />,
  filter: <FilterOutlined />,
  rank: <SortAscendingOutlined />,
  signal: <ThunderboltOutlined />,
  weight: <PieChartOutlined />,
  output: <ExportOutlined />,
}

function WorkflowNodeComponent({ data, selected }: NodeProps<WorkflowNodeData>) {
  const nodeType = data.type
  const color = NODE_COLORS[nodeType]
  const icon = iconMap[nodeType]

  return (
    <div
      className={`
        relative px-4 py-3 rounded-lg border-2 min-w-[160px]
        bg-dark-card shadow-lg transition-all duration-200
        ${selected ? 'ring-2 ring-primary-500 ring-offset-2 ring-offset-dark-bg' : ''}
      `}
      style={{ borderColor: color }}
    >
      {/* 输入连接点 */}
      {nodeType !== 'universe' && (
        <Handle
          type="target"
          position={Position.Left}
          className="w-3 h-3 !bg-gray-400 border-2 border-dark-bg"
        />
      )}

      {/* 节点头部 */}
      <div className="flex items-center gap-2 mb-1">
        <span style={{ color }} className="text-lg">
          {icon}
        </span>
        <span className="font-medium text-gray-200 text-sm">
          {data.label}
        </span>
        {/* 配置状态指示 */}
        <span className="ml-auto">
          {data.isConfigured ? (
            <CheckCircleOutlined className="text-green-500" />
          ) : (
            <ExclamationCircleOutlined className="text-yellow-500" />
          )}
        </span>
      </div>

      {/* 节点描述 */}
      {data.description && (
        <div className="text-xs text-gray-500 truncate">
          {data.description}
        </div>
      )}

      {/* 节点配置预览 */}
      <div className="mt-2 text-xs text-gray-400">
        {renderConfigPreview(data)}
      </div>

      {/* 输出连接点 */}
      {nodeType !== 'output' && (
        <Handle
          type="source"
          position={Position.Right}
          className="w-3 h-3 !bg-gray-400 border-2 border-dark-bg"
        />
      )}
    </div>
  )
}

// 渲染配置预览
function renderConfigPreview(data: WorkflowNodeData): React.ReactNode {
  switch (data.type) {
    case 'universe':
      return data.config.baseUniverse?.toUpperCase() || '未配置'

    case 'factor':
      return data.config.factorName || '选择因子...'

    case 'filter': {
      const condCount = data.config.conditions?.length || 0
      return condCount > 0 ? `${condCount} 个条件` : '添加条件...'
    }

    case 'rank':
      if (data.config.topN) return `Top ${data.config.topN}`
      if (data.config.bottomN) return `Bottom ${data.config.bottomN}`
      return '配置排名...'

    case 'signal':
      return data.config.signalType === 'long' ? '做多' :
             data.config.signalType === 'short' ? '做空' : '多空'

    case 'weight': {
      const methodLabels: Record<string, string> = {
        equal: '等权',
        marketCap: '市值加权',
        inverseVolatility: '波动率倒数',
        riskParity: '风险平价',
        custom: '自定义',
      }
      return methodLabels[data.config.method] || '选择方法...'
    }

    case 'output': {
      const freqLabels: Record<string, string> = {
        daily: '每日',
        weekly: '每周',
        monthly: '每月',
      }
      return freqLabels[data.config.rebalanceFrequency] || '配置输出...'
    }

    default:
      return null
  }
}

export const WorkflowNode = memo(WorkflowNodeComponent)
export default WorkflowNode
