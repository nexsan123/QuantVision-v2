/**
 * 归因报告面板组件
 * PRD 4.5 交易归因系统
 */
import { Progress, Tag, Tooltip, Statistic, Row, Col } from 'antd'
import {
  TrophyOutlined,
  RiseOutlined,
  FallOutlined,
  BarChartOutlined,
  ThunderboltOutlined,
  ClockCircleOutlined,
} from '@ant-design/icons'
import {
  AttributionReport,
  formatMoney,
  formatPercent,
  formatDate,
} from '../../types/tradeAttribution'

interface AttributionReportPanelProps {
  report: AttributionReport
  onViewDiagnosis?: () => void
}

export default function AttributionReportPanel({
  report,
  onViewDiagnosis,
}: AttributionReportPanelProps) {
  const winRateColor = report.win_rate >= 0.6 ? '#22c55e' : report.win_rate >= 0.5 ? '#3b82f6' : '#ef4444'
  const profitFactorColor = report.profit_factor >= 1.5 ? '#22c55e' : report.profit_factor >= 1.0 ? '#3b82f6' : '#ef4444'

  return (
    <div className="bg-dark-card rounded-lg overflow-hidden">
      {/* 头部 */}
      <div className="px-6 py-4 border-b border-gray-700">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-2xl">
              <BarChartOutlined />
            </span>
            <div>
              <h3 className="text-lg font-semibold text-white">
                归因报告
              </h3>
              <p className="text-gray-500 text-sm">
                {report.strategy_name} · {formatDate(report.period_start)} 至 {formatDate(report.period_end)}
              </p>
            </div>
          </div>
          <Tag color="blue">{report.trigger_reason}</Tag>
        </div>
      </div>

      {/* 核心指标 */}
      <div className="px-6 py-4 border-b border-gray-700">
        <Row gutter={[16, 16]}>
          <Col span={6}>
            <div className="text-center">
              <div className="text-gray-500 text-sm mb-1">总交易数</div>
              <div className="text-2xl font-bold text-white font-mono">
                {report.total_trades}
              </div>
              <div className="text-xs text-gray-500 mt-1">
                <span className="text-green-400">{report.win_trades}胜</span>
                {' / '}
                <span className="text-red-400">{report.loss_trades}负</span>
              </div>
            </div>
          </Col>
          <Col span={6}>
            <div className="text-center">
              <div className="text-gray-500 text-sm mb-1">胜率</div>
              <div className="text-2xl font-bold font-mono" style={{ color: winRateColor }}>
                {formatPercent(report.win_rate, 1)}
              </div>
              <Progress
                percent={report.win_rate * 100}
                showInfo={false}
                strokeColor={winRateColor}
                trailColor="#374151"
                size="small"
              />
            </div>
          </Col>
          <Col span={6}>
            <div className="text-center">
              <div className="text-gray-500 text-sm mb-1">盈亏比</div>
              <div className="text-2xl font-bold font-mono" style={{ color: profitFactorColor }}>
                {report.profit_factor.toFixed(2)}
              </div>
              <div className="text-xs text-gray-500 mt-1">
                平均盈利/平均亏损
              </div>
            </div>
          </Col>
          <Col span={6}>
            <div className="text-center">
              <div className="text-gray-500 text-sm mb-1">总收益</div>
              <div
                className={`text-2xl font-bold font-mono ${
                  report.total_pnl >= 0 ? 'text-green-400' : 'text-red-400'
                }`}
              >
                {formatMoney(report.total_pnl)}
              </div>
              <div
                className={`text-xs mt-1 ${
                  report.total_pnl_pct >= 0 ? 'text-green-400' : 'text-red-400'
                }`}
              >
                {formatPercent(report.total_pnl_pct)}
              </div>
            </div>
          </Col>
        </Row>
      </div>

      {/* 平均盈亏 */}
      <div className="px-6 py-4 border-b border-gray-700">
        <div className="grid grid-cols-2 gap-4">
          <div className="flex items-center gap-3 p-3 rounded-lg bg-green-500/5">
            <RiseOutlined className="text-green-400 text-xl" />
            <div>
              <div className="text-gray-500 text-sm">平均盈利</div>
              <div className="text-lg font-bold text-green-400 font-mono">
                {formatMoney(report.avg_win)}
              </div>
            </div>
          </div>
          <div className="flex items-center gap-3 p-3 rounded-lg bg-red-500/5">
            <FallOutlined className="text-red-400 text-xl" />
            <div>
              <div className="text-gray-500 text-sm">平均亏损</div>
              <div className="text-lg font-bold text-red-400 font-mono">
                -{formatMoney(report.avg_loss)}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 因子归因 */}
      <div className="px-6 py-4 border-b border-gray-700">
        <h4 className="text-white font-medium mb-3 flex items-center gap-2">
          <ThunderboltOutlined className="text-yellow-400" /> 因子归因
        </h4>
        <div className="space-y-2">
          {report.factor_attributions.map((factor, index) => (
            <div key={index} className="flex items-center gap-3">
              <span className="text-gray-400 text-sm w-24 truncate">
                {factor.factor_name}
              </span>
              <div className="flex-1">
                <Progress
                  percent={Math.min(Math.abs(factor.contribution_pct) * 100, 100)}
                  showInfo={false}
                  strokeColor={factor.is_positive ? '#22c55e' : '#ef4444'}
                  trailColor="#374151"
                  size="small"
                />
              </div>
              <span
                className={`font-mono text-sm w-20 text-right ${
                  factor.is_positive ? 'text-green-400' : 'text-red-400'
                }`}
              >
                {formatMoney(factor.contribution)}
              </span>
              <span className="text-gray-500 text-xs w-12 text-right">
                {formatPercent(factor.contribution_pct, 1)}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Alpha与市场归因 */}
      <div className="px-6 py-4 border-b border-gray-700">
        <h4 className="text-white font-medium mb-3 flex items-center gap-2">
          <TrophyOutlined className="text-purple-400" /> 收益分解
        </h4>
        <div className="grid grid-cols-2 gap-4">
          <div className="p-3 rounded-lg bg-purple-500/5">
            <div className="flex items-center justify-between">
              <span className="text-gray-400 text-sm">Alpha贡献</span>
              <Tooltip title="策略独立于市场的超额收益能力">
                <span className="text-gray-500 cursor-help">ⓘ</span>
              </Tooltip>
            </div>
            <div className="text-lg font-bold text-purple-400 font-mono mt-1">
              {formatPercent(report.alpha_attribution)}
            </div>
          </div>
          <div className="p-3 rounded-lg bg-blue-500/5">
            <div className="flex items-center justify-between">
              <span className="text-gray-400 text-sm">市场贡献</span>
              <Tooltip title="来自市场整体涨跌的收益">
                <span className="text-gray-500 cursor-help">ⓘ</span>
              </Tooltip>
            </div>
            <div
              className={`text-lg font-bold font-mono mt-1 ${
                report.market_attribution >= 0 ? 'text-blue-400' : 'text-red-400'
              }`}
            >
              {formatPercent(report.market_attribution)}
            </div>
          </div>
        </div>
      </div>

      {/* 市场环境分析 */}
      <div className="px-6 py-4 border-b border-gray-700">
        <h4 className="text-white font-medium mb-3">市场环境分析</h4>
        <div className="space-y-2">
          <div className="flex items-start gap-2">
            <span className="text-green-400">📈</span>
            <div>
              <span className="text-gray-500 text-sm">最佳环境: </span>
              <span className="text-gray-300 text-sm">{report.best_market_condition}</span>
            </div>
          </div>
          <div className="flex items-start gap-2">
            <span className="text-red-400">📉</span>
            <div>
              <span className="text-gray-500 text-sm">最差环境: </span>
              <span className="text-gray-300 text-sm">{report.worst_market_condition}</span>
            </div>
          </div>
        </div>
      </div>

      {/* 交易模式 */}
      <div className="px-6 py-4 border-b border-gray-700">
        <h4 className="text-white font-medium mb-3">识别到的交易模式</h4>
        <ul className="space-y-2">
          {report.patterns.map((pattern, index) => (
            <li key={index} className="flex items-start gap-2 text-gray-300 text-sm">
              <span className="text-blue-400">•</span>
              <span>{pattern}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* 底部 */}
      <div className="px-6 py-3 bg-dark-hover flex items-center justify-between">
        <span className="text-gray-500 text-xs flex items-center gap-1">
          <ClockCircleOutlined />
          生成时间: {new Date(report.created_at).toLocaleString('zh-CN')}
        </span>
        {onViewDiagnosis && (
          <button
            onClick={onViewDiagnosis}
            className="text-blue-400 text-sm hover:text-blue-300 transition-colors"
          >
            查看AI诊断 →
          </button>
        )}
      </div>
    </div>
  )
}
