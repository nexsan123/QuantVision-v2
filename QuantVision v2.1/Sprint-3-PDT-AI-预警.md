# Sprint 3: PDT + AI状态 + 风险预警 (5天)

> **文档版本**: 2.0  
> **预计时长**: 5天 (原3天 + 新增2天)  
> **前置依赖**: Sprint 0 完成  
> **PRD参考**: 4.7 PDT规则管理, 4.2 AI连接状态, 4.14 风险预警通知  
> **交付物**: PDT状态显示、AI连接状态指示器、风险预警邮件通知

---

## 目标

1. 实现PDT规则管理和AI连接状态显示
2. **新增**: 实现风险预警邮件通知系统

---

## Part A: PDT + AI状态 (3天)

### Task 3.1: PDT服务 (后端)

**文件**: `backend/app/services/pdt_service.py`

**核心功能**:
- PDT规则检查 (4次/5交易日)
- 剩余次数计算
- 重置倒计时

**PDT规则**:
```python
# Pattern Day Trader 规则
# - 账户 < $25,000 时受限
# - 5个交易日内最多4次日内交易
# - 超过限制账户被限制90天

from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel

class PDTStatus(BaseModel):
    account_id: str
    account_balance: float
    is_pdt_restricted: bool  # 账户是否受PDT限制 (<$25K)
    remaining_day_trades: int
    max_day_trades: int = 4
    rolling_days: int = 5
    is_blocked: bool  # 是否已被限制
    blocked_until: Optional[datetime] = None
    reset_at: datetime  # 下次重置时间
    recent_day_trades: list["DayTradeRecord"]

class DayTradeRecord(BaseModel):
    trade_id: str
    symbol: str
    buy_time: datetime
    sell_time: datetime
    pnl: float
    expires_at: datetime  # 计入PDT的到期时间

class PDTService:
    MAX_DAY_TRADES = 4  # 5交易日内最多4次
    ROLLING_DAYS = 5    # 滚动5个交易日
    PDT_THRESHOLD = 25000  # $25,000 阈值
    
    def __init__(self, db_session):
        self.db = db_session
    
    async def get_pdt_status(self, account_id: str) -> PDTStatus:
        """获取PDT状态"""
        # 1. 获取账户余额
        account = await self._get_account(account_id)
        is_restricted = account.balance < self.PDT_THRESHOLD
        
        # 2. 获取最近5个交易日的日内交易
        cutoff_date = self._get_rolling_cutoff()
        recent_trades = await self._get_day_trades_since(account_id, cutoff_date)
        
        # 3. 计算剩余次数
        remaining = max(0, self.MAX_DAY_TRADES - len(recent_trades))
        
        # 4. 计算重置时间 (最早一笔交易过期时间)
        reset_at = self._calculate_reset_time(recent_trades)
        
        return PDTStatus(
            account_id=account_id,
            account_balance=account.balance,
            is_pdt_restricted=is_restricted,
            remaining_day_trades=remaining,
            is_blocked=remaining == 0,
            reset_at=reset_at,
            recent_day_trades=recent_trades
        )
    
    async def check_can_day_trade(self, account_id: str) -> tuple[bool, str]:
        """检查是否可以日内交易，返回(可否, 原因)"""
        status = await self.get_pdt_status(account_id)
        
        if not status.is_pdt_restricted:
            return True, "账户余额 >= $25,000，无PDT限制"
        
        if status.remaining_day_trades > 0:
            return True, f"剩余 {status.remaining_day_trades} 次日内交易机会"
        
        return False, f"已达PDT限制，将于 {status.reset_at} 重置"
    
    async def record_day_trade(self, account_id: str, trade: DayTradeRecord) -> PDTStatus:
        """记录一次日内交易"""
        # 记录交易
        await self._save_day_trade(account_id, trade)
        # 返回更新后的状态
        return await self.get_pdt_status(account_id)
    
    def _get_rolling_cutoff(self) -> datetime:
        """获取滚动窗口起始日期"""
        # 需要考虑交易日历，这里简化处理
        return datetime.now() - timedelta(days=7)  # 简化：7自然日约等于5交易日
    
    def _calculate_reset_time(self, trades: list[DayTradeRecord]) -> datetime:
        """计算下次重置时间"""
        if not trades:
            return datetime.now()
        # 最早的交易过期时间
        return min(t.expires_at for t in trades)
```

**验收标准**:
- [ ] PDT次数计算正确
- [ ] 重置时间计算正确
- [ ] 限制检查正确
- [ ] 账户余额判断正确

---

### Task 3.2: PDT API (后端)

**文件**: `backend/app/api/v1/pdt.py`

```python
from fastapi import APIRouter, Depends, HTTPException
from app.services.pdt_service import PDTService, PDTStatus
from app.core.deps import get_current_user, get_db

router = APIRouter(prefix="/pdt", tags=["PDT"])

@router.get("/status", response_model=PDTStatus)
async def get_pdt_status(
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """获取当前用户的PDT状态"""
    service = PDTService(db)
    return await service.get_pdt_status(current_user.account_id)

@router.get("/check")
async def check_day_trade_allowed(
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """检查是否允许日内交易"""
    service = PDTService(db)
    allowed, reason = await service.check_can_day_trade(current_user.account_id)
    return {
        "allowed": allowed,
        "reason": reason
    }

@router.get("/trades")
async def get_recent_day_trades(
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """获取最近的日内交易记录"""
    service = PDTService(db)
    status = await service.get_pdt_status(current_user.account_id)
    return {
        "trades": status.recent_day_trades,
        "count": len(status.recent_day_trades)
    }
```

