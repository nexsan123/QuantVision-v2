import { Row, Col, Statistic, Empty, Alert, Button, Tooltip } from 'antd'
import {
  ArrowUpOutlined,
  ArrowDownOutlined,
  ReloadOutlined,
  InfoCircleOutlined,
} from '@ant-design/icons'
import { Card, NumberDisplay } from '@/components/ui'
import { ReturnChart, PieChart } from '@/components/Chart'
import { PanelErrorBoundary } from '@/components/common/ErrorBoundary'
import {
  StatCardSkeleton,
  ChartSkeleton,
  TableSkeleton,
} from '@/components/common/LoadingStates'
import { useDashboardData } from '@/hooks/useDashboard'

/**
 * 仪表盘页面
 *
 * 展示:
 * - 组合总览
 * - 关键指标
 * - 收益曲线
 * - 持仓分布
 * - 最近交易
 */
export default function Dashboard() {
  const {
    portfolio,
    returnChart,
    holdings,
    recentTrades,
    isLoading,
    refetchAll,
  } = useDashboardData()

  // 格式化更新时间
  const formatUpdateTime = () => {
    return new Date().toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  return (
    <div className="space-y-6 animate-in">
      {/* 页面标题 */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">仪表盘</h1>
        <div className="flex items-center gap-4">
          <span className="text-gray-500 text-sm">
            更新于 {formatUpdateTime()}
          </span>
          <Tooltip title="刷新数据">
            <Button
              type="text"
              icon={<ReloadOutlined spin={isLoading} />}
              onClick={() => refetchAll()}
              disabled={isLoading}
            />
          </Tooltip>
        </div>
      </div>

      {/* 错误提示 */}
      {portfolio.error && (
        <Alert
          message="数据加载失败"
          description="无法连接到后端服务，请检查服务是否正常运行"
          type="warning"
          showIcon
          closable
          action={
            <Button size="small" onClick={() => refetchAll()}>
              重试
            </Button>
          }
        />
      )}

      {/* 关键指标 */}
      <PanelErrorBoundary title="关键指标">
        {portfolio.isLoading ? (
          <StatCardSkeleton count={4} />
        ) : portfolio.data ? (
          <Row gutter={[16, 16]}>
            <Col xs={24} sm={12} lg={6}>
              <Card className="h-full">
                <Statistic
                  title={<span className="text-gray-400">组合总值</span>}
                  value={portfolio.data.totalValue}
                  precision={2}
                  prefix="$"
                  valueStyle={{ color: '#e5e7eb', fontFamily: 'JetBrains Mono' }}
                />
                <div className="mt-2 text-xs text-gray-500 flex items-center gap-1">
                  <InfoCircleOutlined />
                  <span>现金: ${portfolio.data.cash?.toLocaleString() ?? '-'}</span>
                </div>
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <Card className="h-full">
                <Statistic
                  title={<span className="text-gray-400">今日盈亏</span>}
                  value={portfolio.data.dailyPnL}
                  precision={2}
                  prefix={portfolio.data.dailyPnL >= 0 ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
                  valueStyle={{
                    color: portfolio.data.dailyPnL >= 0 ? '#22c55e' : '#ef4444',
                    fontFamily: 'JetBrains Mono',
                  }}
                />
                <div className="mt-1">
                  <NumberDisplay
                    value={portfolio.data.dailyReturn}
                    type="percent"
                    colorize
                    showSign
                    size="sm"
                  />
                </div>
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <Card className="h-full">
                <Statistic
                  title={<span className="text-gray-400">累计收益</span>}
                  value={portfolio.data.totalReturn * 100}
                  precision={2}
                  suffix="%"
                  prefix={portfolio.data.totalReturn >= 0 ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
                  valueStyle={{
                    color: portfolio.data.totalReturn >= 0 ? '#22c55e' : '#ef4444',
                    fontFamily: 'JetBrains Mono',
                  }}
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <Card className="h-full">
                <div className="flex justify-between items-start">
                  <div>
                    <div className="text-gray-400 mb-1">夏普比率</div>
                    <NumberDisplay value={portfolio.data.sharpe} type="ratio" size="xl" />
                  </div>
                  <div className="text-right">
                    <div className="text-gray-400 mb-1">最大回撤</div>
                    <NumberDisplay
                      value={portfolio.data.maxDrawdown}
                      type="percent"
                      colorize
                      size="lg"
                    />
                  </div>
                </div>
              </Card>
            </Col>
          </Row>
        ) : (
          <Empty description="暂无组合数据" />
        )}
      </PanelErrorBoundary>

      {/* 图表区域 */}
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={16}>
          <PanelErrorBoundary title="收益曲线">
            <Card title="收益曲线" subtitle="策略 vs 基准">
              {returnChart.isLoading ? (
                <ChartSkeleton height={350} type="line" />
              ) : returnChart.data ? (
                <ReturnChart data={returnChart.data} height={350} />
              ) : (
                <Empty
                  description="暂无收益数据"
                  style={{ height: 350, display: 'flex', flexDirection: 'column', justifyContent: 'center' }}
                />
              )}
            </Card>
          </PanelErrorBoundary>
        </Col>
        <Col xs={24} lg={8}>
          <PanelErrorBoundary title="持仓分布">
            <Card title="持仓分布" subtitle="按市值占比">
              {holdings.isLoading ? (
                <ChartSkeleton height={350} type="pie" />
              ) : holdings.data && holdings.data.length > 0 ? (
                <PieChart data={holdings.data} height={350} />
              ) : (
                <Empty
                  description="暂无持仓"
                  style={{ height: 350, display: 'flex', flexDirection: 'column', justifyContent: 'center' }}
                />
              )}
            </Card>
          </PanelErrorBoundary>
        </Col>
      </Row>

      {/* 最近交易 */}
      <PanelErrorBoundary title="最近交易">
        <Card title="最近交易" subtitle="最近5笔">
          {recentTrades.isLoading ? (
            <TableSkeleton rows={5} columns={6} />
          ) : recentTrades.data && recentTrades.data.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="text-left text-gray-500 border-b border-dark-border">
                    <th className="pb-3">时间</th>
                    <th className="pb-3">股票</th>
                    <th className="pb-3">方向</th>
                    <th className="pb-3 text-right">数量</th>
                    <th className="pb-3 text-right">价格</th>
                    <th className="pb-3 text-right">金额</th>
                  </tr>
                </thead>
                <tbody>
                  {recentTrades.data.map((trade, i) => (
                    <tr key={i} className="border-b border-dark-border hover:bg-dark-hover transition-colors">
                      <td className="py-3 font-mono text-gray-400">{trade.time}</td>
                      <td className="py-3 font-medium">{trade.symbol}</td>
                      <td className={`py-3 ${trade.side === 'BUY' ? 'text-profit' : 'text-loss'}`}>
                        {trade.side}
                      </td>
                      <td className="py-3 text-right font-mono">{trade.qty}</td>
                      <td className="py-3 text-right font-mono">${trade.price.toFixed(2)}</td>
                      <td className="py-3 text-right font-mono">${trade.amount.toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <Empty description="暂无交易记录" />
          )}
        </Card>
      </PanelErrorBoundary>
    </div>
  )
}
