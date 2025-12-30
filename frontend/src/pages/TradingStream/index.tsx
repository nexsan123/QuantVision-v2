/**
 * 实时交易流页面
 *
 * 显示实时交易事件、价格行情和账户状态
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
} from '@ant-design/icons'

import { useTradingStream } from '@/hooks/useTradingStream'
import {
  TradingEventCard,
  ConnectionStatus,
  TradingModeToggle,
  PriceGrid,
} from '@/components/Trading'
import { TradingEventType } from '@/types/trading'

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

  // 是否已连接
  const isConnected = state.connectionStatus === 'connected'

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

      {/* 主内容区 */}
      <div className="grid grid-cols-3 gap-6">
        {/* 左侧：事件流 */}
        <div className="col-span-2">
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
                {/* 事件类型筛选 */}
                <Select
                  value={eventFilter}
                  onChange={setEventFilter}
                  options={eventTypeFilters}
                  style={{ width: 140 }}
                  size="small"
                />

                {/* 股票筛选 */}
                <Input
                  placeholder="筛选股票"
                  prefix={<FilterOutlined />}
                  value={symbolFilter}
                  onChange={(e) => setSymbolFilter(e.target.value)}
                  style={{ width: 120 }}
                  size="small"
                  allowClear
                />

                {/* 清空事件 */}
                <Button
                  type="text"
                  icon={<DeleteOutlined />}
                  onClick={clearEvents}
                  size="small"
                  disabled={state.events.length === 0}
                >
                  清空
                </Button>
              </Space>
            }
            className="bg-dark-card border-dark-border"
            bodyStyle={{ padding: 0, maxHeight: 600, overflow: 'auto' }}
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
                description={
                  isConnected
                    ? '等待交易事件...'
                    : '连接后显示实时事件'
                }
                className="py-12"
              />
            )}
          </Card>
        </div>

        {/* 右侧：价格和持仓 */}
        <div className="space-y-6">
          {/* 实时行情 */}
          <Card
            title={
              <Space>
                <DollarOutlined />
                <span>实时行情</span>
              </Space>
            }
            className="bg-dark-card border-dark-border"
          >
            {prices.size > 0 ? (
              <PriceGrid prices={prices} maxItems={8} />
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
            className="bg-dark-card border-dark-border"
          >
            {positions.length > 0 ? (
              <List
                dataSource={positions}
                renderItem={(pos) => (
                  <List.Item className="!border-dark-border">
                    <div className="flex items-center justify-between w-full">
                      <div>
                        <div className="font-medium text-gray-200">
                          {pos.symbol}
                        </div>
                        <div className="text-xs text-gray-500">
                          {pos.quantity}股 @ ${pos.avgPrice.toFixed(2)}
                        </div>
                      </div>
                      <div className="text-right">
                        <div
                          className={`font-medium ${
                            pos.unrealizedPnl >= 0
                              ? 'text-green-400'
                              : 'text-red-400'
                          }`}
                        >
                          {pos.unrealizedPnl >= 0 ? '+' : ''}$
                          {pos.unrealizedPnl.toFixed(2)}
                        </div>
                        <div
                          className={`text-xs ${
                            pos.unrealizedPnlPercent >= 0
                              ? 'text-green-400'
                              : 'text-red-400'
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
