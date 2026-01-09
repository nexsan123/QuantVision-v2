/**
 * 策略模板库页面
 * PRD 4.13 策略模板库
 */
import { useState, useEffect } from 'react'
import { Input, Select, Empty, Spin, Row, Col } from 'antd'
import { SearchOutlined, BookOutlined, FilterOutlined } from '@ant-design/icons'
import {
  StrategyTemplate,
  TemplateCategory,
  DifficultyLevel,
  CATEGORY_CONFIG,
  DIFFICULTY_CONFIG,
} from '../../types/strategyTemplate'
import TemplateCard from '../../components/Template/TemplateCard'
import TemplateDetailModal from '../../components/Template/TemplateDetailModal'

// 模拟API调用
const mockTemplates: StrategyTemplate[] = [
  {
    template_id: 'tpl-value-buffett',
    name: '巴菲特价值',
    description: '基于巴菲特投资理念，寻找具有护城河的优质低估值公司。适合长期持有，追求稳健增值。',
    category: 'value',
    difficulty: 'beginner',
    holding_period: 'long_term',
    risk_level: 'low',
    expected_annual_return: '10-15%',
    max_drawdown: '15-20%',
    sharpe_ratio: '0.8-1.2',
    strategy_config: {
      factors: [
        { id: 'PE_TTM', weight: 0.3 },
        { id: 'ROE', weight: 0.3 },
      ],
      universe: 'S&P 500',
      rebalance_frequency: 'monthly',
      position_count: 20,
    },
    user_count: 1523,
    rating: 4.5,
    tags: ['经典策略', '低风险', '长线投资'],
    icon: '💎',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    template_id: 'tpl-momentum-breakout',
    name: '动量突破',
    description: '追踪强势股票的价格突破，顺势加仓。适合趋势行情，需要较强的执行力。',
    category: 'momentum',
    difficulty: 'intermediate',
    holding_period: 'short_term',
    risk_level: 'medium',
    expected_annual_return: '15-25%',
    max_drawdown: '20-30%',
    sharpe_ratio: '1.0-1.5',
    strategy_config: {
      factors: [
        { id: 'MOMENTUM_3M', weight: 0.4 },
        { id: 'VOLUME_RATIO', weight: 0.3 },
      ],
      universe: 'NASDAQ 100',
      rebalance_frequency: 'weekly',
      position_count: 10,
    },
    user_count: 892,
    rating: 4.2,
    tags: ['趋势跟踪', '高收益', '需要盯盘'],
    icon: '🚀',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    template_id: 'tpl-dividend-low-vol',
    name: '低波红利',
    description: '选择高股息率且波动较低的股票，追求稳定的现金流收益。适合稳健型投资者。',
    category: 'dividend',
    difficulty: 'beginner',
    holding_period: 'long_term',
    risk_level: 'low',
    expected_annual_return: '8-12%',
    max_drawdown: '10-15%',
    sharpe_ratio: '1.0-1.4',
    strategy_config: {
      factors: [
        { id: 'DIVIDEND_YIELD', weight: 0.4 },
        { id: 'VOLATILITY', weight: 0.3 },
      ],
      universe: 'S&P 500',
      rebalance_frequency: 'quarterly',
      position_count: 30,
    },
    user_count: 1105,
    rating: 4.6,
    tags: ['稳健收益', '现金分红', '防守型'],
    icon: '💰',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    template_id: 'tpl-multi-factor',
    name: '多因子增强',
    description: '综合价值、动量、质量、低波动等多个因子，构建风险调整后收益最优的组合。',
    category: 'multi_factor',
    difficulty: 'advanced',
    holding_period: 'medium_term',
    risk_level: 'medium',
    expected_annual_return: '12-18%',
    max_drawdown: '18-25%',
    sharpe_ratio: '1.2-1.8',
    strategy_config: {
      factors: [
        { id: 'PE_TTM', weight: 0.15 },
        { id: 'MOMENTUM', weight: 0.2 },
        { id: 'ROE', weight: 0.2 },
      ],
      universe: 'Russell 1000',
      rebalance_frequency: 'bi-weekly',
      position_count: 50,
    },
    user_count: 567,
    rating: 4.3,
    tags: ['量化策略', '因子投资', '专业级'],
    icon: '🔬',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    template_id: 'tpl-sector-rotation',
    name: '行业轮动',
    description: '根据宏观经济周期和行业相对强弱，动态调整行业配置，追求超额收益。',
    category: 'timing',
    difficulty: 'advanced',
    holding_period: 'medium_term',
    risk_level: 'medium',
    expected_annual_return: '15-20%',
    max_drawdown: '20-28%',
    sharpe_ratio: '1.1-1.6',
    strategy_config: {
      factors: [
        { id: 'SECTOR_MOMENTUM', weight: 0.3 },
        { id: 'SECTOR_BREADTH', weight: 0.25 },
      ],
      universe: 'Sector ETFs',
      rebalance_frequency: 'weekly',
      position_count: 5,
    },
    user_count: 432,
    rating: 4.1,
    tags: ['行业ETF', '宏观择时', '高换手'],
    icon: '🔄',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    template_id: 'tpl-intraday-momentum',
    name: '日内动量',
    description: '捕捉日内价格动量，快速进出。高频交易，需要严格的风控和执行纪律。',
    category: 'intraday',
    difficulty: 'advanced',
    holding_period: 'intraday',
    risk_level: 'high',
    expected_annual_return: '20-40%',
    max_drawdown: '25-35%',
    sharpe_ratio: '1.5-2.5',
    strategy_config: {
      factors: [
        { id: 'PRICE_MOMENTUM_5MIN', weight: 0.3 },
        { id: 'VOLUME_SURGE', weight: 0.25 },
      ],
      universe: 'High Volume 100',
      rebalance_frequency: 'intraday',
      position_count: 5,
    },
    user_count: 289,
    rating: 3.9,
    tags: ['高频交易', '日内平仓', '高风险高收益'],
    icon: '⚡',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
]

export default function TemplatesPage() {
  const [templates, setTemplates] = useState<StrategyTemplate[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [category, setCategory] = useState<TemplateCategory | 'all'>('all')
  const [difficulty, setDifficulty] = useState<DifficultyLevel | 'all'>('all')
  const [selectedTemplate, setSelectedTemplate] = useState<StrategyTemplate | null>(
    null
  )
  const [detailOpen, setDetailOpen] = useState(false)

  useEffect(() => {
    // 模拟API调用
    setTimeout(() => {
      setTemplates(mockTemplates)
      setLoading(false)
    }, 500)
  }, [])

  // 筛选模板
  const filteredTemplates = templates.filter((t) => {
    if (category !== 'all' && t.category !== category) return false
    if (difficulty !== 'all' && t.difficulty !== difficulty) return false
    if (search) {
      const searchLower = search.toLowerCase()
      return (
        t.name.toLowerCase().includes(searchLower) ||
        t.description.toLowerCase().includes(searchLower) ||
        t.tags.some((tag) => tag.toLowerCase().includes(searchLower))
      )
    }
    return true
  })

  const categoryOptions = [
    { value: 'all', label: '全部分类' },
    ...Object.entries(CATEGORY_CONFIG).map(([key, config]) => ({
      value: key,
      label: `${config.icon} ${config.label}`,
    })),
  ]

  const difficultyOptions = [
    { value: 'all', label: '全部难度' },
    ...Object.entries(DIFFICULTY_CONFIG).map(([key, config]) => ({
      value: key,
      label: `${'⭐'.repeat(config.stars)} ${config.label}`,
    })),
  ]

  return (
    <div className="p-6">
      {/* 头部 */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white flex items-center gap-3">
          <BookOutlined className="text-blue-400" />
          策略模板库
        </h1>
        <p className="text-gray-400 mt-1">
          选择预设模板，一键部署开始交易
        </p>
      </div>

      {/* 筛选栏 */}
      <div className="mb-6 flex items-center gap-4">
        <Input
          placeholder="搜索模板..."
          prefix={<SearchOutlined className="text-gray-500" />}
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{ width: 300 }}
          allowClear
        />
        <Select
          value={category}
          onChange={setCategory}
          options={categoryOptions}
          style={{ width: 150 }}
          prefix={<FilterOutlined />}
        />
        <Select
          value={difficulty}
          onChange={setDifficulty}
          options={difficultyOptions}
          style={{ width: 150 }}
        />
        <span className="text-gray-500 ml-auto">
          共 {filteredTemplates.length} 个模板
        </span>
      </div>

      {/* 模板列表 */}
      {loading ? (
        <div className="flex justify-center py-20">
          <Spin size="large" />
        </div>
      ) : filteredTemplates.length === 0 ? (
        <Empty
          description="暂无匹配的模板"
          className="py-20"
        />
      ) : (
        <Row gutter={[16, 16]}>
          {filteredTemplates.map((template) => (
            <Col key={template.template_id} xs={24} sm={12} lg={8} xl={6}>
              <TemplateCard
                template={template}
                onClick={() => {
                  setSelectedTemplate(template)
                  setDetailOpen(true)
                }}
              />
            </Col>
          ))}
        </Row>
      )}

      {/* 详情弹窗 */}
      <TemplateDetailModal
        template={selectedTemplate}
        open={detailOpen}
        onClose={() => {
          setDetailOpen(false)
          setSelectedTemplate(null)
        }}
      />
    </div>
  )
}
