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
import { useState, useCallback } from 'react'
import { Button, message, Row, Col, Modal } from 'antd'
import {
  SaveOutlined, PlayCircleOutlined, LeftOutlined, RightOutlined,
  CheckCircleOutlined
} from '@ant-design/icons'
import { Card } from '@/components/ui'
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
  UniverseConfig, AlphaConfig, SignalConfig, RiskConfig,
  PortfolioConfig, ExecutionConfig, MonitorConfig
} from '@/types/strategy'

export default function StrategyBuilder() {
  // 模式状态
  const [mode, setMode] = useState<BuilderMode>('wizard')

  // 当前步骤
  const [currentStep, setCurrentStep] = useState(0)

  // 策略配置
  const [config, setConfig] = useState<Partial<StrategyConfig>>(
    createDefaultStrategyConfig('我的第一个策略')
  )

  // 是否有未保存的更改
  const [isDirty, setIsDirty] = useState(false)

  // AI助手面板展开状态
  const [aiPanelExpanded, setAiPanelExpanded] = useState(true)

  // 步骤元数据（包含状态）
  const [steps, setSteps] = useState<StepMeta[]>(
    STRATEGY_STEPS.map((step, index) => ({
      ...step,
      status: index === 0 ? 'current' : 'pending',
    }))
  )

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

  // 保存策略
  const handleSave = useCallback(async () => {
    try {
      // 这里应该调用后端API保存策略
      console.log('Saving strategy:', config)
      message.success('策略已保存')
      setIsDirty(false)
    } catch (error) {
      message.error('保存失败')
    }
  }, [config])

  // 运行回测
  const handleRunBacktest = useCallback(() => {
    if (isDirty) {
      Modal.confirm({
        title: '有未保存的更改',
        content: '是否先保存再运行回测？',
        okText: '保存并运行',
        cancelText: '直接运行',
        onOk: async () => {
          await handleSave()
          message.info('回测功能即将上线')
        },
        onCancel: () => {
          message.info('回测功能即将上线')
        }
      })
    } else {
      message.info('回测功能即将上线')
    }
  }, [isDirty, handleSave])

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

  return (
    <div className="h-full flex flex-col">
      {/* 头部 */}
      <div className="flex justify-between items-center p-4 border-b border-dark-border">
        <div>
          <h1 className="text-xl font-bold">策略构建器</h1>
          <span className="text-gray-500 text-sm">
            {config.name || '未命名策略'}
            {isDirty && <span className="text-yellow-400 ml-2">*未保存</span>}
          </span>
        </div>
        <div className="flex items-center gap-4">
          <ModeToggle mode={mode} onChange={setMode} />
          <Button
            icon={<SaveOutlined />}
            onClick={handleSave}
            disabled={!isDirty}
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
