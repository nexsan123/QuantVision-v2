/**
 * PDT (Pattern Day Trader) 类型定义
 * PRD 4.7
 */

// 日内交易记录
export interface DayTradeRecord {
  tradeId: string;
  symbol: string;
  buyTime: string;
  sellTime: string;
  pnl: number;
  expiresAt: string;
}

// PDT 状态
export interface PDTStatus {
  accountId: string;
  accountBalance: number;
  isPdtRestricted: boolean;
  remainingDayTrades: number;
  maxDayTrades: number;
  rollingDays: number;
  isBlocked: boolean;
  blockedUntil?: string;
  resetAt: string;
  recentDayTrades: DayTradeRecord[];
}

// PDT 警告级别
export type PDTWarningLevel = 'none' | 'warning' | 'danger';

// 获取 PDT 警告级别
export function getPDTWarningLevel(remaining: number): PDTWarningLevel {
  if (remaining >= 2) return 'none';
  if (remaining === 1) return 'warning';
  return 'danger';
}

// PDT 警告级别配置
export const PDT_WARNING_CONFIG: Record<PDTWarningLevel, {
  color: string;
  bgColor: string;
  text: string;
}> = {
  none: {
    color: '#22c55e',
    bgColor: 'bg-green-500/20',
    text: '正常',
  },
  warning: {
    color: '#eab308',
    bgColor: 'bg-yellow-500/20',
    text: '注意',
  },
  danger: {
    color: '#ef4444',
    bgColor: 'bg-red-500/20',
    text: '已达限制',
  },
};

// 格式化 PDT 阈值金额
export function formatPDTThreshold(amount: number = 25000): string {
  return `$${amount.toLocaleString()}`;
}
