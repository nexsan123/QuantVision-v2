import ReactECharts from 'echarts-for-react'
import { useMemo } from 'react'
import { useChartTheme } from '@/hooks/useChartTheme'

interface ReturnChartProps {
  data: {
    dates: string[]
    strategy: number[]
    benchmark?: number[]
  }
  height?: number
  showBenchmark?: boolean
}

/**
 * 收益曲线图
 *
 * 展示策略收益与基准对比
 */
export function ReturnChart({
  data,
  height = 350,
  showBenchmark = true,
}: ReturnChartProps) {
  const { theme, baseOption } = useChartTheme()

  const option = useMemo(() => {
    const series: any[] = [
      {
        name: '策略收益',
        type: 'line',
        data: data.strategy,
        smooth: true,
        lineStyle: { width: 2 },
        itemStyle: { color: theme.colors.primary },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(59, 130, 246, 0.3)' },
              { offset: 1, color: 'rgba(59, 130, 246, 0)' },
            ],
          },
        },
      },
    ]

    if (showBenchmark && data.benchmark) {
      series.push({
        name: '基准',
        type: 'line',
        data: data.benchmark,
        smooth: true,
        lineStyle: { width: 2, type: 'dashed' },
        itemStyle: { color: theme.colors.textSecondary },
      })
    }

    return {
      ...baseOption,
      legend: {
        ...baseOption.legend,
        data: showBenchmark ? ['策略收益', '基准'] : ['策略收益'],
        top: 0,
        right: 0,
      },
      tooltip: {
        ...baseOption.tooltip,
        trigger: 'axis',
        formatter: (params: any) => {
          const date = params[0].axisValue
          let html = `<div class="font-medium mb-1">${date}</div>`
          params.forEach((p: any) => {
            const value = (p.value * 100).toFixed(2)
            const color = p.value >= 0 ? theme.colors.profit : theme.colors.loss
            html += `<div style="color: ${color}">${p.seriesName}: ${value}%</div>`
          })
          return html
        },
      },
      xAxis: {
        ...baseOption.xAxis,
        type: 'category',
        data: data.dates,
        boundaryGap: false,
      },
      yAxis: {
        type: 'value',
        axisLine: { lineStyle: { color: theme.colors.border } },
        axisTick: { lineStyle: { color: theme.colors.border } },
        splitLine: { lineStyle: { color: theme.colors.grid, type: 'dashed' } },
        axisLabel: {
          color: theme.colors.textSecondary,
          formatter: (v: number) => `${(v * 100).toFixed(0)}%`,
        },
      },
      series,
    }
  }, [data, showBenchmark, theme, baseOption])

  return (
    <ReactECharts
      option={option}
      style={{ height }}
      opts={{ renderer: 'svg' }}
    />
  )
}

export default ReturnChart
