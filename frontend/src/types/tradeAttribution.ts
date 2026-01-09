/**
 * 交易归因类型定义
 * PRD 4.5 交易归因系统
 */

// 交易方向
export type TradeSide = 'buy' | 'sell';

// 交易结果
export type TradeOutcome = 'win' | 'loss' | 'breakeven' | 'open';

// 市场情绪
export type MarketSentiment = 'bullish' | 'neutral' | 'bearish';

// 因子快照
export interface FactorSnapshot {
  factor_id: string;
  factor_name: string;
  factor_value: number;
  factor_rank: number;
  signal_contribution: number;
}

// 市场快照
export interface MarketSnapshot {
  market_index: number;
  market_change_1d: number;
  market_change_5d: number;
  vix: number;
  sector_rank: number;
  market_sentiment: MarketSentiment;
}

// 交易记录
export interface TradeRecord {
  trade_id: string;
  strategy_id: string;
  strategy_name: string;
  deployment_id: string;
  symbol: string;
  side: TradeSide;
  quantity: number;
  entry_price: number;
  entry_time: string;
  exit_price?: number;
  exit_time?: string;
  pnl?: number;
  pnl_pct?: number;
  outcome: TradeOutcome;
  factor_snapshot: FactorSnapshot[];
  market_snapshot?: MarketSnapshot;
  hold_days?: number;
  created_at: string;
  updated_at: string;
}

// 归因因子
export interface AttributionFactor {
  factor_name: string;
  contribution: number;
  contribution_pct: number;
  is_positive: boolean;
}

// 归因报告
export interface AttributionReport {
  report_id: string;
  strategy_id: string;
  strategy_name: string;
  period_start: string;
  period_end: string;
  total_trades: number;
  win_trades: number;
  loss_trades: number;
  win_rate: number;
  total_pnl: number;
  total_pnl_pct: number;
  avg_win: number;
  avg_loss: number;
  profit_factor: number;
  factor_attributions: AttributionFactor[];
  market_attribution: number;
  alpha_attribution: number;
  best_market_condition: string;
  worst_market_condition: string;
  patterns: string[];
  created_at: string;
  trigger_reason: string;
}

// AI诊断
export interface AIDiagnosis {
  diagnosis_id: string;
  report_id: string;
  summary: string;
  strengths: string[];
  weaknesses: string[];
  suggestions: string[];
  risk_alerts: string[];
  confidence: number;
  created_at: string;
}

// 策略归因摘要
export interface AttributionSummary {
  strategy_id: string;
  total_trades: number;
  win_rate: number;
  profit_factor: number;
  top_factors: { name: string; contribution: number }[];
  has_reports: boolean;
  latest_report_id?: string;
}

// 交易结果配置
export const TRADE_OUTCOME_CONFIG: Record<
  TradeOutcome,
  { label: string; color: string; bgColor: string }
> = {
  win: { label: '盈利', color: '#22c55e', bgColor: 'bg-green-500/10' },
  loss: { label: '亏损', color: '#ef4444', bgColor: 'bg-red-500/10' },
  breakeven: { label: '持平', color: '#6b7280', bgColor: 'bg-gray-500/10' },
  open: { label: '持仓中', color: '#3b82f6', bgColor: 'bg-blue-500/10' },
};

// 交易方向配置
export const TRADE_SIDE_CONFIG: Record<TradeSide, { label: string; color: string }> = {
  buy: { label: '买入', color: '#22c55e' },
  sell: { label: '卖出', color: '#ef4444' },
};

// 市场情绪配置
export const MARKET_SENTIMENT_CONFIG: Record<
  MarketSentiment,
  { label: string; color: string; icon: string }
> = {
  bullish: { label: '看涨', color: '#22c55e', icon: '📈' },
  neutral: { label: '中性', color: '#6b7280', icon: '➡️' },
  bearish: { label: '看跌', color: '#ef4444', icon: '📉' },
};

// 格式化金额
export function formatMoney(value: number): string {
  const absValue = Math.abs(value);
  const sign = value >= 0 ? '+' : '-';
  if (absValue >= 10000) {
    return `${sign}$${(absValue / 1000).toFixed(1)}K`;
  }
  return `${sign}$${absValue.toFixed(2)}`;
}

// 格式化百分比
export function formatPercent(value: number, decimals: number = 2): string {
  const sign = value >= 0 ? '+' : '';
  return `${sign}${(value * 100).toFixed(decimals)}%`;
}

// 格式化日期
export function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  });
}

// 格式化日期时间
export function formatDateTime(dateStr: string): string {
  return new Date(dateStr).toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}
