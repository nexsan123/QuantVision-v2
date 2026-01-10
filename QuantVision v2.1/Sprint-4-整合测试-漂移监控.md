# Sprint 4: 整合测试 + 策略漂移监控 (6天)

> **文档版本**: 2.0  
> **预计时长**: 6天 (原3天 + 新增3天)  
> **前置依赖**: Sprint 1-3 全部完成  
> **PRD参考**: 4.8 实盘vs回测差异监控  
> **交付物**: Sprint 1-3功能完整测试、Bug修复、策略漂移监控系统

---

## 目标

1. 对Sprint 1-3的功能进行端到端测试，修复Bug
2. **新增**: 实现实盘vs回测差异监控 (策略漂移监控)

---

## Part A: 整合测试 (3天)

### Task 4.1: 端到端测试场景

#### 场景1: 策略创建到部署

```
步骤:
1. 进入 StrategyBuilder 页面
2. 创建一个新策略 (选择因子、设置规则)
3. 运行回测验证
4. 保存策略
5. 进入 "我的策略" 页面
6. 找到新创建的策略
7. 点击 "部署" 按钮
8. 完成4步部署向导
9. 确认策略在模拟盘启动

验收标准:
- [ ] 策略创建流程顺畅
- [ ] 策略在列表中显示
- [ ] 部署向导4步完整
- [ ] 模拟盘启动成功
```

#### 场景2: 模拟盘到实盘切换

```
步骤:
1. 准备一个运行中的模拟盘策略
2. 确认运行满30天 (或使用测试数据)
3. 确认胜率 > 40%
4. 点击 "切换环境"
5. 选择 "实盘"
6. 确认风险提示
7. 完成切换

验收标准:
- [ ] 未满足条件时显示错误
- [ ] 满足条件时可切换
- [ ] 风险提示显示正确
- [ ] 切换后状态正确
```

#### 场景3: 信号雷达监控

```
步骤:
1. 进入 Trading 页面
2. 查看信号雷达面板
3. 确认买入/卖出信号显示
4. 使用筛选功能
5. 搜索特定股票
6. 查看信号详情

验收标准:
- [ ] 信号列表正确显示
- [ ] 买入/卖出区分明确
- [ ] 筛选功能正常
- [ ] 搜索功能正常
```

#### 场景4: PDT规则验证

```
步骤:
1. 查看PDT状态面板
2. 确认剩余次数显示
3. 模拟接近限制 (剩余1次)
4. 确认黄色警告显示
5. 模拟达到限制 (剩余0次)
6. 确认红色警告 + 禁止交易

验收标准:
- [ ] 剩余次数正确
- [ ] 警告级别正确
- [ ] 限制时禁止日内交易
```

#### 场景5: AI连接状态

```
步骤:
1. 查看AI状态指示器
2. 确认正常连接状态
3. 模拟断开连接
4. 确认断开状态显示
5. 点击重新连接
6. 确认重连成功

验收标准:
- [ ] 连接状态正确
- [ ] 断开时显示错误
- [ ] 重连按钮可用
- [ ] 重连成功
```

#### 场景6: 风险预警触发 🆕

```
步骤:
1. 配置预警阈值 (单日亏损3%)
2. 模拟触发条件 (亏损达到3%)
3. 确认预警创建
4. 确认邮件发送
5. 在界面查看预警
6. 标记预警为已读

验收标准:
- [ ] 预警触发正确
- [ ] 邮件发送成功
- [ ] 预警列表显示正确
- [ ] 已读标记正确
```

---

### Task 4.2: Bug修复清单

#### 高优先级

| Bug描述 | 预期行为 | 状态 |
|---------|----------|:----:|
| 策略列表加载失败无错误提示 | 显示友好错误信息 | ⬜ |
| 部署向导关闭后数据未清空 | 重新打开时数据重置 | ⬜ |
| 环境切换后状态未更新 | 立即刷新状态 | ⬜ |
| PDT倒计时不准确 | 秒级精确倒计时 | ⬜ |
| 预警邮件发送失败无重试 | 失败后自动重试3次 | ⬜ |

