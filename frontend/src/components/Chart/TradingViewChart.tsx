/**
 * TradingView 图表组件
 * PRD 4.16 实时交易监控界面
 * Sprint 6: 增强配置和功能
 *
 * v2.1 更新: 支持 autosize 模式，图表自动填满父容器
 */
import { useEffect, useRef, memo, useState } from 'react'
import { Spin, Alert, Button } from 'antd'
import { ReloadOutlined } from '@ant-design/icons'

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
  height?: number | string  // 支持数字或 '100%'
  autosize?: boolean        // 自动填满父容器
  chartStyle?: ChartStyle
  indicators?: IndicatorConfig[]
  showToolbar?: boolean
  showDrawingTools?: boolean
  onSymbolChange?: (symbol: string) => void
  onIntervalChange?: (interval: TimeFrame) => void
  onReady?: () => void
  className?: string        // 支持自定义样式
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
  autosize = true,  // 默认启用自适应
  chartStyle = 'candles',
  indicators = DEFAULT_INDICATORS,
  showToolbar = true,
  showDrawingTools = true,
  onSymbolChange,
  onIntervalChange,
  onReady,
  className = '',
}: TradingViewChartProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const widgetRef = useRef<any>(null)
  const containerId = useRef(`tradingview_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`)
  const isReadyRef = useRef(false)

  // 新增状态: 加载和错误处理
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // 初始化 TradingView Widget
  useEffect(() => {
    const initWidget = () => {
      if (!containerRef.current) return

      setLoading(true)
      setError(null)

      // 检查 TradingView 库是否加载
      if (!window.TradingView) {
        setError('TradingView 库加载失败')
        setLoading(false)
        return
      }

      // 清理旧 widget
      if (widgetRef.current) {
        try {
          widgetRef.current.remove()
        } catch (e) {
          console.warn('Widget cleanup warning:', e)
        }
      }

      // 构建指标 ID 列表
      const studyIds = indicators.map(ind => ind.id)

      // 根据主题选择背景色
      const bgColor = theme === 'dark' ? '#0a0a1a' : '#ffffff'
      const toolbarBg = theme === 'dark' ? '#0d0d1f' : '#f5f5f5'
      const gridColor = theme === 'dark' ? '#2a2a4a' : '#e0e0e0'
      const textColor = theme === 'dark' ? '#9ca3af' : '#333333'

      try {
        // 配置对象 - 根据 autosize 决定尺寸策略
        const widgetConfig: any = {
          container_id: containerId.current,
          symbol: symbol,
          interval: interval,
          timezone: 'America/New_York',
          theme: theme,
          style: CHART_STYLE_MAP[chartStyle],
          locale: 'zh_CN',
          toolbar_bg: toolbarBg,
          enable_publishing: false,
          hide_side_toolbar: !showDrawingTools,
          hide_top_toolbar: !showToolbar,
          allow_symbol_change: true,
          save_image: false,
          autosize: autosize,  // 自适应模式

          // 自定义样式
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

          // 指标
          studies: studyIds,
        }

        // 非自适应模式时设置固定尺寸
        if (!autosize) {
          widgetConfig.height = typeof height === 'number' ? height : 500
          widgetConfig.width = '100%'
        }

        widgetRef.current = new window.TradingView.widget(widgetConfig)

        // 轻量级 widget 使用 iframe，等待加载完成
        // 注意: tv.js 轻量级 widget 不支持完整的 onChartReady API
        if (typeof widgetRef.current.onChartReady === 'function') {
          // 高级图表库支持 onChartReady
          widgetRef.current.onChartReady(() => {
            isReadyRef.current = true
            setLoading(false)

            try {
              const chart = widgetRef.current.activeChart()

              // 监听符号变化
              chart.onSymbolChanged().subscribe(null, (symbolInfo: any) => {
                onSymbolChange?.(symbolInfo.name)
              })

              // 监听时间周期变化
              chart.onIntervalChanged().subscribe(null, (newInterval: string) => {
                onIntervalChange?.(newInterval as TimeFrame)
              })
            } catch (e) {
              console.warn('Chart event binding failed:', e)
            }

            // 触发就绪回调
            onReady?.()
          })
        } else {
          // 轻量级 widget 使用 iframe onload 事件
          // 设置一个短延迟来确保 iframe 加载完成
          setTimeout(() => {
            isReadyRef.current = true
            setLoading(false)
            onReady?.()
          }, 1500)
        }
      } catch (err) {
        console.error('TradingView init error:', err)
        setError(err instanceof Error ? err.message : '图表初始化失败')
        setLoading(false)
      }
    }

    // 加载 TradingView 库
    if (window.TradingView) {
      initWidget()
    } else {
      const script = document.createElement('script')
      script.src = 'https://s3.tradingview.com/tv.js'
      script.async = true
      script.onload = initWidget
      script.onerror = () => {
        setError('无法加载 TradingView 库')
        setLoading(false)
      }
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
  }, [symbol, interval, theme, height, autosize, chartStyle, indicators, showToolbar, showDrawingTools, onSymbolChange, onIntervalChange, onReady])

  // 重试加载
  const handleRetry = () => {
    setError(null)
    setLoading(true)
    // 触发重新初始化
    if (widgetRef.current) {
      try {
        widgetRef.current.remove()
      } catch (e) { /* ignore */ }
      widgetRef.current = null
    }
    // 强制重新加载
    window.location.reload()
  }

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

  // 计算容器样式
  const containerStyle: React.CSSProperties = autosize
    ? { width: '100%', height: '100%', minHeight: 300 }
    : { width: '100%', height: typeof height === 'number' ? height : height }

  // 错误状态渲染
  if (error) {
    return (
      <div
        className={`h-full flex items-center justify-center bg-dark-card rounded-lg ${className}`}
        style={containerStyle}
      >
        <Alert
          type="error"
          message="图表加载失败"
          description={
            <div className="mt-2">
              <p className="text-gray-400 mb-3">{error}</p>
              <Button
                type="primary"
                icon={<ReloadOutlined />}
                onClick={handleRetry}
              >
                重试加载
              </Button>
            </div>
          }
          showIcon
        />
      </div>
    )
  }

  return (
    <div
      className={`tradingview-wrapper relative bg-dark-card rounded-lg overflow-hidden ${className}`}
      style={containerStyle}
    >
      {/* 加载遮罩 */}
      {loading && (
        <div className="absolute inset-0 z-10 flex items-center justify-center bg-dark-bg/80">
          <Spin tip="加载图表中..." size="large" />
        </div>
      )}

      {/* TradingView 容器 */}
      <div
        id={containerId.current}
        ref={containerRef}
        className="tradingview-container w-full h-full"
        style={{ width: '100%', height: '100%' }}
      />
    </div>
  )
}

export const TradingViewChart = memo(TradingViewChartComponent)
export default TradingViewChart
