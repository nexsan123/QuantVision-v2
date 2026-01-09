/**
 * 信号雷达类型定义
 * PRD 4.16.2
 */

// 信号类型
export type SignalType = 'buy' | 'sell' | 'hold';

// 信号强度
export type SignalStrength = 'strong' | 'medium' | 'weak';

// 信号状态
export type SignalStatus =
  | 'holding'      // 已持仓
  | 'buy_signal'   // 买入信号
  | 'sell_signal'  // 卖出信号
  | 'near_trigger' // 接近触发
  | 'monitoring'   // 监控中
  | 'excluded';    // 不符合条件

// 因子触发信息
export interface FactorTrigger {
  factorId: string;
  factorName: string;
  currentValue: number;
  threshold: number;
  direction: 'above' | 'below';
  nearTriggerPct: number;
  isSatisfied: boolean;
}

// 信号实体
export interface Signal {
  signalId: string;
  strategyId: string;
  symbol: string;
  companyName: string;
  signalType: SignalType;
  signalStrength: SignalStrength;
  signalScore: number;
  status: SignalStatus;
  triggeredFactors: FactorTrigger[];
  currentPrice: number;
  targetPrice?: number;
  stopLossPrice?: number;
  expectedReturnPct?: number;
  signalTime: string;
  expiresAt?: string;
  isHolding: boolean;
}

// 信号列表响应
export interface SignalListResponse {
  total: number;
  signals: Signal[];
  summary: {
    buy: number;
    sell: number;
    hold: number;
  };
}

// 股票搜索结果
export interface StockSearchResult {
  symbol: string;
  companyName: string;
  sector?: string;
  currentPrice: number;
  signalStatus?: SignalStatus;
  signalScore?: number;
}

// 状态分布统计
export interface StatusSummary {
  holding: number;
  buySignal: number;
  sellSignal: number;
  nearTrigger: number;
  monitoring: number;
  excluded: number;
}

// 信号类型配置
export const SIGNAL_TYPE_CONFIG: Record<SignalType, {
  label: string;
  color: string;
  bgColor: string;
  icon: string;
}> = {
  buy: { label: '买入', color: 'green', bgColor: 'bg-green-500', icon: '📈' },
  sell: { label: '卖出', color: 'red', bgColor: 'bg-red-500', icon: '📉' },
  hold: { label: '持有', color: 'blue', bgColor: 'bg-blue-500', icon: '⏸️' },
};

// 信号强度配置
export const SIGNAL_STRENGTH_CONFIG: Record<SignalStrength, {
  label: string;
  color: string;
  stars: number;
}> = {
  strong: { label: '强', color: 'green', stars: 3 },
  medium: { label: '中', color: 'orange', stars: 2 },
  weak: { label: '弱', color: 'gray', stars: 1 },
};

// 信号状态配置
export const SIGNAL_STATUS_CONFIG: Record<SignalStatus, {
  label: string;
  color: string;
  emoji: string;
}> = {
  holding: { label: '已持仓', color: 'red', emoji: '🔴' },
  buy_signal: { label: '买入信号', color: 'green', emoji: '🟢' },
  sell_signal: { label: '卖出信号', color: 'orange', emoji: '🟠' },
  near_trigger: { label: '接近触发', color: 'yellow', emoji: '🟡' },
  monitoring: { label: '监控中', color: 'gray', emoji: '⚪' },
  excluded: { label: '不符合', color: 'gray', emoji: '⚫' },
};

// 渲染星级
export function renderStars(count: number): string {
  return '⭐'.repeat(count);
}

// 格式化价格
export function formatPrice(price: number): string {
  return `$${price.toFixed(2)}`;
}

// 格式化百分比
export function formatPercent(value: number): string {
  const sign = value >= 0 ? '+' : '';
  return `${sign}${(value * 100).toFixed(2)}%`;
}