**端点**:
```
GET /api/v1/pdt/status     - 获取PDT状态
GET /api/v1/pdt/check      - 检查是否允许日内交易
GET /api/v1/pdt/trades     - 获取日内交易记录
```

**验收标准**:
- [ ] 状态API返回正确
- [ ] 检查API返回正确
- [ ] 交易记录查询正确

---

### Task 3.3: AI状态API (后端)

**文件**: `backend/app/api/v1/ai_assistant.py`

```python
from fastapi import APIRouter, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import asyncio

router = APIRouter(prefix="/ai-assistant", tags=["AI"])

class AIConnectionStatus(BaseModel):
    is_connected: bool
    status: str  # 'connected' | 'connecting' | 'disconnected' | 'error'
    model_name: str = "Claude 4.5 Sonnet"
    last_heartbeat: Optional[datetime] = None
    latency_ms: Optional[int] = None
    error_message: Optional[str] = None
    can_reconnect: bool = True

# 全局状态 (生产环境应使用Redis)
_ai_status = AIConnectionStatus(
    is_connected=True,
    status="connected",
    last_heartbeat=datetime.now(),
    latency_ms=45
)

@router.get("/status", response_model=AIConnectionStatus)
async def get_ai_status():
    """获取AI连接状态"""
    return _ai_status

@router.post("/reconnect")
async def reconnect_ai(background_tasks: BackgroundTasks):
    """重新连接AI服务"""
    global _ai_status
    
    if not _ai_status.can_reconnect:
        return {"success": False, "message": "当前无法重连，请稍后再试"}
    
    # 设置为重连中状态
    _ai_status.status = "connecting"
    _ai_status.is_connected = False
    _ai_status.can_reconnect = False
    
    # 后台执行重连
    background_tasks.add_task(_do_reconnect)
    
    return {"success": True, "message": "正在重新连接..."}

async def _do_reconnect():
    """执行重连逻辑"""
    global _ai_status
    await asyncio.sleep(2)  # 模拟重连耗时
    
    # 模拟重连成功
    _ai_status.is_connected = True
    _ai_status.status = "connected"
    _ai_status.last_heartbeat = datetime.now()
    _ai_status.latency_ms = 50
    _ai_status.error_message = None
    _ai_status.can_reconnect = True

@router.get("/heartbeat")
async def heartbeat():
    """心跳检测"""
    global _ai_status
    _ai_status.last_heartbeat = datetime.now()
    return {"status": "ok", "timestamp": _ai_status.last_heartbeat}
```

**端点**:
```
GET  /api/v1/ai-assistant/status     - 获取AI连接状态
POST /api/v1/ai-assistant/reconnect  - 重新连接AI
GET  /api/v1/ai-assistant/heartbeat  - 心跳检测
```

**验收标准**:
- [ ] 连接状态正确
- [ ] 重连功能正常
- [ ] 心跳更新正常

---

### Task 3.4: 前端类型定义

**文件**: `frontend/src/types/pdt.ts`

```typescript
// PDT相关类型
export interface PDTStatus {
  accountId: string;
  accountBalance: number;
  isPdtRestricted: boolean;
  remainingDayTrades: number;
  maxDayTrades: number;
  rollingDays: number;
  isBlocked: boolean;
  blockedUntil?: string;
  resetAt: string;
  recentDayTrades: DayTradeRecord[];
}

export interface DayTradeRecord {
  tradeId: string;
  symbol: string;
  buyTime: string;
  sellTime: string;
  pnl: number;
  expiresAt: string;
}

export type PDTWarningLevel = 'none' | 'warning' | 'danger';

export function getPDTWarningLevel(remaining: number): PDTWarningLevel {
  if (remaining >= 2) return 'none';
  if (remaining === 1) return 'warning';
  return 'danger';
}
```

**文件**: `frontend/src/types/ai.ts`

```typescript
// AI连接状态类型
export type AIStatusType = 'connected' | 'connecting' | 'disconnected' | 'error';

export interface AIConnectionStatus {
  isConnected: boolean;
  status: AIStatusType;
  modelName: string;
  lastHeartbeat?: string;
  latencyMs?: number;
  errorMessage?: string;
  canReconnect: boolean;
}

export const AI_STATUS_CONFIG = {
  connected: { icon: '🟢', text: 'AI已连接', color: '#22c55e' },
  connecting: { icon: '🟡', text: '正在连接...', color: '#eab308' },
  disconnected: { icon: '🔴', text: 'AI已断开', color: '#ef4444' },
  error: { icon: '🔴', text: '连接错误', color: '#ef4444' },
} as const;
```

---

### Task 3.5: PDT状态组件

**文件**: `frontend/src/components/PDT/PDTStatus.tsx`

