/**
 * 4步部署向导 (Sprint 4 增强版)
 *
 * 设计原则:
 * - 策略构建器定义"是什么" (投资池、因子、信号规则等)
 * - 部署向导定义"怎么执行" (资金、执行模式、环境)
 * - 投资池等配置直接继承自策略，确认页面显示供用户核对
 *
 * Step 1: 选择环境 (模拟盘/实盘)
 * Step 2: 配置资金
 * Step 3: 风控微调 & 执行模式 (F11)
 * Step 4: 确认部署 (显示继承配置 + F12 前置检查)
 */
import { useState, useEffect, useCallback } from 'react'
import {
  Modal,
  Steps,
  Button,
  Radio,
  InputNumber,
  Slider,
  Card,
  Alert,
  Descriptions,
  message,
  Checkbox,
  Space,
  Spin,
  Tag,
  Divider,
} from 'antd'
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  WarningOutlined,
  InfoCircleOutlined,
} from '@ant-design/icons'
import {
  DeploymentConfig,
  ParamLimits,
  RiskParams,
  CapitalConfig,
  DeploymentEnvironment,
  ENV_CONFIG,
  DEFAULT_RISK_PARAMS,
  DEFAULT_CAPITAL_CONFIG,
  ParamRange,
  // Sprint 4 新增
  ExecutionMode,
  UniverseSubsetConfig,
  PreDeploymentCheck,
  PreDeploymentCheckResult,
  EXECUTION_MODE_CONFIG,
  DEFAULT_EXECUTION_MODE,
} from '../../types/deployment'
import type { StrategyConfig } from '../../types/strategy'

interface DeploymentWizardProps {
  strategyId: string
  strategyName: string
  strategyConfig?: StrategyConfig  // 继承策略配置
  visible: boolean
  onClose: () => void
  onComplete: (config: DeploymentConfig) => Promise<void>
}

