# QuantVision v2.1 SPEC 优化计划

**版本**: 2.1.0
**日期**: 2026-01-09
**状态**: 执行中
**模式**: SPEC (Specification-Driven Development)

---

## 1. 项目概述

### 1.1 目标
- 修复所有P0级阻塞性Bug
- 补全PRD v2.1要求的核心功能
- 提升代码质量和用户体验

### 1.2 当前状态
| 指标 | 状态 |
|------|:----:|
| TypeScript 错误 | ✅ 0个 (已修复) |
| TradingView 组件 | ✅ 已修复 |
| 页面崩溃 | ⚠️ 待验证 |
| PRD 功能覆盖率 | ~70% |

---

## 2. 阶段规划

### Phase 1: TradingView 组件修复 ✅ 已完成
**状态**: 已完成
**报告**: `Phase1-Report-TradingView-Fix.md`

修复内容:
- [x] TradingView autosize 自适应模式
- [x] 日内交易页面布局优化
- [x] 策略回放页面图表填充
- [x] 实时交易页面三栏布局

---

### Phase 2: TypeScript 类型错误修复 ✅ 已完成
**状态**: 已完成
**报告**: `Phase2-Report-TypeScript-Fix.md`

修复内容:
- [x] import.meta.env 类型定义
- [x] antd Card size 属性扩展
- [x] 自定义 Card 组件 props 扩展
- [x] 清理 30+ 文件未使用导入
- [x] 修复模块导出错误
- [x] 120+ 错误 → 0 错误

---

### Phase 3: AI 连接状态指示器 (PRD 4.2) 🔄 进行中
**优先级**: P0
**预计工作量**: 中

#### 3.1 需求规格
| 状态 | 图标 | 颜色 | 描述 |
|------|:----:|:----:|------|
| 已连接 | ✓ | #22c55e | API正常，可对话 |
| 连接中 | ○ | #eab308 | 正在建立连接 |
| 未连接 | ✗ | #ef4444 | 连接失败 |
| 离线模式 | ⊘ | #6b7280 | 使用本地功能 |

#### 3.2 实现规格
```
文件: src/components/AI/AIStatusIndicator.tsx
功能:
  - 连接状态检测 (30秒轮询)
  - 网络状态监听 (online/offline)
  - 延迟显示
  - 重试功能
  - 当前模型显示
```

#### 3.3 验收标准
- [ ] 顶栏显示AI连接状态
- [ ] 4种状态正确切换
- [ ] 显示响应延迟
- [ ] 离线时自动切换状态
- [ ] 点击可重试连接

---

### Phase 4: 因子有效性验证面板 (PRD 4.3)
**优先级**: P0
**预计工作量**: 大

#### 4.1 需求规格
| 指标 | 数据来源 | 显示格式 |
|------|----------|----------|
| IC均值 | 回测计算 | 数值 + 进度条 |
| IC_IR | IC均值/IC标准差 | 数值 + 稳定性标签 |
| 多头年化收益 | 回测结果 | 百分比 (绿色) |
| 空头年化收益 | 回测结果 | 百分比 (红色) |
| 多空收益差 | 计算值 | 百分比 + 有效标签 |
| 有效性等级 | 综合判断 | 强/中/弱 + 星级 |
| 最佳市场环境 | 分析结果 | 文本描述 |
| 最差市场环境 | 分析结果 | 文本描述 |
| 建议搭配因子 | AI分析 | 因子标签列表 |

#### 4.2 实现规格
```
文件: src/components/Factor/FactorValidationPanel.tsx
依赖:
  - 后端API: /api/v1/factors/{id}/validation
  - 类型定义: src/types/factor.ts
布局:
  - 因子说明区
  - 历史回测验证区
  - 实测结论区
```

#### 4.3 验收标准
- [ ] 选择因子后显示验证结果
- [ ] IC指标正确显示
- [ ] 多空收益差计算正确
- [ ] 有效性等级判断准确
- [ ] 建议搭配因子显示