```tsx
import React from 'react';
import { PDTStatus as PDTStatusType, getPDTWarningLevel } from '@/types/pdt';
import { formatDistanceToNow } from 'date-fns';
import { zhCN } from 'date-fns/locale';

interface Props {
  status: PDTStatusType;
}

export const PDTStatusPanel: React.FC<Props> = ({ status }) => {
  const warningLevel = getPDTWarningLevel(status.remainingDayTrades);
  const percentage = (status.remainingDayTrades / status.maxDayTrades) * 100;
  
  const resetText = formatDistanceToNow(new Date(status.resetAt), {
    addSuffix: true,
    locale: zhCN
  });
  
  return (
    <div className="pdt-status-panel">
      <div className="pdt-header">
        <span className="pdt-icon">📊</span>
        <span className="pdt-title">PDT状态</span>
        {!status.isPdtRestricted && (
          <span className="pdt-badge pdt-badge-success">无限制</span>
        )}
      </div>
      
      {status.isPdtRestricted && (
        <div className="pdt-content">
          <div className="pdt-remaining">
            <span className="pdt-label">剩余日内交易次数:</span>
            <span className={`pdt-value pdt-${warningLevel}`}>
              {status.remainingDayTrades}/{status.maxDayTrades}
            </span>
          </div>
          
          <div className="pdt-progress">
            <div 
              className={`pdt-progress-bar pdt-progress-${warningLevel}`}
              style={{ width: `${percentage}%` }}
            />
          </div>
          
          <div className="pdt-reset">
            <span className="pdt-label">下次重置:</span>
            <span className="pdt-value">{resetText}</span>
          </div>
          
          {warningLevel === 'danger' && (
            <div className="pdt-blocked-warning">
              ⚠️ 已达到PDT限制，暂时无法进行日内交易
            </div>
          )}
        </div>
      )}
      
      {!status.isPdtRestricted && (
        <div className="pdt-unlimited">
          <p>账户余额 ≥ $25,000</p>
          <p>无日内交易次数限制</p>
        </div>
      )}
    </div>
  );
};
```

**验收标准**:
- [ ] 剩余次数显示正确
- [ ] 进度条显示正确
- [ ] 重置倒计时正确
- [ ] 无限制账户显示正确

---

### Task 3.6: PDT警告组件

**文件**: `frontend/src/components/PDT/PDTWarning.tsx`

```tsx
import React from 'react';
import { PDTWarningLevel } from '@/types/pdt';

interface Props {
  level: PDTWarningLevel;
  remaining: number;
  onConfirm?: () => void;
  onCancel?: () => void;
}

export const PDTWarning: React.FC<Props> = ({ 
  level, 
  remaining, 
  onConfirm, 
  onCancel 
}) => {
  if (level === 'none') return null;
  
  const isBlocked = level === 'danger';
  
  return (
    <div className={`pdt-warning pdt-warning-${level}`}>
      <div className="pdt-warning-icon">
        {isBlocked ? '🚫' : '⚠️'}
      </div>
      
      <div className="pdt-warning-content">
        <h4 className="pdt-warning-title">
          {isBlocked ? 'PDT限制已达上限' : 'PDT次数即将用尽'}
        </h4>
        
        <p className="pdt-warning-message">
          {isBlocked 
            ? '您已用完本周所有日内交易次数，暂时无法进行新的日内交易。'
            : `您仅剩 ${remaining} 次日内交易机会，请谨慎使用。`
          }
        </p>
        
        {!isBlocked && (
          <p className="pdt-warning-tip">
            💡 入金至 $25,000 以上可解除PDT限制
          </p>
        )}
      </div>
      
      <div className="pdt-warning-actions">
        {!isBlocked && onConfirm && (
          <button className="btn btn-warning" onClick={onConfirm}>
            我已了解，继续交易
          </button>
        )}
        {onCancel && (
          <button className="btn btn-secondary" onClick={onCancel}>
            取消
          </button>
        )}
      </div>
    </div>
  );
};
```

**验收标准**:
- [ ] 警告级别正确显示
- [ ] 黄色警告可确认继续
- [ ] 红色警告阻止交易
- [ ] 提示信息清晰

---

### Task 3.7: AI状态指示器

**文件**: `frontend/src/components/AI/AIStatusIndicator.tsx`

```tsx
import React, { useState } from 'react';
import { AIConnectionStatus, AI_STATUS_CONFIG } from '@/types/ai';

interface Props {
  status: AIConnectionStatus;
  onReconnect?: () => Promise<void>;
}

export const AIStatusIndicator: React.FC<Props> = ({ status, onReconnect }) => {
  const [reconnecting, setReconnecting] = useState(false);
  const config = AI_STATUS_CONFIG[status.status];
  
  const handleReconnect = async () => {
    if (!onReconnect || !status.canReconnect) return;
    setReconnecting(true);
    try {
      await onReconnect();
    } finally {
      setReconnecting(false);
    }
  };
  
  return (
    <div className="ai-status-indicator">
      <span className="ai-status-icon">{config.icon}</span>
      <span className="ai-status-text" style={{ color: config.color }}>
        {config.text}
      </span>
      
      {status.isConnected && status.latencyMs && (
        <span className="ai-latency">
          (延迟: {status.latencyMs}ms)
        </span>
      )}
      
      {!status.isConnected && status.canReconnect && (
        <button 
          className="ai-reconnect-btn"
          onClick={handleReconnect}
          disabled={reconnecting}
        >
          {reconnecting ? '重连中...' : '重新连接'}
        </button>
      )}
      
      {status.errorMessage && (
        <span className="ai-error" title={status.errorMessage}>
          ⚠️
        </span>
      )}
    </div>
  );
};
```

**验收标准**:
- [ ] 状态图标正确 (🟢🟡🔴)
- [ ] 重连按钮可用
- [ ] 延迟显示正确
- [ ] 错误信息可查看

---

### Task 3.8: 布局集成

**修改文件**: `frontend/src/layouts/MainLayout.tsx`

- 顶部栏添加AI状态指示器
- Trading页面添加PDT状态

