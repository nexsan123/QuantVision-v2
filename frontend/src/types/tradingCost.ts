/**
 * 交易成本类型定义
 * PRD 4.4 交易成本配置
 */

// 成本模式
export type CostMode = 'simple' | 'professional';

// 市值分类
export type MarketCap = 'large' | 'mid' | 'small';

// 滑点配置
export interface SlippageConfig {
  large_cap: number;
  mid_cap: number;
  small_cap: number;
}

// 市场冲击配置
export interface MarketImpactConfig {
  impact_coefficient: number;
  enabled: boolean;
}

// 成本配置
export interface TradingCostConfig {
  config_id: string;
  user_id: string;
  mode: CostMode;
  commission_per_share: number;
  sec_fee_rate: number;
  taf_fee_per_share: number;
  simple_slippage: number;
  slippage?: SlippageConfig;
  market_impact?: MarketImpactConfig;
  cost_buffer: number;
}

// 成本估算请求
export interface CostEstimateRequest {
  symbol: string;
  quantity: number;
  price: number;
  side: 'buy' | 'sell';
  market_cap?: MarketCap;
  daily_volume?: number;
  volatility?: number;
}

// 成本估算结果
export interface CostEstimateResult {
  symbol: string;
  side: string;
  quantity: number;
  price: number;
  trade_value: number;
  commission: number;
  sec_fee: number;
  taf_fee: number;
  slippage_cost: number;
  market_impact_cost: number;
  total_cost: number;
  total_cost_pct: number;
  cost_with_buffer: number;
  breakdown: Record<string, any>;
}

// 成本配置更新
export interface CostConfigUpdate {
  mode?: CostMode;
  commission_per_share?: number;
  simple_slippage?: number;
  slippage?: SlippageConfig;
  market_impact?: MarketImpactConfig;
  cost_buffer?: number;
}

// 默认配置
export const DEFAULT_COST_CONFIG = {
  simple: {
    commission_per_share: 0.005,
    simple_slippage: 0.001,
    cost_buffer: 0.2,
  },
  professional: {
    commission_per_share: 0.005,
    slippage: {
      large_cap: 0.0005,
      mid_cap: 0.001,
      small_cap: 0.0025,
    },
    market_impact: {
      impact_coefficient: 0.1,
      enabled: true,
    },
    cost_buffer: 0.15,
  },
};

// 最低限制
export const COST_MINIMUMS = {
  commission_per_share: 0.003,
  slippage_large_cap: 0.0002,
  slippage_mid_cap: 0.0005,
  slippage_small_cap: 0.0015,
};

// 模式配置
export const COST_MODE_CONFIG: Record<CostMode, { label: string; description: string }> = {
  simple: {
    label: '简单模式',
    description: '适合新手，使用固定滑点比例',
  },
  professional: {
    label: '专业模式',
    description: '按市值分类设置滑点，支持市场冲击模型',
  },
};

// 市值配置
export const MARKET_CAP_CONFIG: Record<MarketCap, { label: string; description: string }> = {
  large: { label: '大盘股', description: '市值 > $10B' },
  mid: { label: '中盘股', description: '市值 $2B - $10B' },
  small: { label: '小盘股', description: '市值 < $2B' },
};

// 格式化百分比
export function formatCostPercent(value: number, decimals: number = 2): string {
  return `${(value * 100).toFixed(decimals)}%`;
}

// 格式化金额
export function formatCostMoney(value: number): string {
  return `$${value.toFixed(4)}`;
}
