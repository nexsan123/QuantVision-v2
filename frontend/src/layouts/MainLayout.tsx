import { useState, useEffect, useCallback } from 'react'
import { Outlet, useLocation, useNavigate } from 'react-router-dom'
import { Layout, Menu } from 'antd'
import {
  DashboardOutlined,
  ExperimentOutlined,
  SettingOutlined,
  LineChartOutlined,
  SwapOutlined,
  SafetyOutlined,
  FolderOutlined,
  AppstoreOutlined,
  PlayCircleOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons'
import { AIStatusIndicator } from '../components/AI'
import { AlertBell } from '../components/Alert'
import { AIConnectionStatus } from '../types/ai'
import { RiskAlert } from '../types/alert'

const { Sider, Content, Header } = Layout

const menuItems = [
  { key: '/dashboard', icon: <DashboardOutlined />, label: '仪表盘' },
  { key: '/my-strategies', icon: <FolderOutlined />, label: '我的策略' },
  { key: '/templates', icon: <AppstoreOutlined />, label: '策略模板' },
  { key: '/factor-lab', icon: <ExperimentOutlined />, label: '因子实验室' },
  { key: '/strategy', icon: <SettingOutlined />, label: '策略构建' },
  { key: '/strategy/replay', icon: <PlayCircleOutlined />, label: '策略回放' },
  { key: '/backtest', icon: <LineChartOutlined />, label: '回测中心' },
  { key: '/trading', icon: <SwapOutlined />, label: '交易执行' },
  { key: '/intraday', icon: <ThunderboltOutlined />, label: '日内交易' },
  { key: '/risk', icon: <SafetyOutlined />, label: '风险中心' },
]

export default function MainLayout() {
  const [collapsed, setCollapsed] = useState(false)
  const location = useLocation()
  const navigate = useNavigate()

  // AI 连接状态
  const [aiStatus, setAiStatus] = useState<AIConnectionStatus>({
    isConnected: false,
    status: 'connecting',
    modelName: 'Claude 4.5 Sonnet',
    latencyMs: undefined,
    canReconnect: true,
  })

  // API 基础URL
  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || ''

  // 检查 AI 连接状态
  const checkAIConnection = useCallback(async () => {
    // 检查网络状态
    if (!navigator.onLine) {
      setAiStatus(prev => ({
        ...prev,
        isConnected: false,
        status: 'offline',
        latencyMs: undefined,
      }))
      return
    }

    setAiStatus(prev => ({ ...prev, status: 'connecting' }))

    try {
      const startTime = Date.now()
      const response = await fetch(`${API_BASE_URL}/api/v1/ai/health`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
        signal: AbortSignal.timeout(5000),
      })

      const latencyMs = Date.now() - startTime

      if (response.ok) {
        const data = await response.json().catch(() => ({}))
        setAiStatus({
          isConnected: true,
          status: 'connected',
          modelName: data.model || 'Claude 4.5 Sonnet',
          latencyMs,
          lastHeartbeat: new Date().toISOString(),
          canReconnect: true,
        })
      } else {
        setAiStatus(prev => ({
          ...prev,
          isConnected: false,
          status: 'error',
          errorMessage: `API Error: ${response.status}`,
          canReconnect: true,
        }))
      }
    } catch (error) {
      // 连接失败时使用模拟连接状态 (开发模式)
      if (import.meta.env.DEV) {
        setAiStatus({
          isConnected: true,
          status: 'connected',
          modelName: 'Claude 4.5 Sonnet (Dev)',
          latencyMs: Math.floor(Math.random() * 150) + 50,
          lastHeartbeat: new Date().toISOString(),
          canReconnect: true,
        })
      } else {
        setAiStatus(prev => ({
          ...prev,
          isConnected: false,
          status: 'disconnected',
          errorMessage: error instanceof Error ? error.message : '连接失败',
          canReconnect: true,
        }))
      }
    }
  }, [API_BASE_URL])

  // 初始化和定期检查 AI 连接
  useEffect(() => {
    // 初始检查
    checkAIConnection()

    // 每30秒检查一次
    const interval = setInterval(checkAIConnection, 30000)

    // 监听网络状态变化
    const handleOnline = () => checkAIConnection()
    const handleOffline = () => {
      setAiStatus(prev => ({
        ...prev,
        isConnected: false,
        status: 'offline',
        latencyMs: undefined,
      }))
    }

    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)

    return () => {
      clearInterval(interval)
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [checkAIConnection])

  // 预警数据 (模拟数据)
  const [alerts, setAlerts] = useState<RiskAlert[]>([
    {
      alertId: '1',
      userId: 'demo',
      alertType: 'daily_loss',
      severity: 'warning',
      title: '单日亏损预警',
      message: '今日组合亏损已达 2.5%，接近预警阈值',
      isRead: false,
      isSent: true,
      createdAt: new Date(Date.now() - 3600000).toISOString(),
    },
    {
      alertId: '2',
      userId: 'demo',
      alertType: 'vix_high',
      severity: 'info',
      title: 'VIX 波动提醒',
      message: 'VIX 指数当前为 22.5，市场波动性上升',
      isRead: true,
      isSent: true,
      createdAt: new Date(Date.now() - 86400000).toISOString(),
    },
  ])

  const unreadCount = alerts.filter((a) => !a.isRead).length

  // 处理重连
  const handleReconnect = async () => {
    await checkAIConnection()
  }

  // 标记已读
  const handleMarkRead = (alertId: string) => {
    setAlerts((prev) =>
      prev.map((a) => (a.alertId === alertId ? { ...a, isRead: true } : a))
    )
  }

  // 全部已读
  const handleMarkAllRead = () => {
    setAlerts((prev) => prev.map((a) => ({ ...a, isRead: true })))
  }

  return (
    <Layout className="min-h-screen">
      <Sider
        collapsible
        collapsed={collapsed}
        onCollapse={setCollapsed}
        className="!bg-dark-card border-r border-dark-border"
        width={220}
      >
        <div className="h-16 flex items-center justify-center border-b border-dark-border">
          <span className="text-xl font-bold text-primary-400">
            {collapsed ? 'QV' : 'QuantVision'}
          </span>
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
          className="!bg-transparent !border-none mt-2"
        />
      </Sider>
      <Layout>
        <Header className="!bg-dark-card !px-6 border-b border-dark-border flex items-center justify-end gap-4">
          <AIStatusIndicator status={aiStatus} onReconnect={handleReconnect} />
          <AlertBell
            alerts={alerts}
            unreadCount={unreadCount}
            onMarkRead={handleMarkRead}
            onMarkAllRead={handleMarkAllRead}
          />
        </Header>
        <Content className="p-6 bg-dark-bg overflow-auto">
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  )
}
