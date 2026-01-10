/**
 * 风险服务 - 连接后端风险管理 API
 * Phase 4: 前后端集成
 */

import { apiGet, apiPost } from './api'

// ==================== 类型定义 ====================

export interface VaRResult {
  var: number
  cvar: number
  varPct: number
  confidenceLevel: number
  horizonDays: number
  method: string
}

export interface VaRRequest {
  returns: number[]
  confidenceLevel?: number
  method?: 'historical' | 'parametric' | 'monte_carlo' | 'cornish_fisher' | 'ewma'
  horizonDays?: number
  portfolioValue?: number
}

export interface StressTestScenario {
  name: string
  displayName: string
  description: string
  marketShock: number
  volatilityShock: number
}

export interface StressTestResult {
  scenarioName: string
  portfolioLossPct: number
  portfolioLossAmount: number
  varStressed: number
  maxDrawdownStressed: number
  recoveryDays: number
  marketContribution: number
  sectorContribution: number
}

export interface CircuitBreakerStatus {
  state: 'CLOSED' | 'OPEN' | 'HALF_OPEN'
  isTripped: boolean
  canTrade: boolean
  triggerReason: string | null
  triggeredAt: string | null
  consecutiveLosses: number
  dailyPnl: number
}

export interface RiskAlert {
  timestamp: string
  level: 'info' | 'warning' | 'critical' | 'emergency'
  metricType: string
  message: string
  currentValue: number
  threshold: number
}

export interface RiskScore {
  riskScore: number
  riskLevel: 'low' | 'medium' | 'high'
  activeAlerts: number
  currentDrawdown: number
  currentVolatility: number
}

export interface RiskMonitorStatus {
  isRunning: boolean
  lastCheck: string
  activeAlertsCount: number
  currentDrawdown: number
  currentVolatility: number
  circuitBreakerState: string
}

// ==================== API 端点 ====================

const API_PREFIX = '/api/v1/risk'

/**
 * 计算 VaR
 */
export async function calculateVaR(request: VaRRequest): Promise<VaRResult> {
  const response = await apiPost<{
    var: number
    cvar: number
    var_pct: number
    confidence_level: number
    horizon_days: number
    method: string
  }>(`${API_PREFIX}/var`, {
    returns: request.returns,
    confidence_level: request.confidenceLevel || 0.95,
    method: request.method || 'historical',
    horizon_days: request.horizonDays || 1,
    portfolio_value: request.portfolioValue || 1.0,
  })

  return {
    var: response.var,
    cvar: response.cvar,
    varPct: response.var_pct,
    confidenceLevel: response.confidence_level,
    horizonDays: response.horizon_days,
    method: response.method,
  }
}

/**
 * 获取压力测试情景列表
 */
export async function getStressTestScenarios(): Promise<StressTestScenario[]> {
  const response = await apiGet<Array<{
    name: string
    display_name: string
    description: string
    market_shock: number
    volatility_shock: number
  }>>(`${API_PREFIX}/stress-test/scenarios`)

  return response.map(s => ({
    name: s.name,
    displayName: s.display_name,
    description: s.description,
    marketShock: s.market_shock,
    volatilityShock: s.volatility_shock,
  }))
}

/**
 * 运行压力测试
 */
export async function runStressTest(params: {
  holdings: Record<string, number>
  scenario: string
  portfolioValue?: number
  assetBetas?: Record<string, number>
  assetSectors?: Record<string, string>
}): Promise<StressTestResult> {
  const response = await apiPost<{
    scenario_name: string
    portfolio_loss_pct: number
    portfolio_loss_amount: number
    var_stressed: number
    max_drawdown_stressed: number
    recovery_days: number
    market_contribution: number
    sector_contribution: number
  }>(`${API_PREFIX}/stress-test`, {
    holdings: params.holdings,
    scenario: params.scenario,
    portfolio_value: params.portfolioValue || 1000000,
    asset_betas: params.assetBetas,
    asset_sectors: params.assetSectors,
  })

  return {
    scenarioName: response.scenario_name,
    portfolioLossPct: response.portfolio_loss_pct,
    portfolioLossAmount: response.portfolio_loss_amount,
    varStressed: response.var_stressed,
    maxDrawdownStressed: response.max_drawdown_stressed,
    recoveryDays: response.recovery_days,
    marketContribution: response.market_contribution,
    sectorContribution: response.sector_contribution,
  }
}

/**
 * 获取熔断器状态
 */
