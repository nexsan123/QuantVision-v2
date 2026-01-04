/**
 * Step 7: 监控层配置组件
 * 持续监控和告警配置
 */
import { useState } from 'react'
import { Form, Select, Switch, Row, Col, Alert, Button, Table, InputNumber, Tag, Space } from 'antd'
import { PlusOutlined, DeleteOutlined, InfoCircleOutlined, BellOutlined } from '@ant-design/icons'
import { Card } from '@/components/ui'
import {
  MonitorConfig, AlertRule, AlertType, NotifyChannel, MonitorMetric,
  DEFAULT_MONITOR_CONFIG
} from '@/types/strategy'

const { Option } = Select

interface StepMonitorProps {
  value: MonitorConfig
  onChange: (config: MonitorConfig) => void
}

const ALERT_TYPES: { value: AlertType; label: string; description: string; color: string }[] = [
  { value: 'drawdown', label: '回撤告警', description: '回撤超过阈值', color: 'red' },
  { value: 'daily_loss', label: '日亏损告警', description: '单日亏损超过阈值', color: 'orange' },
  { value: 'position_drift', label: '持仓偏离告警', description: '实际持仓偏离目标', color: 'yellow' },
  { value: 'factor_decay', label: '因子衰减告警', description: '因子IC显著下降', color: 'purple' },
  { value: 'execution_fail', label: '执行失败告警', description: '订单执行异常', color: 'volcano' },
  { value: 'circuit_breaker', label: '熔断告警', description: '触发熔断机制', color: 'magenta' },
]

const NOTIFY_CHANNELS: { value: NotifyChannel; label: string }[] = [
  { value: 'email', label: '邮件' },
  { value: 'sms', label: '短信' },
  { value: 'push', label: '推送通知' },
  { value: 'webhook', label: 'Webhook' },
]

const DEFAULT_METRICS: MonitorMetric[] = [
  { name: '总收益', showOnDashboard: true, refreshInterval: 60 },
  { name: '夏普比率', showOnDashboard: true, refreshInterval: 3600 },
  { name: '当前回撤', showOnDashboard: true, refreshInterval: 60 },
  { name: '今日盈亏', showOnDashboard: true, refreshInterval: 60 },
  { name: '持仓数量', showOnDashboard: true, refreshInterval: 300 },
  { name: '换手率', showOnDashboard: false, refreshInterval: 3600 },
  { name: '因子IC', showOnDashboard: false, refreshInterval: 86400 },
]

