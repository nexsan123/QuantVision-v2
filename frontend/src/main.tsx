import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ConfigProvider, theme, Result, Button } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import dayjs from 'dayjs'
import 'dayjs/locale/zh-cn'
import { ErrorBoundary } from './components/common/ErrorBoundary'
import { logger } from './utils/logger'
import App from './App'
import './styles/global.css'

// 设置 dayjs 中文语言
dayjs.locale('zh-cn')

// 全局错误过滤器 - 忽略第三方库的非关键错误
window.addEventListener('error', (event) => {
  const msg = event.message || ''
  // 过滤 TradingView 相关错误
  if (msg.includes('list') && msg.includes('undefined') ||
      msg.includes('tradingview') ||
      msg.includes('Failed to fetch')) {
    event.preventDefault()
    return false
  }
})

window.addEventListener('unhandledrejection', (event) => {
  const reason = event.reason?.message || event.reason?.toString() || ''
  // 过滤 TradingView 相关的 Promise 拒绝
  if (reason.includes('list') ||
      reason.includes('tradingview') ||
      reason.includes('Failed to fetch')) {
    event.preventDefault()
    return false
  }
})

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

// 隐藏启动加载动画
const hideAppLoader = () => {
  const loader = document.getElementById('app-loader')
  if (loader) {
    // 更新状态文字
    const status = loader.querySelector('.loader-status')
    if (status) {
      status.textContent = '加载完成'
    }
    // 延迟隐藏，让用户看到加载完成
    setTimeout(() => {
      loader.classList.add('hidden')
      // 完全移除元素
      setTimeout(() => {
        loader.remove()
      }, 500)
    }, 300)
  }
}

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

// React 渲染完成后隐藏加载动画
requestAnimationFrame(() => {
  requestAnimationFrame(() => {
    hideAppLoader()
  })
})
