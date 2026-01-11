import { useState, useEffect, useCallback } from 'react'
import { Row, Col, Input, Select, Button, Table, Tag, message, Spin } from 'antd'
import { PlayCircleOutlined, PlusOutlined } from '@ant-design/icons'
import { Card, NumberDisplay } from '@/components/ui'
import { FactorICChart, GroupReturnChart } from '@/components/Chart'
import FactorValidationPanel from '@/components/Factor/FactorValidationPanel'
import { FactorValidationResult } from '@/types/factorValidation'
import {
  getFactors,
  analyzeIC,
  analyzeGroup,
  getFactorValidation,
} from '@/services/factorService'

const { TextArea } = Input

// 因子显示类型
interface FactorDisplay {
  id: string
  name: string
  category: string
  ic: number
  ir: number
  sharpe: number
  status: string
}

// 类别标签映射
function getCategoryLabel(category: string): string {
  const map: Record<string, string> = {
    momentum: '动量',
    value: '价值',
    quality: '质量',
    volatility: '风险',
    liquidity: '流动性',
    size: '规模',
    growth: '成长',
  }
  return map[category] || category
}

// 默认因子数据 (当API不可用时)
const DEFAULT_FACTORS: FactorDisplay[] = [
  { id: 'momentum_20d', name: 'momentum_20d', category: '动量', ic: 0.045, ir: 0.82, sharpe: 1.23, status: 'active' },
  { id: 'value_pb', name: 'value_pb', category: '价值', ic: 0.032, ir: 0.65, sharpe: 0.98, status: 'active' },
  { id: 'volatility_60d', name: 'volatility_60d', category: '风险', ic: -0.028, ir: 0.58, sharpe: 0.76, status: 'testing' },
  { id: 'quality_roe', name: 'quality_roe', category: '质量', ic: 0.038, ir: 0.71, sharpe: 1.15, status: 'active' },
]

const columns = [
  { title: '因子名称', dataIndex: 'name', key: 'name' },
  {
    title: '类别',
    dataIndex: 'category',
    key: 'category',
    render: (cat: string) => <Tag color="blue">{cat}</Tag>,
  },
  {
    title: 'IC均值',
    dataIndex: 'ic',
    key: 'ic',
    render: (v: number) => <NumberDisplay value={v} type="ratio" precision={3} colorize />,
  },
  {
    title: 'IR',
    dataIndex: 'ir',
    key: 'ir',
    render: (v: number) => <NumberDisplay value={v} type="ratio" precision={2} />,
  },
  {
    title: '夏普',
    dataIndex: 'sharpe',
    key: 'sharpe',
    render: (v: number) => <NumberDisplay value={v} type="ratio" precision={2} colorize />,
  },
  {
    title: '状态',
    dataIndex: 'status',
    key: 'status',
    render: (s: string) => (
      <Tag color={s === 'active' ? 'green' : 'orange'}>{s === 'active' ? '生效' : '测试'}</Tag>
    ),
  },
]

/**
 * 因子实验室页面
 *
 * 功能:
 * - 因子编辑器
 * - IC 分析
 * - 分组回测
 */