```tsx
// MainLayout.tsx 顶部栏添加
<header className="main-header">
  <Logo />
  <Navigation />
  <div className="header-right">
    <AIStatusIndicator status={aiStatus} onReconnect={handleReconnect} />
    <UserMenu />
  </div>
</header>

// TradingPage.tsx 添加PDT面板
<aside className="trading-sidebar">
  <PDTStatusPanel status={pdtStatus} />
  <SignalRadar />
</aside>
```

**验收标准**:
- [ ] AI状态显示在顶部栏右侧
- [ ] PDT状态显示在Trading页面侧边栏

---

## Part B: 风险预警通知 (2天) 🆕

### Task 3.9: 风险预警Schema (后端)

**文件**: `backend/app/schemas/alert.py`

```python
from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime
from enum import Enum

class AlertType(str, Enum):
    DAILY_LOSS = "daily_loss"           # 单日亏损
    MAX_DRAWDOWN = "max_drawdown"       # 最大回撤
    CONCENTRATION = "concentration"      # 持仓集中度
    VIX_HIGH = "vix_high"               # VIX过高
    CONFLICT_PENDING = "conflict_pending"  # 策略冲突待决策
    SYSTEM_ERROR = "system_error"       # 系统异常
    PDT_WARNING = "pdt_warning"         # PDT警告

class AlertSeverity(str, Enum):
    INFO = "info"       # 信息
    WARNING = "warning"  # 黄色警告
    CRITICAL = "critical"  # 红色严重

class AlertChannel(str, Enum):
    EMAIL = "email"
    # Phase 2: WECHAT = "wechat"
    # Phase 3: APP_PUSH = "app_push"

class RiskAlert(BaseModel):
    alert_id: str
    user_id: str
    strategy_id: Optional[str] = None
    alert_type: AlertType
    severity: AlertSeverity
    title: str
    message: str
    details: Optional[dict] = None
    is_read: bool = False
    is_sent: bool = False
    sent_channels: list[AlertChannel] = []
    created_at: datetime
    sent_at: Optional[datetime] = None

class AlertConfig(BaseModel):
    """用户预警配置"""
    user_id: str
    enabled: bool = True
    
    # 触发阈值
    daily_loss_threshold: float = 0.03  # 3%
    max_drawdown_threshold: float = 0.10  # 10%
    concentration_threshold: float = 0.30  # 30%
    vix_threshold: float = 30.0
    
    # 通知渠道
    email_enabled: bool = True
    email_address: Optional[str] = None
    
    # 静默时段 (避免夜间打扰)
    quiet_hours_start: Optional[int] = 22  # 22:00
    quiet_hours_end: Optional[int] = 8     # 08:00

class CreateAlertRequest(BaseModel):
    alert_type: AlertType
    severity: AlertSeverity
    title: str
    message: str
    strategy_id: Optional[str] = None
    details: Optional[dict] = None
```

---

### Task 3.10: 风险预警服务 (后端)

**文件**: `backend/app/services/alert_service.py`

