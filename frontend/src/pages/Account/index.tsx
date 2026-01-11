/**
 * 账户总览页面
 * 显示账户资金、持仓、运行中策略
 */
import { useState, useEffect, useCallback } from 'react'
import { Row, Col, Card, Table, Tag, Progress, Statistic, Button, Spin, message } from 'antd'
import {
  DollarOutlined,
  StockOutlined,
  RocketOutlined,
  SyncOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined,
  WalletOutlined,
  PieChartOutlined,
} from '@ant-design/icons'
import {
  getAccountOverview,
  AccountInfo as APIAccountInfo,
  Position as APIPosition,
  RunningStrategy as APIRunningStrategy,
  AccountOverviewResponse,
  hasAnyMockData,
  formatDataSourceMessage,
} from '@/services/accountService'
import { DataSourceIndicator, DataSourcesState } from '@/components/common/DataSourceIndicator'

// 转换接口 (API 使用 snake_case, 前端使用 camelCase)
interface AccountInfo {
  totalValue: number
  cashBalance: number
  buyingPower: number
  portfolioValue: number
  dayPnl: number
  dayPnlPct: number
  totalPnl: number
  totalPnlPct: number
}

interface Position {
  symbol: string
  quantity: number
  avgCost: number
  currentPrice: number
  marketValue: number
  pnl: number
  pnlPct: number
  weight: number
}

interface RunningStrategy {
  id: string
  name: string
  environment: 'paper' | 'live'
  status: 'running' | 'paused'
  pnl: number
  pnlPct: number
  trades: number
  winRate: number
  startedAt: string
}

// 转换函数
function transformAccountInfo(api: APIAccountInfo): AccountInfo {
  return {
    totalValue: api.total_value,
    cashBalance: api.cash_balance,
    buyingPower: api.buying_power,
    portfolioValue: api.portfolio_value,
    dayPnl: api.day_pnl,
    dayPnlPct: api.day_pnl_pct,
    totalPnl: api.total_pnl,
    totalPnlPct: api.total_pnl_pct,
  }
}

function transformPosition(api: APIPosition): Position {
  return {
    symbol: api.symbol,
    quantity: api.quantity,
    avgCost: api.avg_cost,
    currentPrice: api.current_price,
    marketValue: api.market_value,
    pnl: api.pnl,
    pnlPct: api.pnl_pct,
    weight: api.weight,
  }
}

function transformStrategy(api: APIRunningStrategy): RunningStrategy {
  return {
    id: api.id,
    name: api.name,
    environment: api.environment,
    status: api.status,
    pnl: api.pnl,
    pnlPct: api.pnl_pct,
    trades: api.trades,
    winRate: api.win_rate,
    startedAt: api.started_at,
  }
}

// 默认账户信息
const defaultAccountInfo: AccountInfo = {
  totalValue: 0,
  cashBalance: 0,
  buyingPower: 0,
  portfolioValue: 0,
  dayPnl: 0,
  dayPnlPct: 0,
  totalPnl: 0,
  totalPnlPct: 0,
}

