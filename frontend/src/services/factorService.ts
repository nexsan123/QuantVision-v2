/**
 * 因子服务 - 连接后端 API
 * PRD 4.3: 因子有效性验证
 */

import { apiGet, apiPost, apiDelete } from './api'
import type { FactorValidationResult } from '../types/factorValidation'

// ==================== 类型定义 ====================

export interface Factor {
  id: string
  name: string
  description: string
  formula?: string
  code?: string
  category: string
  createdAt: string
  updatedAt: string
}

export interface FactorListResponse {
  factors: Factor[]
  total: number
}

export interface FactorCreateRequest {
  name: string
  description?: string
  formula?: string
  code?: string
  category: string
}

export interface ICAnalysisRequest {
  factorId?: string
  formula?: string
  startDate?: string
  endDate?: string
  universe?: string[]
}

export interface ICAnalysisResponse {
  icMean: number
  icStd: number
  icIr: number
  rankIcMean: number
  rankIcIr: number
  tStatistic: number
  pValue: number
  isSignificant: boolean
  icPositiveRatio: number
  icAbsGt2Ratio: number
  icDecay: number[]
  icSeries?: { date: string; value: number }[]
}

export interface GroupBacktestRequest {
  factorId?: string
  formula?: string
  groups?: number
  startDate?: string
  endDate?: string
}

export interface GroupBacktestResponse {
  monotonicity: number
  longShortReturn: number
  longShortSharpe: number
  groupStats: Record<string, {
    mean: number
    std: number
    sharpe: number
    winRate: number
  }>
  groupReturns?: number[]
  groupLabels?: string[]
}

export interface FactorCategory {
  name: string
  label: string
  description: string
  examples: string[]
}

// ==================== API 端点 ====================

const API_PREFIX = '/api/v1/factors'

// ==================== 响应转换 ====================

interface BackendFactor {
  id: string
  name: string
  description: string
  formula?: string
  code?: string
  category: string
  created_at: string
  updated_at: string
}

interface BackendICAnalysisResponse {
  ic_mean: number
  ic_std: number
  ic_ir: number
  rank_ic_mean: number
  rank_ic_ir: number
  t_statistic: number
  p_value: number
  is_significant: boolean
  ic_positive_ratio: number
  ic_abs_gt_2_ratio: number
  ic_decay: number[]
}

interface BackendGroupBacktestResponse {
  monotonicity: number
  long_short_return: number
  long_short_sharpe: number
  group_stats: Record<string, {
    mean: number
    std: number
    sharpe: number
    win_rate: number
  }>
}

function transformFactor(f: BackendFactor): Factor {
  return {
    id: f.id,
    name: f.name,
    description: f.description,
    formula: f.formula,
    code: f.code,
    category: f.category,
    createdAt: f.created_at,
    updatedAt: f.updated_at,
  }
}

// ==================== API 函数 ====================

/**
 * 获取因子列表
 */
export async function getFactors(category?: string): Promise<FactorListResponse> {
  const params = new URLSearchParams()
  if (category) params.append('category', category)

  const query = params.toString()
  const url = query ? `${API_PREFIX}?${query}` : API_PREFIX

  const response = await apiGet<{ factors: BackendFactor[]; total: number }>(url)

  return {
    factors: response.factors.map(transformFactor),
    total: response.total,
  }
}

/**
 * 获取单个因子
 */
export async function getFactor(factorId: string): Promise<Factor> {
  const response = await apiGet<{ data: BackendFactor }>(`${API_PREFIX}/${factorId}`)
  return transformFactor(response.data)
}

/**
 * 创建因子
 */
export async function createFactor(request: FactorCreateRequest): Promise<Factor> {
  const response = await apiPost<{ data: BackendFactor }>(`${API_PREFIX}`, request)
  return transformFactor(response.data)
}

/**
 * 删除因子
 */
export async function deleteFactor(factorId: string): Promise<void> {
  await apiDelete(`${API_PREFIX}/${factorId}`)
}

/**
 * IC 分析
 */
export async function analyzeIC(request: ICAnalysisRequest): Promise<ICAnalysisResponse> {
  const response = await apiPost<{ data: BackendICAnalysisResponse }>(
    `${API_PREFIX}/analyze/ic`,
    {
      factor_id: request.factorId,
      formula: request.formula,
      start_date: request.startDate,
      end_date: request.endDate,
      universe: request.universe,
    }
  )

  const r = response.data
  return {
    icMean: r.ic_mean,
    icStd: r.ic_std,
    icIr: r.ic_ir,
    rankIcMean: r.rank_ic_mean,
    rankIcIr: r.rank_ic_ir,
    tStatistic: r.t_statistic,
    pValue: r.p_value,
    isSignificant: r.is_significant,
    icPositiveRatio: r.ic_positive_ratio,
    icAbsGt2Ratio: r.ic_abs_gt_2_ratio,
    icDecay: r.ic_decay,
  }
}

