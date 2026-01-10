/**
 * 交易成本配置面板组件
 * PRD 4.4 交易成本配置
 */
import { useState } from 'react'
import {
  InputNumber,
  Slider,
  Button,
  Radio,
  Tooltip,
  Alert,
  Switch,
  message,
} from 'antd'
import {
  DollarOutlined,
  SettingOutlined,
  InfoCircleOutlined,
  ReloadOutlined,
  SaveOutlined,
} from '@ant-design/icons'
import {
  TradingCostConfig,
  CostMode,
  SlippageConfig,
  MarketImpactConfig,
  COST_MODE_CONFIG,
  COST_MINIMUMS,
  formatCostPercent,
} from '../../types/tradingCost'

interface CostConfigPanelProps {
  config: TradingCostConfig
  onSave: (config: Partial<TradingCostConfig>) => Promise<void>
  onReset: () => Promise<void>
  loading?: boolean
}

export default function CostConfigPanel({
  config,
  onSave,
  onReset,
  loading = false,
}: CostConfigPanelProps) {
  const [mode, setMode] = useState<CostMode>(config.mode)
  const [commission, setCommission] = useState(config.commission_per_share)
  const [simpleSlippage, setSimpleSlippage] = useState(config.simple_slippage)
  const [slippage, setSlippage] = useState<SlippageConfig>(
    config.slippage || { large_cap: 0.0005, mid_cap: 0.001, small_cap: 0.0025 }
  )
  const [marketImpact, setMarketImpact] = useState<MarketImpactConfig>(
    config.market_impact || { impact_coefficient: 0.1, enabled: true }
  )
  const [costBuffer, setCostBuffer] = useState(config.cost_buffer)
  const [saving, setSaving] = useState(false)

  const handleSave = async () => {
    setSaving(true)
    try {
      await onSave({
        mode,
        commission_per_share: commission,
        simple_slippage: simpleSlippage,
        slippage: mode === 'professional' ? slippage : undefined,
        market_impact: mode === 'professional' ? marketImpact : undefined,
        cost_buffer: costBuffer,
      })
      message.success('配置保存成功')
    } catch (error) {
      message.error('保存失败')
    } finally {
      setSaving(false)
    }
  }

  const handleReset = async () => {
    await onReset()
    setMode('simple')
    setCommission(0.005)
    setSimpleSlippage(0.001)
    setSlippage({ large_cap: 0.0005, mid_cap: 0.001, small_cap: 0.0025 })
    setMarketImpact({ impact_coefficient: 0.1, enabled: true })
    setCostBuffer(0.2)
    message.success('已恢复默认配置')
  }

  return (
    <div className="bg-dark-card rounded-lg overflow-hidden">
      {/* 头部 */}
      <div className="px-6 py-4 border-b border-gray-700 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <DollarOutlined className="text-xl text-green-400" />
          <div>
            <h3 className="text-lg font-semibold text-white">交易成本设置</h3>
            <p className="text-gray-500 text-sm">配置回测和实盘交易的成本参数</p>
          </div>
        </div>
        <Button
          icon={<ReloadOutlined />}
          onClick={handleReset}
          disabled={loading}
        >
          恢复默认
        </Button>
      </div>

      {/* 成本模式 */}
      <div className="px-6 py-4 border-b border-gray-700">
        <div className="flex items-center gap-2 mb-3">
          <SettingOutlined className="text-gray-400" />
          <span className="text-white font-medium">成本模式</span>
        </div>
        <Radio.Group
          value={mode}
          onChange={(e) => setMode(e.target.value)}
          className="w-full"
        >
          <div className="grid grid-cols-2 gap-4">
            {(['simple', 'professional'] as CostMode[]).map((m) => (
              <Radio
                key={m}
                value={m}
                className={`flex-1 p-4 rounded-lg border transition-colors ${
                  mode === m
                    ? 'border-blue-500 bg-blue-500/10'
                    : 'border-gray-700 hover:border-gray-600'
                }`}
              >
                <div>
                  <div className="text-white font-medium">
                    {COST_MODE_CONFIG[m].label}
                    {m === 'simple' && (
                      <span className="text-xs text-green-400 ml-2">(推荐)</span>
                    )}
                  </div>
                  <div className="text-gray-500 text-sm">
                    {COST_MODE_CONFIG[m].description}
                  </div>
                </div>
              </Radio>
            ))}
          </div>
        </Radio.Group>
      </div>

      {/* 佣金设置 */}
      <div className="px-6 py-4 border-b border-gray-700">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <span className="text-white font-medium">佣金</span>
            <Tooltip title={`最低限制: $${COST_MINIMUMS.commission_per_share}/股`}>
              <InfoCircleOutlined className="text-gray-500" />
            </Tooltip>
          </div>
          <span className="text-gray-400 text-sm">$/股</span>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-gray-400">$</span>
          <InputNumber
            value={commission}
            onChange={(v) => setCommission(v || 0.005)}
            min={COST_MINIMUMS.commission_per_share}
            max={0.05}
            step={0.001}
            precision={3}
            className="flex-1"
            style={{ width: '100%' }}
          />
          <span className="text-gray-400">/股</span>
        </div>
        {commission < COST_MINIMUMS.commission_per_share && (
          <Alert
            message={`佣金不能低于 $${COST_MINIMUMS.commission_per_share}/股`}
            type="warning"
            showIcon
            className="mt-2"
          />
        )}
      </div>

      {/* 滑点设置 */}
      <div className="px-6 py-4 border-b border-gray-700">
        <div className="flex items-center gap-2 mb-3">
          <span className="text-white font-medium">滑点</span>
          <Tooltip title="滑点是实际成交价与预期价格的偏差">
            <InfoCircleOutlined className="text-gray-500" />
          </Tooltip>
        </div>

        {mode === 'simple' ? (
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-gray-400">固定滑点</span>
              <span className="text-white font-mono">
                {formatCostPercent(simpleSlippage)}
              </span>
            </div>
            <Slider
              value={simpleSlippage * 100}
              onChange={(v) => setSimpleSlippage(v / 100)}
              min={0.05}
              max={0.5}
              step={0.01}
              marks={{
                0.05: '0.05%',
                0.1: '0.10%',
                0.25: '0.25%',
                0.5: '0.50%',
              }}
            />
          </div>
        ) : (
          <div className="space-y-4">
            {/* 大盘股 */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-gray-400">大盘股 (&gt;$10B)</span>
                <span className="text-white font-mono">
                  {formatCostPercent(slippage.large_cap)}
                </span>
              </div>
              <Slider
                value={slippage.large_cap * 100}
                onChange={(v) =>
                  setSlippage({ ...slippage, large_cap: v / 100 })
                }
                min={0.02}
                max={0.2}
                step={0.01}
              />
            </div>

            {/* 中盘股 */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-gray-400">中盘股 ($2B-$10B)</span>
                <span className="text-white font-mono">
                  {formatCostPercent(slippage.mid_cap)}
                </span>
              </div>
              <Slider
                value={slippage.mid_cap * 100}
                onChange={(v) => setSlippage({ ...slippage, mid_cap: v / 100 })}
                min={0.05}
                max={0.3}
                step={0.01}
              />
            </div>

            {/* 小盘股 */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-gray-400">小盘股 (&lt;$2B)</span>
                <span className="text-white font-mono">
                  {formatCostPercent(slippage.small_cap)}
                </span>
              </div>
              <Slider
                value={slippage.small_cap * 100}
                onChange={(v) =>
                  setSlippage({ ...slippage, small_cap: v / 100 })
                }
                min={0.15}
                max={0.5}
                step={0.01}
              />
            </div>
          </div>
        )}
      </div>

      {/* 市场冲击 (专业模式) */}
      {mode === 'professional' && (
        <div className="px-6 py-4 border-b border-gray-700">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <span className="text-white font-medium">市场冲击模型</span>
              <Tooltip title="Almgren-Chriss模型，计算大额交易对价格的影响">
                <InfoCircleOutlined className="text-gray-500" />
              </Tooltip>
            </div>
            <Switch
              checked={marketImpact.enabled}
              onChange={(checked) =>
                setMarketImpact({ ...marketImpact, enabled: checked })
              }
            />
          </div>

          {marketImpact.enabled && (
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-gray-400">冲击系数 (η)</span>
                <span className="text-white font-mono">
                  {marketImpact.impact_coefficient.toFixed(2)}
                </span>
              </div>
              <Slider
                value={marketImpact.impact_coefficient}
                onChange={(v) =>
                  setMarketImpact({ ...marketImpact, impact_coefficient: v })
                }
                min={0.05}
                max={0.5}
                step={0.01}
                marks={{
                  0.05: '0.05',
                  0.1: '0.10',
                  0.25: '0.25',
                  0.5: '0.50',
                }}
              />
              <p className="text-gray-500 text-xs mt-2">
                公式: 市场冲击 = η × σ × √(Q/ADV) × 交易额
              </p>
            </div>
          )}
        </div>
      )}

      {/* 成本缓冲 */}
      <div className="px-6 py-4 border-b border-gray-700">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <span className="text-white font-medium">成本缓冲</span>
            <Tooltip title="为应对实际成本波动预留的安全边际">
              <InfoCircleOutlined className="text-gray-500" />
            </Tooltip>
          </div>
          <span className="text-white font-mono">
            {formatCostPercent(costBuffer, 0)}
          </span>
        </div>
        <Slider
          value={costBuffer * 100}
          onChange={(v) => setCostBuffer(v / 100)}
          min={0}
          max={50}
          step={5}
          marks={{
            0: '0%',
            10: '10%',
            20: '20%',
            30: '30%',
            50: '50%',
          }}
        />
      </div>

      {/* 提示信息 */}
      <div className="px-6 py-4 border-b border-gray-700">
        <Alert
          message="实际成本可能高于估算，建议预留适当缓冲"
          type="info"
          showIcon
        />
      </div>

      {/* 保存按钮 */}
      <div className="px-6 py-4 flex justify-end">
        <Button
          type="primary"
          icon={<SaveOutlined />}
          onClick={handleSave}
          loading={saving || loading}
          size="large"
        >
          保存设置
        </Button>
      </div>
    </div>
  )
}