export default function AccountPage() {
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [accountInfo, setAccountInfo] = useState<AccountInfo>(defaultAccountInfo)
  const [positions, setPositions] = useState<Position[]>([])
  const [strategies, setStrategies] = useState<RunningStrategy[]>([])
  const [dataSources, setDataSources] = useState<DataSourcesState>({})
  const [lastUpdated, setLastUpdated] = useState<string>('')

  // 加载数据
  const loadData = useCallback(async (showRefreshing = false) => {
    if (showRefreshing) setRefreshing(true)
    else setLoading(true)

    try {
      // 调用真实 API
      const data: AccountOverviewResponse = await getAccountOverview()

      setAccountInfo(transformAccountInfo(data.account))
      setPositions(data.positions.map(transformPosition))
      setStrategies(data.running_strategies.map(transformStrategy))
      setDataSources(data.data_sources as DataSourcesState)
      setLastUpdated(data.last_updated)

      // 如果有 Mock 数据，显示提示
      if (hasAnyMockData(data)) {
        const mockMessage = formatDataSourceMessage(data)
        if (mockMessage) {
          message.warning(mockMessage, 5)
        }
      }
    } catch {
      message.error('加载账户数据失败')
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [])

  useEffect(() => {
    loadData()
  }, [loadData])

  const handleRefresh = () => {
    loadData(true)
  }

  // 持仓表格列
  const positionColumns = [
    {
      title: '股票',
      dataIndex: 'symbol',
      key: 'symbol',
      render: (symbol: string) => <span className="font-medium text-white">{symbol}</span>,
    },
    {
      title: '数量',
      dataIndex: 'quantity',
      key: 'quantity',
      align: 'right' as const,
      render: (qty: number) => <span className="font-mono">{qty}</span>,
    },
    {
      title: '成本',
      dataIndex: 'avgCost',
      key: 'avgCost',
      align: 'right' as const,
      render: (cost: number) => <span className="font-mono">${cost.toFixed(2)}</span>,
    },
    {
      title: '现价',
      dataIndex: 'currentPrice',
      key: 'currentPrice',
      align: 'right' as const,
      render: (price: number) => <span className="font-mono">${price.toFixed(2)}</span>,
    },
    {
      title: '市值',
      dataIndex: 'marketValue',
      key: 'marketValue',
      align: 'right' as const,
      render: (value: number) => <span className="font-mono">${value.toLocaleString()}</span>,
    },
    {
      title: '盈亏',
      dataIndex: 'pnl',
      key: 'pnl',
      align: 'right' as const,
      render: (pnl: number, record: Position) => (
        <div className={pnl >= 0 ? 'text-green-400' : 'text-red-400'}>
          <div className="font-mono">{pnl >= 0 ? '+' : ''}${pnl.toLocaleString()}</div>
          <div className="text-xs">{pnl >= 0 ? '+' : ''}{(record.pnlPct * 100).toFixed(2)}%</div>
        </div>
      ),
    },
    {
      title: '占比',
      dataIndex: 'weight',
      key: 'weight',
      width: 120,
      render: (weight: number) => (
        <Progress
          percent={weight * 100}
          size="small"
          format={p => `${p?.toFixed(0)}%`}
          strokeColor="#3b82f6"
        />
      ),
    },
  ]

  // 策略表格列
  const strategyColumns = [
    {
      title: '策略名称',
      dataIndex: 'name',
      key: 'name',
      render: (name: string) => <span className="font-medium text-white">{name}</span>,
    },
    {
      title: '环境',
      dataIndex: 'environment',
      key: 'environment',
      render: (env: string) => (
        <Tag color={env === 'live' ? 'green' : 'blue'}>
          {env === 'live' ? '实盘' : '模拟'}
        </Tag>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={status === 'running' ? 'green' : 'orange'}>
          {status === 'running' ? '运行中' : '已暂停'}
        </Tag>
      ),
    },
    {
      title: '收益',
      dataIndex: 'pnl',
      key: 'pnl',
      align: 'right' as const,
      render: (pnl: number, record: RunningStrategy) => (
        <div className={pnl >= 0 ? 'text-green-400' : 'text-red-400'}>
          <div className="font-mono">{pnl >= 0 ? '+' : ''}${pnl.toLocaleString()}</div>
          <div className="text-xs">{pnl >= 0 ? '+' : ''}{(record.pnlPct * 100).toFixed(2)}%</div>
        </div>
      ),
    },
    {
      title: '交易/胜率',
      key: 'trades',
      align: 'center' as const,
      render: (_: unknown, record: RunningStrategy) => (
        <div>
          <div>{record.trades} 笔</div>
          <div className={record.winRate >= 0.5 ? 'text-green-400' : 'text-yellow-400'}>
            {(record.winRate * 100).toFixed(1)}%
          </div>
        </div>
      ),
    },
    {
      title: '启动时间',
      dataIndex: 'startedAt',
      key: 'startedAt',
    },
  ]

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Spin size="large" tip="加载账户数据..." />
      </div>
    )
  }

  return (
    <div className="space-y-6 animate-in">
      {/* 页面标题 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">账户总览</h1>
          <p className="text-gray-500">
            查看账户资金、持仓和策略运行状态
            {lastUpdated && (
              <span className="ml-2 text-xs">
                (更新于 {new Date(lastUpdated).toLocaleTimeString()})
              </span>
            )}
          </p>
        </div>
        <div className="flex items-center gap-4">
          <DataSourceIndicator sources={dataSources} onRefresh={handleRefresh} />
          <Button
            icon={<SyncOutlined spin={refreshing} />}
            onClick={handleRefresh}
            loading={refreshing}
          >
            刷新数据
          </Button>
        </div>
      </div>

      {/* 账户概览卡片 */}
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <Card className="!bg-dark-card">
            <Statistic
              title={<span className="text-gray-400"><WalletOutlined className="mr-2" />账户总值</span>}
              value={accountInfo.totalValue}
              precision={2}
              prefix="$"
              valueStyle={{ color: '#fff', fontSize: '24px' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card className="!bg-dark-card">
            <Statistic
              title={<span className="text-gray-400"><DollarOutlined className="mr-2" />现金余额</span>}
              value={accountInfo.cashBalance}
              precision={2}
              prefix="$"
              valueStyle={{ color: '#60a5fa', fontSize: '24px' }}
            />
            <div className="text-xs text-gray-500 mt-1">
              购买力: ${accountInfo.buyingPower.toLocaleString()}
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card className="!bg-dark-card">
            <Statistic
              title={<span className="text-gray-400"><PieChartOutlined className="mr-2" />今日盈亏</span>}
              value={accountInfo.dayPnl}
              precision={2}
              prefix={accountInfo.dayPnl >= 0 ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
              suffix={`(${accountInfo.dayPnl >= 0 ? '+' : ''}${(accountInfo.dayPnlPct * 100).toFixed(2)}%)`}
              valueStyle={{
                color: accountInfo.dayPnl >= 0 ? '#4ade80' : '#f87171',
                fontSize: '24px'
              }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card className="!bg-dark-card">
            <Statistic
              title={<span className="text-gray-400"><StockOutlined className="mr-2" />总盈亏</span>}
              value={accountInfo.totalPnl}
              precision={2}
              prefix={accountInfo.totalPnl >= 0 ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
              suffix={`(${accountInfo.totalPnl >= 0 ? '+' : ''}${(accountInfo.totalPnlPct * 100).toFixed(2)}%)`}
              valueStyle={{
                color: accountInfo.totalPnl >= 0 ? '#4ade80' : '#f87171',
                fontSize: '24px'
              }}
            />
          </Card>
        </Col>
      </Row>

      {/* 持仓列表 */}
      <Card
        className="!bg-dark-card"
        title={
          <span>
            <StockOutlined className="mr-2" />
            持仓明细
            <Tag className="ml-2">{positions.length} 只</Tag>
          </span>
        }
      >
        <Table
          columns={positionColumns}
          dataSource={positions}
          rowKey="symbol"
          pagination={false}
          size="small"
        />
      </Card>

      {/* 运行中策略 */}
      <Card
        className="!bg-dark-card"
        title={
          <span>
            <RocketOutlined className="mr-2" />
            运行中策略
            <Tag color="green" className="ml-2">{strategies.filter(s => s.status === 'running').length} 个</Tag>
          </span>
        }
      >
        {strategies.length > 0 ? (
          <Table
            columns={strategyColumns}
            dataSource={strategies}
            rowKey="id"
            pagination={false}
            size="small"
          />
        ) : (
          <div className="text-center py-8 text-gray-500">
            暂无运行中的策略
          </div>
        )}
      </Card>
    </div>
  )
}
