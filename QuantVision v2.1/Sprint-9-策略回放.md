# Sprint 9: 策略回放功能 (7天)

> **文档版本**: 1.0  
> **预计时长**: 7天  
> **前置依赖**: Sprint 7 完成 (TradingView集成)  
> **PRD参考**: 4.17 策略回放功能 (v1.6第1488-1669行)  
> **交付物**: 历史回放界面、因子面板、信号日志、回放洞察

---

## 目标

实现策略回放功能，让用户回放历史行情，观察策略在过去的信号和执行情况。

**使用场景**:
- 初学者理解策略逻辑
- 验证策略在特定事件中的表现
- Debug策略问题

---

## Part A: 后端数据服务 (3天)

### Task 9.1: 回放数据Schema

**文件**: `backend/app/schemas/replay.py`

```python
"""
策略回放 Pydantic Schema
PRD 4.17
"""

from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class ReplaySpeed(str, Enum):
    """回放速度"""
    HALF = "0.5x"
    NORMAL = "1x"
    DOUBLE = "2x"
    FAST = "5x"


class ReplayStatus(str, Enum):
    """回放状态"""
    IDLE = "idle"        # 空闲
    PLAYING = "playing"  # 播放中
    PAUSED = "paused"    # 已暂停


# ============ 回放配置 ============

class ReplayConfig(BaseModel):
    """回放配置"""
    strategy_id: str
    symbol: str
    start_date: date
    end_date: date
    speed: ReplaySpeed = ReplaySpeed.NORMAL
    

class ReplayState(BaseModel):
    """回放状态"""
    config: ReplayConfig
    status: ReplayStatus = ReplayStatus.IDLE
    current_time: datetime
    current_bar_index: int = 0
    total_bars: int = 0
    
    # 模拟持仓
    position_quantity: int = 0
    position_avg_cost: Decimal = Decimal("0")
    cash: Decimal = Decimal("100000")
    
    # 回放统计
    total_signals: int = 0
    executed_signals: int = 0
    total_return_pct: float = 0
    benchmark_return_pct: float = 0


# ============ 历史数据 ============

class HistoricalBar(BaseModel):
    """历史K线"""
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int


class FactorSnapshot(BaseModel):
    """因子快照"""
    timestamp: datetime
    factor_values: dict[str, float]
    thresholds: dict[str, dict]  # {factor_name: {value, direction, passed}}
    overall_signal: str  # buy/sell/hold
    conditions_met: int
    conditions_total: int


class SignalEvent(BaseModel):
    """信号事件"""
    event_id: str
    timestamp: datetime
    event_type: str  # buy_trigger, sell_trigger, condition_check
    symbol: str
    price: Decimal
    description: str
    factor_details: Optional[dict] = None


# ============ 回放响应 ============

class ReplayInitResponse(BaseModel):
    """回放初始化响应"""
    state: ReplayState
    total_bars: int
    signal_markers: list[dict]  # 进度条上的信号标记位置


class ReplayTickResponse(BaseModel):
    """回放Tick响应"""
    state: ReplayState
    bar: HistoricalBar
    factor_snapshot: FactorSnapshot
    events: list[SignalEvent]  # 本Tick触发的事件


class ReplayInsight(BaseModel):
    """回放洞察"""
    total_signals: int
    execution_rate: float
    win_rate: float
    alpha: float
    
    # AI洞察
    ai_insights: list[str]
    
    # 收益对比
    strategy_return: float
    benchmark_return: float


class ReplayExport(BaseModel):
    """回放导出"""
    events: list[SignalEvent]
    summary: ReplayInsight
```

**验收标准**:
- [ ] 回放状态管理完整
- [ ] 历史数据结构清晰
- [ ] 信号事件定义完整

---

### Task 9.2: 历史数据服务

**文件**: `backend/app/services/historical_data_service.py`

