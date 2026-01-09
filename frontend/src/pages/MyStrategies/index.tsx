/**
 * 我的策略页面
 *
 * PRD 核心页面: 区分"策略配置"与"策略部署"
 * - 策略库 Tab: 显示所有策略配置(可回测、可部署)
 * - 运行中 Tab: 显示所有部署实例(模拟盘/实盘)
 */
import { useState, useEffect, useCallback } from 'react'
import {
  Card,
  Table,
  Tag,
  Button,
  Input,
  Select,
  Space,
  Dropdown,
  message,
  Modal,
  Tabs,
  Tooltip,
  Badge,
} from 'antd'
import {
  PlusOutlined,
  SearchOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
  SettingOutlined,
  MoreOutlined,
  DeleteOutlined,
  SwapOutlined,
  LineChartOutlined,
  RocketOutlined,
  StarOutlined,
  StarFilled,
  CopyOutlined,
  EditOutlined,
} from '@ant-design/icons'
import { useNavigate, useSearchParams } from 'react-router-dom'
import type { MenuProps, TabsProps } from 'antd'
import type { Strategy, StrategyStatus } from '../../types/strategy'
import {
  Deployment,
  DeploymentStatus,
  DeploymentEnvironment,
  STATUS_CONFIG,
  ENV_CONFIG,
  STRATEGY_TYPE_CONFIG,
  StrategyType,
} from '../../types/deployment'
import DeploymentWizard from '../../components/Deployment/DeploymentWizard'
import {
  getStrategies,
  getStrategy,
  deleteStrategy,
  toggleFavorite,
  duplicateStrategy,
  updateStrategy,
} from '../../services/strategyService'
import {
  getDeployments,
  startDeployment,
  pauseDeployment,
  deleteDeployment as deleteDeploymentApi,
  switchDeploymentEnvironment,
} from '../../services/deploymentService'

// 策略状态配置
const STRATEGY_STATUS_CONFIG: Record<StrategyStatus, { label: string; color: string }> = {
  draft: { label: '草稿', color: 'default' },
  backtest: { label: '回测中', color: 'processing' },
  paper: { label: '模拟中', color: 'blue' },
  live: { label: '实盘中', color: 'green' },
  paused: { label: '已暂停', color: 'orange' },
  archived: { label: '已归档', color: 'default' },
}