```python
from datetime import datetime
from typing import Optional
from app.schemas.alert import (
    RiskAlert, AlertType, AlertSeverity, AlertChannel, AlertConfig
)
from app.services.email_service import EmailService
import uuid

class AlertService:
    """风险预警服务"""
    
    # 预警阈值配置
    DEFAULT_THRESHOLDS = {
        AlertType.DAILY_LOSS: 0.03,       # 单日亏损 > 3%
        AlertType.MAX_DRAWDOWN: 0.10,     # 最大回撤 > 10%
        AlertType.CONCENTRATION: 0.30,    # 单股持仓 > 30%
        AlertType.VIX_HIGH: 30.0,         # VIX > 30
    }
    
    def __init__(self, db_session, email_service: EmailService):
        self.db = db_session
        self.email_service = email_service
    
    async def check_and_alert(
        self, 
        user_id: str,
        alert_type: AlertType,
        current_value: float,
        strategy_id: Optional[str] = None,
        extra_details: Optional[dict] = None
    ) -> Optional[RiskAlert]:
        """检查是否需要触发预警"""
        
        # 获取用户配置
        config = await self._get_user_config(user_id)
        if not config.enabled:
            return None
        
        # 获取阈值
        threshold = self._get_threshold(config, alert_type)
        
        # 判断是否触发
        should_alert = self._should_trigger(alert_type, current_value, threshold)
        if not should_alert:
            return None
        
        # 创建预警
        alert = await self._create_alert(
            user_id=user_id,
            strategy_id=strategy_id,
            alert_type=alert_type,
            current_value=current_value,
            threshold=threshold,
            extra_details=extra_details
        )
        
        # 发送通知
        await self._send_notification(alert, config)
        
        return alert
    
    async def create_manual_alert(
        self,
        user_id: str,
        alert_type: AlertType,
        severity: AlertSeverity,
        title: str,
        message: str,
        strategy_id: Optional[str] = None,
        details: Optional[dict] = None
    ) -> RiskAlert:
        """手动创建预警 (用于冲突、系统错误等)"""
        
        alert = RiskAlert(
            alert_id=str(uuid.uuid4()),
            user_id=user_id,
            strategy_id=strategy_id,
            alert_type=alert_type,
            severity=severity,
            title=title,
            message=message,
            details=details,
            created_at=datetime.now()
        )
        
        await self._save_alert(alert)
        
        # 获取用户配置并发送
        config = await self._get_user_config(user_id)
        await self._send_notification(alert, config)
        
        return alert
    
    def _should_trigger(
        self, 
        alert_type: AlertType, 
        value: float, 
        threshold: float
    ) -> bool:
        """判断是否应该触发预警"""
        if alert_type in [AlertType.DAILY_LOSS, AlertType.MAX_DRAWDOWN]:
            return abs(value) >= threshold  # 亏损用绝对值
        elif alert_type == AlertType.VIX_HIGH:
            return value >= threshold
        elif alert_type == AlertType.CONCENTRATION:
            return value >= threshold
        return False
    
    def _get_severity(self, alert_type: AlertType, value: float, threshold: float) -> AlertSeverity:
        """根据超出程度确定严重级别"""
        ratio = abs(value) / threshold if threshold > 0 else 1
        
        if ratio >= 2.0:  # 超出2倍
            return AlertSeverity.CRITICAL
        elif ratio >= 1.0:  # 刚达到阈值
            return AlertSeverity.WARNING
        return AlertSeverity.INFO
    
    async def _create_alert(
        self,
        user_id: str,
        strategy_id: Optional[str],
        alert_type: AlertType,
        current_value: float,
        threshold: float,
        extra_details: Optional[dict]
    ) -> RiskAlert:
        """创建预警对象"""
        
        severity = self._get_severity(alert_type, current_value, threshold)
        title, message = self._generate_alert_message(alert_type, current_value, threshold)
        
        alert = RiskAlert(
            alert_id=str(uuid.uuid4()),
            user_id=user_id,
            strategy_id=strategy_id,
            alert_type=alert_type,
            severity=severity,
            title=title,
            message=message,
            details={
                "current_value": current_value,
                "threshold": threshold,
                **(extra_details or {})
            },
            created_at=datetime.now()
        )
        
        await self._save_alert(alert)
        return alert
    
    def _generate_alert_message(
        self, 
        alert_type: AlertType, 
        value: float, 
        threshold: float
    ) -> tuple[str, str]:
        """生成预警标题和消息"""
        
        messages = {
            AlertType.DAILY_LOSS: (
                f"⚠️ 单日亏损预警: {abs(value)*100:.1f}%",
                f"您的账户今日亏损已达 {abs(value)*100:.1f}%，超过预设阈值 {threshold*100:.1f}%。建议检查持仓风险。"
            ),
            AlertType.MAX_DRAWDOWN: (
                f"🔴 最大回撤预警: {abs(value)*100:.1f}%",
                f"策略最大回撤已达 {abs(value)*100:.1f}%，触及预警阈值 {threshold*100:.1f}%。建议评估是否暂停策略。"
            ),
            AlertType.CONCENTRATION: (
                f"⚠️ 持仓集中度预警",
                f"单只股票持仓占比达 {value*100:.1f}%，超过安全阈值 {threshold*100:.1f}%。建议分散投资。"
            ),
            AlertType.VIX_HIGH: (
                f"📈 市场波动率预警: VIX={value:.1f}",
                f"VIX指数已达 {value:.1f}，市场波动加剧。建议谨慎操作，注意风险控制。"
            ),
        }
        
        return messages.get(alert_type, ("风险预警", "请检查您的账户"))
    
    async def _send_notification(self, alert: RiskAlert, config: AlertConfig):
        """发送通知"""
        
        # 检查静默时段
        if self._is_quiet_hours(config):
            return
        
        # 发送邮件 (Phase 1)
        if config.email_enabled and config.email_address:
            try:
                await self.email_service.send_alert_email(
                    to_email=config.email_address,
                    alert=alert
                )
                alert.sent_channels.append(AlertChannel.EMAIL)
                alert.is_sent = True
                alert.sent_at = datetime.now()
                await self._update_alert(alert)
            except Exception as e:
                print(f"Failed to send email: {e}")
    
    def _is_quiet_hours(self, config: AlertConfig) -> bool:
        """检查是否在静默时段"""
        if config.quiet_hours_start is None or config.quiet_hours_end is None:
            return False
        
        current_hour = datetime.now().hour
        start, end = config.quiet_hours_start, config.quiet_hours_end
        
        if start <= end:
            return start <= current_hour < end
        else:  # 跨午夜
            return current_hour >= start or current_hour < end
    
    async def get_user_alerts(
        self, 
        user_id: str, 
        unread_only: bool = False,
        limit: int = 50
    ) -> list[RiskAlert]:
        """获取用户的预警列表"""
        # 数据库查询实现
        pass
    
    async def mark_as_read(self, alert_id: str, user_id: str) -> bool:
        """标记预警为已读"""
        pass
```

---

### Task 3.11: 邮件服务 (后端)

**文件**: `backend/app/services/email_service.py`