#### 中优先级

| Bug描述 | 预期行为 | 状态 |
|---------|----------|:----:|
| 信号雷达自动刷新过于频繁 | 30秒刷新一次 | ⬜ |
| 策略卡片hover效果缺失 | 添加hover阴影 | ⬜ |
| AI状态延迟显示不稳定 | 平滑更新延迟值 | ⬜ |
| 预警铃铛数量更新延迟 | 实时更新 | ⬜ |

#### 低优先级

| Bug描述 | 预期行为 | 状态 |
|---------|----------|:----:|
| 表格分页样式不统一 | 统一分页样式 | ⬜ |
| 部分图标大小不一致 | 统一图标尺寸 | ⬜ |

---

### Task 4.3: 性能优化

#### 前端优化

```
优化项:
1. 策略列表懒加载
2. 信号雷达虚拟滚动 (大量数据时)
3. 组件按需加载
4. 预警列表分页加载

检查项:
- [ ] 首页加载时间 < 2秒
- [ ] 策略列表渲染 < 500ms
- [ ] 信号雷达更新无卡顿
- [ ] 预警列表滚动流畅
```

#### 后端优化

```
优化项:
1. 数据库查询索引
2. API响应缓存
3. 并发处理优化
4. 邮件发送队列

检查项:
- [ ] API响应时间 < 200ms
- [ ] 并发100用户无错误
- [ ] 邮件发送不阻塞主流程
```

---

### Task 4.4: 文档更新

| 文档 | 更新内容 | 状态 |
|------|----------|:----:|
| API文档 | 新增预警端点说明 | ⬜ |
| 用户手册 | 新功能使用说明 | ⬜ |
| 部署文档 | 邮件服务配置 | ⬜ |

---

### Task 4.5: 代码审查

- [ ] 代码风格一致性
- [ ] 错误处理完整性
- [ ] 类型定义准确性
- [ ] 安全性检查
- [ ] 性能考虑

---

## Part B: 策略漂移监控 (3天) 🆕

### Task 4.6: 漂移监控Schema (后端)

**文件**: `backend/app/schemas/drift.py`

```python
from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime, date
from enum import Enum

class DriftMetricType(str, Enum):
    """漂移指标类型"""
    RETURN = "return"           # 收益差异
    WIN_RATE = "win_rate"       # 胜率差异
    TURNOVER = "turnover"       # 换手率差异
    SLIPPAGE = "slippage"       # 滑点差异
    MAX_DRAWDOWN = "max_drawdown"  # 最大回撤差异
    HOLD_PERIOD = "hold_period"    # 持仓时间差异

class DriftSeverity(str, Enum):
    """漂移严重程度"""
    NORMAL = "normal"      # 正常范围
    WARNING = "warning"    # 黄色预警
    CRITICAL = "critical"  # 红色严重

class DriftMetric(BaseModel):
    """单个漂移指标"""
    metric_type: DriftMetricType
    backtest_value: float      # 回测值
    live_value: float          # 实盘值
    difference: float          # 差异 (绝对值)
    difference_pct: float      # 差异百分比
    warning_threshold: float   # 黄色预警阈值
    critical_threshold: float  # 红色严重阈值
    severity: DriftSeverity
    description: str

class StrategyDriftReport(BaseModel):
    """策略漂移报告"""
    report_id: str
    strategy_id: str
    strategy_name: str
    deployment_id: str
    environment: Literal["paper", "live"]
    
    # 时间范围
    period_start: date
    period_end: date
    days_compared: int
    
    # 整体状态
    overall_severity: DriftSeverity
    drift_score: float  # 0-100, 越高越偏离
    
    # 各指标详情
    metrics: list[DriftMetric]
    
    # 建议
    recommendations: list[str]
    should_pause: bool  # 是否建议暂停策略
    
    # 元数据
    created_at: datetime
    is_acknowledged: bool = False  # 用户是否已确认

class DriftThresholds(BaseModel):
    """漂移阈值配置 (PRD 附录C)"""
    # 黄色预警阈值
    return_warning: float = 0.10       # 收益差异 > 10%
    win_rate_warning: float = 0.05     # 胜率差异 > 5%
    turnover_warning: float = 0.20     # 换手率差异 > 20%
    slippage_warning: float = 0.30     # 滑点差异 > 30%
    max_drawdown_warning: float = 0.15 # 最大回撤差异 > 15%
    hold_period_warning: float = 0.25  # 持仓时间差异 > 25%
    
    # 红色严重阈值
    return_critical: float = 0.20      # 收益差异 > 20%
    win_rate_critical: float = 0.10    # 胜率差异 > 10%
    turnover_critical: float = 0.35    # 换手率差异 > 35%
    slippage_critical: float = 0.50    # 滑点差异 > 50%
    max_drawdown_critical: float = 0.25 # 最大回撤差异 > 25%
    hold_period_critical: float = 0.40  # 持仓时间差异 > 40%

class DriftCheckRequest(BaseModel):
    """漂移检查请求"""
    strategy_id: str
    deployment_id: str
    period_days: int = 30  # 默认比较最近30天
```

