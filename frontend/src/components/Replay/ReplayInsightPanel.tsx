/**
 * 回放洞察面板
 * PRD 4.17.1 回放洞察面板
 *
 * 显示回放期间的统计和AI洞察
 */
import { Button, Progress } from 'antd'
import {
  FileTextOutlined,
  SaveOutlined,
  BulbOutlined,
} from '@ant-design/icons'
import { ReplayInsight, formatPercent } from '../../types/replay'

interface ReplayInsightPanelProps {
  insight: ReplayInsight | null
  onDetailReport: () => void
  onSaveReplay: () => void
}

export default function ReplayInsightPanel({
  insight,
  onDetailReport,
  onSaveReplay,
}: ReplayInsightPanelProps) {
  if (!insight) {
    return (
      <div className="bg-dark-card rounded-lg p-4">
        <div className="text-gray-500 text-center py-4">
          回放结束后显示洞察
        </div>
      </div>
    )
  }

  const getAlphaColor = (alpha: number) => {
    if (alpha > 0.05) return 'text-green-400'
    if (alpha < -0.05) return 'text-red-400'
    return 'text-yellow-400'
  }

  return (
    <div className="bg-dark-card rounded-lg overflow-hidden">
      {/* 头部 */}
      <div className="px-4 py-3 border-b border-gray-700 flex items-center gap-2">
        <span className="text-lg">🎯</span>
        <span className="text-white font-medium">回放洞察</span>
      </div>

      <div className="p-4 space-y-4">
        {/* 统计指标 */}
        <div className="grid grid-cols-2 gap-3">
          <div className="bg-gray-800/50 rounded p-3">
            <div className="text-gray-400 text-xs mb-1">信号数</div>
            <div className="text-white text-xl font-medium">
              {insight.totalSignals}
            </div>
          </div>
          <div className="bg-gray-800/50 rounded p-3">
            <div className="text-gray-400 text-xs mb-1">执行率</div>
            <div className="text-white text-xl font-medium">
              {(insight.executionRate * 100).toFixed(0)}%
            </div>
          </div>
          <div className="bg-gray-800/50 rounded p-3">
            <div className="text-gray-400 text-xs mb-1">胜率</div>
            <div
              className={`text-xl font-medium ${
                insight.winRate >= 0.5 ? 'text-green-400' : 'text-red-400'
              }`}
            >
              {(insight.winRate * 100).toFixed(0)}%
            </div>
          </div>
          <div className="bg-gray-800/50 rounded p-3">
            <div className="text-gray-400 text-xs mb-1">Alpha</div>
            <div className={`text-xl font-medium ${getAlphaColor(insight.alpha)}`}>
              {formatPercent(insight.alpha)}
            </div>
          </div>
        </div>

        {/* 收益对比 */}
        <div>
          <div className="text-gray-400 text-sm mb-2">收益对比</div>
          <div className="space-y-2">
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-300">策略</span>
                <span
                  className={
                    insight.strategyReturn >= 0 ? 'text-green-400' : 'text-red-400'
                  }
                >
                  {formatPercent(insight.strategyReturn)}
                </span>
              </div>
              <Progress
                percent={Math.min(Math.abs(insight.strategyReturn) * 1000, 100)}
                showInfo={false}
                strokeColor={insight.strategyReturn >= 0 ? '#22c55e' : '#ef4444'}
                trailColor="#374151"
                size="small"
              />
            </div>
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-300">SPY基准</span>
                <span
                  className={
                    insight.benchmarkReturn >= 0 ? 'text-green-400' : 'text-red-400'
                  }
                >
                  {formatPercent(insight.benchmarkReturn)}
                </span>
              </div>
              <Progress
                percent={Math.min(Math.abs(insight.benchmarkReturn) * 1000, 100)}
                showInfo={false}
                strokeColor={insight.benchmarkReturn >= 0 ? '#3b82f6' : '#f59e0b'}
                trailColor="#374151"
                size="small"
              />
            </div>
          </div>
        </div>

        {/* AI洞察 */}
        {insight.aiInsights.length > 0 && (
          <div>
            <div className="flex items-center gap-2 text-gray-400 text-sm mb-2">
              <BulbOutlined className="text-yellow-400" />
              <span>AI洞察</span>
            </div>
            <div className="space-y-2">
              {insight.aiInsights.map((text, index) => (
                <div
                  key={index}
                  className="text-sm text-gray-300 bg-blue-900/20 border-l-2 border-blue-500 p-2 rounded-r"
                >
                  {text}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 操作按钮 */}
        <div className="flex gap-2 pt-2">
          <Button
            icon={<FileTextOutlined />}
            onClick={onDetailReport}
            className="flex-1"
          >
            详细报告
          </Button>
          <Button
            icon={<SaveOutlined />}
            onClick={onSaveReplay}
            className="flex-1"
          >
            保存回放
          </Button>
        </div>
      </div>
    </div>
  )
}
