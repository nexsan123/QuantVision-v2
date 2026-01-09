/**
 * 预警配置面板组件
 * PRD 4.14
 */
import { useState } from 'react'
import {
  Form,
  Switch,
  InputNumber,
  Input,
  Button,
  Card,
  Divider,
  TimePicker,
  message,
  Tooltip,
} from 'antd'
import {
  MailOutlined,
  BellOutlined,
  InfoCircleOutlined,
  SendOutlined,
} from '@ant-design/icons'
import dayjs from 'dayjs'
import { AlertConfig } from '../../types/alert'

interface AlertConfigPanelProps {
  config: AlertConfig
  onSave?: (config: AlertConfig) => Promise<void>
  onTestEmail?: () => Promise<void>
}

export default function AlertConfigPanel({
  config,
  onSave,
  onTestEmail,
}: AlertConfigPanelProps) {
  const [form] = Form.useForm()
  const [saving, setSaving] = useState(false)
  const [testing, setTesting] = useState(false)

  // 处理保存
  const handleSave = async (values: any) => {
    if (!onSave) return

    setSaving(true)
    try {
      const updatedConfig: AlertConfig = {
        ...config,
        enabled: values.enabled,
        dailyLossThreshold: values.dailyLossThreshold,
        maxDrawdownThreshold: values.maxDrawdownThreshold,
        concentrationThreshold: values.concentrationThreshold,
        vixThreshold: values.vixThreshold,
        emailEnabled: values.emailEnabled,
        emailAddress: values.emailAddress,
        quietHoursStart: values.quietHours?.[0]?.hour() ?? undefined,
        quietHoursEnd: values.quietHours?.[1]?.hour() ?? undefined,
      }

      await onSave(updatedConfig)
      message.success('预警配置已保存')
    } catch (error) {
      message.error('保存失败，请重试')
    } finally {
      setSaving(false)
    }
  }

  // 处理测试邮件
  const handleTestEmail = async () => {
    if (!onTestEmail) return

    const emailAddress = form.getFieldValue('emailAddress')
    if (!emailAddress) {
      message.warning('请先填写邮箱地址')
      return
    }

    setTesting(true)
    try {
      await onTestEmail()
      message.success('测试邮件已发送')
    } catch (error) {
      message.error('发送失败，请检查邮箱配置')
    } finally {
      setTesting(false)
    }
  }

  // 初始值
  const initialValues = {
    enabled: config.enabled,
    dailyLossThreshold: config.dailyLossThreshold,
    maxDrawdownThreshold: config.maxDrawdownThreshold,
    concentrationThreshold: config.concentrationThreshold,
    vixThreshold: config.vixThreshold,
    emailEnabled: config.emailEnabled,
    emailAddress: config.emailAddress,
    quietHours:
      config.quietHoursStart !== undefined && config.quietHoursEnd !== undefined
        ? [dayjs().hour(config.quietHoursStart), dayjs().hour(config.quietHoursEnd)]
        : undefined,
  }

  return (
    <div className="space-y-4">
      <Form
        form={form}
        layout="vertical"
        initialValues={initialValues}
        onFinish={handleSave}
      >
        {/* 基础设置 */}
        <Card
          title={
            <div className="flex items-center gap-2">
              <BellOutlined />
              <span>预警开关</span>
            </div>
          }
          className="bg-dark-card border-gray-700"
          headStyle={{ borderBottom: '1px solid #374151' }}
        >
          <Form.Item
            name="enabled"
            valuePropName="checked"
            label="启用风险预警"
          >
            <Switch />
          </Form.Item>
        </Card>

        {/* 阈值设置 */}
        <Card
          title={
            <div className="flex items-center gap-2">
              <span>📊</span>
              <span>预警阈值</span>
            </div>
          }
          className="bg-dark-card border-gray-700"
          headStyle={{ borderBottom: '1px solid #374151' }}
        >
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Form.Item
              name="dailyLossThreshold"
              label={
                <div className="flex items-center gap-1">
                  <span>单日亏损阈值</span>
                  <Tooltip title="当单日亏损超过此比例时触发预警">
                    <InfoCircleOutlined className="text-gray-500" />
                  </Tooltip>
                </div>
              }
            >
              <InputNumber
                min={0}
                max={100}
                step={0.5}
                formatter={(value) => `${value}%`}
                parser={(value) => value?.replace('%', '') as any}
                className="w-full"
              />
            </Form.Item>

            <Form.Item
              name="maxDrawdownThreshold"
              label={
                <div className="flex items-center gap-1">
                  <span>最大回撤阈值</span>
                  <Tooltip title="当组合回撤超过此比例时触发预警">
                    <InfoCircleOutlined className="text-gray-500" />
                  </Tooltip>
                </div>
              }
            >
              <InputNumber
                min={0}
                max={100}
                step={1}
                formatter={(value) => `${value}%`}
                parser={(value) => value?.replace('%', '') as any}
                className="w-full"
              />
            </Form.Item>

            <Form.Item
              name="concentrationThreshold"
              label={
                <div className="flex items-center gap-1">
                  <span>持仓集中度阈值</span>
                  <Tooltip title="当单一持仓占比超过此比例时触发预警">
                    <InfoCircleOutlined className="text-gray-500" />
                  </Tooltip>
                </div>
              }
            >
              <InputNumber
                min={0}
                max={100}
                step={5}
                formatter={(value) => `${value}%`}
                parser={(value) => value?.replace('%', '') as any}
                className="w-full"
              />
            </Form.Item>

            <Form.Item
              name="vixThreshold"
              label={
                <div className="flex items-center gap-1">
                  <span>VIX预警阈值</span>
                  <Tooltip title="当VIX指数超过此值时触发预警">
                    <InfoCircleOutlined className="text-gray-500" />
                  </Tooltip>
                </div>
              }
            >
              <InputNumber min={0} max={100} step={1} className="w-full" />
            </Form.Item>
          </div>
        </Card>

        {/* 邮件设置 */}
        <Card
          title={
            <div className="flex items-center gap-2">
              <MailOutlined />
              <span>邮件通知</span>
            </div>
          }
          className="bg-dark-card border-gray-700"
          headStyle={{ borderBottom: '1px solid #374151' }}
        >
          <Form.Item
            name="emailEnabled"
            valuePropName="checked"
            label="启用邮件通知"
          >
            <Switch />
          </Form.Item>

          <Form.Item
            noStyle
            shouldUpdate={(prev, curr) => prev.emailEnabled !== curr.emailEnabled}
          >
            {({ getFieldValue }) =>
              getFieldValue('emailEnabled') && (
                <>
                  <Form.Item
                    name="emailAddress"
                    label="通知邮箱"
                    rules={[
                      { type: 'email', message: '请输入有效的邮箱地址' },
                    ]}
                  >
                    <Input
                      placeholder="your@email.com"
                      suffix={
                        <Button
                          type="link"
                          size="small"
                          icon={<SendOutlined />}
                          loading={testing}
                          onClick={handleTestEmail}
                        >
                          测试
                        </Button>
                      }
                    />
                  </Form.Item>

                  <Form.Item name="quietHours" label="免打扰时段">
                    <TimePicker.RangePicker
                      format="HH:00"
                      placeholder={['开始时间', '结束时间']}
                      className="w-full"
                    />
                  </Form.Item>

                  <p className="text-gray-500 text-xs">
                    在免打扰时段内，预警仅记录不发送邮件
                  </p>
                </>
              )
            }
          </Form.Item>
        </Card>

        {/* 保存按钮 */}
        <div className="flex justify-end">
          <Button type="primary" htmlType="submit" loading={saving}>
            保存配置
          </Button>
        </div>
      </Form>
    </div>
  )
}
