/**
 * 日内交易记录组件
 * PRD 4.18.1 日内交易专用视图
 */
import { Table, Tag, Empty } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { IntradayTrade } from '../../types/preMarket'

interface IntradayTradeLogProps {
  trades: IntradayTrade[]
  loading?: boolean
}

export default function IntradayTradeLog({
  trades,
  loading = false,
}: IntradayTradeLogProps) {
  // 计算汇总数据
  const summary = trades.reduce(
    (acc, trade) => {
      if (!trade.is_open && trade.pnl !== undefined) {
        acc.totalPnl += trade.pnl
        acc.closedTrades += 1
        if (trade.pnl > 0) acc.winTrades += 1
      }
      if (trade.is_open) acc.openTrades += 1
      return acc
    },
    { totalPnl: 0, closedTrades: 0, winTrades: 0, openTrades: 0 }
  )

  const winRate =
    summary.closedTrades > 0
      ? ((summary.winTrades / summary.closedTrades) * 100).toFixed(0)
      : '0'

  const columns: ColumnsType<IntradayTrade> = [
    {
      title: '时间',
      dataIndex: 'time',
      width: 80,
      render: (time) => (
        <span className="text-gray-400 text-xs font-mono">
          {new Date(time).toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit',
          })}
        </span>
      ),
    },
    {
      title: '股票',
      dataIndex: 'symbol',
      width: 70,
      render: (symbol) => <span className="text-white font-medium">{symbol}</span>,
    },
    {
      title: '方向',
      dataIndex: 'side',
      width: 60,
      render: (side) => (
        <Tag color={side === 'buy' ? 'green' : 'red'} className="m-0">
          {side === 'buy' ? '买入' : '卖出'}
        </Tag>
      ),
    },
    {
      title: '数量',
      dataIndex: 'quantity',
      width: 60,
      render: (qty) => <span className="text-gray-300">{qty}</span>,
    },
    {
      title: '价格',
      dataIndex: 'price',
      width: 80,
      render: (price) => (
        <span className="text-white font-mono">${price.toFixed(2)}</span>
      ),
    },
    {
      title: '止损/止盈',
      width: 100,
      render: (_, record) => (
        <div className="text-xs">
          {record.stop_loss && (
            <div className="text-red-400">SL: ${record.stop_loss.toFixed(2)}</div>
          )}
          {record.take_profit && (
            <div className="text-green-400">TP: ${record.take_profit.toFixed(2)}</div>
          )}
        </div>
      ),
    },
    {
      title: '状态',
      width: 70,
      render: (_, record) => (
        <Tag color={record.is_open ? 'blue' : 'default'}>
          {record.is_open ? '持仓中' : '已平仓'}
        </Tag>
      ),
    },
    {
      title: '盈亏',
      dataIndex: 'pnl',
      width: 80,
      render: (pnl, record) =>
        !record.is_open && pnl !== undefined ? (
          <span
            className={`font-medium ${pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}
          >
            {pnl >= 0 ? '+' : ''}${pnl.toFixed(2)}
          </span>
        ) : (
          <span className="text-gray-500">-</span>
        ),
    },
  ]

  return (
    <div className="bg-dark-card rounded-lg overflow-hidden h-full flex flex-col">
      {/* 头部 */}
      <div className="px-4 py-3 border-b border-gray-700 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-lg">📋</span>
          <span className="text-white font-medium">今日交易</span>
        </div>
        <div className="flex items-center gap-4 text-sm">
          <span className="text-gray-400">
            持仓: <span className="text-blue-400">{summary.openTrades}</span>
          </span>
          <span className="text-gray-400">
            胜率: <span className="text-yellow-400">{winRate}%</span>
          </span>
        </div>
      </div>

      {/* 汇总栏 */}
      <div className="px-4 py-2 border-b border-gray-700 bg-gray-800/30">
        <div className="flex items-center justify-between">
          <div className="text-sm">
            <span className="text-gray-400">已平仓: </span>
            <span className="text-white">{summary.closedTrades}笔</span>
          </div>
          <div className="text-sm">
            <span className="text-gray-400">今日盈亏: </span>
            <span
              className={`font-medium ${
                summary.totalPnl >= 0 ? 'text-green-400' : 'text-red-400'
              }`}
            >
              {summary.totalPnl >= 0 ? '+' : ''}${summary.totalPnl.toFixed(2)}
            </span>
          </div>
        </div>
      </div>

      {/* 交易列表 */}
      <div className="flex-1 overflow-auto p-2">
        {trades.length === 0 ? (
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description={<span className="text-gray-500">今日暂无交易</span>}
            className="mt-8"
          />
        ) : (
          <Table
            columns={columns}
            dataSource={trades}
            rowKey={(record, index) => `${record.time}-${record.symbol}-${index}`}
            size="small"
            pagination={false}
            loading={loading}
            scroll={{ y: 300 }}
          />
        )}
      </div>

      {/* PDT 警告 */}
      <div className="px-4 py-2 border-t border-gray-700 bg-yellow-900/20">
        <div className="flex items-center gap-2 text-xs text-yellow-400">
          <span>⚠️</span>
          <span>PDT规则: 5个交易日内日内交易不超过3次 (账户&lt;$25K)</span>
        </div>
      </div>
    </div>
  )
}
