import { useState } from 'react'
import { Outlet, useLocation, useNavigate } from 'react-router-dom'
import { Layout, Menu } from 'antd'
import {
  DashboardOutlined,
  ExperimentOutlined,
  SettingOutlined,
  LineChartOutlined,
  SwapOutlined,
  SafetyOutlined,
} from '@ant-design/icons'

const { Sider, Content } = Layout

const menuItems = [
  { key: '/dashboard', icon: <DashboardOutlined />, label: '仪表盘' },
  { key: '/factor-lab', icon: <ExperimentOutlined />, label: '因子实验室' },
  { key: '/strategy', icon: <SettingOutlined />, label: '策略构建' },
  { key: '/backtest', icon: <LineChartOutlined />, label: '回测中心' },
  { key: '/trading', icon: <SwapOutlined />, label: '交易执行' },
  { key: '/risk', icon: <SafetyOutlined />, label: '风险中心' },
]

export default function MainLayout() {
  const [collapsed, setCollapsed] = useState(false)
  const location = useLocation()
  const navigate = useNavigate()

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
        <Content className="p-6 bg-dark-bg overflow-auto">
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  )
}
