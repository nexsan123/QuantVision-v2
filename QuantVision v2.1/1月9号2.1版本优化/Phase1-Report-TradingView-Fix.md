# Phase 1 阶段报告: TradingView 布局修复

**日期**: 2026-01-09
**状态**: 已完成
**优先级**: P0

---

## 1. 问题描述

根据 PRD 4.16-4.18 和审计报告，以下页面的 TradingView 图表存在布局问题：
- 日内交易页面 (`/intraday`) - 图表未填满中间工作台
- 策略回放页面 (`/strategy/replay`) - 图表未填满中间工作台
- 实时交易页面 (`/trading-stream`) - 缺少图表组件

**根本原因**: TradingViewChart 组件使用固定高度 (`height=500px`)，不支持自适应布局 (`autosize`)。

---

## 2. 修复方案

### 2.1 TradingViewChart 组件增强

**文件**: `src/components/Chart/TradingViewChart.tsx`

**修改内容**:
1. 新增 `autosize` 属性，默认启用自适应模式
2. 新增 `className` 属性，支持自定义样式
3. 添加加载状态 (`loading`) 和错误处理 (`error`)
4. 添加重试功能 (`handleRetry`)
5. 优化容器样式计算逻辑

**新增属性**:
```typescript
interface TradingViewChartProps {
  height?: number | string  // 支持数字或 '100%'
  autosize?: boolean        // 自动填满父容器 (默认: true)
  className?: string        // 支持自定义样式
}
```

**关键代码变更**:
```typescript
// 配置对象 - 根据 autosize 决定尺寸策略
const widgetConfig: any = {
  autosize: autosize,  // 自适应模式
  // ...
}

// 非自适应模式时设置固定尺寸
if (!autosize) {
  widgetConfig.height = typeof height === 'number' ? height : 500
  widgetConfig.width = '100%'
}
```

### 2.2 日内交易页面修复

**文件**: `src/components/Intraday/IntradayTradingPage.tsx`

**修改内容**:
1. 中间图表区域使用 `flex-[2]` 让主图占据更多空间
2. 添加 `autosize={true}` 属性让图表自适应
3. 设置 `min-h-[300px]` 确保最小高度
4. 添加 `min-w-0` 防止 flex 溢出

**布局结构**:
```
┌─────────────────────────────────────────────────────────┐
│ 顶部栏: PDT规则 + 当前股票信息                              │
├────────┬──────────────────────────────────┬─────────────┤
│        │ 5min 主图 (flex-[2])              │             │
│ 监控   │ TradingView autosize             │ 止盈止损    │
│ 列表   ├──────────────────────────────────┤             │
│ 100px  │ 1min 细节图 (flex-1)              │ 交易记录    │
│        ├──────────────────────────────────┤ 320px       │
│        │ 快速交易面板 (130px)               │             │
├────────┴──────────────────────────────────┴─────────────┤
│ 底部状态栏                                               │
└─────────────────────────────────────────────────────────┘
```

### 2.3 策略回放页面修复

**文件**: `src/pages/StrategyReplay/index.tsx`

**修改内容**:
1. K线图区域添加 `autosize={true}`
2. 添加 `min-h-[400px]` 确保最小高度
3. 添加 `min-h-0` 和 `min-w-0` 防止 flex 溢出
4. 回放进度覆盖层 z-index 调整为 20

### 2.4 实时交易页面增强

**文件**: `src/pages/TradingStream/index.tsx`

**修改内容**:
1. 改为三栏布局 (事件流 | 图表 | 行情+持仓)
2. 中间添加 TradingViewChart 组件
3. 新增股票选择器 (`selectedSymbol` 状态)
4. 图表区域使用 `autosize={true}` 填满工作台

**布局结构**:
```
┌─────────────────────────────────────────────────────────┐
│ 页面头部: 标题 + 连接控制                                  │
├─────────────────────────────────────────────────────────┤
│ 账户摘要: 总资产 | 现金 | 市值 | 盈亏                       │
├────────────┬────────────────────────────┬───────────────┤
│ 交易事件    │ TradingView 实时图表        │ 实时行情      │
│ 事件流      │ 股票选择器                  │               │
│ 360px      │ autosize                   │ 当前持仓      │
│            │ 填满中间工作台              │ 300px         │
└────────────┴────────────────────────────┴───────────────┘
```

---

## 3. 验收测试

### 3.1 TradingViewChart 组件
- [x] 支持 autosize 自适应模式
- [x] 支持固定高度模式
- [x] 加载状态显示
- [x] 错误处理和重试功能
- [x] 组件类型定义完整

### 3.2 日内交易页面
- [x] 主图 (5min) 填满大部分空间
- [x] 细节图 (1min) 显示正常
- [x] 快速交易面板固定高度
- [x] 三栏布局正确

### 3.3 策略回放页面
- [x] K线图填满中间工作台
- [x] 回放进度覆盖层正确显示
- [x] 右侧面板正常滚动

### 3.4 实时交易页面
- [x] 新增 TradingView 图表
- [x] 三栏布局正确
- [x] 股票选择器功能正常

---

## 4. 文件变更清单

| 文件路径 | 变更类型 | 行数 |
|---------|:--------:|:----:|
| `src/components/Chart/TradingViewChart.tsx` | 修改 | +80 |
| `src/components/Intraday/IntradayTradingPage.tsx` | 修改 | +15 |
| `src/pages/StrategyReplay/index.tsx` | 修改 | +8 |
| `src/pages/TradingStream/index.tsx` | 修改 | +60 |

---

## 5. TypeScript 检查结果

**新增错误**: 0
**修复状态**: 所有修改文件无类型错误

---

## 6. 后续建议

1. **性能优化**: 考虑添加图表缓存，避免切换股票时重复加载
2. **错误监控**: 集成 Sentry 或类似服务，监控 TradingView 加载失败率
3. **离线支持**: 添加 TradingView 库的本地备份，防止 CDN 故障

---

**报告生成**: Claude Opus 4.5
**版本**: Phase 1 v1.0
