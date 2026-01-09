import ReactECharts from 'echarts-for-react'
import { useMemo } from 'react'
import { useChartTheme } from '@/hooks/useChartTheme'

interface RiskRadarChartProps {
  data: {
    indicators: { name: string; max: number }[]
    values: number[]
  }
  height?: number
}

/**
 * 风险因子雷达图
 *
 * 展示多维风险因子暴露
 */
export function RiskRadarChart({ data, height = 350 }: RiskRadarChartProps) {
  const { theme, baseOption } = useChartTheme()

  const option = useMemo(() => {
    return {
      ...baseOption,
      tooltip: {
        ...baseOption.tooltip,
        trigger: 'item',
      },
      radar: {
        indicator: data.indicators,
        shape: 'polygon',
        splitNumber: 4,
        axisName: {
          color: theme.colors.textSecondary,
        },
        splitLine: {
          lineStyle: {
            color: theme.colors.border,
          },
        },
        splitArea: {
          areaStyle: {
            color: ['transparent', 'rgba(30, 30, 46, 0.3)'],
          },
        },
        axisLine: {
          lineStyle: {
            color: theme.colors.border,
          },
        },
      },
      series: [
        {
          type: 'radar',
          data: [
            {
              value: data.values,
              name: '风险暴露',
              areaStyle: {
                color: 'rgba(59, 130, 246, 0.3)',
              },
              lineStyle: {
                color: theme.colors.primary,
                width: 2,
              },
              itemStyle: {
                color: theme.colors.primary,
              },
            },
          ],
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

export default RiskRadarChart