```python
from typing import Optional
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.schemas.alert import RiskAlert, AlertSeverity
from app.core.config import settings

class EmailService:
    """邮件发送服务"""
    
    def __init__(self):
        self.smtp_server = settings.SMTP_SERVER
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_email = settings.FROM_EMAIL
    
    async def send_alert_email(self, to_email: str, alert: RiskAlert):
        """发送预警邮件"""
        
        subject = f"[QuantVision] {alert.title}"
        html_body = self._build_alert_html(alert)
        
        await self._send_email(to_email, subject, html_body)
    
    def _build_alert_html(self, alert: RiskAlert) -> str:
        """构建预警邮件HTML"""
        
        severity_colors = {
            AlertSeverity.INFO: "#3b82f6",      # 蓝色
            AlertSeverity.WARNING: "#eab308",   # 黄色
            AlertSeverity.CRITICAL: "#ef4444",  # 红色
        }
        
        color = severity_colors.get(alert.severity, "#666")
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: -apple-system, sans-serif; background: #f5f5f5; padding: 20px; }}
                .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 8px; overflow: hidden; }}
                .header {{ background: {color}; color: white; padding: 20px; }}
                .header h1 {{ margin: 0; font-size: 18px; }}
                .content {{ padding: 20px; }}
                .message {{ color: #333; line-height: 1.6; }}
                .details {{ background: #f9f9f9; padding: 15px; border-radius: 4px; margin-top: 15px; }}
                .footer {{ padding: 20px; text-align: center; color: #999; font-size: 12px; }}
                .btn {{ display: inline-block; background: #3b82f6; color: white; padding: 10px 20px; 
                        text-decoration: none; border-radius: 4px; margin-top: 15px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>{alert.title}</h1>
                </div>
                <div class="content">
                    <p class="message">{alert.message}</p>
                    
                    {self._build_details_html(alert.details) if alert.details else ""}
                    
                    <a href="https://quantvision.app/alerts/{alert.alert_id}" class="btn">
                        查看详情
                    </a>
                </div>
                <div class="footer">
                    <p>此邮件由 QuantVision 系统自动发送</p>
                    <p>如需修改预警设置，请访问 <a href="https://quantvision.app/settings/alerts">预警配置</a></p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _build_details_html(self, details: dict) -> str:
        """构建详情区块"""
        if not details:
            return ""
        
        items = []
        labels = {
            "current_value": "当前值",
            "threshold": "预警阈值",
            "strategy_name": "策略名称",
            "symbol": "股票代码",
        }
        
        for key, value in details.items():
            label = labels.get(key, key)
            if isinstance(value, float):
                if 0 < abs(value) < 1:
                    value = f"{value*100:.2f}%"
                else:
                    value = f"{value:.2f}"
            items.append(f"<p><strong>{label}:</strong> {value}</p>")
        
        return f'<div class="details">{"".join(items)}</div>'
    
    async def _send_email(self, to_email: str, subject: str, html_body: str):
        """发送邮件"""
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = self.from_email
        msg['To'] = to_email
        
        html_part = MIMEText(html_body, 'html', 'utf-8')
        msg.attach(html_part)
        
        with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
            server.starttls()
            server.login(self.smtp_user, self.smtp_password)
            server.send_message(msg)
```

---

### Task 3.12: 风险预警API (后端)

**文件**: `backend/app/api/v1/alerts.py`

```python
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from app.services.alert_service import AlertService
from app.schemas.alert import (
    RiskAlert, AlertConfig, CreateAlertRequest, AlertType, AlertSeverity
)
from app.core.deps import get_current_user, get_db, get_alert_service

router = APIRouter(prefix="/alerts", tags=["Alerts"])

@router.get("/", response_model=list[RiskAlert])
async def get_alerts(
    unread_only: bool = Query(False, description="只显示未读"),
    alert_type: Optional[AlertType] = Query(None, description="预警类型筛选"),
    limit: int = Query(50, le=100),
    current_user = Depends(get_current_user),
    alert_service: AlertService = Depends(get_alert_service)
):
    """获取预警列表"""
    alerts = await alert_service.get_user_alerts(
        user_id=current_user.id,
        unread_only=unread_only,
        limit=limit
    )
    
    if alert_type:
        alerts = [a for a in alerts if a.alert_type == alert_type]
    
    return alerts

@router.get("/unread-count")
async def get_unread_count(
    current_user = Depends(get_current_user),
    alert_service: AlertService = Depends(get_alert_service)
):
    """获取未读预警数量"""
    alerts = await alert_service.get_user_alerts(
        user_id=current_user.id,
        unread_only=True
    )
    return {"count": len(alerts)}

@router.post("/{alert_id}/read")
async def mark_alert_read(
    alert_id: str,
    current_user = Depends(get_current_user),
    alert_service: AlertService = Depends(get_alert_service)
):
    """标记预警为已读"""
    success = await alert_service.mark_as_read(alert_id, current_user.id)
    if not success:
        raise HTTPException(404, "预警不存在")
    return {"success": True}

@router.post("/mark-all-read")
async def mark_all_read(
    current_user = Depends(get_current_user),
    alert_service: AlertService = Depends(get_alert_service)
):
    """标记所有预警为已读"""
    await alert_service.mark_all_as_read(current_user.id)
    return {"success": True}

@router.get("/config", response_model=AlertConfig)
async def get_alert_config(
    current_user = Depends(get_current_user),
    alert_service: AlertService = Depends(get_alert_service)
):
    """获取预警配置"""
    return await alert_service.get_user_config(current_user.id)

@router.put("/config", response_model=AlertConfig)
async def update_alert_config(
    config: AlertConfig,
    current_user = Depends(get_current_user),
    alert_service: AlertService = Depends(get_alert_service)
):
    """更新预警配置"""
    config.user_id = current_user.id
    return await alert_service.update_user_config(config)

@router.post("/test-email")
async def test_email_notification(
    current_user = Depends(get_current_user),
    alert_service: AlertService = Depends(get_alert_service)
):
    """发送测试邮件"""
    await alert_service.send_test_email(current_user.id)
    return {"success": True, "message": "测试邮件已发送"}
```

