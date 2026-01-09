/**
 * 盘前扫描器组件
 * PRD 4.18.0 盘前扫描器
 */
import { useState, useEffect } from 'react'
import {
  Table,
  Button,
  Checkbox,
  Select,
  Tag,
  Tooltip,
  message,
  Spin,
  Alert,
} from 'antd'
import {
  ReloadOutlined,
  RightOutlined,
  BulbOutlined,
} from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import {
  PreMarketScanResult,
  PreMarketStock,
  PreMarketScanFilter,
  DEFAULT_FILTERS,
  formatGap,
  getScoreStars,
  getScoreColorClass,
} from '../../types/preMarket'
import { intradayStorage } from '../../services/storageService'

interface PreMarketScannerProps {
  strategyId: string
  onConfirmWatchlist: (symbols: string[]) => void
  loading?: boolean
}

export default function PreMarketScanner({
  strategyId,
  onConfirmWatchlist,
  loading: externalLoading = false,
}: PreMarketScannerProps) {
  const [scanResult, setScanResult] = useState<PreMarketScanResult | null>(null)
  const [filters, setFilters] = useState<PreMarketScanFilter>(DEFAULT_FILTERS)
  const [selectedSymbols, setSelectedSymbols] = useState<Set<string>>(new Set())
  const [scanning, setScanning] = useState(false)

  // 首次加载时执行扫描并恢复已保存的选择
  useEffect(() => {
    handleScan()
    // 恢复之前保存的 watchlist
    const savedWatchlist = intradayStorage.getWatchlist()
    if (savedWatchlist.length > 0) {
      setSelectedSymbols(new Set(savedWatchlist))
    }
  }, [strategyId])

  // 执行扫描 (模拟)
  const handleScan = async () => {
    setScanning(true)
    try {
      // 模拟 API 调用
      await new Promise((resolve) => setTimeout(resolve, 1000))

      // 模拟数据
      const mockResult: PreMarketScanResult = {
        scan_time: new Date().toISOString(),
        strategy_id: strategyId,
        strategy_name: '动量突破策略',
        filters_applied: filters,
        total_matched: 8,
        stocks: [
          {
            symbol: 'NVDA',
            name: 'NVIDIA Corp.',
            gap: 0.042,
            gap_direction: 'up',
            premarket_price: 525.0,
            premarket_volume: 2500000,
            premarket_volume_ratio: 3.2,
            prev_close: 504.0,
            prev_volume: 15000000,
            volatility: 0.045,
            avg_daily_volume: 15000000,
            avg_daily_value: 7500000000,
            has_news: true,
            news_headline: 'NVIDIA 宣布新一代AI芯片',
            is_earnings_day: false,
            score: 85,
            score_breakdown: { gap: 42, volume: 32, volatility: 22.5, news: 10, weights: { gap: 0.3, volume: 0.3, volatility: 0.2, news: 1 } },
          },
          {
            symbol: 'TSLA',
            name: 'Tesla Inc.',
            gap: 0.035,
            gap_direction: 'up',
            premarket_price: 252.0,
            premarket_volume: 3200000,
            premarket_volume_ratio: 2.8,
            prev_close: 243.5,
            prev_volume: 25000000,
            volatility: 0.052,
            avg_daily_volume: 25000000,
            avg_daily_value: 6000000000,
            has_news: true,
            news_headline: 'Tesla 交付量超预期',
            is_earnings_day: false,
            score: 78,
            score_breakdown: { gap: 35, volume: 28, volatility: 26, news: 10, weights: { gap: 0.3, volume: 0.3, volatility: 0.2, news: 1 } },
          },
          {
            symbol: 'AMD',
            name: 'Advanced Micro Devices',
            gap: -0.028,
            gap_direction: 'down',
            premarket_price: 142.0,
            premarket_volume: 1800000,
            premarket_volume_ratio: 2.5,
            prev_close: 146.0,
            prev_volume: 18000000,
            volatility: 0.038,
            avg_daily_volume: 18000000,
            avg_daily_value: 2600000000,
            has_news: false,
            is_earnings_day: false,
            score: 62,
            score_breakdown: { gap: 28, volume: 25, volatility: 19, news: 0, weights: { gap: 0.3, volume: 0.3, volatility: 0.2, news: 1 } },
          },
          {
            symbol: 'META',
            name: 'Meta Platforms Inc.',
            gap: 0.025,
            gap_direction: 'up',
            premarket_price: 512.0,
            premarket_volume: 1200000,
            premarket_volume_ratio: 2.2,
            prev_close: 499.5,
            prev_volume: 12000000,
            volatility: 0.032,
            avg_daily_volume: 12000000,
            avg_daily_value: 6000000000,
            has_news: false,
            is_earnings_day: false,
            score: 55,
            score_breakdown: { gap: 25, volume: 22, volatility: 16, news: 0, weights: { gap: 0.3, volume: 0.3, volatility: 0.2, news: 1 } },
          },
        ],
        ai_suggestion: 'NVDA, TSLA 今日有重大新闻催化，建议重点关注；NVDA 跳空幅度较大，注意风险控制',
      }

      setScanResult(mockResult)

      // 默认选中高评分股票
      const topSymbols = mockResult.stocks
        .filter((s) => s.score >= 70)
        .map((s) => s.symbol)
      setSelectedSymbols(new Set(topSymbols))
    } finally {
      setScanning(false)
    }
  }

  // 切换选中
  const toggleSymbol = (symbol: string) => {
    const newSet = new Set(selectedSymbols)
    if (newSet.has(symbol)) {
      newSet.delete(symbol)
    } else {
      newSet.add(symbol)
    }
    setSelectedSymbols(newSet)
  }

  // 全选/取消全选
  const toggleAll = () => {
    if (selectedSymbols.size === scanResult?.stocks.length) {
      setSelectedSymbols(new Set())
    } else {
      setSelectedSymbols(new Set(scanResult?.stocks.map((s) => s.symbol)))
    }
  }

  // 确认监控列表
  const handleConfirm = () => {
    if (selectedSymbols.size === 0) {
      message.warning('请至少选择一只股票')
      return
    }
    const symbols = Array.from(selectedSymbols)
    // 保存到 localStorage
    intradayStorage.saveWatchlist(symbols)
    onConfirmWatchlist(symbols)
    message.success(`监控列表已保存 (${symbols.length}只)`)
  }

  // 表格列定义
  const columns: ColumnsType<PreMarketStock> = [
    {
      title: (
        <Checkbox
          checked={
            !!(scanResult &&
            selectedSymbols.size === scanResult.stocks.length &&
            scanResult.stocks.length > 0)
          }
          indeterminate={
            selectedSymbols.size > 0 &&
            selectedSymbols.size < (scanResult?.stocks.length || 0)
          }
          onChange={toggleAll}
        />
      ),
      width: 50,
      render: (_, record) => (
        <Checkbox
          checked={selectedSymbols.has(record.symbol)}
          onChange={() => toggleSymbol(record.symbol)}
        />
      ),
    },
    {
      title: '股票',
      dataIndex: 'symbol',
      width: 120,
      render: (symbol, record) => (
        <div>
          <div className="text-white font-medium">{symbol}</div>
          <div className="text-gray-500 text-xs truncate" style={{ maxWidth: 100 }}>
            {record.name}
          </div>
        </div>
      ),
    },
    {
      title: 'Gap',
      dataIndex: 'gap',
      width: 80,
      render: (gap, record) => (
        <span
          className={`font-medium ${
            record.gap_direction === 'up' ? 'text-green-400' : 'text-red-400'
          }`}
        >
          {formatGap(gap)}
        </span>
      ),
    },
    {
      title: '盘前量',
      dataIndex: 'premarket_volume_ratio',
      width: 80,
      render: (ratio) => <span>{(ratio * 100).toFixed(0)}%</span>,
    },
    {
      title: '波动率',
      dataIndex: 'volatility',
      width: 80,
      render: (vol) => <span>{(vol * 100).toFixed(1)}%</span>,
    },
    {
      title: '流动性',
      dataIndex: 'avg_daily_value',
      width: 80,
      render: (value) => <span>${(value / 1000000).toFixed(0)}M</span>,
    },
    {
      title: '催化',
      width: 70,
      render: (_, record) => (
        <div className="flex gap-1">
          {record.has_news && (
            <Tooltip title={record.news_headline}>
              <span className="cursor-help">📰</span>
            </Tooltip>
          )}
          {record.is_earnings_day && (
            <Tooltip title="财报日">
              <span>📊</span>
            </Tooltip>
          )}
        </div>
      ),
    },
    {
      title: '评分',
      dataIndex: 'score',
      width: 100,
      render: (score) => (
        <div className={getScoreColorClass(score)}>
          <span className="mr-1">{getScoreStars(score)}</span>
          <span>{score}</span>
        </div>
      ),
    },
  ]

  return (
    <div className="bg-dark-card rounded-lg overflow-hidden">
      {/* 头部 */}
      <div className="px-6 py-4 border-b border-gray-700 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-2xl">⏰</span>
          <div>
            <h2 className="text-lg font-semibold text-white">盘前扫描器</h2>
            <p className="text-gray-500 text-sm">
              {new Date().toLocaleTimeString()} EST
            </p>
          </div>
        </div>
        <Button
          icon={<ReloadOutlined spin={scanning} />}
          onClick={handleScan}
          loading={scanning}
        >
          刷新
        </Button>
      </div>

      {/* 筛选条件 */}
      <div className="px-6 py-4 border-b border-gray-700 bg-gray-800/30">
        <div className="flex flex-wrap gap-4 items-center">
          <div className="flex items-center gap-2">
            <span className="text-gray-400 text-sm">Gap &gt;</span>
            <Select
              value={filters.min_gap * 100}
              onChange={(v) => setFilters({ ...filters, min_gap: v / 100 })}
              style={{ width: 80 }}
              size="small"
              options={[
                { value: 1, label: '1%' },
                { value: 2, label: '2%' },
                { value: 3, label: '3%' },
                { value: 5, label: '5%' },
              ]}
            />
          </div>

          <div className="flex items-center gap-2">
            <span className="text-gray-400 text-sm">盘前量 &gt;</span>
            <Select
              value={filters.min_premarket_volume * 100}
              onChange={(v) =>
                setFilters({ ...filters, min_premarket_volume: v / 100 })
              }
              style={{ width: 90 }}
              size="small"
              options={[
                { value: 100, label: '100%' },
                { value: 200, label: '200%' },
                { value: 300, label: '300%' },
                { value: 500, label: '500%' },
              ]}
            />
          </div>

          <Checkbox
            checked={filters.has_news === true}
            onChange={(e) =>
              setFilters({
                ...filters,
                has_news: e.target.checked ? true : null,
              })
            }
          >
            <span className="text-gray-400">有新闻</span>
          </Checkbox>

          <Checkbox
            checked={filters.is_earnings_day === true}
            onChange={(e) =>
              setFilters({
                ...filters,
                is_earnings_day: e.target.checked ? true : null,
              })
            }
          >
            <span className="text-gray-400">财报日</span>
          </Checkbox>

          <Button
            size="small"
            onClick={() => setFilters(DEFAULT_FILTERS)}
          >
            重置
          </Button>

          {scanResult && (
            <Tag color="blue">符合条件: {scanResult.total_matched} 只</Tag>
          )}
        </div>
      </div>

      {/* 股票列表 */}
      <div className="px-6 py-4">
        <Spin spinning={scanning}>
          <Table
            columns={columns}
            dataSource={scanResult?.stocks || []}
            rowKey="symbol"
            size="small"
            pagination={false}
            rowClassName={(record) =>
              selectedSymbols.has(record.symbol) ? 'bg-blue-900/20' : ''
            }
          />
        </Spin>

        {/* AI 建议 */}
        {scanResult?.ai_suggestion && (
          <Alert
            message={
              <div className="flex items-center gap-2">
                <BulbOutlined className="text-yellow-400" />
                <span>{scanResult.ai_suggestion}</span>
              </div>
            }
            type="info"
            className="mt-4"
            style={{ background: 'rgba(59, 130, 246, 0.1)', border: 'none' }}
          />
        )}
      </div>

      {/* 底部操作 */}
      <div className="px-6 py-4 border-t border-gray-700 flex items-center justify-between">
        <div className="text-gray-400">
          已选择: <span className="text-white">{selectedSymbols.size}</span> 只
          <span className="text-gray-500 ml-2">(建议: 5-15只，不超过20只)</span>
        </div>

        <Button
          type="primary"
          size="large"
          icon={<RightOutlined />}
          onClick={handleConfirm}
          disabled={selectedSymbols.size === 0}
          loading={externalLoading}
        >
          确认监控列表，进入交易界面
        </Button>
      </div>
    </div>
  )
}
