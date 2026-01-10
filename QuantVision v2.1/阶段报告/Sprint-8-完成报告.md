# Sprint-8 完成报告: 日内交易完整UI

## 概述

Sprint-8 实现了日内交易完整UI，包含盘前扫描器和日内交易专用视图，支持时间止损等日内交易专属功能。

## 完成内容

### PRD 4.18.0 盘前扫描器

#### 后端实现

| 文件 | 描述 |
|------|------|
| `backend/app/schemas/pre_market.py` | 盘前扫描数据模型 |
| `backend/app/services/pre_market_service.py` | 盘前扫描业务逻辑 |
| `backend/app/api/v1/pre_market.py` | 盘前扫描API端点 |

**API 端点:**

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/v1/intraday/pre-market-scanner` | 盘前扫描 |
| POST | `/api/v1/intraday/watchlist` | 确认监控列表 |
| GET | `/api/v1/intraday/watchlist` | 获取今日监控列表 |
| GET | `/api/v1/intraday/watchlist/history` | 获取监控列表历史 |
| GET | `/api/v1/intraday/market-status` | 获取市场状态 |

**评分算法:**
- Gap分数: 30%权重
- 成交量分数: 30%权重
- 波动率分数: 20%权重
- 新闻催化: 额外10分

#### 前端实现

| 文件 | 描述 |
|------|------|
| `frontend/src/types/preMarket.ts` | TypeScript类型定义 |
| `frontend/src/components/Intraday/PreMarketScanner.tsx` | 盘前扫描器组件 |

**功能特性:**
- 支持Gap、盘前成交量、波动率、流动性筛选
- 支持新闻催化、财报日筛选
- AI建议展示
- 批量选择确认监控列表

### PRD 4.18.1 日内交易专用视图

#### 前端组件

| 文件 | 描述 |
|------|------|
| `frontend/src/components/Intraday/SimplifiedWatchlist.tsx` | 简化监控列表 (100px宽) |
| `frontend/src/components/Intraday/StopLossPanel.tsx` | 止盈止损面板 |
| `frontend/src/components/Intraday/IntradayTradeLog.tsx` | 今日交易记录 |
| `frontend/src/components/Intraday/IntradayTradingPage.tsx` | 日内交易主页面 |
| `frontend/src/components/Intraday/index.ts` | 组件导出 |

**三栏布局:**
```
┌─────────┬────────────────────────┬──────────────┐
│  简化   │                        │   止盈止损   │
│  监控   │   TradingView 图表     │     面板     │
│  列表   │                        ├──────────────┤
│ (100px) │                        │   今日交易   │
│         │   快速交易面板         │     记录     │
└─────────┴────────────────────────┴──────────────┘
```

**止盈止损功能:**
- ATR动态止损/止盈 (1.0x - 3.0x)
- 固定价格止损/止盈
- 百分比止损/止盈
- 时间止损 (收盘前自动平仓)
- 移动止损 (追踪止损)
- 盈亏比实时计算

#### 后端定时任务

| 文件 | 描述 |
|------|------|
| `backend/app/tasks/time_stop_task.py` | 时间止损定时任务 |

**时间止损配置:**
- 15:45 (收盘前15分钟)
- 15:50 (收盘前10分钟)
- 15:55 (收盘前5分钟)

使用APScheduler调度，在美东时间指定时刻自动执行平仓。

### 路由注册

已在 `backend/app/main.py` 注册:
```python
# v2.1 Sprint 8: 日内交易 API (PRD 4.18.0-4.18.1)
app.include_router(
    pre_market.router,
    prefix=settings.API_V1_PREFIX,
    tags=["日内交易"],
)
```

## 数据结构

### PreMarketStock
```typescript
interface PreMarketStock {
  symbol: string
  name: string
  gap: number
  gap_direction: 'up' | 'down'
  premarket_price: number
  premarket_volume: number
  premarket_volume_ratio: number
  prev_close: number
  volatility: number
  avg_daily_volume: number
  avg_daily_value: number
  has_news: boolean
  news_headline?: string
  is_earnings_day: boolean
  score: number
  score_breakdown: ScoreBreakdown
}
```

### StopLossConfig
```typescript
interface StopLossConfig {
  stop_loss_type: 'atr' | 'fixed' | 'percentage' | 'technical'
  stop_loss_value: number
  take_profit_type: 'atr' | 'fixed' | 'percentage' | 'technical'
  take_profit_value: number
  time_stop_enabled: boolean
  time_stop_time: string
  trailing_stop_enabled: boolean
  trailing_trigger_pct: number
  trailing_distance_pct: number
}
```

## 新增文件清单

```
backend/
├── app/
│   ├── schemas/
│   │   └── pre_market.py          # 盘前扫描Schema
│   ├── services/
│   │   └── pre_market_service.py  # 盘前扫描服务
│   ├── api/v1/
│   │   └── pre_market.py          # 盘前扫描API
│   └── tasks/
│       └── time_stop_task.py      # 时间止损任务

frontend/
├── src/
│   ├── types/
│   │   └── preMarket.ts           # 类型定义
│   └── components/
│       └── Intraday/
│           ├── index.ts
│           ├── PreMarketScanner.tsx
│           ├── SimplifiedWatchlist.tsx
│           ├── StopLossPanel.tsx
│           ├── IntradayTradeLog.tsx
│           └── IntradayTradingPage.tsx
```

## 修改文件清单

| 文件 | 修改内容 |
|------|----------|
| `backend/app/main.py` | 添加pre_market路由注册 |
| `backend/app/tasks/__init__.py` | 导出时间止损任务 |

## 待集成事项

1. **实际API对接**: 当前使用模拟数据，需对接真实盘前数据源
2. **时间止损执行**: 需对接实际交易服务执行平仓
3. **WebSocket推送**: 实时价格和信号更新
4. **持仓数据库**: 持久化持仓和止损配置

## 测试建议

1. 盘前扫描器筛选功能测试
2. 监控列表确认流程测试
3. 止盈止损配置保存测试
4. 三栏布局响应式测试
5. 时间止损定时任务测试

## 完成时间

2025年1月5日
