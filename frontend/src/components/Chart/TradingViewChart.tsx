/**
 * TradingView 图表组件
 * PRD 4.16 实时交易监控界面
 * Sprint 6: 增强配置和功能
 */
import { useEffect, useRef, memo } from 'react'

// 时间框架类型
export type TimeFrame = '1' | '5' | '15' | '30' | '60' | '240' | 'D' | 'W' | 'M'

// 图表样式
export type ChartStyle = 'candles' | 'bars' | 'line' | 'area' | 'heikinashi'

// 指标配置
export interface IndicatorConfig {
  id: string
  name: string
  inputs?: Record<string, number | string>
}

interface TradingViewChartProps {
  symbol: string
  interval?: TimeFrame
  theme?: 'light' | 'dark'
  height?: number
  chartStyle?: ChartStyle
  indicators?: IndicatorConfig[]
  showToolbar?: boolean
  showDrawingTools?: boolean
  onSymbolChange?: (symbol: string) => void
  onIntervalChange?: (interval: TimeFrame) => void
  onReady?: () => void
}

// 图表样式映射
const CHART_STYLE_MAP: Record<ChartStyle, string> = {
  candles: '1',
  bars: '0',
  line: '2',
  area: '3',
  heikinashi: '8',
}

// 默认指标
const DEFAULT_INDICATORS: IndicatorConfig[] = [
  { id: 'MASimple@tv-basicstudies', name: 'MA 20', inputs: { length: 20 } },
  { id: 'RSI@tv-basicstudies', name: 'RSI', inputs: { length: 14 } },
  { id: 'MACD@tv-basicstudies', name: 'MACD' },
]

// TradingView Widget 类型声明
declare global {
  interface Window {
    TradingView: any
  }
}

function TradingViewChartComponent({
  symbol,
  interval = '15',
  theme = 'dark',
  height = 500,
  chartStyle = 'candles',
  indicators = DEFAULT_INDICATORS,
  showToolbar = true,
  showDrawingTools = true,
  onSymbolChange,
  onIntervalChange,
  onReady,
}: TradingViewChartProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const widgetRef = useRef<any>(null)
  const containerId = useRef(`tradingview_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`)
  const isReadyRef = useRef(false)

  // 初始化 TradingView Widget
  useEffect(() => {
    const initWidget = () => {
      if (!containerRef.current || !window.TradingView) return

      // 清理旧 widget
      if (widgetRef.current) {
        try {
          widgetRef.current.remove()
        } catch (e) {
          // 忽略清理错误
        }
      }

      // 构建指标 ID 列表
      const studyIds = indicators.map(ind => ind.id)

      // 根据主题选择背景色
      const bgColor = theme === 'dark' ? '#0a0a1a' : '#ffffff'
      const toolbarBg = theme === 'dark' ? '#0d0d1f' : '#f5f5f5'
      const gridColor = theme === 'dark' ? '#2a2a4a' : '#e0e0e0'
      const textColor = theme === 'dark' ? '#9ca3af' : '#333333'

      widgetRef.current = new window.TradingView.widget({
        container_id: containerId.current,
        symbol: symbol,
        interval: interval,
        timezone: 'America/New_York',
        theme: theme,
        style: CHART_STYLE_MAP[chartStyle], // 根据 chartStyle 设置
        locale: 'zh_CN',
        toolbar_bg: toolbarBg,
        enable_publishing: false,
        hide_side_toolbar: !showDrawingTools,
        hide_top_toolbar: !showToolbar,
        allow_symbol_change: true,
        save_image: false,
        height: height,
        width: '100%',
        autosize: false,

        // 自定义样式 - 根据主题动态调整
        overrides: {
          'mainSeriesProperties.candleStyle.upColor': '#22c55e',
          'mainSeriesProperties.candleStyle.downColor': '#ef4444',
          'mainSeriesProperties.candleStyle.borderUpColor': '#22c55e',
          'mainSeriesProperties.candleStyle.borderDownColor': '#ef4444',
          'mainSeriesProperties.candleStyle.wickUpColor': '#22c55e',
          'mainSeriesProperties.candleStyle.wickDownColor': '#ef4444',
          'paneProperties.background': bgColor,
          'paneProperties.vertGridProperties.color': gridColor,
          'paneProperties.horzGridProperties.color': gridColor,
          'scalesProperties.textColor': textColor,
        },

        // 禁用部分功能
        disabled_features: [
          'header_symbol_search',
          'header_compare',
          'header_undo_redo',
          'header_screenshot',
          'header_fullscreen_button',
        ],

        // 启用功能
        enabled_features: [
          'study_templates',
          'use_localstorage_for_settings',
        ],

        // 根据配置的指标加载
        studies: studyIds,
      })

      // 监听图表事件
      widgetRef.current.onChartReady(() => {
        isReadyRef.current = true
        const chart = widgetRef.current.activeChart()

        // 监听符号变化
        chart.onSymbolChanged().subscribe(null, (symbolInfo: any) => {
          onSymbolChange?.(symbolInfo.name)
        })

        // 监听时间周期变化
        chart.onIntervalChanged().subscribe(null, (newInterval: string) => {
          onIntervalChange?.(newInterval as TimeFrame)
        })

        // 触发就绪回调
        onReady?.()
      })
    }

    // 加载 TradingView 库
    if (window.TradingView) {
      initWidget()
    } else {
      const script = document.createElement('script')
      script.src = 'https://s3.tradingview.com/tv.js'
      script.async = true
      script.onload = initWidget
      document.head.appendChild(script)
    }

    return () => {
      if (widgetRef.current) {
        try {
          widgetRef.current.remove()
        } catch (e) {
          // 忽略清理错误
        }
        isReadyRef.current = false
      }
    }
  }, [symbol, interval, theme, height, chartStyle, indicators, showToolbar, showDrawingTools, onSymbolChange, onIntervalChange, onReady])

  // 符号或周期变化时更新 (只在 widget 就绪后)
  useEffect(() => {
    if (widgetRef.current && isReadyRef.current) {
      try {
        widgetRef.current.activeChart().setSymbol(symbol, interval)
      } catch (e) {
        // widget 可能还未就绪，忽略错误
      }
    }
  }, [symbol, interval])

  return (
    <div
      id={containerId.current}
      ref={containerRef}
      className="tradingview-container bg-dark-card rounded-lg overflow-hidden"
      style={{ height }}
    />
  )
}

export const TradingViewChart = memo(TradingViewChartComponent)
export default TradingViewChart