/**
 * 分组回测
 */
export async function analyzeGroup(request: GroupBacktestRequest): Promise<GroupBacktestResponse> {
  const response = await apiPost<{ data: BackendGroupBacktestResponse }>(
    `${API_PREFIX}/analyze/group`,
    {
      factor_id: request.factorId,
      formula: request.formula,
      groups: request.groups,
      start_date: request.startDate,
      end_date: request.endDate,
    }
  )

  const r = response.data
  return {
    monotonicity: r.monotonicity,
    longShortReturn: r.long_short_return,
    longShortSharpe: r.long_short_sharpe,
    groupStats: Object.fromEntries(
      Object.entries(r.group_stats).map(([k, v]) => [k, {
        mean: v.mean,
        std: v.std,
        sharpe: v.sharpe,
        winRate: v.win_rate,
      }])
    ),
  }
}

/**
 * 获取可用算子列表
 */
export async function getOperators(): Promise<Record<string, string[]>> {
  const response = await apiGet<{ data: Record<string, string[]> }>(`${API_PREFIX}/operators`)
  return response.data
}

// ==================== 因子验证 API ====================

// 后端因子验证响应 (snake_case)
interface BackendFactorValidationResult {
  factor_id: string
  factor_name: string
  factor_category: string
  plain_description: string
  investment_logic: string
  ic_stats: {
    ic_mean: number
    ic_std: number
    ic_ir: number
    ic_positive_ratio: number
    ic_series: number[]
    ic_dates: string[]
  }
  return_stats: {
    group_returns: number[]
    group_labels: string[]
    long_short_spread: number
    top_group_sharpe: number
    bottom_group_sharpe: number
  }
  is_effective: boolean
  effectiveness_level: string
  effectiveness_score: number
  suggested_combinations: string[]
  usage_tips: string[]
  risk_warnings: string[]
  validation_date: string
  data_period: string
  sample_size: number
}

/**
 * 获取因子验证结果
 */
export async function getFactorValidation(factorId: string): Promise<FactorValidationResult> {
  const response = await apiGet<BackendFactorValidationResult>(`${API_PREFIX}/${factorId}/validation`)

  // 转换 snake_case 到 camelCase
  return {
    factorId: response.factor_id,
    factorName: response.factor_name,
    factorCategory: response.factor_category,
    plainDescription: response.plain_description,
    investmentLogic: response.investment_logic,
    icStats: {
      icMean: response.ic_stats.ic_mean,
      icStd: response.ic_stats.ic_std,
      icIr: response.ic_stats.ic_ir,
      icPositiveRatio: response.ic_stats.ic_positive_ratio,
      icSeries: response.ic_stats.ic_series || [],
      icDates: response.ic_stats.ic_dates || [],
    },
    returnStats: {
      groupReturns: response.return_stats.group_returns || [],
      groupLabels: response.return_stats.group_labels || [],
      longShortSpread: response.return_stats.long_short_spread,
      topGroupSharpe: response.return_stats.top_group_sharpe,
      bottomGroupSharpe: response.return_stats.bottom_group_sharpe,
    },
    isEffective: response.is_effective,
    effectivenessLevel: response.effectiveness_level as FactorValidationResult['effectivenessLevel'],
    effectivenessScore: response.effectiveness_score,
    suggestedCombinations: response.suggested_combinations || [],
    usageTips: response.usage_tips || [],
    riskWarnings: response.risk_warnings || [],
    validationDate: response.validation_date,
    dataPeriod: response.data_period,
    sampleSize: response.sample_size,
  }
}

/**
 * 触发因子验证
 */
export async function validateFactor(
  factorId: string,
  options?: {
    startDate?: string
    endDate?: string
    universe?: string
  }
): Promise<FactorValidationResult> {
  const params = new URLSearchParams()
  if (options?.startDate) params.append('start_date', options.startDate)
  if (options?.endDate) params.append('end_date', options.endDate)
  if (options?.universe) params.append('universe', options.universe)

  const query = params.toString()
  const url = query
    ? `${API_PREFIX}/${factorId}/validate?${query}`
    : `${API_PREFIX}/${factorId}/validate`

  return apiPost<FactorValidationResult>(url, {})
}

/**
 * 获取因子类别配置
 */
export async function getFactorCategories(): Promise<Record<string, FactorCategory>> {
  return apiGet<Record<string, FactorCategory>>(`${API_PREFIX}/categories`)
}

/**
 * 获取可用因子列表 (用于验证)
 */
export async function getAvailableFactors(): Promise<Array<{
  factorId: string
  factorName: string
  category: string
  description: string
}>> {
  return apiGet<Array<{
    factor_id: string
    factor_name: string
    category: string
    description: string
  }>>(`${API_PREFIX}/available`).then(data =>
    data.map(f => ({
      factorId: f.factor_id,
      factorName: f.factor_name,
      category: f.category,
      description: f.description,
    }))
  )
}
