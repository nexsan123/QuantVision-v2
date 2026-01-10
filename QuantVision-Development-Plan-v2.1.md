# QuantVision v2.1 开发任务清单

**基于**: 审计报告 + PRD v2.1 完整需求  
**日期**: 2026-01-09  
**目标**: 补全所有PRD功能，修复P0级Bug

---

## 📊 当前状态 vs PRD需求对比

### 页面实现状态

| 页面 | PRD章节 | 当前状态 | 优先级 |
|------|---------|:--------:|:------:|
| 仪表盘 | - | ✅ 已实现 | - |
| 我的策略 | 4.1 | ✅ 已实现 | - |
| 策略模板库 | Q6 | ✅ 已实现 | - |
| 因子实验室 | 4.3 | ⚠️ 部分实现 | P1 |
| 策略构建 | - | ✅ 已实现 | - |
| 策略回放 | 4.17 | 🔴 **崩溃** | P0 |
| 回测中心 | - | ✅ 已实现 | - |
| 交易执行 | 4.16 | ✅ 已实现 | - |
| 日内交易 | 4.18 | 🔴 **崩溃** | P0 |
| 风险中心 | - | ✅ 已实现 | - |
| 策略部署向导 | 4.15 | ❌ 未实现 | P1 |
| 盘前扫描器 | 4.18.0 | ⚠️ 部分实现 | P1 |
| 因子有效性验证 | 4.3 | ❌ 未实现 | P0 |
| 交易归因系统 | 4.5 | ❌ 未实现 | P1 |
| 策略冲突检测 | 4.6 | ❌ 未实现 | P1 |
| 税务合规系统 | Q16 | ❌ 未实现 | P2 |
| 实盘vs回测监控 | 4.12 | ❌ 未实现 | P1 |

---

## 🔴 P0 - 立即修复 (阻塞核心功能)

### Task 1: TradingView组件修复 + 缩放功能

**问题**: TradingViewChart.tsx:32行崩溃，导致策略回放和日内交易页面不可用

**影响页面**:
- `/strategy/replay`
- `/intraday`

**修复方案**: 见下方代码实现

---

### Task 2: AI连接状态指示器 (PRD 4.2)

**需求**: 用户需要知道AI助手是否已连接

**状态定义**:
| 状态 | 图标 | 含义 |
|------|:----:|------|
| 已连接 | 🟢 | API正常 |
| 连接中 | 🟡 | 正在建立连接 |
| 未连接 | 🔴 | 连接失败 |
| 离线模式 | ⚪ | 使用本地功能 |

---

### Task 3: 因子有效性验证面板 (PRD 4.3)

**需求**: 在因子实验室添加验证面板

**显示内容**:
- IC均值/IC_IR
- 多空年化收益差
- 有效性等级 (强/中/弱)
- 最佳/最差市场环境
- 建议搭配因子

---

## 🟠 P1 - 本迭代完成 (提升专业度)

### Task 4: 策略部署向导 (PRD 4.15)

**4步部署流程**:
1. 模拟盘运行 → 2. 风险检查 → 3. 确认部署 → 4. 开始监控

### Task 5: 策略冲突检测 (PRD 4.6)

**冲突类型**:
- 逻辑冲突: 同策略类型对同股票发出相反信号
- 执行冲突: 不同策略类型需顺序执行
- 无冲突: 完全不同股票

### Task 6: 交易归因系统 (PRD 4.5)

**功能**:
- 每笔交易记录
- 因子贡献度分解
- AI诊断建议
- 历史数据保留

### Task 7: 实盘vs回测监控 (PRD附录C)

**监控阈值**:
| 监控项 | 黄色预警 | 红色预警 |
|--------|:--------:|:--------:|
| 收益差异 | >10% | >20% |
| 胜率差异 | >5% | >10% |
| 最大回撤差异 | >15% | >25% |

### Task 8: PDT规则管理增强 (PRD 4.7)

**功能**:
- 显示账户类型
- 剩余日内交易次数
- 重置时间倒计时
- 解锁提示

---

## 🟡 P2 - 下迭代完成 (完善专业功能)

### Task 9: 税务合规系统 (PRD Q16)
### Task 10: 策略版本管理 (PRD Q9)
### Task 11: MCP多模型支持 (PRD Q4)
### Task 12: 风险预警通知 (PRD Q7)

---

## 💻 代码实现

### 1. TradingView 可缩放组件

