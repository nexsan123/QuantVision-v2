/**
 * PDT 状态面板组件
 * PRD 4.7
 */
import { Progress, Tag, Tooltip } from 'antd'
import { InfoCircleOutlined, ClockCircleOutlined } from '@ant-design/icons'
import {
  PDTStatus as PDTStatusType,
  getPDTWarningLevel,
  PDT_WARNING_CONFIG,
  formatPDTThreshold,
} from '../../types/pdt'

interface PDTStatusProps {
  status: PDTStatusType
}

export default function PDTStatus({ status }: PDTStatusProps) {
  const warningLevel = getPDTWarningLevel(status.remainingDayTrades)
  const config = PDT_WARNING_CONFIG[warningLevel]
  const percentage = (status.remainingDayTrades / status.maxDayTrades) * 100

  // 格式化重置时间
  const formatResetTime = () => {
    const resetDate = new Date(status.resetAt)
    const now = new Date()
    const diffMs = resetDate.getTime() - now.getTime()

    if (diffMs <= 0) return '即将重置'

    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffHours / 24)

    if (diffDays > 0) return `${diffDays}天${diffHours % 24}小时后`
    if (diffHours > 0) return `${diffHours}小时后`
    return '即将重置'
  }

  return (
    <div className="bg-dark-card rounded-lg p-4">
      {/* 标题 */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="text-lg">📊</span>
          <span className="font-medium text-white">PDT状态</span>
          <Tooltip title="Pattern Day Trader 规则：账户余额低于 $25,000 时，5个交易日内最多4次日内交易">
            <InfoCircleOutlined className="text-gray-500 cursor-help" />
          </Tooltip>
        </div>
        {!status.isPdtRestricted && (
          <Tag color="green">无限制</Tag>
        )}
        {status.isPdtRestricted && (
          <Tag color={warningLevel === 'danger' ? 'red' : warningLevel === 'warning' ? 'orange' : 'blue'}>
            {config.text}
          </Tag>
        )}
      </div>

      {/* 受限制账户显示 */}
      {status.isPdtRestricted && (
        <div className="space-y-3">
          {/* 剩余次数 */}
          <div>
            <div className="flex justify-between text-sm mb-1">
              <span className="text-gray-400">剩余日内交易次数</span>
              <span style={{ color: config.color }} className="font-medium">
                {status.remainingDayTrades}/{status.maxDayTrades}
              </span>
            </div>
            <Progress
              percent={percentage}
              showInfo={false}
              strokeColor={config.color}
              trailColor="#374151"
              size="small"
            />
          </div>

          {/* 重置时间 */}
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-400 flex items-center gap-1">
              <ClockCircleOutlined />
              下次重置
            </span>
            <span className="text-gray-300">{formatResetTime()}</span>
          </div>

          {/* 账户余额 */}
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-400">账户余额</span>
            <span className="text-gray-300">
              ${status.accountBalance.toLocaleString()}
            </span>
          </div>

          {/* 警告提示 */}
          {warningLevel === 'danger' && (
            <div className="bg-red-500/10 border border-red-500/30 rounded p-3 mt-2">
              <p className="text-red-400 text-sm">
                已达到PDT限制，暂时无法进行日内交易
              </p>
            </div>
          )}

          {warningLevel === 'warning' && (
            <div className="bg-yellow-500/10 border border-yellow-500/30 rounded p-3 mt-2">
              <p className="text-yellow-400 text-sm">
                仅剩 {status.remainingDayTrades} 次日内交易机会，请谨慎使用
              </p>
            </div>
          )}
        </div>
      )}

      {/* 无限制账户显示 */}
      {!status.isPdtRestricted && (
        <div className="text-center py-4">
          <p className="text-green-400 text-sm">
            账户余额 ≥ {formatPDTThreshold()}
          </p>
          <p className="text-gray-500 text-xs mt-1">
            无日内交易次数限制
          </p>
        </div>
      )}
    </div>
  )
}
