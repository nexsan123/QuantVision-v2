import { Button as AntButton, ButtonProps as AntButtonProps } from 'antd'
import { forwardRef } from 'react'

export type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger'

interface ButtonProps extends Omit<AntButtonProps, 'type' | 'variant'> {
  variant?: ButtonVariant
}

const variantStyles: Record<ButtonVariant, string> = {
  primary: 'bg-primary-600 hover:bg-primary-700 text-white border-primary-600',
  secondary: 'bg-dark-card hover:bg-dark-hover text-gray-200 border-dark-border',
  ghost: 'bg-transparent hover:bg-dark-hover text-gray-300 border-transparent',
  danger: 'bg-red-600 hover:bg-red-700 text-white border-red-600',
}

/**
 * 按钮组件
 *
 * 提供四种变体: primary, secondary, ghost, danger
 */
export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = 'primary', className = '', children, ...props }, ref) => {
    const typeMap: Record<ButtonVariant, AntButtonProps['type']> = {
      primary: 'primary',
      secondary: 'default',
      ghost: 'text',
      danger: 'primary',
    }

    return (
      <AntButton
        ref={ref}
        type={typeMap[variant]}
        danger={variant === 'danger'}
        className={`${variantStyles[variant]} ${className}`}
        {...props}
      >
        {children}
      </AntButton>
    )
  }
)

Button.displayName = 'Button'

export default Button
