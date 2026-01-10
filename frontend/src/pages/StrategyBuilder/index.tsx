/**
 * 策略构建器页面 - Phase 8 重构版
 *
 * 7步向导流程:
 * 1. 投资池 (Universe) - 定义可交易的股票范围
 * 2. 因子层 (Alpha) - 选择和配置选股因子
 * 3. 信号层 (Signal) - 定义买入和卖出规则 [新增]
 * 4. 风险层 (Risk) - 设置风险约束和限制 [新增]
 * 5. 组合层 (Portfolio) - 仓位分配和权重优化
 * 6. 执行层 (Execution) - 配置交易执行方式
 * 7. 监控层 (Monitor) - 设置监控和告警
 *
 * 支持双模式: 向导模式 / 工作流模式
 */
import { useState, useCallback, useEffect } from 'react'
import { Button, message, Modal, Input, Spin } from 'antd'
import {
  SaveOutlined, PlayCircleOutlined, LeftOutlined, RightOutlined,
  CheckCircleOutlined, EditOutlined
} from '@ant-design/icons'
import { useNavigate, useSearchParams } from 'react-router-dom'
import WizardSteps from '@/components/StrategyBuilder/WizardSteps'
import ModeToggle from '@/components/StrategyBuilder/ModeToggle'
import AIAssistantPanel from '@/components/StrategyBuilder/AIAssistantPanel'
import {
  StepUniverse, StepAlpha, StepSignal, StepRisk,
  StepPortfolio, StepExecution, StepMonitor
} from '@/components/StrategyBuilder/steps'
import WorkflowCanvas from '@/components/Workflow/WorkflowCanvas'
import {
  StrategyConfig, StepMeta, BuilderMode, STRATEGY_STEPS,
  createDefaultStrategyConfig,
  Strategy
} from '@/types/strategy'
import { createStrategy, updateStrategy, getStrategy } from '@/services/strategyService'