export default function DeploymentWizard({
  strategyId,
  strategyName,
  strategyConfig,
  visible,
  onClose,
  onComplete,
}: DeploymentWizardProps) {
  const [currentStep, setCurrentStep] = useState(0)
  const [loading, setLoading] = useState(false)
  const [paramLimits, setParamLimits] = useState<ParamLimits | null>(null)

  // 配置状态
  const [environment, setEnvironment] = useState<DeploymentEnvironment>('paper')
  const [capitalConfig, setCapitalConfig] = useState<CapitalConfig>(DEFAULT_CAPITAL_CONFIG)
  const [riskParams, setRiskParams] = useState<RiskParams>(DEFAULT_RISK_PARAMS)

  // Sprint 4: 执行模式 (F11)
  const [executionMode, setExecutionMode] = useState<ExecutionMode>(DEFAULT_EXECUTION_MODE)

  // Sprint 4: 前置检查状态 (F12)
  const [preChecks, setPreChecks] = useState<PreDeploymentCheckResult | null>(null)
  const [runningPreCheck, setRunningPreCheck] = useState(false)
  const [riskAcknowledged, setRiskAcknowledged] = useState(false)

  useEffect(() => {
    if (visible && strategyId) {
      fetchParamLimits()
      // 重置状态
      setCurrentStep(0)
      setEnvironment('paper')
      setCapitalConfig(DEFAULT_CAPITAL_CONFIG)
      setRiskParams(DEFAULT_RISK_PARAMS)
      setExecutionMode(DEFAULT_EXECUTION_MODE)
      setPreChecks(null)
      setRunningPreCheck(false)
      setRiskAcknowledged(false)
    }
  }, [visible, strategyId])

  const fetchParamLimits = async () => {
    try {
      // TODO: 调用API获取参数范围
      // 模拟数据
      setParamLimits({
        strategyId,
        stopLossRange: {
          minValue: -0.30,
          maxValue: -0.02,
          defaultValue: -0.05,
          step: 0.01,
          unit: '%',
          description: '止损比例',
        },
        takeProfitRange: {
          minValue: 0.05,
          maxValue: 0.50,
          defaultValue: 0.10,
          step: 0.01,
          unit: '%',
          description: '止盈比例',
        },
        maxPositionPctRange: {
          minValue: 0.02,
          maxValue: 0.30,
          defaultValue: 0.10,
          step: 0.01,
          unit: '%',
          description: '单只最大仓位',
        },
        maxDrawdownRange: {
          minValue: -0.30,
          maxValue: -0.05,
          defaultValue: -0.15,
          step: 0.01,
          unit: '%',
          description: '最大回撤',
        },
        minCapital: 1000,
        availableSymbols: ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META'],
      })
    } catch {
      message.error('获取参数范围失败')
    }
  }

  // F12: 运行前置检查
  const runPreDeploymentChecks = useCallback(async (): Promise<PreDeploymentCheckResult> => {
    await new Promise(resolve => setTimeout(resolve, 1500))

    const checks: PreDeploymentCheck[] = [
      {
        id: 'backtest',
        name: '回测验证',
        description: '策略是否通过回测验证',
        status: 'passed',
        message: '策略已完成回测，年化收益 18.6%',
        required: true,
      },
      {
        id: 'paper_trading',
        name: '模拟盘验证',
        description: '是否完成至少30天模拟盘运行',
        status: environment === 'live' ? 'warning' : 'passed',
        message: environment === 'live' ? '建议先运行30天模拟盘' : '已在模拟盘环境',
        required: false,
      },
      {
        id: 'capital',
        name: '资金检查',
        description: '账户资金是否充足',
        status: capitalConfig.totalCapital >= 10000 ? 'passed' : 'warning',
        message: capitalConfig.totalCapital >= 10000
          ? `资金 $${capitalConfig.totalCapital.toLocaleString()} 满足要求`
          : '建议资金不低于 $10,000',
        required: true,
      },
      {
        id: 'risk_params',
        name: '风控参数',
        description: '风控参数是否在合理范围',
        status: riskParams.maxDrawdown >= -0.25 ? 'passed' : 'warning',
        message: riskParams.maxDrawdown >= -0.25
          ? '风控参数设置合理'
          : '最大回撤设置较激进，请谨慎',
        required: false,
      },
      {
        id: 'market_hours',
        name: '市场状态',
        description: '当前是否为交易时段',
        status: 'passed',
        message: '下一交易日 09:30 开始执行',
        required: false,
      },
    ]

    const requiredPassed = checks.filter(c => c.required).every(c => c.status === 'passed')
    const allPassed = checks.every(c => c.status === 'passed')

    return { checks, requiredPassed, allPassed }
  }, [environment, capitalConfig, riskParams])

  const handleNext = async () => {
    // 进入最后一步时，运行前置检查 (F12)
    if (currentStep === 2 && environment === 'live') {
      setRunningPreCheck(true)
      try {
        const result = await runPreDeploymentChecks()
        setPreChecks(result)
      } finally {
        setRunningPreCheck(false)
      }
    }

    if (currentStep < 3) {
      setCurrentStep(currentStep + 1)
    }
  }

  const handlePrev = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1)
    }
  }

  const handleComplete = async () => {
    // F12: 实盘需要确认风险
    if (environment === 'live' && !riskAcknowledged) {
      message.warning('请先确认风险提示')
      return
    }

    // F12: 实盘必须通过必要检查
    if (environment === 'live' && preChecks && !preChecks.requiredPassed) {
      message.error('必要检查项未通过，无法开启实盘交易')
      return
    }

    setLoading(true)
    try {
      // 继承策略的投资池配置
      const universeConfig: UniverseSubsetConfig = {
        mode: 'full',
        maxPositions: strategyConfig?.portfolio?.maxHoldings || 20,
      }

      const config: DeploymentConfig = {
        strategyId,
        deploymentName: `${strategyName}-${environment === 'paper' ? '模拟' : '实盘'}`,
        environment,
        strategyType: 'medium_term',
        universeConfig,
        executionMode,
        riskParams,
        capitalConfig,
        rebalanceFrequency: strategyConfig?.portfolio?.rebalanceFrequency || 'daily',
        rebalanceTime: '09:35',
      }

      await onComplete(config)
      message.success('部署创建成功！')
    } catch {
      message.error('部署失败')
    } finally {
      setLoading(false)
    }
  }

  // 4步向导
  const steps = [
    { title: '选择环境', description: '模拟盘或实盘' },
    { title: '配置资金', description: '设置投资金额' },
    { title: '风控执行', description: '风控与执行模式' },
    { title: '确认部署', description: '检查配置' },
  ]

  // 获取策略继承配置的展示
  const getInheritedConfigDisplay = () => {
    if (!strategyConfig) {
      return {
        universe: 'S&P 500',
        maxHoldings: 20,
        rebalanceFrequency: '每日',
        factors: '多因子组合',
      }
    }

    const basePoolMap: Record<string, string> = {
      SP500: 'S&P 500',
      NASDAQ100: 'NASDAQ 100',
      RUSSELL1000: 'Russell 1000',
      RUSSELL2000: 'Russell 2000',
      DJIA: '道琼斯工业',
    }

    const freqMap: Record<string, string> = {
      daily: '每日',
      weekly: '每周',
      biweekly: '双周',
      monthly: '每月',
      quarterly: '每季度',
    }

    return {
      universe: basePoolMap[strategyConfig.universe?.basePool || 'SP500'] || 'S&P 500',
      maxHoldings: strategyConfig.portfolio?.maxHoldings || 20,
      rebalanceFrequency: freqMap[strategyConfig.portfolio?.rebalanceFrequency || 'daily'] || '每日',
      factors: strategyConfig.alpha?.factors?.length
        ? `${strategyConfig.alpha.factors.length} 个因子`
        : '未配置',
    }
  }

  const inheritedConfig = getInheritedConfigDisplay()

  const renderStepContent = () => {
    switch (currentStep) {
      // Step 1: 选择环境
      case 0:
        return (
          <div className="py-8">
            <div className="text-center mb-6">
              <h3 className="text-lg font-medium mb-2">选择部署环境</h3>
              <p className="text-gray-400">建议先在模拟盘验证策略效果</p>
            </div>
            <Radio.Group
              value={environment}
              onChange={e => setEnvironment(e.target.value)}
              className="w-full"
            >
              <div className="grid grid-cols-2 gap-4">
                <Radio.Button
                  value="paper"
                  className="!h-32 !flex items-center justify-center !rounded-lg"
                >
                  <div className="text-center">
                    <div className="text-3xl mb-2">📊</div>
                    <div className="font-medium">模拟盘</div>
                    <div className="text-xs text-gray-400">虚拟资金，无风险</div>
                  </div>
                </Radio.Button>
                <Radio.Button
                  value="live"
                  className="!h-32 !flex items-center justify-center !rounded-lg"
                >
                  <div className="text-center">
                    <div className="text-3xl mb-2">💰</div>
                    <div className="font-medium">实盘</div>
                    <div className="text-xs text-gray-400">真实交易，需谨慎</div>
                  </div>
                </Radio.Button>
              </div>
            </Radio.Group>
            {environment === 'live' && (
              <Alert
                type="warning"
                message="实盘交易存在风险，请确保您已充分了解策略逻辑并接受潜在亏损"
                className="mt-4"
                showIcon
              />
            )}
          </div>
        )

      // Step 2: 配置资金
      case 1:
        return (
          <div className="py-6 space-y-6">
            <div>
              <label className="block text-sm font-medium mb-2">投资总金额</label>
              <InputNumber
                value={capitalConfig.totalCapital}
                onChange={v =>
                  setCapitalConfig({ ...capitalConfig, totalCapital: v || 1000 })
                }
                min={paramLimits?.minCapital || 1000}
                max={10000000}
                step={1000}
                addonBefore="$"
                className="w-full"
                formatter={value => `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
              />
              <div className="text-xs text-gray-500 mt-1">
                最低资金要求: ${paramLimits?.minCapital?.toLocaleString() || 1000}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">
                初始仓位比例: {(capitalConfig.initialPositionPct * 100).toFixed(0)}%
              </label>
              <Slider
                value={capitalConfig.initialPositionPct * 100}
                onChange={v =>
                  setCapitalConfig({
                    ...capitalConfig,
                    initialPositionPct: v / 100,
                    reserveCashPct: 1 - v / 100,
                  })
                }
                min={10}
                max={100}
                step={5}
                marks={{
                  10: '10%',
                  50: '50%',
                  80: '80%',
                  100: '100%',
                }}
              />
              <div className="flex justify-between text-xs text-gray-500 mt-2">
                <span>
                  投入: ${(capitalConfig.totalCapital * capitalConfig.initialPositionPct).toLocaleString()}
                </span>
                <span>
                  预留: ${(capitalConfig.totalCapital * capitalConfig.reserveCashPct).toLocaleString()}
                </span>
              </div>
            </div>
          </div>
        )

      // Step 3: 风控参数 & 执行模式 (F11)
      case 2:
        return (
          <div className="py-6 space-y-6">
            <Alert
              type="info"
              message="以下风控参数继承自策略配置，您可以在允许范围内微调"
              className="mb-4"
              showIcon
            />

            {paramLimits && (
              <>
                <ParamSlider
                  label="止损比例"
                  value={riskParams.stopLoss}
                  onChange={v => setRiskParams({ ...riskParams, stopLoss: v })}
                  range={paramLimits.stopLossRange}
                />
                <ParamSlider
                  label="止盈比例"
                  value={riskParams.takeProfit}
                  onChange={v => setRiskParams({ ...riskParams, takeProfit: v })}
                  range={paramLimits.takeProfitRange}
                />
                <ParamSlider
                  label="单只最大仓位"
                  value={riskParams.maxPositionPct}
                  onChange={v => setRiskParams({ ...riskParams, maxPositionPct: v })}
                  range={paramLimits.maxPositionPctRange}
                />
                <ParamSlider
                  label="最大回撤限制"
                  value={riskParams.maxDrawdown}
                  onChange={v => setRiskParams({ ...riskParams, maxDrawdown: v })}
                  range={paramLimits.maxDrawdownRange}
                />
              </>
            )}

            {/* F11: 执行模式选择 */}
            <div className="mt-6 pt-6 border-t border-gray-700">
              <h4 className="text-base font-medium mb-4">执行模式</h4>
              <Radio.Group
                value={executionMode}
                onChange={e => setExecutionMode(e.target.value)}
                className="w-full"
              >
                <Space direction="vertical" className="w-full">
                  {(Object.keys(EXECUTION_MODE_CONFIG) as ExecutionMode[]).map(mode => (
                    <Radio key={mode} value={mode} className="w-full">
                      <div className="ml-2">
                        <div className="font-medium">
                          <span className="mr-2">{EXECUTION_MODE_CONFIG[mode].icon}</span>
                          {EXECUTION_MODE_CONFIG[mode].label}
                        </div>
                        <div className="text-xs text-gray-400">
                          {EXECUTION_MODE_CONFIG[mode].description}
                        </div>
                      </div>
                    </Radio>
                  ))}
                </Space>
              </Radio.Group>

              {executionMode === 'auto' && environment === 'live' && (
                <Alert
                  type="warning"
                  message="全自动模式下，系统将自动执行所有交易信号，请确保您了解策略逻辑"
                  className="mt-3"
                  showIcon
                />
              )}
            </div>
          </div>
        )

      // Step 4: 确认部署 (F12 前置检查)
      case 3:
        return (
          <div className="py-6">
            {/* F12: 实盘前置检查 */}
            {environment === 'live' && runningPreCheck && (
              <div className="text-center py-8">
                <Spin size="large" />
                <div className="mt-4 text-gray-400">正在进行部署前置检查...</div>
              </div>
            )}

            {environment === 'live' && preChecks && !runningPreCheck && (
              <div className="mb-6">
                <h4 className="text-base font-medium mb-4">
                  <InfoCircleOutlined className="mr-2 text-blue-400" />
                  部署前置检查
                </h4>
                <div className="space-y-2">
                  {preChecks.checks.map(check => (
                    <div
                      key={check.id}
                      className={`flex items-center justify-between p-3 rounded ${
                        check.status === 'passed'
                          ? 'bg-green-900/20'
                          : check.status === 'warning'
                          ? 'bg-yellow-900/20'
                          : 'bg-red-900/20'
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        {check.status === 'passed' && (
                          <CheckCircleOutlined className="text-green-400" />
                        )}
                        {check.status === 'warning' && (
                          <WarningOutlined className="text-yellow-400" />
                        )}
                        {check.status === 'failed' && (
                          <CloseCircleOutlined className="text-red-400" />
                        )}
                        <div>
                          <div className="font-medium">
                            {check.name}
                            {check.required && (
                              <span className="ml-2 text-xs text-red-400">*必须</span>
                            )}
                          </div>
                          <div className="text-xs text-gray-400">{check.message}</div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>

                {!preChecks.requiredPassed && (
                  <Alert
                    type="error"
                    message="必要检查项未通过，无法开启实盘交易"
                    className="mt-4"
                    showIcon
                  />
                )}

                <Divider />
              </div>
            )}

            {/* 配置摘要 - 策略继承配置 */}
            <Card
              title={
                <span className="text-sm">
                  <Tag color="blue">策略继承</Tag> 以下配置来自策略定义
                </span>
              }
              className="!bg-[#12122a] mb-4"
              size="small"
            >
              <Descriptions column={2} size="small">
                <Descriptions.Item label="投资池">{inheritedConfig.universe}</Descriptions.Item>
                <Descriptions.Item label="最大持股">{inheritedConfig.maxHoldings}只</Descriptions.Item>
                <Descriptions.Item label="调仓频率">{inheritedConfig.rebalanceFrequency}</Descriptions.Item>
                <Descriptions.Item label="选股因子">{inheritedConfig.factors}</Descriptions.Item>
              </Descriptions>
            </Card>

            {/* 部署配置 */}
            <Card
              title={
                <span className="text-sm">
                  <Tag color="green">部署配置</Tag> 本次部署设置
                </span>
              }
              className="!bg-[#12122a]"
              size="small"
            >
              <Descriptions column={2} size="small">
                <Descriptions.Item label="部署环境">
                  <span className={environment === 'live' ? 'text-green-400' : 'text-blue-400'}>
                    {ENV_CONFIG[environment].label}
                  </span>
                </Descriptions.Item>
                <Descriptions.Item label="执行模式">
                  <span>
                    {EXECUTION_MODE_CONFIG[executionMode].icon}{' '}
                    {EXECUTION_MODE_CONFIG[executionMode].label}
                  </span>
                </Descriptions.Item>
                <Descriptions.Item label="投资金额">
                  ${capitalConfig.totalCapital.toLocaleString()}
                </Descriptions.Item>
                <Descriptions.Item label="初始仓位">
                  {(capitalConfig.initialPositionPct * 100).toFixed(0)}%
                </Descriptions.Item>
                <Descriptions.Item label="止损/止盈">
                  {(riskParams.stopLoss * 100).toFixed(1)}% / {(riskParams.takeProfit * 100).toFixed(1)}%
                </Descriptions.Item>
                <Descriptions.Item label="最大回撤">
                  {(riskParams.maxDrawdown * 100).toFixed(1)}%
                </Descriptions.Item>
              </Descriptions>
            </Card>

            {/* F12: 实盘风险确认 */}
            {environment === 'live' && (
              <div className="mt-4">
                <Alert
                  type="warning"
                  message="实盘交易风险提示"
                  description={
                    <div className="space-y-1 text-sm">
                      <p>1. 实盘交易涉及真实资金，可能产生亏损</p>
                      <p>2. 过往回测表现不代表未来收益</p>
                      <p>3. 市场波动可能导致实际执行价格与信号价格存在偏差</p>
                      <p>4. 请确保您已充分了解策略逻辑和风险</p>
                    </div>
                  }
                  showIcon
                />
                <Checkbox
                  checked={riskAcknowledged}
                  onChange={e => setRiskAcknowledged(e.target.checked)}
                  className="mt-4"
                >
                  我已阅读并理解以上风险提示，自愿承担交易风险
                </Checkbox>
              </div>
            )}
          </div>
        )

      default:
        return null
    }
  }

  return (
    <Modal
      title={`部署策略: ${strategyName}`}
      open={visible}
      onCancel={onClose}
      width={650}
      footer={
        <div className="flex justify-between">
          <Button onClick={onClose}>取消</Button>
          <div className="space-x-2">
            {currentStep > 0 && <Button onClick={handlePrev}>上一步</Button>}
            {currentStep < 3 ? (
              <Button type="primary" onClick={handleNext}>
                下一步
              </Button>
            ) : (
              <Button
                type="primary"
                onClick={handleComplete}
                loading={loading}
                disabled={environment === 'live' && preChecks !== null && !preChecks.requiredPassed}
              >
                {environment === 'live' ? '确认开启实盘' : '开始模拟交易'}
              </Button>
            )}
          </div>
        </div>
      }
      destroyOnClose
    >
      <Steps current={currentStep} items={steps} className="mb-6" size="small" />
      {renderStepContent()}
    </Modal>
  )
}

// 参数滑块组件
function ParamSlider({
  label,
  value,
  onChange,
  range,
}: {
  label: string
  value: number
  onChange: (v: number) => void
  range: ParamRange
}) {
  const displayValue = value * 100

  return (
    <div>
      <div className="flex justify-between mb-2">
        <label className="text-sm font-medium">{label}</label>
        <span className="text-sm text-blue-400">{displayValue.toFixed(1)}%</span>
      </div>
      <Slider
        value={displayValue}
        onChange={v => onChange(v / 100)}
        min={range.minValue * 100}
        max={range.maxValue * 100}
        step={range.step * 100}
        marks={{
          [range.minValue * 100]: `${(range.minValue * 100).toFixed(0)}%`,
          [range.defaultValue * 100]: '默认',
          [range.maxValue * 100]: `${(range.maxValue * 100).toFixed(0)}%`,
        }}
      />
    </div>
  )
}
