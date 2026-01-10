import { useState } from 'react'
import { Row, Col, Input, Select, Button, Table, Tag, message } from 'antd'
import { PlayCircleOutlined, PlusOutlined } from '@ant-design/icons'
import { Card, NumberDisplay } from '@/components/ui'
import { FactorICChart, GroupReturnChart } from '@/components/Chart'
import FactorValidationPanel from '@/components/Factor/FactorValidationPanel'
import { FactorValidationResult } from '@/types/factorValidation'

const { TextArea } = Input

// 模拟因子数据
const mockFactors = [
  { id: 1, name: 'momentum_20d', category: '动量', ic: 0.045, ir: 0.82, sharpe: 1.23, status: 'active' },
  { id: 2, name: 'value_pb', category: '价值', ic: 0.032, ir: 0.65, sharpe: 0.98, status: 'active' },
  { id: 3, name: 'volatility_60d', category: '风险', ic: -0.028, ir: 0.58, sharpe: 0.76, status: 'testing' },
  { id: 4, name: 'quality_roe', category: '质量', ic: 0.038, ir: 0.71, sharpe: 1.15, status: 'active' },
]

const mockICData = {
  dates: ['2024-01', '2024-02', '2024-03', '2024-04', '2024-05', '2024-06'],
  ic: [0.052, 0.038, 0.041, 0.055, 0.029, 0.048],
  icMean: 0.044,
}

const mockGroupData = {
  groups: ['G1', 'G2', 'G3', 'G4', 'G5', 'G6', 'G7', 'G8', 'G9', 'G10'],
  returns: [-0.08, -0.04, -0.02, 0.01, 0.03, 0.05, 0.07, 0.10, 0.14, 0.22],
}

