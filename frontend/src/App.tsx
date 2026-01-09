import { Suspense, lazy } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { Spin } from 'antd'
import MainLayout from './layouts/MainLayout'
import { RouteErrorBoundary } from './components/common/ErrorBoundary'

// 懒加载页面组件 - 提升首屏加载性能
const Dashboard = lazy(() => import('./pages/Dashboard'))
const FactorLab = lazy(() => import('./pages/FactorLab'))
const StrategyBuilder = lazy(() => import('./pages/StrategyBuilder'))
const BacktestCenter = lazy(() => import('./pages/BacktestCenter'))
const Trading = lazy(() => import('./pages/Trading'))
const RiskCenter = lazy(() => import('./pages/RiskCenter'))
const MyStrategies = lazy(() => import('./pages/MyStrategies'))
const Templates = lazy(() => import('./pages/Templates'))
const TradingStream = lazy(() => import('./pages/TradingStream'))
const StrategyReplay = lazy(() => import('./pages/StrategyReplay'))
const Intraday = lazy(() => import('./pages/Intraday'))

// 页面加载占位符
const PageLoading = () => (
  <div style={{
    height: '100%',
    minHeight: '400px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  }}>
    <Spin size="large" tip="页面加载中..." />
  </div>
)

// 带错误边界的页面包装器
const PageWrapper = ({ children }: { children: React.ReactNode }) => (
  <RouteErrorBoundary>
    <Suspense fallback={<PageLoading />}>
      {children}
    </Suspense>
  </RouteErrorBoundary>
)

function App() {
  return (
    <Routes>
      <Route path="/" element={<MainLayout />}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<PageWrapper><Dashboard /></PageWrapper>} />
        <Route path="my-strategies" element={<PageWrapper><MyStrategies /></PageWrapper>} />
        <Route path="factor-lab" element={<PageWrapper><FactorLab /></PageWrapper>} />
        <Route path="strategy" element={<PageWrapper><StrategyBuilder /></PageWrapper>} />
        <Route path="backtest" element={<PageWrapper><BacktestCenter /></PageWrapper>} />
        <Route path="trading" element={<PageWrapper><Trading /></PageWrapper>} />
        <Route path="trading/stream" element={<PageWrapper><TradingStream /></PageWrapper>} />
        <Route path="risk" element={<PageWrapper><RiskCenter /></PageWrapper>} />
        <Route path="templates" element={<PageWrapper><Templates /></PageWrapper>} />
        <Route path="strategy/replay" element={<PageWrapper><StrategyReplay /></PageWrapper>} />
        <Route path="intraday" element={<PageWrapper><Intraday /></PageWrapper>} />
      </Route>
    </Routes>
  )
}

export default App
