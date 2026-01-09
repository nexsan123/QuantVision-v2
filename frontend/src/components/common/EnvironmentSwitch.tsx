/**
 * 环境切换器组件
 * PRD 4.15.3: 模拟盘/实盘切换
 */
import { useState } from 'react'
import { Switch, Modal, Alert, message, Tooltip, Tag } from 'antd'
import {
  ExperimentOutlined,
  DollarOutlined,
  WarningOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
} from '@ant-design/icons'

export type TradingEnvironment = 'paper' | 'live'

interface EnvironmentSwitchProps {
  currentEnv: TradingEnvironment
  onEnvChange: (env: TradingEnvironment) => Promise<boolean>
  // 切换到实盘的前置条件
  paperDays?: number        // 模拟盘运行天数
  winRate?: number          // 胜率
  minPaperDays?: number     // 最低模拟盘天数要求 (默认30)
  minWinRate?: number       // 最低胜率要求 (默认40%)
  disabled?: boolean
  size?: 'small' | 'default'
}

interface SwitchCondition {
  key: string
  label: string
  current: number
  required: number
  unit: string
  passed: boolean
}

export default function EnvironmentSwitch({
  currentEnv,
  onEnvChange,
  paperDays = 0,
  winRate = 0,
  minPaperDays = 30,
  minWinRate = 40,
  disabled = false,
  size = 'default',
}: EnvironmentSwitchProps) {
  const [loading, setLoading] = useState(false)
  const [confirmVisible, setConfirmVisible] = useState(false)
  const [targetEnv, setTargetEnv] = useState<TradingEnvironment>('paper')

  const isLive = currentEnv === 'live'

  // 检查切换条件
  const checkConditions = (): SwitchCondition[] => {
    return [
      {
        key: 'paperDays',
        label: '模拟盘运行天数',
        current: paperDays,
        required: minPaperDays,
        unit: '天',
        passed: paperDays >= minPaperDays,
      },
      {
        key: 'winRate',
        label: '策略胜率',
        current: winRate,
        required: minWinRate,
        unit: '%',
        passed: winRate >= minWinRate,
      },
    ]
  }

  const conditions = checkConditions()
  const allConditionsPassed = conditions.every(c => c.passed)

  const handleSwitchClick = () => {
    const newEnv: TradingEnvironment = isLive ? 'paper' : 'live'
    setTargetEnv(newEnv)
    setConfirmVisible(true)
  }

  const handleConfirm = async () => {
    if (targetEnv === 'live' && !allConditionsPassed) {
      message.warning('未满足实盘切换条件')
      return
    }

    setLoading(true)
    try {
      const success = await onEnvChange(targetEnv)
      if (success) {
        message.success(`已切换至${targetEnv === 'live' ? '实盘' : '模拟盘'}交易`)
        setConfirmVisible(false)
      } else {
        message.error('环境切换失败')
      }
    } catch (error) {
      message.error('环境切换失败')
    } finally {
      setLoading(false)
    }
  }

  const renderConditionItem = (condition: SwitchCondition) => (
    <div key={condition.key} className="flex items-center justify-between py-2">
      <div className="flex items-center gap-2">
        {condition.passed ? (
          <CheckCircleOutlined className="text-green-500" />
        ) : (
          <CloseCircleOutlined className="text-red-500" />
        )}
        <span className="text-gray-300">{condition.label}</span>
      </div>
      <div className="text-right">
        <span className={condition.passed ? 'text-green-400' : 'text-red-400'}>
          {condition.current.toFixed(1)}{condition.unit}
        </span>
        <span className="text-gray-500 ml-1">
          / 要求 {condition.required}{condition.unit}
        </span>
      </div>
    </div>
  )

  return (
    <>
      <div className={`flex items-center gap-2 ${size === 'small' ? 'text-sm' : ''}`}>
        <Tooltip title="切换交易环境">
          <div
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg cursor-pointer transition-colors
              ${isLive ? 'bg-green-500/20 border border-green-500/50' : 'bg-blue-500/20 border border-blue-500/50'}
              ${disabled ? 'opacity-50 cursor-not-allowed' : 'hover:opacity-80'}
            `}
            onClick={disabled ? undefined : handleSwitchClick}
          >
            {isLive ? (
              <>
                <DollarOutlined className="text-green-400" />
                <span className="text-green-400 font-medium">实盘</span>
              </>
            ) : (
              <>
                <ExperimentOutlined className="text-blue-400" />
                <span className="text-blue-400 font-medium">模拟盘</span>
              </>
            )}
          </div>
        </Tooltip>

        {/* 条件状态指示 */}
        {!isLive && !allConditionsPassed && (
          <Tooltip title="未满足实盘切换条件">
            <Tag color="orange" className="flex items-center gap-1">
              <WarningOutlined />
              需继续模拟
            </Tag>
          </Tooltip>
        )}
        {!isLive && allConditionsPassed && (
          <Tooltip title="已满足实盘切换条件">
            <Tag color="green" className="flex items-center gap-1">
              <CheckCircleOutlined />
              可切实盘
            </Tag>
          </Tooltip>
        )}
      </div>

      {/* 确认弹窗 */}
      <Modal
        title={
          <div className="flex items-center gap-2">
            <WarningOutlined className="text-yellow-500" />
            <span>确认切换交易环境</span>
          </div>
        }
        open={confirmVisible}
        onOk={handleConfirm}
        onCancel={() => setConfirmVisible(false)}
        confirmLoading={loading}
        okText={`确认切换至${targetEnv === 'live' ? '实盘' : '模拟盘'}`}
        cancelText="取消"
        okButtonProps={{
          danger: targetEnv === 'live',
          disabled: targetEnv === 'live' && !allConditionsPassed,
        }}
        width={480}
      >
        <div className="py-4">
          {targetEnv === 'live' ? (
            <>
              <Alert
                type="warning"
                showIcon
                message="实盘交易风险提示"
                description="实盘交易将使用真实资金，所有交易订单将被实际执行。请确保您了解相关风险并已做好资金准备。"
                className="mb-4"
              />

              <div className="bg-dark-hover rounded-lg p-4">
                <div className="text-gray-400 mb-2">切换条件检查</div>
                {conditions.map(renderConditionItem)}
              </div>

              {!allConditionsPassed && (
                <Alert
                  type="error"
                  showIcon
                  message="未满足切换条件"
                  description="请继续在模拟盘运行，满足上述条件后方可切换至实盘。"
                  className="mt-4"
                />
              )}
            </>
          ) : (
            <>
              <Alert
                type="info"
                showIcon
                message="切换至模拟盘"
                description="切换后将停止实盘交易，所有新订单将在模拟环境中执行。现有实盘持仓不受影响。"
                className="mb-4"
              />

              <div className="bg-dark-hover rounded-lg p-4">
                <div className="flex items-center gap-2 text-gray-300">
                  <ExperimentOutlined className="text-blue-400" />
                  <span>模拟盘模式下：</span>
                </div>
                <ul className="mt-2 text-gray-400 text-sm list-disc list-inside space-y-1">
                  <li>订单将在模拟环境中执行</li>
                  <li>不会产生实际交易费用</li>
                  <li>可以安全测试新策略</li>
                  <li>随时可切回实盘</li>
                </ul>
              </div>
            </>
          )}
        </div>
      </Modal>
    </>
  )
}

/**
 * 简化版环境指示器 (仅显示状态，不可切换)
 */
export function EnvironmentIndicator({
  env,
  size = 'default',
}: {
  env: TradingEnvironment
  size?: 'small' | 'default'
}) {
  const isLive = env === 'live'

  return (
    <div
      className={`inline-flex items-center gap-1.5 px-2 py-1 rounded
        ${isLive ? 'bg-green-500/20 text-green-400' : 'bg-blue-500/20 text-blue-400'}
        ${size === 'small' ? 'text-xs' : 'text-sm'}
      `}
    >
      {isLive ? (
        <>
          <DollarOutlined />
          <span>实盘</span>
        </>
      ) : (
        <>
          <ExperimentOutlined />
          <span>模拟盘</span>
        </>
      )}
    </div>
  )
}
