/**
 * 节点工具箱组件
 *
 * 提供可拖拽的节点模板
 */

import {
  DatabaseOutlined,
  FunctionOutlined,
  FilterOutlined,
  SortAscendingOutlined,
  ThunderboltOutlined,
  PieChartOutlined,
  ExportOutlined,
} from '@ant-design/icons'
import { NODE_TEMPLATES, WorkflowNodeType, NODE_COLORS } from '@/types/workflow'

const iconMap: Record<WorkflowNodeType, React.ReactNode> = {
  universe: <DatabaseOutlined />,
  factor: <FunctionOutlined />,
  filter: <FilterOutlined />,
  rank: <SortAscendingOutlined />,
  signal: <ThunderboltOutlined />,
  weight: <PieChartOutlined />,
  output: <ExportOutlined />,
}

const categoryLabels: Record<string, string> = {
  data: '数据源',
  transform: '转换',
  signal: '信号',
  output: '输出',
}

export function NodeToolbox() {
  const categories = ['data', 'transform', 'signal', 'output']

  const onDragStart = (
    event: React.DragEvent,
    nodeType: WorkflowNodeType,
    nodeData: object
  ) => {
    event.dataTransfer.setData('application/reactflow', nodeType)
    event.dataTransfer.setData('nodeData', JSON.stringify(nodeData))
    event.dataTransfer.effectAllowed = 'move'
  }

  return (
    <div className="p-4">
      <h3 className="text-sm font-medium text-gray-400 mb-4">节点工具箱</h3>

      {categories.map((category) => {
        const categoryNodes = NODE_TEMPLATES.filter((t) => t.category === category)

        if (categoryNodes.length === 0) return null

        return (
          <div key={category} className="mb-4">
            <div className="text-xs text-gray-500 mb-2">
              {categoryLabels[category]}
            </div>
            <div className="space-y-2">
              {categoryNodes.map((template) => {
                const color = NODE_COLORS[template.type]
                const icon = iconMap[template.type]

                return (
                  <div
                    key={template.type}
                    className="
                      flex items-center gap-2 p-2 rounded-md cursor-grab
                      bg-dark-hover border border-dark-border
                      hover:border-primary-500 transition-colors
                    "
                    draggable
                    onDragStart={(e) =>
                      onDragStart(e, template.type, template.defaultData)
                    }
                  >
                    <span style={{ color }} className="text-base">
                      {icon}
                    </span>
                    <div className="flex-1 min-w-0">
                      <div className="text-sm text-gray-200 truncate">
                        {template.label}
                      </div>
                      <div className="text-xs text-gray-500 truncate">
                        {template.description}
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        )
      })}

      <div className="mt-6 pt-4 border-t border-dark-border">
        <div className="text-xs text-gray-500">
          拖拽节点到画布添加
        </div>
      </div>
    </div>
  )
}

export default NodeToolbox