---

### Phase 5: 策略部署向导 (PRD 4.15)
**优先级**: P1
**预计工作量**: 大

#### 5.1 部署流程
```
Step 1: 模拟盘运行
  - 资金配置
  - 运行时长设置
  - 开始模拟

Step 2: 风险检查
  - 自动风险评估
  - 警告项展示
  - 确认继续

Step 3: 确认部署
  - 最终配置预览
  - 法律声明确认
  - 确认部署

Step 4: 开始监控
  - 部署成功提示
  - 跳转监控面板
```

#### 5.2 实现规格
```
文件: src/components/StrategyDeploy/DeployWizard.tsx
子组件:
  - StepSimulation.tsx (模拟盘)
  - StepRiskCheck.tsx (风险检查)
  - StepConfirm.tsx (确认部署)
  - StepMonitor.tsx (监控入口)
```

#### 5.3 验收标准
- [ ] 4步向导流程完整
- [ ] 模拟盘可正常运行
- [ ] 风险检查项完整
- [ ] 部署后跳转监控

---

### Phase 6: 策略冲突检测 (PRD 4.6)
**优先级**: P1
**预计工作量**: 大

#### 6.1 冲突类型定义
| 类型 | 描述 | 处理方式 |
|------|------|----------|
| 逻辑冲突 | 同策略对同股票相反信号 | 用户选择 |
| 执行冲突 | 不同策略需顺序执行 | 自动排序 |
| 资金冲突 | 资金不足执行全部 | 优先级排序 |

#### 6.2 实现规格
```
文件:
  - src/components/Conflict/ConflictList.tsx ✅ 已存在
  - src/components/Conflict/ConflictModal.tsx
  - src/components/Conflict/ConflictResolver.tsx
后端API:
  - GET /api/v1/conflicts
  - POST /api/v1/conflicts/{id}/resolve
```

#### 6.3 验收标准
- [ ] 冲突列表正确显示
- [ ] 冲突详情弹窗正常
- [ ] 用户可选择解决方案
- [ ] 解决后自动执行

---

### Phase 7: 交易归因系统 (PRD 4.5)
**优先级**: P1
**预计工作量**: 大

#### 7.1 归因内容
| 维度 | 分析内容 |
|------|----------|
| 因子贡献 | 各因子对收益的贡献度 |
| 时机贡献 | 入场/出场时机评估 |
| 行业贡献 | 行业配置的影响 |
| 风险贡献 | Beta/Alpha分解 |

#### 7.2 实现规格
```
文件:
  - src/components/Attribution/AttributionPanel.tsx
  - src/components/Attribution/FactorContribution.tsx
  - src/components/Attribution/TimingAnalysis.tsx
图表:
  - 因子贡献瀑布图
  - 时间序列归因
  - 行业配置饼图
```

#### 7.3 验收标准
- [ ] 每笔交易可查看归因
- [ ] 因子贡献度正确计算
- [ ] 图表正确渲染
- [ ] AI诊断建议显示

---

### Phase 8: 实盘vs回测监控 (PRD 4.12)
**优先级**: P1
**预计工作量**: 中

#### 8.1 监控阈值
| 监控项 | 黄色预警 | 红色预警 |
|--------|:--------:|:--------:|
| 收益差异 | >10% | >20% |
| 胜率差异 | >5% | >10% |
| 最大回撤差异 | >15% | >25% |
| 换手率差异 | >20% | >40% |

#### 8.2 实现规格
```
文件:
  - src/components/Monitor/LiveVsBacktestPanel.tsx
  - src/components/Monitor/DriftAlert.tsx
功能:
  - 实时对比图表
  - 偏离度计算
  - 预警通知
  - 历史记录
```

#### 8.3 验收标准
- [ ] 实时对比图表正常
- [ ] 偏离度计算准确
- [ ] 预警阈值触发正确
- [ ] 通知推送正常

---