```typescript
// src/components/Chart/TradingViewChart.tsx

import React, { useEffect, useRef, useState, useCallback } from 'react';
import { Alert, Spin, Empty, Button, Tooltip, Slider } from 'antd';
import { 
  ExpandOutlined, 
  CompressOutlined, 
  FullscreenOutlined,
  FullscreenExitOutlined,
  ReloadOutlined,
  ZoomInOutlined,
  ZoomOutOutlined
} from '@ant-design/icons';

// ================== 类型定义 ==================
interface TradingViewChartProps {
  symbol?: string;
  interval?: string;
  dateRange?: { start: string; end: string };
  theme?: 'dark' | 'light';
  showToolbar?: boolean;
  showZoomControls?: boolean;
  onSignalClick?: (signal: SignalMarker) => void;
  signals?: SignalMarker[];
  height?: number | string;
  allowFullscreen?: boolean;
  className?: string;
}

interface SignalMarker {
  time: number;
  type: 'buy' | 'sell' | 'stop_loss' | 'take_profit';
  price: number;
  label?: string;
}

interface ChartState {
  loading: boolean;
  error: string | null;
  isFullscreen: boolean;
  isExpanded: boolean;
  zoomLevel: number;
}

// ================== 主组件 ==================
const TradingViewChart: React.FC<TradingViewChartProps> = ({
  symbol,
  interval = '15',
  dateRange,
  theme = 'dark',
  showToolbar = true,
  showZoomControls = true,
  onSignalClick,
  signals = [],
  height = 500,
  allowFullscreen = true,
  className = ''
}) => {
  // Refs
  const containerRef = useRef<HTMLDivElement>(null);
  const widgetRef = useRef<any>(null);
  const fullscreenRef = useRef<HTMLDivElement>(null);
  
  // State
  const [state, setState] = useState<ChartState>({
    loading: true,
    error: null,
    isFullscreen: false,
    isExpanded: false,
    zoomLevel: 100
  });

  // ================== 参数校验 ==================
  if (!symbol) {
    return (
      <div className="h-full flex items-center justify-center bg-[#0d0d1f] rounded-lg">
        <Empty 
          description={
            <span className="text-gray-400">请选择要查看的股票</span>
          }
          image={Empty.PRESENTED_IMAGE_SIMPLE}
        />
      </div>
    );
  }

  // ================== 初始化 TradingView ==================
  const initWidget = useCallback(() => {
    if (!containerRef.current) return;
    
    // 清理旧实例
    if (widgetRef.current) {
      try {
        widgetRef.current.remove();
      } catch (e) {
        console.warn('Widget cleanup warning:', e);
      }
      widgetRef.current = null;
    }

    setState(prev => ({ ...prev, loading: true, error: null }));

    try {
      // 检查 TradingView 库
      if (typeof window.TradingView === 'undefined') {
        throw new Error('TradingView library not loaded');
      }

      // 创建 Widget
      widgetRef.current = new window.TradingView.widget({
        container: containerRef.current,
        symbol: symbol,
        interval: interval,
        theme: theme,
        style: '1',
        locale: 'zh_CN',
        toolbar_bg: theme === 'dark' ? '#0a0a1a' : '#ffffff',
        enable_publishing: false,
        hide_side_toolbar: false,
        allow_symbol_change: true,
        autosize: true,
        studies: [
          'MASimple@tv-basicstudies',
          'RSI@tv-basicstudies',
          'MACD@tv-basicstudies'
        ],
        disabled_features: [
          'use_localstorage_for_settings'
        ],
        enabled_features: [
          'study_templates',
          'hide_left_toolbar_by_default'
        ],
        overrides: {
          'mainSeriesProperties.candleStyle.upColor': '#22c55e',
          'mainSeriesProperties.candleStyle.downColor': '#ef4444',
          'mainSeriesProperties.candleStyle.borderUpColor': '#22c55e',
          'mainSeriesProperties.candleStyle.borderDownColor': '#ef4444',
          'mainSeriesProperties.candleStyle.wickUpColor': '#22c55e',
          'mainSeriesProperties.candleStyle.wickDownColor': '#ef4444',
          'paneProperties.background': theme === 'dark' ? '#0a0a1a' : '#ffffff',
          'paneProperties.vertGridProperties.color': theme === 'dark' ? '#1a1a3a' : '#e0e0e0',
          'paneProperties.horzGridProperties.color': theme === 'dark' ? '#1a1a3a' : '#e0e0e0',
        },
        loading_screen: {
          backgroundColor: theme === 'dark' ? '#0a0a1a' : '#ffffff',
          foregroundColor: '#3b82f6'
        },
        // 回调函数
        onChartReady: () => {
          setState(prev => ({ ...prev, loading: false }));
          
          // 添加信号标记
          if (signals.length > 0 && widgetRef.current) {
            addSignalMarkers();
          }
        },
      });
    } catch (err) {
      console.error('TradingView init error:', err);
      setState(prev => ({
        ...prev,
        loading: false,
        error: err instanceof Error ? err.message : '图表初始化失败'
      }));
    }
  }, [symbol, interval, theme, signals]);

  // ================== 添加信号标记 ==================
  const addSignalMarkers = useCallback(() => {
    if (!widgetRef.current) return;
    
    try {
      const chart = widgetRef.current.chart();
      
      signals.forEach(signal => {
        const color = signal.type === 'buy' || signal.type === 'take_profit' 
          ? '#22c55e' 
          : '#ef4444';
        const shape = signal.type === 'buy' ? 'arrowUp' : 'arrowDown';
        
        chart.createShape(
          { time: signal.time, price: signal.price },
          {
            shape: shape,
            overrides: {
              color: color,
              fontsize: 12
            },
            text: signal.label || signal.type.toUpperCase()
          }
        );
      });
    } catch (e) {
      console.warn('Failed to add signal markers:', e);
    }
  }, [signals]);

  // ================== 缩放控制 ==================
  const handleZoomIn = useCallback(() => {
    setState(prev => ({
      ...prev,
      zoomLevel: Math.min(prev.zoomLevel + 20, 200)
    }));
  }, []);

  const handleZoomOut = useCallback(() => {
    setState(prev => ({
      ...prev,
      zoomLevel: Math.max(prev.zoomLevel - 20, 50)
    }));
  }, []);

  const handleZoomChange = useCallback((value: number) => {
    setState(prev => ({ ...prev, zoomLevel: value }));
  }, []);

  const handleResetZoom = useCallback(() => {
    setState(prev => ({ ...prev, zoomLevel: 100 }));
  }, []);

  // ================== 展开/收起控制 ==================
  const handleToggleExpand = useCallback(() => {
    setState(prev => ({ ...prev, isExpanded: !prev.isExpanded }));
  }, []);

  // ================== 全屏控制 ==================
  const handleToggleFullscreen = useCallback(() => {
    if (!fullscreenRef.current) return;

    if (!state.isFullscreen) {
      if (fullscreenRef.current.requestFullscreen) {
        fullscreenRef.current.requestFullscreen();
      }
    } else {
      if (document.exitFullscreen) {
        document.exitFullscreen();
      }
    }
  }, [state.isFullscreen]);

  // 监听全屏变化
  useEffect(() => {
    const handleFullscreenChange = () => {
      setState(prev => ({
        ...prev,
        isFullscreen: !!document.fullscreenElement
      }));
    };

    document.addEventListener('fullscreenchange', handleFullscreenChange);
    return () => {
      document.removeEventListener('fullscreenchange', handleFullscreenChange);
    };
  }, []);

  // ================== 初始化 ==================
  useEffect(() => {
    initWidget();
    
    return () => {
      if (widgetRef.current) {
        try {
          widgetRef.current.remove();
        } catch (e) {
          // 忽略清理错误
        }
      }
    };
  }, [initWidget]);

  // ================== 错误状态 ==================
  if (state.error) {
    return (
      <div className="h-full flex items-center justify-center bg-[#0d0d1f] rounded-lg p-8">
        <Alert
          type="error"
          message="图表加载失败"
          description={
            <div className="mt-2">
              <p className="text-gray-400 mb-3">{state.error}</p>
              <Button 
                type="primary" 
                icon={<ReloadOutlined />}
                onClick={initWidget}
              >
                重试加载
              </Button>
            </div>
          }
          showIcon
        />
      </div>
    );
  }

  // ================== 计算样式 ==================
  const chartHeight = state.isExpanded 
    ? 'calc(100vh - 200px)' 
    : (typeof height === 'number' ? `${height}px` : height);

  const transformStyle = {
    transform: `scale(${state.zoomLevel / 100})`,
    transformOrigin: 'top left',
    width: `${10000 / state.zoomLevel}%`,
    height: `${10000 / state.zoomLevel}%`
  };

  // ================== 渲染 ==================
  return (
    <div 
      ref={fullscreenRef}
      className={`relative bg-[#0a0a1a] rounded-lg overflow-hidden ${className}`}
    >
      {/* 工具栏 */}
      {showToolbar && (
        <div className="absolute top-2 right-2 z-10 flex items-center gap-2 bg-[#0d0d1f]/90 backdrop-blur-sm rounded-lg px-3 py-2">
          {/* 缩放控制 */}
          {showZoomControls && (
            <>
              <Tooltip title="缩小">
                <Button 
                  type="text" 
                  size="small"
                  icon={<ZoomOutOutlined />}
                  onClick={handleZoomOut}
                  disabled={state.zoomLevel <= 50}
                  className="text-gray-400 hover:text-white"
                />
              </Tooltip>
              
              <div className="w-24 mx-2">
                <Slider
                  min={50}
                  max={200}
                  step={10}
                  value={state.zoomLevel}
                  onChange={handleZoomChange}
                  tooltip={{ formatter: (v) => `${v}%` }}
                />
              </div>
              
              <Tooltip title="放大">
                <Button 
                  type="text" 
                  size="small"
                  icon={<ZoomInOutlined />}
                  onClick={handleZoomIn}
                  disabled={state.zoomLevel >= 200}
                  className="text-gray-400 hover:text-white"
                />
              </Tooltip>

              <Tooltip title="重置缩放">
                <Button 
                  type="text" 
                  size="small"
                  onClick={handleResetZoom}
                  className="text-gray-400 hover:text-white text-xs"
                >
                  {state.zoomLevel}%
                </Button>
              </Tooltip>

              <div className="w-px h-4 bg-gray-600 mx-1" />
            </>
          )}

          {/* 展开/收起 */}
          <Tooltip title={state.isExpanded ? '收起' : '展开'}>
            <Button 
              type="text" 
              size="small"
              icon={state.isExpanded ? <CompressOutlined /> : <ExpandOutlined />}
              onClick={handleToggleExpand}
              className="text-gray-400 hover:text-white"
            />
          </Tooltip>

          {/* 全屏 */}
          {allowFullscreen && (
            <Tooltip title={state.isFullscreen ? '退出全屏' : '全屏'}>
              <Button 
                type="text" 
                size="small"
                icon={state.isFullscreen ? <FullscreenExitOutlined /> : <FullscreenOutlined />}
                onClick={handleToggleFullscreen}
                className="text-gray-400 hover:text-white"
              />
            </Tooltip>
          )}
        </div>
      )}

      {/* 图表容器 */}
      <div 
        className="overflow-auto"
        style={{ height: chartHeight }}
      >
        <Spin spinning={state.loading} tip="加载图表中...">
          <div 
            ref={containerRef}
            style={{
              ...transformStyle,
              minHeight: chartHeight,
            }}
          />
        </Spin>
      </div>

      {/* 缩放指示器 (左下角) */}
      {state.zoomLevel !== 100 && (
        <div className="absolute bottom-2 left-2 bg-[#0d0d1f]/80 text-gray-400 text-xs px-2 py-1 rounded">
          缩放: {state.zoomLevel}%
        </div>
      )}
    </div>
  );
};

