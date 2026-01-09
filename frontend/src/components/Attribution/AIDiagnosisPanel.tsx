/**
 * AI诊断面板组件
 * PRD 4.5 交易归因系统
 */
import { Progress, Tag, Alert } from 'antd'
import {
  RobotOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  BulbOutlined,
  WarningOutlined,
  SafetyOutlined,
} from '@ant-design/icons'
import { AIDiagnosis } from '../../types/tradeAttribution'

interface AIDiagnosisPanelProps {
  diagnosis: AIDiagnosis
  onClose?: () => void
}

export default function AIDiagnosisPanel({
  diagnosis,
  onClose,
}: AIDiagnosisPanelProps) {
  const confidenceColor =
    diagnosis.confidence >= 0.8 ? '#22c55e' : diagnosis.confidence >= 0.6 ? '#3b82f6' : '#eab308'

  return (
    <div className="bg-dark-card rounded-lg overflow-hidden">
      {/* 头部 */}
      <div className="px-6 py-4 border-b border-gray-700 bg-gradient-to-r from-purple-500/10 to-blue-500/10">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-2xl text-purple-400">
              <RobotOutlined />
            </span>
            <div>
              <h3 className="text-lg font-semibold text-white">
                AI 诊断报告
              </h3>
              <p className="text-gray-500 text-sm">
                基于归因分析的智能诊断
              </p>
            </div>
          </div>
          <div className="text-right">
            <div className="flex items-center gap-2">
              <span className="text-gray-400 text-sm">置信度</span>
              <Tag
                style={{
                  backgroundColor: `${confidenceColor}20`,
                  color: confidenceColor,
                  border: 'none',
                }}
              >
                {(diagnosis.confidence * 100).toFixed(0)}%
              </Tag>
            </div>
            <Progress
              percent={diagnosis.confidence * 100}
              showInfo={false}
              strokeColor={confidenceColor}
              trailColor="#374151"
              size="small"
              style={{ width: 100 }}
            />
          </div>
        </div>
      </div>

      {/* 诊断摘要 */}
      <div className="px-6 py-4 border-b border-gray-700">
        <div className="flex items-start gap-3 p-4 rounded-lg bg-blue-500/5">
          <SafetyOutlined className="text-blue-400 text-xl mt-1" />
          <div>
            <h4 className="text-white font-medium mb-2">诊断摘要</h4>
            <p className="text-gray-300 text-sm leading-relaxed">
              {diagnosis.summary}
            </p>
          </div>
        </div>
      </div>

      {/* 优势分析 */}
      <div className="px-6 py-4 border-b border-gray-700">
        <h4 className="text-white font-medium mb-3 flex items-center gap-2">
          <CheckCircleOutlined className="text-green-400" /> 优势分析
        </h4>
        <ul className="space-y-2">
          {diagnosis.strengths.map((strength, index) => (
            <li
              key={index}
              className="flex items-start gap-2 p-2 rounded bg-green-500/5"
            >
              <span className="text-green-400 mt-0.5">✔</span>
              <span className="text-gray-300 text-sm">{strength}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* 劣势分析 */}
      <div className="px-6 py-4 border-b border-gray-700">
        <h4 className="text-white font-medium mb-3 flex items-center gap-2">
          <CloseCircleOutlined className="text-red-400" /> 劣势分析
        </h4>
        <ul className="space-y-2">
          {diagnosis.weaknesses.map((weakness, index) => (
            <li
              key={index}
              className="flex items-start gap-2 p-2 rounded bg-red-500/5"
            >
              <span className="text-red-400 mt-0.5">✗</span>
              <span className="text-gray-300 text-sm">{weakness}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* 改进建议 */}
      <div className="px-6 py-4 border-b border-gray-700">
        <h4 className="text-white font-medium mb-3 flex items-center gap-2">
          <BulbOutlined className="text-yellow-400" /> 改进建议
        </h4>
        <ul className="space-y-2">
          {diagnosis.suggestions.map((suggestion, index) => (
            <li key={index} className="flex items-start gap-3">
              <span className="flex-shrink-0 w-6 h-6 rounded-full bg-yellow-500/20 text-yellow-400 text-xs flex items-center justify-center">
                {index + 1}
              </span>
              <span className="text-gray-300 text-sm">{suggestion}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* 风险提示 */}
      {diagnosis.risk_alerts.length > 0 && (
        <div className="px-6 py-4 border-b border-gray-700">
          <h4 className="text-white font-medium mb-3 flex items-center gap-2">
            <WarningOutlined className="text-orange-400" /> 风险提示
          </h4>
          <div className="space-y-2">
            {diagnosis.risk_alerts.map((alert, index) => (
              <Alert
                key={index}
                message={alert}
                type="warning"
                showIcon
                style={{
                  backgroundColor: 'rgba(251, 146, 60, 0.1)',
                  border: '1px solid rgba(251, 146, 60, 0.2)',
                }}
              />
            ))}
          </div>
        </div>
      )}

      {/* 底部 */}
      <div className="px-6 py-3 bg-dark-hover flex items-center justify-between">
        <span className="text-gray-500 text-xs">
          生成时间: {new Date(diagnosis.created_at).toLocaleString('zh-CN')}
        </span>
        {onClose && (
          <button
            onClick={onClose}
            className="text-gray-400 text-sm hover:text-white transition-colors"
          >
            关闭
          </button>
        )}
      </div>
    </div>
  )
}
