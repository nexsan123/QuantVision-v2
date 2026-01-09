import ReactECharts from 'echarts-for-react'
import { useMemo } from 'react'
import { useChartTheme } from '@/hooks/useChartTheme'

interface FactorICChartProps {
  data: {
    dates: string[]
    ic: number[]
    icMean?: number
  }
  height?: number
  showMeanLine?: boolean
}

/**
 * 因子 IC 时序图
 *
 * 展示因子 IC 值随时间变化，含均值线
 */
export function FactorICChart({
  data,
  height = 300,
  showMeanLine = true,
}: FactorICChartProps) {
  const { theme, baseOption } = useChartTheme()

  const icMean = useMemo(() => {
    if (data.icMean !== undefined) return data.icMean
    const validIc = data.ic.filter((v) => !isNaN(v))
    return validIc.reduce((a, b) => a + b, 0) / validIc.length
  }, [data])

  const option = useMemo(() => {
    const series: any[] = [
      {
        name: 'IC',
        type: 'bar',
        data: data.ic.map((v) => ({
          value: v,
          itemStyle: {
            color: v >= 0 ? theme.colors.profit : theme.colors.loss,
          },
        })),
        barWidth: '60%',
      },
    ]

    if (showMeanLine) {
      series.push({
        name: 'IC均值',
        type: 'line',
        data: data.ic.map(() => icMean),
        lineStyle: {
          type: 'dashed',
          width: 2,
          color: theme.colors.warning,
        },
        symbol: 'none',
      })
    }

    return {
      ...baseOption,
      legend: {
        ...baseOption.legend,
        data: showMeanLine ? ['IC', 'IC均值'] : ['IC'],
        top: 0,
        right: 0,
      },
      tooltip: {
        ...baseOption.tooltip,
        trigger: 'axis',
        formatter: (params: any) => {
          const date = params[0].axisValue
          const ic = params[0].value
          const color = ic >= 0 ? theme.colors.profit : theme.colors.loss
          return `
            <div class="font-medium mb-1">${date}</div>
            <div style="color: ${color}">IC: ${ic.toFixed(4)}</div>
            ${showMeanLine ? `<div>均值: ${icMean.toFixed(4)}</div>` : ''}
          `
        },
      },
      xAxis: {
        ...baseOption.xAxis,
        type: 'category',
        data: data.dates,
      },
      yAxis: {
        ...baseOption.yAxis,
        type: 'value',
      },
      series,
    }
  }, [data, icMean, showMeanLine, theme, baseOption])

  return (
    <ReactECharts
      option={option}
      style={{ height }}
      opts={{ renderer: 'svg' }}
    />
  )
}

export default FactorICChart
