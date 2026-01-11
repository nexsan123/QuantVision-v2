# QuantVision v2.2 机构级升级计划

## 项目概述

**版本**: v2.2 - 机构级升级
**目标**: 建立完整的量化交易生命周期，实现从研究到实盘的无缝衔接
**预计周期**: 64个工作日 (约3个月)

---

## 核心使用流程

```
┌─────────────────────────────────────────────────────────────────────┐
│                     量化投资完整生命周期                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   阶段1          阶段2          阶段3          阶段4          阶段5   │
│  因子研究   →   策略构建   →   回测验证   →   模拟交易   →   实盘部署  │
│  FactorLab     Strategy      Backtest      Paper         Live      │
│                Builder       Center        Trading       Trading    │
│     ↓             ↓             ↓             ↓             ↓       │
│  发现Alpha    组合因子      验证策略      验证执行      真实交易    │
│  验证因子    设置风控      优化参数      测试系统      监控运维    │
│                                                                     │
│                           阶段6: 监控运维 (贯穿全程)                  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: 因子研究增强

### Spec 1.1: 因子验证完整实现

**目标**: 实现完整的因子有效性验证流程

**当前状态**:
- IC分析: 框架存在，后端计算缺失
- 分组回测: 框架存在，后端计算缺失
- 因子库: 仅显示默认因子

**实现任务**:

| 任务ID | 任务描述 | 优先级 | 预计工时 |
|--------|----------|--------|----------|
| 1.1.1 | 完成 `/api/v1/factors/analyze/ic` 后端实现 | P0 | 2天 |
| 1.1.2 | 完成 `/api/v1/factors/analyze/group` 后端实现 | P0 | 2天 |
| 1.1.3 | 集成 LookaheadDetector (前视偏差检测) | P0 | 1天 |
| 1.1.4 | 集成 SurvivorshipDetector (生存偏差检测) | P1 | 1天 |
| 1.1.5 | 实现因子相关性分析 (Spearman/Pearson) | P1 | 2天 |
| 1.1.6 | 实现因子对标工具 | P2 | 2天 |

**数据流**:
```
因子表达式输入
    ↓
后端验证与编译 (factor_validation_service.py)
    ↓
历史数据加载 (Polygon API → 本地缓存)
    ↓
IC分析引擎计算 → 返回 IC/IR/t-stat
    ↓
分组回测引擎计算 → 返回分组收益
    ↓
前视偏差检测 → 警告或通过
    ↓
前端展示结果
```

**验收标准**:
- [ ] IC分析返回完整指标 (IC均值、IC标准差、IR、t统计量)
- [ ] 分组回测返回完整收益曲线
- [ ] 前视偏差检测集成并显示警告
- [ ] 因子库显示真实因子列表 (20+个)

---

## Phase 2: 回测引擎核心实现

### Spec 2.1: BacktestEngine 完整实现

**目标**: 实现事件驱动的回测引擎核心

**当前状态**:
- 类定义存在，逻辑为空
- 权益曲线API缺失
- 热力图API缺失

**实现任务**:

| 任务ID | 任务描述 | 优先级 | 预计工时 |
|--------|----------|--------|----------|
| 2.1.1 | 实现 BacktestEngine.run() 事件循环 | P0 | 3天 |
| 2.1.2 | 集成信号生成逻辑 | P0 | 2天 |
| 2.1.3 | 集成订单执行和滑点模型 | P0 | 2天 |
| 2.1.4 | 实现 `/backtests/{id}/equity-curve` API | P0 | 1天 |
| 2.1.5 | 实现 `/backtests/{id}/heatmap` API | P0 | 1天 |
| 2.1.6 | 实现 `/backtests/{id}/trades` API | P0 | 1天 |
| 2.1.7 | 集成 Walk-Forward 分析 | P1 | 3天 |
| 2.1.8 | 实现参数网格搜索 | P1 | 2天 |
| 2.1.9 | 集成过拟合检测 (Deflated Sharpe Ratio) | P1 | 2天 |

**核心代码框架**:
```python
# backend/app/backtest/engine.py

class BacktestEngine:
    def run(self, config: BacktestConfig) -> BacktestResult:
        result = BacktestResult(config=config)
        portfolio = Portfolio(initial_capital=config.initial_capital)
        broker = SimulatedBroker(config)

        for date in self._generate_dates(config):
            # 1. 加载当日数据
            market_data = self.data_source.get_ohlcv(date)
            factors = self.factor_engine.compute(date)

            # 2. 生成信号
            signals = self.strategy.generate_signals(factors, market_data)

            # 3. 调仓
            if self._should_rebalance(date, config.rebalance_freq):
                orders = self.strategy.generate_orders(signals, portfolio)
                portfolio = broker.execute_orders(orders, market_data)

            # 4. 更新绩效
            portfolio.update_prices(market_data)
            result.equity_curve[date] = portfolio.equity
            result.trades_history.extend(broker.get_trades(date))

        # 5. 计算绩效指标
        result = self._calculate_metrics(result)
        return result
