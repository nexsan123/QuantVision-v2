/**
 * 实时交易流页面
 * PRD 4.16 实时交易监控界面
 *
 * v2.1 更新: 添加 TradingView 图表到中间工作台
 */

import { useState, useCallback, useMemo } from 'react'
import {
  Card,
  Button,
  Space,
  Empty,
  Statistic,
  Row,
  Col,
  Badge,
  List,
  Select,
  Input,
} from 'antd'
import {
  PlayCircleOutlined,
  PauseCircleOutlined,
  ReloadOutlined,
  DeleteOutlined,
  FilterOutlined,
  DollarOutlined,
  StockOutlined,
  BellOutlined,
  LineChartOutlined,
} from '@ant-design/icons'

import { useTradingStream } from '@/hooks/useTradingStream'
import {
  TradingEventCard,
  ConnectionStatus,
  TradingModeToggle,
  PriceGrid,
} from '@/components/Trading'
import { TradingEventType } from '@/types/trading'
import TradingViewChart from '@/components/Chart/TradingViewChart'

import './TradingStream.css'

// 事件类型筛选选项
const eventTypeFilters: { value: TradingEventType | 'all'; label: string }[] = [
  { value: 'all', label: '全部事件' },
  { value: 'order_submitted', label: '订单提交' },
  { value: 'order_filled', label: '订单成交' },
  { value: 'position_opened', label: '开仓' },
  { value: 'position_closed', label: '平仓' },
  { value: 'price_update', label: '价格更新' },
  { value: 'risk_alert', label: '风险警报' },
]

