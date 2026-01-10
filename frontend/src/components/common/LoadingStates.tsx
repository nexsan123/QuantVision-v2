/**
 * 加载状态组件
 * Sprint 12: T30 - 加载状态优化
 *
 * 提供统一的加载状态展示:
 * - 骨架屏 (Skeleton)
 * - 加载遮罩 (Overlay)
 * - 内容占位符
 */

import { ReactNode } from 'react'
import { Skeleton, Spin, Card, Space, Progress } from 'antd'
import { LoadingOutlined } from '@ant-design/icons'

// ==================== 通用加载指示器 ====================

interface LoadingSpinnerProps {
  size?: 'small' | 'default' | 'large'
  tip?: string
  fullScreen?: boolean
}

/**
 * 加载旋转器
 */
export function LoadingSpinner({
  size = 'default',
  tip,
  fullScreen = false,
}: LoadingSpinnerProps) {
  const spinner = (
    <Spin
      indicator={<LoadingOutlined style={{ fontSize: size === 'large' ? 48 : size === 'small' ? 16 : 24 }} spin />}
      tip={tip}
      size={size}
    />
  )

  if (fullScreen) {
    return (
      <div style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'rgba(0, 0, 0, 0.45)',
        zIndex: 1000,
      }}>
        {spinner}
      </div>
    )
  }

  return spinner
}

// ==================== 内容加载包装 ====================

interface ContentLoaderProps {
  loading: boolean
  children: ReactNode
  skeleton?: ReactNode
  minHeight?: number
  delay?: number
}

/**
 * 内容加载器 - 在加载时显示骨架屏
 */
export function ContentLoader({
  loading,
  children,
  skeleton,
  minHeight = 100,
}: ContentLoaderProps) {
  if (loading) {
    return (
      <div style={{ minHeight }}>
        {skeleton || <Skeleton active paragraph={{ rows: 3 }} />}
      </div>
    )
  }

  return <>{children}</>
}

// ==================== 面板骨架屏 ====================

interface PanelSkeletonProps {
  rows?: number
  avatar?: boolean
  title?: boolean
}

/**
 * 面板骨架屏
 */
export function PanelSkeleton({ rows = 4, avatar = false, title = true }: PanelSkeletonProps) {
  return (
    <Card style={{ background: 'transparent', border: 'none' }}>
      <Skeleton
        active
        avatar={avatar}
        title={title}
        paragraph={{ rows }}
      />
    </Card>
  )
}

// ==================== 表格骨架屏 ====================

interface TableSkeletonProps {
  rows?: number
  columns?: number
}

/**
 * 表格骨架屏
 */
export function TableSkeleton({ rows = 5, columns = 4 }: TableSkeletonProps) {
  return (
    <div style={{ padding: '16px 0' }}>
      {/* 表头 */}
      <div style={{
        display: 'flex',
        gap: 16,
        marginBottom: 16,
        padding: '0 8px',
      }}>
        {Array.from({ length: columns }).map((_, i) => (
          <Skeleton.Input
            key={`header-${i}`}
            active
            size="small"
            style={{ width: `${100 / columns}%`, minWidth: 80 }}
          />
        ))}
      </div>

      {/* 表格行 */}
      {Array.from({ length: rows }).map((_, rowIndex) => (
        <div
          key={`row-${rowIndex}`}
          style={{
            display: 'flex',
            gap: 16,
            marginBottom: 12,
            padding: '8px',
            background: rowIndex % 2 === 0 ? 'rgba(255,255,255,0.02)' : 'transparent',
            borderRadius: 4,
          }}
        >
          {Array.from({ length: columns }).map((_, colIndex) => (
            <Skeleton.Input
              key={`cell-${rowIndex}-${colIndex}`}
              active
              size="small"
              style={{ width: `${100 / columns}%`, minWidth: 60 }}
            />
          ))}
        </div>
      ))}
    </div>
  )
}

// ==================== 图表骨架屏 ====================

interface ChartSkeletonProps {
  height?: number
  type?: 'line' | 'bar' | 'pie'
}

/**
 * 图表骨架屏
 */
export function ChartSkeleton({ height = 300, type = 'line' }: ChartSkeletonProps) {
  return (
    <div style={{
      height,
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'space-between',
      padding: 16,
    }}>
      {/* 图表标题区 */}
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <Skeleton.Input active size="small" style={{ width: 120 }} />
        <Space>
          <Skeleton.Button active size="small" style={{ width: 60 }} />
          <Skeleton.Button active size="small" style={{ width: 60 }} />
        </Space>
      </div>

      {/* 图表主体区 */}
      <div style={{
        flex: 1,
        display: 'flex',
        alignItems: 'flex-end',
        gap: type === 'bar' ? 8 : 0,
        paddingTop: 20,
      }}>
        {type === 'bar' ? (
          // 柱状图骨架
          Array.from({ length: 8 }).map((_, i) => (
            <div
              key={i}
              style={{
                flex: 1,
                height: `${30 + Math.random() * 60}%`,
                background: 'linear-gradient(180deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%)',
                borderRadius: '4px 4px 0 0',
                animation: 'skeleton-pulse 1.5s ease-in-out infinite',
              }}
            />
          ))
        ) : type === 'pie' ? (
          // 饼图骨架
          <div style={{
            width: Math.min(height - 80, 200),
            height: Math.min(height - 80, 200),
            margin: '0 auto',
            borderRadius: '50%',
            background: 'conic-gradient(rgba(255,255,255,0.1) 0deg, rgba(255,255,255,0.05) 120deg, rgba(255,255,255,0.08) 240deg, rgba(255,255,255,0.1) 360deg)',
            animation: 'skeleton-pulse 1.5s ease-in-out infinite',
          }} />
        ) : (
          // 折线图骨架
          <svg width="100%" height="100%" style={{ opacity: 0.3 }}>
            <path
              d="M 0 80 Q 50 60 100 70 T 200 50 T 300 65 T 400 40 T 500 55"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              style={{ animation: 'skeleton-pulse 1.5s ease-in-out infinite' }}
            />
          </svg>
        )}
      </div>

      {/* X 轴标签 */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        marginTop: 16,
      }}>
        {Array.from({ length: 5 }).map((_, i) => (
          <Skeleton.Input key={i} active size="small" style={{ width: 40 }} />
        ))}
      </div>
    </div>
  )
}

