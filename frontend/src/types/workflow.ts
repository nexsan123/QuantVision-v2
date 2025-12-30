/**
 * 节点工作流类型定义
 *
 * 定义策略构建工作流中的节点类型和配置
 */

// 节点类型枚举
export type WorkflowNodeType =
  | 'universe'    // 股票池
  | 'factor'      // 因子
  | 'filter'      // 筛选
  | 'rank'        // 排名
  | 'signal'      // 信号
  | 'weight'      // 权重
  | 'output'      // 输出

// 节点基础数据
export interface BaseNodeData {
  label: string
  description?: string
  isConfigured: boolean
}

// 股票池节点
export interface UniverseNodeData extends BaseNodeData {
  type: 'universe'
  config: {
    baseUniverse: 'sp500' | 'nasdaq100' | 'russell1000' | 'custom'
    customSymbols?: string[]
    excludeSymbols?: string[]
    marketCapMin?: number
    marketCapMax?: number
    sectorFilter?: string[]
  }
}

// 因子节点
export interface FactorNodeData extends BaseNodeData {
  type: 'factor'
  config: {
    factorId: string
    factorName: string
    expression?: string
    parameters: Record<string, number | string>
    lookbackPeriod: number
  }
}

// 筛选节点
export interface FilterNodeData extends BaseNodeData {
  type: 'filter'
  config: {
    conditions: FilterCondition[]
    logic: 'and' | 'or'
  }
}

export interface FilterCondition {
  id: string
  field: string
  operator: 'gt' | 'lt' | 'gte' | 'lte' | 'eq' | 'neq' | 'between'
  value: number | [number, number]
}

// 排名节点
export interface RankNodeData extends BaseNodeData {
  type: 'rank'
  config: {
    rankBy: string
    ascending: boolean
    topN?: number
    bottomN?: number
    percentile?: number
  }
}

// 信号节点
export interface SignalNodeData extends BaseNodeData {
  type: 'signal'
  config: {
    signalType: 'long' | 'short' | 'longshort'
    entryCondition: string
    exitCondition?: string
    holdPeriod?: number
  }
}

// 权重节点
export interface WeightNodeData extends BaseNodeData {
  type: 'weight'
  config: {
    method: 'equal' | 'marketCap' | 'inverseVolatility' | 'riskParity' | 'custom'
    maxWeight?: number
    minWeight?: number
    customWeights?: Record<string, number>
  }
}

// 输出节点
export interface OutputNodeData extends BaseNodeData {
  type: 'output'
  config: {
    outputType: 'portfolio' | 'signal' | 'backtest'
    rebalanceFrequency: 'daily' | 'weekly' | 'monthly'
    targetPositions?: number
  }
}

// 所有节点数据类型
export type WorkflowNodeData =
  | UniverseNodeData
  | FactorNodeData
  | FilterNodeData
  | RankNodeData
  | SignalNodeData
  | WeightNodeData
  | OutputNodeData

// React Flow 节点类型
export interface WorkflowNode {
  id: string
  type: WorkflowNodeType
  position: { x: number; y: number }
  data: WorkflowNodeData
}

// React Flow 边类型
export interface WorkflowEdge {
  id: string
  source: string
  target: string
  sourceHandle?: string
  targetHandle?: string
  animated?: boolean
}

// 完整工作流
export interface Workflow {
  id: string
  name: string
  description?: string
  nodes: WorkflowNode[]
  edges: WorkflowEdge[]
  createdAt: string
  updatedAt: string
  version: number
}

// 节点模板 (用于工具箱)
export interface NodeTemplate {
  type: WorkflowNodeType
  label: string
  description: string
  icon: string
  category: 'data' | 'transform' | 'signal' | 'output'
  defaultData: Partial<WorkflowNodeData>
}

// 节点模板配置
export const NODE_TEMPLATES: NodeTemplate[] = [
  {
    type: 'universe',
    label: '股票池',
    description: '定义交易标的范围',
    icon: 'database',
    category: 'data',
    defaultData: {
      label: '股票池',
      isConfigured: false,
      type: 'universe',
      config: {
        baseUniverse: 'sp500',
      },
    } as Partial<UniverseNodeData>,
  },
  {
    type: 'factor',
    label: '因子',
    description: '添加量化因子',
    icon: 'function',
    category: 'data',
    defaultData: {
      label: '因子',
      isConfigured: false,
      type: 'factor',
      config: {
        factorId: '',
        factorName: '',
        parameters: {},
        lookbackPeriod: 20,
      },
    } as Partial<FactorNodeData>,
  },
  {
    type: 'filter',
    label: '筛选',
    description: '根据条件筛选股票',
    icon: 'filter',
    category: 'transform',
    defaultData: {
      label: '筛选',
      isConfigured: false,
      type: 'filter',
      config: {
        conditions: [],
        logic: 'and',
      },
    } as Partial<FilterNodeData>,
  },
  {
    type: 'rank',
    label: '排名',
    description: '按指标排名',
    icon: 'sort-ascending',
    category: 'transform',
    defaultData: {
      label: '排名',
      isConfigured: false,
      type: 'rank',
      config: {
        rankBy: '',
        ascending: false,
        topN: 10,
      },
    } as Partial<RankNodeData>,
  },
  {
    type: 'signal',
    label: '信号',
    description: '生成交易信号',
    icon: 'thunderbolt',
    category: 'signal',
    defaultData: {
      label: '信号',
      isConfigured: false,
      type: 'signal',
      config: {
        signalType: 'long',
        entryCondition: '',
      },
    } as Partial<SignalNodeData>,
  },
  {
    type: 'weight',
    label: '权重',
    description: '分配持仓权重',
    icon: 'pie-chart',
    category: 'transform',
    defaultData: {
      label: '权重',
      isConfigured: false,
      type: 'weight',
      config: {
        method: 'equal',
        maxWeight: 0.1,
      },
    } as Partial<WeightNodeData>,
  },
  {
    type: 'output',
    label: '输出',
    description: '策略输出配置',
    icon: 'export',
    category: 'output',
    defaultData: {
      label: '输出',
      isConfigured: false,
      type: 'output',
      config: {
        outputType: 'portfolio',
        rebalanceFrequency: 'monthly',
        targetPositions: 20,
      },
    } as Partial<OutputNodeData>,
  },
]

// 节点颜色配置
export const NODE_COLORS: Record<WorkflowNodeType, string> = {
  universe: '#3b82f6',   // blue
  factor: '#8b5cf6',     // purple
  filter: '#f59e0b',     // amber
  rank: '#10b981',       // emerald
  signal: '#ef4444',     // red
  weight: '#06b6d4',     // cyan
  output: '#22c55e',     // green
}

// 验证工作流连接
export function validateConnection(
  sourceType: WorkflowNodeType,
  targetType: WorkflowNodeType
): boolean {
  const validConnections: Record<WorkflowNodeType, WorkflowNodeType[]> = {
    universe: ['factor', 'filter', 'rank'],
    factor: ['filter', 'rank', 'signal'],
    filter: ['rank', 'signal', 'weight'],
    rank: ['signal', 'weight', 'output'],
    signal: ['weight', 'output'],
    weight: ['output'],
    output: [],
  }

  return validConnections[sourceType]?.includes(targetType) ?? false
}