```python
"""
历史数据服务
提供回放所需的K线和因子数据
"""

from datetime import date, datetime
from typing import AsyncGenerator
from app.schemas.replay import HistoricalBar, FactorSnapshot


class HistoricalDataService:
    """历史数据服务"""
    
    async def get_historical_bars(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
        interval: str = "1m"  # 1m, 5m, 15m, 1H, 1D
    ) -> list[HistoricalBar]:
        """
        获取历史K线数据
        
        数据来源: 本地数据库 / Polygon.io历史API
        存储: ~50GB/年 (1分钟级别)
        """
        pass
    
    async def get_factor_snapshots(
        self,
        strategy_id: str,
        symbol: str,
        start_date: date,
        end_date: date
    ) -> dict[datetime, FactorSnapshot]:
        """
        获取历史因子快照
        
        按日存储的因子值，用于回放时实时计算
        """
        pass
    
    async def stream_bars(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
        speed: float = 1.0
    ) -> AsyncGenerator[HistoricalBar, None]:
        """
        流式返回K线 (用于实时回放)
        """
        pass
```

**验收标准**:
- [ ] K线数据获取正常
- [ ] 因子快照加载正常
- [ ] 流式传输稳定

---

### Task 9.3: 回放引擎服务

**文件**: `backend/app/services/replay_engine_service.py`

```python
"""
回放引擎服务
控制回放流程、计算信号、生成事件
"""

from datetime import datetime
from app.schemas.replay import (
    ReplayConfig, ReplayState, ReplayTickResponse,
    SignalEvent, FactorSnapshot
)


class ReplayEngineService:
    """回放引擎"""
    
    def __init__(self):
        self._sessions: dict[str, ReplayState] = {}
    
    async def init_replay(
        self,
        user_id: str,
        config: ReplayConfig
    ) -> ReplayState:
        """初始化回放会话"""
        pass
    
    async def play(self, session_id: str) -> None:
        """开始/继续播放"""
        pass
    
    async def pause(self, session_id: str) -> None:
        """暂停"""
        pass
    
    async def step_forward(self, session_id: str) -> ReplayTickResponse:
        """前进一步"""
        pass
    
    async def step_backward(self, session_id: str) -> ReplayTickResponse:
        """后退一步"""
        pass
    
    async def seek_to_time(
        self,
        session_id: str,
        target_time: datetime
    ) -> ReplayTickResponse:
        """跳转到指定时间"""
        pass
    
    async def seek_to_next_signal(self, session_id: str) -> ReplayTickResponse:
        """跳转到下一个信号"""
        pass
    
    async def set_speed(self, session_id: str, speed: str) -> None:
        """设置回放速度"""
        pass
    
    def _calculate_factor_snapshot(
        self,
        strategy_id: str,
        bar: dict,
        historical_data: list
    ) -> FactorSnapshot:
        """
        实时计算因子值
        
        PRD 4.17: 因子值实时计算显示
        """
        pass
    
    def _check_signal(
        self,
        snapshot: FactorSnapshot,
        state: ReplayState
    ) -> list[SignalEvent]:
        """
        检查是否触发信号
        
        返回本Tick产生的信号事件
        """
        pass
    
    def _simulate_execution(
        self,
        state: ReplayState,
        event: SignalEvent
    ) -> None:
        """
        模拟执行交易
        
        更新模拟持仓和现金
        """
        pass
```

**验收标准**:
- [ ] 回放控制正常 (播放/暂停/快进/后退)
- [ ] 因子实时计算正确
- [ ] 信号触发检测正确
- [ ] 模拟持仓跟踪正确

---

### Task 9.4: 回放API

**文件**: `backend/app/api/v1/replay.py`