---

### Task 4.7: 漂移监控服务 (后端)

**文件**: `backend/app/services/drift_service.py`

```python
from datetime import datetime, date, timedelta
from typing import Optional
from app.schemas.drift import (
    StrategyDriftReport, DriftMetric, DriftMetricType,
    DriftSeverity, DriftThresholds
)
from app.services.alert_service import AlertService
from app.schemas.alert import AlertType, AlertSeverity
import uuid

class StrategyDriftService:
    """策略漂移监控服务"""
    
    # PRD 附录C 定义的阈值
    DEFAULT_THRESHOLDS = DriftThresholds()
    
    def __init__(self, db_session, alert_service: AlertService):
        self.db = db_session
        self.alert_service = alert_service
    
    async def check_drift(
        self,
        strategy_id: str,
        deployment_id: str,
        period_days: int = 30
    ) -> StrategyDriftReport:
        """检查策略漂移"""
        
        # 1. 获取回测数据
        backtest_stats = await self._get_backtest_stats(strategy_id)
        
        # 2. 获取实盘/模拟盘数据
        live_stats = await self._get_live_stats(deployment_id, period_days)
        
        # 3. 计算各指标漂移
        metrics = self._calculate_drift_metrics(backtest_stats, live_stats)
        
        # 4. 计算整体漂移评分
        overall_severity, drift_score = self._calculate_overall_drift(metrics)
        
        # 5. 生成建议
        recommendations, should_pause = self._generate_recommendations(
            metrics, overall_severity
        )
        
        # 6. 创建报告
        report = StrategyDriftReport(
            report_id=str(uuid.uuid4()),
            strategy_id=strategy_id,
            strategy_name=await self._get_strategy_name(strategy_id),
            deployment_id=deployment_id,
            environment=live_stats.environment,
            period_start=date.today() - timedelta(days=period_days),
            period_end=date.today(),
            days_compared=period_days,
            overall_severity=overall_severity,
            drift_score=drift_score,
            metrics=metrics,
            recommendations=recommendations,
            should_pause=should_pause,
            created_at=datetime.now()
        )
        
        # 7. 保存报告
        await self._save_report(report)
        
        # 8. 触发预警 (如果严重)
        if overall_severity in [DriftSeverity.WARNING, DriftSeverity.CRITICAL]:
            await self._trigger_drift_alert(report)
        
        return report
    
    def _calculate_drift_metrics(
        self,
        backtest: dict,
        live: dict
    ) -> list[DriftMetric]:
        """计算各指标漂移"""
        
        thresholds = self.DEFAULT_THRESHOLDS
        metrics = []
        
        # 定义指标映射
        metric_configs = [
            (DriftMetricType.RETURN, "total_return", "收益率",
             thresholds.return_warning, thresholds.return_critical),
            (DriftMetricType.WIN_RATE, "win_rate", "胜率",
             thresholds.win_rate_warning, thresholds.win_rate_critical),
            (DriftMetricType.TURNOVER, "turnover_rate", "换手率",
             thresholds.turnover_warning, thresholds.turnover_critical),
            (DriftMetricType.SLIPPAGE, "avg_slippage", "平均滑点",
             thresholds.slippage_warning, thresholds.slippage_critical),
            (DriftMetricType.MAX_DRAWDOWN, "max_drawdown", "最大回撤",
             thresholds.max_drawdown_warning, thresholds.max_drawdown_critical),
            (DriftMetricType.HOLD_PERIOD, "avg_hold_days", "平均持仓天数",
             thresholds.hold_period_warning, thresholds.hold_period_critical),
        ]
        
        for metric_type, key, name, warn_thresh, crit_thresh in metric_configs:
            bt_value = backtest.get(key, 0)
            live_value = live.get(key, 0)
            
            # 计算差异
            if bt_value != 0:
                diff_pct = abs(live_value - bt_value) / abs(bt_value)
            else:
                diff_pct = 0 if live_value == 0 else 1.0
            
            # 判断严重程度
            if diff_pct >= crit_thresh:
                severity = DriftSeverity.CRITICAL
            elif diff_pct >= warn_thresh:
                severity = DriftSeverity.WARNING
            else:
                severity = DriftSeverity.NORMAL
            
            # 生成描述
            description = self._generate_metric_description(
                name, bt_value, live_value, diff_pct, severity
            )
            
            metrics.append(DriftMetric(
                metric_type=metric_type,
                backtest_value=bt_value,
                live_value=live_value,
                difference=abs(live_value - bt_value),
                difference_pct=diff_pct,
                warning_threshold=warn_thresh,
                critical_threshold=crit_thresh,
                severity=severity,
                description=description
            ))
        
        return metrics
    
    def _calculate_overall_drift(
        self,
        metrics: list[DriftMetric]
    ) -> tuple[DriftSeverity, float]:
        """计算整体漂移程度"""
        
        # 统计各级别数量
        critical_count = sum(1 for m in metrics if m.severity == DriftSeverity.CRITICAL)
        warning_count = sum(1 for m in metrics if m.severity == DriftSeverity.WARNING)
        
        # 计算漂移评分 (0-100)
        # 权重: 收益最重要, 其次是胜率和回撤
        weights = {
            DriftMetricType.RETURN: 0.30,
            DriftMetricType.WIN_RATE: 0.20,
            DriftMetricType.MAX_DRAWDOWN: 0.20,
            DriftMetricType.TURNOVER: 0.10,
            DriftMetricType.SLIPPAGE: 0.10,
            DriftMetricType.HOLD_PERIOD: 0.10,
        }
        
        drift_score = 0
        for metric in metrics:
            weight = weights.get(metric.metric_type, 0.1)
            # 相对于critical阈值的比例
            relative = metric.difference_pct / metric.critical_threshold
            drift_score += min(relative, 2.0) * weight * 50  # 最高100分
        
        # 确定整体严重程度
        if critical_count >= 2 or drift_score >= 70:
            overall = DriftSeverity.CRITICAL
        elif critical_count >= 1 or warning_count >= 3 or drift_score >= 40:
            overall = DriftSeverity.WARNING
        else:
            overall = DriftSeverity.NORMAL
        
        return overall, min(drift_score, 100)
    
    def _generate_recommendations(
        self,
        metrics: list[DriftMetric],
        overall: DriftSeverity
    ) -> tuple[list[str], bool]:
        """生成建议"""
        
        recommendations = []
        should_pause = False
        
        for metric in metrics:
            if metric.severity == DriftSeverity.CRITICAL:
                if metric.metric_type == DriftMetricType.RETURN:
                    recommendations.append(
                        "收益差异严重，建议检查因子有效性是否发生变化"
                    )
                elif metric.metric_type == DriftMetricType.SLIPPAGE:
                    recommendations.append(
                        "滑点差异过大，考虑调整交易频率或选择流动性更好的股票"
                    )
                elif metric.metric_type == DriftMetricType.MAX_DRAWDOWN:
                    recommendations.append(
                        "实盘回撤显著高于回测，建议检查风控参数是否合理"
                    )
        
        if overall == DriftSeverity.CRITICAL:
            recommendations.insert(0, "⚠️ 策略实盘表现与回测差异过大，强烈建议暂停策略并进行深入分析")
            should_pause = True
        elif overall == DriftSeverity.WARNING:
            recommendations.insert(0, "策略出现漂移迹象，建议密切关注并考虑调整")
        
        if not recommendations:
            recommendations.append("策略运行正常，实盘表现与回测基本一致")
        
        return recommendations, should_pause
    
    def _generate_metric_description(
        self,
        name: str,
        bt_value: float,
        live_value: float,
        diff_pct: float,
        severity: DriftSeverity
    ) -> str:
        """生成指标描述"""
        
        direction = "高于" if live_value > bt_value else "低于"
        
        # 格式化数值
        if name in ["收益率", "胜率", "换手率", "最大回撤", "平均滑点"]:
            bt_str = f"{bt_value*100:.1f}%"
            live_str = f"{live_value*100:.1f}%"
        else:
            bt_str = f"{bt_value:.1f}"
            live_str = f"{live_value:.1f}"
        
        status = {
            DriftSeverity.NORMAL: "正常",
            DriftSeverity.WARNING: "需关注",
            DriftSeverity.CRITICAL: "异常"
        }[severity]
        
        return f"{name}: 实盘{live_str} {direction}回测{bt_str}, 差异{diff_pct*100:.1f}% [{status}]"
    
    async def _trigger_drift_alert(self, report: StrategyDriftReport):
        """触发漂移预警"""
        
        severity = AlertSeverity.CRITICAL if report.overall_severity == DriftSeverity.CRITICAL else AlertSeverity.WARNING
        
        title = f"策略漂移预警: {report.strategy_name}"
        message = f"策略'{report.strategy_name}'实盘表现与回测差异达到{report.drift_score:.0f}分。\n"
        message += "\n".join(report.recommendations[:3])
        
        await self.alert_service.create_manual_alert(
            user_id=await self._get_strategy_owner(report.strategy_id),
            alert_type=AlertType.SYSTEM_ERROR,  # 使用系统预警类型
            severity=severity,
            title=title,
            message=message,
            strategy_id=report.strategy_id,
            details={
                "drift_score": report.drift_score,
                "period_days": report.days_compared,
                "should_pause": report.should_pause,
                "report_id": report.report_id
            }
        )
    
    async def get_drift_history(
        self,
        strategy_id: str,
        limit: int = 10
    ) -> list[StrategyDriftReport]:
        """获取漂移历史报告"""
        # 数据库查询实现
        pass
    
    async def acknowledge_report(
        self,
        report_id: str,
        user_id: str
    ) -> bool:
        """确认漂移报告"""
        # 标记为已确认
        pass
```

