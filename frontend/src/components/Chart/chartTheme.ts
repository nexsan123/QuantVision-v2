/**
 * TradingView 图表主题配置
 * Sprint 6: T4 - 图表主题同步
 */

export interface ChartThemeConfig {
  // 主要颜色
  upColor: string
  downColor: string
  backgroundColor: string
  gridColor: string
  textColor: string
  toolbarBg: string

  // 蜡烛图配置
  candleUpColor: string
  candleDownColor: string
  candleBorderUpColor: string
  candleBorderDownColor: string
  candleWickUpColor: string
  candleWickDownColor: string

  // 十字光标
  crosshairColor: string

  // 刻度
  scaleTextColor: string
  scaleLinesColor: string
}

// 深色主题
export const DARK_THEME: ChartThemeConfig = {
  upColor: '#22c55e',
  downColor: '#ef4444',
  backgroundColor: '#0a0a1a',
  gridColor: '#2a2a4a',
  textColor: '#9ca3af',
  toolbarBg: '#0d0d1f',

  candleUpColor: '#22c55e',
  candleDownColor: '#ef4444',
  candleBorderUpColor: '#22c55e',
  candleBorderDownColor: '#ef4444',
  candleWickUpColor: '#22c55e',
  candleWickDownColor: '#ef4444',

  crosshairColor: '#6b7280',

  scaleTextColor: '#9ca3af',
  scaleLinesColor: '#374151',
}

// 浅色主题
export const LIGHT_THEME: ChartThemeConfig = {
  upColor: '#16a34a',
  downColor: '#dc2626',
  backgroundColor: '#ffffff',
  gridColor: '#e5e7eb',
  textColor: '#374151',
  toolbarBg: '#f5f5f5',

  candleUpColor: '#16a34a',
  candleDownColor: '#dc2626',
  candleBorderUpColor: '#16a34a',
  candleBorderDownColor: '#dc2626',
  candleWickUpColor: '#16a34a',
  candleWickDownColor: '#dc2626',

  crosshairColor: '#9ca3af',

  scaleTextColor: '#374151',
  scaleLinesColor: '#d1d5db',
}

// 专业深色主题 (更暗)
export const PRO_DARK_THEME: ChartThemeConfig = {
  upColor: '#00d4aa',
  downColor: '#ff4757',
  backgroundColor: '#0d0d1f',
  gridColor: '#1a1a3a',
  textColor: '#8b92a5',
  toolbarBg: '#12122a',

  candleUpColor: '#00d4aa',
  candleDownColor: '#ff4757',
  candleBorderUpColor: '#00d4aa',
  candleBorderDownColor: '#ff4757',
  candleWickUpColor: '#00d4aa',
  candleWickDownColor: '#ff4757',

  crosshairColor: '#4a5568',

  scaleTextColor: '#8b92a5',
  scaleLinesColor: '#2d2d4a',
}

// 根据主题名称获取配置
export function getChartTheme(theme: 'light' | 'dark' | 'pro-dark' = 'dark'): ChartThemeConfig {
  switch (theme) {
    case 'light':
      return LIGHT_THEME
    case 'pro-dark':
      return PRO_DARK_THEME
    case 'dark':
    default:
      return DARK_THEME
  }
}

// 转换为 TradingView overrides 格式
export function toTradingViewOverrides(config: ChartThemeConfig): Record<string, string> {
  return {
    'mainSeriesProperties.candleStyle.upColor': config.candleUpColor,
    'mainSeriesProperties.candleStyle.downColor': config.candleDownColor,
    'mainSeriesProperties.candleStyle.borderUpColor': config.candleBorderUpColor,
    'mainSeriesProperties.candleStyle.borderDownColor': config.candleBorderDownColor,
    'mainSeriesProperties.candleStyle.wickUpColor': config.candleWickUpColor,
    'mainSeriesProperties.candleStyle.wickDownColor': config.candleWickDownColor,
    'paneProperties.background': config.backgroundColor,
    'paneProperties.vertGridProperties.color': config.gridColor,
    'paneProperties.horzGridProperties.color': config.gridColor,
    'paneProperties.crossHairProperties.color': config.crosshairColor,
    'scalesProperties.textColor': config.scaleTextColor,
    'scalesProperties.lineColor': config.scaleLinesColor,
  }
}

// 导出默认主题
export const DEFAULT_CHART_THEME = DARK_THEME