**端点**:
```
GET    /api/v1/alerts              - 获取预警列表
GET    /api/v1/alerts/unread-count - 获取未读数量
POST   /api/v1/alerts/{id}/read    - 标记为已读
POST   /api/v1/alerts/mark-all-read - 全部标记已读
GET    /api/v1/alerts/config       - 获取预警配置
PUT    /api/v1/alerts/config       - 更新预警配置
POST   /api/v1/alerts/test-email   - 发送测试邮件
```

---

### Task 3.13: 前端预警组件

**文件**: `frontend/src/types/alert.ts`

```typescript
export type AlertType = 
  | 'daily_loss' 
  | 'max_drawdown' 
  | 'concentration' 
  | 'vix_high' 
  | 'conflict_pending' 
  | 'system_error'
  | 'pdt_warning';

export type AlertSeverity = 'info' | 'warning' | 'critical';

export interface RiskAlert {
  alertId: string;
  userId: string;
  strategyId?: string;
  alertType: AlertType;
  severity: AlertSeverity;
  title: string;
  message: string;
  details?: Record<string, any>;
  isRead: boolean;
  isSent: boolean;
  createdAt: string;
  sentAt?: string;
}

export interface AlertConfig {
  userId: string;
  enabled: boolean;
  dailyLossThreshold: number;
  maxDrawdownThreshold: number;
  concentrationThreshold: number;
  vixThreshold: number;
  emailEnabled: boolean;
  emailAddress?: string;
  quietHoursStart?: number;
  quietHoursEnd?: number;
}

export const ALERT_SEVERITY_CONFIG = {
  info: { icon: 'ℹ️', color: '#3b82f6', bg: '#eff6ff' },
  warning: { icon: '⚠️', color: '#eab308', bg: '#fefce8' },
  critical: { icon: '🔴', color: '#ef4444', bg: '#fef2f2' },
};
```

**文件**: `frontend/src/components/Alerts/AlertBell.tsx`

```tsx
import React, { useState } from 'react';
import { RiskAlert, ALERT_SEVERITY_CONFIG } from '@/types/alert';

interface Props {
  unreadCount: number;
  alerts: RiskAlert[];
  onMarkRead: (alertId: string) => void;
  onMarkAllRead: () => void;
}

export const AlertBell: React.FC<Props> = ({
  unreadCount,
  alerts,
  onMarkRead,
  onMarkAllRead
}) => {
  const [isOpen, setIsOpen] = useState(false);
  
  return (
    <div className="alert-bell-container">
      <button 
        className="alert-bell-btn"
        onClick={() => setIsOpen(!isOpen)}
      >
        🔔
        {unreadCount > 0 && (
          <span className="alert-badge">{unreadCount}</span>
        )}
      </button>
      
      {isOpen && (
        <div className="alert-dropdown">
          <div className="alert-dropdown-header">
            <span>风险预警</span>
            {unreadCount > 0 && (
              <button onClick={onMarkAllRead}>全部已读</button>
            )}
          </div>
          
          <div className="alert-list">
            {alerts.length === 0 ? (
              <div className="alert-empty">暂无预警</div>
            ) : (
              alerts.slice(0, 10).map(alert => (
                <AlertItem 
                  key={alert.alertId}
                  alert={alert}
                  onClick={() => onMarkRead(alert.alertId)}
                />
              ))
            )}
          </div>
          
          <div className="alert-dropdown-footer">
            <a href="/alerts">查看全部</a>
          </div>
        </div>
      )}
    </div>
  );
};

const AlertItem: React.FC<{ alert: RiskAlert; onClick: () => void }> = ({
  alert,
  onClick
}) => {
  const config = ALERT_SEVERITY_CONFIG[alert.severity];
  
  return (
    <div 
      className={`alert-item ${alert.isRead ? 'read' : 'unread'}`}
      style={{ borderLeftColor: config.color }}
      onClick={onClick}
    >
      <span className="alert-icon">{config.icon}</span>
      <div className="alert-content">
        <div className="alert-title">{alert.title}</div>
        <div className="alert-time">
          {new Date(alert.createdAt).toLocaleString()}
        </div>
      </div>
    </div>
  );
};
```

**文件**: `frontend/src/components/Alerts/AlertConfigPanel.tsx`

