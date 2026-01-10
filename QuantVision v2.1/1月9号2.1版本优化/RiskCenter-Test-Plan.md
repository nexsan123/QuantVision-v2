# 风险中心 (RiskCenter) 全面测试方案

**日期**: 2026-01-09
**版本**: 2.1.1
**测试范围**: 前端 UI + 后端 API

---

## 1. 测试准备

### 1.1 环境检查
```bash
# 1. 确保后端运行
curl http://localhost:8000/api/v1/health
# 预期: {"status":"healthy",...}

# 2. 确保数据库连接
docker exec quantvision-dev-postgres psql -U quantvision -c "SELECT 1"

# 3. 确保前端编译通过
cd frontend && npx tsc --noEmit --skipLibCheck
```

### 1.2 测试账户
- 准备不同角色账户 (Admin/Trader/Analyst/Viewer)
- 确认 JWT Token 可正常获取

---

## 2. API 端点测试 (后端)

### 2.1 熔断器 API (核心)

| 测试用例 | API 端点 | 方法 | 预期结果 |
|----------|----------|:----:|----------|
| TC-CB-01 | 获取熔断器状态 | GET `/api/v1/risk/circuit-breaker` | 返回 state, isTripped, canTrade |
| TC-CB-02 | 触发熔断 (无原因) | POST `/api/v1/risk/circuit-breaker/trigger` | state=OPEN, isTripped=true |
| TC-CB-03 | 触发熔断 (带原因) | POST `/api/v1/risk/circuit-breaker/trigger?reason=测试触发` | triggerReason=测试触发 |
| TC-CB-04 | 重置熔断器 | POST `/api/v1/risk/circuit-breaker/reset` | state=CLOSED, canTrade=true |
| TC-CB-05 | 更新风险指标 | POST `/api/v1/risk/circuit-breaker/update` | 返回更新后状态 |

**测试命令**:
```bash
# TC-CB-01: 获取状态
curl http://localhost:8000/api/v1/risk/circuit-breaker

# TC-CB-02: 触发熔断
curl -X POST http://localhost:8000/api/v1/risk/circuit-breaker/trigger

# TC-CB-03: 带原因触发
curl -X POST "http://localhost:8000/api/v1/risk/circuit-breaker/trigger?reason=压力测试"

# TC-CB-04: 重置
curl -X POST http://localhost:8000/api/v1/risk/circuit-breaker/reset

# TC-CB-05: 更新指标
curl -X POST http://localhost:8000/api/v1/risk/circuit-breaker/update \
  -H "Content-Type: application/json" \
  -d '{"daily_pnl": -0.02, "drawdown": -0.05, "volatility": 0.25}'
```

---

### 2.2 VaR 计算 API

| 测试用例 | 测试内容 | 预期结果 |
|----------|----------|----------|
| TC-VAR-01 | 历史模拟法 VaR | 返回 var, cvar, var_pct |
| TC-VAR-02 | 参数法 VaR | 返回正态分布 VaR |
| TC-VAR-03 | 蒙特卡洛 VaR | 返回模拟 VaR |
| TC-VAR-04 | 不同置信度 | 95% < 99% VaR |
| TC-VAR-05 | 无效方法 | 返回 400 错误 |

**测试命令**:
```bash
# TC-VAR-01: 历史模拟法
curl -X POST http://localhost:8000/api/v1/risk/var \
  -H "Content-Type: application/json" \
  -d '{
    "returns": [0.01, -0.02, 0.015, -0.01, 0.02, -0.03, 0.005],
    "confidence_level": 0.95,
    "method": "historical",
    "horizon_days": 1,
    "portfolio_value": 1000000
  }'

# TC-VAR-02: 参数法
curl -X POST http://localhost:8000/api/v1/risk/var \
  -H "Content-Type: application/json" \
  -d '{
    "returns": [0.01, -0.02, 0.015, -0.01, 0.02, -0.03, 0.005],
    "method": "parametric"
  }'

# TC-VAR-05: 无效方法 (应返回 400)
curl -X POST http://localhost:8000/api/v1/risk/var \
  -H "Content-Type: application/json" \
  -d '{"returns": [0.01, -0.02], "method": "invalid_method"}'
```

---

### 2.3 压力测试 API

| 测试用例 | 测试内容 | 预期结果 |
|----------|----------|----------|
| TC-ST-01 | 获取情景列表 | 返回 5+ 个预设情景 |
| TC-ST-02 | 2008 金融危机 | portfolio_loss_pct 约 -50% |
| TC-ST-03 | 2020 新冠崩盘 | portfolio_loss_pct 约 -34% |
| TC-ST-04 | 无效情景 | 返回 400 错误 |

