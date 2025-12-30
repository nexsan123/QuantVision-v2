/**
 * 工作流画布组件
 *
 * 基于 React Flow 的可视化策略构建画布
 */

import { useCallback, useState, useMemo } from 'react'
import ReactFlow, {
  Node,
  Edge,
  Controls,
  Background,
  MiniMap,
  Connection,
  addEdge,
  useNodesState,
  useEdgesState,
  BackgroundVariant,
  Panel,
} from 'reactflow'
import 'reactflow/dist/style.css'
import { Button, message } from 'antd'
import {
  SaveOutlined,
  ImportOutlined,
  ExportOutlined,
} from '@ant-design/icons'

import { WorkflowNode } from './WorkflowNode'
import { NodeToolbox } from './NodeToolbox'
import { NodeConfigPanel } from './NodeConfigPanel'
import {
  WorkflowNodeData,
  WorkflowNodeType,
  Workflow,
  NODE_COLORS,
  validateConnection,
} from '@/types/workflow'

// 自定义节点类型
const nodeTypes = {
  universe: WorkflowNode,
  factor: WorkflowNode,
  filter: WorkflowNode,
  rank: WorkflowNode,
  signal: WorkflowNode,
  weight: WorkflowNode,
  output: WorkflowNode,
}

interface WorkflowCanvasProps {
  workflow?: Workflow
  onSave?: (workflow: Workflow) => void
  onChange?: (nodes: Node[], edges: Edge[]) => void
  readOnly?: boolean
}