```tsx
import React, { useState } from 'react';
import { AlertConfig } from '@/types/alert';

interface Props {
  config: AlertConfig;
  onSave: (config: AlertConfig) => Promise<void>;
  onTestEmail: () => Promise<void>;
}

export const AlertConfigPanel: React.FC<Props> = ({
  config,
  onSave,
  onTestEmail
}) => {
  const [formData, setFormData] = useState(config);
  const [saving, setSaving] = useState(false);
  
  const handleSave = async () => {
    setSaving(true);
    try {
      await onSave(formData);
    } finally {
      setSaving(false);
    }
  };
  
  return (
    <div className="alert-config-panel">
      <h3>预警配置</h3>
      
      <div className="config-section">
        <label className="config-toggle">
          <input
            type="checkbox"
            checked={formData.enabled}
            onChange={e => setFormData({...formData, enabled: e.target.checked})}
          />
          启用风险预警
        </label>
      </div>
      
      <div className="config-section">
        <h4>触发阈值</h4>
        
        <div className="config-field">
          <label>单日亏损预警</label>
          <input
            type="number"
            value={formData.dailyLossThreshold * 100}
            onChange={e => setFormData({
              ...formData, 
              dailyLossThreshold: parseFloat(e.target.value) / 100
            })}
          />
          <span>%</span>
        </div>
        
        <div className="config-field">
          <label>最大回撤预警</label>
          <input
            type="number"
            value={formData.maxDrawdownThreshold * 100}
            onChange={e => setFormData({
              ...formData,
              maxDrawdownThreshold: parseFloat(e.target.value) / 100
            })}
          />
          <span>%</span>
        </div>
        
        <div className="config-field">
          <label>VIX预警阈值</label>
          <input
            type="number"
            value={formData.vixThreshold}
            onChange={e => setFormData({
              ...formData,
              vixThreshold: parseFloat(e.target.value)
            })}
          />
        </div>
      </div>
      
      <div className="config-section">
        <h4>邮件通知</h4>
        
        <label className="config-toggle">
          <input
            type="checkbox"
            checked={formData.emailEnabled}
            onChange={e => setFormData({...formData, emailEnabled: e.target.checked})}
          />
          启用邮件通知
        </label>
        
        {formData.emailEnabled && (
          <>
            <div className="config-field">
              <label>邮箱地址</label>
              <input
                type="email"
                value={formData.emailAddress || ''}
                onChange={e => setFormData({...formData, emailAddress: e.target.value})}
                placeholder="your@email.com"
              />
            </div>
            
            <button 
              className="btn btn-secondary"
              onClick={onTestEmail}
            >
              发送测试邮件
            </button>
          </>
        )}
      </div>
      
      <div className="config-actions">
        <button 
          className="btn btn-primary"
          onClick={handleSave}
          disabled={saving}
        >
          {saving ? '保存中...' : '保存配置'}
        </button>
      </div>
    </div>
  );
};
```

**验收标准**:
- [ ] 预警铃铛显示未读数量
- [ ] 下拉列表显示最近预警
- [ ] 配置面板可调整阈值
- [ ] 测试邮件功能正常

---

### Task 3.14: 布局集成 (预警)

**修改文件**: `frontend/src/layouts/MainLayout.tsx`

```tsx
// 顶部栏添加预警铃铛
<header className="main-header">
  <Logo />
  <Navigation />
  <div className="header-right">
    <AlertBell 
      unreadCount={unreadAlertCount}
      alerts={recentAlerts}
      onMarkRead={handleMarkAlertRead}
      onMarkAllRead={handleMarkAllAlertsRead}
    />
    <AIStatusIndicator status={aiStatus} onReconnect={handleReconnect} />
    <UserMenu />
  </div>
</header>
```

---

## Sprint 3 完成检查清单

### Part A: PDT + AI状态
- [ ] pdt_service.py 服务完整
- [ ] pdt.py API可调用
- [ ] ai_assistant.py 状态端点完整
- [ ] PDTStatus.tsx 状态显示正常
- [ ] PDTWarning.tsx 警告正常
- [ ] AIStatusIndicator.tsx 指示器正常

### Part B: 风险预警 🆕
- [ ] alert.py Schema完整
- [ ] alert_service.py 预警服务完整
- [ ] email_service.py 邮件发送正常
- [ ] alerts.py API可调用
- [ ] AlertBell.tsx 铃铛组件正常
- [ ] AlertConfigPanel.tsx 配置面板正常
- [ ] 测试邮件发送成功

### 集成测试
- [ ] PDT剩余次数正确
- [ ] PDT警告触发正确
- [ ] AI状态实时显示
- [ ] AI重连功能正常
- [ ] 单日亏损预警触发正确 🆕
- [ ] 邮件通知发送成功 🆕
- [ ] 预警列表显示正确 🆕

---

## 新增API端点

```
# PDT相关
GET  /api/v1/pdt/status               - 获取PDT状态
GET  /api/v1/pdt/check                - 检查是否允许日内交易
GET  /api/v1/pdt/trades               - 获取日内交易记录

# AI状态相关
GET  /api/v1/ai-assistant/status      - 获取AI连接状态
POST /api/v1/ai-assistant/reconnect   - 重新连接AI
GET  /api/v1/ai-assistant/heartbeat   - 心跳检测

# 风险预警相关 🆕
GET    /api/v1/alerts                 - 获取预警列表
GET    /api/v1/alerts/unread-count    - 获取未读数量
POST   /api/v1/alerts/{id}/read       - 标记为已读
POST   /api/v1/alerts/mark-all-read   - 全部标记已读
GET    /api/v1/alerts/config          - 获取预警配置
PUT    /api/v1/alerts/config          - 更新预警配置
POST   /api/v1/alerts/test-email      - 发送测试邮件
```

---

## 新增文件清单

### 后端
```
backend/app/
├── schemas/
│   └── alert.py           🆕
├── services/
│   ├── pdt_service.py
│   ├── alert_service.py   🆕
│   └── email_service.py   🆕
└── api/v1/
    ├── pdt.py
    ├── ai_assistant.py
    └── alerts.py          🆕
```

### 前端
```
frontend/src/
├── types/
│   ├── pdt.ts
│   ├── ai.ts
│   └── alert.ts           🆕
└── components/
    ├── PDT/
    │   ├── PDTStatus.tsx
    │   └── PDTWarning.tsx
    ├── AI/
    │   └── AIStatusIndicator.tsx
    └── Alerts/            🆕
        ├── AlertBell.tsx
        └── AlertConfigPanel.tsx
```

---

## 下一步

完成后进入 **Sprint 4: 整合测试 + 漂移监控**

---

**预计完成时间**: 5天 (原3天 + 新增2天)
