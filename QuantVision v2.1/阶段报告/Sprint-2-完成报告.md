# Sprint 2 完成报告: 交易监控升级

> **完成日期**: 2026-01-04
> **Sprint 周期**: 5.5天
> **状态**: 已完成

---

## 一、完成概览

### 后端 (Python FastAPI)

| 任务 | 文件 | 状态 |
|------|------|------|
| Task 2.1 | `backend/app/schemas/signal_radar.py` | ✅ 完成 |
| Task 2.2 | `backend/app/services/signal_service.py` | ✅ 完成 |
| Task 2.3 | `backend/app/api/v1/signal_radar.py` | ✅ 完成 |
| Task 2.9 | 接近触发计算逻辑 (集成在 signal_service.py) | ✅ 完成 |
| Task 2.10 | SignalStatusCache (内存缓存) | ✅ 完成 |
| 路由注册 | `backend/app/main.py` | ✅ 完成 |

### 前端 (React + TypeScript)

| 任务 | 文件 | 状态 |
|------|------|------|
| Task 2.4 | `frontend/src/types/signalRadar.ts` | ✅ 完成 |
| Task 2.5 | `frontend/src/components/SignalRadar/index.tsx` | ✅ 完成 |
| Task 2.6 | `frontend/src/components/SignalRadar/SignalList.tsx` | ✅ 完成 |
| Task 2.7 | `frontend/src/components/common/EnvironmentSwitch.tsx` | ✅ 完成 |
| Task 2.8 | `frontend/src/pages/Trading/index.tsx` (升级) | ✅ 完成 |

---

## 二、新增API端点

```
GET  /api/v1/signal-radar/{strategy_id}           - 获取策略信号列表
GET  /api/v1/signal-radar/stocks/search           - 搜索股票
GET  /api/v1/signal-radar/{strategy_id}/history   - 获取历史信号
GET  /api/v1/signal-radar/{strategy_id}/status-summary - 状态分布统计
POST /api/v1/signal-radar/{strategy_id}/refresh   - 刷新信号
```

---

## 三、核心功能实现

### 3.1 信号雷达 Schema (PRD 4.16.2)

```python
# 信号类型
class SignalType(str, Enum):
    BUY = "buy"      # 买入信号
    SELL = "sell"    # 卖出信号
    HOLD = "hold"    # 持有

# 信号状态 (6种优先级)
class SignalStatus(str, Enum):
    HOLDING = "holding"           # 🔴 已持仓
    BUY_SIGNAL = "buy_signal"     # 🟢 买入信号
    SELL_SIGNAL = "sell_signal"   # 🟠 卖出信号
    NEAR_TRIGGER = "near_trigger" # 🟡 接近触发 (>=80%)
    MONITORING = "monitoring"     # ⚪ 监控中
    EXCLUDED = "excluded"         # ⚫ 不符合条件

# 信号强度
class SignalStrength(str, Enum):
    STRONG = "strong"    # 强信号 (score >= 80)
    MEDIUM = "medium"    # 中等 (60 <= score < 80)
    WEAK = "weak"        # 弱信号 (score < 60)
```

### 3.2 接近触发计算 (PRD 4.16.2)

```python
def calc_near_trigger_pct(current_value, threshold, start_value, direction):
    """
    计算因子接近触发程度

    - direction='below': 阈值要求小于某值 (如 PE < 20)
    - direction='above': 阈值要求大于某值 (如 ROE > 15%)

    当 near_trigger_pct >= 80% 时，标记为接近触发
    """
```

### 3.3 Task 2.10: 信号状态缓存实现说明

> **实现方式**: 使用内存缓存实现，数据库模型待后续 Sprint 集成

**当前实现**:
- `SignalStatusCache` 定义为 Pydantic model (位于 `schemas/signal_radar.py`)
- 服务层使用内存字典 `_status_cache: dict[str, dict[str, SignalStatusCache]]` 存储
- 适用于开发阶段和单实例部署

**后续数据库集成计划**:
```python
# backend/app/models/signal_status.py (待实现)
class SignalStatusCache(Base):
    __tablename__ = "signal_status_cache"
    strategy_id = Column(String(36), nullable=False)
    symbol = Column(String(10), nullable=False)
    status = Column(Enum(SignalStatus), default=SignalStatus.MONITORING)
    signal_strength = Column(Numeric(5, 2), default=0)
    factor_values = Column(JSONB, default={})
    updated_at = Column(DateTime, nullable=False)
    __table_args__ = (PrimaryKeyConstraint('strategy_id', 'symbol'),)
```

