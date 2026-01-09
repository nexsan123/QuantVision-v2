/**
 * 策略回放类型定义
 * PRD 4.17 策略回放功能
 */

export type ReplaySpeed = '0.5x' | '1x' | '2x' | '5x'
export type ReplayStatus = 'idle' | 'playing' | 'paused'

export interface ReplayConfig {
  strategyId: string
  symbol: string
  startDate: string
  endDate: string
  speed: ReplaySpeed
}

export interface ReplayState {
  sessionId: string
  config: ReplayConfig
  status: ReplayStatus
  currentTime: string
  currentBarIndex: number
  totalBars: number

  // 模拟持仓
  positionQuantity: number
  positionAvgCost: number
  cash: number

  // 统计
  totalSignals: number
  executedSignals: number
  totalReturnPct: number
  benchmarkReturnPct: number
}

export interface HistoricalBar {
  timestamp: string
  open: number
  high: number
  low: number
  close: number
  volume: number
}

export interface ThresholdConfig {
  value: number
  direction: 'above' | 'below'
  passed: boolean
}

export interface FactorSnapshot {
  timestamp: string
  factorValues: Record<string, number>
  thresholds: Record<string, ThresholdConfig>
  overallSignal: 'buy' | 'sell' | 'hold'
  conditionsMet: number
  conditionsTotal: number
}

export interface SignalEvent {
  eventId: string
  timestamp: string
  eventType: 'buy_trigger' | 'sell_trigger' | 'condition_check'
  symbol: string
  price: number
  description: string
  factorDetails?: Record<string, any>
}

export interface SignalMarker {
  index: number
  time: string
  type: 'buy' | 'sell'
}

export interface ReplayInitResponse {
  state: ReplayState
  totalBars: number
  signalMarkers: SignalMarker[]
}

export interface ReplayTickResponse {
  state: ReplayState
  bar: HistoricalBar
  factorSnapshot: FactorSnapshot
  events: SignalEvent[]
}

export interface ReplayInsight {
  totalSignals: number
  executionRate: number
  winRate: number
  alpha: number
  aiInsights: string[]
  strategyReturn: number
  benchmarkReturn: number
}

// 颜色配置
export const REPLAY_COLORS = {
  // K线区域
  replayedBars: 'normal',
  currentBar: '#8b5cf6',
  futureBars: 'rgba(128,128,128,0.3)',
  positionLine: '#8b5cf6',

  // 信号标记
  buySignal: '#22c55e',
  sellSignal: '#ef4444',

  // 因子状态
  factorPassed: '#22c55e',
  factorFailed: '#ef4444',
}

// 速度配置
export const REPLAY_SPEEDS: { value: ReplaySpeed; label: string; interval: number }[] = [
  { value: '0.5x', label: '0.5x 慢速', interval: 2000 },
  { value: '1x', label: '1x 正常', interval: 1000 },
  { value: '2x', label: '2x 快速', interval: 500 },
  { value: '5x', label: '5x 极速', interval: 200 },
]

// 格式化时间
export function formatReplayTime(timestamp: string): string {
  const date = new Date(timestamp)
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

// 格式化百分比
export function formatPercent(value: number): string {
  const sign = value >= 0 ? '+' : ''
  return `${sign}${(value * 100).toFixed(2)}%`
}

// 获取信号图标
export function getSignalIcon(type: string): string {
  switch (type) {
    case 'buy':
    case 'buy_trigger':
      return '🟢'
    case 'sell':
    case 'sell_trigger':
      return '🔴'
    default:
      return '⚪'
  }
}

// 获取信号标签
export function getEventLabel(type: string): string {
  switch (type) {
    case 'buy_trigger':
      return '买入信号触发'
    case 'sell_trigger':
      return '卖出信号'
    case 'condition_check':
      return '条件检查'
    default:
      return '未知事件'
  }
}