export function WorkflowCanvas({
  workflow,
  onSave,
  onChange: _onChange,
  readOnly = false,
}: WorkflowCanvasProps) {
  // 初始化节点和边
  const initialNodes: Node<WorkflowNodeData>[] = workflow?.nodes || []
  const initialEdges: Edge[] = workflow?.edges || []

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges)
  const [selectedNode, setSelectedNode] = useState<Node<WorkflowNodeData> | null>(null)

  // 节点类型映射
  const nodeTypesMap = useMemo(() => nodeTypes, [])

  // 处理连接
  const onConnect = useCallback(
    (connection: Connection) => {
      if (!connection.source || !connection.target) return

      const sourceNode = nodes.find((n) => n.id === connection.source)
      const targetNode = nodes.find((n) => n.id === connection.target)

      if (!sourceNode || !targetNode) return

      const sourceType = sourceNode.type as WorkflowNodeType
      const targetType = targetNode.type as WorkflowNodeType

      // 验证连接有效性
      if (!validateConnection(sourceType, targetType)) {
        message.warning(`无法连接 ${sourceNode.data.label} 到 ${targetNode.data.label}`)
        return
      }

      const newEdge: Edge = {
        id: `e${connection.source}-${connection.target}`,
        source: connection.source,
        target: connection.target,
        sourceHandle: connection.sourceHandle,
        targetHandle: connection.targetHandle,
        animated: true,
        style: { stroke: NODE_COLORS[sourceType] },
      }

      setEdges((eds) => addEdge(newEdge, eds))
    },
    [nodes, setEdges]
  )

  // 处理拖放
  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault()
    event.dataTransfer.dropEffect = 'move'
  }, [])

  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault()

      const type = event.dataTransfer.getData('application/reactflow')
      const nodeData = event.dataTransfer.getData('nodeData')

      if (!type || !nodeData) return

      const position = {
        x: event.clientX - 300, // 调整偏移
        y: event.clientY - 100,
      }

      const newNode: Node<WorkflowNodeData> = {
        id: `${type}-${Date.now()}`,
        type,
        position,
        data: JSON.parse(nodeData),
      }

      setNodes((nds) => [...nds, newNode])
    },
    [setNodes]
  )

  // 处理节点选择
  const onNodeClick = useCallback(
    (_event: React.MouseEvent, node: Node<WorkflowNodeData>) => {
      setSelectedNode(node)
    },
    []
  )

  // 处理画布点击 (取消选择)
  const onPaneClick = useCallback(() => {
    setSelectedNode(null)
  }, [])

  // 更新节点数据
  const onNodeDataChange = useCallback(
    (nodeId: string, newData: WorkflowNodeData) => {
      setNodes((nds) =>
        nds.map((node) =>
          node.id === nodeId
            ? { ...node, data: { ...newData, isConfigured: true } }
            : node
        )
      )
      setSelectedNode(null)
      message.success('节点配置已更新')
    },
    [setNodes]
  )

  // 删除节点
  const onNodeDelete = useCallback(
    (nodeId: string) => {
      setNodes((nds) => nds.filter((n) => n.id !== nodeId))
      setEdges((eds) => eds.filter((e) => e.source !== nodeId && e.target !== nodeId))
      setSelectedNode(null)
      message.info('节点已删除')
    },
    [setNodes, setEdges]
  )

  // 导出工作流
  const handleExport = useCallback(() => {
    const workflowData: Workflow = {
      id: workflow?.id || `workflow-${Date.now()}`,
      name: workflow?.name || '未命名工作流',
      nodes: nodes.map((n) => ({
        id: n.id,
        type: n.type as WorkflowNodeType,
        position: n.position,
        data: n.data,
      })),
      edges: edges.map((e) => ({
        id: e.id,
        source: e.source,
        target: e.target,
      })),
      createdAt: workflow?.createdAt || new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      version: (workflow?.version || 0) + 1,
    }

    const blob = new Blob([JSON.stringify(workflowData, null, 2)], {
      type: 'application/json',
    })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `${workflowData.name}.json`
    link.click()
    URL.revokeObjectURL(url)

    message.success('工作流已导出')
  }, [nodes, edges, workflow])

  // 导入工作流
  const handleImport = useCallback(() => {
    const input = document.createElement('input')
    input.type = 'file'
    input.accept = '.json'
    input.onchange = async (e) => {
      const file = (e.target as HTMLInputElement).files?.[0]
      if (!file) return

      try {
        const text = await file.text()
        const data = JSON.parse(text) as Workflow

        setNodes(
          data.nodes.map((n) => ({
            id: n.id,
            type: n.type,
            position: n.position,
            data: n.data,
          }))
        )

        setEdges(
          data.edges.map((e) => ({
            id: e.id,
            source: e.source,
            target: e.target,
            animated: true,
          }))
        )

        message.success('工作流已导入')
      } catch {
        message.error('导入失败: 无效的工作流文件')
      }
    }
    input.click()
  }, [setNodes, setEdges])

  // 保存工作流
  const handleSave = useCallback(() => {
    const workflowData: Workflow = {
      id: workflow?.id || `workflow-${Date.now()}`,
      name: workflow?.name || '未命名工作流',
      nodes: nodes.map((n) => ({
        id: n.id,
        type: n.type as WorkflowNodeType,
        position: n.position,
        data: n.data,
      })),
      edges: edges.map((e) => ({
        id: e.id,
        source: e.source,
        target: e.target,
      })),
      createdAt: workflow?.createdAt || new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      version: (workflow?.version || 0) + 1,
    }

    onSave?.(workflowData)
    message.success('工作流已保存')
  }, [nodes, edges, workflow, onSave])

  return (
    <div className="flex h-full">
      {/* 左侧工具箱 */}
      {!readOnly && (
        <div className="w-48 border-r border-dark-border bg-dark-card">
          <NodeToolbox />
        </div>
      )}

      {/* 中间画布 */}
      <div className="flex-1 relative">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={readOnly ? undefined : onNodesChange}
          onEdgesChange={readOnly ? undefined : onEdgesChange}
          onConnect={readOnly ? undefined : onConnect}
          onDragOver={readOnly ? undefined : onDragOver}
          onDrop={readOnly ? undefined : onDrop}
          onNodeClick={onNodeClick}
          onPaneClick={onPaneClick}
          nodeTypes={nodeTypesMap}
          fitView
          className="bg-dark-bg"
          defaultEdgeOptions={{
            animated: true,
            style: { stroke: '#6b7280' },
          }}
        >
          <Background
            variant={BackgroundVariant.Dots}
            gap={20}
            size={1}
            color="#374151"
          />
          <Controls className="!bg-dark-card !border-dark-border" />
          <MiniMap
            className="!bg-dark-card"
            nodeColor={(node) => NODE_COLORS[node.type as WorkflowNodeType] || '#6b7280'}
          />

          {/* 工具栏 */}
          {!readOnly && (
            <Panel position="top-right" className="flex gap-2">
              <Button
                icon={<SaveOutlined />}
                onClick={handleSave}
                className="!bg-dark-card !border-dark-border"
              >
                保存
              </Button>
              <Button
                icon={<ImportOutlined />}
                onClick={handleImport}
                className="!bg-dark-card !border-dark-border"
              >
                导入
              </Button>
              <Button
                icon={<ExportOutlined />}
                onClick={handleExport}
                className="!bg-dark-card !border-dark-border"
              >
                导出
              </Button>
            </Panel>
          )}
        </ReactFlow>
      </div>

      {/* 右侧配置面板 */}
      {selectedNode && !readOnly && (
        <div className="w-80 border-l border-dark-border bg-dark-card">
          <NodeConfigPanel
            node={selectedNode}
            onUpdate={(data) => onNodeDataChange(selectedNode.id, data)}
            onDelete={() => onNodeDelete(selectedNode.id)}
            onClose={() => setSelectedNode(null)}
          />
        </div>
      )}
    </div>
  )
}

export default WorkflowCanvas
