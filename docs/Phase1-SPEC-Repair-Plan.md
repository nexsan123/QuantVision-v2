# QuantVision v2.1 第一阶段修复计划

> **计划版本**: v1.0
> **创建日期**: 2026-01-07
> **计划目标**: 完善页面交互，Mock数据跑通全流程
> **计划方法**: SPEC (Specific, Prioritized, Estimated, Checklist)
> **阶段报告**: 每个Sprint完成后生成阶段报告

---

## 目录

1. [计划概述](#一计划概述)
2. [Sprint规划](#二sprint规划)
3. [Sprint 1: 数据持久化](#三sprint-1-数据持久化)
4. [Sprint 2: 流程断裂修复](#四sprint-2-流程断裂修复)
5. [Sprint 3: 实时监控重构](#五sprint-3-实时监控重构)
6. [Sprint 4: 日内交易完善](#六sprint-4-日内交易完善)
7. [Sprint 5: 集成测试](#七sprint-5-集成测试)
8. [验收标准](#八验收标准)
9. [风险与依赖](#九风险与依赖)

---

## 一、计划概述

### 1.1 目标

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           第一阶段目标                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. 数据持久化 - localStorage替代内存Mock，刷新不丢失                        │
│  2. 流程贯通 - 模板→策略→回测→部署 全流程无断裂                              │
│  3. UI完善 - 实时监控三栏布局、日内交易双图+环境切换                          │
│  4. 交互完整 - 所有按钮点击有响应，所有流程可走通                             │
│                                                                             │
│  不包含:                                                                    │
│  ❌ 真实回测计算 (第二阶段)                                                  │
│  ❌ 真实行情数据 (第二阶段)                                                  │
│  ❌ 真实交易执行 (第二阶段)                                                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 成功标准

| 标准 | 描述 | 验收方式 |
|------|------|----------|
| 数据持久 | 刷新页面后数据不丢失 | 手动测试 |
| 流程贯通 | 5个核心流程全部可走通 | 流程测试 |
| UI符合PRD | 实时监控三栏、日内双图 | 视觉检查 |
| 无控制台错误 | TypeScript编译通过 | `npm run build` |
| 交互完整 | 所有按钮有响应 | 手动测试 |

### 1.3 Sprint概览

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Sprint 1        Sprint 2        Sprint 3        Sprint 4        Sprint 5  │
│  数据持久化      流程断裂修复     实时监控重构     日内交易完善     集成测试   │
│                                                                             │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐  │
│  │ F1-F3   │───▶│ F4-F7   │───▶│ F8-F11  │───▶│ F12-F15 │───▶│ F16-F18 │  │
│  │ 3任务   │    │ 4任务   │    │ 4任务   │    │ 4任务   │    │ 3任务   │  │
│  └─────────┘    └─────────┘    └─────────┘    └─────────┘    └─────────┘  │
│       │              │              │              │              │        │
│       ▼              ▼              ▼              ▼              ▼        │
│   阶段报告1      阶段报告2      阶段报告3      阶段报告4      最终报告     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 二、Sprint规划

### 2.1 任务总表

| Sprint | 任务ID | 任务名称 | 优先级 | 依赖 |
|--------|--------|----------|:------:|------|
| **Sprint 1** | F1 | localStorage持久化层 | P0 | - |
| | F2 | 策略数据持久化 | P0 | F1 |
| | F3 | 部署数据持久化 | P0 | F1 |
| **Sprint 2** | F4 | 模板→策略创建修复 | P0 | F2 |
| | F5 | 策略→回测连接修复 | P0 | F2 |
| | F6 | 回测→部署连接修复 | P0 | F3 |
| | F7 | 部署→运行监控连接 | P0 | F3 |
| **Sprint 3** | F8 | 实时监控三栏布局 | P1 | F7 |
| | F9 | 信号雷达面板完善 | P1 | F8 |
| | F10 | TradingView图表区 | P1 | F8 |
| | F11 | 策略动态面板 | P1 | F8 |
| **Sprint 4** | F12 | 日内交易路由修复 | P1 | - |
| | F13 | 双图布局实现 | P1 | F12 |
| | F14 | 环境切换器添加 | P1 | F12 |
| | F15 | 盘前→交易流程贯通 | P1 | F12 |
| **Sprint 5** | F16 | 核心流程测试 | P0 | All |
| | F17 | TypeScript编译检查 | P0 | All |
| | F18 | 全流程验收测试 | P0 | All |

### 2.2 文件修改预览

| Sprint | 预计修改文件 |
|--------|-------------|
| Sprint 1 | `services/storageService.ts` (新建), `services/strategyService.ts`, `types/` |
| Sprint 2 | `TemplateDetailModal.tsx`, `BacktestCenter/index.tsx`, `DeploymentWizard.tsx`, `MyStrategies/index.tsx` |
| Sprint 3 | `pages/Trading/index.tsx`, `components/SignalRadar/`, 新建布局组件 |
| Sprint 4 | `App.tsx`, `Intraday/IntradayTradingPage.tsx`, `Intraday/PreMarketScanner.tsx` |
| Sprint 5 | `docs/` 测试报告 |

---

## 三、Sprint 1: 数据持久化

### 3.1 概述

**目标**: 建立localStorage持久化层，解决刷新数据丢失问题

**产出**:
- `storageService.ts` 持久化服务
- 策略数据持久化
- 部署数据持久化

---

### F1: localStorage持久化层

#### 任务详情

| 属性 | 值 |
|------|---|
| 任务ID | F1 |
| 优先级 | P0 |
| 依赖 | 无 |
| 修改文件 | `frontend/src/services/storageService.ts` (新建) |

#### 具体实现

**新建文件**: `frontend/src/services/storageService.ts`

```typescript
/**
 * localStorage 持久化服务
 * 提供类型安全的本地存储操作
 */

const STORAGE_PREFIX = 'qv_'  // QuantVision 前缀

// 存储键定义
export const STORAGE_KEYS = {
  STRATEGIES: `${STORAGE_PREFIX}strategies`,
  DEPLOYMENTS: `${STORAGE_PREFIX}deployments`,
  USER_SETTINGS: `${STORAGE_PREFIX}settings`,
  BACKTEST_HISTORY: `${STORAGE_PREFIX}backtest_history`,
} as const

/**
 * 通用存储操作
 */
export function setItem<T>(key: string, value: T): void {
  try {
    localStorage.setItem(key, JSON.stringify(value))
  } catch (error) {
    console.error(`Failed to save to localStorage: ${key}`, error)
  }
}

export function getItem<T>(key: string, defaultValue: T): T {
  try {
    const item = localStorage.getItem(key)
    return item ? JSON.parse(item) : defaultValue
  } catch (error) {
    console.error(`Failed to read from localStorage: ${key}`, error)
    return defaultValue
  }
}

export function removeItem(key: string): void {
  localStorage.removeItem(key)
}

/**
 * 策略存储操作
 */
export const strategyStorage = {
  getAll: () => getItem<Strategy[]>(STORAGE_KEYS.STRATEGIES, []),
  save: (strategies: Strategy[]) => setItem(STORAGE_KEYS.STRATEGIES, strategies),
  clear: () => removeItem(STORAGE_KEYS.STRATEGIES),
}

/**
 * 部署存储操作
 */
export const deploymentStorage = {
  getAll: () => getItem<Deployment[]>(STORAGE_KEYS.DEPLOYMENTS, []),
  save: (deployments: Deployment[]) => setItem(STORAGE_KEYS.DEPLOYMENTS, deployments),
  clear: () => removeItem(STORAGE_KEYS.DEPLOYMENTS),
}

/**
 * 初始化存储 (首次使用时填充默认数据)
 */
export function initializeStorage(defaultStrategies: Strategy[], defaultDeployments: Deployment[]): void {
  if (strategyStorage.getAll().length === 0) {
    strategyStorage.save(defaultStrategies)
  }
  if (deploymentStorage.getAll().length === 0) {
    deploymentStorage.save(defaultDeployments)
  }
}
```

#### 验收检查点

- [ ] 新建 `storageService.ts` 文件
- [ ] 实现 `setItem`, `getItem`, `removeItem` 通用方法
- [ ] 实现 `strategyStorage` 对象
- [ ] 实现 `deploymentStorage` 对象
- [ ] 实现 `initializeStorage` 初始化函数
- [ ] TypeScript 类型正确

---

### F2: 策略数据持久化

#### 任务详情

| 属性 | 值 |
|------|---|
| 任务ID | F2 |
| 优先级 | P0 |
| 依赖 | F1 |
| 修改文件 | `frontend/src/services/strategyService.ts` |

#### 具体实现

**修改**: `strategyService.ts`

```typescript
// 修改前
let mockStrategies: Strategy[] = [...]  // 内存数组

// 修改后
import { strategyStorage, initializeStorage } from './storageService'

// 默认数据 (首次使用)
const DEFAULT_STRATEGIES: Strategy[] = [...]

// 初始化
initializeStorage(DEFAULT_STRATEGIES, [])

// 获取策略列表
export async function getStrategies(params?: StrategyFilterParams): Promise<StrategyListResponse> {
  await simulateDelay()

  let strategies = strategyStorage.getAll()  // 从localStorage读取

  // 筛选逻辑...

  return { total: strategies.length, items: strategies }
}

// 创建策略
export async function createStrategy(request: StrategyCreateRequest): Promise<Strategy> {
  await simulateDelay()

  const strategies = strategyStorage.getAll()
  const newStrategy: Strategy = {
    id: `stg-${Date.now()}`,
    ...request,
    // ...
  }

  strategies.push(newStrategy)
  strategyStorage.save(strategies)  // 保存到localStorage

  return newStrategy
}

// 其他方法类似修改...
```

#### 验收检查点

- [ ] 引入 `storageService`
- [ ] `getStrategies` 从 localStorage 读取
- [ ] `createStrategy` 保存到 localStorage
- [ ] `updateStrategy` 更新 localStorage
- [ ] `deleteStrategy` 从 localStorage 删除
- [ ] 刷新页面后数据保留
- [ ] 无 TypeScript 错误

---

### F3: 部署数据持久化

#### 任务详情

| 属性 | 值 |
|------|---|
| 任务ID | F3 |
| 优先级 | P0 |
| 依赖 | F1 |
| 修改文件 | `frontend/src/services/deploymentService.ts` (新建) |

#### 具体实现

**新建文件**: `frontend/src/services/deploymentService.ts`

```typescript
/**
 * 部署服务 - 管理策略部署实例
 */
import { deploymentStorage } from './storageService'
import type { Deployment, DeploymentConfig } from '../types/deployment'

// 默认部署数据
const DEFAULT_DEPLOYMENTS: Deployment[] = [...]

// 初始化
if (deploymentStorage.getAll().length === 0) {
  deploymentStorage.save(DEFAULT_DEPLOYMENTS)
}

export async function getDeployments(filters?: DeploymentFilters): Promise<Deployment[]> {
  // 从localStorage读取并筛选
}

export async function createDeployment(config: DeploymentConfig): Promise<Deployment> {
  // 创建部署并保存到localStorage
}

export async function updateDeploymentStatus(id: string, status: DeploymentStatus): Promise<Deployment> {
  // 更新状态
}

export async function deleteDeployment(id: string): Promise<void> {
  // 删除部署
}
```

#### 验收检查点

- [ ] 新建 `deploymentService.ts` 文件
- [ ] 实现 `getDeployments`
- [ ] 实现 `createDeployment`
- [ ] 实现 `updateDeploymentStatus`
- [ ] 实现 `deleteDeployment`
- [ ] 刷新页面后部署数据保留

---

### Sprint 1 完成标准

| 检查项 | 验收方式 |
|--------|----------|
| 创建策略后刷新，策略仍存在 | 手动测试 |
| 删除策略后刷新，策略已删除 | 手动测试 |
| 部署数据持久化 | 手动测试 |
| TypeScript 编译通过 | `npm run build` |

**阶段报告**: Sprint 1 完成后生成 `Sprint1-Completion-Report.md`

---

## 四、Sprint 2: 流程断裂修复

### 4.1 概述

**目标**: 修复核心流程的断裂点，实现端到端贯通

**产出**:
- 模板→策略创建流程贯通
- 策略→回测流程贯通
- 回测→部署流程贯通
- 部署→运行监控流程贯通

---

### F4: 模板→策略创建修复

#### 任务详情

| 属性 | 值 |
|------|---|
| 任务ID | F4 |
| 优先级 | P0 |
| 依赖 | F2 |
| 修改文件 | `components/Template/TemplateDetailModal.tsx` |

#### 问题描述

当前模板创建策略后，虽然调用了 `createStrategy()`，但：
1. 数据存在内存中，刷新丢失
2. 跳转到策略编辑器后，需要能正确加载新创建的策略

#### 具体实现

```typescript
// TemplateDetailModal.tsx

// 确保创建的策略能被正确读取
const handleUseTemplate = async () => {
  setCreating(true)
  try {
    const config = buildStrategyConfig()
    const newStrategy = await createStrategy({
      name: strategyName || `我的${template.name}`,
      source: 'template',
      templateId: template.template_id,
      config,
      tags: template.tags,
    })

    message.success('策略已创建')
    onClose()

    // 跳转到策略编辑器，携带ID
    navigate(`/strategy?id=${newStrategy.id}`)
  } catch (error) {
    message.error('创建失败')
  } finally {
    setCreating(false)
  }
}
```

#### 验收检查点

- [ ] 从模板创建策略成功
- [ ] 跳转到编辑器后能加载策略
- [ ] 刷新编辑器页面后策略仍存在
- [ ] 在"我的策略"列表能看到新创建的策略

---

### F5: 策略→回测连接修复

#### 任务详情

| 属性 | 值 |
|------|---|
| 任务ID | F5 |
| 优先级 | P0 |
| 依赖 | F2 |
| 修改文件 | `pages/BacktestCenter/index.tsx`, `pages/StrategyBuilder/index.tsx` |

#### 问题描述

1. 策略构建器"运行回测"按钮需正确跳转
2. 回测中心需从持久化存储读取策略列表
3. 回测完成后需更新策略的 `lastBacktest` 字段

#### 具体实现

```typescript
// StrategyBuilder/index.tsx
const handleRunBacktest = async () => {
  if (isDirty) {
    await handleSave()
  }
  if (existingStrategy) {
    navigate(`/backtest?strategyId=${existingStrategy.id}`)
  }
}

// BacktestCenter/index.tsx
// 回测完成后更新策略
const handleBacktestComplete = async () => {
  const backtestResult: BacktestSummary = {
    backtestId: `bt-${Date.now()}`,
    annualReturn: mockMetrics.annualReturn,
    sharpeRatio: mockMetrics.sharpe,
    maxDrawdown: mockMetrics.maxDrawdown,
    winRate: mockMetrics.winRate,
    startDate: dateRange[0].format('YYYY-MM-DD'),
    endDate: dateRange[1].format('YYYY-MM-DD'),
    completedAt: new Date().toISOString(),
  }

  // 更新策略的lastBacktest字段
  await updateBacktestResult(selectedStrategy.id, backtestResult)

  setShowCompleteModal(true)
}
```

#### 验收检查点

- [ ] 策略编辑器"运行回测"正确跳转
- [ ] 回测中心策略选择器显示所有策略
- [ ] 选择策略后显示策略信息
- [ ] 回测完成后策略的lastBacktest更新
- [ ] 刷新后lastBacktest仍存在

---

### F6: 回测→部署连接修复

#### 任务详情

| 属性 | 值 |
|------|---|
| 任务ID | F6 |
| 优先级 | P0 |
| 依赖 | F3, F5 |
| 修改文件 | `pages/BacktestCenter/index.tsx`, `components/Deployment/DeploymentWizard.tsx` |

#### 问题描述

1. 回测完成弹窗的"部署到模拟盘"需触发部署向导
2. 部署向导完成后需真正创建部署记录
3. 部署记录需要持久化

#### 具体实现

```typescript
// BacktestCenter/index.tsx
const handleDeploy = () => {
  setShowCompleteModal(false)
  setShowDeploymentWizard(true)  // 显示部署向导
}

// 添加部署向导组件
{selectedStrategy && (
  <DeploymentWizard
    strategyId={selectedStrategy.id}
    strategyName={selectedStrategy.name}
    strategyConfig={selectedStrategy.config}
    visible={showDeploymentWizard}
    onClose={() => setShowDeploymentWizard(false)}
    onComplete={async (config) => {
      // 调用deploymentService创建部署
      await createDeployment({
        ...config,
        strategyId: selectedStrategy.id,
        strategyName: selectedStrategy.name,
      })
      message.success('部署成功')
      setShowDeploymentWizard(false)
      navigate('/my-strategies?tab=running')
    }}
  />
)}
```

#### 验收检查点

- [ ] 回测完成后点击"部署到模拟盘"显示部署向导
- [ ] 部署向导完成后创建部署记录
- [ ] 部署记录持久化（刷新后仍存在）
- [ ] 跳转到"我的策略-运行中"Tab

---

### F7: 部署→运行监控连接

#### 任务详情

| 属性 | 值 |
|------|---|
| 任务ID | F7 |
| 优先级 | P0 |
| 依赖 | F6 |
| 修改文件 | `pages/MyStrategies/index.tsx` |

#### 问题描述

1. "运行中"Tab需从deploymentService读取数据
2. 点击部署记录应跳转到交易监控页面
3. 启动/暂停操作需更新部署状态

#### 具体实现

```typescript
// MyStrategies/index.tsx

import { getDeployments, updateDeploymentStatus } from '@/services/deploymentService'

// 加载部署列表
const fetchDeployments = useCallback(async () => {
  setDeploymentsLoading(true)
  try {
    const result = await getDeployments({
      status: deploymentStatusFilter || undefined,
      environment: deploymentEnvFilter || undefined,
    })
    setDeployments(result)
  } finally {
    setDeploymentsLoading(false)
  }
}, [deploymentStatusFilter, deploymentEnvFilter])

// 启动部署
const handleStartDeployment = async (id: string) => {
  await updateDeploymentStatus(id, 'running')
  message.success('启动成功')
  fetchDeployments()
}

// 点击部署记录跳转到监控
const handleViewDeployment = (deployment: Deployment) => {
  navigate(`/trading?deploymentId=${deployment.deploymentId}`)
}
```

#### 验收检查点

- [ ] "运行中"Tab显示持久化的部署数据
- [ ] 启动/暂停按钮更新状态
- [ ] 状态更新持久化
- [ ] 点击部署可跳转到交易监控

---

### Sprint 2 完成标准

| 检查项 | 验收方式 |
|--------|----------|
| 模板→创建策略→编辑器 流程通畅 | 流程测试 |
| 策略→回测 流程通畅 | 流程测试 |
| 回测→部署 流程通畅 | 流程测试 |
| 部署→监控 流程通畅 | 流程测试 |
| 所有数据刷新后保留 | 手动测试 |

**阶段报告**: Sprint 2 完成后生成 `Sprint2-Completion-Report.md`

---

## 五、Sprint 3: 实时监控重构

### 5.1 概述

**目标**: 按PRD 4.16设计重构实时交易监控页面为三栏布局

**产出**:
- 三栏布局框架
- 信号雷达面板 (280px)
- TradingView图表区 (自适应)
- 策略动态面板 (288px)

---

### F8: 实时监控三栏布局

#### 任务详情

| 属性 | 值 |
|------|---|
| 任务ID | F8 |
| 优先级 | P1 |
| 依赖 | F7 |
| 修改文件 | `pages/Trading/index.tsx` (重构) |

#### PRD设计规格

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  顶部导航栏 (h=56px)                                                         │
│  [Logo] [🔍搜索] [策略:xxx▼] [🟢运行中] [账户$xxx] [PDT:x/3] [⚙️]            │
├───────────────┬─────────────────────────────────────────┬───────────────────┤
│               │                                         │                   │
│  📡 信号雷达  │           TradingView 图表              │    策略动态       │
│   (w=280px)   │              (自适应)                   │   (w=288px)       │
│               │                                         │                   │
│  ┌──────────┐ │  ┌─────────────────────────────────────┐ │  ┌─────────────┐ │
│  │ 股票池   │ │  │                                     │ │  │ 信号通知   │ │
│  │ 搜索框   │ │  │      K线 + 技术指标 + 信号标记      │ │  │ 交易记录   │ │
│  │ 信号列表 │ │  │                                     │ │  │ 持仓管理   │ │
│  │          │ │  │                                     │ │  │ 快速交易   │ │
│  └──────────┘ │  └─────────────────────────────────────┘ │  └─────────────┘ │
│               │                                         │                   │
└───────────────┴─────────────────────────────────────────┴───────────────────┘
```

#### 具体实现

```typescript
// pages/Trading/index.tsx (重构)

export default function TradingMonitor() {
  return (
    <div className="h-screen flex flex-col bg-dark-bg">
      {/* 顶部导航栏 */}
      <TradingHeader />

      {/* 三栏主体 */}
      <div className="flex-1 flex overflow-hidden">
        {/* 左侧: 信号雷达 */}
        <div className="w-[280px] border-r border-gray-700 flex-shrink-0">
          <SignalRadarPanel strategyId={currentStrategyId} />
        </div>

        {/* 中间: 图表区 */}
        <div className="flex-1 flex flex-col">
          <ChartToolbar />
          <TradingViewChart symbol={currentSymbol} />
        </div>

        {/* 右侧: 策略动态 */}
        <div className="w-[288px] border-l border-gray-700 flex-shrink-0">
          <StrategyActivityPanel />
        </div>
      </div>
    </div>
  )
}
```

#### 验收检查点

- [ ] 三栏布局正确显示
- [ ] 左侧固定宽度 280px
- [ ] 右侧固定宽度 288px
- [ ] 中间自适应
- [ ] 响应式 (小屏幕可折叠侧边栏)

---

### F9: 信号雷达面板完善

#### 任务详情

| 属性 | 值 |
|------|---|
| 任务ID | F9 |
| 优先级 | P1 |
| 依赖 | F8 |
| 修改文件 | `components/SignalRadar/index.tsx`, `SignalList.tsx` |

#### 功能清单

- [ ] 股票池选择器 (SP500/NASDAQ100/自选)
- [ ] 搜索框 (Ctrl+K 快捷键)
- [ ] 信号状态分布统计
- [ ] 信号列表 (按状态分组)
- [ ] 信号状态颜色: 🔴持仓 🟢买入 🟠卖出 🟡接近 ⚪监控

---

### F10: TradingView图表区

#### 任务详情

| 属性 | 值 |
|------|---|
| 任务ID | F10 |
| 优先级 | P1 |
| 依赖 | F8 |
| 修改文件 | `components/Chart/TradingViewChart.tsx` |

#### 功能清单

- [ ] 图表工具栏 (股票选择、时间周期、指标、画线)
- [ ] TradingView Widget 占位区域 (后续集成真实Widget)
- [ ] 信号标记层 (买入/卖出点标记)

---

### F11: 策略动态面板

#### 任务详情

| 属性 | 值 |
|------|---|
| 任务ID | F11 |
| 优先级 | P1 |
| 依赖 | F8 |
| 修改文件 | 新建 `components/TradingCenter/StrategyActivityPanel.tsx` |

#### 功能清单

- [ ] 信号通知列表
- [ ] 今日交易记录
- [ ] 当前持仓概览
- [ ] 快速交易表单

---

### Sprint 3 完成标准

| 检查项 | 验收方式 |
|--------|----------|
| 三栏布局符合PRD设计 | 视觉检查 |
| 信号雷达功能完整 | 功能测试 |
| 图表区正确显示 | 视觉检查 |
| 策略动态面板完整 | 功能测试 |

**阶段报告**: Sprint 3 完成后生成 `Sprint3-Completion-Report.md`

---

## 六、Sprint 4: 日内交易完善

### 6.1 概述

**目标**: 完善日内交易页面，实现PRD 4.18设计

**产出**:
- 盘前→交易流程贯通
- 双图布局 (1分钟+5分钟)
- 环境切换器
- 止盈止损面板

---

### F12: 日内交易路由修复

#### 任务详情

| 属性 | 值 |
|------|---|
| 任务ID | F12 |
| 优先级 | P1 |
| 依赖 | - |
| 修改文件 | `App.tsx`, 新建状态管理 |

#### 问题描述

当前路由配置:
```typescript
<Route path="intraday" element={<PreMarketScanner onConfirmWatchlist={() => {}} />} />
<Route path="intraday/trading" element={<IntradayTradingPage watchlistSymbols={['NVDA', 'TSLA', 'AAPL']} />} />
```

问题:
1. `onConfirmWatchlist` 是空函数
2. `watchlistSymbols` 是硬编码

#### 解决方案

使用状态管理或URL参数传递监控列表:

```typescript
// App.tsx
const [intradayWatchlist, setIntradayWatchlist] = useState<string[]>([])

<Route path="intraday" element={
  <PreMarketScanner
    strategyId="intraday-momentum"
    onConfirmWatchlist={(symbols) => {
      setIntradayWatchlist(symbols)
      navigate('/intraday/trading')
    }}
  />
} />

<Route path="intraday/trading" element={
  <IntradayTradingPage
    watchlistSymbols={intradayWatchlist.length > 0 ? intradayWatchlist : ['NVDA', 'TSLA', 'AAPL']}
    strategyId="intraday-momentum"
    onBack={() => navigate('/intraday')}
  />
} />
```

#### 验收检查点

- [ ] 盘前扫描器选择股票后能传递到交易页面
- [ ] 交易页面显示选中的股票列表
- [ ] 返回按钮能回到扫描器

---

### F13: 双图布局实现

#### 任务详情

| 属性 | 值 |
|------|---|
| 任务ID | F13 |
| 优先级 | P1 |
| 依赖 | F12 |
| 修改文件 | `components/Intraday/IntradayTradingPage.tsx` |

#### PRD设计

```
┌─────────────────────────────────────────────────────────────────┐
│  主图区域 (70% 高度)                                             │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                    1分钟 K线图                               │ │
│  │                                                             │ │
│  └─────────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│  辅图区域 (30% 高度)                                             │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                    5分钟 K线图 (宏观视图)                     │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

#### 验收检查点

- [ ] 双图垂直排列
- [ ] 主图 70% 高度，辅图 30%
- [ ] 图表联动 (点击同步)

---

### F14: 环境切换器添加

#### 任务详情

| 属性 | 值 |
|------|---|
| 任务ID | F14 |
| 优先级 | P1 |
| 依赖 | F12 |
| 修改文件 | `components/Intraday/IntradayTradingPage.tsx` |

#### 验收检查点

- [ ] 添加 EnvironmentSwitch 组件
- [ ] 环境切换时显示确认提示
- [ ] 不同环境显示不同标识

---

### F15: 盘前→交易流程贯通

#### 任务详情

| 属性 | 值 |
|------|---|
| 任务ID | F15 |
| 优先级 | P1 |
| 依赖 | F12, F13, F14 |
| 修改文件 | 整合测试 |

#### 验收检查点

- [ ] 完整流程: 盘前扫描 → 选择股票 → 确认 → 进入交易
- [ ] 可以返回修改监控列表
- [ ] 交易页面功能完整

---

### Sprint 4 完成标准

| 检查项 | 验收方式 |
|--------|----------|
| 盘前→交易流程贯通 | 流程测试 |
| 双图布局正确 | 视觉检查 |
| 环境切换器工作 | 功能测试 |
| 止盈止损面板完整 | 功能测试 |

**阶段报告**: Sprint 4 完成后生成 `Sprint4-Completion-Report.md`

---

## 七、Sprint 5: 集成测试

### 7.1 概述

**目标**: 全面测试所有修复，确保质量

---

### F16: 核心流程测试

#### 测试场景

| 场景ID | 场景描述 | 预期结果 |
|--------|----------|----------|
| TC-01 | 从模板创建策略 | 策略创建成功，可在"我的策略"查看 |
| TC-02 | 编辑并保存策略 | 修改保存成功，刷新后保留 |
| TC-03 | 运行回测 | 回测完成，显示结果，lastBacktest更新 |
| TC-04 | 部署到模拟盘 | 部署创建成功，在"运行中"可见 |
| TC-05 | 启动/暂停部署 | 状态正确切换 |
| TC-06 | 盘前扫描→日内交易 | 流程贯通，数据传递正确 |
| TC-07 | 环境切换 | 切换成功，显示正确标识 |

---

### F17: TypeScript编译检查

```bash
cd frontend && npm run build
```

**通过标准**: 无编译错误

---

### F18: 全流程验收测试

完整走通所有流程，生成最终验收报告。

---

### Sprint 5 完成标准

**最终报告**: 生成 `Phase1-Final-Report.md`

---

## 八、验收标准

### 8.1 功能验收

| 验收项 | 标准 |
|--------|------|
| 数据持久化 | 所有数据刷新后保留 |
| 流程贯通 | 5个核心流程无断裂 |
| UI完整 | 三栏布局、双图布局正确 |
| 交互响应 | 所有按钮有响应 |

### 8.2 技术验收

| 验收项 | 标准 |
|--------|------|
| TypeScript | `npm run build` 无错误 |
| Console | 无红色错误 |
| 响应式 | 1200px以下可用 |

---

## 九、风险与依赖

### 9.1 风险

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| localStorage容量限制 | 数据过多时可能失败 | 定期清理旧数据 |
| 组件重构影响范围大 | 可能引入新bug | 每Sprint做回归测试 |

### 9.2 依赖

| 依赖 | 说明 |
|------|------|
| 现有组件库 | SignalRadar, DeploymentWizard等 |
| 类型定义 | Strategy, Deployment, Signal等 |

---

## 附录A: 阶段报告模板

每个Sprint完成后生成的阶段报告应包含:

```markdown
# Sprint X 完成报告

## 概述
- 完成日期:
- 完成任务:
- 未完成任务:

## 任务完成详情

### FX: 任务名称
- 状态: ✅ 完成 / ⚠️ 部分完成 / ❌ 未完成
- 修改文件:
- 验收检查点:
  - [x] 检查项1
  - [x] 检查项2
- 问题与解决:

## 测试结果
- TypeScript编译:
- 功能测试:
- 发现的问题:

## 下一步
- Sprint X+1 准备事项
```

---

*计划创建时间: 2026-01-07*
*计划版本: v1.0*
