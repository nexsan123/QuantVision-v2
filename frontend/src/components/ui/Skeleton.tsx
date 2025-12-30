interface SkeletonProps {
  width?: string | number
  height?: string | number
  className?: string
  variant?: 'text' | 'circular' | 'rectangular'
  animation?: 'pulse' | 'wave' | 'none'
}

/**
 * 骨架屏组件
 *
 * 用于加载状态占位
 */
export function Skeleton({
  width,
  height,
  className = '',
  variant = 'rectangular',
  animation = 'pulse',
}: SkeletonProps) {
  const baseStyles = 'bg-dark-border'

  const variantStyles = {
    text: 'rounded',
    circular: 'rounded-full',
    rectangular: 'rounded-lg',
  }

  const animationStyles = {
    pulse: 'animate-pulse',
    wave: 'animate-pulse', // 简化处理
    none: '',
  }

  const style = {
    width: typeof width === 'number' ? `${width}px` : width,
    height: typeof height === 'number' ? `${height}px` : height,
  }

  return (
    <div
      className={`${baseStyles} ${variantStyles[variant]} ${animationStyles[animation]} ${className}`}
      style={style}
    />
  )
}

/**
 * 卡片骨架屏
 */
export function CardSkeleton() {
  return (
    <div className="bg-dark-card border border-dark-border rounded-xl p-6">
      <Skeleton width="40%" height={24} className="mb-4" />
      <Skeleton width="100%" height={16} className="mb-2" />
      <Skeleton width="80%" height={16} className="mb-2" />
      <Skeleton width="60%" height={16} />
    </div>
  )
}

/**
 * 表格骨架屏
 */
export function TableSkeleton({ rows = 5 }: { rows?: number }) {
  return (
    <div className="space-y-3">
      <Skeleton width="100%" height={40} />
      {Array.from({ length: rows }).map((_, i) => (
        <Skeleton key={i} width="100%" height={48} />
      ))}
    </div>
  )
}

/**
 * 图表骨架屏
 */
export function ChartSkeleton({ height = 300 }: { height?: number }) {
  return (
    <div className="bg-dark-card border border-dark-border rounded-xl p-6">
      <Skeleton width="30%" height={24} className="mb-4" />
      <Skeleton width="100%" height={height} />
    </div>
  )
}

export default Skeleton
