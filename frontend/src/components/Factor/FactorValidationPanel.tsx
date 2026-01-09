/**
 * 因子有效性验证面板组件
 * PRD 4.3 因子有效性验证
 */
import { Progress, Tag, Tooltip, Button, Divider } from 'antd'
import {
  ExperimentOutlined,
  InfoCircleOutlined,
  BulbOutlined,
  WarningOutlined,
  PlusOutlined,
  SwapOutlined,
} from '@ant-design/icons'
import {
  FactorValidationResult,
  EFFECTIVENESS_LEVEL_CONFIG,
  FACTOR_CATEGORY_CONFIG,
  formatPercent,
  generateStars,
} from '../../types/factorValidation'

interface FactorValidationPanelProps {
  result: FactorValidationResult
  onCompare?: () => void
  onAddToStrategy?: () => void
}

export default function FactorValidationPanel({
  result,
  onCompare,
  onAddToStrategy,
}: FactorValidationPanelProps) {
  const levelConfig = EFFECTIVENESS_LEVEL_CONFIG[result.effectivenessLevel]
  const categoryConfig = FACTOR_CATEGORY_CONFIG[result.factorCategory] || {
    label: '其他',
    icon: '📊',
    color: '#6b7280',
  }

  return (
    <div className="bg-dark-card rounded-lg overflow-hidden">
      {/* 头部 */}
      <div className="px-6 py-4 border-b border-gray-700">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-2xl">
              <ExperimentOutlined />
            </span>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-lg font-semibold text-white">
                  {result.factorName}
                </h3>
                <Tag
                  style={{
                    backgroundColor: `${categoryConfig.color}20`,
                    color: categoryConfig.color,
                    border: 'none',
                  }}
                >
                  {categoryConfig.icon} {categoryConfig.label}
                </Tag>
              </div>
              <p className="text-gray-500 text-sm">{result.factorId}</p>
            </div>
          </div>
          <div className="text-right">
            <div className="flex items-center gap-2">
              <span className="text-gray-400">有效性:</span>
              <Tag
                style={{
                  backgroundColor: levelConfig.color,
                  color: '#fff',
                  fontSize: '14px',
                  padding: '2px 12px',
                }}
              >
                {levelConfig.label}
              </Tag>
            </div>
            <div className="text-yellow-400 mt-1">
              {generateStars(levelConfig.stars)}
            </div>
          </div>
        </div>
      </div>

      {/* 通俗解释 */}
      <div className="px-6 py-4 border-b border-gray-700 bg-blue-500/5">
        <h4 className="text-white font-medium mb-2 flex items-center gap-2">
          <span>📖</span> 通俗解释
        </h4>
        <p className="text-gray-300 text-sm leading-relaxed">
          {result.plainDescription}
        </p>
        <p className="text-gray-400 text-sm mt-2 leading-relaxed">
          {result.investmentLogic}
        </p>
      </div>

      {/* 核心指标 */}
      <div className="px-6 py-4 border-b border-gray-700">
        <div className="grid grid-cols-3 gap-4">
          <div className="text-center">
            <div className="text-gray-500 text-sm mb-1">IC均值</div>
            <div className="text-xl font-bold text-white font-mono">
              {formatPercent(result.icStats.icMean)}
            </div>
          </div>
          <div className="text-center">
            <div className="text-gray-500 text-sm mb-1">IC_IR</div>
            <div
              className="text-xl font-bold font-mono"
              style={{ color: levelConfig.color }}
            >
              {result.icStats.icIr.toFixed(2)}
            </div>
          </div>
          <div className="text-center">
            <div className="text-gray-500 text-sm mb-1">多空收益差</div>
            <div className="text-xl font-bold text-green-400 font-mono">
              {formatPercent(result.returnStats.longShortSpread)}
            </div>
          </div>
        </div>
      </div>

      {/* 分组收益 */}
      <div className="px-6 py-4 border-b border-gray-700">
        <h4 className="text-white font-medium mb-3 flex items-center gap-2">
          <span>📊</span> 分组收益
        </h4>
        <div className="space-y-2">
          {result.returnStats.groupReturns.map((ret, index) => (
            <div key={index} className="flex items-center gap-3">
              <span className="text-gray-400 text-sm w-20">
                {result.returnStats.groupLabels[index]}
              </span>
              <div className="flex-1">
                <Progress
                  percent={Math.abs(ret) * 100 * 3}
                  showInfo={false}
                  strokeColor={ret >= 0 ? '#22c55e' : '#ef4444'}
                  trailColor="#374151"
                  size="small"
                />
              </div>
              <span
                className={`font-mono text-sm w-16 text-right ${
                  ret >= 0 ? 'text-green-400' : 'text-red-400'
                }`}
              >
                {formatPercent(ret)}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* 使用建议 */}
      <div className="px-6 py-4 border-b border-gray-700">
        <h4 className="text-white font-medium mb-3 flex items-center gap-2">
          <BulbOutlined className="text-yellow-400" /> 使用建议
        </h4>
        <ul className="space-y-2">
          {result.usageTips.map((tip, index) => (
            <li key={index} className="flex items-start gap-2 text-gray-300 text-sm">
              <span className="text-blue-400">•</span>
              <span>{tip}</span>
            </li>
          ))}
        </ul>
        {result.suggestedCombinations.length > 0 && (
          <div className="mt-3 flex items-center gap-2 flex-wrap">
            <span className="text-gray-500 text-sm">推荐搭配:</span>
            {result.suggestedCombinations.map((factor) => (
              <Tag key={factor} color="blue">
                {factor}
              </Tag>
            ))}
          </div>
        )}
      </div>

      {/* 风险提示 */}
      <div className="px-6 py-4 border-b border-gray-700 bg-red-500/5">
        <h4 className="text-white font-medium mb-3 flex items-center gap-2">
          <WarningOutlined className="text-red-400" /> 风险提示
        </h4>
        <ul className="space-y-2">
          {result.riskWarnings.map((warning, index) => (
            <li key={index} className="flex items-start gap-2 text-gray-400 text-sm">
              <span className="text-red-400">!</span>
              <span>{warning}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* 元数据 */}
      <div className="px-6 py-3 bg-dark-hover flex items-center justify-between text-gray-500 text-xs">
        <span>数据区间: {result.dataPeriod}</span>
        <span>样本量: {result.sampleSize.toLocaleString()}</span>
        <span>验证日期: {result.validationDate}</span>
      </div>

      {/* 操作按钮 */}
      <div className="px-6 py-4 flex items-center justify-end gap-3">
        {onCompare && (
          <Button icon={<SwapOutlined />} onClick={onCompare}>
            对比其他因子
          </Button>
        )}
        {onAddToStrategy && (
          <Button type="primary" icon={<PlusOutlined />} onClick={onAddToStrategy}>
            添加到策略
          </Button>
        )}
      </div>
    </div>
  )
}