export default TradingViewChart;
```

---

### 2. 全局 ErrorBoundary 组件

```typescript
// src/components/ErrorBoundary/ChartErrorBoundary.tsx

import React, { Component, ReactNode } from 'react';
import { Button, Result } from 'antd';
import { ReloadOutlined, BugOutlined, HomeOutlined } from '@ant-design/icons';

interface Props {
  children: ReactNode;
  fallbackTitle?: string;
  onRetry?: () => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: React.ErrorInfo | null;
  showDetails: boolean;
}

class ChartErrorBoundary extends Component<Props, State> {
  state: State = {
    hasError: false,
    error: null,
    errorInfo: null,
    showDetails: false
  };

  static getDerivedStateFromError(error: Error): Partial<State> {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    this.setState({ errorInfo });
    console.error('Chart Error:', error, errorInfo);
    
    // TODO: 上报到错误监控系统
    // reportError({ error, errorInfo, page: window.location.pathname });
  }

  handleReload = () => {
    window.location.reload();
  };

  handleRetry = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
    this.props.onRetry?.();
  };

  handleGoHome = () => {
    window.location.href = '/dashboard';
  };

  handleToggleDetails = () => {
    this.setState(prev => ({ showDetails: !prev.showDetails }));
  };

  render() {
    if (this.state.hasError) {
      const { fallbackTitle = '图表组件加载失败' } = this.props;

      return (
        <div className="h-full min-h-[400px] flex flex-col items-center justify-center bg-[#0d0d1f] rounded-lg p-8">
          <Result
            status="error"
            title={<span className="text-white text-lg">{fallbackTitle}</span>}
            subTitle={
              <span className="text-gray-400">
                组件渲染时发生错误，请尝试刷新页面或返回主页
              </span>
            }
            extra={[
              <Button 
                type="primary" 
                key="retry"
                icon={<ReloadOutlined />}
                onClick={this.handleRetry}
              >
                重试
              </Button>,
              <Button 
                key="reload"
                onClick={this.handleReload}
              >
                刷新页面
              </Button>,
              <Button 
                key="home"
                icon={<HomeOutlined />}
                onClick={this.handleGoHome}
              >
                返回主页
              </Button>,
              <Button 
                key="details"
                type="text"
                icon={<BugOutlined />}
                onClick={this.handleToggleDetails}
                className="text-gray-500"
              >
                {this.state.showDetails ? '隐藏' : '查看'}错误详情
              </Button>
            ]}
          />
          
          {this.state.showDetails && (
            <div className="mt-4 w-full max-w-2xl">
              <pre className="p-4 bg-gray-900/50 rounded-lg text-xs text-red-400 overflow-auto max-h-48 border border-gray-700">
                <strong>Error:</strong> {this.state.error?.toString()}
                {'\n\n'}
                <strong>Component Stack:</strong>
                {this.state.errorInfo?.componentStack}
              </pre>
            </div>
          )}
        </div>
      );
    }

    return this.props.children;
  }
}

