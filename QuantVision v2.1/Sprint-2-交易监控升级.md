# Sprint 2: 交易监控升级 (5天)

> **文档版本**: 1.0  
> **预计时长**: 5天  
> **前置依赖**: Sprint 1 完成  
> **PRD参考**: 4.16.2 信号雷达, 4.15.3 环境切换  
> **交付物**: 信号雷达面板、环境切换器、卖出信号展示

---

## 目标

升级交易监控功能：实时信号展示、环境切换、卖出信号

---

## Task 2.1: 信号雷达Schema (后端)

**文件**: `backend/app/schemas/signal_radar.py`

**核心模型**:
```python
class SignalType(str, Enum):
    BUY = "buy"      # 买入信号
    SELL = "sell"    # 卖出信号
    HOLD = "hold"    # 持有

class SignalStrength(str, Enum):
    STRONG = "strong"    # 强信号
    MEDIUM = "medium"    # 中等
    WEAK = "weak"        # 弱信号

class Signal(BaseModel):
    signal_id: str
    strategy_id: str
    symbol: str
    company_name: str
    signal_type: SignalType
    signal_strength: SignalStrength
    signal_score: float  # 0-100
    triggered_factors: list[str]  # 触发的因子
    current_price: Decimal
    target_price: Optional[Decimal]
    stop_loss_price: Optional[Decimal]
    signal_time: datetime
    expires_at: Optional[datetime]
```

**验收标准**:
- [ ] 信号类型包含买入/卖出/持有
- [ ] 信号强度分级正确
- [ ] 因子触发记录完整

---

## Task 2.2: 信号服务 (后端)

**文件**: `backend/app/services/signal_service.py`

**核心功能**:
- 获取策略的实时信号
- 按股票/强度筛选
- 信号过期管理

**验收标准**:
- [ ] 信号列表获取正常
- [ ] 筛选功能正确
- [ ] 过期信号自动标记

---

## Task 2.3: 信号雷达API (后端)

**文件**: `backend/app/api/v1/signal_radar.py`

**端点**:
```
GET /api/v1/signal-radar/{strategy_id}     - 获取策略信号
GET /api/v1/signal-radar/stocks/search     - 搜索股票
GET /api/v1/signal-radar/{strategy_id}/history - 历史信号
```

**验收标准**:
- [ ] 信号列表API正常
- [ ] 股票搜索API正常
- [ ] 分页和筛选正确

---

## Task 2.4: 前端类型定义

**文件**: `frontend/src/types/signalRadar.ts`

```typescript
export type SignalType = 'buy' | 'sell' | 'hold';
export type SignalStrength = 'strong' | 'medium' | 'weak';

export interface Signal {
  signalId: string;
  strategyId: string;
  symbol: string;
  companyName: string;
  signalType: SignalType;
  signalStrength: SignalStrength;
  signalScore: number;
  triggeredFactors: string[];
  currentPrice: number;
  targetPrice?: number;
  stopLossPrice?: number;
  signalTime: string;
  expiresAt?: string;
}

export const SIGNAL_TYPE_CONFIG = {
  buy: { label: '买入', color: 'green', icon: '📈' },
  sell: { label: '卖出', color: 'red', icon: '📉' },
  hold: { label: '持有', color: 'blue', icon: '⏸️' },
};

export const SIGNAL_STRENGTH_CONFIG = {
  strong: { label: '强', color: 'green', stars: 3 },
  medium: { label: '中', color: 'orange', stars: 2 },
  weak: { label: '弱', color: 'gray', stars: 1 },
};
```

**验收标准**:
- [ ] 类型定义与后端一致
- [ ] 配置常量完整

---

## Task 2.5: 信号雷达面板

**文件**: `frontend/src/components/SignalRadar/index.tsx`

**功能**:
- 实时信号列表展示
- 按类型/强度筛选
- 股票搜索
- 信号详情展开

**UI布局**:
```
┌─────────────────────────────────────────────────────┐
│ 🎯 信号雷达                    [搜索] [筛选] [刷新] │
├─────────────────────────────────────────────────────┤
│ ┌─────────┐ ┌─────────┐ ┌─────────┐                 │
│ │ 买入 12 │ │ 卖出 5  │ │ 持有 8  │                 │
│ └─────────┘ └─────────┘ └─────────┘                 │
├─────────────────────────────────────────────────────┤
│ AAPL  📈 买入  ⭐⭐⭐  85分  $185.50 → $195.00      │
│ MSFT  📈 买入  ⭐⭐    72分  $378.20 → $400.00      │
│ GOOGL 📉 卖出  ⭐⭐⭐  90分  $142.80 止损: $135.00  │
│ ...                                                  │
└─────────────────────────────────────────────────────┘
```

