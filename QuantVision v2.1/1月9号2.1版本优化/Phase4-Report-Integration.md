# Phase 4 阶段报告: 前后端集成

**日期**: 2026-01-09
**状态**: 已完成
**优先级**: P1 (用户体验)

---

## 1. 完成内容

### 1.1 Mock 数据清理

#### 识别的 Mock 使用点
| 组件/文件 | Mock 数据类型 | 状态 |
|----------|--------------|:----:|
| BacktestCenter | mockMetrics, mockReturnData, mockHeatmapData, mockTrades | 已替换 |
| RiskCenter | mockRiskMetrics, mockCircuitBreaker, mockAlerts | 已替换 |
| FactorLab | 内部 mock 数据 | 待处理 |
| StrategyReplay | 内部 mock 数据 | 待处理 |
| Templates | 内部 mock 数据 | 待处理 |

### 1.2 新增前端服务

#### backtestService.ts (270行)
连接后端回测 API，提供以下功能：
- `getBacktests()` - 获取回测列表
- `createBacktest()` - 创建回测
- `getBacktest()` - 获取回测详情
- `getBacktestStatus()` - 获取回测状态
- `deleteBacktest()` - 删除回测
- `cancelBacktest()` - 取消回测
- `getBacktestTrades()` - 获取交易记录
- `getBacktestPositions()` - 获取持仓

#### riskService.ts (280行)
连接后端风险管理 API，提供以下功能：
- `calculateVaR()` - VaR 计算
- `getStressTestScenarios()` - 获取压力测试情景
- `runStressTest()` - 运行压力测试
- `getCircuitBreakerStatus()` - 获取熔断器状态
- `triggerCircuitBreaker()` - 触发熔断
- `resetCircuitBreaker()` - 重置熔断器
- `getRiskMonitorStatus()` - 获取风险监控状态
- `getRiskAlerts()` - 获取风险警报
- `getRiskScore()` - 获取风险评分

### 1.3 组件更新

#### BacktestCenter/index.tsx
- 移除 hardcoded mock 数据
- 添加状态管理 (metrics, trades, returnData, heatmapData)
- 集成 backtestService API 调用
- 添加轮询机制监控回测进度
- 添加加载状态和错误处理

#### RiskCenter/index.tsx
- 移除 mock 数据常量
- 添加状态管理和数据加载逻辑
- 集成 riskService API 调用
- 添加加载状态和刷新功能
- 添加 Spin 加载指示器

### 1.4 WebSocket 稳定性

已验证 backendWebSocket.ts 具备以下稳定性特性：
| 特性 | 实现 |
|------|------|
| 自动重连 | 最多10次，间隔3秒 |
| 心跳机制 | 30秒间隔 |
| 状态管理 | disconnected/connecting/connected/error |
| 错误处理 | onError + 自动重连 |
| 回调管理 | Set 集合，支持多订阅者 |
| 订阅管理 | subscribe/unsubscribe |

---

## 2. 文件变更清单

### 新增文件
| 文件路径 | 行数 | 功能 |
|----------|:----:|------|
| frontend/src/services/backtestService.ts | 270 | 回测 API 服务 |
| frontend/src/services/riskService.ts | 280 | 风险管理 API 服务 |

### 修改文件
| 文件路径 | 变更内容 |
|----------|----------|
| frontend/src/pages/BacktestCenter/index.tsx | 移除 mock，集成 API |
| frontend/src/pages/RiskCenter/index.tsx | 移除 mock，集成 API |

---

## 3. 验收测试

### 3.1 TypeScript 编译
```bash
$ cd frontend && npx tsc --noEmit --skipLibCheck
# 结果: 通过，无错误
```

### 3.2 API 连接验证
- backtestService: 连接 `/api/v1/backtests/*`
- riskService: 连接 `/api/v1/risk/*`

### 3.3 WebSocket 稳定性验证
- backendWebSocket: 实现完整重连机制
- 心跳: 30秒间隔
- 重连: 最多10次

---

## 4. 遗留问题

### 待后续处理
1. **FactorLab、StrategyReplay、Templates** 组件仍有 mock 数据
   - 需要确认后端是否有对应 API
   - 优先级较低，不影响核心功能

2. **收益曲线和热力图数据**
   - 后端需要提供 `/backtests/{id}/equity_curve` API
   - 后端需要提供 `/backtests/{id}/monthly_returns` API

3. **因子暴露和行业暴露数据**
   - 后端需要提供 `/risk/factor_exposure` API
   - 后端需要提供 `/risk/sector_exposure` API

---

## 5. 下一步

- Phase 5: 生产运维就绪
  - 监控告警
  - 日志聚合
  - 部署自动化

---

**文档版本**: 1.0
**创建时间**: 2026-01-09
**作者**: Claude Opus 4.5