**迁移时机**: 当需要多实例部署或持久化缓存时，创建数据库模型并迁移

### 3.4 环境切换器 (PRD 4.15.3)

**切换条件检查**:
- 模拟盘运行天数 >= 30天
- 策略胜率 >= 40%
- 用户确认弹窗

**实盘风险提示**:
- 实盘交易将使用真实资金
- 所有交易订单将被实际执行

---

## 四、前端组件架构

```
frontend/src/
├── types/
│   └── signalRadar.ts          # 信号雷达类型定义
├── components/
│   ├── SignalRadar/
│   │   ├── index.tsx           # 信号雷达主面板
│   │   └── SignalList.tsx      # 信号列表组件
│   └── common/
│       └── EnvironmentSwitch.tsx # 环境切换器
└── pages/
    └── Trading/
        └── index.tsx           # 交易页面 (三栏布局)
```

### 4.1 信号雷达面板功能

- 实时信号列表展示 (30秒自动刷新)
- 按信号类型筛选 (买入/卖出/持有)
- 按信号强度筛选 (强/中/弱)
- 股票搜索
- 信号统计徽章
- 信号详情展开

### 4.2 信号列表组件功能

- 信号卡片展示 (股票、价格、评分、状态)
- 因子触发进度条
- 快速下单按钮
- 目标价/止损价显示
- 预期收益显示

### 4.3 环境切换器功能

- 模拟盘/实盘状态显示
- 切换条件检查 (天数、胜率)
- 确认弹窗
- 条件状态指示标签

### 4.4 Trading 页面升级

**三栏布局**:
```
┌────────────────┬────────────────┬────────────────┐
│   信号雷达     │    持仓列表    │    订单管理    │
│                │                │                │
│  - 实时信号    │  - 当前持仓    │  - 今日订单    │
│  - 筛选搜索    │  - 盈亏显示    │  - 订单状态    │
│  - 一键下单    │  - 平仓操作    │  - 取消订单    │
└────────────────┴────────────────┴────────────────┘
```

---

## 五、验收标准完成情况

### 后端验收

- [x] signal_radar.py Schema 完整
- [x] signal_service.py 服务完整
- [x] signal_radar.py API 可调用
- [x] 路由已注册 (main.py)
- [x] 接近触发计算正确 (80%阈值)
- [x] 状态优先级判断正确
- [x] 支持 above/below 两种方向

### 前端验收

- [x] signalRadar.ts 类型定义完整
- [x] SignalRadar/index.tsx 面板正常
- [x] SignalList.tsx 组件正常
- [x] EnvironmentSwitch.tsx 切换器正常
- [x] Trading 页面集成成功 (三栏布局)

### 集成验收

- [x] 信号雷达显示正常
- [x] 买入/卖出信号区分明确
- [x] 环境切换流程完整
- [x] 信号点击预填充下单表单

---

## 六、文件清单

### 新增文件

| 文件路径 | 说明 |
|----------|------|
| `backend/app/schemas/signal_radar.py` | 信号雷达 Pydantic Schema |
| `backend/app/services/signal_service.py` | 信号雷达服务层 |
| `backend/app/api/v1/signal_radar.py` | 信号雷达 API 路由 |
| `frontend/src/types/signalRadar.ts` | 前端类型定义 |
| `frontend/src/components/SignalRadar/index.tsx` | 信号雷达主面板 |
| `frontend/src/components/SignalRadar/SignalList.tsx` | 信号列表组件 |
| `frontend/src/components/common/EnvironmentSwitch.tsx` | 环境切换器 |

### 修改文件

| 文件路径 | 修改内容 |
|----------|----------|
| `backend/app/main.py` | 注册 signal_radar 路由 |
| `frontend/src/pages/Trading/index.tsx` | 升级为三栏布局，集成信号雷达和环境切换器 |

---

## 七、技术规范遵循

- [x] 后端: FastAPI + Pydantic + structlog
- [x] 前端: React 18 + TypeScript + Ant Design + TailwindCSS
- [x] 暗色主题: `bg-dark-card`, `bg-dark-hover`, `text-gray-400` 等
- [x] 中文 UI 文本
- [x] 组件化架构
- [x] 类型安全

---

## 八、下一步

完成后进入 **Sprint 3: PDT + AI状态**

---

**报告生成时间**: 2026-01-04
