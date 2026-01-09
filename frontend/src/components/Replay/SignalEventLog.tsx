/**
 * 信号事件日志
 * PRD 4.17.1 信号事件日志
 *
 * 显示回放期间的所有信号事件
 */
import { Button, Empty } from 'antd'
import { DownloadOutlined } from '@ant-design/icons'
import {
  SignalEvent,
  getSignalIcon,
  getEventLabel,
  formatReplayTime,
} from '../../types/replay'

interface SignalEventLogProps {
  events: SignalEvent[]
  onExport: () => void
}

export default function SignalEventLog({ events, onExport }: SignalEventLogProps) {
  const getEventClass = (type: string) => {
    switch (type) {
      case 'buy_trigger':
        return 'border-l-green-500 bg-green-900/10'
      case 'sell_trigger':
        return 'border-l-red-500 bg-red-900/10'
      default:
        return 'border-l-yellow-500 bg-yellow-900/10'
    }
  }

  return (
    <div className="bg-dark-card rounded-lg overflow-hidden flex flex-col h-full">
      {/* 头部 */}
      <div className="px-4 py-3 border-b border-gray-700 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-lg">📋</span>
          <span className="text-white font-medium">信号事件日志</span>
          <span className="text-gray-500 text-sm">({events.length})</span>
        </div>
        <Button
          type="text"
          icon={<DownloadOutlined />}
          onClick={onExport}
          size="small"
          className="text-gray-400 hover:text-white"
        >
          导出
        </Button>
      </div>

      {/* 事件列表 */}
      <div className="flex-1 overflow-y-auto p-2">
        {events.length === 0 ? (
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description={<span className="text-gray-500">暂无信号事件</span>}
            className="mt-8"
          />
        ) : (
          <div className="space-y-2">
            {events.map((event) => (
              <div
                key={event.eventId}
                className={`p-3 rounded border-l-4 ${getEventClass(event.eventType)}`}
              >
                {/* 事件头 */}
                <div className="flex items-center justify-between mb-1">
                  <div className="flex items-center gap-2">
                    <span>{getSignalIcon(event.eventType)}</span>
                    <span className="text-white text-sm font-medium">
                      {getEventLabel(event.eventType)}
                    </span>
                  </div>
                  <span className="text-gray-500 text-xs">
                    {formatReplayTime(event.timestamp)}
                  </span>
                </div>

                {/* 事件详情 */}
                <div className="text-gray-400 text-sm mb-1">
                  {event.description}
                </div>

                {/* 价格信息 */}
                <div className="flex items-center gap-2 text-xs">
                  <span className="text-gray-500">{event.symbol}</span>
                  <span className="text-white font-mono">
                    @${event.price.toFixed(2)}
                  </span>
                </div>

                {/* 因子详情 (可展开) */}
                {event.factorDetails && (
                  <div className="mt-2 pt-2 border-t border-gray-700">
                    <div className="grid grid-cols-2 gap-1 text-xs">
                      {Object.entries(event.factorDetails)
                        .slice(0, 4)
                        .map(([key, value]) => (
                          <div key={key} className="flex justify-between">
                            <span className="text-gray-500">{key}:</span>
                            <span className="text-gray-300">
                              {typeof value === 'number' ? value.toFixed(2) : String(value)}
                            </span>
                          </div>
                        ))}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