```

**验收标准**:
- [ ] 回测可正常运行并生成结果
- [ ] 权益曲线图表正确显示
- [ ] 月度热力图正确显示
- [ ] 交易记录完整准确
- [ ] 绩效指标计算正确

---

## Phase 3: 模拟交易集成

### Spec 3.1: Paper Trading 完整实现

**目标**: 实现与 Alpaca Paper 账户的完整集成

**当前状态**:
- 部署向导UI完整
- 部署启动/停止逻辑缺失
- Paper账户创建缺失
- 实时数据推送缺失

**实现任务**:

| 任务ID | 任务描述 | 优先级 | 预计工时 |
|--------|----------|--------|----------|
| 3.1.1 | 实现 deployment_service.start_deployment() | P0 | 2天 |
| 3.1.2 | 实现 deployment_service.stop_deployment() | P0 | 1天 |
| 3.1.3 | 实现 Alpaca Paper 账户初始化 | P0 | 2天 |
| 3.1.4 | 实现策略执行循环 (DeploymentExecutor) | P0 | 3天 |
| 3.1.5 | 实现 WebSocket 实时数据推送 | P0 | 3天 |
| 3.1.6 | 实现订单自动提交 | P1 | 2天 |
| 3.1.7 | 实现实时P&L更新 | P1 | 2天 |
| 3.1.8 | 实现 Paper vs 回测 对标分析 | P2 | 2天 |

**核心数据流**:
```
部署启动
    ↓
初始化 Alpaca Paper 账户
    ↓
启动策略执行循环 (Celery Worker)
    ├─→ 订阅实时数据 (Alpaca WebSocket)
    ├─→ 因子实时计算
    ├─→ 信号生成
    ├─→ 订单提交 (自动/手动)
    └─→ 持仓/订单同步
    ↓
WebSocket 推送到前端
    ├─→ PositionMonitorPanel
    ├─→ OrderPanel
    └─→ SignalRadarPanel
```

**验收标准**:
- [ ] 部署可正常启动和停止
- [ ] Paper账户订单正确执行
- [ ] 持仓数据实时更新
- [ ] 订单状态实时同步
- [ ] P&L数据准确计算

---

## Phase 4: 风险管理完善

### Spec 4.1: 熔断器与风控系统

**目标**: 实现完整的风险管理体系

**当前状态**:
- 熔断器框架存在，触发逻辑缺失
- PDT检查不完整
- 风险分解缺失

**实现任务**:

| 任务ID | 任务描述 | 优先级 | 预计工时 |
|--------|----------|--------|----------|
| 4.1.1 | 实现熔断器触发逻辑 (CircuitBreaker) | P0 | 2天 |
| 4.1.2 | 完善PDT规则检查 | P0 | 1天 |
| 4.1.3 | 实现实时风险监控计算 | P0 | 2天 |
| 4.1.4 | 实现风险恢复机制 | P1 | 2天 |
| 4.1.5 | 实现 Fama-French 因子模型 | P1 | 3天 |
| 4.1.6 | 实现 VaR/CVaR 计算 | P2 | 2天 |
| 4.1.7 | 实现压力测试框架 | P2 | 3天 |

**熔断器规则**:
```python
class CircuitBreaker:
    # 触发条件
    rules = {
        'daily_loss': -0.03,      # 日内亏损 3%
        'weekly_drawdown': -0.08,  # 周回撤 8%
        'max_drawdown': -0.15,     # 最大回撤 15%
        'volatility_spike': 2.0,   # 波动率激增 2倍
    }

    # 恢复策略
    recovery = {
        'partial_close': 0.5,     # 部分平仓比例
        'full_close': True,       # 完全平仓
        'cooldown_period': 3600,  # 冷却期(秒)
    }
```

**验收标准**:
- [ ] 熔断器触发时自动停止交易
- [ ] PDT规则检查准确
- [ ] 风险指标实时更新
- [ ] 风险告警正确触发

---

## Phase 5: 监控运维增强

### Spec 5.1: 实时监控与告警

**目标**: 实现完整的监控运维能力

**当前状态**:
- 监控UI基本完整
- WebSocket推送缺失
- 邮件/短信通知缺失
- 策略漂移检测不完整

**实现任务**:

| 任务ID | 任务描述 | 优先级 | 预计工时 |
|--------|----------|--------|----------|
| 5.1.1 | 实现 WebSocket 实时数据推送 | P0 | 3天 |
| 5.1.2 | 实现邮件通知 (SMTP集成) | P0 | 2天 |
| 5.1.3 | 实现短信告警 (可选) | P1 | 2天 |
| 5.1.4 | 完善策略漂移检测 | P1 | 2天 |
| 5.1.5 | 实现性能报告自动生成 | P1 | 3天 |
| 5.1.6 | 实现Slack/钉钉集成 | P2 | 2天 |

**告警分发流程**:
```
风险指标超限
    ↓