**验收标准**:
- [ ] 信号列表正确显示
- [ ] 买入/卖出信号区分明确
- [ ] 筛选功能正常
- [ ] 自动刷新

---

## Task 2.6: 信号列表组件

**文件**: `frontend/src/components/SignalRadar/SignalList.tsx`

**功能**:
- 信号卡片展示
- 信号详情展开
- 一键下单入口

**验收标准**:
- [ ] 信号卡片信息完整
- [ ] 展开详情正常
- [ ] 操作按钮可点击

---

## Task 2.7: 环境切换器

**文件**: `frontend/src/components/common/EnvironmentSwitch.tsx`

**功能**:
- 模拟盘/实盘切换
- 切换确认弹窗
- 实盘切换条件检查

```tsx
// 核心逻辑
const handleSwitch = async () => {
  if (targetEnv === 'live') {
    // 检查切换条件
    // 1. 模拟盘运行满30天
    // 2. 胜率 > 40%
    // 3. 用户确认
  }
  // 执行切换
};
```

**验收标准**:
- [ ] 切换按钮显示当前环境
- [ ] 切换有确认弹窗
- [ ] 实盘切换条件检查

---

## Task 2.8: Trading页面集成

**修改文件**: `frontend/src/pages/Trading/index.tsx`

**改造**:
- 集成信号雷达面板
- 添加环境切换器
- 优化三栏布局

**布局**:
```
┌────────────────┬────────────────┬────────────────┐
│   信号雷达     │    持仓列表    │    订单管理    │
│                │                │                │
│   [Task 2.5]   │   [现有功能]   │   [现有功能]   │
│                │                │                │
└────────────────┴────────────────┴────────────────┘
```

**验收标准**:
- [ ] 三栏布局正常
- [ ] 信号雷达集成成功
- [ ] 页面切换流畅

---

## Sprint 2 完成检查清单

### 后端
- [ ] signal_radar.py Schema完整
- [ ] signal_service.py 服务完整
- [ ] signal_radar.py API可调用
- [ ] 路由已注册

### 前端
- [ ] signalRadar.ts 类型定义完整
- [ ] SignalRadar/index.tsx 面板正常
- [ ] SignalList.tsx 组件正常
- [ ] EnvironmentSwitch.tsx 切换器正常
- [ ] Trading页面集成成功

### 集成测试
- [ ] 信号雷达显示正常
- [ ] 买入/卖出信号区分明确
- [ ] 环境切换流程完整

---

## 新增API端点

```
GET /api/v1/signal-radar/{strategy_id}     - 获取策略信号
GET /api/v1/signal-radar/stocks/search     - 搜索股票
GET /api/v1/signal-radar/{strategy_id}/history - 历史信号
```

---

## 下一步

完成后进入 **Sprint 3: PDT + AI状态**

---

## Task 2.9: 接近触发计算逻辑 (PRD 4.16.2补充)

**文件**: `backend/app/services/signal_service.py` (补充)

