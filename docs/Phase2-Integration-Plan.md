# QuantVision v2.1 Phase 2 - 真实数据集成计划

**计划日期**: 2026-01-07
**目标**: 将 Mock 数据替换为真实数据源

---

## 一、集成优先级

### P0 - 核心功能 (Sprint 6-7)

| 模块 | 当前状态 | 目标 | 依赖 |
|------|----------|------|------|
| TradingView Widget | 占位符 | 真实 K 线图表 | TradingView 账号 |
| 实时行情 | Mock 数据 | Polygon.io WebSocket | API Key |
| 历史数据 | Mock 数据 | Polygon.io REST API | API Key |

### P1 - 交易功能 (Sprint 8-9)

| 模块 | 当前状态 | 目标 | 依赖 |
|------|----------|------|------|
| 交易执行 | Mock 下单 | Alpaca Trading API | OAuth |
| 账户信息 | Mock 余额 | Alpaca Account API | OAuth |
| 持仓同步 | Mock 持仓 | Alpaca Positions API | OAuth |
| 订单管理 | Mock 订单 | Alpaca Orders API | OAuth |

### P2 - 后端服务 (Sprint 10-11)

| 模块 | 当前状态 | 目标 | 依赖 |
|------|----------|------|------|
| 策略存储 | localStorage | PostgreSQL | FastAPI |
| 回测引擎 | Mock 结果 | Python Backtest | vectorbt/backtrader |
| 信号服务 | Mock 信号 | 实时信号计算 | FastAPI + Redis |
| 风控系统 | Mock 预警 | 实时风控 | FastAPI + Celery |

---

## 二、Sprint 6: TradingView 集成

### 目标
- 集成真实 TradingView Widget
- 支持多时间框架切换
- 支持技术指标

### 任务清单

| 任务ID | 任务名称 | 优先级 | 预计文件 |
|--------|----------|--------|----------|
| T1 | TradingView Widget 配置 | P0 | `components/Chart/TradingViewChart.tsx` |
| T2 | 多时间框架支持 | P0 | `components/Chart/TimeframeSelector.tsx` |
| T3 | 技术指标面板 | P1 | `components/Chart/IndicatorPanel.tsx` |
| T4 | 图表主题同步 | P1 | 全局主题配置 |

### 技术方案

```typescript
// TradingView Widget 配置
const widget = new TradingView.widget({
  symbol: 'NASDAQ:NVDA',
  interval: '5',
  timezone: 'America/New_York',
  theme: 'dark',
  style: '1', // 蜡烛图
  locale: 'zh_CN',
  toolbar_bg: '#1a1a3a',
  enable_publishing: false,
  withdateranges: true,
  hide_side_toolbar: false,
  allow_symbol_change: true,
  studies: ['RSI@tv-basicstudies', 'MACD@tv-basicstudies'],
  container_id: 'tradingview_container',
})
```

---

## 三、Sprint 7: Polygon.io 行情集成

### 目标
- 实时行情 WebSocket 推送
- 历史 K 线数据获取
- 盘前盘后数据

### 任务清单

| 任务ID | 任务名称 | 优先级 | 预计文件 |
|--------|----------|--------|----------|
| T5 | Polygon WebSocket 服务 | P0 | `services/polygonWebSocket.ts` |
| T6 | 实时报价 Hook | P0 | `hooks/useRealTimeQuote.ts` |
| T7 | 历史数据 API | P0 | `services/polygonApi.ts` |
| T8 | 盘前扫描器数据源 | P1 | `services/preMarketService.ts` |

### 技术方案

```typescript
// Polygon WebSocket 连接
const ws = new WebSocket('wss://socket.polygon.io/stocks')

ws.onopen = () => {
  ws.send(JSON.stringify({ action: 'auth', params: API_KEY }))
  ws.send(JSON.stringify({
    action: 'subscribe',
    params: 'T.NVDA,T.AAPL,T.TSLA' // 实时交易
  }))
}

ws.onmessage = (event) => {
  const data = JSON.parse(event.data)
  // 更新实时价格
  dispatch(updateQuote(data))
}
```

### API 端点

```
# 实时报价
wss://socket.polygon.io/stocks

# 历史 K 线
GET /v2/aggs/ticker/{ticker}/range/{multiplier}/{timespan}/{from}/{to}

# 盘前数据
GET /v2/snapshot/locale/us/markets/stocks/tickers/{ticker}
```

---

## 四、Sprint 8: Alpaca 交易集成

### 目标
- OAuth 认证流程
- 下单 API 集成
- 账户余额同步

### 任务清单

| 任务ID | 任务名称 | 优先级 | 预计文件 |
|--------|----------|--------|----------|
| T9 | Alpaca OAuth 流程 | P0 | `services/alpacaAuth.ts` |
| T10 | 交易 API 服务 | P0 | `services/alpacaTrading.ts` |
| T11 | 订单管理 Hook | P0 | `hooks/useOrders.ts` |
| T12 | 账户状态 Hook | P0 | `hooks/useAccount.ts` |

