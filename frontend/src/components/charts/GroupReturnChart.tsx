import ReactECharts from 'echarts-for-react'
import { useMemo } from 'react'
import { useChartTheme } from '@/hooks/useChartTheme'

interface GroupReturnChartProps {
  data: {
    groups: string[] // ['G1', 'G2', ..., 'G10']
    returns: number[]
  }
  height?: number
}

/**
 * 分组回测收益图
 *
 * 展示因子分组收益，通常10组
 */
export function GroupReturnChart({ data, height = 300 }: GroupReturnChartProps) {
  const { theme, baseOption } = useChartTheme()

  const option = useMemo(() => {
    // 计算颜色渐变
    const colors = data.returns.map((v, i) => {
      const ratio = i / (data.returns.length - 1)
      if (v >= 0) {
        return `rgba(34, 197, 94, ${0.4 + ratio * 0.6})`
      }
      return `rgba(239, 68, 68, ${0.4 + (1 - ratio) * 0.6})`
    })

    return {
      ...baseOption,
      tooltip: {
        ...baseOption.tooltip,
        trigger: 'axis',
        formatter: (params: any) => {
          const group = params[0].name
          const value = (params[0].value * 100).toFixed(2)
          const color = params[0].value >= 0 ? theme.colors.profit : theme.colors.loss
          return `
            <div class="font-medium mb-1">${group}</div>
            <div style="color: ${color}">收益率: ${value}%</div>
          `
        },
      },
      xAxis: {
        ...baseOption.xAxis,
        type: 'category',
        data: data.groups,
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
      series: [
        {
          type: 'bar',
          data: data.returns.map((v, i) => ({
            value: v,
            itemStyle: { color: colors[i] },
          })),
          barWidth: '60%',
          label: {
            show: true,
            position: 'top',
            formatter: (params: any) => `${(params.value * 100).toFixed(1)}%`,
            color: theme.colors.textSecondary,
            fontSize: 11,
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

export default GroupReturnChart