---

### Task 4.8: 漂移监控API (后端)

**文件**: `backend/app/api/v1/drift.py`

```python
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from typing import Optional
from app.services.drift_service import StrategyDriftService
from app.schemas.drift import (
    StrategyDriftReport, DriftCheckRequest, DriftThresholds
)
from app.core.deps import get_current_user, get_drift_service

router = APIRouter(prefix="/drift", tags=["Drift Monitoring"])

@router.post("/check", response_model=StrategyDriftReport)
async def check_strategy_drift(
    request: DriftCheckRequest,
    current_user = Depends(get_current_user),
    drift_service: StrategyDriftService = Depends(get_drift_service)
):
    """检查策略漂移"""
    
    # 验证用户对策略的访问权限
    # ...
    
    return await drift_service.check_drift(
        strategy_id=request.strategy_id,
        deployment_id=request.deployment_id,
        period_days=request.period_days
    )

@router.get("/reports/{strategy_id}", response_model=list[StrategyDriftReport])
async def get_drift_reports(
    strategy_id: str,
    limit: int = Query(10, le=50),
    current_user = Depends(get_current_user),
    drift_service: StrategyDriftService = Depends(get_drift_service)
):
    """获取策略的漂移报告历史"""
    return await drift_service.get_drift_history(strategy_id, limit)

@router.get("/reports/{strategy_id}/latest", response_model=Optional[StrategyDriftReport])
async def get_latest_drift_report(
    strategy_id: str,
    current_user = Depends(get_current_user),
    drift_service: StrategyDriftService = Depends(get_drift_service)
):
    """获取策略最新的漂移报告"""
    reports = await drift_service.get_drift_history(strategy_id, limit=1)
    return reports[0] if reports else None

@router.post("/reports/{report_id}/acknowledge")
async def acknowledge_drift_report(
    report_id: str,
    current_user = Depends(get_current_user),
    drift_service: StrategyDriftService = Depends(get_drift_service)
):
    """确认漂移报告 (表示已阅读并采取措施)"""
    success = await drift_service.acknowledge_report(report_id, current_user.id)
    if not success:
        raise HTTPException(404, "报告不存在")
    return {"success": True}

@router.get("/thresholds", response_model=DriftThresholds)
async def get_drift_thresholds():
    """获取漂移监控阈值配置"""
    return DriftThresholds()

@router.post("/schedule-check")
async def schedule_drift_check(
    strategy_id: str,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user),
    drift_service: StrategyDriftService = Depends(get_drift_service)
):
    """安排后台漂移检查"""
    # 将任务添加到后台队列
    background_tasks.add_task(
        drift_service.check_all_deployments,
        strategy_id
    )
    return {"success": True, "message": "漂移检查已安排"}
```

