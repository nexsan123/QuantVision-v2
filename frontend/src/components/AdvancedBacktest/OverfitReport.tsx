/**
 * 过拟合检测报告组件
 * Phase 9: 回测引擎升级
 */
import { useState } from 'react'
import {
  Row, Col, Progress, Tag, Collapse, Tooltip, Statistic, List, Alert
} from 'antd'
import {
  WarningOutlined, CheckCircleOutlined, InfoCircleOutlined,
  LineChartOutlined, ExperimentOutlined, SafetyOutlined
} from '@ant-design/icons'
import { Card } from '@/components/ui'
import {
  OverfitDetectionResult, ParameterSensitivity,
  OVERFIT_RISK_COLORS
} from '@/types/backtest'

interface OverfitReportProps {
  result: OverfitDetectionResult
}

export default function OverfitReport({ result }: OverfitReportProps) {
  const { overallAssessment } = result

  // 风险等级颜色
  const getRiskColor = (level: string) => OVERFIT_RISK_COLORS[level] || '#1890ff'

  // 风险等级标签
  const getRiskLabel = (level: string) => {
    const labels: Record<string, string> = {
      low: '低风险',
      moderate: '中等风险',
      high: '高风险',
      critical: '严重风险'
    }
    return labels[level] || level
  }

  // 评估结论颜色
  const getVerdictColor = (verdict: string) => {
    const colors: Record<string, string> = {
      robust: 'green',
      stable: 'green',
      moderate: 'orange',
      sensitive: 'red',
      likely_overfit: 'red',
      acceptable: 'green',
      suspicious: 'orange'
    }
    return colors[verdict] || 'default'
  }

  return (
    <div className="space-y-6">
      {/* 综合评估卡片 */}
      <Card className="bg-dark-hover">
        <Row gutter={24} align="middle">
          <Col span={8}>
            <div className="text-center">
              <Progress
                type="dashboard"
                percent={overallAssessment.overfitProbability}
                strokeColor={getRiskColor(overallAssessment.riskLevel)}
                format={(pct) => (
                  <div>
                    <div className="text-2xl font-bold">{pct}%</div>
                    <div className="text-xs text-gray-500">过拟合概率</div>
                  </div>
                )}
                size={150}
              />
            </div>
          </Col>
          <Col span={16}>
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <Tag
                  color={getRiskColor(overallAssessment.riskLevel)}
                  className="text-lg px-4 py-1"
                >
                  {getRiskLabel(overallAssessment.riskLevel)}
                </Tag>
                <Tag color="blue">置信度: {overallAssessment.confidence}</Tag>
              </div>
              <p className="text-gray-400">{overallAssessment.explanation}</p>
              {overallAssessment.recommendations.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium mb-2">建议:</h4>
                  <ul className="list-disc list-inside text-sm text-gray-500 space-y-1">
                    {overallAssessment.recommendations.map((rec, i) => (
                      <li key={i}>{rec}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </Col>
        </Row>
      </Card>

      <Row gutter={24}>
        {/* 参数敏感性分析 */}
        <Col span={12}>
          <Card title={<><LineChartOutlined /> 参数敏感性分析</>}>
            {result.parameterSensitivity.length === 0 ? (
              <div className="text-center text-gray-500 py-8">
                未进行参数敏感性分析
              </div>
            ) : (
              <div className="space-y-4">
                {result.parameterSensitivity.map((param, index) => (
                  <div key={index} className="border border-dark-border rounded p-3">
                    <div className="flex justify-between items-center mb-2">
                      <span className="font-medium">{param.parameterLabel}</span>
                      <Tag color={getVerdictColor(param.verdict)}>
                        {param.verdict === 'stable' ? '稳定' :
                         param.verdict === 'moderate' ? '一般' : '敏感'}
                      </Tag>
                    </div>
                    <Progress
                      percent={Math.round(param.sensitivityScore * 100)}
                      strokeColor={param.sensitivityScore > 0.6 ? '#ff4d4f' :
                                   param.sensitivityScore > 0.3 ? '#faad14' : '#52c41a'}
                      format={(pct) => `敏感度: ${pct}%`}
                    />
                    <div className="text-xs text-gray-500 mt-2">
                      当前值: {param.currentValue.toFixed(2)} |
                      最优范围: {param.optimalRange[0].toFixed(1)} - {param.optimalRange[1].toFixed(1)}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </Col>

        {/* 样本内外对比 */}
        <Col span={12}>
          <Card title={<><ExperimentOutlined /> 样本内外对比</>}>
            {!result.inOutSampleComparison ? (
              <div className="text-center text-gray-500 py-8">
                未进行样本内外对比
              </div>
            ) : (
              <div className="space-y-4">
                <Row gutter={16}>
                  <Col span={12}>
                    <Statistic
                      title="样本内夏普"
                      value={result.inOutSampleComparison.inSampleSharpe}
                      precision={2}
                      valueStyle={{ color: '#1890ff' }}
                    />
                  </Col>
                  <Col span={12}>
                    <Statistic
                      title="样本外夏普"
                      value={result.inOutSampleComparison.outSampleSharpe}
                      precision={2}
                      valueStyle={{
                        color: result.inOutSampleComparison.outSampleSharpe >=
                               result.inOutSampleComparison.inSampleSharpe * 0.7
                          ? '#52c41a' : '#ff4d4f'
                      }}
                    />
                  </Col>
                </Row>

                <div className="border-t border-dark-border pt-4">
                  <div className="flex justify-between items-center mb-2">
                    <span>稳定性比率</span>
                    <Tag color={getVerdictColor(result.inOutSampleComparison.verdict)}>
                      {result.inOutSampleComparison.verdict === 'robust' ? '稳健' :
                       result.inOutSampleComparison.verdict === 'moderate' ? '一般' : '可能过拟合'}
                    </Tag>
                  </div>
                  <Progress
                    percent={Math.round(result.inOutSampleComparison.stabilityRatio * 100)}
                    strokeColor={result.inOutSampleComparison.stabilityRatio >= 0.7 ? '#52c41a' :
                                 result.inOutSampleComparison.stabilityRatio >= 0.5 ? '#faad14' : '#ff4d4f'}
                  />
                  <div className="text-xs text-gray-500 mt-2">
                    <Tooltip title="样本外夏普 / 样本内夏普。>0.7 表示稳健，0.5-0.7 一般，<0.5 可能过拟合">
                      <InfoCircleOutlined /> 稳定性比率 = OOS / IS 夏普比率
                    </Tooltip>
                  </div>
                </div>
              </div>
            )}
          </Card>
        </Col>
      </Row>

      <Row gutter={24}>
        {/* Deflated Sharpe Ratio */}
        <Col span={12}>
          <Card title={<><SafetyOutlined /> Deflated Sharpe Ratio</>}>
            {!result.deflatedSharpeRatio ? (
              <div className="text-center text-gray-500 py-8">
                未计算 DSR
              </div>
            ) : (
              <div className="space-y-4">
                <Alert
                  type="info"
                  showIcon
                  message="什么是 DSR？"
                  description="调整多重检验偏差后的夏普比率。如果你测试了很多策略，最好的那个可能只是运气好。"
                />

                <Row gutter={16}>
                  <Col span={12}>
                    <Statistic
                      title="原始夏普"
                      value={result.deflatedSharpeRatio.originalSharpe}
                      precision={2}
                    />
                  </Col>
                  <Col span={12}>
                    <Statistic
                      title="调整后夏普"
                      value={result.deflatedSharpeRatio.deflatedSharpe}
                      precision={2}
                      valueStyle={{
                        color: result.deflatedSharpeRatio.significant ? '#52c41a' : '#ff4d4f'
                      }}
                    />
                  </Col>
                </Row>

                <div className="bg-dark-hover rounded p-3">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500">测试次数</span>
                    <span>{result.deflatedSharpeRatio.trialsCount}</span>
                  </div>
                  <div className="flex justify-between text-sm mt-2">
                    <span className="text-gray-500">调整系数</span>
                    <span>{result.deflatedSharpeRatio.adjustmentFactor.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between text-sm mt-2">
                    <span className="text-gray-500">p 值</span>
                    <span>{result.deflatedSharpeRatio.pValue.toFixed(4)}</span>
                  </div>
                  <div className="flex justify-between text-sm mt-2">
                    <span className="text-gray-500">统计显著</span>
                    <Tag color={result.deflatedSharpeRatio.significant ? 'green' : 'red'}>
                      {result.deflatedSharpeRatio.significant ? '是' : '否'}
                    </Tag>
                  </div>
                </div>
              </div>
            )}
          </Card>
        </Col>

        {/* 夏普比率上限检验 */}
        <Col span={12}>
          <Card title={<><WarningOutlined /> 夏普比率合理性检验</>}>
            {!result.sharpeUpperBound ? (
              <div className="text-center text-gray-500 py-8">
                未进行上限检验
              </div>
            ) : (
              <div className="space-y-4">
                <Alert
                  type="warning"
                  showIcon
                  message="经验法则"
                  description="夏普 > 3 几乎肯定过拟合，夏普 > 2 需要仔细检查，夏普 1-2 是合理范围。"
                />

                <Row gutter={16}>
                  <Col span={12}>
                    <Statistic
                      title="观察夏普"
                      value={result.sharpeUpperBound.observedSharpe}
                      precision={2}
                    />
                  </Col>
                  <Col span={12}>
                    <Statistic
                      title="理论上限"
                      value={result.sharpeUpperBound.theoreticalUpperBound}
                      precision={2}
                    />
                  </Col>
                </Row>

                <div className="text-center">
                  <Tag
                    color={getVerdictColor(result.sharpeUpperBound.verdict)}
                    className="text-lg px-4 py-1"
                  >
                    {result.sharpeUpperBound.verdict === 'acceptable' ? '合理范围' :
                     result.sharpeUpperBound.verdict === 'suspicious' ? '需要警惕' : '可能过拟合'}
                  </Tag>
                  <div className="text-xs text-gray-500 mt-2">
                    超过上限的概率: {(result.sharpeUpperBound.exceedsProbability * 100).toFixed(0)}%
                  </div>
                </div>
              </div>
            )}
          </Card>
        </Col>
      </Row>
    </div>
  )
}
