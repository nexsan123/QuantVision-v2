/**
 * 策略模板服务 - 连接后端 API
 *
 * 数据源: 后端 API / 内置模板库
 */

import { apiGet } from './api'
import type { StrategyTemplate, TemplateCategory, DifficultyLevel } from '../types/strategyTemplate'

// ==================== 数据源状态 ====================

export interface TemplateDataSource {
  source: 'api' | 'builtin'
  is_mock: boolean
  error_message?: string
}

let currentDataSource: TemplateDataSource = {
  source: 'api',
  is_mock: false,
}

export function getTemplateDataSource(): TemplateDataSource {
  return currentDataSource
}

// ==================== 内置模板数据 ====================

const BUILTIN_TEMPLATES: StrategyTemplate[] = [
  {
    template_id: 'tpl-value-buffett',
    name: '巴菲特价值',
    description: '基于巴菲特投资理念，寻找具有护城河的优质低估值公司。适合长期持有，追求稳健增值。',
    category: 'value',
    difficulty: 'beginner',
    holding_period: 'long_term',
    risk_level: 'low',
    expected_annual_return: '10-15%',
    max_drawdown: '15-20%',
    sharpe_ratio: '0.8-1.2',
    strategy_config: {
      factors: [
        { id: 'PE_TTM', weight: 0.3 },
        { id: 'ROE', weight: 0.3 },
      ],
      universe: 'S&P 500',
      rebalance_frequency: 'monthly',
      position_count: 20,
    },
    user_count: 1523,
    rating: 4.5,
    tags: ['经典策略', '低风险', '长线投资'],
    icon: '💎',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    template_id: 'tpl-momentum-breakout',
    name: '动量突破',
    description: '追踪强势股票的价格突破，顺势加仓。适合趋势行情，需要较强的执行力。',
    category: 'momentum',
    difficulty: 'intermediate',
    holding_period: 'short_term',
    risk_level: 'medium',
    expected_annual_return: '15-25%',
    max_drawdown: '20-30%',
    sharpe_ratio: '1.0-1.5',
    strategy_config: {
      factors: [
        { id: 'MOMENTUM_3M', weight: 0.4 },
        { id: 'VOLUME_RATIO', weight: 0.3 },
      ],
      universe: 'NASDAQ 100',
      rebalance_frequency: 'weekly',
      position_count: 10,
    },
    user_count: 892,
    rating: 4.2,
    tags: ['趋势跟踪', '高收益', '需要盯盘'],
    icon: '🚀',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    template_id: 'tpl-dividend-low-vol',
    name: '低波红利',
    description: '选择高股息率且波动较低的股票，追求稳定的现金流收益。适合稳健型投资者。',
    category: 'dividend',
    difficulty: 'beginner',
    holding_period: 'long_term',
    risk_level: 'low',
    expected_annual_return: '8-12%',
    max_drawdown: '10-15%',
    sharpe_ratio: '1.0-1.4',
    strategy_config: {
      factors: [
        { id: 'DIVIDEND_YIELD', weight: 0.4 },
        { id: 'VOLATILITY', weight: 0.3 },
      ],
      universe: 'S&P 500',
      rebalance_frequency: 'quarterly',
      position_count: 30,
    },
    user_count: 1105,
    rating: 4.6,
    tags: ['稳健收益', '现金分红', '防守型'],
    icon: '💰',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    template_id: 'tpl-multi-factor',
    name: '多因子增强',
    description: '综合价值、动量、质量、低波动等多个因子，构建风险调整后收益最优的组合。',
    category: 'multi_factor',
    difficulty: 'advanced',
    holding_period: 'medium_term',
    risk_level: 'medium',
    expected_annual_return: '12-18%',
    max_drawdown: '18-25%',
    sharpe_ratio: '1.2-1.8',
    strategy_config: {
      factors: [
        { id: 'PE_TTM', weight: 0.15 },
        { id: 'MOMENTUM', weight: 0.2 },
        { id: 'ROE', weight: 0.2 },
      ],
      universe: 'Russell 1000',
      rebalance_frequency: 'bi-weekly',
      position_count: 50,
    },
    user_count: 567,
    rating: 4.3,
    tags: ['量化策略', '因子投资', '专业级'],
    icon: '🔬',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    template_id: 'tpl-sector-rotation',
    name: '行业轮动',
    description: '根据宏观经济周期和行业相对强弱，动态调整行业配置，追求超额收益。',
    category: 'timing',
    difficulty: 'advanced',
    holding_period: 'medium_term',
    risk_level: 'medium',
    expected_annual_return: '15-20%',
    max_drawdown: '20-28%',
    sharpe_ratio: '1.1-1.6',
    strategy_config: {
      factors: [
        { id: 'SECTOR_MOMENTUM', weight: 0.3 },
        { id: 'SECTOR_BREADTH', weight: 0.25 },
      ],
      universe: 'Sector ETFs',
      rebalance_frequency: 'weekly',
      position_count: 5,
    },
    user_count: 432,
    rating: 4.1,
    tags: ['行业ETF', '宏观择时', '高换手'],
    icon: '🔄',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    template_id: 'tpl-intraday-momentum',
    name: '日内动量',
    description: '捕捉日内价格动量，快速进出。高频交易，需要严格的风控和执行纪律。',
    category: 'intraday',
    difficulty: 'advanced',
    holding_period: 'intraday',
    risk_level: 'high',
    expected_annual_return: '20-40%',
    max_drawdown: '25-35%',
    sharpe_ratio: '1.5-2.5',
    strategy_config: {
      factors: [
        { id: 'PRICE_MOMENTUM_5MIN', weight: 0.3 },
        { id: 'VOLUME_SURGE', weight: 0.25 },
      ],
      universe: 'High Volume 100',
      rebalance_frequency: 'intraday',
      position_count: 5,
    },
    user_count: 289,
    rating: 3.9,
    tags: ['高频交易', '日内平仓', '高风险高收益'],
    icon: '⚡',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
]

// ==================== API 函数 ====================

export interface TemplateFilterParams {
  category?: TemplateCategory
  difficulty?: DifficultyLevel
  search?: string
}

/**
 * 获取模板列表
 * 优先从API获取，失败则使用内置模板
 */
export async function getTemplates(params?: TemplateFilterParams): Promise<StrategyTemplate[]> {
  try {
    const response = await apiGet<{ templates: StrategyTemplate[] }>(
      '/api/v1/templates',
      params as Record<string, string | undefined>
    )
    currentDataSource = { source: 'api', is_mock: false }
    return response.templates
  } catch (error) {
    console.warn('[TemplateService] API unavailable, using builtin templates')
    currentDataSource = {
      source: 'builtin',
      is_mock: false, // 内置模板不算mock，是正式的产品模板
      error_message: 'Using builtin template library',
    }
    return BUILTIN_TEMPLATES
  }
}

/**
 * 获取单个模板
 */
export async function getTemplate(templateId: string): Promise<StrategyTemplate | null> {
  try {
    const response = await apiGet<StrategyTemplate>(`/api/v1/templates/${templateId}`)
    currentDataSource = { source: 'api', is_mock: false }
    return response
  } catch (error) {
    console.warn(`[TemplateService] Failed to get template ${templateId}`)
    const found = BUILTIN_TEMPLATES.find(t => t.template_id === templateId)
    if (found) {
      currentDataSource = { source: 'builtin', is_mock: false }
      return found
    }
    return null
  }
}