**端点**:
```
POST /api/v1/drift/check                    - 立即检查策略漂移
GET  /api/v1/drift/reports/{strategyId}     - 获取漂移报告历史
GET  /api/v1/drift/reports/{strategyId}/latest - 获取最新漂移报告
POST /api/v1/drift/reports/{reportId}/acknowledge - 确认报告
GET  /api/v1/drift/thresholds               - 获取阈值配置
POST /api/v1/drift/schedule-check           - 安排后台检查
```

---

### Task 4.9: 漂移监控前端类型

**文件**: `frontend/src/types/drift.ts`

```typescript
export type DriftMetricType = 
  | 'return'
  | 'win_rate'
  | 'turnover'
  | 'slippage'
  | 'max_drawdown'
  | 'hold_period';

export type DriftSeverity = 'normal' | 'warning' | 'critical';

export interface DriftMetric {
  metricType: DriftMetricType;
  backtestValue: number;
  liveValue: number;
  difference: number;
  differencePct: number;
  warningThreshold: number;
  criticalThreshold: number;
  severity: DriftSeverity;
  description: string;
}

export interface StrategyDriftReport {
  reportId: string;
  strategyId: string;
  strategyName: string;
  deploymentId: string;
  environment: 'paper' | 'live';
  periodStart: string;
  periodEnd: string;
  daysCompared: number;
  overallSeverity: DriftSeverity;
  driftScore: number;
  metrics: DriftMetric[];
  recommendations: string[];
  shouldPause: boolean;
  createdAt: string;
  isAcknowledged: boolean;
}

export const DRIFT_METRIC_LABELS: Record<DriftMetricType, string> = {
  return: '收益率',
  win_rate: '胜率',
  turnover: '换手率',
  slippage: '滑点',
  max_drawdown: '最大回撤',
  hold_period: '持仓时间',
};

export const DRIFT_SEVERITY_CONFIG = {
  normal: { icon: '✅', color: '#22c55e', text: '正常' },
  warning: { icon: '⚠️', color: '#eab308', text: '需关注' },
  critical: { icon: '🔴', color: '#ef4444', text: '异常' },
};
```