export default function StepMonitor({ value = DEFAULT_MONITOR_CONFIG, onChange }: StepMonitorProps) {
  const [metrics] = useState<MonitorMetric[]>(DEFAULT_METRICS)

  const updateField = <K extends keyof MonitorConfig>(field: K, fieldValue: MonitorConfig[K]) => {
    onChange({ ...value, [field]: fieldValue })
  }

  const addAlert = () => {
    const newAlert: AlertRule = {
      id: `alert_${Date.now()}`,
      type: 'drawdown',
      threshold: 10,
      channels: ['email'],
      enabled: true,
    }
    updateField('alerts', [...value.alerts, newAlert])
  }

  const removeAlert = (alertId: string) => {
    updateField('alerts', value.alerts.filter(a => a.id !== alertId))
  }

  const updateAlert = (alertId: string, updates: Partial<AlertRule>) => {
    updateField('alerts', value.alerts.map(a =>
      a.id === alertId ? { ...a, ...updates } : a
    ))
  }

  const alertColumns = [
    {
      title: '告警类型',
      dataIndex: 'type',
      render: (type: AlertType) => {
        const alertType = ALERT_TYPES.find(t => t.value === type)
        return (
          <Tag color={alertType?.color}>
            {alertType?.label || type}
          </Tag>
        )
      },
    },
    {
      title: '配置',
      key: 'config',
      render: (_: unknown, record: AlertRule) => (
        <Space>
          <Select
            value={record.type}
            onChange={(v) => updateAlert(record.id, { type: v })}
            style={{ width: 120 }}
            size="small"
          >
            {ALERT_TYPES.map(t => (
              <Option key={t.value} value={t.value}>{t.label}</Option>
            ))}
          </Select>
          <InputNumber
            value={record.threshold}
            onChange={(v) => updateAlert(record.id, { threshold: v || 0 })}
            style={{ width: 80 }}
            size="small"
            addonAfter="%"
          />
        </Space>
      ),
    },
    {
      title: '通知渠道',
      dataIndex: 'channels',
      render: (channels: NotifyChannel[], record: AlertRule) => (
        <Select
          mode="multiple"
          value={channels}
          onChange={(v) => updateAlert(record.id, { channels: v })}
          style={{ width: 150 }}
          size="small"
        >
          {NOTIFY_CHANNELS.map(c => (
            <Option key={c.value} value={c.value}>{c.label}</Option>
          ))}
        </Select>
      ),
    },
    {
      title: '启用',
      dataIndex: 'enabled',
      width: 80,
      render: (enabled: boolean, record: AlertRule) => (
        <Switch
          checked={enabled}
          onChange={(v) => updateAlert(record.id, { enabled: v })}
          size="small"
        />
      ),
    },
    {
      title: '操作',
      width: 60,
      render: (_: unknown, record: AlertRule) => (
        <Button
          type="text"
          danger
          size="small"
          icon={<DeleteOutlined />}
          onClick={() => removeAlert(record.id)}
        />
      ),
    },
  ]

  return (
    <div className="space-y-6">
      {/* 教育提示 */}
      <Alert
        type="info"
        showIcon
        icon={<InfoCircleOutlined />}
        message="持续监控的重要性"
        description="策略上线只是开始，持续监控才是关键。市场环境变化、因子衰减、执行异常都需要及时发现。好的监控系统可以帮你在问题变严重之前采取行动。"
      />

      <Row gutter={24}>
        <Col span={14}>
          {/* 告警规则 */}
          <Card
            title={
              <span>
                <BellOutlined className="mr-2" />
                告警规则
              </span>
            }
            extra={
              <Button
                type="link"
                icon={<PlusOutlined />}
                onClick={addAlert}
              >
                添加告警
              </Button>
            }
          >
            <Table
              dataSource={value.alerts}
              columns={alertColumns}
              rowKey="id"
              size="small"
              pagination={false}
            />
          </Card>

          {/* 报告配置 */}
          <Card title="报告配置" className="mt-4">
            <Form layout="vertical">
              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item label="报告生成频率">
                    <Select
                      value={value.reportFrequency}
                      onChange={(v) => updateField('reportFrequency', v)}
                    >
                      <Option value="daily">每日报告</Option>
                      <Option value="weekly">每周报告</Option>
                      <Option value="monthly">每月报告</Option>
                    </Select>
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item label="实时监控">
                    <Switch
                      checked={value.enableRealtime}
                      onChange={(v) => updateField('enableRealtime', v)}
                    />
                    <span className="ml-2 text-gray-500">
                      {value.enableRealtime ? 'WebSocket实时推送' : '轮询更新'}
                    </span>
                  </Form.Item>
                </Col>
              </Row>
            </Form>
          </Card>
        </Col>

        <Col span={10}>
          {/* 仪表盘指标 */}
          <Card title="仪表盘指标">
            <div className="space-y-2">
              {metrics.map((metric, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-2 bg-dark-hover rounded"
                >
                  <span>{metric.name}</span>
                  <div className="flex items-center gap-2">
                    <Tag color={metric.showOnDashboard ? 'blue' : 'default'}>
                      {metric.showOnDashboard ? '显示' : '隐藏'}
                    </Tag>
                    <span className="text-xs text-gray-500">
                      {metric.refreshInterval < 60
                        ? `${metric.refreshInterval}秒`
                        : metric.refreshInterval < 3600
                        ? `${metric.refreshInterval / 60}分钟`
                        : `${metric.refreshInterval / 3600}小时`}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </Card>

          {/* 告警类型说明 */}
          <Card title="告警类型说明" className="mt-4">
            <div className="space-y-3 text-sm">
              {ALERT_TYPES.map(alert => (
                <div key={alert.value} className="flex items-start gap-2">
                  <Tag color={alert.color} className="mt-1">{alert.label}</Tag>
                  <span className="text-gray-500">{alert.description}</span>
                </div>
              ))}
            </div>
          </Card>

          {/* 最佳实践 */}
          <Card title="监控最佳实践" className="mt-4">
            <div className="space-y-2 text-sm text-gray-400">
              <div className="flex items-start gap-2">
                <span className="text-green-400">1.</span>
                <span>设置多层告警：预警 &gt; 警告 &gt; 紧急</span>
              </div>
              <div className="flex items-start gap-2">
                <span className="text-green-400">2.</span>
                <span>熔断告警必须启用，是最后一道防线</span>
              </div>
              <div className="flex items-start gap-2">
                <span className="text-green-400">3.</span>
                <span>定期检查因子衰减，市场一直在变化</span>
              </div>
              <div className="flex items-start gap-2">
                <span className="text-green-400">4.</span>
                <span>每周阅读策略报告，了解运行状态</span>
              </div>
            </div>
          </Card>
        </Col>
      </Row>
    </div>
  )
}
