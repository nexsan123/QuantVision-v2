/**
 * Workflow 组件导出
 *
 * 基于 React Flow 的可视化策略构建模块
 */

export { WorkflowCanvas } from './WorkflowCanvas'
export { WorkflowNode } from './WorkflowNode'
export { NodeToolbox } from './NodeToolbox'
export { NodeConfigPanel } from './NodeConfigPanel'

// 类型重导出
export type {
  WorkflowNodeType,
  WorkflowNodeData,
  UniverseNodeData,
  FactorNodeData,
  FilterNodeData,
  RankNodeData,
  SignalNodeData,
  WeightNodeData,
  OutputNodeData,
  Workflow,
  WorkflowNode as WorkflowNodeType_,
  WorkflowEdge,
  NodeTemplate,
} from '@/types/workflow'

export {
  NODE_TEMPLATES,
  NODE_COLORS,
  validateConnection,
} from '@/types/workflow'