**计算公式**:
```python
def calc_near_trigger_pct(
    current_value: float,
    threshold: float,
    start_value: float,
    direction: str  # 'above' 或 'below'
) -> float:
    """
    计算因子接近触发程度
    
    PRD 4.16.2 定义:
    - 如果 当前值 已满足阈值: 100%
    - 如果 当前值 接近阈值: (当前值 - 起始值) / (阈值 - 起始值) × 100%
    
    示例: PE 阈值 < 20
    - 当前 PE = 21.5, 起始观察值 = 25
    - 接近程度 = (25 - 21.5) / (25 - 20) × 100% = 70%
    
    当接近程度 ≥ 80% 时，标记为 🟡 接近触发
    """
    if direction == 'below':
        # 阈值要求小于某值 (如 PE < 20)
        if current_value <= threshold:
            return 100.0
        if start_value <= threshold:
            return 0.0  # 起始值已满足，无法计算接近程度
        return max(0, (start_value - current_value) / (start_value - threshold) * 100)
    else:
        # 阈值要求大于某值 (如 ROE > 15%)
        if current_value >= threshold:
            return 100.0
        if start_value >= threshold:
            return 0.0
        return max(0, (current_value - start_value) / (threshold - start_value) * 100)


def get_stock_signal_status(
    strategy_id: str,
    symbol: str,
    factor_values: dict,
    thresholds: dict,
    is_holding: bool
) -> tuple[str, float]:
    """
    获取股票信号状态
    
    返回: (status, signal_strength)
    
    状态优先级 (PRD 4.16.2):
    1. 🔴 holding - 已持仓
    2. 🟢 buy_signal - 已触发买入
    3. 🟠 sell_signal - 已触发卖出
    4. 🟡 near_trigger - 接近触发 (≥80%)
    5. ⚪ monitoring - 正常监控
    6. ⚫ excluded - 不符合条件
    """
    if is_holding:
        return ('holding', 100.0)
    
    # 计算各因子接近程度
    near_percentages = []
    all_satisfied = True
    
    for factor_name, config in thresholds.items():
        current = factor_values.get(factor_name)
        if current is None:
            continue
        
        pct = calc_near_trigger_pct(
            current,
            config['threshold'],
            config['start_value'],
            config['direction']
        )
        near_percentages.append(pct)
        
        if pct < 100:
            all_satisfied = False
    
    if not near_percentages:
        return ('excluded', 0.0)
    
    min_pct = min(near_percentages)
    
    if all_satisfied:
        return ('buy_signal', 100.0)
    elif min_pct >= 80:
        return ('near_trigger', min_pct)
    else:
        return ('monitoring', min_pct)
```

**验收标准**:
- [ ] 接近触发计算正确 (80%阈值)
- [ ] 状态优先级判断正确
- [ ] 支持above/below两种方向

---

## Task 2.10: 信号状态缓存表 (PRD 4.16.2补充)

**数据库迁移**: `backend/app/models/signal_status.py`

```python
"""
信号状态缓存表
PRD 4.16.2 定义

用于存储每个策略-股票组合的实时信号状态，
提高信号雷达的查询性能。
"""

from sqlalchemy import Column, String, Enum, Numeric, DateTime, PrimaryKeyConstraint
from sqlalchemy.dialects.postgresql import JSONB
from app.db.base_class import Base
import enum


class SignalStatus(str, enum.Enum):
    HOLDING = "holding"           # 🔴 已持仓
    BUY_SIGNAL = "buy_signal"     # 🟢 买入信号
    SELL_SIGNAL = "sell_signal"   # 🟠 卖出信号
    NEAR_TRIGGER = "near_trigger" # 🟡 接近触发
    MONITORING = "monitoring"     # ⚪ 监控中
    EXCLUDED = "excluded"         # ⚫ 不符合条件


class SignalStatusCache(Base):
    """信号状态缓存"""
    __tablename__ = "signal_status_cache"
    
    strategy_id = Column(String(36), nullable=False)
    symbol = Column(String(10), nullable=False)
    status = Column(Enum(SignalStatus), default=SignalStatus.MONITORING)
    signal_strength = Column(Numeric(5, 2), default=0)  # 0-100%
    factor_values = Column(JSONB, default={})  # 各因子当前值
    updated_at = Column(DateTime, nullable=False)
    
    __table_args__ = (
        PrimaryKeyConstraint('strategy_id', 'symbol'),
    )
```

**API补充**: `backend/app/api/v1/signal_radar.py`

```python
# 补充端点：获取信号状态分布统计
@router.get("/{strategy_id}/status-summary")
async def get_status_summary(strategy_id: str) -> dict:
    """
    获取策略的信号状态分布
    
    返回:
    {
        "holding": 3,
        "buy_signal": 2,
        "sell_signal": 0,
        "near_trigger": 5,
        "monitoring": 505,
        "excluded": 0
    }
    """
    pass
```

**验收标准**:
- [ ] 缓存表创建成功
- [ ] 状态更新机制正常
- [ ] 查询性能提升明显

---

## Sprint 2 更新说明

**版本**: 1.1 (2025-01-05更新)

**新增内容**:
- Task 2.9: 接近触发计算逻辑 (PRD 4.16.2 第1386-1398行)
- Task 2.10: 信号状态缓存表 (PRD 4.16.2 第1419-1428行)

**预计额外工时**: +0.5天

---

**预计完成时间**: 5.5天
