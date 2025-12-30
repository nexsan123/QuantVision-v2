/**
 * 节点配置面板组件
 *
 * 根据节点类型显示不同的配置表单
 */

import { useState, useEffect } from 'react'
import { Node } from 'reactflow'
import {
  Form,
  Input,
  Select,
  InputNumber,
  Switch,
  Button,
  Space,
  Divider,
  Popconfirm,
} from 'antd'
import {
  CloseOutlined,
  DeleteOutlined,
  SaveOutlined,
} from '@ant-design/icons'
import { WorkflowNodeData } from '@/types/workflow'

interface NodeConfigPanelProps {
  node: Node<WorkflowNodeData>
  onUpdate: (data: WorkflowNodeData) => void
  onDelete: () => void
  onClose: () => void
}

export function NodeConfigPanel({
  node,
  onUpdate,
  onDelete,
  onClose,
}: NodeConfigPanelProps) {
  const [form] = Form.useForm()
  const [nodeData, setNodeData] = useState<WorkflowNodeData>(node.data)

  useEffect(() => {
    setNodeData(node.data)
    form.setFieldsValue({
      label: node.data.label,
      description: node.data.description,
      ...node.data.config,
    })
  }, [node, form])

  const handleSave = () => {
    form.validateFields().then((values) => {
      const { label, description, ...config } = values
      const updatedData = {
        ...nodeData,
        label,
        description,
        config: { ...nodeData.config, ...config },
      } as WorkflowNodeData

      onUpdate(updatedData)
    })
  }

  return (
    <div className="h-full flex flex-col">
      {/* 头部 */}
      <div className="flex items-center justify-between p-4 border-b border-dark-border">
        <h3 className="font-medium text-gray-200">配置节点</h3>
        <Button
          type="text"
          icon={<CloseOutlined />}
          onClick={onClose}
          className="!text-gray-400"
        />
      </div>

      {/* 表单 */}
      <div className="flex-1 overflow-auto p-4">
        <Form
          form={form}
          layout="vertical"
          size="small"
          className="text-gray-200"
        >
          {/* 通用字段 */}
          <Form.Item
            name="label"
            label={<span className="text-gray-400">节点名称</span>}
            rules={[{ required: true, message: '请输入节点名称' }]}
          >
            <Input placeholder="输入名称" />
          </Form.Item>

          <Form.Item
            name="description"
            label={<span className="text-gray-400">描述</span>}
          >
            <Input.TextArea placeholder="可选描述" rows={2} />
          </Form.Item>

          <Divider className="!border-dark-border" />

          {/* 类型特定配置 */}
          {renderTypeConfig(node.data.type, form)}
        </Form>
      </div>

      {/* 底部操作 */}
      <div className="p-4 border-t border-dark-border">
        <Space className="w-full justify-between">
          <Popconfirm
            title="确定删除此节点?"
            onConfirm={onDelete}
            okText="删除"
            cancelText="取消"
          >
            <Button
              danger
              icon={<DeleteOutlined />}
            >
              删除
            </Button>
          </Popconfirm>
          <Button
            type="primary"
            icon={<SaveOutlined />}
            onClick={handleSave}
          >
            保存
          </Button>
        </Space>
      </div>
    </div>
  )
}

// 渲染类型特定配置
function renderTypeConfig(type: string, _form: ReturnType<typeof Form.useForm>[0]) {
  switch (type) {
    case 'universe':
      return <UniverseConfig />
    case 'factor':
      return <FactorConfig />
    case 'filter':
      return <FilterConfig />
    case 'rank':
      return <RankConfig />
    case 'signal':
      return <SignalConfig />
    case 'weight':
      return <WeightConfig />
    case 'output':
      return <OutputConfig />
    default:
      return null
  }
}

// 股票池配置
function UniverseConfig() {
  return (
    <>
      <Form.Item
        name="baseUniverse"
        label={<span className="text-gray-400">基础股票池</span>}
      >
        <Select
          options={[
            { value: 'sp500', label: 'S&P 500' },
            { value: 'nasdaq100', label: 'NASDAQ 100' },
            { value: 'russell1000', label: 'Russell 1000' },
            { value: 'custom', label: '自定义' },
          ]}
        />
      </Form.Item>
      <Form.Item
        name="marketCapMin"
        label={<span className="text-gray-400">最小市值 (亿美元)</span>}
      >
        <InputNumber min={0} className="w-full" />
      </Form.Item>
      <Form.Item
        name="marketCapMax"
        label={<span className="text-gray-400">最大市值 (亿美元)</span>}
      >
        <InputNumber min={0} className="w-full" />
      </Form.Item>
    </>
  )
}