export default function StrategyBuilder() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const strategyId = searchParams.get('id')

  // 加载状态
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)

  // 当前编辑的策略实体(如果是编辑现有策略)
  const [existingStrategy, setExistingStrategy] = useState<Strategy | null>(null)

  // 策略名称编辑
  const [editingName, setEditingName] = useState(false)
  const [tempName, setTempName] = useState('')

  // 模式状态
  const [mode, setMode] = useState<BuilderMode>('wizard')

  // 当前步骤
  const [currentStep, setCurrentStep] = useState(0)

  // 策略配置
  const [config, setConfig] = useState<Partial<StrategyConfig>>(
    createDefaultStrategyConfig('我的新策略')
  )

  // 是否有未保存的更改
  const [isDirty, setIsDirty] = useState(false)

  // AI助手面板展开状态
  const [aiPanelExpanded, _setAiPanelExpanded] = useState(true)

  // 步骤元数据（包含状态）
  const [steps, setSteps] = useState<StepMeta[]>(
    STRATEGY_STEPS.map((step, index) => ({
      ...step,
      status: index === 0 ? 'current' : 'pending',
    }))
  )

  // 加载现有策略
  useEffect(() => {
    if (strategyId) {
      setLoading(true)
      getStrategy(strategyId)
        .then(strategy => {
          if (strategy) {
            setExistingStrategy(strategy)
            setConfig(strategy.config)
          } else {
            message.error('策略不存在')
            navigate('/my-strategies')
          }
        })
        .catch(() => {
          message.error('加载策略失败')
        })
        .finally(() => {
          setLoading(false)
        })
    }
  }, [strategyId, navigate])

  // 更新配置的通用方法
  const updateConfig = useCallback(<K extends keyof StrategyConfig>(
    key: K,
    value: StrategyConfig[K]
  ) => {
    setConfig(prev => ({ ...prev, [key]: value }))
    setIsDirty(true)
  }, [])

  // 切换步骤
  const goToStep = useCallback((stepIndex: number) => {
    if (stepIndex < 0 || stepIndex >= steps.length) return

    setSteps(prev => prev.map((step, index) => ({
      ...step,
      status: index < stepIndex ? 'completed' :
              index === stepIndex ? 'current' : 'pending'
    })))
    setCurrentStep(stepIndex)
  }, [steps.length])

  // 下一步
  const nextStep = useCallback(() => {
    if (currentStep < steps.length - 1) {
      goToStep(currentStep + 1)
    }
  }, [currentStep, steps.length, goToStep])

  // 上一步
  const prevStep = useCallback(() => {
    if (currentStep > 0) {
      goToStep(currentStep - 1)
    }
  }, [currentStep, goToStep])

  // 更新策略名称
  const handleNameSave = useCallback(() => {
    if (tempName.trim()) {
      setConfig(prev => ({ ...prev, name: tempName.trim() }))
      setIsDirty(true)
    }
    setEditingName(false)
  }, [tempName])

  // 保存策略
  const handleSave = useCallback(async () => {
    if (!config.name?.trim()) {
      message.error('请输入策略名称')
      return
    }

    setSaving(true)
    try {
      if (existingStrategy) {
        // 更新现有策略
        await updateStrategy(existingStrategy.id, {
          name: config.name,
          description: config.description,
          config: config as StrategyConfig,
        })
        message.success('策略已更新')
      } else {
        // 创建新策略
        const newStrategy = await createStrategy({
          name: config.name!,
          description: config.description || '',
          config: config as StrategyConfig,
        })
        setExistingStrategy(newStrategy)
        // 更新URL以便刷新后能继续编辑
        navigate(`/strategy?id=${newStrategy.id}`, { replace: true })
        message.success('策略已保存')
      }
      setIsDirty(false)
    } catch {
      message.error('保存失败')
    } finally {
      setSaving(false)
    }
  }, [config, existingStrategy, navigate])

  // 运行回测
  const handleRunBacktest = useCallback(async () => {
    const goToBacktest = () => {
      if (existingStrategy) {
        navigate(`/backtest?strategyId=${existingStrategy.id}`)
      } else {
        message.warning('请先保存策略')
      }
    }

    if (isDirty) {
      Modal.confirm({
        title: '有未保存的更改',
        content: '是否先保存再运行回测？',
        okText: '保存并运行',
        cancelText: '取消',
        onOk: async () => {
          await handleSave()
          // 等待一下确保保存完成后再跳转
          setTimeout(() => {
            if (existingStrategy) {
              navigate(`/backtest?strategyId=${existingStrategy.id}`)
            }
          }, 100)
        },
      })
    } else {
      goToBacktest()
    }
  }, [isDirty, handleSave, existingStrategy, navigate])

  // 渲染当前步骤内容
  const renderStepContent = () => {
    switch (currentStep) {
      case 0:
        return (
          <StepUniverse
            value={config.universe!}
            onChange={(v) => updateConfig('universe', v)}
          />
        )
      case 1:
        return (
          <StepAlpha
            value={config.alpha!}
            onChange={(v) => updateConfig('alpha', v)}
          />
        )
      case 2:
        return (
          <StepSignal
            value={config.signal!}
            onChange={(v) => updateConfig('signal', v)}
          />
        )
      case 3:
        return (
          <StepRisk
            value={config.risk!}
            onChange={(v) => updateConfig('risk', v)}
          />
        )
      case 4:
        return (
          <StepPortfolio
            value={config.portfolio!}
            onChange={(v) => updateConfig('portfolio', v)}
          />
        )
      case 5:
        return (
          <StepExecution
            value={config.execution!}
            onChange={(v) => updateConfig('execution', v)}
          />
        )
      case 6:
        return (
          <StepMonitor
            value={config.monitor!}
            onChange={(v) => updateConfig('monitor', v)}
          />
        )
      default:
        return null
    }
  }

  // 显示加载状态
  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <Spin size="large" tip="加载策略中..." />
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col">
      {/* 头部 */}
      <div className="flex justify-between items-center p-4 border-b border-dark-border">
        <div>
          <h1 className="text-xl font-bold">
            {existingStrategy ? '编辑策略' : '创建新策略'}
          </h1>
          <div className="flex items-center gap-2 mt-1">
            {editingName ? (
              <Input
                value={tempName}
                onChange={e => setTempName(e.target.value)}
                onBlur={handleNameSave}
                onPressEnter={handleNameSave}
                autoFocus
                size="small"
                className="w-48"
                placeholder="输入策略名称"
              />
            ) : (
              <span
                className="text-gray-400 text-sm cursor-pointer hover:text-white flex items-center gap-1"
                onClick={() => {
                  setTempName(config.name || '')
                  setEditingName(true)
                }}
              >
                {config.name || '点击输入策略名称'}
                <EditOutlined className="text-xs" />
              </span>
            )}
            {isDirty && <span className="text-yellow-400 text-xs">*未保存</span>}
          </div>
        </div>
        <div className="flex items-center gap-4">
          <ModeToggle mode={mode} onChange={setMode} />
          <Button
            icon={<SaveOutlined />}
            onClick={handleSave}
            loading={saving}
            disabled={!isDirty && !!existingStrategy}
          >
            保存
          </Button>
          <Button
            type="primary"
            icon={<PlayCircleOutlined />}
            onClick={handleRunBacktest}
          >
            运行回测
          </Button>
        </div>
      </div>

      {/* 主体内容 */}
      <div className="flex-1 flex overflow-hidden">
        {/* 左侧主内容区 */}
        <div className={`flex-1 flex flex-col overflow-hidden ${aiPanelExpanded ? '' : 'w-full'}`}>
          {mode === 'wizard' ? (
            <>
              {/* 步骤导航 */}
              <div className="p-4">
                <WizardSteps
                  steps={steps}
                  currentStep={currentStep}
                  onStepClick={goToStep}
                />
              </div>

              {/* 步骤内容 */}
              <div className="flex-1 overflow-y-auto p-4">
                {renderStepContent()}
              </div>

              {/* 底部导航 */}
              <div className="p-4 border-t border-dark-border flex justify-between">
                <Button
                  icon={<LeftOutlined />}
                  onClick={prevStep}
                  disabled={currentStep === 0}
                >
                  上一步
                </Button>
                <div className="text-gray-500">
                  {currentStep + 1} / {steps.length}
                </div>
                {currentStep === steps.length - 1 ? (
                  <Button
                    type="primary"
                    icon={<CheckCircleOutlined />}
                    onClick={handleSave}
                  >
                    完成配置
                  </Button>
                ) : (
                  <Button
                    type="primary"
                    onClick={nextStep}
                  >
                    下一步
                    <RightOutlined />
                  </Button>
                )}
              </div>
            </>
          ) : (
            /* 工作流模式 */
            <div className="flex-1 p-4">
              <WorkflowCanvas />
            </div>
          )}
        </div>

        {/* 右侧AI助手面板 */}
        {aiPanelExpanded && mode === 'wizard' && (
          <div className="w-80 flex-shrink-0">
            <AIAssistantPanel
              currentStep={currentStep}
              config={config}
              onApplyConfig={(updates) => {
                setConfig(prev => ({ ...prev, ...updates }))
                setIsDirty(true)
              }}
            />
          </div>
        )}
      </div>
    </div>
  )
}
