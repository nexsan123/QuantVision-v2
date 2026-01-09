/**
 * 漂移报告面板组件
 * PRD 4.8 实盘vs回测差异监控
 */
import { Table, Button, Progress, Tag, Tooltip } from 'antd'
import {
  CheckCircleOutlined,
  PauseCircleOutlined,
  InfoCircleOutlined,
} from '@ant-design/icons'
import {
  StrategyDriftReport,
  DriftMetric,
  DRIFT_METRIC_LABELS,
  DRIFT_SEVERITY_CONFIG,
  formatDriftValue,
  formatDifferencePct,
  getDriftScoreLevel,
} from '../../types/drift'

interface DriftReportPanelProps {
  report: StrategyDriftReport
  onAcknowledge?: () => void
  onPauseStrategy?: () => void
}

export default function DriftReportPanel({
  report,
  onAcknowledge,
  onPauseStrategy,
}: DriftReportPanelProps) {
  const severityConfig = DRIFT_SEVERITY_CONFIG[report.overallSeverity]
  const scoreLevel = getDriftScoreLevel(report.driftScore)

  // 表格列定义
  const columns = [
    {
      title: '指标',
      dataIndex: 'metricType',
      key: 'metricType',
      render: (type: string) => (
        <span className="font-medium">{DRIFT_METRIC_LABELS[type as keyof typeof DRIFT_METRIC_LABELS]}</span>
      ),
    },
    {
      title: '回测',
      dataIndex: 'backtestValue',
      key: 'backtestValue',
      className: 'text-right font-mono',
      render: (value: number, record: DriftMetric) =>
        formatDriftValue(value, record.metricType),
    },
    {
      title: '实盘',
      dataIndex: 'liveValue',
      key: 'liveValue',
      className: 'text-right font-mono',
      render: (value: number, record: DriftMetric) =>
        formatDriftValue(value, record.metricType),
    },
    {
      title: '差异',
      dataIndex: 'differencePct',
      key: 'differencePct',
      className: 'text-right font-mono',
      render: (pct: number) => formatDifferencePct(pct),
    },
    {
      title: '状态',
      dataIndex: 'severity',
      key: 'severity',
      render: (severity: string) => {
        const config = DRIFT_SEVERITY_CONFIG[severity as keyof typeof DRIFT_SEVERITY_CONFIG]
        return (
          <Tag
            style={{
              backgroundColor: `${config.color}20`,
              color: config.color,
              border: 'none',
            }}
          >
            {config.icon} {config.text}
          </Tag>
        )
      },
    },
  ]

  return (
    <div className="bg-dark-card rounded-lg overflow-hidden">
      {/* 头部 */}
      <div
        className="px-6 py-4 border-b-2"
        style={{ borderColor: severityConfig.color }}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-2xl">{severityConfig.icon}</span>
            <div>
              <h3 className="text-lg font-semibold text-white">策略漂移报告</h3>
              <p className="text-gray-400 text-sm">
                {report.strategyName} ·{' '}
                {report.environment === 'live' ? '实盘' : '模拟盘'}
              </p>
            </div>
          </div>
          <Tag
            style={{
              backgroundColor: severityConfig.color,
              color: '#fff',
              fontSize: '14px',
              padding: '4px 12px',
            }}
          >
            {severityConfig.text}
          </Tag>
        </div>
        <div className="flex items-center gap-4 mt-3 text-gray-500 text-sm">
          <span>分析周期: {report.daysCompared}天</span>
          <span>
            {report.periodStart} ~ {report.periodEnd}
          </span>
        </div>
      </div>

      {/* 漂移评分 */}
      <div className="px-6 py-4 border-b border-gray-700">
        <div className="flex items-center gap-6">
          <div className="text-center">
            <div
              className="text-4xl font-bold"
              style={{ color: scoreLevel.color }}
            >
              {report.driftScore.toFixed(0)}
            </div>
            <div className="text-gray-500 text-sm">漂移评分</div>
          </div>
          <div className="flex-1">
            <Progress
              percent={report.driftScore}
              showInfo={false}
              strokeColor={{
                '0%': '#22c55e',
                '40%': '#eab308',
                '70%': '#ef4444',
              }}
              trailColor="#374151"
              size="small"
            />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>0 正常</span>
              <span>40 关注</span>
              <span>70 异常</span>
              <span>100</span>
            </div>
          </div>
        </div>
      </div>

      {/* 指标对比表格 */}
      <div className="px-6 py-4 border-b border-gray-700">
        <h4 className="text-white font-medium mb-3 flex items-center gap-2">
          <InfoCircleOutlined />
          指标对比
        </h4>
        <Table
          dataSource={report.metrics}
          columns={columns}
          rowKey="metricType"
          pagination={false}
          size="small"
          rowClassName={(record) => {
            if (record.severity === 'critical') return 'bg-red-500/5'
            if (record.severity === 'warning') return 'bg-yellow-500/5'
            return ''
          }}
        />
      </div>

      {/* 建议 */}
      <div className="px-6 py-4 border-b border-gray-700">
        <h4 className="text-white font-medium mb-3">建议</h4>
        <ul className="space-y-2">
          {report.recommendations.map((rec, index) => (
            <li key={index} className="flex items-start gap-2 text-gray-300 text-sm">
              <span className="text-gray-500">•</span>
              <span>{rec}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* 操作按钮 */}
      <div className="px-6 py-4 flex items-center justify-end gap-3">
        {report.shouldPause && onPauseStrategy && (
          <Button
            danger
            icon={<PauseCircleOutlined />}
            onClick={onPauseStrategy}
          >
            暂停策略
          </Button>
        )}
        {!report.isAcknowledged && onAcknowledge && (
          <Tooltip title="标记为已阅读，表示已知晓该漂移情况">
            <Button icon={<CheckCircleOutlined />} onClick={onAcknowledge}>
              我已知晓
            </Button>
          </Tooltip>
        )}
        {report.isAcknowledged && (
          <Tag color="green" icon={<CheckCircleOutlined />}>
            已确认
          </Tag>
        )}
      </div>
    </div>
  )
}