**测试命令**:
```bash
# TC-ST-01: 获取情景列表
curl http://localhost:8000/api/v1/risk/stress-test/scenarios

# TC-ST-02: 2008 金融危机
curl -X POST http://localhost:8000/api/v1/risk/stress-test \
  -H "Content-Type: application/json" \
  -d '{
    "holdings": {"AAPL": 0.3, "MSFT": 0.3, "GOOGL": 0.2, "AMZN": 0.2},
    "scenario": "2008_financial_crisis",
    "portfolio_value": 1000000
  }'

# TC-ST-03: 2020 新冠崩盘
curl -X POST http://localhost:8000/api/v1/risk/stress-test \
  -H "Content-Type: application/json" \
  -d '{
    "holdings": {"AAPL": 0.5, "XOM": 0.5},
    "scenario": "2020_covid_crash",
    "portfolio_value": 500000
  }'
```

---

### 2.4 风险监控 API

| 测试用例 | API 端点 | 方法 | 预期结果 |
|----------|----------|:----:|----------|
| TC-RM-01 | 获取监控状态 | GET `/api/v1/risk/monitor/status` | 返回 isRunning, currentDrawdown |
| TC-RM-02 | 获取风险警报 | GET `/api/v1/risk/monitor/alerts` | 返回警报列表 |
| TC-RM-03 | 按级别筛选警报 | GET `/api/v1/risk/monitor/alerts?level=critical` | 仅返回 critical |
| TC-RM-04 | 获取风险评分 | GET `/api/v1/risk/monitor/score` | 返回 0-100 评分 |

**测试命令**:
```bash
# TC-RM-01: 监控状态
curl http://localhost:8000/api/v1/risk/monitor/status

# TC-RM-02: 所有警报
curl http://localhost:8000/api/v1/risk/monitor/alerts

# TC-RM-03: 筛选 critical
curl "http://localhost:8000/api/v1/risk/monitor/alerts?level=critical"

# TC-RM-04: 风险评分
curl http://localhost:8000/api/v1/risk/monitor/score
```

---

## 3. 前端 UI 测试

### 3.1 页面加载测试

| 测试用例 | 测试步骤 | 预期结果 |
|----------|----------|----------|
| TC-UI-01 | 打开风险中心页面 | 显示加载动画 -> 显示数据 |
| TC-UI-02 | 检查风险指标卡片 | VaR(95%), VaR(99%), CVaR, 波动率 显示 |
| TC-UI-03 | 检查熔断器状态 | 显示 CLOSED/OPEN 状态标签 |
| TC-UI-04 | 检查进度条 | 回撤/日亏损/波动率 进度条正常 |
| TC-UI-05 | 点击刷新按钮 | 显示加载状态, 数据更新 |

### 3.2 熔断器交互测试

| 测试用例 | 测试步骤 | 预期结果 |
|----------|----------|----------|
| TC-CB-UI-01 | 查看熔断器状态 | 显示绿色 "正常交易" 标签 |
| TC-CB-UI-02 | 观察触发阈值 | 回撤/日亏损/波动率 百分比显示 |
| TC-CB-UI-03 | 观察进度条颜色 | 接近阈值时变红 |

### 3.3 图表测试

| 测试用例 | 测试步骤 | 预期结果 |
|----------|----------|----------|
| TC-CH-01 | 因子暴露雷达图 | 显示 6 个因子维度 |
| TC-CH-02 | 行业暴露饼图 | 显示行业占比 |
| TC-CH-03 | 图表交互 | 鼠标悬停显示 tooltip |

### 3.4 警报显示测试

| 测试用例 | 测试步骤 | 预期结果 |
|----------|----------|----------|
| TC-AL-01 | 无警报时 | 显示绿色 "暂无风险警报" |
| TC-AL-02 | 有警报时 | 显示警报卡片列表 |
| TC-AL-03 | 警报颜色 | critical=红, warning=橙, info=蓝 |

---

## 4. 集成测试流程

### 4.1 完整业务流程测试

```
步骤 1: 初始状态检查
├── 打开风险中心
├── 确认熔断器 state=CLOSED
├── 确认 canTrade=true
└── 记录初始风险指标

步骤 2: 模拟风险事件
├── 调用 API 更新风险指标
│   POST /api/v1/risk/circuit-breaker/update
│   {"daily_pnl": -0.035, "drawdown": -0.12}
├── 刷新前端页面
└── 观察进度条变化

步骤 3: 触发熔断
├── 继续更新风险指标超过阈值
│   或直接调用 POST /circuit-breaker/trigger
├── 前端刷新
├── 确认 state=OPEN
├── 确认 canTrade=false
└── 确认显示红色 "熔断中" 标签

步骤 4: 恢复熔断
├── 调用 POST /circuit-breaker/reset
├── 前端刷新
├── 确认 state=CLOSED
└── 确认 canTrade=true
```