AlertService.trigger()
    ├─→ UI推送 (WebSocket - 立即)
    ├─→ 邮件通知 (重要事件)
    ├─→ 短信告警 (紧急事件)
    └─→ Slack通知 (团队协作)
```

**验收标准**:
- [ ] 数据实时推送 (<1秒延迟)
- [ ] 告警邮件正确发送
- [ ] 策略漂移检测准确
- [ ] 报告自动生成

---

## Phase 6: 用户体验优化

### Spec 6.1: UI/UX 完善

**目标**: 提升专业性和易用性

**实现任务**:

| 任务ID | 任务描述 | 优先级 | 预计工时 |
|--------|----------|--------|----------|
| 6.1.1 | 添加全局数据源状态指示器 | P0 | 1天 |
| 6.1.2 | 优化加载状态和错误提示 | P0 | 1天 |
| 6.1.3 | 实现策略模板库 | P1 | 3天 |
| 6.1.4 | 实现AI助手完整集成 | P1 | 5天 |
| 6.1.5 | 实现策略版本管理 | P2 | 3天 |
| 6.1.6 | 实现策略对比工具 | P2 | 2天 |

**验收标准**:
- [ ] 所有页面显示数据源状态
- [ ] 加载和错误状态友好
- [ ] 模板库可用
- [ ] AI助手可对话

---

## 执行时间表

### Sprint 规划

| Sprint | 周期 | 主要任务 | 产出 |
|--------|------|----------|------|
| S1 | Week 1-2 | Phase 2.1 (回测引擎) | 回测功能可用 |
| S2 | Week 3-4 | Phase 1.1 (因子验证) | 因子研究完整 |
| S3 | Week 5-6 | Phase 3.1 (模拟交易) | Paper Trading可用 |
| S4 | Week 7-8 | Phase 4.1 (风险管理) | 风控系统完整 |
| S5 | Week 9-10 | Phase 5.1 (监控运维) | 监控告警完整 |
| S6 | Week 11-12 | Phase 6.1 (体验优化) | 产品打磨完成 |

### 里程碑

| 日期 | 里程碑 | 交付物 |
|------|--------|--------|
| Week 2 | M1: 回测可用 | 完整回测流程 |
| Week 4 | M2: 研究完整 | 因子研究闭环 |
| Week 6 | M3: 模拟可用 | Paper Trading |
| Week 8 | M4: 风控完整 | 熔断器上线 |
| Week 10 | M5: 监控完整 | 告警系统上线 |
| Week 12 | M6: v2.2发布 | 正式版本 |

---

## 数据源依赖矩阵

| 阶段 | 数据源1 | 数据源2 | 降级策略 |
|------|---------|---------|----------|
| 因子研究 | Polygon (行情) | 本地缓存 | 历史缓存 |
| 策略构建 | PostgreSQL | 本地存储 | localStorage |
| 回测验证 | Polygon (历史) | 本地数据库 | 缓存数据 |
| 模拟交易 | Alpaca Paper | WebSocket | 轮询API |
| 实盘部署 | Alpaca Live | WebSocket | 熔断停止 |
| 监控运维 | 全部数据源 | Redis缓存 | 降级显示 |

---

## 质量保证

### 测试要求

| 类型 | 覆盖要求 | 工具 |
|------|----------|------|
| 单元测试 | 核心逻辑 80%+ | pytest |
| 集成测试 | API端点 100% | pytest + httpx |
| E2E测试 | 关键流程 | Playwright |
| 性能测试 | 回测引擎 | locust |

### 代码检查

- [ ] TypeScript 类型检查通过
- [ ] Python 语法检查通过
- [ ] ESLint/Pylint 无严重警告
- [ ] 安全扫描无高危漏洞

---

## 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| Alpaca API限流 | 数据延迟 | 本地缓存 + 重试 |
| Polygon数据不全 | 回测不准 | 多数据源对照 |
| WebSocket断连 | 实时性下降 | 自动重连 + 心跳 |
| 策略执行延迟 | 滑点增加 | 订单超时保护 |

---

## 附录: 关键API清单

### 需要实现的API

```
POST   /api/v1/factors/analyze/ic          # IC分析
POST   /api/v1/factors/analyze/group       # 分组回测
GET    /api/v1/backtests/{id}/equity-curve # 权益曲线
GET    /api/v1/backtests/{id}/heatmap      # 月度热力图
GET    /api/v1/backtests/{id}/trades       # 交易记录
POST   /api/v1/deployments/{id}/start      # 启动部署
POST   /api/v1/deployments/{id}/stop       # 停止部署
GET    /api/v1/risk/realtime/{id}          # 实时风险
POST   /api/v1/alerts/send                 # 发送告警
WebSocket /ws/trading/{deployment_id}      # 实时数据推送
```

---

**文档版本**: 1.0
**创建日期**: 2026-01-10
**创建者**: Claude Code