### Phase 9: PDT规则管理增强 (PRD 4.7)
**优先级**: P1
**预计工作量**: 小

#### 9.1 显示内容
- 账户类型 (现金/保证金/PDT)
- 剩余日内交易次数 (0-3)
- 重置时间倒计时
- 解锁条件提示

#### 9.2 实现规格
```
文件:
  - src/components/PDT/PDTStatusCard.tsx
  - src/components/PDT/PDTWarning.tsx
集成:
  - 交易面板顶部
  - 下单前检查
```

#### 9.3 验收标准
- [ ] PDT状态正确显示
- [ ] 剩余次数实时更新
- [ ] 倒计时正确
- [ ] 超限时阻止下单

---

### Phase 10: 代码质量检查与优化
**优先级**: P0
**类型**: 持续性

#### 10.1 检查项
- TypeScript 编译 (`tsc --noEmit`)
- ESLint 检查
- 未使用导入清理
- 类型覆盖率

#### 10.2 执行命令
```bash
# TypeScript 检查
npx tsc --noEmit --skipLibCheck

# ESLint 检查
npx eslint src --ext .ts,.tsx

# 构建测试
npm run build
```

---

## 3. 报告规范

### 3.1 阶段报告模板
```markdown
# Phase X 阶段报告: [标题]

**日期**: YYYY-MM-DD
**状态**: 已完成/进行中/待开始
**优先级**: P0/P1/P2

## 1. 问题描述
[描述本阶段要解决的问题]

## 2. 修复方案
[详细说明修复方案]

## 3. 文件变更清单
[列出所有修改的文件]

## 4. 验收测试
[测试命令和结果]

## 5. 后续建议
[改进建议]
```

### 3.2 代码报告模板
```markdown
# Phase X 代码报告

**日期**: YYYY-MM-DD
**检测结果**: 通过/未通过

## TypeScript 检测
- 命令: `npx tsc --noEmit`
- 结果: X errors

## ESLint 检测
- 命令: `npx eslint src`
- 结果: X warnings, Y errors

## 构建测试
- 命令: `npm run build`
- 结果: 成功/失败

## 问题清单
[如有问题，列出待修复项]
```

---

## 4. 目录结构

```
F:\quantvision-v2\QuantVision v2.1\1月9号2.1版本优化\
├── SPEC-QuantVision-v2.1-优化计划.md (本文档)
├── Phase1-Report-TradingView-Fix.md ✅
├── Phase1-Code-Report.md
├── Phase2-Report-TypeScript-Fix.md ✅
├── Phase2-Code-Report.md
├── Phase3-Report-AIStatus.md
├── Phase3-Code-Report.md
├── Phase4-Report-FactorValidation.md
├── Phase4-Code-Report.md
├── ...
└── Final-Summary-Report.md
```

---

## 5. 执行状态

| Phase | 名称 | 状态 | 阶段报告 | 代码报告 |
|:-----:|------|:----:|:--------:|:--------:|
| 1 | TradingView修复 | ✅ 完成 | ✅ | ✅ |
| 2 | TypeScript修复 | ✅ 完成 | ✅ | ✅ |
| 3 | AI状态指示器 | ✅ 完成 | ✅ | ✅ |
| 4 | 因子验证面板 | ✅ 完成 | ✅ | ✅ |
| 5 | 策略部署向导 | ✅ 完成 | ✅ | ✅ |
| 6 | 策略冲突检测 | ✅ 完成 | ✅ | ✅ |
| 7 | 交易归因系统 | ✅ 完成 | ✅ | ✅ |
| 8 | 实盘vs回测监控 | ✅ 完成 | ✅ | ✅ |
| 9 | PDT规则增强 | ✅ 完成 | ✅ | ✅ |
| 10 | 代码质量检查 | ✅ 完成 | - | ✅ |

**最终状态**: 全部完成 (2026-01-09)

---

**文档版本**: 1.0
**创建时间**: 2026-01-09
**作者**: Claude Opus 4.5