export default function MyStrategiesPage() {
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const deployStrategyId = searchParams.get('deploy')

  const [activeTab, setActiveTab] = useState<'library' | 'running'>('library')

  // 策略库状态
  const [strategies, setStrategies] = useState<Strategy[]>([])
  const [strategiesLoading, setStrategiesLoading] = useState(false)
  const [strategySearch, setStrategySearch] = useState('')
  const [strategyStatusFilter, setStrategyStatusFilter] = useState<StrategyStatus | ''>('')

  // 部署状态
  const [deployments, setDeployments] = useState<Deployment[]>([])
  const [deploymentsLoading, setDeploymentsLoading] = useState(false)
  const [deploymentSearch, setDeploymentSearch] = useState('')
  const [deploymentStatusFilter, setDeploymentStatusFilter] = useState<DeploymentStatus | ''>('')
  const [deploymentEnvFilter, setDeploymentEnvFilter] = useState<DeploymentEnvironment | ''>('')

  // 部署向导
  const [wizardVisible, setWizardVisible] = useState(false)
  const [selectedStrategy, setSelectedStrategy] = useState<Strategy | null>(null)

  // 加载策略库
  const fetchStrategies = useCallback(async () => {
    setStrategiesLoading(true)
    try {
      const result = await getStrategies({
        status: strategyStatusFilter || undefined,
        search: strategySearch || undefined,
      })
      setStrategies(result.items)
    } catch {
      message.error('获取策略列表失败')
    } finally {
      setStrategiesLoading(false)
    }
  }, [strategyStatusFilter, strategySearch])

  // 加载部署列表 (使用 deploymentService)
  const fetchDeployments = useCallback(async () => {
    setDeploymentsLoading(true)
    try {
      const result = await getDeployments({
        status: deploymentStatusFilter || undefined,
        environment: deploymentEnvFilter || undefined,
      })
      let filtered = result.items
      // 客户端搜索过滤
      if (deploymentSearch) {
        const search = deploymentSearch.toLowerCase()
        filtered = filtered.filter(
          d =>
            d.strategyName.toLowerCase().includes(search) ||
            d.deploymentName.toLowerCase().includes(search)
        )
      }
      setDeployments(filtered)
    } catch {
      message.error('获取部署列表失败')
    } finally {
      setDeploymentsLoading(false)
    }
  }, [deploymentStatusFilter, deploymentEnvFilter, deploymentSearch])

  useEffect(() => {
    if (activeTab === 'library') {
      fetchStrategies()
    } else {
      fetchDeployments()
    }
  }, [activeTab, fetchStrategies, fetchDeployments])

  // 处理 deploy URL 参数 - 从回测页面跳转过来时自动打开部署向导
  useEffect(() => {
    if (deployStrategyId && strategies.length > 0) {
      const strategy = strategies.find(s => s.id === deployStrategyId)
      if (strategy) {
        setSelectedStrategy(strategy)
        setWizardVisible(true)
        // 清除 URL 参数
        setSearchParams({})
      } else {
        // 策略不在当前列表中，尝试加载
        getStrategy(deployStrategyId).then(loaded => {
          if (loaded) {
            setSelectedStrategy(loaded)
            setWizardVisible(true)
            setSearchParams({})
          } else {
            message.warning('未找到要部署的策略')
          }
        })
      }
    }
  }, [deployStrategyId, strategies, setSearchParams])

  // ==================== 策略操作 ====================

  const handleToggleFavorite = async (strategy: Strategy) => {
    try {
      await toggleFavorite(strategy.id)
      fetchStrategies()
    } catch {
      message.error('操作失败')
    }
  }

  const handleDeleteStrategy = async (id: string) => {
    Modal.confirm({
      title: '确认删除',
      content: '删除后无法恢复，且关联的部署也将被删除。确定要删除此策略吗？',
      okType: 'danger',
      onOk: async () => {
        try {
          await deleteStrategy(id)
          message.success('删除成功')
          fetchStrategies()
        } catch {
          message.error('删除失败')
        }
      },
    })
  }

  const handleDuplicateStrategy = async (strategy: Strategy) => {
    try {
      await duplicateStrategy(strategy.id, `${strategy.name} (副本)`)
      message.success('复制成功')
      fetchStrategies()
    } catch {
      message.error('复制失败')
    }
  }

  const handleBacktest = (strategy: Strategy) => {
    navigate(`/backtest?strategyId=${strategy.id}`)
  }

  const handleDeploy = (strategy: Strategy) => {
    setSelectedStrategy(strategy)
    setWizardVisible(true)
  }

  const handleEditStrategy = (strategy: Strategy) => {
    navigate(`/strategy?id=${strategy.id}`)
  }

  // ==================== 部署操作 (使用 deploymentService) ====================

  const handleStartDeployment = async (id: string) => {
    try {
      const deployment = await startDeployment(id)
      // 同步更新策略状态
      if (deployment.strategyId) {
        await updateStrategy(deployment.strategyId, {
          status: deployment.environment === 'live' ? 'live' : 'paper',
        })
      }
      message.success('启动成功')
      fetchDeployments()
      fetchStrategies() // 刷新策略列表以更新状态
    } catch {
      message.error('启动失败')
    }
  }

  const handlePauseDeployment = async (id: string) => {
    try {
      const deployment = await pauseDeployment(id)
      // 同步更新策略状态
      if (deployment.strategyId) {
        await updateStrategy(deployment.strategyId, { status: 'paused' })
      }
      message.success('已暂停')
      fetchDeployments()
      fetchStrategies()
    } catch {
      message.error('暂停失败')
    }
  }

  const handleDeleteDeployment = async (id: string) => {
    Modal.confirm({
      title: '确认删除',
      content: '删除后无法恢复，确定要删除此部署吗？',
      okType: 'danger',
      onOk: async () => {
        try {
          await deleteDeploymentApi(id)
          message.success('删除成功')
          fetchDeployments()
        } catch {
          message.error('删除失败')
        }
      },
    })
  }

  const handleSwitchEnv = async (id: string, currentEnv: DeploymentEnvironment) => {
    const targetEnv = currentEnv === 'paper' ? 'live' : 'paper'
    Modal.confirm({
      title: `切换到${targetEnv === 'live' ? '实盘' : '模拟盘'}`,
      content:
        targetEnv === 'live'
          ? '切换到实盘将使用真实资金进行交易，请确认已充分测试策略。'
          : '切换到模拟盘后将使用虚拟资金。',
      onOk: async () => {
        try {
          await switchDeploymentEnvironment(id, targetEnv)
          message.success('环境切换成功')
          fetchDeployments()
        } catch {
          message.error('环境切换失败')
        }
      },
    })
  }

  // ==================== 策略表格列 ====================

  const getStrategyMenuItems = (record: Strategy): MenuProps['items'] => [
    {
      key: 'edit',
      icon: <EditOutlined />,
      label: '编辑策略',
      onClick: () => handleEditStrategy(record),
    },
    {
      key: 'backtest',
      icon: <LineChartOutlined />,
      label: '运行回测',
      onClick: () => handleBacktest(record),
    },
    {
      key: 'deploy',
      icon: <RocketOutlined />,
      label: '部署策略',
      onClick: () => handleDeploy(record),
      disabled: !record.lastBacktest,
    },
    { type: 'divider' },
    {
      key: 'duplicate',
      icon: <CopyOutlined />,
      label: '复制策略',
      onClick: () => handleDuplicateStrategy(record),
    },
    { type: 'divider' },
    {
      key: 'delete',
      icon: <DeleteOutlined />,
      label: '删除',
      danger: true,
      onClick: () => handleDeleteStrategy(record.id),
    },
  ]

  const strategyColumns = [
    {
      title: '策略名称',
      dataIndex: 'name',
      key: 'name',
      render: (text: string, record: Strategy) => (
        <div className="flex items-center gap-2">
          <Button
            type="text"
            size="small"
            icon={record.isFavorite ? <StarFilled className="text-yellow-400" /> : <StarOutlined />}
            onClick={() => handleToggleFavorite(record)}
          />
          <div>
            <div className="font-medium text-white">{text}</div>
            <div className="text-xs text-gray-500 truncate max-w-[200px]">{record.description}</div>
          </div>
        </div>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: StrategyStatus) => (
        <Tag color={STRATEGY_STATUS_CONFIG[status].color}>
          {STRATEGY_STATUS_CONFIG[status].label}
        </Tag>
      ),
    },
    {
      title: '来源',
      dataIndex: 'source',
      key: 'source',
      width: 80,
      render: (source: Strategy['source']) => (
        <span className="text-gray-400">
          {source === 'template' ? '模板' : source === 'imported' ? '导入' : '自建'}
        </span>
      ),
    },
    {
      title: '最近回测',
      key: 'lastBacktest',
      width: 180,
      render: (_: unknown, record: Strategy) =>
        record.lastBacktest ? (
          <div>
            <div className="flex items-center gap-2">
              <span
                className={
                  record.lastBacktest.annualReturn >= 0 ? 'text-green-400' : 'text-red-400'
                }
              >
                {(record.lastBacktest.annualReturn * 100).toFixed(1)}% 年化
              </span>
              <span className="text-gray-500">|</span>
              <span className="text-blue-400">
                SR: {record.lastBacktest.sharpeRatio.toFixed(2)}
              </span>
            </div>
            <div className="text-xs text-gray-500">
              回撤: {(record.lastBacktest.maxDrawdown * 100).toFixed(1)}%
            </div>
          </div>
        ) : (
          <span className="text-gray-500">未回测</span>
        ),
    },
    {
      title: '部署',
      dataIndex: 'deploymentCount',
      key: 'deploymentCount',
      width: 80,
      align: 'center' as const,
      render: (count: number) =>
        count > 0 ? (
          <Badge count={count} style={{ backgroundColor: '#52c41a' }} />
        ) : (
          <span className="text-gray-500">-</span>
        ),
    },
    {
      title: '更新时间',
      dataIndex: 'updatedAt',
      key: 'updatedAt',
      width: 120,
      render: (date: string) => new Date(date).toLocaleDateString(),
    },
    {
      title: '操作',
      key: 'action',
      width: 180,
      render: (_: unknown, record: Strategy) => (
        <Space>
          <Tooltip title="运行回测">
            <Button
              icon={<LineChartOutlined />}
              size="small"
              onClick={() => handleBacktest(record)}
            />
          </Tooltip>
          <Tooltip title={record.lastBacktest ? '部署策略' : '请先完成回测'}>
            <Button
              icon={<RocketOutlined />}
              size="small"
              type="primary"
              disabled={!record.lastBacktest}
              onClick={() => handleDeploy(record)}
            />
          </Tooltip>
          <Dropdown menu={{ items: getStrategyMenuItems(record) }} trigger={['click']}>
            <Button icon={<MoreOutlined />} size="small" />
          </Dropdown>
        </Space>
      ),
    },
  ]

  // ==================== 部署表格列 ====================

  const getDeploymentMenuItems = (record: Deployment): MenuProps['items'] => [
    {
      key: 'detail',
      label: '查看详情',
      onClick: () => navigate(`/deployment/${record.deploymentId}`),
    },
    {
      key: 'signals',
      label: '查看信号',
    },
    {
      key: 'switch',
      icon: <SwapOutlined />,
      label: record.environment === 'paper' ? '切换到实盘' : '切换到模拟盘',
      onClick: () => handleSwitchEnv(record.deploymentId, record.environment),
    },
    { type: 'divider' },
    {
      key: 'delete',
      icon: <DeleteOutlined />,
      label: '删除',
      danger: true,
      onClick: () => handleDeleteDeployment(record.deploymentId),
    },
  ]

  const deploymentColumns = [
    {
      title: '策略/部署名称',
      key: 'name',
      render: (_: unknown, record: Deployment) => (
        <div>
          <div className="font-medium text-white">{record.strategyName}</div>
          <div className="text-xs text-gray-500">{record.deploymentName}</div>
        </div>
      ),
    },
    {
      title: '环境',
      dataIndex: 'environment',
      key: 'environment',
      width: 100,
      render: (env: DeploymentEnvironment) => (
        <Tag color={ENV_CONFIG[env].color}>{ENV_CONFIG[env].label}</Tag>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: DeploymentStatus) => (
        <Tag color={STATUS_CONFIG[status].color}>{STATUS_CONFIG[status].label}</Tag>
      ),
    },
    {
      title: '类型',
      dataIndex: 'strategyType',
      key: 'strategyType',
      width: 100,
      render: (type: StrategyType) => STRATEGY_TYPE_CONFIG[type].label,
    },
    {
      title: '收益',
      key: 'pnl',
      width: 120,
      render: (_: unknown, record: Deployment) => (
        <div className={record.currentPnl >= 0 ? 'text-green-400' : 'text-red-400'}>
          <div className="font-medium font-mono">
            {record.currentPnl >= 0 ? '+' : ''}${record.currentPnl.toFixed(2)}
          </div>
          <div className="text-xs">
            {record.currentPnl >= 0 ? '+' : ''}
            {(record.currentPnlPct * 100).toFixed(2)}%
          </div>
        </div>
      ),
    },
    {
      title: '交易/胜率',
      key: 'trades',
      width: 100,
      render: (_: unknown, record: Deployment) => (
        <div>
          <div>{record.totalTrades} 笔</div>
          <div className={record.winRate >= 0.5 ? 'text-green-400' : 'text-yellow-400'}>
            {(record.winRate * 100).toFixed(1)}%
          </div>
        </div>
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      render: (_: unknown, record: Deployment) => (
        <Space>
          {record.status === 'running' ? (
            <Button
              icon={<PauseCircleOutlined />}
              size="small"
              onClick={() => handlePauseDeployment(record.deploymentId)}
            />
          ) : (
            <Button
              icon={<PlayCircleOutlined />}
              size="small"
              type="primary"
              onClick={() => handleStartDeployment(record.deploymentId)}
            />
          )}
          <Button
            icon={<SettingOutlined />}
            size="small"
            onClick={() => navigate(`/deployment/${record.deploymentId}/edit`)}
          />
          <Dropdown menu={{ items: getDeploymentMenuItems(record) }} trigger={['click']}>
            <Button icon={<MoreOutlined />} size="small" />
          </Dropdown>
        </Space>
      ),
    },
  ]

  // ==================== Tab Items ====================

  const tabItems: TabsProps['items'] = [
    {
      key: 'library',
      label: (
        <span>
          策略库
          <Badge count={strategies.length} className="ml-2" style={{ backgroundColor: '#1677ff' }} />
        </span>
      ),
      children: (
        <div className="space-y-4">
          {/* 筛选栏 */}
          <Card className="!bg-dark-card">
            <div className="flex flex-wrap gap-4">
              <Input
                placeholder="搜索策略..."
                prefix={<SearchOutlined className="text-gray-500" />}
                value={strategySearch}
                onChange={e => setStrategySearch(e.target.value)}
                className="w-64"
                allowClear
              />
              <Select
                placeholder="状态"
                value={strategyStatusFilter || undefined}
                onChange={v => setStrategyStatusFilter(v || '')}
                allowClear
                className="w-32"
                options={Object.entries(STRATEGY_STATUS_CONFIG).map(([key, config]) => ({
                  value: key,
                  label: config.label,
                }))}
              />
            </div>
          </Card>

          {/* 策略列表 */}
          <Card className="!bg-dark-card">
            <Table
              columns={strategyColumns}
              dataSource={strategies}
              rowKey="id"
              loading={strategiesLoading}
              pagination={{
                pageSize: 10,
                showSizeChanger: true,
                showTotal: total => `共 ${total} 条`,
              }}
            />
          </Card>
        </div>
      ),
    },
    {
      key: 'running',
      label: (
        <span>
          运行中
          <Badge
            count={deployments.filter(d => d.status === 'running').length}
            className="ml-2"
            style={{ backgroundColor: '#52c41a' }}
          />
        </span>
      ),
      children: (
        <div className="space-y-4">
          {/* 筛选栏 */}
          <Card className="!bg-dark-card">
            <div className="flex flex-wrap gap-4">
              <Input
                placeholder="搜索部署..."
                prefix={<SearchOutlined className="text-gray-500" />}
                value={deploymentSearch}
                onChange={e => setDeploymentSearch(e.target.value)}
                className="w-64"
                allowClear
              />
              <Select
                placeholder="状态"
                value={deploymentStatusFilter || undefined}
                onChange={v => setDeploymentStatusFilter(v || '')}
                allowClear
                className="w-32"
                options={Object.entries(STATUS_CONFIG).map(([key, config]) => ({
                  value: key,
                  label: config.label,
                }))}
              />
              <Select
                placeholder="环境"
                value={deploymentEnvFilter || undefined}
                onChange={v => setDeploymentEnvFilter(v || '')}
                allowClear
                className="w-32"
                options={Object.entries(ENV_CONFIG).map(([key, config]) => ({
                  value: key,
                  label: config.label,
                }))}
              />
            </div>
          </Card>

          {/* 部署列表 */}
          <Card className="!bg-dark-card">
            <Table
              columns={deploymentColumns}
              dataSource={deployments}
              rowKey="deploymentId"
              loading={deploymentsLoading}
              pagination={{
                pageSize: 10,
                showSizeChanger: true,
                showTotal: total => `共 ${total} 条`,
              }}
            />
          </Card>
        </div>
      ),
    },
  ]

  return (
    <div className="space-y-6 animate-in">
      {/* 页面标题 */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold">我的策略</h1>
          <p className="text-gray-500">管理策略配置与部署实例</p>
        </div>
        <Space>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => navigate('/strategy')}>
            创建策略
          </Button>
          <Button onClick={() => navigate('/templates')}>浏览模板</Button>
        </Space>
      </div>

      {/* Tabs */}
      <Tabs
        activeKey={activeTab}
        onChange={key => setActiveTab(key as 'library' | 'running')}
        items={tabItems}
        className="strategy-tabs"
      />

      {/* 部署向导 */}
      {selectedStrategy && (
        <DeploymentWizard
          strategyId={selectedStrategy.id}
          strategyName={selectedStrategy.name}
          strategyConfig={selectedStrategy.config}
          visible={wizardVisible}
          onClose={() => {
            setWizardVisible(false)
            setSelectedStrategy(null)
          }}
          onComplete={async config => {
            // 调用 deploymentService 创建部署
            const { createDeployment } = await import('../../services/deploymentService')
            await createDeployment({
              config,
              autoStart: true,
            })
            // 同步更新策略状态
            await updateStrategy(selectedStrategy.id, {
              status: config.environment === 'live' ? 'live' : 'paper',
              deploymentCount: (selectedStrategy.deploymentCount || 0) + 1,
            })
            message.success('部署成功')
            setWizardVisible(false)
            setSelectedStrategy(null)
            setActiveTab('running')
            fetchDeployments()
            fetchStrategies()
          }}
        />
      )}
    </div>
  )
}
