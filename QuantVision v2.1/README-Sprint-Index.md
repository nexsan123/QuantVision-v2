# QuantVision v2.1 Sprint 任务包索引

> **文档版本**: 4.0  
> **创建日期**: 2025-01-05  
> **更新日期**: 2025-01-05  
> **总时长**: 50.5天 (约10周)  
> **文档结构**: 每个Sprint一个独立文档

---

## 📊 Sprint 总览

| Sprint | 名称 | 时长 | 文档 | 状态 |
|:------:|------|:----:|------|:----:|
| 0 | 项目准备 | 1天 | [Sprint-0-项目准备.md](./Sprint-0-项目准备.md) | ⬜ |
| 1 | 策略管理基础 | 5天 | [Sprint-1-策略管理基础.md](./Sprint-1-策略管理基础.md) | ⬜ |
| 2 | 交易监控升级 | 5天 | [Sprint-2-交易监控升级.md](./Sprint-2-交易监控升级.md) | ⬜ |
| 3 | PDT + AI + 预警 | **5天** | [Sprint-3-PDT-AI-预警.md](./Sprint-3-PDT-AI-预警.md) | ⬜ |
| 4 | 整合测试 + 漂移监控 | **6天** | [Sprint-4-整合测试-漂移监控.md](./Sprint-4-整合测试-漂移监控.md) | ⬜ |
| 5 | 因子+归因+冲突 | 5天 | [Sprint-5-因子归因冲突.md](./Sprint-5-因子归因冲突.md) | ⬜ |
| 6 | 成本+模板+测试 | 4天 | [Sprint-6-成本模板测试.md](./Sprint-6-成本模板测试.md) | ⬜ |
| 7 | 实时交易监控 | **7天** | [Sprint-7-实时交易监控.md](./Sprint-7-实时交易监控.md) | ⬜ |
| 8 | 日内交易UI | **5天** | [Sprint-8-日内交易UI.md](./Sprint-8-日内交易UI.md) | ⬜ |
| 9 | 策略回放 | **7天** | [Sprint-9-策略回放.md](./Sprint-9-策略回放.md) | ⬜ |

**状态图例**: ⬜ 未开始 | 🔄 进行中 | ✅ 已完成

### 版本变更说明 (v4.0)

| 变更项 | 原计划 | 更新后 | 说明 |
|--------|:------:|:------:|------|
| Sprint 2 | 5天 | 5.5天 | **补充**: 接近触发计算 + 信号缓存表 |
| Sprint 3 | 3天 | 5天 | **新增**: 风险预警通知 (邮件) |
| Sprint 4 | 3天 | 6天 | **新增**: 策略漂移监控 |
| Sprint 7 | - | 7天 | **新增**: TradingView + 手动交易 + 分策略持仓 |
| Sprint 8 | - | 5天 | **新增**: 盘前扫描器 + 日内交易专用视图 |
| Sprint 9 | - | 7天 | **新增**: 策略回放功能 (PRD 4.17) |
| **总时长** | 26天 | 50.5天 | +24.5天 |

---

## 📅 时间线

```
Week 1-2        Week 3-4        Week 5          Week 6          Week 7-8        Week 9-10
──────────────────────────────────────────────────────────────────────────────────────────
Sprint 0 (1d)   Sprint 1 (5d)   Sprint 2 (5.5d) Sprint 3 (5d)   Sprint 5 (5d)   Sprint 7 (7d)
项目准备        策略管理        交易监控        PDT+AI+预警     因子+归因+冲突   实时交易监控
                                                Sprint 4 (6d)   Sprint 6 (4d)   Sprint 8 (5d)
                                                整合+漂移监控    成本+模板       日内交易UI
                                                                                Sprint 9 (7d)
                                                                                策略回放
```

---

## 🔗 依赖关系