export default ChartErrorBoundary;
```

---

### 3. AI 连接状态指示器

```typescript
// src/components/AIStatus/AIStatusIndicator.tsx

import React, { useEffect, useState } from 'react';
import { Tooltip, Badge, Button } from 'antd';
import { 
  CheckCircleFilled, 
  CloseCircleFilled, 
  LoadingOutlined,
  DisconnectOutlined,
  ReloadOutlined
} from '@ant-design/icons';

type AIStatus = 'connected' | 'connecting' | 'disconnected' | 'offline';

interface AIStatusIndicatorProps {
  showLabel?: boolean;
  showModel?: boolean;
  size?: 'small' | 'default' | 'large';
  onRetryConnect?: () => void;
}

const statusConfig = {
  connected: {
    icon: <CheckCircleFilled />,
    color: '#22c55e',
    badge: 'success' as const,
    label: 'AI已连接',
    description: 'API正常，可以对话'
  },
  connecting: {
    icon: <LoadingOutlined spin />,
    color: '#eab308',
    badge: 'processing' as const,
    label: '连接中',
    description: '正在建立连接...'
  },
  disconnected: {
    icon: <CloseCircleFilled />,
    color: '#ef4444',
    badge: 'error' as const,
    label: '未连接',
    description: '连接失败，点击重试'
  },
  offline: {
    icon: <DisconnectOutlined />,
    color: '#6b7280',
    badge: 'default' as const,
    label: '离线模式',
    description: '使用本地功能'
  }
};

