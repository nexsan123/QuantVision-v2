import { useMemo } from 'react'
import type { EChartsOption } from 'echarts'

/**
 * 图表主题 Hook
 *
 * 提供统一的深色主题配置
 */
export function useChartTheme() {
  const theme = useMemo(
    () => ({
      // 颜色
      colors: {
        primary: '#3b82f6',
        profit: '#22c55e',
        loss: '#ef4444',
        warning: '#f59e0b',
        text: '#e5e7eb',
        textSecondary: '#9ca3af',
        border: '#1e1e2e',
        background: '#12121a',
        grid: '#1e1e2e',
      },
      // 调色板
      palette: [
        '#3b82f6', // blue
        '#22c55e', // green
        '#f59e0b', // amber
        '#ef4444', // red
        '#8b5cf6', // violet
        '#ec4899', // pink
        '#14b8a6', // teal
        '#f97316', // orange
      ],
    }),
    []
  )

  const baseOption: Partial<EChartsOption> = useMemo(
    () => ({
      backgroundColor: 'transparent',
      textStyle: {
        color: theme.colors.text,
        fontFamily: 'Inter, system-ui, sans-serif',
      },
      grid: {
        top: 40,
        right: 20,
        bottom: 40,
        left: 60,
        containLabel: true,
      },
      legend: {
        textStyle: {
          color: theme.colors.textSecondary,
        },
      },
      tooltip: {
        backgroundColor: theme.colors.background,
        borderColor: theme.colors.border,
        textStyle: {
          color: theme.colors.text,
        },
      },
      xAxis: {
        axisLine: {
          lineStyle: { color: theme.colors.border },
        },
        axisTick: {
          lineStyle: { color: theme.colors.border },
        },
        axisLabel: {
          color: theme.colors.textSecondary,
        },
        splitLine: {
          lineStyle: { color: theme.colors.grid, type: 'dashed' },
        },
      },
      yAxis: {
        axisLine: {
          lineStyle: { color: theme.colors.border },
        },
        axisTick: {
          lineStyle: { color: theme.colors.border },
        },
        axisLabel: {
          color: theme.colors.textSecondary,
        },
        splitLine: {
          lineStyle: { color: theme.colors.grid, type: 'dashed' },
        },
      },
    }),
    [theme]
  )

  return { theme, baseOption }
}

export default useChartTheme