```
Sprint 0 (项目准备)
    │
    ├──→ Sprint 1 (策略管理基础)
    │        │
    │        └──→ Sprint 2 (交易监控升级) 🆕补充
    │                  │
    ├──→ Sprint 3 (PDT + AI + 预警) 🆕扩展
    │        │
    │        └──────→ Sprint 4 (整合测试 + 漂移监控) 🆕扩展
    │                      │
    │                      └──→ Sprint 5 (因子+归因+冲突)
    │                                │
    │                                └──→ Sprint 6 (成本+模板+测试)
    │                                          │
    │                                          └──→ Sprint 7 (实时交易监控) 🆕
    │                                                    │
    │                                                    ├──→ Sprint 8 (日内交易UI) 🆕
    │                                                    │
    │                                                    └──→ Sprint 9 (策略回放) 🆕
    │
    └────────────────────────────────────────────────────────────→ 发布 v2.1 ✨
```

---

## 📁 文件清单

### 后端新增文件 (共47个)

#### Sprint 1-4 (原有 + 新增)

| Sprint | 文件路径 | 说明 |
|:------:|----------|------|
| 1 | schemas/deployment.py | 部署Schema |
| 1 | services/deployment_service.py | 部署服务 |
| 1 | api/v1/deployment.py | 部署API |
| 2 | schemas/signal_radar.py | 信号雷达Schema |
| 2 | services/signal_service.py | 信号服务 |
| 2 | api/v1/signal_radar.py | 信号雷达API |
| 3 | services/pdt_service.py | PDT服务 |
| 3 | api/v1/pdt.py | PDT API |
| 3 | **schemas/alert.py** | 🆕 预警Schema |
| 3 | **services/alert_service.py** | 🆕 预警服务 |
| 3 | **services/email_service.py** | 🆕 邮件服务 |
| 3 | **api/v1/alerts.py** | 🆕 预警API |
| 4 | **schemas/drift.py** | 🆕 漂移监控Schema |
| 4 | **services/drift_service.py** | 🆕 漂移监控服务 |
| 4 | **api/v1/drift.py** | 🆕 漂移监控API |

#### Sprint 5-6 (原有)

