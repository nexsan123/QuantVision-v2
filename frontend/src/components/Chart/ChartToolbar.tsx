/**
 * 图表工具栏组件
 * PRD 4.16 实时交易监控界面
 */
import { Button, Tooltip } from 'antd'
import {
  SearchOutlined,
  LineChartOutlined,
  EditOutlined,
  FullscreenOutlined,
} from '@ant-design/icons'

interface ChartToolbarProps {
  symbol: string
  price: number
  change: number
  changePct: number
  interval: string
  onIntervalChange: (interval: string) => void
  onSymbolSearch: () => void
  onIndicatorClick?: () => void
  onDrawingClick?: () => void
  onFullscreenClick?: () => void
}

// 时间周期配置
const INTERVALS = [
  { value: '1', label: '1分' },
  { value: '5', label: '5分' },
  { value: '15', label: '15分' },
  { value: '60', label: '1时' },
  { value: '240', label: '4时' },
  { value: 'D', label: '日线' },
] as const

export default function ChartToolbar({
  symbol,
  price,
  change,
  changePct,
  interval,
  onIntervalChange,
  onSymbolSearch,
  onIndicatorClick,
  onDrawingClick,
  onFullscreenClick,
}: ChartToolbarProps) {
  const isPositive = change >= 0

  return (
    <div className="flex items-center justify-between px-4 py-3 bg-dark-card border-b border-gray-700">
      {/* 股票信息 */}
      <div className="flex items-center gap-4">
        <button
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-gray-800 hover:bg-gray-700 transition-colors"
          onClick={onSymbolSearch}
        >
          <span className="text-white font-semibold text-lg">{symbol}</span>
          <SearchOutlined className="text-gray-400 text-sm" />
        </button>

        <div className="flex items-center gap-3">
          <span className="text-white text-xl font-mono">${price.toFixed(2)}</span>
          <span
            className={`text-lg font-medium ${
              isPositive ? 'text-green-400' : 'text-red-400'
            }`}
          >
            {isPositive ? '+' : ''}
            {change.toFixed(2)} ({changePct.toFixed(2)}%)
          </span>
        </div>
      </div>

      {/* 时间周期 */}
      <div className="flex items-center gap-1">
        {INTERVALS.map(({ value, label }) => (
          <button
            key={value}
            className={`px-3 py-1.5 rounded text-sm font-medium transition-colors ${
              interval === value
                ? 'bg-blue-600 text-white'
                : 'text-gray-400 hover:text-white hover:bg-gray-700'
            }`}
            onClick={() => onIntervalChange(value)}
          >
            {label}
          </button>
        ))}
      </div>

      {/* 工具按钮 */}
      <div className="flex items-center gap-2">
        <Tooltip title="指标">
          <Button
            type="text"
            icon={<LineChartOutlined />}
            className="text-gray-400 hover:text-white"
            onClick={onIndicatorClick}
          />
        </Tooltip>
        <Tooltip title="画线">
          <Button
            type="text"
            icon={<EditOutlined />}
            className="text-gray-400 hover:text-white"
            onClick={onDrawingClick}
          />
        </Tooltip>
        <Tooltip title="全屏">
          <Button
            type="text"
            icon={<FullscreenOutlined />}
            className="text-gray-400 hover:text-white"
            onClick={onFullscreenClick}
          />
        </Tooltip>
      </div>
    </div>
  )
}
