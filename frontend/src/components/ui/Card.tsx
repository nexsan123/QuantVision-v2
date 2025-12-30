import { ReactNode } from 'react'

interface CardProps {
  title?: string
  subtitle?: string
  extra?: ReactNode
  children: ReactNode
  className?: string
  hoverable?: boolean
  padding?: 'none' | 'sm' | 'md' | 'lg'
}

const paddingStyles = {
  none: '',
  sm: 'p-3',
  md: 'p-4',
  lg: 'p-6',
}

/**
 * 卡片组件
 *
 * 深色主题卡片容器
 */
export function Card({
  title,
  subtitle,
  extra,
  children,
  className = '',
  hoverable = false,
  padding = 'lg',
}: CardProps) {
  return (
    <div
      className={`
        bg-dark-card border border-dark-border rounded-xl
        ${hoverable ? 'hover:bg-dark-hover hover:border-gray-700 transition-colors cursor-pointer' : ''}
        ${paddingStyles[padding]}
        ${className}
      `}
    >
      {(title || extra) && (
        <div className="flex items-center justify-between mb-4">
          <div>
            {title && <h3 className="text-lg font-semibold text-gray-100">{title}</h3>}
            {subtitle && <p className="text-sm text-gray-500 mt-0.5">{subtitle}</p>}
          </div>
          {extra && <div>{extra}</div>}
        </div>
      )}
      {children}
    </div>
  )
}

export default Card