const AIStatusIndicator: React.FC<AIStatusIndicatorProps> = ({
  showLabel = true,
  showModel = true,
  size = 'default',
  onRetryConnect
}) => {
  const [status, setStatus] = useState<AIStatus>('connecting');
  const [currentModel, setCurrentModel] = useState<string>('Claude 4.5 Sonnet');
  const [latency, setLatency] = useState<number | null>(null);

  // 检查AI连接状态
  const checkConnection = async () => {
    setStatus('connecting');
    
    try {
      const startTime = Date.now();
      const response = await fetch('/api/v1/ai/health', {
        method: 'GET',
        timeout: 5000
      });
      
      if (response.ok) {
        const data = await response.json();
        setStatus('connected');
        setCurrentModel(data.model || 'Claude 4.5 Sonnet');
        setLatency(Date.now() - startTime);
      } else {
        setStatus('disconnected');
      }
    } catch (error) {
      // 检查是否是网络离线
      if (!navigator.onLine) {
        setStatus('offline');
      } else {
        setStatus('disconnected');
      }
    }
  };

  useEffect(() => {
    checkConnection();
    
    // 定期检查连接状态
    const interval = setInterval(checkConnection, 30000);
    
    // 监听网络状态变化
    window.addEventListener('online', checkConnection);
    window.addEventListener('offline', () => setStatus('offline'));
    
    return () => {
      clearInterval(interval);
      window.removeEventListener('online', checkConnection);
      window.removeEventListener('offline', () => setStatus('offline'));
    };
  }, []);

  const handleRetry = () => {
    checkConnection();
    onRetryConnect?.();
  };

  const config = statusConfig[status];
  const fontSize = size === 'small' ? 12 : size === 'large' ? 16 : 14;

  return (
    <Tooltip 
      title={
        <div className="text-center">
          <div className="font-medium">{config.description}</div>
          {showModel && status === 'connected' && (
            <div className="text-xs text-gray-400 mt-1">
              模型: {currentModel}
            </div>
          )}
          {latency && status === 'connected' && (
            <div className="text-xs text-gray-400">
              延迟: {latency}ms
            </div>
          )}
        </div>
      }
      placement="bottom"
    >
      <div 
        className="flex items-center gap-2 cursor-pointer"
        onClick={status === 'disconnected' ? handleRetry : undefined}
      >
        <Badge status={config.badge} />
        
        <span 
          className="flex items-center gap-1"
          style={{ color: config.color, fontSize }}
        >
          {config.icon}
          {showLabel && <span>{config.label}</span>}
        </span>

        {status === 'disconnected' && (
          <Button 
            type="text" 
            size="small" 
            icon={<ReloadOutlined />}
            onClick={handleRetry}
            className="text-gray-400 hover:text-white"
          />
        )}
        
        {latency && status === 'connected' && size !== 'small' && (
          <span className="text-xs text-gray-500">
            {latency}ms
          </span>
        )}
      </div>
    </Tooltip>
  );
};

export default AIStatusIndicator;
```

---

### 4. 因子有效性验证面板

```typescript
// src/components/FactorLab/FactorValidationPanel.tsx

import React from 'react';
import { Card, Progress, Tag, Tooltip, Descriptions, Alert } from 'antd';
import { 
  CheckCircleFilled, 
  CloseCircleFilled,
  QuestionCircleOutlined,
  BulbOutlined
} from '@ant-design/icons';

interface FactorValidation {
  factorId: string;
  factorName: string;
  factorDescription: string;
  icMean: number;
  icIR: number;
  longAnnualReturn: number;
  shortAnnualReturn: number;
  longShortSpread: number;
  isEffective: boolean;
  effectivenessLevel: 'strong' | 'medium' | 'weak';
  bestMarketCondition: string;
  worstMarketCondition: string;
  suggestedCombination: string[];
  backtestPeriod: string;
  universe: string;
}

interface Props {
  validation: FactorValidation | null;
  loading?: boolean;
}

const levelConfig = {
  strong: { color: '#22c55e', label: '强', stars: 5 },
  medium: { color: '#eab308', label: '中', stars: 3 },
  weak: { color: '#ef4444', label: '弱', stars: 1 }
};

