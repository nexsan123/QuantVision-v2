import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ConfigProvider, theme, Result, Button } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import { ErrorBoundary } from './components/common/ErrorBoundary'
import { logger } from './utils/logger'
import App from './App'
import './styles/global.css'

// 全局错误处理回调
const handleGlobalError = (error: Error, errorInfo: React.ErrorInfo) => {
  logger.error('Global application error', {
    error: error.message,
    stack: error.stack,
    componentStack: errorInfo.componentStack,
  })
}

// 全局错误回退UI
const GlobalErrorFallback = (
  <div style={{
    minHeight: '100vh',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    background: 'linear-gradient(135deg, #0a0a12 0%, #12121a 100%)',
  }}>
    <Result
      status="error"
      title={<span style={{ color: '#e5e7eb' }}>系统异常</span>}
      subTitle={<span style={{ color: '#9ca3af' }}>应用发生了意外错误，请刷新页面重试</span>}
      extra={[
        <Button
          key="reload"
          type="primary"
          size="large"
          onClick={() => window.location.reload()}
          style={{ background: '#3b82f6' }}
        >
          刷新页面
        </Button>,
        <Button
          key="home"
          size="large"
          onClick={() => window.location.href = '/'}
          style={{ color: '#9ca3af', borderColor: '#374151' }}
        >
          返回首页
        </Button>,
      ]}
    />
  </div>
)

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5,
      retry: 1,
    },
  },
})

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ErrorBoundary
      fallback={GlobalErrorFallback}
      onError={handleGlobalError}
    >
      <QueryClientProvider client={queryClient}>
        <ConfigProvider
          locale={zhCN}
          theme={{
            algorithm: theme.darkAlgorithm,
            token: {
              colorPrimary: '#3b82f6',
              colorBgContainer: '#12121a',
              colorBgElevated: '#1a1a28',
              colorBorder: '#1e1e2e',
              colorText: '#e5e7eb',
              colorTextSecondary: '#9ca3af',
              borderRadius: 8,
              fontFamily: 'Inter, system-ui, sans-serif',
            },
          }}
        >
          <BrowserRouter>
            <App />
          </BrowserRouter>
        </ConfigProvider>
      </QueryClientProvider>
    </ErrorBoundary>
  </React.StrictMode>
)
