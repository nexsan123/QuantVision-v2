# Phase 6 阶段报告: 策略冲突检测

**日期**: 2026-01-09
**状态**: 已完成 (组件已存在)
**优先级**: P1

---

## 1. 需求分析

根据 PRD 4.6，策略冲突检测需要实现：
- 逻辑冲突：同策略类型对同股票发出相反信号
- 执行冲突：不同策略类型需顺序执行
- 资金冲突：资金不足执行全部

---

## 2. 现有组件分析

### 2.1 组件清单
| 组件 | 路径 | 状态 |
|------|------|:----:|
| ConflictList | `src/components/Conflict/ConflictList.tsx` | ✅ |
| ConflictModal | `src/components/Conflict/ConflictModal.tsx` | ✅ |
| ConflictSummaryCard | `src/components/Conflict/ConflictList.tsx` | ✅ |
| conflict.ts (types) | `src/types/conflict.ts` | ✅ |

### 2.2 类型定义

#### 冲突类型
| 类型 | 标识 | 图标 | 描述 |
|------|------|:----:|------|
| 逻辑冲突 | logic | ⚔️ | 同一股票存在相反信号 |
| 执行冲突 | execution | 💰 | 资金或仓位限制 |
| 超时冲突 | timeout | ⏰ | 信号已超过有效期 |
| 重复冲突 | duplicate | 📋 | 多策略相同买入信号 |

#### 严重程度
| 级别 | 颜色 | 描述 |
|------|------|------|
| 严重 | 红色 | 必须处理后才能继续 |
| 警告 | 黄色 | 建议处理，可忽略 |
| 提示 | 蓝色 | 仅供参考 |

#### 解决方案
| 方案 | 图标 | 描述 |
|------|:----:|------|
| 执行策略A | 1️⃣ | 执行第一个策略信号 |
| 执行策略B | 2️⃣ | 执行第二个策略信号 |
| 同时执行 | ✅ | 同时执行两个信号 |
| 全部取消 | ❌ | 取消两个信号 |
| 减仓执行 | 📉 | 减少执行数量 |
| 延迟执行 | ⏳ | 等待条件满足 |
| 忽略 | 🔇 | 忽略此冲突 |

---

## 3. 组件功能

### 3.1 ConflictList
- 冲突列表展示
- 按严重程度着色
- 点击进入详情
- 空状态处理

### 3.2 ConflictModal
- 冲突详情展示
- 双方信号对比
- 解决方案选择
- 推荐方案标注
- 剩余时间显示
- 影响说明
- 确认/忽略操作

### 3.3 ConflictSummaryCard
- 总冲突数显示
- 按严重程度分类计数
- 快速查看全部

---

## 4. 技术实现

### 4.1 数据结构
```typescript
interface ConflictDetail {
  conflict_id: string;
  conflict_type: ConflictType;
  severity: ConflictSeverity;
  status: ConflictStatus;
  signal_a: ConflictingSignal;
  signal_b?: ConflictingSignal;
  description: string;
  reason: string;
  impact: string;
  suggested_resolution: ResolutionAction;
  resolution_reason: string;
  alternative_resolutions: ResolutionAction[];
  detected_at: string;
  expires_at?: string;
}
```

### 4.2 辅助函数
- `formatConflictTime()` - 格式化检测时间
- `getRemainingTime()` - 计算剩余处理时间

---

## 5. 验收测试

### 5.1 功能验证
- [x] 冲突列表正确展示
- [x] 按严重程度着色
- [x] 点击打开详情弹窗
- [x] 信号对比显示
- [x] 解决方案选择
- [x] 推荐方案标注
- [x] 确认/忽略操作
- [x] 剩余时间显示

### 5.2 类型覆盖
- [x] 4种冲突类型
- [x] 3种严重程度
- [x] 7种解决方案
- [x] 4种状态

---

## 6. TypeScript 检查结果

```bash
npx tsc --noEmit --skipLibCheck
# 结果: 无错误输出，编译成功
```

---

## 7. 后续建议

1. **后端 API**: 实现冲突检测和解决 API
2. **实时检测**: WebSocket 推送冲突通知
3. **自动解决**: 基于规则的自动冲突处理
4. **历史记录**: 冲突处理历史追踪

---

**报告生成**: Claude Opus 4.5
**版本**: Phase 6 v1.0