export async function getCircuitBreakerStatus(): Promise<CircuitBreakerStatus> {
  const response = await apiGet<{
    state: string
    is_tripped: boolean
    can_trade: boolean
    trigger_reason: string | null
    triggered_at: string | null
    consecutive_losses: number
    daily_pnl: number
  }>(`${API_PREFIX}/circuit-breaker`)

  return {
    state: response.state as CircuitBreakerStatus['state'],
    isTripped: response.is_tripped,
    canTrade: response.can_trade,
    triggerReason: response.trigger_reason,
    triggeredAt: response.triggered_at,
    consecutiveLosses: response.consecutive_losses,
    dailyPnl: response.daily_pnl,
  }
}

/**
 * 触发熔断
 */
export async function triggerCircuitBreaker(reason?: string): Promise<CircuitBreakerStatus> {
  const url = reason
    ? `${API_PREFIX}/circuit-breaker/trigger?reason=${encodeURIComponent(reason)}`
    : `${API_PREFIX}/circuit-breaker/trigger?reason=${encodeURIComponent('手动触发')}`

  const response = await apiPost<{
    state: string
    is_tripped: boolean
    can_trade: boolean
    trigger_reason: string | null
    triggered_at: string | null
    consecutive_losses: number
    daily_pnl: number
  }>(url, {})

  return {
    state: response.state as CircuitBreakerStatus['state'],
    isTripped: response.is_tripped,
    canTrade: response.can_trade,
    triggerReason: response.trigger_reason,
    triggeredAt: response.triggered_at,
    consecutiveLosses: response.consecutive_losses,
    dailyPnl: response.daily_pnl,
  }
}

/**
 * 重置熔断器
 */
export async function resetCircuitBreaker(): Promise<CircuitBreakerStatus> {
  const response = await apiPost<{
    state: string
    is_tripped: boolean
    can_trade: boolean
    trigger_reason: string | null
    triggered_at: string | null
    consecutive_losses: number
    daily_pnl: number
  }>(`${API_PREFIX}/circuit-breaker/reset`, {})

  return {
    state: response.state as CircuitBreakerStatus['state'],
    isTripped: response.is_tripped,
    canTrade: response.can_trade,
    triggerReason: response.trigger_reason,
    triggeredAt: response.triggered_at,
    consecutiveLosses: response.consecutive_losses,
    dailyPnl: response.daily_pnl,
  }
}

/**
 * 获取风险监控状态
 */
export async function getRiskMonitorStatus(): Promise<RiskMonitorStatus> {
  const response = await apiGet<{
    is_running: boolean
    last_check: string
    active_alerts_count: number
    current_drawdown: number
    current_volatility: number
    circuit_breaker_state: string
  }>(`${API_PREFIX}/monitor/status`)

  return {
    isRunning: response.is_running,
    lastCheck: response.last_check,
    activeAlertsCount: response.active_alerts_count,
    currentDrawdown: response.current_drawdown,
    currentVolatility: response.current_volatility,
    circuitBreakerState: response.circuit_breaker_state,
  }
}

/**
 * 获取风险警报
 */
export async function getRiskAlerts(params?: {
  level?: 'info' | 'warning' | 'critical' | 'emergency'
  sinceHours?: number
}): Promise<RiskAlert[]> {
  const queryParams = new URLSearchParams()
  if (params?.level) queryParams.append('level', params.level)
  if (params?.sinceHours) queryParams.append('since_hours', String(params.sinceHours))

  const query = queryParams.toString()
  const url = query ? `${API_PREFIX}/monitor/alerts?${query}` : `${API_PREFIX}/monitor/alerts`

  const response = await apiGet<Array<{
    timestamp: string
    level: string
    metric_type: string
    message: string
    current_value: number
    threshold: number
  }>>(url)

  return response.map(a => ({
    timestamp: a.timestamp,
    level: a.level as RiskAlert['level'],
    metricType: a.metric_type,
    message: a.message,
    currentValue: a.current_value,
    threshold: a.threshold,
  }))
}

/**
 * 获取风险评分
 */
export async function getRiskScore(): Promise<RiskScore> {
  const response = await apiGet<{
    risk_score: number
    risk_level: string
    active_alerts: number
    current_drawdown: number
    current_volatility: number
  }>(`${API_PREFIX}/monitor/score`)

  return {
    riskScore: response.risk_score,
    riskLevel: response.risk_level as RiskScore['riskLevel'],
    activeAlerts: response.active_alerts,
    currentDrawdown: response.current_drawdown,
    currentVolatility: response.current_volatility,
  }
}
