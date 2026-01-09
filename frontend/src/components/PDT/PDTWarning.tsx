/**
 * PDT 警告弹窗组件
 * PRD 4.7
 */
import { Modal, Button } from 'antd'
import { WarningOutlined, StopOutlined, DollarOutlined } from '@ant-design/icons'
import { PDTWarningLevel, PDT_WARNING_CONFIG, formatPDTThreshold } from '../../types/pdt'

interface PDTWarningProps {
  level: PDTWarningLevel
  remaining: number
  visible: boolean
  onConfirm?: () => void
  onCancel?: () => void
}

export default function PDTWarning({
  level,
  remaining,
  visible,
  onConfirm,
  onCancel,
}: PDTWarningProps) {
  if (level === 'none') return null

  const isBlocked = level === 'danger'
  const config = PDT_WARNING_CONFIG[level]

  return (
    <Modal
      open={visible}
      onCancel={onCancel}
      footer={null}
      centered
      width={440}
      className="pdt-warning-modal"
    >
      <div className="text-center py-4">
        {/* 图标 */}
        <div
          className="w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4"
          style={{ backgroundColor: `${config.color}20` }}
        >
          {isBlocked ? (
            <StopOutlined style={{ fontSize: 32, color: config.color }} />
          ) : (
            <WarningOutlined style={{ fontSize: 32, color: config.color }} />
          )}
        </div>

        {/* 标题 */}
        <h3 className="text-xl font-semibold text-white mb-2">
          {isBlocked ? 'PDT限制已达上限' : 'PDT次数即将用尽'}
        </h3>

        {/* 描述 */}
        <p className="text-gray-400 mb-4">
          {isBlocked
            ? '您已用完本周所有日内交易次数，暂时无法进行新的日内交易。'
            : `您仅剩 ${remaining} 次日内交易机会，请谨慎使用。`}
        </p>

        {/* 提示 */}
        {!isBlocked && (
          <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-3 mb-4 text-left">
            <div className="flex items-start gap-2">
              <DollarOutlined className="text-blue-400 mt-0.5" />
              <div>
                <p className="text-blue-400 text-sm font-medium">解除限制方法</p>
                <p className="text-gray-400 text-xs mt-1">
                  入金至 {formatPDTThreshold()} 以上可永久解除PDT限制
                </p>
              </div>
            </div>
          </div>
        )}

        {/* PDT规则说明 */}
        <div className="bg-dark-hover rounded-lg p-3 mb-4 text-left">
          <p className="text-gray-500 text-xs mb-2">PDT规则说明</p>
          <ul className="text-gray-400 text-sm space-y-1">
            <li>• 账户余额 &lt; $25,000 时受PDT限制</li>
            <li>• 5个交易日内最多4次日内交易</li>
            <li>• 违规可能导致账户被限制90天</li>
          </ul>
        </div>

        {/* 操作按钮 */}
        <div className="flex gap-3 justify-center">
          {!isBlocked && onConfirm && (
            <Button
              type="primary"
              onClick={onConfirm}
              style={{ backgroundColor: config.color, borderColor: config.color }}
            >
              我已了解，继续交易
            </Button>
          )}
          {onCancel && (
            <Button onClick={onCancel}>
              {isBlocked ? '我知道了' : '取消'}
            </Button>
          )}
        </div>
      </div>
    </Modal>
  )
}
