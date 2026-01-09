/**
 * 模板详情弹窗组件
 * PRD 4.13 策略模板库
 *
 * 修改: 使用模板创建策略副本，而非直接部署
 */
import { useState } from 'react'
import {
  Modal,
  Tag,
  Input,
  Button,
  Divider,
  message,
  Descriptions,
} from 'antd'
import {
  RocketOutlined,
  UserOutlined,
  ThunderboltOutlined,
  EditOutlined,
  LineChartOutlined,
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import {
  StrategyTemplate,
  CATEGORY_CONFIG,
  DIFFICULTY_CONFIG,
  HOLDING_PERIOD_CONFIG,
  RISK_LEVEL_CONFIG,
  generateDifficultyStars,
  formatUserCount,
} from '../../types/strategyTemplate'
import { createStrategy } from '../../services/strategyService'
import type { StrategyConfig } from '../../types/strategy'
import {
  DEFAULT_UNIVERSE_CONFIG,
  DEFAULT_ALPHA_CONFIG,
  DEFAULT_SIGNAL_CONFIG,
  DEFAULT_RISK_CONFIG,
  DEFAULT_PORTFOLIO_CONFIG,
  DEFAULT_EXECUTION_CONFIG,
  DEFAULT_MONITOR_CONFIG,
} from '../../types/strategy'

interface TemplateDetailModalProps {
  template: StrategyTemplate | null
  open: boolean
  onClose: () => void
}

export default function TemplateDetailModal({
  template,
  open,
  onClose,
}: TemplateDetailModalProps) {
  const navigate = useNavigate()
  const [strategyName, setStrategyName] = useState('')
  const [creating, setCreating] = useState(false)

  if (!template) return null

  const categoryConfig = CATEGORY_CONFIG[template.category]
  const difficultyConfig = DIFFICULTY_CONFIG[template.difficulty]
  const holdingConfig = HOLDING_PERIOD_CONFIG[template.holding_period]
  const riskConfig = RISK_LEVEL_CONFIG[template.risk_level]

  // 从模板创建策略配置
  const buildStrategyConfig = (): StrategyConfig => {
    // 将模板的配置映射到完整的7步策略配置
    return {
      name: strategyName.trim() || `我的${template.name}`,
      description: template.description,
      status: 'draft',
      universe: {
        ...DEFAULT_UNIVERSE_CONFIG,
        // 根据模板的universe字段设置基础股票池
        basePool: template.strategy_config.universe?.includes('500') ? 'SP500' :
                  template.strategy_config.universe?.includes('NASDAQ') ? 'NASDAQ100' :
                  template.strategy_config.universe?.includes('Russell') ? 'RUSSELL1000' : 'SP500',
      },
      alpha: {
        ...DEFAULT_ALPHA_CONFIG,
        factors: template.strategy_config.factors?.map((f: { id: string; weight: number }) => ({
          factorId: f.id,
          expression: f.id,
          weight: f.weight,
          direction: 1 as const,
          lookbackPeriod: 20,
        })) || [],
      },
      signal: {
        ...DEFAULT_SIGNAL_CONFIG,
        targetPositions: template.strategy_config.position_count || 20,
      },
      risk: DEFAULT_RISK_CONFIG,
      portfolio: {
        ...DEFAULT_PORTFOLIO_CONFIG,
        maxHoldings: template.strategy_config.position_count || 50,
        rebalanceFrequency:
          template.strategy_config.rebalance_frequency === 'weekly' ? 'weekly' :
          template.strategy_config.rebalance_frequency === 'bi-weekly' ? 'biweekly' :
          template.strategy_config.rebalance_frequency === 'quarterly' ? 'quarterly' : 'monthly',
      },
      execution: DEFAULT_EXECUTION_CONFIG,
      monitor: DEFAULT_MONITOR_CONFIG,
    }
  }

  // 使用模板 - 创建策略并跳转到编辑器
  const handleUseTemplate = async () => {
    const name = strategyName.trim() || `我的${template.name}`

    setCreating(true)
    try {
      const config = buildStrategyConfig()
      const newStrategy = await createStrategy({
        name,
        description: template.description,
        source: 'template',
        templateId: template.template_id,
        config,
        tags: template.tags,
      })

      message.success('策略已创建，可以开始自定义配置')
      onClose()
      setStrategyName('')
      navigate(`/strategy?id=${newStrategy.id}`)
    } catch {
      message.error('创建失败，请重试')
    } finally {
      setCreating(false)
    }
  }

  // 运行回测 - 创建策略并跳转到回测页面
  const handleRunBacktest = async () => {
    const name = strategyName.trim() || `我的${template.name}`

    setCreating(true)
    try {
      const config = buildStrategyConfig()
      const newStrategy = await createStrategy({
        name,
        description: template.description,
        source: 'template',
        templateId: template.template_id,
        config,
        tags: template.tags,
      })

      message.success('策略已创建，正在跳转到回测中心')
      onClose()
      setStrategyName('')
      navigate(`/backtest?strategyId=${newStrategy.id}`)
    } catch {
      message.error('创建失败，请重试')
    } finally {
      setCreating(false)
    }
  }

  return (
    <Modal
      title={
        <div className="flex items-center gap-3">
          <span className="text-3xl">{template.icon}</span>
          <div>
            <div className="text-lg font-semibold">{template.name}</div>
            <Tag
              style={{
                backgroundColor: `${categoryConfig.color}20`,
                color: categoryConfig.color,
                border: 'none',
              }}
            >
              {categoryConfig.label}
            </Tag>
          </div>
        </div>
      }
      open={open}
      onCancel={onClose}
      width={700}
      footer={null}
    >
      {/* 基本信息 */}
      <div className="grid grid-cols-4 gap-4 mb-4">
        <div className="text-center p-3 rounded-lg bg-gray-800">
          <div className="text-gray-500 text-xs mb-1">难度</div>
          <div className="text-yellow-400">{generateDifficultyStars(template.difficulty)}</div>
          <div className="text-white text-sm">{difficultyConfig.label}</div>
        </div>
        <div className="text-center p-3 rounded-lg bg-gray-800">
          <div className="text-gray-500 text-xs mb-1">持仓周期</div>
          <div className="text-white text-lg font-semibold">{holdingConfig.label}</div>
        </div>
        <div className="text-center p-3 rounded-lg bg-gray-800">
          <div className="text-gray-500 text-xs mb-1">预期年化</div>
          <div className="text-green-400 text-lg font-semibold">
            {template.expected_annual_return}
          </div>
        </div>
        <div className="text-center p-3 rounded-lg bg-gray-800">
          <div className="text-gray-500 text-xs mb-1">风险等级</div>
          <div
            className="text-lg font-semibold"
            style={{ color: riskConfig.color }}
          >
            {riskConfig.label}
          </div>
        </div>
      </div>

      {/* 描述 */}
      <div className="mb-4 p-4 rounded-lg bg-gray-800/50">
        <p className="text-gray-300">{template.description}</p>
      </div>

      {/* 性能指标 */}
      <Descriptions
        column={3}
        size="small"
        className="mb-4"
        labelStyle={{ color: '#9ca3af' }}
        contentStyle={{ color: '#fff' }}
      >
        <Descriptions.Item label="最大回撤">{template.max_drawdown}</Descriptions.Item>
        <Descriptions.Item label="夏普比率">{template.sharpe_ratio}</Descriptions.Item>
        <Descriptions.Item label="使用人数">
          <span className="flex items-center gap-1">
            <UserOutlined /> {formatUserCount(template.user_count)}
          </span>
        </Descriptions.Item>
      </Descriptions>

      {/* 策略配置预览 */}
      <div className="mb-4">
        <h4 className="text-white font-medium mb-2 flex items-center gap-2">
          <ThunderboltOutlined className="text-yellow-400" /> 策略配置
        </h4>
        <div className="p-4 rounded-lg bg-gray-800/50 text-sm">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <span className="text-gray-500">选股范围: </span>
              <span className="text-white">
                {template.strategy_config.universe || 'S&P 500'}
              </span>
            </div>
            <div>
              <span className="text-gray-500">调仓频率: </span>
              <span className="text-white">
                {template.strategy_config.rebalance_frequency || 'monthly'}
              </span>
            </div>
            <div>
              <span className="text-gray-500">持仓数量: </span>
              <span className="text-white">
                {template.strategy_config.position_count || 20}
              </span>
            </div>
            <div>
              <span className="text-gray-500">因子数量: </span>
              <span className="text-white">
                {template.strategy_config.factors?.length || 0}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* 标签 */}
      {template.tags.length > 0 && (
        <div className="mb-4">
          <div className="flex flex-wrap gap-2">
            {template.tags.map((tag) => (
              <Tag key={tag} color="blue">
                {tag}
              </Tag>
            ))}
          </div>
        </div>
      )}

      <Divider className="my-4" />

      {/* 使用模板表单 */}
      <div className="mb-4">
        <h4 className="text-white font-medium mb-3 flex items-center gap-2">
          <RocketOutlined className="text-blue-400" /> 使用此模板
        </h4>

        <div className="space-y-4">
          <div>
            <label className="text-gray-400 text-sm mb-1 block">策略名称</label>
            <Input
              placeholder={`我的${template.name}`}
              value={strategyName}
              onChange={(e) => setStrategyName(e.target.value)}
              maxLength={50}
            />
            <div className="text-xs text-gray-500 mt-1">
              将以此模板为基础创建您自己的策略副本
            </div>
          </div>
        </div>
      </div>

      {/* 操作按钮 */}
      <div className="flex justify-end gap-3">
        <Button onClick={onClose}>取消</Button>
        <Button
          icon={<EditOutlined />}
          onClick={handleUseTemplate}
          loading={creating}
        >
          自定义配置
        </Button>
        <Button
          type="primary"
          icon={<LineChartOutlined />}
          onClick={handleRunBacktest}
          loading={creating}
          size="large"
        >
          直接回测
        </Button>
      </div>
    </Modal>
  )
}