// 因子配置
function FactorConfig() {
  return (
    <>
      <Form.Item
        name="factorName"
        label={<span className="text-gray-400">因子名称</span>}
        rules={[{ required: true, message: '请选择因子' }]}
      >
        <Select
          showSearch
          placeholder="选择因子"
          options={[
            { value: 'momentum_20', label: '20日动量' },
            { value: 'reversal_5', label: '5日反转' },
            { value: 'volatility', label: '波动率' },
            { value: 'rsi_14', label: 'RSI(14)' },
            { value: 'macd', label: 'MACD' },
            { value: 'trend_strength', label: '趋势强度' },
          ]}
        />
      </Form.Item>
      <Form.Item
        name="lookbackPeriod"
        label={<span className="text-gray-400">回望周期</span>}
      >
        <InputNumber min={1} max={252} className="w-full" />
      </Form.Item>
    </>
  )
}

// 筛选配置
function FilterConfig() {
  return (
    <>
      <Form.Item
        name="logic"
        label={<span className="text-gray-400">条件逻辑</span>}
      >
        <Select
          options={[
            { value: 'and', label: '全部满足 (AND)' },
            { value: 'or', label: '任一满足 (OR)' },
          ]}
        />
      </Form.Item>
      <div className="text-xs text-gray-500 mt-2">
        条件编辑器开发中...
      </div>
    </>
  )
}

// 排名配置
function RankConfig() {
  return (
    <>
      <Form.Item
        name="rankBy"
        label={<span className="text-gray-400">排名字段</span>}
      >
        <Select
          placeholder="选择排名依据"
          options={[
            { value: 'factor_value', label: '因子值' },
            { value: 'returns', label: '收益率' },
            { value: 'volatility', label: '波动率' },
          ]}
        />
      </Form.Item>
      <Form.Item
        name="ascending"
        label={<span className="text-gray-400">排序方向</span>}
        valuePropName="checked"
      >
        <Switch
          checkedChildren="升序"
          unCheckedChildren="降序"
        />
      </Form.Item>
      <Form.Item
        name="topN"
        label={<span className="text-gray-400">选取 Top N</span>}
      >
        <InputNumber min={1} max={100} className="w-full" />
      </Form.Item>
    </>
  )
}

// 信号配置
function SignalConfig() {
  return (
    <>
      <Form.Item
        name="signalType"
        label={<span className="text-gray-400">信号类型</span>}
      >
        <Select
          options={[
            { value: 'long', label: '只做多' },
            { value: 'short', label: '只做空' },
            { value: 'longshort', label: '多空' },
          ]}
        />
      </Form.Item>
      <Form.Item
        name="entryCondition"
        label={<span className="text-gray-400">入场条件</span>}
      >
        <Input.TextArea placeholder="例: factor_value > 0.5" rows={2} />
      </Form.Item>
      <Form.Item
        name="holdPeriod"
        label={<span className="text-gray-400">持仓周期 (天)</span>}
      >
        <InputNumber min={1} className="w-full" />
      </Form.Item>
    </>
  )
}

// 权重配置
function WeightConfig() {
  return (
    <>
      <Form.Item
        name="method"
        label={<span className="text-gray-400">权重方法</span>}
      >
        <Select
          options={[
            { value: 'equal', label: '等权' },
            { value: 'marketCap', label: '市值加权' },
            { value: 'inverseVolatility', label: '波动率倒数' },
            { value: 'riskParity', label: '风险平价' },
          ]}
        />
      </Form.Item>
      <Form.Item
        name="maxWeight"
        label={<span className="text-gray-400">单股最大权重</span>}
      >
        <InputNumber
          min={0.01}
          max={1}
          step={0.01}
          className="w-full"
          formatter={(value) => `${(value || 0) * 100}%`}
          parser={(value) => (parseFloat(value?.replace('%', '') || '0') / 100) as 0.01}
        />
      </Form.Item>
    </>
  )
}

// 输出配置
function OutputConfig() {
  return (
    <>
      <Form.Item
        name="outputType"
        label={<span className="text-gray-400">输出类型</span>}
      >
        <Select
          options={[
            { value: 'portfolio', label: '投资组合' },
            { value: 'signal', label: '交易信号' },
            { value: 'backtest', label: '回测结果' },
          ]}
        />
      </Form.Item>
      <Form.Item
        name="rebalanceFrequency"
        label={<span className="text-gray-400">再平衡频率</span>}
      >
        <Select
          options={[
            { value: 'daily', label: '每日' },
            { value: 'weekly', label: '每周' },
            { value: 'monthly', label: '每月' },
          ]}
        />
      </Form.Item>
      <Form.Item
        name="targetPositions"
        label={<span className="text-gray-400">目标持仓数</span>}
      >
        <InputNumber min={1} max={100} className="w-full" />
      </Form.Item>
    </>
  )
}

export default NodeConfigPanel