| Sprint | 文件路径 | 说明 |
|:------:|----------|------|
| 5 | schemas/factor_validation.py | 因子验证Schema |
| 5 | services/factor_validation_service.py | 因子验证服务 |
| 5 | api/v1/factor_validation.py | 因子验证API |
| 5 | schemas/trade_record.py | 交易记录Schema |
| 5 | schemas/attribution_report.py | 归因报告Schema |
| 5 | services/attribution_service.py | 归因服务 |
| 5 | api/v1/attribution.py | 归因API |
| 5 | tasks/attribution_tasks.py | 归因定时任务 |
| 5 | schemas/conflict.py | 冲突Schema |
| 5 | services/conflict_service.py | 冲突服务 |
| 5 | api/v1/conflict.py | 冲突API |
| 5 | tasks/conflict_tasks.py | 冲突超时任务 |
| 6 | schemas/trading_cost.py | 成本配置Schema |
| 6 | services/cost_service.py | 成本计算服务 |
| 6 | api/v1/trading_cost.py | 成本配置API |
| 6 | schemas/strategy_template.py | 模板Schema |
| 6 | services/template_service.py | 模板服务 |
| 6 | api/v1/templates.py | 模板API |
| 6 | data/templates/*.json | 6个预设模板 |

#### Sprint 7-8 (🆕 新增)

| Sprint | 文件路径 | 说明 |
|:------:|----------|------|
| 7 | **schemas/position.py** | 🆕 分策略持仓Schema |
| 7 | **services/manual_trade_service.py** | 🆕 手动交易服务 |
| 7 | **services/position_service.py** | 🆕 持仓管理服务 |
| 7 | **api/v1/manual_trade.py** | 🆕 手动交易API |
| 7 | **api/v1/positions.py** | 🆕 持仓管理API |
| 8 | **schemas/pre_market.py** | 🆕 盘前扫描Schema |
| 8 | **services/pre_market_service.py** | 🆕 盘前扫描服务 |
| 8 | **api/v1/pre_market.py** | 🆕 盘前扫描API |
| 8 | **tasks/time_stop_task.py** | 🆕 时间止损任务 |

### 前端新增文件 (共40个)

#### Sprint 1-6 (原有)

| Sprint | 文件路径 | 说明 |
|:------:|----------|------|
| 1 | pages/MyStrategies/index.tsx | 我的策略页面 |
| 1 | components/Strategy/StrategyCard.tsx | 策略卡片 |
| 1 | components/Deployment/DeploymentWizard.tsx | 部署向导 |
| 1 | types/deployment.ts | 部署类型 |
| 2 | components/SignalRadar/index.tsx | 信号雷达面板 |
| 2 | components/SignalRadar/SignalList.tsx | 信号列表 |
| 2 | components/common/EnvironmentSwitch.tsx | 环境切换器 |
| 2 | types/signalRadar.ts | 信号雷达类型 |
| 3 | components/PDT/PDTStatus.tsx | PDT状态 |
| 3 | components/PDT/PDTWarning.tsx | PDT警告 |
| 3 | components/AI/AIStatusIndicator.tsx | AI状态指示器 |
| 3 | types/pdt.ts | PDT类型 |
| 3 | types/ai.ts | AI状态类型 |
| 3 | **types/alert.ts** | 🆕 预警类型 |
| 3 | **components/Alerts/AlertBell.tsx** | 🆕 预警铃铛 |
| 3 | **components/Alerts/AlertConfigPanel.tsx** | 🆕 预警配置面板 |
| 4 | **types/drift.ts** | 🆕 漂移类型 |
| 4 | **components/Drift/DriftReportPanel.tsx** | 🆕 漂移报告面板 |
| 4 | **components/Drift/DriftIndicator.tsx** | 🆕 漂移指示器 |
| 5 | components/Factor/FactorValidation.tsx | 因子验证面板 |
| 5 | components/Factor/ICChart.tsx | IC时序图 |
| 5 | components/Attribution/ReportPanel.tsx | 归因报告面板 |
| 5 | components/Attribution/AIDiagnosis.tsx | AI诊断卡片 |
| 5 | components/Conflict/ConflictModal.tsx | 冲突决策弹窗 |
| 5 | types/factorValidation.ts | 因子验证类型 |
| 5 | types/attribution.ts | 归因类型 |
| 5 | types/conflict.ts | 冲突类型 |
| 6 | pages/Templates/index.tsx | 模板库页面 |
| 6 | components/TradingCost/CostConfig.tsx | 成本配置面板 |
| 6 | components/Template/TemplateCard.tsx | 模板卡片 |
| 6 | components/Template/TemplateDetail.tsx | 模板详情 |
| 6 | types/tradingCost.ts | 成本类型 |
| 6 | types/template.ts | 模板类型 |

#### Sprint 7-8 (🆕 新增)

| Sprint | 文件路径 | 说明 |
|:------:|----------|------|
| 7 | **types/position.ts** | 🆕 持仓类型 |
| 7 | **components/Chart/TradingViewChart.tsx** | 🆕 TradingView图表 |
| 7 | **components/Chart/ChartToolbar.tsx** | 🆕 图表工具栏 |
| 7 | **components/Chart/SignalOverlay.tsx** | 🆕 信号覆盖层 |
| 7 | **components/Trade/QuickTradePanel.tsx** | 🆕 快速交易面板 |
| 7 | **components/Position/PositionPanel.tsx** | 🆕 持仓面板 |
| 8 | **types/pre_market.ts** | 🆕 盘前扫描类型 |
| 8 | **pages/IntradayTradingPage.tsx** | 🆕 日内交易页面 |
| 8 | **components/Intraday/PreMarketScanner.tsx** | 🆕 盘前扫描器 |
| 8 | **components/Intraday/SimplifiedWatchlist.tsx** | 🆕 简化监控列表 |
| 8 | **components/Intraday/StopLossPanel.tsx** | 🆕 止盈止损面板 |
| 8 | **components/Intraday/IntradayTradeLog.tsx** | 🆕 交易记录 |

---

## 🔌 新增API端点 (共52个)

### Sprint 1-4 (23个，含新增7个)

```
# 部署相关
POST   /api/v1/deployments              - 创建部署
GET    /api/v1/deployments              - 获取部署列表
GET    /api/v1/deployments/{id}         - 获取部署详情
PUT    /api/v1/deployments/{id}         - 更新部署
DELETE /api/v1/deployments/{id}         - 删除部署
POST   /api/v1/deployments/{id}/start   - 启动
POST   /api/v1/deployments/{id}/pause   - 暂停
POST   /api/v1/deployments/{id}/stop    - 停止
POST   /api/v1/deployments/{id}/switch-env - 切换环境
GET    /api/v1/deployments/{id}/param-limits - 获取参数范围

# 信号雷达
GET    /api/v1/signal-radar/{strategy_id} - 获取信号雷达
GET    /api/v1/signal-radar/stocks/search - 搜索股票

# PDT相关
GET    /api/v1/pdt/status               - 获取PDT状态
GET    /api/v1/pdt/check                - 检查日内交易

# AI状态
GET    /api/v1/ai-assistant/status      - AI连接状态
POST   /api/v1/ai-assistant/reconnect   - 重新连接AI

# 风险预警 🆕
GET    /api/v1/alerts                   - 获取预警列表
GET    /api/v1/alerts/unread-count      - 获取未读数量
POST   /api/v1/alerts/{id}/read         - 标记为已读
POST   /api/v1/alerts/mark-all-read     - 全部标记已读
GET    /api/v1/alerts/config            - 获取预警配置
PUT    /api/v1/alerts/config            - 更新预警配置
POST   /api/v1/alerts/test-email        - 发送测试邮件

# 漂移监控 🆕
POST   /api/v1/drift/check              - 检查策略漂移
GET    /api/v1/drift/reports/{strategyId} - 获取漂移报告历史
GET    /api/v1/drift/reports/{strategyId}/latest - 获取最新报告
POST   /api/v1/drift/reports/{reportId}/acknowledge - 确认报告
GET    /api/v1/drift/thresholds         - 获取阈值配置
```

### Sprint 5 (12个)

```
GET  /api/v1/factors/{id}/validation      - 获取因子验证结果
POST /api/v1/factors/{id}/validate        - 触发因子验证
GET  /api/v1/factors/{id}/suggestions     - 获取因子组合建议
GET  /api/v1/trades                       - 交易记录列表
GET  /api/v1/trades/{id}                  - 交易记录详情
GET  /api/v1/attribution/reports          - 归因报告列表
POST /api/v1/attribution/generate         - 手动触发归因
GET  /api/v1/attribution/diagnosis/{id}   - 获取AI诊断
GET  /api/v1/conflicts                    - 冲突列表
GET  /api/v1/conflicts/pending            - 待处理冲突
POST /api/v1/conflicts/{id}/resolve       - 解决冲突
```

### Sprint 6 (6个)

```
GET  /api/v1/trading-cost/config          - 获取成本配置
PUT  /api/v1/trading-cost/config          - 更新成本配置
POST /api/v1/trading-cost/estimate        - 估算交易成本
GET  /api/v1/templates                    - 模板列表
GET  /api/v1/templates/{id}               - 模板详情
POST /api/v1/templates/{id}/deploy        - 从模板部署
```

### Sprint 7-8 (11个) 🆕

```
# 手动交易 🆕
POST   /api/v1/manual-trade/order         - 下单
DELETE /api/v1/manual-trade/order/{id}    - 取消订单
GET    /api/v1/manual-trade/orders        - 获取订单列表
GET    /api/v1/manual-trade/quote/{symbol} - 获取实时报价

# 持仓管理 🆕
GET    /api/v1/positions/summary          - 获取持仓汇总
GET    /api/v1/positions/strategy/{id}    - 获取策略持仓
GET    /api/v1/positions/symbol/{symbol}  - 获取股票持仓详情

# 日内交易 🆕
GET    /api/v1/intraday/pre-market-scanner - 盘前扫描
POST   /api/v1/intraday/watchlist         - 确认监控列表
GET    /api/v1/intraday/watchlist         - 获取今日监控列表
```

---

## ✅ PRD 功能覆盖表

### P0 功能 (8/8 = 100%)

| PRD章节 | 功能名称 | Sprint | 验收标准 |
|:-------:|----------|:------:|----------|
| 4.1 | 我的策略列表 | 1 | 策略CRUD、状态管理 |
| 4.2 | AI连接状态 | 3 | 状态指示器、重连按钮 |
| 4.3 | 因子有效性验证 | 5 | IC/IR分析、有效性判定 |
| 4.4 | 交易成本配置 | 6 | 简单/专业模式、最低限制 |
| 4.5 | 交易归因系统 | 5 | 自动记录、AI诊断 |
| 4.6 | 策略冲突检测 | 5 | 逻辑/执行冲突、超时处理 |
| 4.7 | PDT规则管理 | 3 | 次数显示、警告提醒 |
| 4.15.2 | 策略部署向导 | 1 | 4步部署流程 |

### P1 功能 (4/8 = 50%) 🆕扩展

| PRD章节 | 功能名称 | Sprint | 验收标准 |
|:-------:|----------|:------:|----------|
| 4.13 | 策略模板库 | 6 | 6个预设模板、一键部署 |
| 4.15.3 | 环境切换 | 2 | 模拟盘/实盘切换 |
| 4.14 | **风险预警通知** | 3 | 🆕 邮件通知、阈值配置 |
| 4.8 | **实盘vs回测监控** | 4 | 🆕 漂移检测、建议生成 |

### 额外实现 (PRD 4.16/4.17/4.18) 🆕

| PRD章节 | 功能名称 | Sprint | 验收标准 |
|:-------:|----------|:------:|----------|
| 4.16 | TradingView集成 | 7 | 🆕 实时图表、信号覆盖 |
| 4.16 | 手动交易面板 | 7 | 🆕 快速下单、市价/限价 |
| 4.18 | 分策略持仓管理 | 7 | 🆕 独立账本、汇总视图 |
| 4.18.0 | 盘前扫描器 | 8 | 🆕 筛选条件、评分算法 |
| 4.18.1 | 日内交易专用视图 | 8 | 🆕 简化布局、止盈止损 |
| **4.17** | **策略回放功能** | **9** | 🆕 回放控制、因子显示、信号日志 |

---

## 📋 使用说明

1. **按顺序执行**: 从Sprint 0开始，按依赖关系依次完成
2. **一次一个Sprint**: 将单个Sprint文档交给Claude Code执行
3. **检查验收标准**: 每个Sprint结束时确认所有验收项
4. **更新状态**: 完成后将索引中的状态从 ⬜ 改为 ✅

---

## 📝 进度记录

| 日期 | Sprint | 完成情况 | 备注 |
|------|:------:|----------|------|
| - | 0 | 待开始 | - |
| - | 1 | 待开始 | - |
| - | 2 | 待开始 | 🆕 +接近触发逻辑 |
| - | 3 | 待开始 | 🆕 +预警功能 |
| - | 4 | 待开始 | 🆕 +漂移监控 |
| - | 5 | 待开始 | - |
| - | 6 | 待开始 | - |
| - | 7 | 待开始 | 🆕 新增Sprint |
| - | 8 | 待开始 | 🆕 新增Sprint |
| - | 9 | 待开始 | 🆕 新增Sprint (策略回放) |

---

## 📊 版本规划

### v2.1.0 完整版 (当前计划)

```
总时长: 50.5天 (约10周)
功能覆盖:
├── P0: 100% (8/8)
├── P1: 50% (4/8)
└── 额外: 100% (6/6) - TradingView + 日内交易 + 策略回放
```

### 后续版本建议 (v2.2.0)

| 功能 | PRD章节 | 预计工时 |
|------|:-------:|:--------:|
| 税务计算系统 | 4.9 | 7天 |
| 策略版本管理 | - | 5天 |
| MCP多模型支持 | 4.10 | 10天 |
| MCP新闻捕捉 | 4.11 | 7天 |

---

**总文档数**: 11个 (1个索引 + 10个Sprint)  
**预计完成时间**: 50.5天 (约10周)
