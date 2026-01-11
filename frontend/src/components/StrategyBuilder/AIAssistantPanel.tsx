/**
 * AI助手侧边栏组件
 * 全程陪伴策略构建过程
 */
import { useState, useRef, useEffect } from 'react'
import { Input, Button, Spin, Tag, Collapse, Select, Tooltip, message } from 'antd'
import {
  RobotOutlined, SendOutlined, BulbOutlined,
  QuestionCircleOutlined, SettingOutlined, SwapOutlined
} from '@ant-design/icons'
import { AIMessage, STRATEGY_STEPS, StrategyConfig } from '@/types/strategy'

const { TextArea } = Input

// AI模型信息
interface AIModelInfo {
  id: string
  name: string
  provider: string  // "anthropic" | "openai" | "deepseek"
  description: string
  max_tokens: number
  is_recommended: boolean
  tier: string  // "economy" | "standard" | "premium"
}

// 平台显示名称
const PROVIDER_NAMES: Record<string, string> = {
  anthropic: 'Anthropic',
  openai: 'OpenAI',
  deepseek: 'DeepSeek',
}

// 平台颜色
const PROVIDER_COLORS: Record<string, string> = {
  anthropic: '#D97706',  // 橙色
  openai: '#10B981',     // 绿色
  deepseek: '#3B82F6',   // 蓝色
}

interface AIAssistantPanelProps {
  currentStep: number
  config: Partial<StrategyConfig>
  onApplyConfig?: (updates: Partial<StrategyConfig>) => void
}

// 预置的提示问题
const STEP_SUGGESTIONS: Record<number, string[]> = {
  0: ['什么样的投资池适合我？', '为什么要排除小市值股票？', '流动性筛选有什么用？'],
  1: ['推荐适合新手的因子组合', '动量和价值因子的区别？', 'IC和IR指标怎么看？'],
  2: ['如何设置合理的止损？', '入场规则有哪些常见模式？', '排名入场和阈值入场的区别？'],
  3: ['机构级风控是什么标准？', '为什么不能关闭熔断？', '最大回撤设多少合适？'],
  4: ['等权重和因子加权哪个好？', '调仓频率怎么选择？', '最大换手率设多少？'],
  5: ['市价单和TWAP的区别？', '滑点模型怎么选？', '交易成本对收益影响多大？'],
  6: ['应该设置哪些告警？', '因子衰减告警是什么？', '报告频率选日报还是周报？'],
}

// 本地模拟AI响应 (作为后端API不可用时的降级方案)
const simulateAIResponse = async (question: string, step: number): Promise<string> => {
  await new Promise(resolve => setTimeout(resolve, 500))

  const stepInfo = STRATEGY_STEPS[step]
  const responses: Record<string, string> = {
    '什么样的投资池适合我？': `根据您的投资目标，我建议：

**新手投资者**: S&P 500
- 成分股流动性好，交易成本低
- 数据质量高，因子计算准确
- 约500只股票，足够分散

**追求成长**: NASDAQ 100
- 科技股集中，成长性强
- 波动较大，适合能承受风险的投资者

**小盘股策略**: Russell 2000
- 小盘股alpha机会更多
- 流动性相对差，需要注意交易成本`,

    '推荐适合新手的因子组合': `对于新手，我推荐一个简单但有效的组合：

**动量 + 价值 + 质量** (三因子组合)

1. **20日动量** - 捕捉趋势
2. **PB估值** - 寻找便宜股票
3. **ROE质量** - 筛选盈利能力强的公司

这个组合：
- 逻辑清晰，容易理解
- 因子之间低相关，互补性好
- 历史表现稳定，IR约0.8`,

    '如何设置合理的止损？': `止损设置的几个原则：

1. **必须设置** - 没有止损的策略是赌博
2. **不能太紧** - 给股票正常波动留空间
3. **不能太松** - 否则等于没设

**建议值：**
- 保守型：10-12%
- 平衡型：15% (推荐)
- 激进型：20%

**注意：** 止损不是坏事，它是保护资金的手段。真正的高手敢于止损。`,

    '机构级风控是什么标准？': `机构投资者的风控标准非常严格：

**仓位限制：**
- 单股：2-5%（绝不超过5%）
- 行业：15-25%
- 现金：5-10%

**回撤控制：**
- 日亏损预警：3%
- 周回撤红线：7%
- 月回撤熔断：15%

**核心理念：**
"先学会不亏钱，才能赚钱"
机构可以承受收益低，但绝不能承受大回撤。`,
  }

  // 查找匹配的回复
  for (const [key, value] of Object.entries(responses)) {
    if (question.includes(key.slice(0, 10))) {
      return value
    }
  }

  // 默认回复
  return `关于"${question}"：

这是一个很好的问题！在**${stepInfo.title}**这一步，需要注意：

${stepInfo.educationTip}

如果您需要更具体的建议，可以告诉我您的：
- 投资目标（学习/稳健/积极）
- 风险承受能力
- 预期投资周期

我会给出更有针对性的建议。`
}