### 技术方案

```typescript
// Alpaca API 服务
class AlpacaService {
  private baseUrl = 'https://paper-api.alpaca.markets' // 模拟盘
  // private baseUrl = 'https://api.alpaca.markets' // 实盘

  async submitOrder(order: OrderRequest): Promise<Order> {
    return fetch(`${this.baseUrl}/v2/orders`, {
      method: 'POST',
      headers: {
        'APCA-API-KEY-ID': apiKey,
        'APCA-API-SECRET-KEY': secretKey,
      },
      body: JSON.stringify(order),
    })
  }

  async getPositions(): Promise<Position[]> {
    return fetch(`${this.baseUrl}/v2/positions`, {
      headers: { ... },
    })
  }
}
```

---

## 五、Sprint 9: 订单与持仓同步

### 目标
- 实时持仓更新
- 订单状态 WebSocket
- 成交通知

### 任务清单

| 任务ID | 任务名称 | 优先级 | 预计文件 |
|--------|----------|--------|----------|
| T13 | Alpaca WebSocket | P0 | `services/alpacaWebSocket.ts` |
| T14 | 持仓面板更新 | P0 | `components/TradingMonitor/PositionMonitorPanel.tsx` |
| T15 | 订单面板更新 | P0 | `components/TradingMonitor/OrderPanel.tsx` |
| T16 | 成交通知组件 | P1 | `components/Notification/TradeNotification.tsx` |

---

## 六、Sprint 10-11: 后端服务

### 架构设计

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (React)                     │
└────────────────────────┬────────────────────────────────┘
                         │ REST / WebSocket
┌────────────────────────▼────────────────────────────────┐
│                   FastAPI Backend                        │
├─────────────┬─────────────┬─────────────┬───────────────┤
│  策略服务   │  回测服务    │  信号服务   │   风控服务     │
└──────┬──────┴──────┬──────┴──────┬──────┴───────┬───────┘
       │             │             │              │
┌──────▼──────┐ ┌────▼────┐ ┌──────▼──────┐ ┌────▼────┐
│ PostgreSQL  │ │ vectorbt│ │   Redis     │ │ Celery  │
│ (策略存储)  │ │ (回测)  │ │ (实时数据)  │ │ (任务)  │
└─────────────┘ └─────────┘ └─────────────┘ └─────────┘
```

### 任务清单

| 任务ID | 任务名称 | 优先级 | 预计文件 |
|--------|----------|--------|----------|
| T17 | 策略 CRUD API | P0 | `backend/app/routers/strategies.py` |
| T18 | 回测 API | P0 | `backend/app/routers/backtest.py` |
| T19 | 信号计算服务 | P1 | `backend/app/services/signal_service.py` |
| T20 | 风控预警服务 | P1 | `backend/app/services/risk_service.py` |
| T21 | WebSocket 网关 | P1 | `backend/app/websocket/gateway.py` |

---

## 七、环境变量配置

```env
# .env.local (前端)
VITE_POLYGON_API_KEY=your_polygon_key
VITE_ALPACA_API_KEY=your_alpaca_key
VITE_ALPACA_SECRET_KEY=your_alpaca_secret
VITE_API_BASE_URL=http://localhost:8000

# .env (后端)
DATABASE_URL=postgresql://user:pass@localhost:5432/quantvision
REDIS_URL=redis://localhost:6379
POLYGON_API_KEY=your_polygon_key
ALPACA_API_KEY=your_alpaca_key
ALPACA_SECRET_KEY=your_alpaca_secret
```

---

## 八、测试策略

### 单元测试
- API 服务 Mock 测试
- 组件渲染测试
- Hook 逻辑测试

### 集成测试
- Polygon API 连通性
- Alpaca Paper Trading
- 端到端流程测试

### 性能测试
- WebSocket 延迟监控
- 大量数据渲染性能
- 内存泄漏检测

---

## 九、里程碑

| 里程碑 | 目标日期 | 交付物 |
|--------|----------|--------|
| M1: TradingView 集成 | Sprint 6 完成 | 真实 K 线图表 |
| M2: 实时行情 | Sprint 7 完成 | Polygon.io 数据流 |
| M3: 交易功能 | Sprint 9 完成 | Alpaca 下单 |
| M4: 后端服务 | Sprint 11 完成 | 完整后端 API |

---

## 十、风险与应对

| 风险 | 可能性 | 影响 | 应对措施 |
|------|--------|------|----------|
| API 限流 | 中 | 高 | 实现请求队列、缓存 |
| WebSocket 断连 | 中 | 中 | 自动重连机制 |
| 数据延迟 | 低 | 中 | 延迟监控、降级策略 |
| 交易失败 | 低 | 高 | 重试机制、失败通知 |

---

**计划生成时间**: 2026-01-07
**下一步**: 开始 Sprint 6 - TradingView 集成
