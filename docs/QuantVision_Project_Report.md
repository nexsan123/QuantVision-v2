# QuantVision v2.1 项目总报告

**版本**: v2.1.0
**日期**: 2026-01-09
**状态**: 生产就绪

---

## 目录

1. [项目概述](#1-项目概述)
2. [技术架构](#2-技术架构)
3. [后端详情](#3-后端详情)
4. [前端详情](#4-前端详情)
5. [数据库设计](#5-数据库设计)
6. [API 接口清单](#6-api-接口清单)
7. [核心功能模块](#7-核心功能模块)
8. [基础设施与部署](#8-基础设施与部署)
9. [开发阶段回顾](#9-开发阶段回顾)
10. [项目统计](#10-项目统计)
11. [附录](#11-附录)

---

## 1. 项目概述

### 1.1 项目定位

QuantVision v2.1 是一个**机构级量化投资平台**，提供从因子研究、策略构建、回测验证到实盘交易的完整工作流。系统面向专业量化交易员和资产管理机构，强调数据质量、风险控制和执行效率。

### 1.2 核心价值

| 特性 | 描述 |
|------|------|
| **全流程覆盖** | 因子研究 → 策略构建 → 回测验证 → 风险评估 → 实盘部署 → 监控预警 |
| **专业级分析** | Walk-forward 验证、过拟合检测、幸存者偏差检测、前视偏差检测 |
| **实时交易** | 多券商集成、智能执行算法 (VWAP/TWAP/POV)、WebSocket 实时推送 |
| **风险管理** | VaR 计算、因子暴露分析、压力测试、熔断机制、PDT 规则 |
| **企业级架构** | 异步高性能、微服务化、容器化部署、完整监控告警 |

### 1.3 目标用户

- 量化研究员 (因子挖掘、策略研发)
- 交易员 (策略执行、风险监控)
- 风控经理 (风险度量、压力测试)
- 投资组合经理 (组合优化、归因分析)

---

## 2. 技术架构

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           QuantVision v2.1                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                        Frontend (React + TypeScript)               │  │
│  │                                                                    │  │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐   │  │
│  │  │Dashboard│ │ Factor  │ │Strategy │ │Backtest │ │ Trading │   │  │
│  │  │         │ │   Lab   │ │ Builder │ │ Center  │ │ Center  │   │  │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘   │  │
│  │                                                                    │  │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐   │  │
│  │  │  Risk   │ │ Signal  │ │Template │ │ Replay  │ │Intraday │   │  │
│  │  │ Center  │ │  Radar  │ │ Library │ │  View   │ │ Trading │   │  │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘   │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                              │ REST API / WebSocket                      │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                        Backend (FastAPI + Python)                  │  │
│  │                                                                    │  │
│  │  ┌─────────────────────────┐  ┌─────────────────────────┐        │  │
│  │  │      API Layer          │  │     WebSocket Layer      │        │  │
│  │  │  • 33 API Modules       │  │  • Trading Stream        │        │  │
│  │  │  • 100+ Endpoints       │  │  • Market Data           │        │  │
│  │  │  • OpenAPI Docs         │  │  • Alpaca Stream         │        │  │
│  │  └─────────────────────────┘  └─────────────────────────┘        │  │
│  │                                                                    │  │
│  │  ┌─────────────────────────┐  ┌─────────────────────────┐        │  │
│  │  │    Service Layer        │  │    Engine Layer          │        │  │
│  │  │  • 20+ Business Svc     │  │  • Backtest Engine       │        │  │
│  │  │  • Alpaca Client        │  │  • Factor Engine         │        │  │
│  │  │  • Data Source          │  │  • Execution Engine      │        │  │
│  │  │  • Alert Service        │  │  • Risk Engine           │        │  │
│  │  └─────────────────────────┘  └─────────────────────────┘        │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                       Data & Infrastructure                        │  │
│  │                                                                    │  │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐   │  │
│  │  │PostgreSQL│ │  Redis  │ │ Celery  │ │ Docker  │ │Prometheus│   │  │
│  │  │+Timescale│ │ Cache   │ │ Worker  │ │ Compose │ │ Metrics │   │  │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘   │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                       External Services                            │  │
│  │                                                                    │  │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐               │  │
│  │  │ Alpaca  │ │ Polygon │ │  FRED   │ │ YFinance│               │  │
│  │  │ Markets │ │   API   │ │   API   │ │   API   │               │  │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘               │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 技术栈详情

#### 后端技术栈

| 类别 | 技术 | 版本 | 用途 |
|------|------|------|------|
| Web 框架 | FastAPI | 0.109+ | 异步 Web API |
| ORM | SQLAlchemy | 2.0+ | 数据库访问 |
| 数据库 | PostgreSQL + TimescaleDB | 15+ | 关系型 + 时序数据 |
| 缓存 | Redis | 7+ | 缓存/队列/会话 |
| 任务队列 | Celery | 5.3+ | 异步任务处理 |
| 数据处理 | Pandas/NumPy/SciPy | Latest | 数值计算 |
| 性能优化 | Numba | Latest | JIT 编译加速 |
| 券商集成 | alpaca-py | 0.18+ | 交易执行 |
| 日志 | structlog | Latest | 结构化日志 |
| 配置 | Pydantic | 2.5+ | 配置验证 |

#### 前端技术栈

| 类别 | 技术 | 版本 | 用途 |
|------|------|------|------|
| 框架 | React | 18+ | UI 框架 |
| 语言 | TypeScript | 5.3+ | 类型安全 |
| 构建工具 | Vite | 5.0+ | 快速构建 |
| UI 库 | Ant Design | 5+ | 组件库 |
| 样式 | TailwindCSS | 3+ | 原子化 CSS |
| 图表 | ECharts | 5+ | 数据可视化 |
| 状态管理 | Zustand | Latest | 轻量状态管理 |
| 数据请求 | React Query | 5+ | 服务端状态 |
| 路由 | React Router | 6+ | SPA 路由 |

### 2.3 目录结构

```
quantvision-v2/
├── backend/                    # 后端服务
│   ├── app/                   # 应用代码
│   │   ├── api/              # API 路由
│   │   ├── core/             # 核心配置
│   │   ├── models/           # ORM 模型
│   │   ├── schemas/          # 请求/响应模型
│   │   ├── services/         # 业务逻辑
│   │   ├── backtest/         # 回测引擎
│   │   ├── factor_engine/    # 因子计算
│   │   ├── risk/             # 风险管理
│   │   ├── execution/        # 执行算法
│   │   ├── validation/       # 策略验证
│   │   ├── strategy/         # 策略框架
│   │   ├── tasks/            # Celery 任务
│   │   └── websocket/        # WebSocket
│   ├── alembic/              # 数据库迁移
│   ├── tests/                # 测试代码
│   └── requirements.txt      # Python 依赖
│
├── frontend/                   # 前端应用
│   ├── src/
│   │   ├── pages/            # 页面组件
│   │   ├── components/       # UI 组件
│   │   ├── hooks/            # 自定义 Hooks
│   │   ├── services/         # API 服务
│   │   ├── types/            # TypeScript 类型
│   │   ├── utils/            # 工具函数
│   │   └── styles/           # 样式文件
│   ├── public/               # 静态资源
│   └── package.json          # Node 依赖
│
├── docs/                       # 项目文档
├── .github/                    # CI/CD 配置
├── docker-compose.yml          # 容器编排
└── .env.example               # 环境变量模板
```

---

## 3. 后端详情

### 3.1 核心模块 (core/)

| 文件 | 功能 |
|------|------|
| `config.py` | Pydantic Settings 配置管理 |
| `config_production.py` | 生产环境配置 |
| `config_validation.py` | 配置验证器 |
| `database.py` | SQLAlchemy 异步引擎 |
| `redis.py` | Redis 客户端 |
| `logging.py` | structlog 结构化日志 |
| `metrics.py` | Prometheus 指标收集 |
| `security.py` | JWT/CORS/限流/安全头 |

### 3.2 数据模型 (models/)

| 模型 | 说明 |
|------|------|
| `base.py` | 基类 (UUID, Timestamp, SoftDelete) |
| `strategy_v2.py` | 7步策略配置 (JSONB 字段) |
| `universe.py` | 投资组合定义 |
| `factor_cache.py` | 因子缓存 |
| `market_data.py` | 市场行情 (TimescaleDB) |
| `financial_data.py` | 财务数据 |
| `data_lineage.py` | 数据血缘追踪 |

### 3.3 业务服务 (services/) - 20+ 服务

| 服务 | 功能 |
|------|------|
| `alpaca_client.py` | Alpaca 券商集成 |
| `data_source.py` | 多数据源提供者 |
| `factor_cache_service.py` | 因子缓存管理 |
| `deployment_service.py` | 策略部署管理 |
| `drift_service.py` | 策略漂移监控 |
| `signal_service.py` | 信号生成 |
| `attribution_service.py` | 交易归因分析 |
| `conflict_service.py` | 策略冲突检测 |
| `pdt_service.py` | PDT 规则执行 |
| `position_service.py` | 持仓管理 |
| `alert_service.py` | 风险预警 |
| `manual_trade_service.py` | 手动交易 |
| `replay_engine_service.py` | 策略回放 |
| `realtime_monitor.py` | 实时监控 |
| `notification_service.py` | 多渠道通知 |
| `template_service.py` | 策略模板 |

### 3.4 回测引擎 (backtest/)

```python
backtest/
├── engine.py           # 核心回测执行
├── broker.py           # 券商模拟
├── portfolio.py        # 组合管理
├── performance.py      # 绩效计算
└── data_handler.py     # 数据处理
```

**支持特性**:
- 事件驱动回测架构
- 滑点/手续费模拟
- 多资产组合
- 现金管理
- 绩效归因

### 3.5 因子引擎 (factor_engine/)

```python
factor_engine/
├── operators.py        # 45K+ 因子算子库
├── factor_tester.py    # 因子测试
├── preprocessor.py     # 数据预处理
└── cache.py            # 因子缓存
```

**因子类别**:
- 动量因子 (Momentum)
- 价值因子 (Value)
- 质量因子 (Quality)
- 波动因子 (Volatility)
- 流动性因子 (Liquidity)
- 技术因子 (Technical)

### 3.6 风险管理 (risk/)

```python
risk/
├── var_calculator.py       # VaR 计算 (历史/参数/蒙特卡洛)
├── factor_exposure.py      # 因子暴露分析
├── circuit_breaker.py      # 熔断机制
├── monitor.py              # 风险监控
└── stress_test.py          # 压力测试
```

### 3.7 执行算法 (execution/)

| 算法 | 说明 |
|------|------|
| `vwap.py` | 成交量加权平均价 |
| `twap.py` | 时间加权平均价 |
| `pov.py` | 成交量百分比 |
| `tca.py` | 交易成本分析 |
| `order_manager.py` | 订单管理 |

### 3.8 策略验证 (validation/)

| 模块 | 功能 |
|------|------|
| `walk_forward.py` | Walk-Forward 验证 |
| `overfitting_detector.py` | 过拟合检测 |
| `lookahead_detector.py` | 前视偏差检测 |
| `data_snooping.py` | 数据窥探检测 |
| `robustness.py` | 鲁棒性测试 |
| `survivorship_detector.py` | 幸存者偏差检测 |

### 3.9 WebSocket 服务

| 端点 | 功能 |
|------|------|
| `/ws/trading` | 交易流 (订单/成交/取消) |
| `/ws/alpaca` | Alpaca 市场数据流 |
| `/ws/polygon` | Polygon 数据流 |

---

## 4. 前端详情

### 4.1 页面组件 (pages/) - 11 页面

| 页面 | 路由 | 功能 |
|------|------|------|
| Dashboard | `/dashboard` | 组合总览、关键指标、收益曲线 |
| MyStrategies | `/my-strategies` | 策略列表、管理、部署 |
| FactorLab | `/factor-lab` | 因子研究、测试、可视化 |
| StrategyBuilder | `/strategy` | 7步策略构建器 |
| BacktestCenter | `/backtest` | 回测执行、结果分析 |
| Trading | `/trading` | 实时交易监控 (三栏布局) |
| TradingStream | `/trading/stream` | 交易流实时推送 |
| RiskCenter | `/risk` | 风险分析仪表盘 |
| Templates | `/templates` | 策略模板库 |
| StrategyReplay | `/strategy/replay` | 策略回放调试 |
| Intraday | `/intraday` | 日内交易工具 |

### 4.2 组件库 (components/) - 30 组件目录

#### 核心业务组件

| 目录 | 组件数 | 功能 |
|------|--------|------|
| `StrategyBuilder/` | 10+ | 7步策略构建 UI |
| `TradingMonitor/` | 8+ | 交易监控面板 |
| `Chart/` | 6+ | ECharts 图表封装 |
| `RiskDashboard/` | 5+ | 风险指标展示 |
| `Factor/` | 5+ | 因子管理 |
| `SignalRadar/` | 4+ | 信号雷达 |
| `Deployment/` | 4+ | 部署工作流 |
| `Attribution/` | 3+ | 归因分析 |

#### 通用组件

| 目录 | 组件 |
|------|------|
| `ui/` | Card, Button, NumberDisplay, LoadingSpinner, FinancialComponents |
| `common/` | ErrorBoundary, LoadingStates, HealthStatus, EnvironmentSwitch |

### 4.3 自定义 Hooks (hooks/) - 12 个

| Hook | 功能 |
|------|------|
| `useAccount` | 账户信息管理 |
| `useDashboard` | Dashboard 数据聚合 |
| `useHealth` | 后端健康检查 |
| `useNotifications` | 通知管理 |
| `useOrders` | 订单管理 |
| `usePerformance` | 性能指标监控 |
| `useRealtime` | WebSocket 实时更新 |
| `useRealTimeQuote` | 实时行情 |
| `useTradingStream` | 交易流数据 |
| `usePreMarketScanner` | 盘前扫描 |
| `useChartTheme` | 图表主题 |

### 4.4 类型定义 (types/) - 21 文件

```typescript
types/
├── ai.ts              // AI 助手
├── alert.ts           // 预警
├── attribution.ts     // 归因
├── backtest.ts        // 回测
├── conflict.ts        // 冲突检测
├── deployment.ts      // 部署
├── drift.ts           // 漂移监控
├── factorValidation.ts // 因子验证
├── marketData.ts      // 市场数据
├── pdt.ts             // PDT 规则
├── position.ts        // 持仓
├── preMarket.ts       // 盘前
├── replay.ts          // 回放
├── risk.ts            // 风险
├── signalRadar.ts     // 信号雷达
├── strategy.ts        // 策略
├── strategyTemplate.ts // 模板
├── tradeAttribution.ts // 交易归因
├── trading.ts         // 交易
├── tradingCost.ts     // 交易成本
└── workflow.ts        // 工作流
```

### 4.5 API 服务 (services/) - 13 模块

| 服务 | 功能 |
|------|------|
| `api.ts` | 基础 fetch 封装 |
| `apiClient.ts` | 增强 API 客户端 (重试/超时/错误处理) |
| `backendApi.ts` | 后端 API 集成 |
| `alpacaAuth.ts` | Alpaca 认证 |
| `alpacaTrading.ts` | Alpaca 交易 API |
| `alpacaWebSocket.ts` | Alpaca WebSocket |
| `backendWebSocket.ts` | 后端 WebSocket |
| `polygonApi.ts` | Polygon API |
| `polygonWebSocket.ts` | Polygon WebSocket |
| `deploymentService.ts` | 部署服务 |
| `preMarketService.ts` | 盘前服务 |
| `storageService.ts` | 本地存储 |
| `strategyService.ts` | 策略管理 |

### 4.6 UI 优化特性

- **懒加载**: 页面级代码分割
- **错误边界**: 全局 + 页面 + 面板级
- **骨架屏**: 11+ 种加载状态组件
- **响应式**: 移动端/平板端/桌面端适配
- **金融组件**: PriceTicker, PortfolioCard, MarketStatus 等
- **性能优化**: React.memo, useCallback, useMemo

---

## 5. 数据库设计

### 5.1 数据库架构

- **主数据库**: PostgreSQL 15+
- **时序扩展**: TimescaleDB (市场数据优化)
- **迁移工具**: Alembic (异步支持)

### 5.2 核心表结构

#### strategies_v2 (策略配置表)

```sql
CREATE TABLE strategies_v2 (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'draft',

    -- 7步配置 (JSONB)
    universe_config JSONB,      -- 投资域配置
    alpha_config JSONB,         -- Alpha 因子配置
    signal_config JSONB,        -- 信号生成配置
    risk_config JSONB,          -- 风险管理配置
    portfolio_config JSONB,     -- 组合优化配置
    execution_config JSONB,     -- 执行算法配置
    monitor_config JSONB,       -- 监控预警配置

    -- 元数据
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    is_deleted BOOLEAN DEFAULT FALSE
);
```

#### market_data (市场数据表 - TimescaleDB)

```sql
CREATE TABLE market_data (
    time TIMESTAMPTZ NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    open DECIMAL(18,6),
    high DECIMAL(18,6),
    low DECIMAL(18,6),
    close DECIMAL(18,6),
    volume BIGINT,
    vwap DECIMAL(18,6),
    PRIMARY KEY (time, symbol)
);

-- 创建 hypertable
SELECT create_hypertable('market_data', 'time');
```

#### factor_cache (因子缓存表)

```sql
CREATE TABLE factor_cache (
    id UUID PRIMARY KEY,
    factor_name VARCHAR(100) NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    date DATE NOT NULL,
    value DECIMAL(18,8),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE (factor_name, symbol, date)
);
```

### 5.3 索引策略

- 主键: UUID (分布式友好)
- 时序索引: TimescaleDB 自动优化
- 组合索引: (symbol, date), (strategy_id, status)
- JSONB 索引: GIN 索引支持 JSON 查询

---

## 6. API 接口清单

### 6.1 API 模块统计

| 类别 | 模块数 | 端点数 |
|------|--------|--------|
| 核心 API | 10 | 40+ |
| 交易 API | 5 | 25+ |
| 风险 API | 3 | 15+ |
| 功能 API | 15 | 50+ |
| **总计** | **33** | **130+** |

### 6.2 核心 API 端点

#### 健康检查 `/api/v1/health`

```
GET  /health              基本健康检查
GET  /health/live         存活探针 (Kubernetes)
GET  /health/ready        就绪探针 (Kubernetes)
GET  /health/detailed     详细健康检查 (DB/Redis/外部服务)
GET  /health/metrics      健康指标
```

#### 策略管理 `/api/v1/strategies/v2`

```
GET    /                  获取策略列表
POST   /                  创建策略
GET    /{id}              获取策略详情
PATCH  /{id}              更新策略
DELETE /{id}              删除策略
POST   /{id}/validate     验证策略
POST   /{id}/run-backtest 运行回测
POST   /{id}/deploy       部署策略
```

#### 因子管理 `/api/v1/factors`

```
GET    /                  获取因子列表
GET    /categories        获取因子分类
GET    /{name}            获取因子详情
POST   /compute           计算因子值
POST   /backtest          因子回测
GET    /correlation       因子相关性
```

#### 回测中心 `/api/v1/backtests`

```
POST   /                  创建回测任务
GET    /{id}              获取回测状态
GET    /{id}/results      获取回测结果
GET    /{id}/metrics      获取绩效指标
GET    /{id}/trades       获取交易记录
GET    /{id}/positions    获取持仓历史
```

### 6.3 交易 API 端点

#### 实时监控 `/api/v1/realtime`

```
GET    /status            获取实时状态
GET    /positions         获取持仓详情
GET    /orders            获取订单列表
GET    /clock             获取市场时钟
GET    /account           获取账户信息
POST   /monitor/start     启动监控
POST   /monitor/stop      停止监控
POST   /orders            提交订单
DELETE /orders/{id}       取消订单
DELETE /positions/{symbol} 平仓
DELETE /positions         全部平仓
```

#### 执行算法 `/api/v1/execution`

```
POST   /vwap              VWAP 执行
POST   /twap              TWAP 执行
POST   /pov               POV 执行
GET    /algorithms        获取算法列表
GET    /tca/{order_id}    交易成本分析
```

#### 手动交易 `/api/v1/manual-trade`

```
POST   /order             提交手动订单
GET    /recent            最近手动交易
POST   /quick-close       快速平仓
```

### 6.4 风险 API 端点

#### 风险分析 `/api/v1/risk`

```
GET    /var               获取 VaR
GET    /exposure          获取因子暴露
GET    /concentration     获取集中度
GET    /correlation       获取相关性矩阵
POST   /stress-test       运行压力测试
```

#### 预警管理 `/api/v1/alerts`

```
GET    /                  获取预警列表
GET    /unread-count      未读数量
POST   /{id}/read         标记已读
POST   /mark-all-read     全部已读
GET    /config            获取预警配置
PUT    /config            更新预警配置
POST   /test-email        测试邮件
```

### 6.5 功能 API 端点

#### 信号雷达 `/api/v1/signal-radar`

```
GET    /{strategy_id}            获取策略信号
GET    /{strategy_id}/summary    信号汇总
POST   /{strategy_id}/refresh    刷新信号
```

#### 部署管理 `/api/v1/deployment`

```
GET    /                  获取部署列表
POST   /                  创建部署
GET    /{id}              获取部署详情
PATCH  /{id}              更新部署
DELETE /{id}              删除部署
POST   /{id}/start        启动部署
POST   /{id}/stop         停止部署
```

#### 策略模板 `/api/v1/templates`

```
GET    /                  获取模板列表
GET    /categories        获取模板分类
GET    /{id}              获取模板详情
POST   /{id}/apply        应用模板
```

#### 通知管理 `/api/v1/notifications`

```
GET    /rules             获取通知规则
PUT    /rules/{id}        更新规则
POST   /rules/{id}/toggle 切换规则状态
GET    /history           通知历史
POST   /test              测试通知
GET    /stats             通知统计
```

#### 日志与指标

```
POST   /api/v1/logs              批量日志上报
POST   /api/v1/logs/error        错误即时上报
GET    /api/v1/metrics           JSON 格式指标
GET    /api/v1/metrics/prometheus Prometheus 格式
GET    /api/v1/metrics/summary   指标摘要
```

---

## 7. 核心功能模块

### 7.1 七步策略构建器

QuantVision 的核心特色是 **7步策略构建框架**，将量化策略分解为可配置的模块：

```
┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐
│ Step 1  │──▶│ Step 2  │──▶│ Step 3  │──▶│ Step 4  │
│ Universe│   │  Alpha  │   │ Signal  │   │  Risk   │
│ 投资域  │   │因子配置 │   │信号生成 │   │风险管理 │
└─────────┘   └─────────┘   └─────────┘   └─────────┘
                                              │
┌─────────┐   ┌─────────┐   ┌─────────┐      │
│ Step 7  │◀──│ Step 6  │◀──│ Step 5  │◀─────┘
│ Monitor │   │Execution│   │Portfolio│
│监控预警 │   │执行算法 │   │组合优化 │
└─────────┘   └─────────┘   └─────────┘
```

| 步骤 | 配置项 |
|------|--------|
| **Step 1: Universe** | 市场选择、指数成分、市值筛选、流动性筛选、行业排除 |
| **Step 2: Alpha** | 因子选择、权重配置、标准化方法、中性化处理 |
| **Step 3: Signal** | 信号阈值、信号强度、买卖规则、信号有效期 |
| **Step 4: Risk** | 止损比例、最大回撤、VaR 限制、持仓限制 |
| **Step 5: Portfolio** | 权重算法、再平衡频率、约束条件、现金比例 |
| **Step 6: Execution** | 执行算法、滑点模型、手续费模型、执行窗口 |
| **Step 7: Monitor** | 预警规则、漂移阈值、通知渠道、检查频率 |

### 7.2 回测验证系统

#### 验证方法

| 方法 | 说明 |
|------|------|
| Walk-Forward | 滚动窗口回测，避免过拟合 |
| 过拟合检测 | 检测策略是否过度拟合历史数据 |
| 前视偏差 | 检测是否使用了未来数据 |
| 幸存者偏差 | 检测是否只使用了存活股票 |
| 数据窥探 | 检测是否多次测试同一数据 |
| 鲁棒性测试 | 参数敏感性分析 |

#### 绩效指标

| 指标 | 说明 |
|------|------|
| 总收益率 | Total Return |
| 年化收益 | CAGR |
| 夏普比率 | Sharpe Ratio |
| 索提诺比率 | Sortino Ratio |
| 最大回撤 | Maximum Drawdown |
| 卡玛比率 | Calmar Ratio |
| 胜率 | Win Rate |
| 盈亏比 | Profit Factor |
| 换手率 | Turnover |
| Alpha/Beta | 相对基准 |

### 7.3 风险管理系统

#### VaR 计算

- **历史模拟法**: 基于历史收益分布
- **参数法**: 假设正态分布
- **蒙特卡洛**: 随机模拟

#### 风险控制

| 机制 | 说明 |
|------|------|
| 止损 | 个股/组合止损 |
| 熔断 | 日亏损/回撤熔断 |
| 限仓 | 单股/行业/总仓位限制 |
| PDT | Pattern Day Trader 规则 |
| 压力测试 | 极端情景分析 |

### 7.4 实时交易系统

#### 交易流程

```
信号生成 → 风控检查 → 订单拆分 → 算法执行 → 成交确认 → 持仓更新
                                    │
                                    ▼
                            ┌───────────────┐
                            │   执行算法    │
                            ├───────────────┤
                            │ VWAP - 跟随量 │
                            │ TWAP - 时间均│
                            │ POV - 量比例  │
                            └───────────────┘
```

#### 实时监控

- WebSocket 推送订单/成交状态
- 持仓实时更新
- 盈亏实时计算
- 风险指标实时监控

---

## 8. 基础设施与部署

### 8.1 Docker 容器化

```yaml
# docker-compose.yml 主要服务
services:
  backend:
    build: ./backend
    ports: ["8000:8000"]
    depends_on: [postgres, redis]

  frontend:
    build: ./frontend
    ports: ["80:80"]

  postgres:
    image: timescale/timescaledb:latest-pg15
    ports: ["5432:5432"]

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]

  celery_worker:
    build: ./backend
    command: celery -A app.tasks.celery_app worker

  celery_beat:
    build: ./backend
    command: celery -A app.tasks.celery_app beat
```

### 8.2 CI/CD 流水线

```
┌────────┐    ┌────────┐    ┌────────┐    ┌────────┐    ┌────────┐
│  Lint  │───▶│  Test  │───▶│ Build  │───▶│  Scan  │───▶│ Deploy │
└────────┘    └────────┘    └────────┘    └────────┘    └────────┘
    │              │              │              │              │
    ▼              ▼              ▼              ▼              ▼
 Ruff/ESLint   pytest/Jest   Docker Build    Trivy      ECS Update
 Black         Coverage      Push to GHCR   Security   Blue-Green
 TypeCheck     Backend/FE                    SARIF     Staging/Prod
```

### 8.3 环境配置

#### 必需环境变量

```bash
# 数据库
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/quantvision

# Redis
REDIS_URL=redis://localhost:6379/0

# Alpaca
ALPACA_API_KEY=your_key
ALPACA_SECRET_KEY=your_secret
ALPACA_PAPER=true

# 安全
SECRET_KEY=your-secret-key-min-32-chars
JWT_EXPIRE_MINUTES=60

# 日志
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### 8.4 监控与告警

#### 日志系统

- structlog 结构化日志
- Correlation ID 全链路追踪
- 前端日志批量上报 (30秒/10条)

#### 指标监控

- Prometheus 兼容格式
- HTTP 请求计数/延迟
- 数据库查询延迟
- WebSocket 连接数
- 业务指标 (交易/策略/信号)

#### 告警通道

- WebSocket 实时推送
- Email 邮件通知
- Webhook 集成

### 8.5 安全措施

| 措施 | 实现 |
|------|------|
| HTTPS | Strict-Transport-Security |
| CORS | 白名单配置 |
| 限流 | 100 次/分钟/IP |
| 安全头 | X-Frame-Options, CSP 等 |
| 请求验证 | Content-Type, Content-Length |
| 密钥管理 | 最小 32 字符，默认密码检测 |

---

## 9. 开发阶段回顾

### 9.1 版本历程

| 版本 | 日期 | 主要内容 |
|------|------|----------|
| v2.0.0 | 2025-12 | 核心功能完成，7步策略框架 |
| v2.1.0 | 2026-01 | 系统加固，生产就绪 |

### 9.2 Phase 1: 核心功能 (Sprint 1-7)

- 因子引擎开发
- 策略框架 v2 设计
- 回测引擎实现
- 基础 UI 组件

### 9.3 Phase 2: 功能集成 (Sprint 8-11)

- Alpaca 券商集成
- WebSocket 实时推送
- 风险管理模块
- 信号雷达系统
- 部署管理系统

### 9.4 Phase 3: 系统加固 (Sprint 12-14)

#### Sprint 12: 错误处理与健康检查
- API 错误处理增强
- 重试机制实现
- 前端错误边界
- 加载状态优化
- 健康检查端点

#### Sprint 13: 日志与监控
- structlog 结构化日志
- 前端日志收集
- Prometheus 指标
- 多渠道告警系统

#### Sprint 14: 生产部署
- Docker 多阶段构建
- 环境配置验证
- Alembic 异步迁移
- CI/CD 流水线
- 安全中间件

### 9.5 UI 优化阶段

- 全局 ErrorBoundary
- Dashboard API 集成
- Trading 页面性能优化
- 金融级 UI 组件
- 响应式布局

---

## 10. 项目统计

### 10.1 代码统计

| 类别 | 数量 |
|------|------|
| **后端** | |
| API 模块 | 33 |
| API 端点 | 130+ |
| 服务模块 | 20+ |
| Schema 文件 | 24+ |
| 核心模块 | 12 |
| **前端** | |
| 页面 | 11 |
| 组件目录 | 30 |
| 组件文件 | 89+ |
| Hooks | 12 |
| 类型定义 | 21 |
| 服务模块 | 13 |
| **文档** | |
| 报告文件 | 15+ |

### 10.2 功能统计

| 类别 | 数量 |
|------|------|
| 因子算子 | 45K+ |
| 风险模块 | 5 |
| 执行算法 | 5 |
| 验证方法 | 6 |
| 数据源 | 4 (Alpaca/Polygon/FRED/YFinance) |
| 通知渠道 | 3 (WebSocket/Email/Webhook) |

### 10.3 技术债务

| 项目 | 优先级 | 状态 |
|------|--------|------|
| 单元测试覆盖 | 高 | 待完成 |
| E2E 测试 | 中 | 待完成 |
| 性能测试 | 中 | 待完成 |
| 安全审计 | 高 | 待完成 |
| API 文档完善 | 中 | 进行中 |

---

## 11. 附录

### 11.1 命令参考

```bash
# 启动开发环境
docker-compose up -d

# 启动生产环境
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# 数据库迁移
cd backend && alembic upgrade head

# 生成新迁移
cd backend && alembic revision --autogenerate -m "description"

# 后端开发
cd backend && uvicorn app.main:app --reload --port 8000

# 前端开发
cd frontend && npm run dev

# 健康检查
curl http://localhost:8000/api/v1/health/detailed

# 查看日志
docker-compose logs -f backend
```

### 11.2 环境变量清单

参见 `.env.example` 文件，包含所有必需和可选配置项。

### 11.3 相关文档

| 文档 | 说明 |
|------|------|
| `Phase3_Completion_Report.md` | Phase 3 完成报告 |
| `UI_Optimization_Report.md` | UI 优化报告 |
| `Project-Completion-Audit-Report.md` | 项目审计报告 |
| `QuantVision-v2.1-PRD-vs-Implementation-Analysis.md` | PRD 对比分析 |

### 11.4 联系方式

- 项目仓库: quantvision-v2
- 问题反馈: GitHub Issues

---

**QuantVision v2.1 - 机构级量化投资平台**

*文档生成日期: 2026-01-09*