// API配置
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || ''

// 连接状态类型
type ConnectionStatus = 'checking' | 'connected' | 'offline'

export default function AIAssistantPanel({
  currentStep,
  config,
  onApplyConfig: _onApplyConfig
}: AIAssistantPanelProps) {
  const [messages, setMessages] = useState<AIMessage[]>([])
  const [inputValue, setInputValue] = useState('')
  const [loading, setLoading] = useState(false)
  const [apiError, setApiError] = useState(false)
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('checking')
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // 模型相关状态
  const [availableModels, setAvailableModels] = useState<AIModelInfo[]>([])
  const [currentModelId, setCurrentModelId] = useState<string>('')
  const [showModelSelector, setShowModelSelector] = useState(false)
  const [switchingModel, setSwitchingModel] = useState(false)

  const stepInfo = STRATEGY_STEPS[currentStep]
  const suggestions = STEP_SUGGESTIONS[currentStep] || []

  // 获取可用模型列表
  useEffect(() => {
    const fetchModels = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/v1/ai-assistant/models`)
        if (response.ok) {
          const data = await response.json()
          setAvailableModels(data.models)
          setCurrentModelId(data.current_model_id)
        }
      } catch (error) {
        console.error('Failed to fetch models:', error)
      }
    }
    fetchModels()
  }, [])

  // 切换模型
  const handleSwitchModel = async (modelId: string) => {
    setSwitchingModel(true)
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/ai-assistant/models/switch`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model_id: modelId })
      })
      if (response.ok) {
        const data = await response.json()
        setCurrentModelId(modelId)
        message.success(data.message)
      } else {
        message.error('模型切换失败')
      }
    } catch (error) {
      console.error('Failed to switch model:', error)
      message.error('模型切换失败')
    } finally {
      setSwitchingModel(false)
      setShowModelSelector(false)
    }
  }

  // 获取当前模型信息
  const currentModel = availableModels.find(m => m.id === currentModelId)

  // 检查AI助手连接状态
  useEffect(() => {
    const checkConnection = async () => {
      setConnectionStatus('checking')
      try {
        const response = await fetch(`${API_BASE_URL}/api/v1/ai-assistant/status`, {
          method: 'GET',
          headers: { 'Content-Type': 'application/json' },
          signal: AbortSignal.timeout(5000),
        })
        if (response.ok) {
          const data = await response.json()
          setConnectionStatus(data.has_api_key ? 'connected' : 'offline')
          setApiError(false)
        } else {
          setConnectionStatus('offline')
          setApiError(true)
        }
      } catch {
        // 开发模式下模拟连接成功
        if (import.meta.env.DEV) {
          setConnectionStatus('connected')
          setApiError(false)
        } else {
          setConnectionStatus('offline')
          setApiError(true)
        }
      }
    }

    checkConnection()
    // 每30秒检查一次
    const interval = setInterval(checkConnection, 30000)
    return () => clearInterval(interval)
  }, [])

  // 调用后端AI助手API
  const callAIAssistant = async (question: string, step: number): Promise<string> => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/ai-assistant/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question,
          current_step: step,
          context: config,
          history: messages.slice(-10).map(m => ({
            role: m.role,
            content: m.content
          }))
        })
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        console.error('AI Assistant API error:', response.status, errorData)
        throw new Error(`API error: ${response.status}`)
      }

      const data = await response.json()
      setApiError(false)
      return data.answer
    } catch (error) {
      console.error('AI Assistant request failed:', error)
      setApiError(true)
      // 降级到本地模拟响应
      return simulateAIResponse(question, step)
    }
  }

  // 自动滚动到底部
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // 切换步骤时显示提示
  useEffect(() => {
    const welcomeMessage: AIMessage = {
      id: `welcome_${currentStep}`,
      role: 'assistant',
      content: `您现在进入了**${stepInfo.title}**步骤。

${stepInfo.educationTip}

有任何问题都可以问我！`,
      timestamp: new Date().toISOString(),
      relatedStep: currentStep,
    }
    setMessages([welcomeMessage])
    setApiError(false)
  }, [currentStep])

  const sendMessage = async (question: string) => {
    if (!question.trim() || loading) return

    const userMessage: AIMessage = {
      id: `user_${Date.now()}`,
      role: 'user',
      content: question,
      timestamp: new Date().toISOString(),
      relatedStep: currentStep,
    }

    setMessages(prev => [...prev, userMessage])
    setInputValue('')
    setLoading(true)

    try {
      // 使用真实API，失败时自动降级到本地模拟
      const response = await callAIAssistant(question, currentStep)

      const assistantMessage: AIMessage = {
        id: `assistant_${Date.now()}`,
        role: 'assistant',
        content: response,
        timestamp: new Date().toISOString(),
        relatedStep: currentStep,
      }

      setMessages(prev => [...prev, assistantMessage])
    } catch (error) {
      console.error('AI response error:', error)
      // 即使callAIAssistant内部已经处理了降级，这里也做一个兜底
      const fallbackMessage: AIMessage = {
        id: `assistant_${Date.now()}`,
        role: 'assistant',
        content: '抱歉，我暂时无法回答这个问题。请稍后再试，或者换个方式提问。',
        timestamp: new Date().toISOString(),
        relatedStep: currentStep,
      }
      setMessages(prev => [...prev, fallbackMessage])
    } finally {
      setLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage(inputValue)
    }
  }

  return (
    <div className="h-full flex flex-col bg-dark-card border-l border-dark-border">
      {/* 头部 */}
      <div className="p-4 border-b border-dark-border">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <RobotOutlined className="text-xl text-primary-500" />
            <span className="font-medium">策略助手</span>
          </div>
          {/* 设置按钮 */}
          <Tooltip title="模型设置">
            <Button
              type="text"
              size="small"
              icon={<SettingOutlined />}
              onClick={() => setShowModelSelector(!showModelSelector)}
            />
          </Tooltip>
        </div>

        {/* 模型选择器 */}
        {showModelSelector && (
          <div className="mt-3 p-3 bg-dark-hover rounded-lg">
            <div className="text-xs text-gray-400 mb-2">选择AI模型</div>
            <Select
              value={currentModelId}
              onChange={handleSwitchModel}
              loading={switchingModel}
              className="w-full"
              size="small"
              optionLabelProp="label"
            >
              {/* 按平台分组 */}
              {['anthropic', 'openai', 'deepseek'].map(provider => {
                const providerModels = availableModels.filter(m => m.provider === provider)
                if (providerModels.length === 0) return null
                return (
                  <Select.OptGroup
                    key={provider}
                    label={
                      <span style={{ color: PROVIDER_COLORS[provider] }}>
                        {PROVIDER_NAMES[provider]}
                      </span>
                    }
                  >
                    {providerModels.map(model => (
                      <Select.Option
                        key={model.id}
                        value={model.id}
                        label={`${model.name} (${PROVIDER_NAMES[model.provider]})`}
                      >
                        <div className="flex items-center justify-between">
                          <span>{model.name}</span>
                          <div className="flex gap-1">
                            {model.is_recommended && (
                              <Tag color="success" className="text-xs">推荐</Tag>
                            )}
                            <Tag
                              color={
                                model.tier === 'premium' ? 'gold' :
                                model.tier === 'standard' ? 'blue' : 'default'
                              }
                              className="text-xs"
                            >
                              {model.tier === 'premium' ? '高级' :
                               model.tier === 'standard' ? '标准' : '经济'}
                            </Tag>
                          </div>
                        </div>
                        <div className="text-xs text-gray-500">{model.description}</div>
                      </Select.Option>
                    ))}
                  </Select.OptGroup>
                )
              })}
            </Select>
            <div className="text-xs text-gray-500 mt-2">
              提示: 需要在 .env 中配置对应平台的 API Key
            </div>
          </div>
        )}

        {/* 当前模型和连接状态 */}
        <div className="flex items-center justify-between mt-2">
          <div className="flex items-center gap-2">
            <Tag color="blue">{stepInfo.title}</Tag>
            {currentModel && (
              <Tooltip title={`${PROVIDER_NAMES[currentModel.provider]}: ${currentModel.description}`}>
                <Tag
                  style={{
                    borderColor: PROVIDER_COLORS[currentModel.provider],
                    color: PROVIDER_COLORS[currentModel.provider]
                  }}
                  className="cursor-pointer"
                  onClick={() => setShowModelSelector(true)}
                >
                  <SwapOutlined className="mr-1" />
                  {currentModel.name}
                </Tag>
              </Tooltip>
            )}
          </div>
          {/* 连接状态指示器 */}
          <div className="flex items-center gap-1">
            {connectionStatus === 'checking' && (
              <Tag color="processing" className="text-xs">
                <Spin size="small" className="mr-1" />
                检测中
              </Tag>
            )}
            {connectionStatus === 'connected' && !apiError && (
              <Tag color="success" className="text-xs">
                <span className="inline-block w-2 h-2 rounded-full bg-green-500 mr-1 animate-pulse" />
                已连接
              </Tag>
            )}
            {(connectionStatus === 'offline' || apiError) && (
              <Tag color="warning" className="text-xs">
                <span className="inline-block w-2 h-2 rounded-full bg-yellow-500 mr-1" />
                离线模式
              </Tag>
            )}
          </div>
        </div>
      </div>

      {/* 消息区域 */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map(message => (
          <div
            key={message.id}
            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[90%] p-3 rounded-lg text-sm ${
                message.role === 'user'
                  ? 'bg-primary-500/20 text-primary-100'
                  : 'bg-dark-hover'
              }`}
            >
              <div className="whitespace-pre-wrap">{message.content}</div>
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="p-3 bg-dark-hover rounded-lg">
              <Spin size="small" />
              <span className="ml-2 text-gray-500">思考中...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* 快捷问题 */}
      <div className="p-3 border-t border-dark-border">
        <Collapse
          ghost
          items={[{
            key: '1',
            label: (
              <span className="text-xs text-gray-500">
                <BulbOutlined className="mr-1" />
                常见问题
              </span>
            ),
            children: (
              <div className="space-y-2">
                {suggestions.map((q, i) => (
                  <Button
                    key={i}
                    type="text"
                    size="small"
                    className="w-full text-left text-xs"
                    onClick={() => sendMessage(q)}
                    disabled={loading}
                  >
                    <QuestionCircleOutlined className="mr-1" />
                    {q}
                  </Button>
                ))}
              </div>
            )
          }]}
        />
      </div>

      {/* 输入区域 */}
      <div className="p-3 border-t border-dark-border">
        <div className="flex gap-2">
          <TextArea
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="问我任何问题..."
            autoSize={{ minRows: 1, maxRows: 3 }}
            disabled={loading}
          />
          <Button
            type="primary"
            icon={<SendOutlined />}
            onClick={() => sendMessage(inputValue)}
            disabled={!inputValue.trim() || loading}
          />
        </div>
      </div>
    </div>
  )
}
