/**
 * 策略冲突检测类型定义
 * PRD 4.6 策略冲突检测
 */

// 冲突类型
export type ConflictType = 'logic' | 'execution' | 'timeout' | 'duplicate';

// 冲突严重程度
export type ConflictSeverity = 'critical' | 'warning' | 'info';

// 冲突状态
export type ConflictStatus = 'pending' | 'resolved' | 'ignored' | 'auto_resolved';

// 解决方案
export type ResolutionAction =
  | 'execute_strategy_a'
  | 'execute_strategy_b'
  | 'execute_both'
  | 'cancel_both'
  | 'reduce_position'
  | 'delay_execution'
  | 'ignore';

// 冲突信号
export interface ConflictingSignal {
  strategy_id: string;
  strategy_name: string;
  signal_id: string;
  symbol: string;
  direction: 'buy' | 'sell';
  quantity: number;
  price: number;
  signal_time: string;
  signal_strength: number;
  expected_return?: number;
  confidence: number;
}

// 冲突详情
export interface ConflictDetail {
  conflict_id: string;
  conflict_type: ConflictType;
  severity: ConflictSeverity;
  status: ConflictStatus;
  signal_a: ConflictingSignal;
  signal_b?: ConflictingSignal;
  description: string;
  reason: string;
  impact: string;
  suggested_resolution: ResolutionAction;
  resolution_reason: string;
  alternative_resolutions: ResolutionAction[];
  detected_at: string;
  expires_at?: string;
  resolved_at?: string;
  resolution?: ResolutionAction;
  resolved_by?: string;
}

// 冲突检测结果
export interface ConflictCheckResult {
  total_conflicts: number;
  critical_count: number;
  warning_count: number;
  info_count: number;
  conflicts: ConflictDetail[];
  checked_at: string;
}

// 冲突类型配置
export const CONFLICT_TYPE_CONFIG: Record<
  ConflictType,
  { label: string; description: string; icon: string; color: string }
> = {
  logic: {
    label: '逻辑冲突',
    description: '同一股票存在相反的交易信号',
    icon: '⚔️',
    color: '#ef4444',
  },
  execution: {
    label: '执行冲突',
    description: '资金或仓位限制导致无法执行',
    icon: '💰',
    color: '#f59e0b',
  },
  timeout: {
    label: '超时冲突',
    description: '信号已超过有效期',
    icon: '⏰',
    color: '#8b5cf6',
  },
  duplicate: {
    label: '重复冲突',
    description: '多个策略发出相同的买入信号',
    icon: '📋',
    color: '#3b82f6',
  },
};

// 严重程度配置
export const SEVERITY_CONFIG: Record<
  ConflictSeverity,
  { label: string; color: string; bgColor: string; description: string }
> = {
  critical: {
    label: '严重',
    color: '#ef4444',
    bgColor: 'bg-red-500/10',
    description: '必须处理后才能继续执行',
  },
  warning: {
    label: '警告',
    color: '#f59e0b',
    bgColor: 'bg-yellow-500/10',
    description: '建议处理，可选择忽略',
  },
  info: {
    label: '提示',
    color: '#3b82f6',
    bgColor: 'bg-blue-500/10',
    description: '仅供参考，无需处理',
  },
};

// 解决方案配置
export const RESOLUTION_CONFIG: Record<
  ResolutionAction,
  { label: string; description: string; icon: string }
> = {
  execute_strategy_a: {
    label: '执行策略A',
    description: '执行第一个策略的信号，取消第二个',
    icon: '1️⃣',
  },
  execute_strategy_b: {
    label: '执行策略B',
    description: '执行第二个策略的信号，取消第一个',
    icon: '2️⃣',
  },
  execute_both: {
    label: '同时执行',
    description: '同时执行两个策略的信号',
    icon: '✅',
  },
  cancel_both: {
    label: '全部取消',
    description: '取消两个策略的信号',
    icon: '❌',
  },
  reduce_position: {
    label: '减仓执行',
    description: '减少执行数量以满足限制',
    icon: '📉',
  },
  delay_execution: {
    label: '延迟执行',
    description: '等待条件满足后再执行',
    icon: '⏳',
  },
  ignore: {
    label: '忽略',
    description: '忽略此冲突',
    icon: '🔇',
  },
};

// 状态配置
export const STATUS_CONFIG: Record<
  ConflictStatus,
  { label: string; color: string }
> = {
  pending: { label: '待处理', color: '#f59e0b' },
  resolved: { label: '已解决', color: '#22c55e' },
  ignored: { label: '已忽略', color: '#6b7280' },
  auto_resolved: { label: '自动解决', color: '#3b82f6' },
};

// 格式化时间
export function formatConflictTime(dateStr: string): string {
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);

  if (diffMins < 1) return '刚刚';
  if (diffMins < 60) return `${diffMins}分钟前`;
  if (diffMins < 1440) return `${Math.floor(diffMins / 60)}小时前`;
  return date.toLocaleDateString('zh-CN');
}

// 计算剩余时间
export function getRemainingTime(expiresAt: string): string {
  const expires = new Date(expiresAt);
  const now = new Date();
  const diffMs = expires.getTime() - now.getTime();

  if (diffMs <= 0) return '已过期';

  const diffMins = Math.floor(diffMs / 60000);
  if (diffMins < 60) return `${diffMins}分钟`;
  return `${Math.floor(diffMins / 60)}小时${diffMins % 60}分钟`;
}
