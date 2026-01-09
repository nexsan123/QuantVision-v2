/**
 * 因子有效性验证类型定义
 * PRD 4.3 因子有效性验证
 */

// 有效性等级
export type EffectivenessLevel = 'strong' | 'medium' | 'weak' | 'ineffective';

// IC 统计
export interface ICStatistics {
  icMean: number;
  icStd: number;
  icIr: number;
  icPositiveRatio: number;
  icSeries: number[];
  icDates: string[];
}

// 收益统计
export interface ReturnStatistics {
  groupReturns: number[];
  groupLabels: string[];
  longShortSpread: number;
  topGroupSharpe: number;
  bottomGroupSharpe: number;
}

// 因子验证结果
export interface FactorValidationResult {
  factorId: string;
  factorName: string;
  factorCategory: string;
  plainDescription: string;
  investmentLogic: string;
  icStats: ICStatistics;
  returnStats: ReturnStatistics;
  isEffective: boolean;
  effectivenessLevel: EffectivenessLevel;
  effectivenessScore: number;
  suggestedCombinations: string[];
  usageTips: string[];
  riskWarnings: string[];
  validationDate: string;
  dataPeriod: string;
  sampleSize: number;
}

// 因子组合建议
export interface FactorSuggestion {
  factorId: string;
  factorName: string;
  suggestionReason: string;
  expectedImprovement: number;
  correlation: number;
}

// 因子对比结果
export interface FactorCompareResult {
  factors: FactorValidationResult[];
  correlationMatrix: number[][];
  bestCombination: string[];
  combinationScore: number;
}

// 有效性等级配置
export const EFFECTIVENESS_LEVEL_CONFIG: Record<
  EffectivenessLevel,
  {
    label: string;
    stars: number;
    color: string;
    bgColor: string;
    description: string;
  }
> = {
  strong: {
    label: '强',
    stars: 5,
    color: '#22c55e',
    bgColor: 'bg-green-500/10',
    description: '该因子表现优异，可作为主要选股依据',
  },
  medium: {
    label: '中',
    stars: 3,
    color: '#3b82f6',
    bgColor: 'bg-blue-500/10',
    description: '该因子表现中等，建议与其他因子组合使用',
  },
  weak: {
    label: '弱',
    stars: 1,
    color: '#eab308',
    bgColor: 'bg-yellow-500/10',
    description: '该因子表现较弱，仅作为辅助参考',
  },
  ineffective: {
    label: '无效',
    stars: 0,
    color: '#ef4444',
    bgColor: 'bg-red-500/10',
    description: '该因子无明显选股能力，不建议使用',
  },
};

// 因子类别配置
export const FACTOR_CATEGORY_CONFIG: Record<
  string,
  {
    label: string;
    icon: string;
    color: string;
  }
> = {
  value: { label: '价值因子', icon: '💰', color: '#f59e0b' },
  growth: { label: '成长因子', icon: '📈', color: '#10b981' },
  quality: { label: '质量因子', icon: '⭐', color: '#6366f1' },
  momentum: { label: '动量因子', icon: '🚀', color: '#ec4899' },
  volatility: { label: '波动因子', icon: '📊', color: '#8b5cf6' },
};

// 格式化百分比
export function formatPercent(value: number, decimals: number = 1): string {
  return `${(value * 100).toFixed(decimals)}%`;
}

// 生成星级
export function generateStars(count: number, max: number = 5): string {
  return '⭐'.repeat(count) + '☆'.repeat(max - count);
}
