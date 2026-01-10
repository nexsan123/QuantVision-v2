/**
 * 通用组件导出
 * Sprint 11: 组件整合
 * Sprint 12: 错误边界 + 加载状态
 */

export { default as EnvironmentSwitch } from './EnvironmentSwitch'
// ConnectionStatus 已移至 Trading 目录
// export { ConnectionStatus, ConnectionStatusIcon } from '@/components/Trading'
export {
  ErrorBoundary,
  withErrorBoundary,
  PanelErrorBoundary,
  RouteErrorBoundary,
} from './ErrorBoundary'
export {
  LoadingSpinner,
  ContentLoader,
  PanelSkeleton,
  TableSkeleton,
  ChartSkeleton,
  CardListSkeleton,
  StatCardSkeleton,
  LoadingOverlay,
  ProgressLoader,
  InitialLoading,
  PageLoading,
} from './LoadingStates'
export { HealthStatusPanel, HealthIndicator } from './HealthStatus'