---

### Task 4.10: 漂移监控组件

**文件**: `frontend/src/components/Drift/DriftReportPanel.tsx`

```tsx
import React from 'react';
import {
  StrategyDriftReport,
  DriftMetric,
  DRIFT_METRIC_LABELS,
  DRIFT_SEVERITY_CONFIG
} from '@/types/drift';

interface Props {
  report: StrategyDriftReport;
  onAcknowledge?: () => void;
  onPauseStrategy?: () => void;
}

export const DriftReportPanel: React.FC<Props> = ({
  report,
  onAcknowledge,
  onPauseStrategy
}) => {
  const severityConfig = DRIFT_SEVERITY_CONFIG[report.overallSeverity];
  
  return (
    <div className="drift-report-panel">
      {/* 头部 */}
      <div className="drift-header" style={{ borderColor: severityConfig.color }}>
        <div className="drift-title">
          <span className="drift-icon">{severityConfig.icon}</span>
          <h3>策略漂移报告</h3>
          <span 
            className="drift-severity-badge"
            style={{ backgroundColor: severityConfig.color }}
          >
            {severityConfig.text}
          </span>
        </div>
        <div className="drift-meta">
          <span>策略: {report.strategyName}</span>
          <span>环境: {report.environment === 'live' ? '实盘' : '模拟盘'}</span>
          <span>分析周期: {report.daysCompared}天</span>
        </div>
      </div>
      
      {/* 漂移评分 */}
      <div className="drift-score-section">
        <div className="drift-score">
          <div className="score-value">{report.driftScore.toFixed(0)}</div>
          <div className="score-label">漂移评分</div>
        </div>
        <div className="drift-score-bar">
          <div 
            className="drift-score-fill"
            style={{ 
              width: `${report.driftScore}%`,
              backgroundColor: severityConfig.color
            }}
          />
        </div>
        <div className="drift-score-scale">
          <span>0 正常</span>
          <span>40 关注</span>
          <span>70 异常</span>
          <span>100</span>
        </div>
      </div>
      
      {/* 指标详情 */}
      <div className="drift-metrics">
        <h4>指标对比</h4>
        <table className="drift-metrics-table">
          <thead>
            <tr>
              <th>指标</th>
              <th>回测</th>
              <th>实盘</th>
              <th>差异</th>
              <th>状态</th>
            </tr>
          </thead>
          <tbody>
            {report.metrics.map(metric => (
              <DriftMetricRow key={metric.metricType} metric={metric} />
            ))}
          </tbody>
        </table>
      </div>
      
      {/* 建议 */}
      <div className="drift-recommendations">
        <h4>建议</h4>
        <ul>
          {report.recommendations.map((rec, i) => (
            <li key={i}>{rec}</li>
          ))}
        </ul>
      </div>
      
      {/* 操作按钮 */}
      <div className="drift-actions">
        {report.shouldPause && onPauseStrategy && (
          <button 
            className="btn btn-danger"
            onClick={onPauseStrategy}
          >
            暂停策略
          </button>
        )}
        {!report.isAcknowledged && onAcknowledge && (
          <button 
            className="btn btn-secondary"
            onClick={onAcknowledge}
          >
            我已知晓
          </button>
        )}
      </div>
    </div>
  );
};

const DriftMetricRow: React.FC<{ metric: DriftMetric }> = ({ metric }) => {
  const config = DRIFT_SEVERITY_CONFIG[metric.severity];
  
  const formatValue = (value: number, type: string) => {
    if (['return', 'win_rate', 'turnover', 'max_drawdown', 'slippage'].includes(type)) {
      return `${(value * 100).toFixed(1)}%`;
    }
    return value.toFixed(1);
  };
  
  return (
    <tr className={`drift-row drift-row-${metric.severity}`}>
      <td>{DRIFT_METRIC_LABELS[metric.metricType]}</td>
      <td>{formatValue(metric.backtestValue, metric.metricType)}</td>
      <td>{formatValue(metric.liveValue, metric.metricType)}</td>
      <td>{(metric.differencePct * 100).toFixed(1)}%</td>
      <td>
        <span 
          className="drift-status"
          style={{ color: config.color }}
        >
          {config.icon} {config.text}
        </span>
      </td>
    </tr>
  );
};
```

