/**
 * 策略模板库页面
 * PRD 4.13 策略模板库
 *
 * 数据源: 后端API / 内置模板库
 */
import { useState, useEffect, useCallback } from 'react'
import { Input, Select, Empty, Spin, Row, Col, message } from 'antd'
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
import { getTemplates, getTemplateDataSource } from '../../services/templateService'

export default function TemplatesPage() {
  const [templates, setTemplates] = useState<StrategyTemplate[]>([])
  const [loading, setLoading] = useState(true)
  const [, setDataSourceInfo] = useState<string>('')
  const [search, setSearch] = useState('')
  const [category, setCategory] = useState<TemplateCategory | 'all'>('all')
  const [difficulty, setDifficulty] = useState<DifficultyLevel | 'all'>('all')
  const [selectedTemplate, setSelectedTemplate] = useState<StrategyTemplate | null>(
    null
  )
  const [detailOpen, setDetailOpen] = useState(false)

  // 加载模板数据
  const loadTemplates = useCallback(async () => {
    setLoading(true)
    try {
      const data = await getTemplates()
      setTemplates(data)

      const source = getTemplateDataSource()
      if (source.source === 'builtin') {
        setDataSourceInfo('内置模板库')
      } else {
        setDataSourceInfo('')
      }
    } catch (err) {
      console.error('Failed to load templates:', err)
      message.error('加载模板失败')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadTemplates()
  }, [loadTemplates])

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
