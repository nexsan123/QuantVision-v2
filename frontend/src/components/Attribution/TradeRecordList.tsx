/**
 * 交易记录列表组件
 * PRD 4.5 交易归因系统
 */
import { Table, Tag, Tooltip, Button } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { EyeOutlined } from '@ant-design/icons'
import {
  TradeRecord,
  TRADE_OUTCOME_CONFIG,
  TRADE_SIDE_CONFIG,
  formatMoney,
  formatPercent,
  formatDateTime,
} from '../../types/tradeAttribution'

interface TradeRecordListProps {
  trades: TradeRecord[]
  loading?: boolean
  onViewDetail?: (trade: TradeRecord) => void
}

export default function TradeRecordList({
  trades,
  loading = false,
  onViewDetail,
}: TradeRecordListProps) {
  const columns: ColumnsType<TradeRecord> = [
    {
      title: '股票',
      dataIndex: 'symbol',
      key: 'symbol',
      width: 100,
      render: (symbol: string) => (
        <span className="font-mono font-semibold text-white">{symbol}</span>
      ),
    },
    {
      title: '方向',
      dataIndex: 'side',
      key: 'side',
      width: 80,
      render: (side: string) => {
        const config = TRADE_SIDE_CONFIG[side as keyof typeof TRADE_SIDE_CONFIG]
        return (
          <Tag
            style={{
              backgroundColor: `${config.color}20`,
              color: config.color,
              border: 'none',
            }}
          >
            {config.label}
          </Tag>
        )
      },
    },
    {
      title: '数量',
      dataIndex: 'quantity',
      key: 'quantity',
      width: 80,
      render: (qty: number) => (
        <span className="font-mono text-gray-300">{qty}</span>
      ),
    },
    {
      title: '入场价',
      dataIndex: 'entry_price',
      key: 'entry_price',
      width: 100,
      render: (price: number) => (
        <span className="font-mono text-gray-300">${price.toFixed(2)}</span>
      ),
    },
    {
      title: '出场价',
      dataIndex: 'exit_price',
      key: 'exit_price',
      width: 100,
      render: (price: number | undefined) => (
        <span className="font-mono text-gray-300">
          {price ? `$${price.toFixed(2)}` : '-'}
        </span>
      ),
    },
    {
      title: '盈亏',
      dataIndex: 'pnl',
      key: 'pnl',
      width: 120,
      render: (pnl: number | undefined, record) => {
        if (pnl === undefined) return <span className="text-gray-500">-</span>
        return (
          <div>
            <span
              className={`font-mono font-semibold ${
                pnl >= 0 ? 'text-green-400' : 'text-red-400'
              }`}
            >
              {formatMoney(pnl)}
            </span>
            {record.pnl_pct !== undefined && (
              <span
                className={`text-xs ml-1 ${
                  record.pnl_pct >= 0 ? 'text-green-400' : 'text-red-400'
                }`}
              >
                ({formatPercent(record.pnl_pct, 1)})
              </span>
            )}
          </div>
        )
      },
    },
    {
      title: '结果',
      dataIndex: 'outcome',
      key: 'outcome',
      width: 80,
      render: (outcome: string) => {
        const config = TRADE_OUTCOME_CONFIG[outcome as keyof typeof TRADE_OUTCOME_CONFIG]
        return (
          <Tag
            style={{
              backgroundColor: `${config.color}20`,
              color: config.color,
              border: 'none',
            }}
          >
            {config.label}
          </Tag>
        )
      },
    },
    {
      title: '持仓天数',
      dataIndex: 'hold_days',
      key: 'hold_days',
      width: 90,
      render: (days: number | undefined) => (
        <span className="text-gray-400">{days ? `${days}天` : '-'}</span>
      ),
    },
    {
      title: '因子快照',
      key: 'factors',
      width: 150,
      render: (_, record) => (
        <div className="flex flex-wrap gap-1">
          {record.factor_snapshot.slice(0, 2).map((f, i) => (
            <Tooltip
              key={i}
              title={`${f.factor_name}: ${f.factor_value.toFixed(3)} (贡献: ${(f.signal_contribution * 100).toFixed(0)}%)`}
            >
              <Tag color="blue" className="text-xs">
                {f.factor_name.slice(0, 4)}
              </Tag>
            </Tooltip>
          ))}
          {record.factor_snapshot.length > 2 && (
            <Tag className="text-xs">+{record.factor_snapshot.length - 2}</Tag>
          )}
        </div>
      ),
    },
    {
      title: '入场时间',
      dataIndex: 'entry_time',
      key: 'entry_time',
      width: 120,
      render: (time: string) => (
        <span className="text-gray-400 text-sm">{formatDateTime(time)}</span>
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 80,
      fixed: 'right',
      render: (_, record) => (
        <Button
          type="text"
          size="small"
          icon={<EyeOutlined />}
          onClick={() => onViewDetail?.(record)}
          className="text-gray-400 hover:text-blue-400"
        >
          详情
        </Button>
      ),
    },
  ]

  return (
    <Table
      columns={columns}
      dataSource={trades}
      rowKey="trade_id"
      loading={loading}
      pagination={{
        pageSize: 10,
        showSizeChanger: true,
        showQuickJumper: true,
        showTotal: (total) => `共 ${total} 条记录`,
      }}
      scroll={{ x: 1200 }}
      className="trade-record-table"
      style={{
        backgroundColor: 'transparent',
      }}
    />
  )
}