```python
"""
策略回放API
PRD 4.17
"""

from fastapi import APIRouter, WebSocket
from app.schemas.replay import *

router = APIRouter(prefix="/replay", tags=["策略回放"])


@router.post("/init")
async def init_replay(config: ReplayConfig) -> ReplayInitResponse:
    """
    初始化回放会话
    
    1. 加载历史数据
    2. 预计算信号标记位置 (用于进度条)
    3. 返回初始状态
    """
    pass


@router.post("/{session_id}/play")
async def play_replay(session_id: str) -> ReplayState:
    """开始/继续播放"""
    pass


@router.post("/{session_id}/pause")
async def pause_replay(session_id: str) -> ReplayState:
    """暂停播放"""
    pass


@router.post("/{session_id}/step-forward")
async def step_forward(session_id: str) -> ReplayTickResponse:
    """前进一步"""
    pass


@router.post("/{session_id}/step-backward")
async def step_backward(session_id: str) -> ReplayTickResponse:
    """后退一步"""
    pass


@router.post("/{session_id}/seek")
async def seek_to_time(session_id: str, target_time: str) -> ReplayTickResponse:
    """跳转到指定时间"""
    pass


@router.post("/{session_id}/next-signal")
async def seek_to_next_signal(session_id: str) -> ReplayTickResponse:
    """跳转到下一个信号"""
    pass


@router.put("/{session_id}/speed")
async def set_speed(session_id: str, speed: ReplaySpeed) -> ReplayState:
    """设置回放速度 (0.5x/1x/2x/5x)"""
    pass


@router.get("/{session_id}/insight")
async def get_replay_insight(session_id: str) -> ReplayInsight:
    """获取回放洞察"""
    pass


@router.get("/{session_id}/export")
async def export_replay(session_id: str) -> ReplayExport:
    """导出回放记录"""
    pass


@router.websocket("/{session_id}/stream")
async def replay_stream(websocket: WebSocket, session_id: str):
    """
    WebSocket实时回放流
    
    播放时持续推送:
    - 当前K线数据
    - 因子快照
    - 信号事件
    """
    pass
```

**API端点汇总**:
```
POST /api/v1/replay/init                  - 初始化回放
POST /api/v1/replay/{id}/play            - 开始播放
POST /api/v1/replay/{id}/pause           - 暂停
POST /api/v1/replay/{id}/step-forward    - 前进一步
POST /api/v1/replay/{id}/step-backward   - 后退一步
POST /api/v1/replay/{id}/seek            - 跳转时间
POST /api/v1/replay/{id}/next-signal     - 下一信号
PUT  /api/v1/replay/{id}/speed           - 设置速度
GET  /api/v1/replay/{id}/insight         - 获取洞察
GET  /api/v1/replay/{id}/export          - 导出记录
WS   /api/v1/replay/{id}/stream          - 实时流
```

**验收标准**:
- [ ] 所有端点可调用
- [ ] WebSocket连接稳定
- [ ] 错误处理完整

---

## Part B: 前端回放界面 (3天)

### Task 9.5: 回放类型定义

**文件**: `frontend/src/types/replay.ts`

```typescript
/**
 * 策略回放类型定义
 * PRD 4.17
 */

export type ReplaySpeed = '0.5x' | '1x' | '2x' | '5x';
export type ReplayStatus = 'idle' | 'playing' | 'paused';

export interface ReplayConfig {
  strategyId: string;
  symbol: string;
  startDate: string;
  endDate: string;
  speed: ReplaySpeed;
}

export interface ReplayState {
  config: ReplayConfig;
  status: ReplayStatus;
  currentTime: string;
  currentBarIndex: number;
  totalBars: number;
  
  // 模拟持仓
  positionQuantity: number;
  positionAvgCost: number;
  cash: number;
  
  // 统计
  totalSignals: number;
  executedSignals: number;
  totalReturnPct: number;
  benchmarkReturnPct: number;
}

export interface HistoricalBar {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface FactorSnapshot {
  timestamp: string;
  factorValues: Record<string, number>;
  thresholds: Record<string, {
    value: number;
    direction: 'above' | 'below';
    passed: boolean;
  }>;
  overallSignal: 'buy' | 'sell' | 'hold';
  conditionsMet: number;
  conditionsTotal: number;
}

export interface SignalEvent {
  eventId: string;
  timestamp: string;
  eventType: 'buy_trigger' | 'sell_trigger' | 'condition_check';
  symbol: string;
  price: number;
  description: string;
  factorDetails?: Record<string, any>;
}

export interface ReplayInsight {
  totalSignals: number;
  executionRate: number;
  winRate: number;
  alpha: number;
  aiInsights: string[];
  strategyReturn: number;
  benchmarkReturn: number;
}

// 颜色配置
export const REPLAY_COLORS = {
  // K线区域
  replayedBars: 'normal',      // 已回放 - 正常颜色
  currentBar: '#8b5cf6',       // 当前 - 紫色高亮
  futureBars: 'rgba(128,128,128,0.3)', // 未来 - 灰色半透明
  positionLine: '#8b5cf6',     // 回放位置线 - 紫色虚线
  
  // 信号标记
  buySignal: '#22c55e',        // 买入 - 绿色
  sellSignal: '#ef4444',       // 卖出 - 红色
  
  // 因子状态
  factorPassed: '#22c55e',     // 满足 - 绿色
  factorFailed: '#ef4444',     // 不满足 - 红色
};
```

