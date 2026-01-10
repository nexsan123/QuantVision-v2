/**
 * 回放控制条
 * PRD 4.17.1 回放控制条设计
 *
 * 功能:
 * - 日期范围选择
 * - 股票选择
 * - 播放控制按钮
 * - 速度选择
 * - 进度条 (带信号标记)
 * - 当前时间显示
 */
import { useState } from 'react'
import { DatePicker, Select, Button, Slider, Tooltip } from 'antd'
import {
  PlayCircleOutlined,
  PauseCircleOutlined,
  StepForwardOutlined,
  StepBackwardOutlined,
  FastForwardOutlined,
  FastBackwardOutlined,
} from '@ant-design/icons'
import dayjs from 'dayjs'
import {
  ReplayState,
  ReplaySpeed,
  SignalMarker,
  ReplayConfig,
  REPLAY_SPEEDS,
  formatReplayTime,
} from '../../types/replay'

const { RangePicker } = DatePicker

interface ReplayControlBarProps {
  state: ReplayState | null
  signalMarkers: SignalMarker[]
  onPlay: () => void
  onPause: () => void
  onStepForward: () => void
  onStepBackward: () => void
  onSeek: (index: number) => void
  onNextSignal: () => void
  onSpeedChange: (speed: ReplaySpeed) => void
  onConfigChange: (config: Partial<ReplayConfig>) => void
}

export default function ReplayControlBar({
  state,
  signalMarkers,
  onPlay,
  onPause,
  onStepForward,
  onStepBackward,
  onSeek,
  onNextSignal,
  onSpeedChange,
  onConfigChange,
}: ReplayControlBarProps) {
  const [symbolInput, setSymbolInput] = useState(state?.config.symbol || 'NVDA')

  const isPlaying = state?.status === 'playing'

  return (
    <div className="bg-dark-card border-b border-gray-700 px-4 py-3">
      {/* 第一行: 配置 */}
      <div className="flex items-center gap-4 mb-3">
        {/* 日期范围选择 */}
        <div className="flex items-center gap-2">
          <span className="text-gray-400 text-sm">日期:</span>
          <RangePicker
            size="small"
            value={
              state?.config
                ? [dayjs(state.config.startDate), dayjs(state.config.endDate)]
                : undefined
            }
            onChange={(dates) => {
              if (dates && dates[0] && dates[1]) {
                onConfigChange({
                  startDate: dates[0].format('YYYY-MM-DD'),
                  endDate: dates[1].format('YYYY-MM-DD'),
                })
              }
            }}
            style={{ width: 240 }}
          />
        </div>

        {/* 股票选择 */}
        <div className="flex items-center gap-2">
          <span className="text-gray-400 text-sm">股票:</span>
          <Select
            size="small"
            value={symbolInput}
            onChange={(v) => {
              setSymbolInput(v)
              onConfigChange({ symbol: v })
            }}
            style={{ width: 100 }}
            options={[
              { value: 'NVDA', label: 'NVDA' },
              { value: 'TSLA', label: 'TSLA' },
              { value: 'AAPL', label: 'AAPL' },
              { value: 'MSFT', label: 'MSFT' },
              { value: 'AMD', label: 'AMD' },
              { value: 'META', label: 'META' },
            ]}
          />
        </div>

        {/* 速度选择 */}
        <div className="flex items-center gap-2">
          <span className="text-gray-400 text-sm">速度:</span>
          <Select
            size="small"
            value={state?.config.speed || '1x'}
            onChange={(v) => onSpeedChange(v as ReplaySpeed)}
            style={{ width: 100 }}
            options={REPLAY_SPEEDS.map((s) => ({
              value: s.value,
              label: s.label,
            }))}
          />
        </div>

        {/* 当前时间 */}
        <div className="ml-auto flex items-center gap-4">
          <div className="text-white font-mono text-lg">
            {state?.currentTime ? formatReplayTime(state.currentTime) : '--:--'}
          </div>
          <div className="text-gray-400 text-sm">
            {state ? `${state.currentBarIndex + 1} / ${state.totalBars}` : '0 / 0'}
          </div>
        </div>
      </div>

      {/* 第二行: 控制按钮和进度条 */}
      <div className="flex items-center gap-4">
        {/* 播放控制按钮 */}
        <div className="flex items-center gap-1">
          <Tooltip title="后退10步">
            <Button
              type="text"
              icon={<FastBackwardOutlined />}
              onClick={() => {
                for (let i = 0; i < 10; i++) onStepBackward()
              }}
              className="text-gray-400 hover:text-white"
            />
          </Tooltip>
          <Tooltip title="后退一步">
            <Button
              type="text"
              icon={<StepBackwardOutlined />}
              onClick={onStepBackward}
              className="text-gray-400 hover:text-white"
            />
          </Tooltip>
          {isPlaying ? (
            <Tooltip title="暂停">
              <Button
                type="primary"
                icon={<PauseCircleOutlined />}
                onClick={onPause}
                size="large"
                className="mx-1"
              />
            </Tooltip>
          ) : (
            <Tooltip title="播放">
              <Button
                type="primary"
                icon={<PlayCircleOutlined />}
                onClick={onPlay}
                size="large"
                className="mx-1"
              />
            </Tooltip>
          )}
          <Tooltip title="前进一步">
            <Button
              type="text"
              icon={<StepForwardOutlined />}
              onClick={onStepForward}
              className="text-gray-400 hover:text-white"
            />
          </Tooltip>
          <Tooltip title="前进10步">
            <Button
              type="text"
              icon={<FastForwardOutlined />}
              onClick={() => {
                for (let i = 0; i < 10; i++) onStepForward()
              }}
              className="text-gray-400 hover:text-white"
            />
          </Tooltip>
          <div className="w-px h-6 bg-gray-600 mx-2" />
          <Tooltip title="下一个信号">
            <Button
              type="text"
              onClick={onNextSignal}
              className="text-purple-400 hover:text-purple-300"
            >
              ⏭️ 下一信号
            </Button>
          </Tooltip>
        </div>

        {/* 进度条 */}
        <div className="flex-1 relative">
          <Slider
            value={state?.currentBarIndex || 0}
            max={state?.totalBars || 100}
            onChange={(v) => onSeek(v)}
            tooltip={{
              formatter: (v) => `Bar ${v}`,
            }}
            className="replay-slider"
          />

          {/* 信号标记 */}
          <div className="absolute top-0 left-0 right-0 h-full pointer-events-none">
            {signalMarkers.map((marker, index) => {
              const left = state
                ? (marker.index / state.totalBars) * 100
                : 0
              return (
                <div
                  key={index}
                  className="absolute top-1/2 -translate-y-1/2 cursor-pointer pointer-events-auto"
                  style={{ left: `${left}%` }}
                  onClick={() => onSeek(marker.index)}
                  title={`${marker.type === 'buy' ? '买入' : '卖出'}信号 @ ${marker.time}`}
                >
                  <span className="text-xs">
                    {marker.type === 'buy' ? '🟢' : '🔴'}
                  </span>
                </div>
              )
            })}
          </div>
        </div>
      </div>
    </div>
  )
}
