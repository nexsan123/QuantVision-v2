/**
 * 风险预警类型定义
 * PRD 4.14
 */

// 预警类型
export type AlertType =
  | 'daily_loss'
  | 'max_drawdown'
  | 'concentration'
  | 'vix_high'
  | 'conflict_pending'
  | 'system_error'
  | 'pdt_warning';

// 预警严重级别
export type AlertSeverity = 'info' | 'warning' | 'critical';

// 风险预警
export interface RiskAlert {
  alertId: string;
  userId: string;
  strategyId?: string;
  alertType: AlertType;
  severity: AlertSeverity;
  title: string;
  message: string;
  details?: Record<string, unknown>;
  isRead: boolean;
  isSent: boolean;
  createdAt: string;
  sentAt?: string;
}

// 预警配置
export interface AlertConfig {
  userId: string;
  enabled: boolean;
  dailyLossThreshold: number;
  maxDrawdownThreshold: number;
  concentrationThreshold: number;
  vixThreshold: number;
  emailEnabled: boolean;
  emailAddress?: string;
  quietHoursStart?: number;
  quietHoursEnd?: number;
}

// 预警列表响应
export interface AlertListResponse {
  total: number;
  alerts: RiskAlert[];
  unreadCount: number;
}

// 预警严重级别配置
export const ALERT_SEVERITY_CONFIG: Record<AlertSeverity, {
  icon: string;
  color: string;
  bgColor: string;
  borderColor: string;
}> = {
  info: {
    icon: 'ℹ️',
    color: '#3b82f6',
    bgColor: 'bg-blue-500/10',
    borderColor: 'border-blue-500',
  },
  warning: {
    icon: '⚠️',
    color: '#eab308',
    bgColor: 'bg-yellow-500/10',
    borderColor: 'border-yellow-500',
  },
  critical: {
    icon: '🔴',
    color: '#ef4444',
    bgColor: 'bg-red-500/10',
    borderColor: 'border-red-500',
  },
};

// 预警类型配置
export const ALERT_TYPE_CONFIG: Record<AlertType, {
  label: string;
  icon: string;
}> = {
  daily_loss: { label: '单日亏损', icon: '📉' },
  max_drawdown: { label: '最大回撤', icon: '📊' },
  concentration: { label: '持仓集中', icon: '⚖️' },
  vix_high: { label: 'VIX波动', icon: '📈' },
  conflict_pending: { label: '策略冲突', icon: '⚡' },
  system_error: { label: '系统异常', icon: '🔧' },
  pdt_warning: { label: 'PDT警告', icon: '🚫' },
};

// 格式化预警时间
export function formatAlertTime(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return '刚刚';
  if (diffMins < 60) return `${diffMins}分钟前`;
  if (diffHours < 24) return `${diffHours}小时前`;
  if (diffDays < 7) return `${diffDays}天前`;

  return date.toLocaleDateString('zh-CN');
}