const FactorValidationPanel: React.FC<Props> = ({ validation, loading }) => {
  if (!validation) {
    return (
      <Card 
        title="🔬 因子有效性验证" 
        className="bg-[#0d0d1f] border-[#2a2a4a]"
        loading={loading}
      >
        <div className="text-gray-400 text-center py-8">
          选择一个因子查看验证结果
        </div>
      </Card>
    );
  }

  const levelInfo = levelConfig[validation.effectivenessLevel];
  const icPercent = Math.min(Math.abs(validation.icMean) * 1000, 100);
  const irPercent = Math.min(validation.icIR * 50, 100);

  return (
    <Card 
      title={
        <div className="flex items-center justify-between">
          <span>🔬 因子研究中心 - {validation.factorName}</span>
          <Tag color={validation.isEffective ? 'success' : 'error'}>
            {validation.isEffective ? '✅ 有效' : '❌ 无效'}
          </Tag>
        </div>
      }
      className="bg-[#0d0d1f] border-[#2a2a4a]"
      loading={loading}
    >
      {/* 因子说明 */}
      <div className="mb-4 p-3 bg-[#1a1a3a] rounded-lg">
        <div className="text-gray-400 text-sm mb-1">📖 因子说明 (大白话)</div>
        <div className="text-white">{validation.factorDescription}</div>
      </div>

      {/* 历史回测验证 */}
      <div className="mb-4 p-3 bg-[#1a1a3a] rounded-lg">
        <div className="text-gray-400 text-sm mb-3">
          📊 历史回测验证 ({validation.backtestPeriod}, {validation.universe})
        </div>
        
        <Descriptions 
          column={1} 
          size="small"
          labelStyle={{ color: '#9ca3af' }}
          contentStyle={{ color: '#fff' }}
        >
          <Descriptions.Item 
            label={
              <Tooltip title="Information Coefficient，预测能力指标">
                IC均值 <QuestionCircleOutlined className="text-gray-500" />
              </Tooltip>
            }
          >
            <div className="flex items-center gap-2">
              <span style={{ color: levelInfo.color }}>{validation.icMean.toFixed(3)}</span>
              <Progress 
                percent={icPercent} 
                size="small" 
                showInfo={false}
                strokeColor={levelInfo.color}
                style={{ width: 100 }}
              />
              <span className="text-gray-400 text-xs">
                {'⭐'.repeat(levelInfo.stars)} {levelInfo.label}
              </span>
            </div>
          </Descriptions.Item>

          <Descriptions.Item 
            label={
              <Tooltip title="IC_IR = IC均值/IC标准差，稳定性指标">
                IC_IR <QuestionCircleOutlined className="text-gray-500" />
              </Tooltip>
            }
          >
            <div className="flex items-center gap-2">
              <span>{validation.icIR.toFixed(2)}</span>
              <Progress 
                percent={irPercent} 
                size="small" 
                showInfo={false}
                strokeColor="#3b82f6"
                style={{ width: 100 }}
              />
              <span className="text-gray-400 text-xs">
                {validation.icIR >= 0.5 ? '较稳定' : '一般'}
              </span>
            </div>
          </Descriptions.Item>

          <Descriptions.Item label="多头年化收益">
            <span className="text-green-500">
              {(validation.longAnnualReturn * 100).toFixed(1)}%
            </span>
          </Descriptions.Item>

          <Descriptions.Item label="空头年化收益">
            <span className="text-red-500">
              {(validation.shortAnnualReturn * 100).toFixed(1)}%
            </span>
          </Descriptions.Item>

          <Descriptions.Item label="多空收益差">
            <span className={validation.longShortSpread > 0 ? 'text-green-500' : 'text-red-500'}>
              {(validation.longShortSpread * 100).toFixed(1)}%
              {validation.longShortSpread > 0.05 && (
                <Tag color="success" className="ml-2">✅ 因子有效</Tag>
              )}
            </span>
          </Descriptions.Item>
        </Descriptions>
      </div>

      {/* 实测结论 */}
      <div className="p-3 bg-[#1a1a3a] rounded-lg">
        <div className="text-gray-400 text-sm mb-2">🎯 实测结论</div>
        
        <Alert
          type={validation.isEffective ? 'success' : 'warning'}
          message={
            validation.isEffective 
              ? `该因子在美股市场【长期有效】` 
              : `该因子效果较弱，建议谨慎使用`
          }
          className="mb-2"
          showIcon
        />

        <div className="space-y-2 text-sm">
          <div className="flex items-start gap-2">
            <span className="text-yellow-500">⚠️</span>
            <span className="text-gray-300">
              最差表现环境: {validation.worstMarketCondition}
            </span>
          </div>
          
          <div className="flex items-start gap-2">
            <span className="text-green-500">✅</span>
            <span className="text-gray-300">
              最佳表现环境: {validation.bestMarketCondition}
            </span>
          </div>

          {validation.suggestedCombination.length > 0 && (
            <div className="flex items-start gap-2">
              <BulbOutlined className="text-blue-400" />
              <span className="text-gray-300">
                建议搭配: {validation.suggestedCombination.map(f => (
                  <Tag key={f} color="blue" className="mr-1">{f}</Tag>
                ))}
              </span>
            </div>
          )}
        </div>
      </div>
    </Card>
  );
};

export default FactorValidationPanel;
```

---

### 5. 策略回放页面修复

```typescript
// src/pages/StrategyReplay/index.tsx