**验收标准**:
- [ ] 类型定义与后端一致
- [ ] 颜色配置完整

---

### Task 9.6: 回放控制条组件

**文件**: `frontend/src/components/Replay/ReplayControlBar.tsx`

```tsx
/**
 * 回放控制条
 * PRD 4.17.1 回放控制条设计 (第1572-1592行)
 * 
 * 功能:
 * - 日期范围选择
 * - 股票选择
 * - 播放控制按钮
 * - 速度选择
 * - 进度条 (带信号标记)
 * - 当前时间显示
 */

import React, { useState } from 'react';

interface ReplayControlBarProps {
  state: ReplayState;
  signalMarkers: { time: string; type: 'buy' | 'sell' }[];
  onPlay: () => void;
  onPause: () => void;
  onStepForward: () => void;
  onStepBackward: () => void;
  onSeek: (time: string) => void;
  onNextSignal: () => void;
  onSpeedChange: (speed: ReplaySpeed) => void;
  onConfigChange: (config: Partial<ReplayConfig>) => void;
}

export const ReplayControlBar: React.FC<ReplayControlBarProps> = ({
  state,
  signalMarkers,
  ...handlers
}) => {
  return (
    <div className="replay-control-bar">
      {/* 日期范围和股票选择 */}
      <div className="config-section">
        <DateRangePicker
          startDate={state.config.startDate}
          endDate={state.config.endDate}
          onChange={(start, end) => handlers.onConfigChange({ startDate: start, endDate: end })}
        />
        <SymbolSelector
          value={state.config.symbol}
          onChange={(symbol) => handlers.onConfigChange({ symbol })}
        />
      </div>
      
      {/* 播放控制按钮 */}
      <div className="control-buttons">
        <button onClick={handlers.onStepBackward}>⏮️</button>
        <button onClick={handlers.onStepBackward}>⏪</button>
        {state.status === 'playing' ? (
          <button onClick={handlers.onPause}>⏸️</button>
        ) : (
          <button onClick={handlers.onPlay}>▶️</button>
        )}
        <button onClick={handlers.onStepForward}>⏩</button>
        <button onClick={handlers.onNextSignal}>⏭️ 下一信号</button>
      </div>
      
      {/* 速度选择 */}
      <select
        value={state.config.speed}
        onChange={(e) => handlers.onSpeedChange(e.target.value as ReplaySpeed)}
      >
        <option value="0.5x">0.5x</option>
        <option value="1x">1x</option>
        <option value="2x">2x</option>
        <option value="5x">5x</option>
      </select>
      
      {/* 当前时间 */}
      <div className="current-time">
        {formatDateTime(state.currentTime)}
      </div>
      
      {/* 进度条 */}
      <ReplayProgressBar
        currentIndex={state.currentBarIndex}
        totalBars={state.totalBars}
        signalMarkers={signalMarkers}
        onSeek={handlers.onSeek}
      />
    </div>
  );
};


/**
 * 进度条组件
 * 带有信号标记点
 */
const ReplayProgressBar: React.FC<{
  currentIndex: number;
  totalBars: number;
  signalMarkers: { time: string; type: 'buy' | 'sell' }[];
  onSeek: (time: string) => void;
}> = ({ currentIndex, totalBars, signalMarkers, onSeek }) => {
  const progress = (currentIndex / totalBars) * 100;
  
  return (
    <div className="progress-bar-container">
      {/* 进度条 */}
      <div className="progress-bar">
        <div className="progress-fill" style={{ width: `${progress}%` }} />
        <div className="current-indicator" style={{ left: `${progress}%` }} />
      </div>
      
      {/* 信号标记 */}
      {signalMarkers.map((marker, index) => (
        <div
          key={index}
          className={`signal-marker ${marker.type}`}
          style={{ left: `${(marker.index / totalBars) * 100}%` }}
          onClick={() => onSeek(marker.time)}
        >
          {marker.type === 'buy' ? '🟢' : '🔴'}
        </div>
      ))}
    </div>
  );
};
```

