import { Spin } from 'antd'
import { LoadingOutlined } from '@ant-design/icons'

interface LoadingSpinnerProps {
  size?: 'small' | 'default' | 'large'
  tip?: string
  fullScreen?: boolean
  className?: string
}

/**
 * 加载指示器组件
 */
export function LoadingSpinner({
  size = 'default',
  tip,
  fullScreen = false,
  className = '',
}: LoadingSpinnerProps) {
  const sizeMap = {
    small: 16,
    default: 24,
    large: 40,
  }

  const icon = <LoadingOutlined style={{ fontSize: sizeMap[size] }} spin />

  if (fullScreen) {
    return (
      <div className="fixed inset-0 flex items-center justify-center bg-dark-bg/80 z-50">
        <div className="text-center">
          <Spin indicator={icon} size={size} />
          {tip && <p className="mt-4 text-gray-400">{tip}</p>}
        </div>
      </div>
    )
  }

  return (
    <div className={`flex items-center justify-center py-8 ${className}`}>
      <div className="text-center">
        <Spin indicator={icon} size={size} />
        {tip && <p className="mt-2 text-sm text-gray-400">{tip}</p>}
      </div>
    </div>
  )
}

export default LoadingSpinner