**文件**: `frontend/src/components/Drift/DriftIndicator.tsx`

```tsx
import React from 'react';
import { DriftSeverity, DRIFT_SEVERITY_CONFIG } from '@/types/drift';

interface Props {
  severity: DriftSeverity;
  score: number;
  onClick?: () => void;
}

export const DriftIndicator: React.FC<Props> = ({ severity, score, onClick }) => {
  const config = DRIFT_SEVERITY_CONFIG[severity];
  
  if (severity === 'normal') {
    return null; // 正常时不显示
  }
  
  return (
    <div 
      className="drift-indicator"
      style={{ backgroundColor: config.color }}
      onClick={onClick}
      title={`漂移评分: ${score.toFixed(0)}`}
    >
      {config.icon} 漂移{config.text}
    </div>
  );
};
```

**验收标准**:
- [ ] 漂移报告面板显示正确
- [ ] 各指标对比清晰
- [ ] 严重程度颜色区分明确
- [ ] 建议信息有用

---

### Task 4.11: 策略卡片集成漂移指示器

**修改文件**: `frontend/src/components/Strategy/StrategyCard.tsx`

```tsx
// 在策略卡片中添加漂移指示器
<div className="strategy-card">
  <div className="strategy-header">
    <h3>{strategy.name}</h3>
    <StrategyStatusBadge status={strategy.status} />
    {latestDriftReport && (
      <DriftIndicator 
        severity={latestDriftReport.overallSeverity}
        score={latestDriftReport.driftScore}
        onClick={() => setShowDriftReport(true)}
      />
    )}
  </div>
  {/* ... 其他内容 */}
</div>
```