**验收标准**:
- [ ] 日期选择正常
- [ ] 播放控制按钮可用
- [ ] 速度切换正常
- [ ] 进度条信号标记可点击

---

### Task 9.7: 因子值面板组件

**文件**: `frontend/src/components/Replay/FactorPanel.tsx`

```tsx
/**
 * 因子值面板
 * PRD 4.17.1 因子值面板 (第1602-1619行)
 * 
 * 显示当前时刻的因子值和满足状态
 */

import React from 'react';
import { FactorSnapshot } from '@/types/replay';

interface FactorPanelProps {
  snapshot: FactorSnapshot | null;
}

export const FactorPanel: React.FC<FactorPanelProps> = ({ snapshot }) => {
  if (!snapshot) {
    return <div className="factor-panel empty">加载中...</div>;
  }
  
  return (
    <div className="factor-panel">
      <h3>📊 当前时刻因子值</h3>
      
      <div className="factor-list">
        {Object.entries(snapshot.thresholds).map(([name, config]) => (
          <div key={name} className={`factor-item ${config.passed ? 'passed' : 'failed'}`}>
            <span className="indicator">
              {config.passed ? '●' : '○'}
            </span>
            <span className="name">{name}</span>
            <span className="value">
              {snapshot.factorValues[name]?.toFixed(2)}
            </span>
            <span className="threshold">
              ({config.direction === 'below' ? '<' : '>'}{config.value})
            </span>
            <span className="status">
              {config.passed ? '✓' : '✗'}
            </span>
          </div>
        ))}
      </div>
      
      <div className="summary">
        <div className={`overall-signal ${snapshot.overallSignal}`}>
          综合信号: {snapshot.overallSignal === 'buy' ? '买入' : snapshot.overallSignal === 'sell' ? '卖出' : '持有'}
        </div>
        <div className="conditions">
          ({snapshot.conditionsMet}/{snapshot.conditionsTotal} 条件满足)
        </div>
      </div>
    </div>
  );
};
```

**验收标准**:
- [ ] 因子值显示正确
- [ ] 满足/不满足状态区分
- [ ] 综合信号显示正确

---

### Task 9.8: 信号事件日志组件

**文件**: `frontend/src/components/Replay/SignalEventLog.tsx`