// 模拟因子验证结果
const mockValidationResults: Record<number, FactorValidationResult> = {
  1: {
    factorId: 'momentum_20d',
    factorName: '20日动量因子',
    factorCategory: 'momentum',
    plainDescription: '该因子衡量股票过去20个交易日的价格涨跌幅度。数值越高表示近期涨幅越大，可能代表股票处于上涨趋势中。',
    investmentLogic: '动量效应是金融市场最著名的异象之一：过去表现好的股票在未来一段时间内往往继续表现较好，这可能源于投资者对信息的反应不足。',
    icStats: {
      icMean: 0.045,
      icStd: 0.055,
      icIr: 0.82,
      icPositiveRatio: 0.68,
      icSeries: [0.052, 0.038, 0.041, 0.055, 0.029, 0.048],
      icDates: ['2024-01', '2024-02', '2024-03', '2024-04', '2024-05', '2024-06'],
    },
    returnStats: {
      groupReturns: [-0.08, -0.04, -0.02, 0.01, 0.03, 0.05, 0.07, 0.10, 0.14, 0.22],
      groupLabels: ['G1(空)', 'G2', 'G3', 'G4', 'G5', 'G6', 'G7', 'G8', 'G9', 'G10(多)'],
      longShortSpread: 0.30,
      topGroupSharpe: 1.45,
      bottomGroupSharpe: -0.82,
    },
    isEffective: true,
    effectivenessLevel: 'strong',
    effectivenessScore: 85,
    suggestedCombinations: ['价值因子 (PB)', '质量因子 (ROE)', '低波动因子'],
    usageTips: [
      '该因子在趋势市场中表现最佳，震荡市场时效果减弱',
      '建议与价值因子组合使用，可以降低追高风险',
      '适合中等持仓周期（20-60天）',
      'IC_IR高于0.5，表明因子稳定有效',
    ],
    riskWarnings: [
      '动量因子在市场反转时可能遭受较大回撤',
      '极端牛市末期可能累积过多风险敞口',
      '2008年金融危机期间动量因子曾大幅回撤',
    ],
    validationDate: '2026-01-09',
    dataPeriod: '2015-01 ~ 2025-12',
    sampleSize: 125000,
  },
  2: {
    factorId: 'value_pb',
    factorName: 'PB估值因子',
    factorCategory: 'value',
    plainDescription: '该因子使用市净率(P/B)来衡量股票估值水平。数值越低表示股票越便宜，可能存在价值被低估的机会。',
    investmentLogic: '价值投资的核心理念：以低于内在价值的价格买入资产，长期持有等待价值回归。低PB股票通常代表被市场冷落的公司。',
    icStats: {
      icMean: 0.032,
      icStd: 0.049,
      icIr: 0.65,
      icPositiveRatio: 0.62,
      icSeries: [0.028, 0.035, 0.030, 0.038, 0.025, 0.036],
      icDates: ['2024-01', '2024-02', '2024-03', '2024-04', '2024-05', '2024-06'],
    },
    returnStats: {
      groupReturns: [-0.05, -0.02, 0.00, 0.02, 0.03, 0.04, 0.05, 0.07, 0.09, 0.12],
      groupLabels: ['G1(贵)', 'G2', 'G3', 'G4', 'G5', 'G6', 'G7', 'G8', 'G9', 'G10(便宜)'],
      longShortSpread: 0.17,
      topGroupSharpe: 1.10,
      bottomGroupSharpe: -0.45,
    },
    isEffective: true,
    effectivenessLevel: 'medium',
    effectivenessScore: 68,
    suggestedCombinations: ['动量因子', '盈利能力因子', '股息率因子'],
    usageTips: [
      '价值因子需要较长持仓周期才能发挥效果',
      '与成长因子负相关，可作为组合对冲',
      '适合熊市和价值回归阶段',
    ],
    riskWarnings: [
      '价值陷阱：便宜可能是因为公司基本面恶化',
      '价值因子在科技牛市期间可能长期跑输',
      '需要结合质量因子筛选，避免买入垃圾股',
    ],
    validationDate: '2026-01-09',
    dataPeriod: '2015-01 ~ 2025-12',
    sampleSize: 125000,
  },
  3: {
    factorId: 'volatility_60d',
    factorName: '60日波动率因子',
    factorCategory: 'volatility',
    plainDescription: '该因子衡量股票过去60个交易日的价格波动程度。低波动股票通常风险较小，适合稳健型投资者。',
    investmentLogic: '低波动异象：历史上低波动股票的风险调整后收益往往优于高波动股票，这与传统金融理论相悖。',
    icStats: {
      icMean: -0.028,
      icStd: 0.048,
      icIr: 0.58,
      icPositiveRatio: 0.55,
      icSeries: [-0.032, -0.025, -0.030, -0.022, -0.035, -0.024],
      icDates: ['2024-01', '2024-02', '2024-03', '2024-04', '2024-05', '2024-06'],
    },
    returnStats: {
      groupReturns: [0.08, 0.06, 0.04, 0.03, 0.02, 0.01, -0.01, -0.02, -0.04, -0.06],
      groupLabels: ['G1(低波)', 'G2', 'G3', 'G4', 'G5', 'G6', 'G7', 'G8', 'G9', 'G10(高波)'],
      longShortSpread: 0.14,
      topGroupSharpe: 0.92,
      bottomGroupSharpe: -0.35,
    },
    isEffective: true,
    effectivenessLevel: 'medium',
    effectivenessScore: 62,
    suggestedCombinations: ['质量因子', '价值因子', '股息因子'],
    usageTips: [
      '低波动策略在熊市中表现尤为出色',
      '适合作为防御性配置的一部分',
      'IC为负表示低波动组表现更好',
    ],
    riskWarnings: [
      '牛市期间可能跑输大盘',
      '需要注意行业集中度风险',
      '低波动股票可能缺乏催化剂',
    ],
    validationDate: '2026-01-09',
    dataPeriod: '2015-01 ~ 2025-12',
    sampleSize: 125000,
  },
  4: {
    factorId: 'quality_roe',
    factorName: 'ROE质量因子',
    factorCategory: 'quality',
    plainDescription: '该因子使用净资产收益率(ROE)衡量公司盈利能力。高ROE表示公司能够高效利用股东资本创造利润。',
    investmentLogic: '质量投资关注公司的盈利能力和经营效率。高质量公司通常具有持续竞争优势，能在经济周期中保持稳定表现。',
    icStats: {
      icMean: 0.038,
      icStd: 0.054,
      icIr: 0.71,
      icPositiveRatio: 0.65,
      icSeries: [0.042, 0.033, 0.040, 0.035, 0.038, 0.040],
      icDates: ['2024-01', '2024-02', '2024-03', '2024-04', '2024-05', '2024-06'],
    },
    returnStats: {
      groupReturns: [-0.06, -0.03, -0.01, 0.01, 0.02, 0.04, 0.06, 0.08, 0.11, 0.15],
      groupLabels: ['G1(低质)', 'G2', 'G3', 'G4', 'G5', 'G6', 'G7', 'G8', 'G9', 'G10(高质)'],
      longShortSpread: 0.21,
      topGroupSharpe: 1.28,
      bottomGroupSharpe: -0.55,
    },
    isEffective: true,
    effectivenessLevel: 'strong',
    effectivenessScore: 78,
    suggestedCombinations: ['动量因子', '价值因子', '成长因子'],
    usageTips: [
      '质量因子适合各种市场环境',
      '与其他因子的相关性较低，是优秀的组合成分',
      '建议避免极端高ROE（可能不可持续）',
    ],
    riskWarnings: [
      '高ROE公司估值可能已经较高',
      '过去的高质量不保证未来持续',
      '部分行业ROE天然较高，需注意行业中性化',
    ],
    validationDate: '2026-01-09',
    dataPeriod: '2015-01 ~ 2025-12',
    sampleSize: 125000,
  },
}

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
  const [selectedFactor, setSelectedFactor] = useState<number | null>(1)

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
              <Button type="primary" icon={<PlayCircleOutlined />} block>
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
        <Table
          dataSource={mockFactors}
          columns={columns}
          rowKey="id"
          pagination={false}
          onRow={(record) => ({
            onClick: () => setSelectedFactor(record.id),
            className: selectedFactor === record.id ? 'bg-dark-hover' : '',
          })}
        />
      </Card>

      {/* IC 分析 */}
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={12}>
          <Card title="IC 时序" subtitle="因子预测能力">
            <FactorICChart data={mockICData} />
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="分组回测" subtitle="多空组合收益">
            <GroupReturnChart data={mockGroupData} />
          </Card>
        </Col>
      </Row>

      {/* 因子有效性验证面板 */}
      {selectedFactor && mockValidationResults[selectedFactor] && (
        <div className="mt-6">
          <h2 className="text-xl font-bold mb-4">因子有效性验证</h2>
          <FactorValidationPanel
            result={mockValidationResults[selectedFactor]}
            onCompare={() => message.info('因子对比功能开发中')}
            onAddToStrategy={() => message.success('因子已添加到策略构建器')}
          />
        </div>
      )}
    </div>
  )
}