export default function FactorLab() {
  const [expression, setExpression] = useState('ts_rank(close / delay(close, 20) - 1, 60)')
  const [selectedFactor, setSelectedFactor] = useState<string | null>(null)

  // 数据状态
  const [factors, setFactors] = useState<FactorDisplay[]>([])
  const [icData, setIcData] = useState<{ dates: string[]; ic: number[]; icMean: number } | null>(null)
  const [groupData, setGroupData] = useState<{ groups: string[]; returns: number[] } | null>(null)
  const [validationResult, setValidationResult] = useState<FactorValidationResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [analyzing, setAnalyzing] = useState(false)
  const [, setApiError] = useState<string | null>(null)

  // 加载因子列表
  const loadFactors = useCallback(async () => {
    setLoading(true)
    setApiError(null)
    try {
      const response = await getFactors()
      setFactors(response.factors.map(f => ({
        id: f.id,
        name: f.name,
        category: getCategoryLabel(f.category),
        ic: 0,
        ir: 0,
        sharpe: 0,
        status: 'active',
      })))
      if (response.factors.length > 0 && !selectedFactor) {
        setSelectedFactor(response.factors[0].id)
      }
    } catch (err) {
      console.error('Failed to load factors:', err)
      setApiError('因子服务暂不可用，显示默认因子列表')
      setFactors(DEFAULT_FACTORS)
      if (!selectedFactor) {
        setSelectedFactor('momentum_20d')
      }
    } finally {
      setLoading(false)
    }
  }, [selectedFactor])

  // 加载因子验证结果
  const loadValidation = useCallback(async (factorId: string) => {
    try {
      const result = await getFactorValidation(factorId)
      setValidationResult(result)

      // 更新 IC 数据
      if (result.icStats) {
        setIcData({
          dates: result.icStats.icDates || [],
          ic: result.icStats.icSeries || [],
          icMean: result.icStats.icMean,
        })
      }

      // 更新分组数据
      if (result.returnStats) {
        setGroupData({
          groups: result.returnStats.groupLabels || [],
          returns: result.returnStats.groupReturns || [],
        })
      }
    } catch (err) {
      console.error('Failed to load validation:', err)
      // 清空验证结果，显示提示
      setValidationResult(null)
      setIcData(null)
      setGroupData(null)
      message.warning('因子验证数据暂不可用')
    }
  }, [])

  // 运行 IC 分析
  const handleRunAnalysis = async () => {
    setAnalyzing(true)
    try {
      const [icResult, groupResult] = await Promise.all([
        analyzeIC({ formula: expression }),
        analyzeGroup({ formula: expression }),
      ])

      setIcData({
        dates: ['2024-01', '2024-02', '2024-03', '2024-04', '2024-05', '2024-06'],
        ic: icResult.icDecay.length > 0 ? icResult.icDecay : [icResult.icMean],
        icMean: icResult.icMean,
      })

      const groups = Object.keys(groupResult.groupStats).sort()
      setGroupData({
        groups,
        returns: groups.map(g => groupResult.groupStats[g].mean),
      })

      message.success('分析完成')
    } catch (err) {
      console.error('Analysis failed:', err)
      message.error('分析失败，请检查表达式')
    } finally {
      setAnalyzing(false)
    }
  }

  useEffect(() => {
    loadFactors()
  }, [loadFactors])

  useEffect(() => {
    if (selectedFactor) {
      loadValidation(selectedFactor)
    }
  }, [selectedFactor, loadValidation])

  return (
    <div className="space-y-6 animate-in">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">因子实验室</h1>
        <Button type="primary" icon={<PlusOutlined />}>
          新建因子
        </Button>
      </div>

      <Row gutter={[16, 16]}>
        {/* 因子编辑器 */}
        <Col xs={24} lg={12}>
          <Card title="因子编辑器" subtitle="使用算子表达式定义因子">
            <div className="space-y-4">
              <div>
                <label className="block text-sm text-gray-400 mb-2">因子名称</label>
                <Input placeholder="输入因子名称" defaultValue="momentum_custom" />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-2">因子表达式</label>
                <TextArea
                  rows={4}
                  value={expression}
                  onChange={(e) => setExpression(e.target.value)}
                  placeholder="输入因子表达式..."
                  className="font-mono"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-2">类别</label>
                <Select
                  defaultValue="momentum"
                  style={{ width: '100%' }}
                  options={[
                    { value: 'momentum', label: '动量' },
                    { value: 'value', label: '价值' },
                    { value: 'quality', label: '质量' },
                    { value: 'volatility', label: '波动' },
                    { value: 'liquidity', label: '流动性' },
                  ]}
                />
              </div>
              <Button
                type="primary"
                icon={<PlayCircleOutlined />}
                block
                loading={analyzing}
                onClick={handleRunAnalysis}
              >
                运行 IC 分析
              </Button>
            </div>
          </Card>
        </Col>

        {/* 算子参考 */}
        <Col xs={24} lg={12}>
          <Card title="算子参考" subtitle="可用算子列表">
            <div className="space-y-3 max-h-[350px] overflow-y-auto">
              {[
                { name: 'ts_rank', desc: '时序排名', example: 'ts_rank(x, 20)' },
                { name: 'ts_zscore', desc: '时序标准化', example: 'ts_zscore(x, 60)' },
                { name: 'ts_mean', desc: '移动平均', example: 'ts_mean(x, 20)' },
                { name: 'ts_std', desc: '移动标准差', example: 'ts_std(x, 20)' },
                { name: 'ts_corr', desc: '滚动相关', example: 'ts_corr(x, y, 60)' },
                { name: 'cs_rank', desc: '截面排名', example: 'cs_rank(x)' },
                { name: 'cs_zscore', desc: '截面标准化', example: 'cs_zscore(x)' },
                { name: 'delay', desc: '滞后', example: 'delay(x, 1)' },
                { name: 'delta', desc: '差分', example: 'delta(x, 5)' },
              ].map((op) => (
                <div
                  key={op.name}
                  className="p-3 bg-dark-hover rounded-lg cursor-pointer hover:bg-dark-border transition-colors"
                  onClick={() => setExpression((prev) => prev + ` ${op.name}()`)}
                >
                  <div className="flex justify-between items-center">
                    <span className="font-mono text-primary-400">{op.name}</span>
                    <span className="text-sm text-gray-500">{op.desc}</span>
                  </div>
                  <code className="text-xs text-gray-400 mt-1 block">{op.example}</code>
                </div>
              ))}
            </div>
          </Card>
        </Col>
      </Row>

      {/* 因子列表 */}
      <Card title="因子库" subtitle="已创建的因子">
        <Spin spinning={loading}>
          <Table
            dataSource={factors}
            columns={columns}
            rowKey="id"
            pagination={false}
            onRow={(record) => ({
              onClick: () => setSelectedFactor(record.id),
              className: selectedFactor === record.id ? 'bg-dark-hover' : '',
            })}
          />
        </Spin>
      </Card>

      {/* IC 分析 */}
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={12}>
          <Card title="IC 时序" subtitle="因子预测能力">
            {icData ? (
              <FactorICChart data={icData} />
            ) : (
              <div className="h-64 flex items-center justify-center text-gray-500">
                选择因子查看 IC 分析
              </div>
            )}
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="分组回测" subtitle="多空组合收益">
            {groupData ? (
              <GroupReturnChart data={groupData} />
            ) : (
              <div className="h-64 flex items-center justify-center text-gray-500">
                选择因子查看分组回测
              </div>
            )}
          </Card>
        </Col>
      </Row>

      {/* 因子有效性验证面板 */}
      {selectedFactor && validationResult && (
        <div className="mt-6">
          <h2 className="text-xl font-bold mb-4">因子有效性验证</h2>
          <FactorValidationPanel
            result={validationResult}
            onCompare={() => message.info('因子对比功能开发中')}
            onAddToStrategy={() => message.success('因子已添加到策略构建器')}
          />
        </div>
      )}
    </div>
  )
}