### 4.2 VaR 计算验证

```bash
# 使用已知数据验证 VaR 计算正确性
# 测试数据: 10 个日收益率
returns = [0.01, -0.02, 0.015, -0.025, 0.02, -0.01, 0.005, -0.015, 0.025, -0.03]

# 95% 历史 VaR 应该约等于 -2.5% (排序后第 5% 分位)
# 99% 历史 VaR 应该约等于 -3.0%
```

### 4.3 压力测试验证

```
情景: 2008 金融危机
├── 市场冲击: -50%
├── 金融行业额外冲击: -60%
└── 预期组合损失: 根据持仓计算

验证:
├── portfolio_loss_pct 合理 (-30% ~ -60%)
├── var_stressed > 正常 VaR
└── recovery_days 显示合理天数
```

---

## 5. 边界条件测试

### 5.1 异常输入测试

| 测试用例 | 输入 | 预期结果 |
|----------|------|----------|
| TC-ERR-01 | VaR 空收益率数组 | 400 错误或默认值 |
| TC-ERR-02 | 置信度 > 0.99 | 400 错误 |
| TC-ERR-03 | 置信度 < 0.9 | 400 错误 |
| TC-ERR-04 | 负数投资组合价值 | 400 错误 |
| TC-ERR-05 | 不存在的压力情景 | 400 错误 |

### 5.2 并发测试

```bash
# 并发 10 个熔断器状态查询
for i in {1..10}; do
  curl http://localhost:8000/api/v1/risk/circuit-breaker &
done
wait

# 并发 VaR 计算
for i in {1..5}; do
  curl -X POST http://localhost:8000/api/v1/risk/var \
    -H "Content-Type: application/json" \
    -d '{"returns": [0.01, -0.02, 0.015], "method": "historical"}' &
done
wait
```

---

## 6. 性能测试

### 6.1 响应时间基准

| API | 预期响应时间 |
|-----|:------------:|
| GET /circuit-breaker | < 100ms |
| POST /var (historical) | < 200ms |
| POST /var (monte_carlo) | < 1000ms |
| POST /stress-test | < 500ms |
| GET /monitor/status | < 100ms |

### 6.2 测试命令

```bash
# 使用 time 测量响应时间
time curl -s http://localhost:8000/api/v1/risk/circuit-breaker > /dev/null

# 使用 Apache Bench 进行负载测试
ab -n 100 -c 10 http://localhost:8000/api/v1/risk/circuit-breaker
```

---

## 7. 测试检查清单

### 7.1 API 测试 (后端)
- [ ] 熔断器状态查询正常
- [ ] 熔断器触发/重置正常
- [ ] VaR 5 种方法都能计算
- [ ] 压力测试 5 个预设情景可用
- [ ] 风险监控状态/警报/评分正常
- [ ] 错误输入返回正确错误码

### 7.2 UI 测试 (前端)
- [ ] 页面正常加载无白屏
- [ ] 风险指标卡片显示数值
- [ ] 熔断器状态标签正确
- [ ] 进度条颜色变化正确
- [ ] 雷达图/饼图正常渲染
- [ ] 刷新按钮功能正常
- [ ] 警报显示正确颜色

### 7.3 集成测试
- [ ] 熔断触发->重置完整流程
- [ ] 前端刷新后数据同步
- [ ] VaR 计算结果合理
- [ ] 压力测试结果合理

---

## 8. 测试报告模板

```markdown
# 风险中心测试报告

**测试日期**: YYYY-MM-DD
**测试人员**:
**环境**: 开发/测试/生产

## 测试结果汇总

| 类别 | 总数 | 通过 | 失败 | 跳过 |
|------|:----:|:----:|:----:|:----:|
| API 测试 | 20 | | | |
| UI 测试 | 10 | | | |
| 集成测试 | 5 | | | |
| 性能测试 | 5 | | | |

## 失败用例详情

| 用例 ID | 描述 | 实际结果 | 优先级 |
|---------|------|----------|:------:|
| TC-XXX | ... | ... | P1 |

## 问题清单

1. [问题描述]

## 结论

[通过/不通过] - [备注]
```

---

**文档版本**: 1.0
**创建时间**: 2026-01-09
**作者**: Claude Opus 4.5

---

*Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>*
