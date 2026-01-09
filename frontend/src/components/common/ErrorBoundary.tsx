/**
 * React 错误边界组件
 * Sprint 12: T29 - 前端错误边界
 *
 * 捕获子组件中的 JavaScript 错误，防止整个应用崩溃
 */

import React, { Component, ErrorInfo, ReactNode } from 'react'
import { Button, Result, Typography } from 'antd'
import { ReloadOutlined, BugOutlined } from '@ant-design/icons'

const { Paragraph, Text } = Typography

// ==================== 类型定义 ====================

interface ErrorBoundaryProps {
  children: ReactNode
  fallback?: ReactNode
  onError?: (error: Error, errorInfo: ErrorInfo) => void
  showDetails?: boolean
  resetOnNavigate?: boolean
}

interface ErrorBoundaryState {
  hasError: boolean
  error: Error | null
  errorInfo: ErrorInfo | null
}

// ==================== 错误边界组件 ====================

/**
 * 错误边界 - 捕获渲染错误
 */
export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props)
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    }
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    this.setState({ errorInfo })

    // 调用错误回调
    this.props.onError?.(error, errorInfo)

    // 记录错误到控制台
    console.error('[ErrorBoundary] Caught error:', error)
    console.error('[ErrorBoundary] Component stack:', errorInfo.componentStack)

    // 可以在这里上报错误到监控服务
    // reportError(error, errorInfo)
  }

  handleReset = (): void => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    })
  }

  handleReload = (): void => {
    window.location.reload()
  }

  render(): ReactNode {
    const { hasError, error, errorInfo } = this.state
    const { children, fallback, showDetails = false } = this.props

    if (hasError) {
      // 使用自定义 fallback
      if (fallback) {
        return fallback
      }

      // 默认错误 UI
      return (
        <div style={{
          minHeight: '400px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '24px',
        }}>
          <Result
            status="error"
            title="页面出现错误"
            subTitle="抱歉，页面渲染时发生了错误。您可以尝试刷新页面或返回上一页。"
            extra={[
              <Button
                key="retry"
                type="primary"
                icon={<ReloadOutlined />}
                onClick={this.handleReset}
              >
                重试
              </Button>,
              <Button
                key="reload"
                onClick={this.handleReload}
              >
                刷新页面
              </Button>,
            ]}
          >
            {showDetails && error && (
              <div style={{
                marginTop: 16,
                textAlign: 'left',
                background: '#fafafa',
                padding: 16,
                borderRadius: 8,
                maxHeight: 300,
                overflow: 'auto',
              }}>
                <Paragraph>
                  <Text strong>错误信息：</Text>
                </Paragraph>
                <Paragraph>
                  <Text code style={{ wordBreak: 'break-all' }}>
                    {error.message}
                  </Text>
                </Paragraph>
                {errorInfo && (
                  <>
                    <Paragraph>
                      <Text strong>组件堆栈：</Text>
                    </Paragraph>
                    <pre style={{
                      fontSize: 12,
                      maxHeight: 150,
                      overflow: 'auto',
                      background: '#1f1f1f',
                      color: '#d4d4d4',
                      padding: 12,
                      borderRadius: 4,
                    }}>
                      {errorInfo.componentStack}
                    </pre>
                  </>
                )}
              </div>
            )}
          </Result>
        </div>
      )
    }

    return children
  }
}

// ==================== 函数式包装 ====================

interface WithErrorBoundaryOptions {
  fallback?: ReactNode
  onError?: (error: Error, errorInfo: ErrorInfo) => void
  showDetails?: boolean
}

/**
 * 高阶组件 - 为组件添加错误边界
 */
export function withErrorBoundary<P extends object>(
  WrappedComponent: React.ComponentType<P>,
  options: WithErrorBoundaryOptions = {}
): React.FC<P> {
  const WithErrorBoundary: React.FC<P> = (props) => (
    <ErrorBoundary {...options}>
      <WrappedComponent {...props} />
    </ErrorBoundary>
  )

  WithErrorBoundary.displayName = `WithErrorBoundary(${
    WrappedComponent.displayName || WrappedComponent.name || 'Component'
  })`

  return WithErrorBoundary
}

// ==================== 特定场景边界 ====================

interface PanelErrorBoundaryProps {
  children: ReactNode
  title?: string
}

/**
 * 面板错误边界 - 用于仪表盘面板
 */
export function PanelErrorBoundary({ children, title = '此面板' }: PanelErrorBoundaryProps) {
  return (
    <ErrorBoundary
      fallback={
        <div style={{
          padding: 24,
          textAlign: 'center',
          color: '#8c8c8c',
          background: 'rgba(255, 77, 79, 0.05)',
          borderRadius: 8,
          border: '1px dashed rgba(255, 77, 79, 0.3)',
        }}>
          <BugOutlined style={{ fontSize: 24, marginBottom: 8 }} />
          <div>{title}加载失败</div>
          <Button
            type="link"
            size="small"
            onClick={() => window.location.reload()}
          >
            刷新页面
          </Button>
        </div>
      }
    >
      {children}
    </ErrorBoundary>
  )
}

/**
 * 路由错误边界 - 用于页面级别
 */
export function RouteErrorBoundary({ children }: { children: ReactNode }) {
  return (
    <ErrorBoundary
      showDetails={process.env.NODE_ENV === 'development'}
      onError={(error, errorInfo) => {
        // 可以上报到错误监控服务
        console.error('[RouteError]', error.message)
      }}
    >
      {children}
    </ErrorBoundary>
  )
}

export default ErrorBoundary