// ==================== 卡片列表骨架屏 ====================

interface CardListSkeletonProps {
  count?: number
  imageHeight?: number
}

/**
 * 卡片列表骨架屏
 */
export function CardListSkeleton({ count = 3, imageHeight = 120 }: CardListSkeletonProps) {
  return (
    <Space direction="vertical" style={{ width: '100%' }} size={16}>
      {Array.from({ length: count }).map((_, i) => (
        <Card key={i} style={{ background: 'rgba(255,255,255,0.02)' }}>
          <Skeleton.Image
            active
            style={{ width: '100%', height: imageHeight, marginBottom: 16 }}
          />
          <Skeleton active paragraph={{ rows: 2 }} />
        </Card>
      ))}
    </Space>
  )
}

// ==================== 统计卡片骨架屏 ====================

interface StatCardSkeletonProps {
  count?: number
}

/**
 * 统计卡片骨架屏
 */
export function StatCardSkeleton({ count = 4 }: StatCardSkeletonProps) {
  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: `repeat(${Math.min(count, 4)}, 1fr)`,
      gap: 16,
    }}>
      {Array.from({ length: count }).map((_, i) => (
        <Card key={i} size="small" style={{ background: 'rgba(255,255,255,0.02)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div style={{ flex: 1 }}>
              <Skeleton.Input active size="small" style={{ width: 80, marginBottom: 8 }} />
              <Skeleton.Input active size="large" style={{ width: 100 }} />
            </div>
            <Skeleton.Avatar active size={40} shape="square" />
          </div>
        </Card>
      ))}
    </div>
  )
}

// ==================== 加载遮罩 ====================

interface LoadingOverlayProps {
  loading: boolean
  children: ReactNode
  tip?: string
  blur?: boolean
}

/**
 * 加载遮罩 - 在内容上覆盖加载状态
 */
export function LoadingOverlay({
  loading,
  children,
  tip,
  blur = true,
}: LoadingOverlayProps) {
  return (
    <div style={{ position: 'relative' }}>
      {children}
      {loading && (
        <div style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: 'rgba(0, 0, 0, 0.6)',
          backdropFilter: blur ? 'blur(2px)' : undefined,
          borderRadius: 8,
          zIndex: 10,
        }}>
          <Spin
            indicator={<LoadingOutlined style={{ fontSize: 32 }} spin />}
            tip={tip}
          />
        </div>
      )}
    </div>
  )
}

// ==================== 进度加载 ====================

interface ProgressLoaderProps {
  percent: number
  status?: 'active' | 'success' | 'exception'
  showInfo?: boolean
  strokeColor?: string
}

/**
 * 进度加载器
 */
export function ProgressLoader({
  percent,
  status = 'active',
  showInfo = true,
  strokeColor = '#1890ff',
}: ProgressLoaderProps) {
  return (
    <div style={{ padding: '24px 16px' }}>
      <Progress
        percent={percent}
        status={status}
        showInfo={showInfo}
        strokeColor={strokeColor}
        trailColor="rgba(255,255,255,0.1)"
      />
    </div>
  )
}

// ==================== 空状态加载 ====================

interface InitialLoadingProps {
  message?: string
}

/**
 * 初始加载状态 - 用于首次数据加载
 */
export function InitialLoading({ message = '加载中...' }: InitialLoadingProps) {
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: 48,
      color: 'rgba(255,255,255,0.65)',
    }}>
      <Spin
        indicator={<LoadingOutlined style={{ fontSize: 40 }} spin />}
        size="large"
      />
      <div style={{ marginTop: 16, fontSize: 14 }}>{message}</div>
    </div>
  )
}

// ==================== 页面加载 ====================

/**
 * 页面加载状态
 */
export function PageLoading() {
  return (
    <div style={{
      minHeight: '60vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
    }}>
      <Spin
        indicator={<LoadingOutlined style={{ fontSize: 48 }} spin />}
        tip="页面加载中..."
        size="large"
      />
    </div>
  )
}

// ==================== CSS 动画 ====================

// 注入骨架屏动画样式
const styleId = 'loading-states-style'
if (typeof document !== 'undefined' && !document.getElementById(styleId)) {
  const style = document.createElement('style')
  style.id = styleId
  style.textContent = `
    @keyframes skeleton-pulse {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.4; }
    }
  `
  document.head.appendChild(style)
}

export default {
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
}
