import { Row, Col, Statistic } from 'antd'
import { ArrowUpOutlined, ArrowDownOutlined } from '@ant-design/icons'
import { Card, NumberDisplay } from '@/components/ui'
import { ReturnChart, PieChart } from '@/components/charts'

// 模拟数据
const mockPortfolioData = {
  totalValue: 1523456.78,
  dailyPnL: 12345.67,
  dailyReturn: 0.0082,
  totalReturn: 0.2345,
  sharpe: 1.85,
  maxDrawdown: -0.0856,
}

const mockReturnData = {
  dates: ['2024-01', '2024-02', '2024-03', '2024-04', '2024-05', '2024-06'],
  strategy: [0, 0.05, 0.08, 0.12, 0.15, 0.23],
  benchmark: [0, 0.03, 0.05, 0.07, 0.09, 0.12],
}

const mockHoldingsData = [
  { name: 'AAPL', value: 15.2 },
  { name: 'MSFT', value: 12.8 },
  { name: 'GOOGL', value: 10.5 },
  { name: 'AMZN', value: 8.9 },
  { name: 'NVDA', value: 7.6 },
  { name: '其他', value: 45.0 },
]

/**
 * 仪表盘页面
 *
 * 展示:
 * - 组合总览
 * - 关键指标
 * - 收益曲线
 * - 持仓分布
 */
export default function Dashboard() {
  return (
    <div className="space-y-6 animate-in">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">仪表盘</h1>
        <span className="text-gray-500">更新于 2024-12-28 15:30</span>
      </div>

      {/* 关键指标 */}
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <Card className="h-full">
            <Statistic
              title={<span className="text-gray-400">组合总值</span>}
              value={mockPortfolioData.totalValue}
              precision={2}
              prefix="$"
              valueStyle={{ color: '#e5e7eb', fontFamily: 'JetBrains Mono' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card className="h-full">
            <Statistic
              title={<span className="text-gray-400">今日盈亏</span>}
              value={mockPortfolioData.dailyPnL}
              precision={2}
              prefix={mockPortfolioData.dailyPnL >= 0 ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
              valueStyle={{
                color: mockPortfolioData.dailyPnL >= 0 ? '#22c55e' : '#ef4444',
                fontFamily: 'JetBrains Mono',
              }}
            />
            <div className="mt-1">
              <NumberDisplay
                value={mockPortfolioData.dailyReturn}
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
              value={mockPortfolioData.totalReturn * 100}
              precision={2}
              suffix="%"
              prefix={<ArrowUpOutlined />}
              valueStyle={{ color: '#22c55e', fontFamily: 'JetBrains Mono' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card className="h-full">
            <div className="flex justify-between items-start">
              <div>
                <div className="text-gray-400 mb-1">夏普比率</div>
                <NumberDisplay value={mockPortfolioData.sharpe} type="ratio" size="xl" />
              </div>
              <div className="text-right">
                <div className="text-gray-400 mb-1">最大回撤</div>
                <NumberDisplay
                  value={mockPortfolioData.maxDrawdown}
                  type="percent"
                  colorize
                  size="lg"
                />
              </div>
            </div>
          </Card>
        </Col>
      </Row>

      {/* 图表区域 */}
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={16}>
          <Card title="收益曲线" subtitle="策略 vs 基准">
            <ReturnChart data={mockReturnData} height={350} />
          </Card>
        </Col>
        <Col xs={24} lg={8}>
          <Card title="持仓分布" subtitle="按市值占比">
            <PieChart data={mockHoldingsData} height={350} />
          </Card>
        </Col>
      </Row>

      {/* 最近交易 */}
      <Card title="最近交易" subtitle="最近5笔">
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
              {[
                { time: '15:28:32', symbol: 'AAPL', side: 'BUY', qty: 100, price: 178.52, amount: 17852 },
                { time: '14:15:08', symbol: 'MSFT', side: 'SELL', qty: 50, price: 372.15, amount: 18607.5 },
                { time: '11:42:55', symbol: 'GOOGL', side: 'BUY', qty: 30, price: 141.23, amount: 4236.9 },
              ].map((trade, i) => (
                <tr key={i} className="border-b border-dark-border hover:bg-dark-hover">
                  <td className="py-3 font-mono text-gray-400">{trade.time}</td>
                  <td className="py-3 font-medium">{trade.symbol}</td>
                  <td className={`py-3 ${trade.side === 'BUY' ? 'text-profit' : 'text-loss'}`}>
                    {trade.side}
                  </td>
                  <td className="py-3 text-right font-mono">{trade.qty}</td>
                  <td className="py-3 text-right font-mono">${trade.price}</td>
                  <td className="py-3 text-right font-mono">${trade.amount.toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  )
}
