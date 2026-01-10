# QuantVision v2.1 补充优化报告

**日期**: 2026-01-09
**版本**: 2.1.1
**用途**: 后续优化迭代参考

---

## 1. 执行摘要

本报告汇总了 QuantVision v2.1 机构级完善计划 (Phase 1-5) 完成后的所有遗留项、待办事项和优化建议，为后续开发迭代提供参考。

| 类别 | 数量 | 优先级 |
|------|:----:|:------:|
| 后端 TODO | 23 | P1-P2 |
| 前端 TODO | 7 | P2 |
| Mock 数据残留 | 11 文件 | P2-P3 |
| 缺失 API | 4 | P1 |
| 测试覆盖 | 待完善 | P2 |

---

## 2. 后端 TODO 清单

### 2.1 backtests.py (6 个 TODO)
**文件**: `backend/app/api/v1/backtests.py`
**优先级**: P1

| 行号 | TODO 内容 |
|:----:|----------|
| 44 | 从数据库获取回测列表 |
| 90 | 从数据库获取回测详情 |
| 121 | 从数据库获取回测状态 |
| 221 | 从数据库获取交易记录 |
| 257 | 从数据库获取持仓快照 |
| 287 | 从数据库获取每日收益 |

**建议**: 使用 SQLAlchemy ORM 连接 backtests 表，实现完整的数据库查询逻辑。

### 2.2 factors.py (6 个 TODO)
**文件**: `backend/app/api/v1/factors.py`
**优先级**: P2

| 行号 | TODO 内容 |
|:----:|----------|
| 42 | 从数据库获取因子列表 |
| 86 | 保存因子到数据库 |
| 109 | 从数据库获取因子详情 |
| 130 | 更新数据库中的因子 |
| 147 | 从数据库删除因子 |
| 183 | 实际计算 IC/IR 值 |

**建议**: 创建 factors 表，实现因子 CRUD 和 IC/IR 计算逻辑。

### 2.3 notification_service.py (3 个 TODO)
**文件**: `backend/app/services/notification_service.py`
**优先级**: P2

| 行号 | TODO 内容 |
|:----:|----------|
| 77 | 实现实际的邮件发送 |
| 110 | 实现实际的 Webhook 发送 |
| 138 | 实现实际的 SMS 发送 |

**建议**: 集成 SendGrid/SES (邮件)、Twilio (SMS)、HTTP client (Webhook)。

### 2.4 manual_trade_service.py (4 个 TODO)
**文件**: `backend/app/services/manual_trade_service.py`
**优先级**: P1

| 行号 | TODO 内容 |
|:----:|----------|
| 98 | 检查账户资金是否足够 |
| 99 | 检查是否满足 PDT 规则 |
| 144 | 检查账户持仓是否足够 |
| 145 | 检查是否在允许交易时段 |

**建议**: 实现账户资金/持仓校验逻辑，集成 PDT 规则引擎。

### 2.5 time_stop_task.py (2 个 TODO)
**文件**: `backend/app/services/tasks/time_stop_task.py`
**优先级**: P2

| 行号 | TODO 内容 |
|:----:|----------|
| 50 | 实现时间止损逻辑 |
| 68 | 检查持仓是否超过最大持仓时间 |

**建议**: 实现基于时间的止损策略，支持配置最大持仓时间。

### 2.6 deployment_service.py (2 个 TODO)
**文件**: `backend/app/services/deployment_service.py`
**优先级**: P2

| 行号 | TODO 内容 |
|:----:|----------|
| 166 | 从回测结果获取参数范围 |
| 264 | 获取更详细的统计数据 |

**建议**: 关联回测结果，提取最优参数范围用于部署配置。

---

## 3. 前端 TODO 清单

### 3.1 BacktestCenter/index.tsx
**文件**: `frontend/src/pages/BacktestCenter/index.tsx`
**优先级**: P2

| TODO 内容 |
|----------|
| 后端需要提供收益曲线数据的 API |
| 后端需要提供热力图数据的 API |

### 3.2 RiskCenter/index.tsx
**文件**: `frontend/src/pages/RiskCenter/index.tsx`
**优先级**: P2

| TODO 内容 |
|----------|
| 因子暴露需要后端额外 API 支持 |
| 行业暴露需要后端额外 API 支持 |

### 3.3 其他组件
| 文件 | TODO 内容 |
|------|----------|
| StrategyReplay | 回放数据 API |
| FactorLab | 因子分析 API |
| Dashboard | 实时数据优化 |

---

## 4. Mock 数据残留

### 4.1 高优先级 (P2) - 核心功能
| 文件 | Mock 数据 | 建议 |
|------|----------|------|
| `pages/FactorLab/index.tsx` | mockFactors, mockICData, mockGroupData, mockValidationResults | 创建因子分析 API |
| `pages/Templates/index.tsx` | mockTemplates | 创建模板管理 API |
| `pages/StrategyReplay/index.tsx` | 回放数据 | 创建回放数据 API |

### 4.2 中优先级 (P3) - 辅助功能
| 文件 | Mock 数据 | 建议 |
|------|----------|------|
| `components/SignalRadar/index.tsx` | 信号数据 | 集成实时信号 API |
| `components/Intraday/IntradayChart.tsx` | K线数据 | 集成行情数据源 |
| `components/Intraday/TimeAndSales.tsx` | 逐笔数据 | 集成 Level 2 数据 |
| `hooks/usePreMarketScanner.ts` | useMockData=true | 集成盘前扫描 API |

