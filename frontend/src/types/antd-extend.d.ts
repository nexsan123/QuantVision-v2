/**
 * Antd 类型扩展
 * 修复 Card size 属性类型问题 (TS2322)
 */
import { CardProps as AntdCardProps } from 'antd'

declare module 'antd' {
  interface CardProps extends AntdCardProps {
    size?: 'small' | 'default'
  }
}

declare module 'antd/es/card' {
  interface CardProps {
    size?: 'small' | 'default'
  }
}
