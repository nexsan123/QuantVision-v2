/**
 * 策略模板类型定义
 * PRD 4.13 策略模板库
 */

// 模板分类
export type TemplateCategory =
  | 'value'
  | 'momentum'
  | 'dividend'
  | 'multi_factor'
  | 'timing'
  | 'intraday';

// 难度等级
export type DifficultyLevel = 'beginner' | 'intermediate' | 'advanced';

// 持仓周期
export type HoldingPeriod = 'intraday' | 'short_term' | 'medium_term' | 'long_term';

// 风险等级
export type RiskLevel = 'low' | 'medium' | 'high';

// 策略模板
export interface StrategyTemplate {
  template_id: string;
  name: string;
  description: string;
  category: TemplateCategory;
  difficulty: DifficultyLevel;
  holding_period: HoldingPeriod;
  risk_level: RiskLevel;
  expected_annual_return: string;
  max_drawdown: string;
  sharpe_ratio: string;
  strategy_config: Record<string, any>;
  user_count: number;
  rating: number;
  tags: string[];
  icon: string;
  created_at: string;
  updated_at: string;
}

// 模板部署请求
export interface TemplateDeployRequest {
  template_id: string;
  strategy_name: string;
  initial_capital?: number;
}

// 模板部署结果
export interface TemplateDeployResult {
  strategy_id: string;
  strategy_name: string;
  template_id: string;
  template_name: string;
  created_at: string;
  message: string;
}

// 分类配置
export const CATEGORY_CONFIG: Record<
  TemplateCategory,
  { label: string; icon: string; color: string; description: string }
> = {
  value: {
    label: '价值投资',
    icon: '💎',
    color: '#3b82f6',
    description: '基于基本面分析，寻找被低估的优质股票',
  },
  momentum: {
    label: '动量趋势',
    icon: '🚀',
    color: '#22c55e',
    description: '追踪价格趋势，顺势而为',
  },
  dividend: {
    label: '红利收益',
    icon: '💰',
    color: '#f59e0b',
    description: '追求稳定分红收益的防守型策略',
  },
  multi_factor: {
    label: '多因子',
    icon: '🔬',
    color: '#8b5cf6',
    description: '综合多个因子进行量化选股',
  },
  timing: {
    label: '择时轮动',
    icon: '🔄',
    color: '#ec4899',
    description: '根据市场环境切换行业/风格配置',
  },
  intraday: {
    label: '日内交易',
    icon: '⚡',
    color: '#ef4444',
    description: '日内短线交易，当日完成买卖',
  },
};

// 难度配置
export const DIFFICULTY_CONFIG: Record<
  DifficultyLevel,
  { label: string; stars: number; color: string; description: string }
> = {
  beginner: {
    label: '入门',
    stars: 1,
    color: '#22c55e',
    description: '适合新手，规则简单易懂',
  },
  intermediate: {
    label: '进阶',
    stars: 2,
    color: '#f59e0b',
    description: '需要一定投资经验',
  },
  advanced: {
    label: '专业',
    stars: 3,
    color: '#ef4444',
    description: '适合专业投资者',
  },
};

// 持仓周期配置
export const HOLDING_PERIOD_CONFIG: Record<
  HoldingPeriod,
  { label: string; description: string }
> = {
  intraday: { label: '日内', description: '当日买入当日卖出' },
  short_term: { label: '短线', description: '持仓1-5天' },
  medium_term: { label: '中线', description: '持仓5-30天' },
  long_term: { label: '长线', description: '持仓30天以上' },
};

// 风险等级配置
export const RISK_LEVEL_CONFIG: Record<
  RiskLevel,
  { label: string; color: string; description: string }
> = {
  low: { label: '低', color: '#22c55e', description: '波动较小，回撤可控' },
  medium: { label: '中', color: '#f59e0b', description: '波动适中，风险可接受' },
  high: { label: '高', color: '#ef4444', description: '波动较大，可能有较大回撤' },
};

// 生成难度星级
export function generateDifficultyStars(difficulty: DifficultyLevel): string {
  const config = DIFFICULTY_CONFIG[difficulty];
  return '⭐'.repeat(config.stars);
}

// 格式化用户数量
export function formatUserCount(count: number): string {
  if (count >= 1000) {
    return `${(count / 1000).toFixed(1)}K`;
  }
  return count.toString();
}
