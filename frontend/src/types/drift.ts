/**
 * 策略漂移监控类型定义
 * PRD 4.8 实盘vs回测差异监控
 */

// 漂移指标类型
export type DriftMetricType =
  | 'return'
  | 'win_rate'
  | 'turnover'
  | 'slippage'
  | 'max_drawdown'
  | 'hold_period';

// 漂移严重程度
export type DriftSeverity = 'normal' | 'warning' | 'critical';

// 单个漂移指标
export interface DriftMetric {
  metricType: DriftMetricType;
  backtestValue: number;
  liveValue: number;
  difference: number;
  differencePct: number;
  warningThreshold: number;
  criticalThreshold: number;
  severity: DriftSeverity;
  description: string;
}

// 策略漂移报告
export interface StrategyDriftReport {
  reportId: string;
  strategyId: string;
  strategyName: string;
  deploymentId: string;
  environment: 'paper' | 'live';
  periodStart: string;
  periodEnd: string;
  daysCompared: number;
  overallSeverity: DriftSeverity;
  driftScore: number;
  metrics: DriftMetric[];
  recommendations: string[];
  shouldPause: boolean;
  createdAt: string;
  isAcknowledged: boolean;
}

// 漂移检查请求
export interface DriftCheckRequest {
  strategyId: string;
  deploymentId: string;
  periodDays?: number;
}

// 漂移摘要 (用于卡片显示)
export interface DriftSummary {
  hasReport: boolean;
  strategyId: string;
  reportId?: string;
  overallSeverity: DriftSeverity;
  driftScore: number;
  shouldPause: boolean;
  isAcknowledged: boolean;
  createdAt?: string;
  daysCompared?: number;
}

// 指标标签
export const DRIFT_METRIC_LABELS: Record<DriftMetricType, string> = {
  return: '收益率',
  win_rate: '胜率',
  turnover: '换手率',
  slippage: '滑点',
  max_drawdown: '最大回撤',
  hold_period: '持仓时间',
};

// 指标图标
export const DRIFT_METRIC_ICONS: Record<DriftMetricType, string> = {
  return: '📈',
  win_rate: '🎯',
  turnover: '🔄',
  slippage: '💸',
  max_drawdown: '📉',
  hold_period: '📅',
};

// 严重程度配置
export const DRIFT_SEVERITY_CONFIG: Record<
  DriftSeverity,
  {
    icon: string;
    color: string;
    text: string;
    bgColor: string;
    borderColor: string;
  }
> = {
  normal: {
    icon: '✅',
    color: '#22c55e',
    text: '正常',
    bgColor: 'bg-green-500/10',
    borderColor: 'border-green-500',
  },
  warning: {
    icon: '⚠️',
    color: '#eab308',
    text: '需关注',
    bgColor: 'bg-yellow-500/10',
    borderColor: 'border-yellow-500',
  },
  critical: {
    icon: '🔴',
    color: '#ef4444',
    text: '异常',
    bgColor: 'bg-red-500/10',
    borderColor: 'border-red-500',
  },
};

// 格式化漂移值
export function formatDriftValue(
  value: number,
  metricType: DriftMetricType
): string {
  if (
    ['return', 'win_rate', 'turnover', 'max_drawdown', 'slippage'].includes(
      metricType
    )
  ) {
    return `${(value * 100).toFixed(1)}%`;
  }
  return value.toFixed(1);
}

// 格式化差异百分比
export function formatDifferencePct(pct: number): string {
  return `${(pct * 100).toFixed(1)}%`;
}

// 获取漂移评分等级
export function getDriftScoreLevel(score: number): {
  level: string;
  color: string;
} {
  if (score >= 70) {
    return { level: '严重', color: '#ef4444' };
  }
  if (score >= 40) {
    return { level: '警告', color: '#eab308' };
  }
  return { level: '正常', color: '#22c55e' };
}
