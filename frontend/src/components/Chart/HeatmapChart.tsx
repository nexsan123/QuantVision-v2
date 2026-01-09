import ReactECharts from 'echarts-for-react'
import { useMemo } from 'react'
import { useChartTheme } from '@/hooks/useChartTheme'

interface HeatmapChartProps {
  data: {
    years: string[]
    months: string[]
    values: number[][] // [year][month]
  }
  height?: number
}

/**
 * 月度收益热力图
 *
 * 展示每月收益率，正负值使用不同颜色
 */
export function HeatmapChart({ data, height = 300 }: HeatmapChartProps) {
  const { theme, baseOption } = useChartTheme()

  const option = useMemo(() => {
    // 转换为 ECharts 格式: [x, y, value]
    const heatmapData: [number, number, number][] = []
    data.values.forEach((yearData, yearIdx) => {
      yearData.forEach((value, monthIdx) => {
        heatmapData.push([monthIdx, yearIdx, value])
      })
    })

    // 计算最大绝对值用于颜色映射
    const maxAbs = Math.max(
      ...heatmapData.map((d) => Math.abs(d[2])).filter((v) => !isNaN(v))
    )

    return {
      ...baseOption,
      grid: {
        top: 20,
        right: 60,
        bottom: 40,
        left: 60,
      },
      tooltip: {
        ...baseOption.tooltip,
        formatter: (params: any) => {
          const month = data.months[params.data[0]]
          const year = data.years[params.data[1]]
          const value = (params.data[2] * 100).toFixed(2)
          const color = params.data[2] >= 0 ? theme.colors.profit : theme.colors.loss
          return `
            <div class="font-medium">${year}年${month}</div>
            <div style="color: ${color}">${value}%</div>
          `
        },
      },
      xAxis: {
        type: 'category',
        data: data.months,
        axisLine: { lineStyle: { color: theme.colors.border } },
        axisLabel: { color: theme.colors.textSecondary },
        splitArea: { show: false },
      },
      yAxis: {
        type: 'category',
        data: data.years,
        axisLine: { lineStyle: { color: theme.colors.border } },
        axisLabel: { color: theme.colors.textSecondary },
        splitArea: { show: false },
      },
      visualMap: {
        min: -maxAbs,
        max: maxAbs,
        calculable: true,
        orient: 'vertical',
        right: 0,
        top: 'center',
        inRange: {
          color: [theme.colors.loss, '#1e1e2e', theme.colors.profit],
        },
        textStyle: {
          color: theme.colors.textSecondary,
        },
        formatter: (value: number) => `${(value * 100).toFixed(0)}%`,
      },
      series: [
        {
          type: 'heatmap',
          data: heatmapData,
          label: {
            show: true,
            formatter: (params: any) => {
              const value = params.data[2]
              if (isNaN(value)) return ''
              return `${(value * 100).toFixed(1)}%`
            },
            color: theme.colors.text,
            fontSize: 10,
          },
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowColor: 'rgba(0, 0, 0, 0.5)',
            },
          },
        },
      ],
    }
  }, [data, theme, baseOption])

  return (
    <ReactECharts
      option={option}
      style={{ height }}
      opts={{ renderer: 'svg' }}
    />
  )
}

export default HeatmapChart