```tsx
/**
 * 信号事件日志
 * PRD 4.17.1 信号事件日志 (第1621-1639行)
 * 
 * 显示回放期间的所有信号事件
 */

import React from 'react';
import { SignalEvent } from '@/types/replay';

interface SignalEventLogProps {
  events: SignalEvent[];
  onExport: () => void;
}

export const SignalEventLog: React.FC<SignalEventLogProps> = ({ events, onExport }) => {
  const getEventIcon = (type: string) => {
    switch (type) {
      case 'buy_trigger': return '🟢';
      case 'sell_trigger': return '🔴';
      case 'condition_check': return '🟡';
      default: return '⚪';
    }
  };
  
  const getEventLabel = (type: string) => {
    switch (type) {
      case 'buy_trigger': return '买入信号触发';
      case 'sell_trigger': return '卖出信号';
      case 'condition_check': return '条件检查';
      default: return '未知事件';
    }
  };
  
  return (
    <div className="signal-event-log">
      <div className="header">
        <h3>📋 信号事件日志</h3>
        <button onClick={onExport}>导出</button>
      </div>
      
      <div className="event-list">
        {events.map((event) => (
          <div key={event.eventId} className={`event-item ${event.eventType}`}>
            <div className="event-header">
              <span className="icon">{getEventIcon(event.eventType)}</span>
              <span className="label">{getEventLabel(event.eventType)}</span>
              <span className="time">{formatTime(event.timestamp)}</span>
            </div>
            <div className="event-body">
              <div className="description">{event.description}</div>
              <div className="price">{event.symbol} @ ${event.price}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
```

**验收标准**:
- [ ] 事件列表显示正确
- [ ] 事件类型图标区分
- [ ] 导出功能可用

---

### Task 9.9: 回放洞察面板组件

**文件**: `frontend/src/components/Replay/ReplayInsightPanel.tsx`

```tsx
/**
 * 回放洞察面板
 * PRD 4.17.1 回放洞察面板 (第1641-1669行)
 * 
 * 显示回放期间的统计和AI洞察
 */

import React from 'react';
import { ReplayInsight } from '@/types/replay';

interface ReplayInsightPanelProps {
  insight: ReplayInsight | null;
  onDetailReport: () => void;
  onSaveReplay: () => void;
}

export const ReplayInsightPanel: React.FC<ReplayInsightPanelProps> = ({
  insight,
  onDetailReport,
  onSaveReplay
}) => {
  if (!insight) {
    return <div className="insight-panel empty">回放结束后显示洞察</div>;
  }
  
  return (
    <div className="replay-insight-panel">
      <h3>🎯 回放洞察</h3>
      
      {/* 统计指标 */}
      <div className="metrics-grid">
        <div className="metric">
          <div className="label">信号数</div>
          <div className="value">{insight.totalSignals}</div>
        </div>
        <div className="metric">
          <div className="label">执行率</div>
          <div className="value">{(insight.executionRate * 100).toFixed(0)}%</div>
        </div>
        <div className="metric">
          <div className="label">胜率</div>
          <div className={`value ${insight.winRate >= 0.5 ? 'positive' : 'negative'}`}>
            {(insight.winRate * 100).toFixed(0)}%
          </div>
        </div>
        <div className="metric">
          <div className="label">Alpha</div>
          <div className={`value ${insight.alpha >= 0 ? 'positive' : 'negative'}`}>
            {insight.alpha >= 0 ? '+' : ''}{(insight.alpha * 100).toFixed(1)}%
          </div>
        </div>
      </div>
      
      {/* 收益对比 */}
      <div className="return-comparison">
        <div className="label">收益对比:</div>
        <div className="bar-chart">
          <div className="bar strategy">
            <span className="name">策略</span>
            <div className="fill" style={{ width: `${Math.min(insight.strategyReturn * 10, 100)}%` }} />
            <span className="value">{(insight.strategyReturn * 100).toFixed(1)}%</span>
          </div>
          <div className="bar benchmark">
            <span className="name">SPY</span>
            <div className="fill" style={{ width: `${Math.min(insight.benchmarkReturn * 10, 100)}%` }} />
            <span className="value">{(insight.benchmarkReturn * 100).toFixed(1)}%</span>
          </div>
        </div>
      </div>
      
      {/* AI洞察 */}
      {insight.aiInsights.length > 0 && (
        <div className="ai-insights">
          <h4>💡 AI洞察</h4>
          {insight.aiInsights.map((text, index) => (
            <div key={index} className="insight-item">{text}</div>
          ))}
        </div>
      )}
      
      {/* 操作按钮 */}
      <div className="actions">
        <button onClick={onDetailReport}>📊 详细报告</button>
        <button onClick={onSaveReplay}>💾 保存回放</button>
      </div>
    </div>
  );
};
```

