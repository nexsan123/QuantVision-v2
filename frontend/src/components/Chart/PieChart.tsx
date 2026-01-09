import ReactECharts from 'echarts-for-react'
import { useMemo } from 'react'
import { useChartTheme } from '@/hooks/useChartTheme'

interface PieChartProps {
  data: {
    name: string
    value: number
  }[]
  height?: number
  showLegend?: boolean
  donut?: boolean
}

/**
 * 饼图/环形图
 *
 * 用于持仓分布展示
 */
export function PieChart({
  data,
  height = 300,
  showLegend = true,
  donut = true,
}: PieChartProps) {
  const { theme, baseOption } = useChartTheme()

  const option = useMemo(() => {
    return {
      ...baseOption,
      tooltip: {
        ...baseOption.tooltip,
        trigger: 'item',
        formatter: (params: any) => {
          return `
            <div class="font-medium">${params.name}</div>
            <div>${(params.percent).toFixed(1)}% (${params.value.toFixed(2)})</div>
          `
        },
      },
      legend: showLegend
        ? {
            ...baseOption.legend,
            orient: 'vertical',
            right: 10,
            top: 'center',
            data: data.map((d) => d.name),
          }
        : undefined,
      color: theme.palette,
      series: [
        {
          type: 'pie',
          radius: donut ? ['45%', '70%'] : '70%',
          center: showLegend ? ['35%', '50%'] : ['50%', '50%'],
          data: data,
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowOffsetX: 0,
              shadowColor: 'rgba(0, 0, 0, 0.5)',
            },
          },
          label: {
            show: !showLegend,
            formatter: '{b}: {d}%',
            color: theme.colors.textSecondary,
          },
          labelLine: {
            show: !showLegend,
            lineStyle: {
              color: theme.colors.border,
            },
          },
        },
      ],
    }
  }, [data, showLegend, donut, theme, baseOption])

  return (
    <ReactECharts
      option={option}
      style={{ height }}
      opts={{ renderer: 'svg' }}
    />
  )
}

export default PieChart
