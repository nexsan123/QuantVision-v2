/**
 * 因子值面板
 * PRD 4.17.1 因子值面板
 *
 * 显示当前时刻的因子值和满足状态
 */
import { Spin } from 'antd'
import { CheckCircleOutlined, CloseCircleOutlined } from '@ant-design/icons'
import { FactorSnapshot, REPLAY_COLORS } from '../../types/replay'

interface FactorPanelProps {
  snapshot: FactorSnapshot | null
  loading?: boolean
}

export default function FactorPanel({ snapshot, loading = false }: FactorPanelProps) {
  if (loading) {
    return (
      <div className="bg-dark-card rounded-lg p-4">
        <Spin />
      </div>
    )
  }

  if (!snapshot) {
    return (
      <div className="bg-dark-card rounded-lg p-4">
        <div className="text-gray-500 text-center py-4">
          选择日期范围开始回放
        </div>
      </div>
    )
  }

  const getSignalColor = (signal: string) => {
    switch (signal) {
      case 'buy':
        return 'text-green-400'
      case 'sell':
        return 'text-red-400'
      default:
        return 'text-gray-400'
    }
  }

  const getSignalLabel = (signal: string) => {
    switch (signal) {
      case 'buy':
        return '买入'
      case 'sell':
        return '卖出'
      default:
        return '持有'
    }
  }

  return (
    <div className="bg-dark-card rounded-lg overflow-hidden">
      {/* 头部 */}
      <div className="px-4 py-3 border-b border-gray-700 flex items-center gap-2">
        <span className="text-lg">📊</span>
        <span className="text-white font-medium">当前时刻因子值</span>
      </div>

      {/* 因子列表 */}
      <div className="p-4">
        <div className="space-y-2">
          {Object.entries(snapshot.thresholds).map(([name, config]) => (
            <div
              key={name}
              className={`flex items-center justify-between p-2 rounded ${
                config.passed ? 'bg-green-900/20' : 'bg-gray-800/30'
              }`}
            >
              <div className="flex items-center gap-2">
                <span
                  className={`w-2 h-2 rounded-full ${
                    config.passed ? 'bg-green-400' : 'bg-gray-500'
                  }`}
                />
                <span className="text-white text-sm">{name}</span>
              </div>

              <div className="flex items-center gap-3">
                <span className="text-white font-mono text-sm">
                  {snapshot.factorValues[name]?.toFixed(2) || '-'}
                </span>
                <span className="text-gray-500 text-xs">
                  ({config.direction === 'below' ? '<' : '>'}
                  {config.value})
                </span>
                {config.passed ? (
                  <CheckCircleOutlined
                    className="text-green-400"
                    style={{ color: REPLAY_COLORS.factorPassed }}
                  />
                ) : (
                  <CloseCircleOutlined
                    className="text-red-400"
                    style={{ color: REPLAY_COLORS.factorFailed }}
                  />
                )}
              </div>
            </div>
          ))}
        </div>

        {/* 综合信号 */}
        <div className="mt-4 pt-4 border-t border-gray-700">
          <div className="flex items-center justify-between">
            <span className="text-gray-400">综合信号</span>
            <div className="flex items-center gap-2">
              <span
                className={`text-lg font-medium ${getSignalColor(
                  snapshot.overallSignal
                )}`}
              >
                {getSignalLabel(snapshot.overallSignal)}
              </span>
              <span className="text-gray-500 text-sm">
                ({snapshot.conditionsMet}/{snapshot.conditionsTotal} 条件满足)
              </span>
            </div>
          </div>

          {/* 信号强度指示器 */}
          <div className="mt-2">
            <div className="flex gap-1">
              {Array.from({ length: snapshot.conditionsTotal }).map((_, i) => (
                <div
                  key={i}
                  className={`flex-1 h-2 rounded ${
                    i < snapshot.conditionsMet
                      ? snapshot.overallSignal === 'buy'
                        ? 'bg-green-500'
                        : snapshot.overallSignal === 'sell'
                        ? 'bg-red-500'
                        : 'bg-yellow-500'
                      : 'bg-gray-700'
                  }`}
                />
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