**验收标准**:
- [ ] 统计指标显示正确
- [ ] 收益对比图表正常
- [ ] AI洞察显示正常
- [ ] 操作按钮可用

---

### Task 9.10: 回放页面集成

**文件**: `frontend/src/pages/StrategyReplay/index.tsx`

```tsx
/**
 * 策略回放页面
 * PRD 4.17.1 整体布局 (第1528-1569行)
 * 
 * 布局:
 * - 顶部: 导航栏 + 回放标识
 * - 上部: 回放控制条
 * - 中部: K线图 (TradingView回放模式) + 右侧面板
 * - 下部: 模拟持仓
 */

import React, { useState, useEffect, useCallback } from 'react';
import { TradingViewChart } from '@/components/Chart/TradingViewChart';
import { ReplayControlBar } from '@/components/Replay/ReplayControlBar';
import { FactorPanel } from '@/components/Replay/FactorPanel';
import { SignalEventLog } from '@/components/Replay/SignalEventLog';
import { ReplayInsightPanel } from '@/components/Replay/ReplayInsightPanel';
import { useReplay } from '@/hooks/useReplay';

export const StrategyReplayPage: React.FC = () => {
  const {
    state,
    snapshot,
    events,
    insight,
    signalMarkers,
    init,
    play,
    pause,
    stepForward,
    stepBackward,
    seek,
    nextSignal,
    setSpeed,
    exportReplay
  } = useReplay();
  
  return (
    <div className="strategy-replay-page">
      {/* 顶部导航 */}
      <header className="replay-header">
        <span className="logo">QuantVision</span>
        <span className="mode-badge">🔄 策略回放</span>
        <span className="strategy-name">{state?.config.strategyId}</span>
        <span className="replay-indicator">🟣 回放模式</span>
        <button className="exit-button">退出回放</button>
      </header>
      
      {/* 回放控制条 */}
      <ReplayControlBar
        state={state}
        signalMarkers={signalMarkers}
        onPlay={play}
        onPause={pause}
        onStepForward={stepForward}
        onStepBackward={stepBackward}
        onSeek={seek}
        onNextSignal={nextSignal}
        onSpeedChange={setSpeed}
        onConfigChange={(config) => init(config)}
      />
      
      {/* 主内容区 */}
      <div className="main-content">
        {/* K线图区域 */}
        <div className="chart-section">
          <TradingViewChart
            symbol={state?.config.symbol}
            mode="replay"
            currentTime={state?.currentTime}
            signalOverlay={{
              buySignals: events.filter(e => e.eventType === 'buy_trigger'),
              sellSignals: events.filter(e => e.eventType === 'sell_trigger'),
            }}
          />
        </div>
        
        {/* 右侧面板 */}
        <div className="right-panel">
          <FactorPanel snapshot={snapshot} />
          <SignalEventLog events={events} onExport={exportReplay} />
          <ReplayInsightPanel
            insight={insight}
            onDetailReport={() => {}}
            onSaveReplay={() => {}}
          />
        </div>
      </div>
      
      {/* 模拟持仓区 */}
      <div className="position-section">
        <h4>模拟持仓</h4>
        <table>
          <thead>
            <tr>
              <th>股票</th>
              <th>持仓</th>
              <th>成本</th>
              <th>现价</th>
              <th>盈亏</th>
            </tr>
          </thead>
          <tbody>
            {state?.positionQuantity > 0 && (
              <tr>
                <td>{state.config.symbol}</td>
                <td>{state.positionQuantity}股</td>
                <td>${state.positionAvgCost}</td>
                <td>${snapshot?.factorValues.close}</td>
                <td className={state.totalReturnPct >= 0 ? 'positive' : 'negative'}>
                  {state.totalReturnPct >= 0 ? '+' : ''}{(state.totalReturnPct * 100).toFixed(2)}%
                </td>
              </tr>
            )}
          </tbody>
        </table>
        <div className="account-summary">
          总资产: ${(state?.cash + state?.positionQuantity * (snapshot?.factorValues.close || 0)).toFixed(2)}
        </div>
      </div>
    </div>
  );
};
```

