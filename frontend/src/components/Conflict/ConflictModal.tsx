/**
 * 冲突处理弹窗组件
 * PRD 4.6 策略冲突检测
 */
import { Modal, Tag, Button, Radio, Space, Alert, Divider, Tooltip } from 'antd'
import {
  WarningOutlined,
  ThunderboltOutlined,
  ClockCircleOutlined,
  SwapOutlined,
} from '@ant-design/icons'
import { useState } from 'react'
import {
  ConflictDetail,
  ResolutionAction,
  CONFLICT_TYPE_CONFIG,
  SEVERITY_CONFIG,
  RESOLUTION_CONFIG,
  formatConflictTime,
  getRemainingTime,
} from '../../types/conflict'

interface ConflictModalProps {
  conflict: ConflictDetail | null
  open: boolean
  onClose: () => void
  onResolve: (conflictId: string, resolution: ResolutionAction) => void
  loading?: boolean
}

export default function ConflictModal({
  conflict,
  open,
  onClose,
  onResolve,
  loading = false,
}: ConflictModalProps) {
  const [selectedResolution, setSelectedResolution] = useState<ResolutionAction | null>(null)

  if (!conflict) return null

  const typeConfig = CONFLICT_TYPE_CONFIG[conflict.conflict_type]
  const severityConfig = SEVERITY_CONFIG[conflict.severity]

  const handleResolve = () => {
    if (selectedResolution) {
      onResolve(conflict.conflict_id, selectedResolution)
    }
  }

  const allResolutions = [
    conflict.suggested_resolution,
    ...conflict.alternative_resolutions.filter((r) => r !== conflict.suggested_resolution),
  ]

  return (
    <Modal
      title={
        <div className="flex items-center gap-2">
          <span className="text-xl">{typeConfig.icon}</span>
          <span>{typeConfig.label}</span>
          <Tag
            style={{
              backgroundColor: `${severityConfig.color}20`,
              color: severityConfig.color,
              border: 'none',
            }}
          >
            {severityConfig.label}
          </Tag>
        </div>
      }
      open={open}
      onCancel={onClose}
      width={700}
      footer={[
        <Button key="cancel" onClick={onClose}>
          取消
        </Button>,
        <Button key="ignore" onClick={() => onResolve(conflict.conflict_id, 'ignore')}>
          忽略
        </Button>,
        <Button
          key="resolve"
          type="primary"
          onClick={handleResolve}
          disabled={!selectedResolution}
          loading={loading}
        >
          确认解决
        </Button>,
      ]}
      className="conflict-modal"
    >
      {/* 冲突描述 */}
      <div className="mb-4">
        <Alert
          message={conflict.description}
          description={conflict.reason}
          type={conflict.severity === 'critical' ? 'error' : 'warning'}
          showIcon
        />
      </div>

      {/* 冲突双方信号 */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        {/* 信号A */}
        <div className="p-4 rounded-lg bg-blue-500/5 border border-blue-500/20">
          <div className="flex items-center justify-between mb-2">
            <span className="font-semibold text-blue-400">策略A</span>
            <Tag color="blue">{conflict.signal_a.strategy_name}</Tag>
          </div>
          <SignalDetail signal={conflict.signal_a} />
        </div>

        {/* 信号B */}
        {conflict.signal_b ? (
          <div className="p-4 rounded-lg bg-purple-500/5 border border-purple-500/20">
            <div className="flex items-center justify-between mb-2">
              <span className="font-semibold text-purple-400">策略B</span>
              <Tag color="purple">{conflict.signal_b.strategy_name}</Tag>
            </div>
            <SignalDetail signal={conflict.signal_b} />
          </div>
        ) : (
          <div className="p-4 rounded-lg bg-gray-500/5 border border-gray-500/20 flex items-center justify-center">
            <span className="text-gray-500">无对比信号</span>
          </div>
        )}
      </div>

      {/* 影响说明 */}
      <div className="mb-4 p-3 rounded-lg bg-yellow-500/5">
        <div className="flex items-start gap-2">
          <WarningOutlined className="text-yellow-400 mt-1" />
          <div>
            <div className="text-yellow-400 font-medium mb-1">潜在影响</div>
            <div className="text-gray-400 text-sm">{conflict.impact}</div>
          </div>
        </div>
      </div>

      <Divider className="my-4" />

      {/* 解决方案选择 */}
      <div className="mb-4">
        <div className="flex items-center justify-between mb-3">
          <span className="font-semibold text-white">选择解决方案</span>
          {conflict.expires_at && (
            <span className="text-gray-500 text-sm flex items-center gap-1">
              <ClockCircleOutlined />
              剩余时间: {getRemainingTime(conflict.expires_at)}
            </span>
          )}
        </div>

        <Radio.Group
          value={selectedResolution}
          onChange={(e) => setSelectedResolution(e.target.value)}
          className="w-full"
        >
          <Space direction="vertical" className="w-full">
            {allResolutions.map((resolution) => {
              const config = RESOLUTION_CONFIG[resolution]
              const isRecommended = resolution === conflict.suggested_resolution
              return (
                <Radio
                  key={resolution}
                  value={resolution}
                  className={`w-full p-3 rounded-lg border transition-colors ${
                    selectedResolution === resolution
                      ? 'border-blue-500 bg-blue-500/10'
                      : 'border-gray-700 hover:border-gray-600'
                  }`}
                >
                  <div className="flex items-start gap-2">
                    <span className="text-lg">{config.icon}</span>
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="text-white font-medium">{config.label}</span>
                        {isRecommended && (
                          <Tag color="green" className="text-xs">
                            推荐
                          </Tag>
                        )}
                      </div>
                      <div className="text-gray-500 text-sm">{config.description}</div>
                      {isRecommended && (
                        <div className="text-green-400 text-xs mt-1">
                          {conflict.resolution_reason}
                        </div>
                      )}
                    </div>
                  </div>
                </Radio>
              )
            })}
          </Space>
        </Radio.Group>
      </div>

      {/* 时间信息 */}
      <div className="text-gray-500 text-xs flex items-center gap-4">
        <span>检测时间: {formatConflictTime(conflict.detected_at)}</span>
      </div>
    </Modal>
  )
}

// 信号详情组件
function SignalDetail({ signal }: { signal: ConflictDetail['signal_a'] }) {
  return (
    <div className="space-y-2 text-sm">
      <div className="flex items-center justify-between">
        <span className="text-gray-500">股票</span>
        <span className="font-mono font-semibold text-white">{signal.symbol}</span>
      </div>
      <div className="flex items-center justify-between">
        <span className="text-gray-500">方向</span>
        <Tag color={signal.direction === 'buy' ? 'green' : 'red'}>
          {signal.direction === 'buy' ? '买入' : '卖出'}
        </Tag>
      </div>
      <div className="flex items-center justify-between">
        <span className="text-gray-500">数量</span>
        <span className="font-mono text-gray-300">{signal.quantity}</span>
      </div>
      <div className="flex items-center justify-between">
        <span className="text-gray-500">价格</span>
        <span className="font-mono text-gray-300">${signal.price.toFixed(2)}</span>
      </div>
      <div className="flex items-center justify-between">
        <span className="text-gray-500">信号强度</span>
        <Tooltip title={`信号强度: ${(signal.signal_strength * 100).toFixed(0)}%`}>
          <div className="w-16 h-2 bg-gray-700 rounded-full overflow-hidden">
            <div
              className="h-full bg-blue-500 rounded-full"
              style={{ width: `${signal.signal_strength * 100}%` }}
            />
          </div>
        </Tooltip>
      </div>
      <div className="flex items-center justify-between">
        <span className="text-gray-500">置信度</span>
        <span className="text-gray-300">{(signal.confidence * 100).toFixed(0)}%</span>
      </div>
      {signal.expected_return && (
        <div className="flex items-center justify-between">
          <span className="text-gray-500">预期收益</span>
          <span className="text-green-400">
            +{(signal.expected_return * 100).toFixed(1)}%
          </span>
        </div>
      )}
    </div>
  )
}