export function TradingStream() {
  // 使用交易流 Hook
  const {
    state,
    prices,
    positions,
    portfolio,
    connect,
    disconnect,
    reconnect,
    setMode,
    clearEvents,
  } = useTradingStream({ maxEvents: 200 })

  // 本地状态
  const [eventFilter, setEventFilter] = useState<TradingEventType | 'all'>('all')
  const [symbolFilter, setSymbolFilter] = useState<string>('')
  const [selectedSymbol, setSelectedSymbol] = useState<string>('NVDA')  // 当前查看的股票

  // 是否已连接
  const isConnected = state.connectionStatus === 'connected'

  // 股票选项列表
  const symbolOptions = [
    { value: 'NVDA', label: 'NVDA - NVIDIA' },
    { value: 'AAPL', label: 'AAPL - Apple' },
    { value: 'TSLA', label: 'TSLA - Tesla' },
    { value: 'MSFT', label: 'MSFT - Microsoft' },
    { value: 'GOOGL', label: 'GOOGL - Alphabet' },
    { value: 'AMZN', label: 'AMZN - Amazon' },
  ]

  // 筛选后的事件
  const filteredEvents = useMemo(() => {
    return state.events.filter((event) => {
      // 类型筛选
      if (eventFilter !== 'all' && event.type !== eventFilter) {
        return false
      }
      // 股票筛选
      if (symbolFilter && event.symbol) {
        return event.symbol.toLowerCase().includes(symbolFilter.toLowerCase())
      }
      return true
    })
  }, [state.events, eventFilter, symbolFilter])

  // 连接切换
  const handleConnectionToggle = useCallback(() => {
    if (isConnected) {
      disconnect()
    } else {
      connect()
    }
  }, [isConnected, connect, disconnect])

  return (
    <div className="trading-stream-page p-6">
      {/* 页面头部 */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-100">实时交易流</h1>
          <p className="text-gray-400 text-sm mt-1">
            实时监控交易事件、价格行情和账户状态
          </p>
        </div>

        <Space size="middle">
          {/* 连接状态 */}
          <ConnectionStatus
            status={state.connectionStatus}
            reconnectAttempts={state.reconnectAttempts}
            lastHeartbeat={state.lastHeartbeat}
          />

          {/* 交易模式切换 */}
          <TradingModeToggle
            mode={state.mode}
            onChange={setMode}
            disabled={isConnected}
          />

          {/* 连接控制 */}
          <Button
            type={isConnected ? 'default' : 'primary'}
            icon={isConnected ? <PauseCircleOutlined /> : <PlayCircleOutlined />}
            onClick={handleConnectionToggle}
          >
            {isConnected ? '断开连接' : '开始连接'}
          </Button>

          {/* 重连 */}
          {state.connectionStatus === 'error' && (
            <Button icon={<ReloadOutlined />} onClick={reconnect}>
              重新连接
            </Button>
          )}
        </Space>
      </div>

      {/* 账户摘要 */}
      {portfolio && (
        <Card className="mb-6 bg-dark-card border-dark-border">
          <Row gutter={24}>
            <Col span={4}>
              <Statistic
                title="总资产"
                value={portfolio.totalValue}
                precision={2}
                prefix="$"
                valueStyle={{ color: '#fff' }}
              />
            </Col>
            <Col span={4}>
              <Statistic
                title="现金余额"
                value={portfolio.cashBalance}
                precision={2}
                prefix="$"
                valueStyle={{ color: '#fff' }}
              />
            </Col>
            <Col span={4}>
              <Statistic
                title="市值"
                value={portfolio.marketValue}
                precision={2}
                prefix="$"
                valueStyle={{ color: '#fff' }}
              />
            </Col>
            <Col span={4}>
              <Statistic
                title="未实现盈亏"
                value={portfolio.unrealizedPnl}
                precision={2}
                prefix="$"
                valueStyle={{
                  color: portfolio.unrealizedPnl >= 0 ? '#52c41a' : '#ff4d4f',
                }}
              />
            </Col>
            <Col span={4}>
              <Statistic
                title="今日盈亏"
                value={portfolio.dailyPnl}
                precision={2}
                prefix="$"
                suffix={`(${portfolio.dailyPnlPercent >= 0 ? '+' : ''}${portfolio.dailyPnlPercent.toFixed(2)}%)`}
                valueStyle={{
                  color: portfolio.dailyPnl >= 0 ? '#52c41a' : '#ff4d4f',
                }}
              />
            </Col>
            <Col span={4}>
              <Statistic
                title="持仓数"
                value={portfolio.positionCount}
                valueStyle={{ color: '#fff' }}
                suffix="个"
              />
            </Col>
          </Row>
        </Card>
      )}

      {/* 主内容区 - 三栏布局 */}
      <div className="flex gap-4" style={{ height: 'calc(100vh - 280px)' }}>
        {/* 左侧：事件流 */}
        <div className="w-[360px] flex-shrink-0">
          <Card
            title={
              <Space>
                <BellOutlined />
                <span>交易事件</span>
                <Badge count={filteredEvents.length} showZero color="#1890ff" />
              </Space>
            }
            extra={
              <Space>
                <Select
                  value={eventFilter}
                  onChange={setEventFilter}
                  options={eventTypeFilters}
                  style={{ width: 120 }}
                  size="small"
                />
                <Button
                  type="text"
                  icon={<DeleteOutlined />}
                  onClick={clearEvents}
                  size="small"
                  disabled={state.events.length === 0}
                />
              </Space>
            }
            className="bg-dark-card border-dark-border h-full"
            bodyStyle={{ padding: 0, height: 'calc(100% - 57px)', overflow: 'auto' }}
          >
            {filteredEvents.length > 0 ? (
              <List
                dataSource={filteredEvents}
                renderItem={(event) => (
                  <List.Item className="!border-dark-border !px-4">
                    <TradingEventCard event={event} />
                  </List.Item>
                )}
              />
            ) : (
              <Empty
                description={isConnected ? '等待交易事件...' : '连接后显示实时事件'}
                className="py-12"
              />
            )}
          </Card>
        </div>

        {/* 中间：TradingView 图表 - 填满工作台 */}
        <div className="flex-1 flex flex-col min-w-0">
          <Card
            title={
              <Space>
                <LineChartOutlined />
                <span>实时图表</span>
                <Select
                  value={selectedSymbol}
                  onChange={setSelectedSymbol}
                  options={symbolOptions}
                  style={{ width: 160 }}
                  size="small"
                />
              </Space>
            }
            extra={
              <Input
                placeholder="筛选股票"
                prefix={<FilterOutlined />}
                value={symbolFilter}
                onChange={(e) => setSymbolFilter(e.target.value)}
                style={{ width: 120 }}
                size="small"
                allowClear
              />
            }
            className="bg-dark-card border-dark-border h-full flex flex-col"
            bodyStyle={{ flex: 1, padding: 0, minHeight: 0 }}
          >
            <div className="h-full">
              <TradingViewChart
                symbol={selectedSymbol}
                interval="5"
                theme="dark"
                autosize={true}
                className="h-full"
              />
            </div>
          </Card>
        </div>

        {/* 右侧：价格和持仓 */}
        <div className="w-[300px] flex-shrink-0 flex flex-col gap-4">
          {/* 实时行情 */}
          <Card
            title={
              <Space>
                <DollarOutlined />
                <span>实时行情</span>
              </Space>
            }
            className="bg-dark-card border-dark-border"
            size="small"
          >
            {prices.size > 0 ? (
              <PriceGrid prices={prices} maxItems={6} />
            ) : (
              <Empty description="暂无行情数据" />
            )}
          </Card>

          {/* 当前持仓 */}
          <Card
            title={
              <Space>
                <StockOutlined />
                <span>当前持仓</span>
                <Badge count={positions.length} showZero color="#1890ff" />
              </Space>
            }
            className="bg-dark-card border-dark-border flex-1"
            size="small"
            bodyStyle={{ maxHeight: 300, overflow: 'auto' }}
          >
            {positions.length > 0 ? (
              <List
                dataSource={positions}
                size="small"
                renderItem={(pos) => (
                  <List.Item className="!border-dark-border !py-2">
                    <div className="flex items-center justify-between w-full">
                      <div>
                        <div className="font-medium text-gray-200 text-sm">
                          {pos.symbol}
                        </div>
                        <div className="text-xs text-gray-500">
                          {pos.quantity}股 @ ${pos.avgPrice.toFixed(2)}
                        </div>
                      </div>
                      <div className="text-right">
                        <div
                          className={`font-medium text-sm ${
                            pos.unrealizedPnl >= 0 ? 'text-green-400' : 'text-red-400'
                          }`}
                        >
                          {pos.unrealizedPnl >= 0 ? '+' : ''}${pos.unrealizedPnl.toFixed(2)}
                        </div>
                        <div
                          className={`text-xs ${
                            pos.unrealizedPnlPercent >= 0 ? 'text-green-400' : 'text-red-400'
                          }`}
                        >
                          {pos.unrealizedPnlPercent >= 0 ? '+' : ''}
                          {pos.unrealizedPnlPercent.toFixed(2)}%
                        </div>
                      </div>
                    </div>
                  </List.Item>
                )}
              />
            ) : (
              <Empty description="暂无持仓" />
            )}
          </Card>
        </div>
      </div>

      {/* 错误提示 */}
      {state.error && (
        <div className="fixed bottom-4 right-4 bg-red-900/90 text-red-200 px-4 py-2 rounded-lg shadow-lg">
          {state.error}
        </div>
      )}
    </div>
  )
}

export default TradingStream