**验收标准**:
- [ ] 页面布局正确
- [ ] 各组件集成成功
- [ ] 回放流程流畅

---

## Part C: 集成测试 (1天)

### Task 9.11: 回放功能集成测试

**测试用例**:

1. **初始化测试**
   - [ ] 选择日期范围后正确加载数据
   - [ ] 进度条信号标记正确显示
   - [ ] 初始状态正确

2. **播放控制测试**
   - [ ] 播放/暂停切换正常
   - [ ] 前进/后退步进正确
   - [ ] 跳转到指定时间正确
   - [ ] 跳转到下一信号正确
   - [ ] 速度切换生效

3. **因子计算测试**
   - [ ] 因子值实时更新
   - [ ] 信号触发检测正确
   - [ ] 条件满足判定正确

4. **模拟持仓测试**
   - [ ] 买入后持仓增加
   - [ ] 卖出后持仓减少
   - [ ] 盈亏计算正确

5. **洞察生成测试**
   - [ ] 回放结束后生成洞察
   - [ ] 统计指标正确
   - [ ] AI洞察生成正常

---

## Sprint 9 完成检查清单

### 后端
- [ ] replay.py Schema完整
- [ ] historical_data_service.py 数据服务正常
- [ ] replay_engine_service.py 回放引擎正常
- [ ] replay.py API可调用
- [ ] WebSocket流正常

### 前端
- [ ] replay.ts 类型定义完整
- [ ] ReplayControlBar.tsx 控制条正常
- [ ] FactorPanel.tsx 因子面板正常
- [ ] SignalEventLog.tsx 事件日志正常
- [ ] ReplayInsightPanel.tsx 洞察面板正常
- [ ] StrategyReplayPage 页面集成成功

### 集成测试
- [ ] 回放初始化正常
- [ ] 播放控制正常
- [ ] 因子计算正确
- [ ] 信号触发正确
- [ ] 洞察生成正常

---

## 新增API端点

```
POST /api/v1/replay/init                  - 初始化回放
POST /api/v1/replay/{id}/play            - 开始播放
POST /api/v1/replay/{id}/pause           - 暂停
POST /api/v1/replay/{id}/step-forward    - 前进一步
POST /api/v1/replay/{id}/step-backward   - 后退一步
POST /api/v1/replay/{id}/seek            - 跳转时间
POST /api/v1/replay/{id}/next-signal     - 下一信号
PUT  /api/v1/replay/{id}/speed           - 设置速度
GET  /api/v1/replay/{id}/insight         - 获取洞察
GET  /api/v1/replay/{id}/export          - 导出记录
WS   /api/v1/replay/{id}/stream          - 实时流
```

---

## 新增文件清单

### 后端 (4个)
- `backend/app/schemas/replay.py`
- `backend/app/services/historical_data_service.py`
- `backend/app/services/replay_engine_service.py`
- `backend/app/api/v1/replay.py`

### 前端 (6个)
- `frontend/src/types/replay.ts`
- `frontend/src/components/Replay/ReplayControlBar.tsx`
- `frontend/src/components/Replay/FactorPanel.tsx`
- `frontend/src/components/Replay/SignalEventLog.tsx`
- `frontend/src/components/Replay/ReplayInsightPanel.tsx`
- `frontend/src/pages/StrategyReplay/index.tsx`

---

## 下一步

完成后可选择:
- 进入 **v2.2.0** 开发 (税务计算、版本管理)
- 或发布 **v2.1.0** 完整版

---

**预计完成时间**: 7天