---

## Sprint 4 完成检查清单

### Part A: 整合测试
- [ ] 场景1: 策略创建到部署 ✓
- [ ] 场景2: 模拟盘到实盘切换 ✓
- [ ] 场景3: 信号雷达监控 ✓
- [ ] 场景4: PDT规则验证 ✓
- [ ] 场景5: AI连接状态 ✓
- [ ] 场景6: 风险预警触发 ✓

### Part B: 策略漂移监控 🆕
- [ ] drift.py Schema完整
- [ ] drift_service.py 服务完整
- [ ] drift.py API可调用
- [ ] drift.ts 类型定义完整
- [ ] DriftReportPanel.tsx 报告面板正常
- [ ] DriftIndicator.tsx 指示器正常
- [ ] 策略卡片集成指示器

### Bug修复
- [ ] 高优先级Bug全部修复
- [ ] 中优先级Bug大部分修复

### 其他
- [ ] 性能优化完成
- [ ] 文档已更新
- [ ] 代码已审查

---

## Phase 1 发布检查

| 功能 | Sprint | 状态 |
|------|:------:|:----:|
| 我的策略列表 | 1 | ⬜ |
| 4步部署向导 | 1 | ⬜ |
| 信号雷达面板 | 2 | ⬜ |
| 环境切换器 | 2 | ⬜ |
| PDT状态管理 | 3 | ⬜ |
| AI连接状态 | 3 | ⬜ |
| 风险预警通知 | 3 | ⬜ |
| 策略漂移监控 | 4 | ⬜ |

---

## 新增API端点

```
# 漂移监控 🆕
POST /api/v1/drift/check                      - 立即检查策略漂移
GET  /api/v1/drift/reports/{strategyId}       - 获取漂移报告历史
GET  /api/v1/drift/reports/{strategyId}/latest - 获取最新漂移报告
POST /api/v1/drift/reports/{reportId}/acknowledge - 确认报告
GET  /api/v1/drift/thresholds                 - 获取阈值配置
POST /api/v1/drift/schedule-check             - 安排后台检查
```

---

## 新增文件清单

### 后端
```
backend/app/
├── schemas/
│   └── drift.py           🆕
├── services/
│   └── drift_service.py   🆕
└── api/v1/
    └── drift.py           🆕
```

### 前端
```
frontend/src/
├── types/
│   └── drift.ts           🆕
└── components/
    └── Drift/             🆕
        ├── DriftReportPanel.tsx
        └── DriftIndicator.tsx
```

---

## 下一步

完成后进入 **Sprint 5: 因子+归因+冲突**

---

**预计完成时间**: 6天 (原3天 + 新增3天)