import React, { useState, useCallback } from 'react';
import { Card, Select, DatePicker, Button, Space, Spin, Empty } from 'antd';
import { 
  PlayCircleOutlined, 
  PauseCircleOutlined,
  StepBackwardOutlined,
  StepForwardOutlined,
  FastBackwardOutlined,
  FastForwardOutlined
} from '@ant-design/icons';
import dayjs from 'dayjs';

// 关键: 使用 ErrorBoundary 包裹 TradingView
import ChartErrorBoundary from '@/components/ErrorBoundary/ChartErrorBoundary';
import TradingViewChart from '@/components/Chart/TradingViewChart';

const StrategyReplayPage: React.FC = () => {
  const [selectedStrategy, setSelectedStrategy] = useState<string | null>(null);
  const [selectedSymbol, setSelectedSymbol] = useState<string | null>(null);
  const [dateRange, setDateRange] = useState<[dayjs.Dayjs, dayjs.Dayjs] | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [playSpeed, setPlaySpeed] = useState(1);
  const [currentTime, setCurrentTime] = useState<string | null>(null);

  // 模拟策略列表
  const strategies = [
    { id: 'stg-001', name: '价值投资策略' },
    { id: 'stg-002', name: '动量突破策略' },
    { id: 'stg-003', name: '日内交易策略' },
  ];

  // 模拟股票列表
  const stocks = [
    { symbol: 'AAPL', name: 'Apple Inc.' },
    { symbol: 'NVDA', name: 'NVIDIA Corp.' },
    { symbol: 'TSLA', name: 'Tesla Inc.' },
    { symbol: 'MSFT', name: 'Microsoft Corp.' },
  ];

  const handlePlay = useCallback(() => {
    setIsPlaying(!isPlaying);
  }, [isPlaying]);

  // 检查是否可以开始回放
  const canStartReplay = selectedStrategy && selectedSymbol && dateRange;

  return (
    <div className="p-6 bg-[#0a0a1a] min-h-screen">
      {/* 顶部控制栏 */}
      <Card className="mb-4 bg-[#0d0d1f] border-[#2a2a4a]">
        <div className="flex flex-wrap items-center gap-4">
          {/* 策略选择 */}
          <Select
            placeholder="选择策略"
            style={{ width: 200 }}
            value={selectedStrategy}
            onChange={setSelectedStrategy}
            options={strategies.map(s => ({ value: s.id, label: s.name }))}
          />

          {/* 股票选择 */}
          <Select
            placeholder="选择股票"
            style={{ width: 200 }}
            value={selectedSymbol}
            onChange={setSelectedSymbol}
            options={stocks.map(s => ({ value: s.symbol, label: `${s.symbol} - ${s.name}` }))}
            showSearch
            filterOption={(input, option) =>
              (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
            }
          />

          {/* 日期范围 */}
          <DatePicker.RangePicker
            value={dateRange}
            onChange={(dates) => setDateRange(dates as [dayjs.Dayjs, dayjs.Dayjs])}
            style={{ width: 280 }}
          />

          {/* 播放控制 */}
          <Space>
            <Button icon={<FastBackwardOutlined />} disabled={!canStartReplay} />
            <Button icon={<StepBackwardOutlined />} disabled={!canStartReplay} />
            <Button 
              type="primary"
              icon={isPlaying ? <PauseCircleOutlined /> : <PlayCircleOutlined />}
              onClick={handlePlay}
              disabled={!canStartReplay}
            >
              {isPlaying ? '暂停' : '播放'}
            </Button>
            <Button icon={<StepForwardOutlined />} disabled={!canStartReplay} />
            <Button icon={<FastForwardOutlined />} disabled={!canStartReplay} />
          </Space>

          {/* 播放速度 */}
          <Select
            value={playSpeed}
            onChange={setPlaySpeed}
            style={{ width: 100 }}
            options={[
              { value: 0.5, label: '0.5x' },
              { value: 1, label: '1x' },
              { value: 2, label: '2x' },
              { value: 5, label: '5x' },
            ]}
          />

          {/* 当前时间 */}
          {currentTime && (
            <div className="text-blue-400 font-mono text-lg ml-auto">
              {currentTime}
            </div>
          )}
        </div>
      </Card>

      {/* 主内容区 */}
      <div className="flex gap-4">
        {/* 图表区域 - 关键: 使用 ErrorBoundary */}
        <div className="flex-1">
          <Card className="bg-[#0d0d1f] border-[#2a2a4a]">
            <ChartErrorBoundary fallbackTitle="策略回放图表加载失败">
              {canStartReplay ? (
                <TradingViewChart
                  symbol={selectedSymbol!}
                  interval="15"
                  dateRange={{
                    start: dateRange![0].format('YYYY-MM-DD'),
                    end: dateRange![1].format('YYYY-MM-DD')
                  }}
                  height={600}
                  showZoomControls={true}
                  allowFullscreen={true}
                />
              ) : (
                <div className="h-[600px] flex items-center justify-center">
                  <Empty description="请选择策略、股票和日期范围开始回放" />
                </div>
              )}
            </ChartErrorBoundary>
          </Card>
        </div>

        {/* 右侧面板 */}
        <div className="w-80 space-y-4">
          {/* 因子值面板 */}
          <Card 
            title="📊 当前因子值" 
            size="small"
            className="bg-[#0d0d1f] border-[#2a2a4a]"
          >
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-400">PE_TTM</span>
                <span className="text-green-500">18.5 ✓</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">ROE</span>
                <span className="text-green-500">25.3% ✓</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">股息率</span>
                <span className="text-red-500">0.8% ✗</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">动量得分</span>
                <span className="text-green-500">0.72 ✓</span>
              </div>
              <div className="border-t border-[#2a2a4a] pt-2 mt-2">
                <span className="text-blue-400">综合信号: 买入 (3/4满足)</span>
              </div>
            </div>
          </Card>

          {/* 信号日志 */}
          <Card 
            title="📋 信号事件日志" 
            size="small"
            className="bg-[#0d0d1f] border-[#2a2a4a]"
            extra={<Button type="link" size="small">导出</Button>}
          >
            <div className="space-y-2 max-h-60 overflow-auto">
              <div className="p-2 bg-green-500/10 border border-green-500/30 rounded">
                <div className="text-xs text-gray-400">14:32:18</div>
                <div className="text-green-400 text-sm">🟢 买入信号触发</div>
                <div className="text-xs text-gray-400">PE降至18.5，低于阈值20</div>
              </div>
              <div className="p-2 bg-yellow-500/10 border border-yellow-500/30 rounded">
                <div className="text-xs text-gray-400">14:15:00</div>
                <div className="text-yellow-400 text-sm">🟡 条件检查</div>
                <div className="text-xs text-gray-400">PE=19.2，接近阈值</div>
              </div>
              <div className="p-2 bg-red-500/10 border border-red-500/30 rounded">
                <div className="text-xs text-gray-400">11:30:00</div>
                <div className="text-red-400 text-sm">🔴 卖出信号</div>
                <div className="text-xs text-gray-400">止盈触发，收益+5.2%</div>
              </div>
            </div>
          </Card>

          {/* 回放洞察 */}
          <Card 
            title="🎯 回放洞察" 
            size="small"
            className="bg-[#0d0d1f] border-[#2a2a4a]"
          >
            <div className="grid grid-cols-2 gap-2 mb-4">
              <div className="text-center p-2 bg-[#1a1a3a] rounded">
                <div className="text-lg font-bold text-white">8</div>
                <div className="text-xs text-gray-400">信号数</div>
              </div>
              <div className="text-center p-2 bg-[#1a1a3a] rounded">
                <div className="text-lg font-bold text-green-400">75%</div>
                <div className="text-xs text-gray-400">胜率</div>
              </div>
              <div className="text-center p-2 bg-[#1a1a3a] rounded">
                <div className="text-lg font-bold text-white">75%</div>
                <div className="text-xs text-gray-400">执行率</div>
              </div>
              <div className="text-center p-2 bg-[#1a1a3a] rounded">
                <div className="text-lg font-bold text-green-400">+2.3%</div>
                <div className="text-xs text-gray-400">Alpha</div>
              </div>
            </div>
            
            <div className="flex gap-2">
              <Button type="primary" size="small" block>详细报告</Button>
              <Button size="small" block>保存回放</Button>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default StrategyReplayPage;
```

---

## 📋 实施计划

### Week 1: P0修复
| 天数 | 任务 | 负责 |
|:----:|------|------|
| Day 1-2 | TradingView组件修复 + 缩放功能 | 前端 |
| Day 2-3 | ErrorBoundary全局部署 | 前端 |
| Day 3-4 | AI状态指示器 | 前端 |
| Day 4-5 | 因子验证面板 | 前后端 |

### Week 2: P1功能
| 天数 | 任务 | 负责 |
|:----:|------|------|
| Day 1-2 | 策略部署向导 | 前端 |
| Day 2-3 | 策略冲突检测 | 后端 |
| Day 3-4 | PDT规则管理增强 | 前后端 |
| Day 4-5 | 实盘vs回测监控 | 前后端 |

### Week 3: P1完善
| 天数 | 任务 | 负责 |
|:----:|------|------|
| Day 1-3 | 交易归因系统 | 前后端 |
| Day 3-5 | 日内交易视图完善 | 前端 |

---

## ✅ 验收标准

### TradingView组件
- [ ] 策略回放页面正常加载
- [ ] 日内交易页面正常加载
- [ ] 缩放功能 50%-200% 正常工作
- [ ] 全屏功能正常
- [ ] 展开/收起功能正常
- [ ] 组件崩溃时显示友好错误页面

### 因子验证
- [ ] 显示IC均值和IC_IR
- [ ] 显示多空收益差
- [ ] 显示有效性等级
- [ ] 显示建议搭配因子

### AI状态
- [ ] 显示连接状态图标
- [ ] 显示当前模型名称
- [ ] 显示响应延迟
- [ ] 断开时可点击重试

---

**文档版本**: 1.0  
**更新时间**: 2026-01-09
