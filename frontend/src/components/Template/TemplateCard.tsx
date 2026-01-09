/**
 * 模板卡片组件
 * PRD 4.13 策略模板库
 */
import { Tag, Rate, Tooltip } from 'antd'
import { UserOutlined, RightOutlined } from '@ant-design/icons'
import {
  StrategyTemplate,
  CATEGORY_CONFIG,
  DIFFICULTY_CONFIG,
  HOLDING_PERIOD_CONFIG,
  RISK_LEVEL_CONFIG,
  generateDifficultyStars,
  formatUserCount,
} from '../../types/strategyTemplate'

interface TemplateCardProps {
  template: StrategyTemplate
  onClick: () => void
}

export default function TemplateCard({ template, onClick }: TemplateCardProps) {
  const categoryConfig = CATEGORY_CONFIG[template.category]
  const difficultyConfig = DIFFICULTY_CONFIG[template.difficulty]
  const holdingConfig = HOLDING_PERIOD_CONFIG[template.holding_period]
  const riskConfig = RISK_LEVEL_CONFIG[template.risk_level]

  return (
    <div
      className="bg-dark-card rounded-lg p-5 border border-gray-700 hover:border-gray-600 cursor-pointer transition-all group"
      onClick={onClick}
    >
      {/* 头部 */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          <span className="text-3xl">{template.icon}</span>
          <div>
            <h3 className="text-lg font-semibold text-white group-hover:text-blue-400 transition-colors">
              {template.name}
            </h3>
            <Tag
              style={{
                backgroundColor: `${categoryConfig.color}20`,
                color: categoryConfig.color,
                border: 'none',
                fontSize: '11px',
              }}
            >
              {categoryConfig.label}
            </Tag>
          </div>
        </div>
        <RightOutlined className="text-gray-600 group-hover:text-gray-400 transition-colors" />
      </div>

      {/* 难度和周期 */}
      <div className="flex items-center gap-3 mb-3">
        <Tooltip title={difficultyConfig.description}>
          <span className="text-yellow-400 text-sm">
            {generateDifficultyStars(template.difficulty)} {difficultyConfig.label}
          </span>
        </Tooltip>
        <span className="text-gray-600">|</span>
        <span className="text-gray-400 text-sm">{holdingConfig.label}</span>
      </div>

      {/* 预期收益和风险 */}
      <div className="grid grid-cols-2 gap-3 mb-3">
        <div>
          <div className="text-gray-500 text-xs mb-1">预期年化</div>
          <div className="text-green-400 font-semibold">
            {template.expected_annual_return}
          </div>
        </div>
        <div>
          <div className="text-gray-500 text-xs mb-1">风险等级</div>
          <span
            className="font-semibold"
            style={{ color: riskConfig.color }}
          >
            {riskConfig.label}风险
          </span>
        </div>
      </div>

      {/* 描述 */}
      <p className="text-gray-400 text-sm mb-3 line-clamp-2">
        {template.description}
      </p>

      {/* 底部 */}
      <div className="flex items-center justify-between pt-3 border-t border-gray-700">
        <div className="flex items-center gap-1 text-gray-500 text-sm">
          <UserOutlined />
          <span>{formatUserCount(template.user_count)}人使用</span>
        </div>
        <Rate
          disabled
          value={template.rating}
          allowHalf
          style={{ fontSize: 12 }}
        />
      </div>
    </div>
  )
}
