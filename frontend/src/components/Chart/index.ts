/**
 * 图表组件导出
 * 包含 TradingView 交易图表和 ECharts 数据分析图表
 * Sprint 6: 增强 TradingView 集成
 */

// TradingView 交易图表
export { default as TradingViewChart } from './TradingViewChart'
export type { TimeFrame, ChartStyle, IndicatorConfig } from './TradingViewChart'

// 图表工具组件
export { default as ChartToolbar } from './ChartToolbar'
export { default as SignalOverlay } from './SignalOverlay'
export type { TradeSignal, PositionInfo } from './SignalOverlay'

// Sprint 6 新增组件
export { default as TimeframeSelector } from './TimeframeSelector'
export { default as IndicatorPanel } from './IndicatorPanel'

// 主题配置
export {
  DARK_THEME,
  LIGHT_THEME,
  PRO_DARK_THEME,
  DEFAULT_CHART_THEME,
  getChartTheme,
  toTradingViewOverrides,
} from './chartTheme'
export type { ChartThemeConfig } from './chartTheme'

// ECharts 数据分析图表
export { ReturnChart } from './ReturnChart'
export { HeatmapChart } from './HeatmapChart'
export { FactorICChart } from './FactorICChart'
export { GroupReturnChart } from './GroupReturnChart'
export { RiskRadarChart } from './RiskRadarChart'
export { PieChart } from './PieChart'