### 4.3 低优先级 (P4) - 演示/开发用
| 文件 | Mock 数据 | 建议 |
|------|----------|------|
| `services/strategyService.ts` | USE_MOCK=false | 已完成 |
| `services/deploymentService.ts` | USE_MOCK=false | 已完成 |

---

## 5. 缺失 API 实现

### 5.1 replay.py (策略回放)
**文件**: `backend/app/api/v1/replay.py`
**状态**: 仅有 pass 占位符

需要实现:
- `GET /replay/sessions` - 获取回放会话列表
- `POST /replay/sessions` - 创建回放会话
- `GET /replay/sessions/{id}` - 获取回放详情
- `POST /replay/sessions/{id}/play` - 播放控制
- `POST /replay/sessions/{id}/pause` - 暂停控制
- `DELETE /replay/sessions/{id}` - 删除会话

### 5.2 risk_advanced.py (高级风险)
**文件**: `backend/app/api/v1/risk_advanced.py`
**状态**: 仅有 pass 占位符

需要实现:
- `GET /risk/factor-exposure` - 因子暴露分析
- `GET /risk/sector-exposure` - 行业暴露分析
- `GET /risk/correlation-matrix` - 相关性矩阵
- `POST /risk/scenario-analysis` - 情景分析

### 5.3 收益曲线 API
**需求来源**: BacktestCenter

需要实现:
- `GET /backtests/{id}/equity-curve` - 权益曲线数据
- `GET /backtests/{id}/drawdown` - 回撤曲线数据

### 5.4 热力图 API
**需求来源**: BacktestCenter

需要实现:
- `GET /backtests/{id}/heatmap` - 月度收益热力图
- `GET /backtests/{id}/returns/monthly` - 月度收益统计

---

## 6. 测试覆盖建议

### 6.1 后端测试 (pytest)
| 模块 | 当前状态 | 建议 |
|------|:--------:|------|
| API 端点 | 部分 | 增加集成测试 |
| 服务层 | 部分 | 增加单元测试 |
| 数据库模型 | 无 | 添加模型测试 |
| 认证/授权 | 无 | 添加安全测试 |

### 6.2 前端测试 (Jest)
| 模块 | 当前状态 | 建议 |
|------|:--------:|------|
| 服务层 | 无 | 添加 API mock 测试 |
| 组件 | 无 | 添加渲染测试 |
| Hooks | 无 | 添加行为测试 |

---

## 7. 优化建议优先级排序

### P0 - 阻塞性 (立即处理)
*无*

### P1 - 高优先级 (1-2 周)
1. **backtests.py 数据库查询** - 回测功能核心
2. **manual_trade_service.py 校验逻辑** - 交易安全
3. **收益曲线/热力图 API** - 用户体验

### P2 - 中优先级 (2-4 周)
1. **factors.py 数据库操作** - 因子分析功能
2. **notification_service.py 实现** - 通知功能
3. **FactorLab Mock 替换** - 功能完整性
4. **测试覆盖提升** - 代码质量

### P3 - 低优先级 (1-2 月)
1. **replay.py 完整实现** - 策略回放
2. **risk_advanced.py 完整实现** - 高级风险分析
3. **其他 Mock 数据替换** - 功能完善

### P4 - 未来增强 (规划中)
1. **移动端适配**
2. **双因素认证**
3. **API Rate Limiting**
4. **更多数据源集成**

---

## 8. 技术债务清单

| 类别 | 描述 | 影响 | 建议 |
|------|------|------|------|
| 类型安全 | 部分 any 类型使用 | 低 | 逐步替换为具体类型 |
| 错误处理 | 部分 catch 仅 console.error | 中 | 统一错误处理机制 |
| 代码重复 | 部分服务有相似逻辑 | 低 | 抽取公共方法 |
| 注释 | 部分复杂逻辑缺少注释 | 低 | 添加关键注释 |

---

## 9. 安全检查清单

| 检查项 | 状态 | 备注 |
|--------|:----:|------|
| SQL 注入防护 | PASS | 使用 ORM |
| XSS 防护 | PASS | React 默认转义 |
| CSRF 防护 | PASS | JWT Token |
| 敏感信息 | PASS | 环境变量 |
| 密码存储 | PASS | bcrypt 哈希 |
| API 认证 | PASS | JWT + RBAC |
| 日志脱敏 | 待检查 | 确认无敏感数据 |
| Rate Limiting | 未实现 | 建议添加 |

---

## 10. 附录

### 10.1 代码检测结果
```
TypeScript: npx tsc --noEmit --skipLibCheck
结果: PASS (0 errors)

USE_MOCK 标志:
- strategyService.ts: USE_MOCK = false
- deploymentService.ts: USE_MOCK = false
```

### 10.2 文件统计
| 类别 | 文件数 | 行数 |
|------|:------:|:----:|
| 后端 Python | 50+ | 15000+ |
| 前端 TypeScript | 80+ | 25000+ |
| 配置文件 | 20+ | 2000+ |
| 文档 | 15+ | 3000+ |

### 10.3 相关文档
- Phase1-Report-DataPersistence.md
- Phase2-Report-Execution.md
- Phase3-Report-Compliance.md
- Phase4-Report-Integration.md
- Phase5-Report-Operations.md
- Final-Summary-Report-v2.1.md

---

**文档版本**: 1.0
**创建时间**: 2026-01-09
**作者**: Claude Opus 4.5

---

*Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>*
