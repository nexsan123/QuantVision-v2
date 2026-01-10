# Sprint 7: 实时交易监控完整版 (7天)

> **文档版本**: 1.0  
> **预计时长**: 7天  
> **前置依赖**: Sprint 0-6 全部完成  
> **PRD参考**: 4.16 实时交易监控界面, 4.18 分策略持仓管理  
> **交付物**: TradingView图表集成、策略信号可视化、手动交易面板、分策略持仓

---

## 目标

实现完整的实时交易监控界面，包括：
1. TradingView图表集成
2. 策略信号可视化覆盖层
3. 手动交易面板
4. 分策略持仓管理

---

## Part A: TradingView图表集成 (3天)

### Task 7.1: TradingView Widget集成

**文件**: `frontend/src/components/Chart/TradingViewChart.tsx`

```tsx
import React, { useEffect, useRef, useState } from 'react';

interface Props {
  symbol: string;
  interval: '1' | '5' | '15' | '60' | '240' | 'D';
  theme?: 'light' | 'dark';
  height?: number;
  onSymbolChange?: (symbol: string) => void;
}

// TradingView Widget配置
declare global {
  interface Window {
    TradingView: any;
  }
}

export const TradingViewChart: React.FC<Props> = ({
  symbol,
  interval = '15',
  theme = 'dark',
  height = 500,
  onSymbolChange
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const widgetRef = useRef<any>(null);
  
  useEffect(() => {
    // 加载TradingView库
    const script = document.createElement('script');
    script.src = 'https://s3.tradingview.com/tv.js';
    script.async = true;
    script.onload = initWidget;
    document.head.appendChild(script);
    
    return () => {
      if (widgetRef.current) {
        widgetRef.current.remove();
      }
    };
  }, []);
  
  useEffect(() => {
    if (widgetRef.current && symbol) {
      widgetRef.current.setSymbol(symbol, interval);
    }
  }, [symbol, interval]);
  
  const initWidget = () => {
    if (!containerRef.current || !window.TradingView) return;
    
    widgetRef.current = new window.TradingView.widget({
      container_id: containerRef.current.id,
      symbol: symbol,
      interval: interval,
      timezone: 'America/New_York',
      theme: theme,
      style: '1', // 蜡烛图
      locale: 'zh_CN',
      toolbar_bg: '#0d0d1f',
      enable_publishing: false,
      hide_side_toolbar: false,
      allow_symbol_change: true,
      save_image: false,
      height: height,
      width: '100%',
      
      // 自定义样式
      overrides: {
        'mainSeriesProperties.candleStyle.upColor': '#22c55e',
        'mainSeriesProperties.candleStyle.downColor': '#ef4444',
        'mainSeriesProperties.candleStyle.borderUpColor': '#22c55e',
        'mainSeriesProperties.candleStyle.borderDownColor': '#ef4444',
        'mainSeriesProperties.candleStyle.wickUpColor': '#22c55e',
        'mainSeriesProperties.candleStyle.wickDownColor': '#ef4444',
        'paneProperties.background': '#0a0a1a',
        'paneProperties.vertGridProperties.color': '#2a2a4a',
        'paneProperties.horzGridProperties.color': '#2a2a4a',
        'scalesProperties.textColor': '#9ca3af',
      },
      
      // 禁用部分功能
      disabled_features: [
        'header_symbol_search',
        'header_compare',
        'header_undo_redo',
        'header_screenshot',
        'header_fullscreen_button',
      ],
      
      // 启用功能
      enabled_features: [
        'study_templates',
        'use_localstorage_for_settings',
      ],
      
      // 默认指标
      studies: [
        'MASimple@tv-basicstudies',
        'RSI@tv-basicstudies',
        'MACD@tv-basicstudies',
      ],
    });
    
    // 监听符号变化
    widgetRef.current.onChartReady(() => {
      widgetRef.current.activeChart().onSymbolChanged().subscribe(null, (symbolInfo: any) => {
        onSymbolChange?.(symbolInfo.name);
      });
    });
  };
  
  return (
    <div 
      id={`tradingview_${Date.now()}`}
      ref={containerRef}
      className="tradingview-container"
      style={{ height }}
    />
  );
};
```

**验收标准**:
- [ ] 图表加载正常
- [ ] K线显示正确
- [ ] 时间周期切换正常
- [ ] 技术指标可添加

---

### Task 7.2: 图表工具栏

**文件**: `frontend/src/components/Chart/ChartToolbar.tsx`

```tsx
import React from 'react';

interface Props {
  symbol: string;
  price: number;
  change: number;
  changePct: number;
  interval: string;
  onIntervalChange: (interval: string) => void;
  onSymbolSearch: () => void;
}

const INTERVALS = [
  { value: '1', label: '1分' },
  { value: '5', label: '5分' },
  { value: '15', label: '15分' },
  { value: '60', label: '1时' },
  { value: '240', label: '4时' },
  { value: 'D', label: '日线' },
];

export const ChartToolbar: React.FC<Props> = ({
  symbol,
  price,
  change,
  changePct,
  interval,
  onIntervalChange,
  onSymbolSearch
}) => {
  const isPositive = change >= 0;
  
  return (
    <div className="chart-toolbar">
      {/* 股票信息 */}
      <div className="chart-symbol-info">
        <button 
          className="symbol-selector"
          onClick={onSymbolSearch}
        >
          <span className="symbol-name">{symbol}</span>
          <span className="symbol-dropdown">▼</span>
        </button>
        
        <span className="symbol-price">${price.toFixed(2)}</span>
        <span className={`symbol-change ${isPositive ? 'positive' : 'negative'}`}>
          {isPositive ? '+' : ''}{change.toFixed(2)} ({changePct.toFixed(2)}%)
        </span>
      </div>
      
      {/* 时间周期 */}
      <div className="chart-intervals">
        {INTERVALS.map(({ value, label }) => (
          <button
            key={value}
            className={`interval-btn ${interval === value ? 'active' : ''}`}
            onClick={() => onIntervalChange(value)}
          >
            {label}
          </button>
        ))}
      </div>
      
      {/* 工具按钮 */}
      <div className="chart-tools">
        <button className="tool-btn" title="指标">📊</button>
        <button className="tool-btn" title="画线">✏️</button>
        <button className="tool-btn" title="全屏">⛶</button>
      </div>
    </div>
  );
};
```

---

### Task 7.3: 信号覆盖层

**文件**: `frontend/src/components/Chart/SignalOverlay.tsx`

```tsx
import React, { useEffect, useRef } from 'react';

interface Signal {
  type: 'buy' | 'sell';
  price: number;
  time: number; // Unix timestamp
  strength: number;
  reason: string;
}

interface Position {
  entryPrice: number;
  quantity: number;
  stopLoss?: number;
  takeProfit?: number;
}

interface Props {
  signals: Signal[];
  position?: Position;
  chartHeight: number;
  chartWidth: number;
  priceRange: { min: number; max: number };
  timeRange: { start: number; end: number };
}

export const SignalOverlay: React.FC<Props> = ({
  signals,
  position,
  chartHeight,
  chartWidth,
  priceRange,
  timeRange
}) => {
  const svgRef = useRef<SVGSVGElement>(null);
  
  // 价格转Y坐标
  const priceToY = (price: number) => {
    const { min, max } = priceRange;
    return chartHeight - ((price - min) / (max - min)) * chartHeight;
  };
  
  // 时间转X坐标
  const timeToX = (time: number) => {
    const { start, end } = timeRange;
    return ((time - start) / (end - start)) * chartWidth;
  };
  
  return (
    <svg 
      ref={svgRef}
      className="signal-overlay"
      width={chartWidth}
      height={chartHeight}
      style={{ position: 'absolute', top: 0, left: 0, pointerEvents: 'none' }}
    >
      {/* 止盈线 */}
      {position?.takeProfit && (
        <g className="take-profit-line">
          <line
            x1={0}
            y1={priceToY(position.takeProfit)}
            x2={chartWidth}
            y2={priceToY(position.takeProfit)}
            stroke="#22c55e"
            strokeWidth={2}
            strokeDasharray="8 4"
          />
          <text
            x={chartWidth - 80}
            y={priceToY(position.takeProfit) - 5}
            fill="#22c55e"
            fontSize={12}
          >
            🎯止盈 ${position.takeProfit.toFixed(2)}
          </text>
        </g>
      )}
      
      {/* 止损线 */}
      {position?.stopLoss && (
        <g className="stop-loss-line">
          <line
            x1={0}
            y1={priceToY(position.stopLoss)}
            x2={chartWidth}
            y2={priceToY(position.stopLoss)}
            stroke="#ef4444"
            strokeWidth={2}
            strokeDasharray="8 4"
          />
          <text
            x={chartWidth - 80}
            y={priceToY(position.stopLoss) - 5}
            fill="#ef4444"
            fontSize={12}
          >
            🛑止损 ${position.stopLoss.toFixed(2)}
          </text>
        </g>
      )}
      
      {/* 入场价线 */}
      {position?.entryPrice && (
        <g className="entry-price-line">
          <line
            x1={0}
            y1={priceToY(position.entryPrice)}
            x2={chartWidth}
            y2={priceToY(position.entryPrice)}
            stroke="#3b82f6"
            strokeWidth={1}
            strokeDasharray="4 4"
          />
          <text
            x={chartWidth - 80}
            y={priceToY(position.entryPrice) - 5}
            fill="#3b82f6"
            fontSize={12}
          >
            入场 ${position.entryPrice.toFixed(2)}
          </text>
        </g>
      )}
      
      {/* 交易信号标记 */}
      {signals.map((signal, i) => (
        <g 
          key={i}
          className={`signal-marker signal-${signal.type}`}
          transform={`translate(${timeToX(signal.time)}, ${priceToY(signal.price)})`}
        >
          {signal.type === 'buy' ? (
            // 买入信号 - 绿色上三角
            <polygon
              points="0,-12 8,4 -8,4"
              fill="#22c55e"
              stroke="#fff"
              strokeWidth={1}
            />
          ) : (
            // 卖出信号 - 红色下三角
            <polygon
              points="0,12 8,-4 -8,-4"
              fill="#ef4444"
              stroke="#fff"
              strokeWidth={1}
            />
          )}
          
          {/* 悬停提示 (需要JS处理) */}
          <title>
            {signal.type === 'buy' ? '买入' : '卖出'}: ${signal.price.toFixed(2)}
            强度: {signal.strength}%
            原因: {signal.reason}
          </title>
        </g>
      ))}
      
      {/* 持仓标记 */}
      {position && (
        <circle
          cx={chartWidth - 30}
          cy={priceToY(position.entryPrice)}
          r={8}
          fill="#3b82f6"
          stroke="#fff"
          strokeWidth={2}
        />
      )}
    </svg>
  );
};
```

**验收标准**:
- [ ] 止盈止损线显示正确
- [ ] 买入卖出信号标记正确
- [ ] 线条样式符合PRD
- [ ] 悬停提示信息完整

---

## Part B: 手动交易面板 (2天)

### Task 7.4: 手动交易服务 (后端)

**文件**: `backend/app/services/manual_trade_service.py`

```python
from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel
from decimal import Decimal
import uuid

class ManualTradeOrder(BaseModel):
    """手动交易订单"""
    order_id: str
    user_id: str
    account_id: str
    strategy_id: Optional[str] = None  # 可选归属策略
    
    symbol: str
    side: Literal["buy", "sell"]
    order_type: Literal["market", "limit", "stop"]
    quantity: int
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None
    
    # 止盈止损 (买入时设置)
    take_profit: Optional[float] = None
    stop_loss: Optional[float] = None
    
    status: Literal["pending", "filled", "cancelled", "rejected"]
    filled_quantity: int = 0
    filled_price: Optional[float] = None
    
    created_at: datetime
    filled_at: Optional[datetime] = None

class ManualTradeService:
    """手动交易服务"""
    
    def __init__(self, db_session, broker_client):
        self.db = db_session
        self.broker = broker_client
    
    async def place_order(
        self,
        user_id: str,
        account_id: str,
        symbol: str,
        side: str,
        order_type: str,
        quantity: int,
        strategy_id: Optional[str] = None,
        limit_price: Optional[float] = None,
        stop_price: Optional[float] = None,
        take_profit: Optional[float] = None,
        stop_loss: Optional[float] = None,
    ) -> ManualTradeOrder:
        """下单"""
        
        # 1. 验证订单参数
        await self._validate_order(
            user_id, account_id, symbol, side, quantity, limit_price
        )
        
        # 2. 检查PDT规则 (如果是日内交易)
        if await self._is_day_trade(account_id, symbol, side):
            can_trade, reason = await self._check_pdt(account_id)
            if not can_trade:
                raise ValueError(f"PDT限制: {reason}")
        
        # 3. 创建订单
        order = ManualTradeOrder(
            order_id=str(uuid.uuid4()),
            user_id=user_id,
            account_id=account_id,
            strategy_id=strategy_id,
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            limit_price=limit_price,
            stop_price=stop_price,
            take_profit=take_profit,
            stop_loss=stop_loss,
            status="pending",
            created_at=datetime.now()
        )
        
        # 4. 发送到券商
        try:
            broker_order = await self.broker.place_order(order)
            order.status = broker_order.status
            if broker_order.status == "filled":
                order.filled_quantity = broker_order.filled_quantity
                order.filled_price = broker_order.filled_price
                order.filled_at = datetime.now()
        except Exception as e:
            order.status = "rejected"
            raise
        
        # 5. 保存订单
        await self._save_order(order)
        
        # 6. 如果有止盈止损，创建条件单
        if order.status == "filled" and side == "buy":
            if take_profit:
                await self._create_take_profit_order(order, take_profit)
            if stop_loss:
                await self._create_stop_loss_order(order, stop_loss)
        
        return order
    
    async def cancel_order(self, order_id: str, user_id: str) -> bool:
        """取消订单"""
        order = await self._get_order(order_id)
        if not order or order.user_id != user_id:
            return False
        
        if order.status != "pending":
            return False
        
        await self.broker.cancel_order(order.order_id)
        order.status = "cancelled"
        await self._update_order(order)
        return True
    
    async def get_orders(
        self,
        user_id: str,
        status: Optional[str] = None,
        symbol: Optional[str] = None,
        limit: int = 50
    ) -> list[ManualTradeOrder]:
        """获取订单列表"""
        # 数据库查询实现
        pass
    
    async def _validate_order(
        self,
        user_id: str,
        account_id: str,
        symbol: str,
        side: str,
        quantity: int,
        limit_price: Optional[float]
    ):
        """验证订单"""
        # 检查账户权限
        # 检查资金是否足够
        # 检查持仓是否足够（卖出时）
        # 检查最小交易数量
        pass
```

---

### Task 7.5: 手动交易API (后端)

**文件**: `backend/app/api/v1/manual_trade.py`

```python
from fastapi import APIRouter, Depends, HTTPException
from typing import Optional, Literal
from pydantic import BaseModel
from app.services.manual_trade_service import ManualTradeService, ManualTradeOrder
from app.core.deps import get_current_user, get_manual_trade_service

router = APIRouter(prefix="/manual-trade", tags=["Manual Trade"])

class PlaceOrderRequest(BaseModel):
    symbol: str
    side: Literal["buy", "sell"]
    order_type: Literal["market", "limit", "stop"] = "market"
    quantity: int
    strategy_id: Optional[str] = None  # 归属策略
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None
    take_profit: Optional[float] = None
    stop_loss: Optional[float] = None

@router.post("/order", response_model=ManualTradeOrder)
async def place_order(
    request: PlaceOrderRequest,
    current_user = Depends(get_current_user),
    trade_service: ManualTradeService = Depends(get_manual_trade_service)
):
    """下单"""
    try:
        return await trade_service.place_order(
            user_id=current_user.id,
            account_id=current_user.default_account_id,
            **request.dict()
        )
    except ValueError as e:
        raise HTTPException(400, str(e))

@router.delete("/order/{order_id}")
async def cancel_order(
    order_id: str,
    current_user = Depends(get_current_user),
    trade_service: ManualTradeService = Depends(get_manual_trade_service)
):
    """取消订单"""
    success = await trade_service.cancel_order(order_id, current_user.id)
    if not success:
        raise HTTPException(400, "无法取消订单")
    return {"success": True}

@router.get("/orders", response_model=list[ManualTradeOrder])
async def get_orders(
    status: Optional[str] = None,
    symbol: Optional[str] = None,
    limit: int = 50,
    current_user = Depends(get_current_user),
    trade_service: ManualTradeService = Depends(get_manual_trade_service)
):
    """获取订单列表"""
    return await trade_service.get_orders(
        user_id=current_user.id,
        status=status,
        symbol=symbol,
        limit=limit
    )

@router.get("/quote/{symbol}")
async def get_quote(
    symbol: str,
    current_user = Depends(get_current_user),
    trade_service: ManualTradeService = Depends(get_manual_trade_service)
):
    """获取实时报价"""
    quote = await trade_service.get_quote(symbol)
    return {
        "symbol": symbol,
        "bid": quote.bid,
        "ask": quote.ask,
        "last": quote.last,
        "volume": quote.volume
    }
```

---

### Task 7.6: 快速交易面板 (前端)

**文件**: `frontend/src/components/Trade/QuickTradePanel.tsx`

```tsx
import React, { useState } from 'react';

interface Props {
  symbol: string;
  price: number;
  position?: {
    quantity: number;
    avgCost: number;
    pnl: number;
  };
  onBuy: (quantity: number, orderType: string, price?: number) => Promise<void>;
  onSell: (quantity: number, orderType: string, price?: number) => Promise<void>;
}

const QUICK_QUANTITIES = [100, 500, 1000];
const SELL_PERCENTAGES = [25, 50, 100];

export const QuickTradePanel: React.FC<Props> = ({
  symbol,
  price,
  position,
  onBuy,
  onSell
}) => {
  const [activeTab, setActiveTab] = useState<'buy' | 'sell'>('buy');
  const [quantity, setQuantity] = useState(100);
  const [orderType, setOrderType] = useState<'market' | 'limit'>('market');
  const [limitPrice, setLimitPrice] = useState(price);
  const [loading, setLoading] = useState(false);
  
  const estimatedAmount = quantity * (orderType === 'limit' ? limitPrice : price);
  
  const handleSubmit = async () => {
    setLoading(true);
    try {
      if (activeTab === 'buy') {
        await onBuy(quantity, orderType, orderType === 'limit' ? limitPrice : undefined);
      } else {
        await onSell(quantity, orderType, orderType === 'limit' ? limitPrice : undefined);
      }
    } finally {
      setLoading(false);
    }
  };
  
  const handleSellPercentage = (pct: number) => {
    if (position) {
      setQuantity(Math.floor(position.quantity * pct / 100));
    }
  };
  
  return (
    <div className="quick-trade-panel">
      <div className="trade-header">
        <span className="trade-icon">⚡</span>
        <span className="trade-title">快速交易</span>
      </div>
      
      {/* 股票信息 */}
      <div className="trade-symbol">
        <span className="symbol-name">{symbol}</span>
        <span className="symbol-price">${price.toFixed(2)}</span>
      </div>
      
      {/* 买入/卖出切换 */}
      <div className="trade-tabs">
        <button
          className={`tab-btn ${activeTab === 'buy' ? 'active buy' : ''}`}
          onClick={() => setActiveTab('buy')}
        >
          买入
        </button>
        <button
          className={`tab-btn ${activeTab === 'sell' ? 'active sell' : ''}`}
          onClick={() => setActiveTab('sell')}
          disabled={!position}
        >
          卖出
        </button>
      </div>
      
      {/* 订单类型 */}
      <div className="trade-order-type">
        <button
          className={`type-btn ${orderType === 'market' ? 'active' : ''}`}
          onClick={() => setOrderType('market')}
        >
          市价
        </button>
        <button
          className={`type-btn ${orderType === 'limit' ? 'active' : ''}`}
          onClick={() => setOrderType('limit')}
        >
          限价
        </button>
      </div>
      
      {/* 限价输入 */}
      {orderType === 'limit' && (
        <div className="trade-limit-price">
          <label>限价</label>
          <input
            type="number"
            value={limitPrice}
            onChange={e => setLimitPrice(parseFloat(e.target.value))}
            step={0.01}
          />
        </div>
      )}
      
      {/* 数量选择 */}
      <div className="trade-quantity">
        <label>数量</label>
        
        {activeTab === 'buy' ? (
          <div className="quantity-buttons">
            {QUICK_QUANTITIES.map(q => (
              <button
                key={q}
                className={`qty-btn ${quantity === q ? 'active' : ''}`}
                onClick={() => setQuantity(q)}
              >
                {q}
              </button>
            ))}
          </div>
        ) : (
          <div className="quantity-buttons">
            {SELL_PERCENTAGES.map(pct => (
              <button
                key={pct}
                className="qty-btn"
                onClick={() => handleSellPercentage(pct)}
              >
                {pct}%
              </button>
            ))}
          </div>
        )}
        
        <input
          type="number"
          value={quantity}
          onChange={e => setQuantity(parseInt(e.target.value) || 0)}
          className="quantity-input"
        />
      </div>
      
      {/* 预估金额 */}
      <div className="trade-estimate">
        <span>预估金额</span>
        <span className="estimate-value">
          ${estimatedAmount.toLocaleString()}
        </span>
      </div>
      
      {/* 持仓信息 */}
      {position && (
        <div className="trade-position">
          <span>当前持仓: {position.quantity}股</span>
          <span className={position.pnl >= 0 ? 'positive' : 'negative'}>
            {position.pnl >= 0 ? '+' : ''}{position.pnl.toFixed(2)}
          </span>
        </div>
      )}
      
      {/* 提交按钮 */}
      <button
        className={`trade-submit ${activeTab}`}
        onClick={handleSubmit}
        disabled={loading || quantity <= 0}
      >
        {loading ? '处理中...' : (activeTab === 'buy' ? '确认买入' : '确认卖出')}
      </button>
    </div>
  );
};
```

**验收标准**:
- [ ] 买入/卖出切换正常
- [ ] 数量选择正常
- [ ] 市价/限价切换正常
- [ ] 预估金额计算正确

---

## Part C: 分策略持仓管理 (2天)

### Task 7.7: 分策略持仓Schema (后端)

**文件**: `backend/app/schemas/position.py`

```python
from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime
from decimal import Decimal

class StrategyPosition(BaseModel):
    """策略持仓 (逻辑隔离)"""
    position_id: str
    user_id: str
    account_id: str
    strategy_id: Optional[str]  # None = 手动交易
    strategy_name: Optional[str]
    
    symbol: str
    quantity: int
    avg_cost: float
    current_price: float
    market_value: float
    
    unrealized_pnl: float
    unrealized_pnl_pct: float
    realized_pnl: float  # 已实现盈亏
    
    # 止盈止损
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    
    created_at: datetime
    updated_at: datetime

class PositionGroup(BaseModel):
    """持仓分组 (按策略)"""
    strategy_id: Optional[str]
    strategy_name: str  # "手动交易" 或策略名
    positions: list[StrategyPosition]
    total_market_value: float
    total_unrealized_pnl: float
    total_unrealized_pnl_pct: float

class AccountPositionSummary(BaseModel):
    """账户持仓汇总"""
    account_id: str
    total_market_value: float
    total_cash: float
    total_equity: float
    
    # 按策略分组
    groups: list[PositionGroup]
    
    # 同股票汇总视图
    consolidated: list[ConsolidatedPosition]
    
    # 风险指标
    concentration_warnings: list[str]  # 集中度警告

class ConsolidatedPosition(BaseModel):
    """同股票汇总持仓"""
    symbol: str
    total_quantity: int
    weighted_avg_cost: float
    current_price: float
    total_market_value: float
    total_unrealized_pnl: float
    
    # 来源策略
    sources: list[PositionSource]
    
    # 集中度
    concentration_pct: float  # 占账户比例

class PositionSource(BaseModel):
    """持仓来源"""
    strategy_id: Optional[str]
    strategy_name: str
    quantity: int
    pnl: float
```

---

### Task 7.8: 分策略持仓服务 (后端)

**文件**: `backend/app/services/position_service.py`

```python
from typing import Optional
from app.schemas.position import (
    StrategyPosition, PositionGroup, AccountPositionSummary,
    ConsolidatedPosition, PositionSource
)

class PositionService:
    """分策略持仓服务"""
    
    CONCENTRATION_WARNING_THRESHOLD = 0.30  # 30%
    
    def __init__(self, db_session, market_data_service):
        self.db = db_session
        self.market_data = market_data_service
    
    async def get_account_positions(
        self,
        user_id: str,
        account_id: str
    ) -> AccountPositionSummary:
        """获取账户持仓汇总"""
        
        # 1. 获取所有持仓
        all_positions = await self._get_all_positions(account_id)
        
        # 2. 更新实时价格
        symbols = list(set(p.symbol for p in all_positions))
        prices = await self.market_data.get_quotes(symbols)
        for pos in all_positions:
            pos.current_price = prices.get(pos.symbol, pos.current_price)
            pos.market_value = pos.quantity * pos.current_price
            pos.unrealized_pnl = pos.market_value - (pos.quantity * pos.avg_cost)
            pos.unrealized_pnl_pct = pos.unrealized_pnl / (pos.quantity * pos.avg_cost) if pos.avg_cost > 0 else 0
        
        # 3. 按策略分组
        groups = self._group_by_strategy(all_positions)
        
        # 4. 生成同股票汇总
        consolidated = self._consolidate_positions(all_positions)
        
        # 5. 检查集中度风险
        account = await self._get_account(account_id)
        total_equity = account.cash + sum(p.market_value for p in all_positions)
        warnings = self._check_concentration(consolidated, total_equity)
        
        return AccountPositionSummary(
            account_id=account_id,
            total_market_value=sum(p.market_value for p in all_positions),
            total_cash=account.cash,
            total_equity=total_equity,
            groups=groups,
            consolidated=consolidated,
            concentration_warnings=warnings
        )
    
    def _group_by_strategy(
        self,
        positions: list[StrategyPosition]
    ) -> list[PositionGroup]:
        """按策略分组"""
        
        from collections import defaultdict
        grouped = defaultdict(list)
        
        for pos in positions:
            key = pos.strategy_id or "__manual__"
            grouped[key].append(pos)
        
        groups = []
        for strategy_id, pos_list in grouped.items():
            total_value = sum(p.market_value for p in pos_list)
            total_cost = sum(p.quantity * p.avg_cost for p in pos_list)
            total_pnl = sum(p.unrealized_pnl for p in pos_list)
            
            groups.append(PositionGroup(
                strategy_id=None if strategy_id == "__manual__" else strategy_id,
                strategy_name=pos_list[0].strategy_name or "手动交易",
                positions=pos_list,
                total_market_value=total_value,
                total_unrealized_pnl=total_pnl,
                total_unrealized_pnl_pct=total_pnl / total_cost if total_cost > 0 else 0
            ))
        
        return groups
    
    def _consolidate_positions(
        self,
        positions: list[StrategyPosition]
    ) -> list[ConsolidatedPosition]:
        """同股票汇总"""
        
        from collections import defaultdict
        by_symbol = defaultdict(list)
        
        for pos in positions:
            by_symbol[pos.symbol].append(pos)
        
        consolidated = []
        for symbol, pos_list in by_symbol.items():
            total_qty = sum(p.quantity for p in pos_list)
            total_cost = sum(p.quantity * p.avg_cost for p in pos_list)
            weighted_avg = total_cost / total_qty if total_qty > 0 else 0
            
            sources = [
                PositionSource(
                    strategy_id=p.strategy_id,
                    strategy_name=p.strategy_name or "手动交易",
                    quantity=p.quantity,
                    pnl=p.unrealized_pnl
                )
                for p in pos_list
            ]
            
            consolidated.append(ConsolidatedPosition(
                symbol=symbol,
                total_quantity=total_qty,
                weighted_avg_cost=weighted_avg,
                current_price=pos_list[0].current_price,
                total_market_value=sum(p.market_value for p in pos_list),
                total_unrealized_pnl=sum(p.unrealized_pnl for p in pos_list),
                sources=sources,
                concentration_pct=0  # 后续计算
            ))
        
        return consolidated
    
    def _check_concentration(
        self,
        consolidated: list[ConsolidatedPosition],
        total_equity: float
    ) -> list[str]:
        """检查集中度风险"""
        
        warnings = []
        for pos in consolidated:
            pos.concentration_pct = pos.total_market_value / total_equity if total_equity > 0 else 0
            
            if pos.concentration_pct > self.CONCENTRATION_WARNING_THRESHOLD:
                warnings.append(
                    f"⚠️ {pos.symbol} 持仓占比 {pos.concentration_pct*100:.1f}%，"
                    f"超过安全阈值 {self.CONCENTRATION_WARNING_THRESHOLD*100:.0f}%"
                )
        
        return warnings
    
    async def sell_strategy_position(
        self,
        position_id: str,
        quantity: int,
        user_id: str
    ):
        """卖出特定策略的持仓"""
        position = await self._get_position(position_id)
        
        if not position or position.user_id != user_id:
            raise ValueError("持仓不存在")
        
        if quantity > position.quantity:
            raise ValueError("卖出数量超过持仓")
        
        # 只卖出这个策略的份额
        # 实际执行时，券商账户层面是合并的，但我们在系统中独立记录
        # ...
```

---

### Task 7.9: 持仓管理API (后端)

**文件**: `backend/app/api/v1/positions.py`

```python
from fastapi import APIRouter, Depends
from app.services.position_service import PositionService
from app.schemas.position import AccountPositionSummary, StrategyPosition
from app.core.deps import get_current_user, get_position_service

router = APIRouter(prefix="/positions", tags=["Positions"])

@router.get("/summary", response_model=AccountPositionSummary)
async def get_position_summary(
    current_user = Depends(get_current_user),
    position_service: PositionService = Depends(get_position_service)
):
    """获取持仓汇总 (分策略视图)"""
    return await position_service.get_account_positions(
        user_id=current_user.id,
        account_id=current_user.default_account_id
    )

@router.get("/strategy/{strategy_id}", response_model=list[StrategyPosition])
async def get_strategy_positions(
    strategy_id: str,
    current_user = Depends(get_current_user),
    position_service: PositionService = Depends(get_position_service)
):
    """获取特定策略的持仓"""
    return await position_service.get_positions_by_strategy(
        user_id=current_user.id,
        strategy_id=strategy_id
    )

@router.get("/symbol/{symbol}")
async def get_symbol_positions(
    symbol: str,
    current_user = Depends(get_current_user),
    position_service: PositionService = Depends(get_position_service)
):
    """获取特定股票的持仓 (按策略分解)"""
    summary = await position_service.get_account_positions(
        user_id=current_user.id,
        account_id=current_user.default_account_id
    )
    
    for pos in summary.consolidated:
        if pos.symbol == symbol:
            return pos
    
    return None
```

---

### Task 7.10: 持仓面板组件 (前端)

**文件**: `frontend/src/components/Position/PositionPanel.tsx`

```tsx
import React, { useState } from 'react';
import { AccountPositionSummary, PositionGroup, ConsolidatedPosition } from '@/types/position';

interface Props {
  summary: AccountPositionSummary;
  onSellPosition: (positionId: string, quantity: number) => void;
}

type ViewMode = 'strategy' | 'symbol';

export const PositionPanel: React.FC<Props> = ({ summary, onSellPosition }) => {
  const [viewMode, setViewMode] = useState<ViewMode>('strategy');
  
  return (
    <div className="position-panel">
      <div className="position-header">
        <h3>持仓管理</h3>
        
        {/* 视图切换 */}
        <div className="view-toggle">
          <button
            className={viewMode === 'strategy' ? 'active' : ''}
            onClick={() => setViewMode('strategy')}
          >
            按策略
          </button>
          <button
            className={viewMode === 'symbol' ? 'active' : ''}
            onClick={() => setViewMode('symbol')}
          >
            按股票
          </button>
        </div>
      </div>
      
      {/* 账户汇总 */}
      <div className="account-summary">
        <div className="summary-item">
          <span className="label">总市值</span>
          <span className="value">${summary.total_market_value.toLocaleString()}</span>
        </div>
        <div className="summary-item">
          <span className="label">现金</span>
          <span className="value">${summary.total_cash.toLocaleString()}</span>
        </div>
        <div className="summary-item">
          <span className="label">总权益</span>
          <span className="value">${summary.total_equity.toLocaleString()}</span>
        </div>
      </div>
      
      {/* 集中度警告 */}
      {summary.concentration_warnings.length > 0 && (
        <div className="concentration-warnings">
          {summary.concentration_warnings.map((warning, i) => (
            <div key={i} className="warning-item">{warning}</div>
          ))}
        </div>
      )}
      
      {/* 持仓列表 */}
      {viewMode === 'strategy' ? (
        <StrategyView groups={summary.groups} onSellPosition={onSellPosition} />
      ) : (
        <SymbolView positions={summary.consolidated} />
      )}
    </div>
  );
};

const StrategyView: React.FC<{
  groups: PositionGroup[];
  onSellPosition: (positionId: string, quantity: number) => void;
}> = ({ groups, onSellPosition }) => (
  <div className="strategy-view">
    {groups.map(group => (
      <div key={group.strategy_id || 'manual'} className="strategy-group">
        <div className="group-header">
          <span className="group-name">{group.strategy_name}</span>
          <span className={`group-pnl ${group.total_unrealized_pnl >= 0 ? 'positive' : 'negative'}`}>
            {group.total_unrealized_pnl >= 0 ? '+' : ''}
            ${group.total_unrealized_pnl.toFixed(2)}
            ({(group.total_unrealized_pnl_pct * 100).toFixed(2)}%)
          </span>
        </div>
        
        <div className="group-positions">
          {group.positions.map(pos => (
            <div key={pos.position_id} className="position-row">
              <span className="symbol">{pos.symbol}</span>
              <span className="quantity">{pos.quantity}股</span>
              <span className="cost">${pos.avg_cost.toFixed(2)}</span>
              <span className="current">${pos.current_price.toFixed(2)}</span>
              <span className={`pnl ${pos.unrealized_pnl >= 0 ? 'positive' : 'negative'}`}>
                {pos.unrealized_pnl >= 0 ? '+' : ''}${pos.unrealized_pnl.toFixed(2)}
              </span>
              <button 
                className="sell-btn"
                onClick={() => onSellPosition(pos.position_id, pos.quantity)}
              >
                卖出
              </button>
            </div>
          ))}
        </div>
      </div>
    ))}
  </div>
);

const SymbolView: React.FC<{ positions: ConsolidatedPosition[] }> = ({ positions }) => (
  <div className="symbol-view">
    {positions.map(pos => (
      <div key={pos.symbol} className="consolidated-row">
        <div className="consolidated-header">
          <span className="symbol">{pos.symbol}</span>
          <span className="total-qty">{pos.total_quantity}股</span>
          <span className={`total-pnl ${pos.total_unrealized_pnl >= 0 ? 'positive' : 'negative'}`}>
            {pos.total_unrealized_pnl >= 0 ? '+' : ''}${pos.total_unrealized_pnl.toFixed(2)}
          </span>
          <span className="concentration">
            占比: {(pos.concentration_pct * 100).toFixed(1)}%
          </span>
        </div>
        
        <div className="sources">
          {pos.sources.map((source, i) => (
            <div key={i} className="source-row">
              <span className="source-name">{source.strategy_name}</span>
              <span className="source-qty">{source.quantity}股</span>
              <span className={`source-pnl ${source.pnl >= 0 ? 'positive' : 'negative'}`}>
                {source.pnl >= 0 ? '+' : ''}${source.pnl.toFixed(2)}
              </span>
            </div>
          ))}
        </div>
      </div>
    ))}
  </div>
);
```

**验收标准**:
- [ ] 按策略分组显示正确
- [ ] 按股票汇总显示正确
- [ ] 同股票不同策略分开显示
- [ ] 集中度警告正确

---

## Sprint 7 完成检查清单

### Part A: TradingView集成
- [ ] TradingViewChart.tsx 图表加载正常
- [ ] ChartToolbar.tsx 工具栏功能正常
- [ ] SignalOverlay.tsx 信号覆盖层正常
- [ ] 时间周期切换正常
- [ ] 技术指标可添加

### Part B: 手动交易
- [ ] manual_trade_service.py 服务完整
- [ ] manual_trade.py API可调用
- [ ] QuickTradePanel.tsx 交易面板正常
- [ ] 市价/限价单功能正常
- [ ] PDT规则检查正常

### Part C: 分策略持仓
- [ ] position.py Schema完整
- [ ] position_service.py 服务完整
- [ ] positions.py API可调用
- [ ] PositionPanel.tsx 持仓面板正常
- [ ] 按策略/按股票视图切换正常
- [ ] 集中度警告正常

---

## 新增API端点

```
# 手动交易
POST   /api/v1/manual-trade/order         - 下单
DELETE /api/v1/manual-trade/order/{id}    - 取消订单
GET    /api/v1/manual-trade/orders        - 获取订单列表
GET    /api/v1/manual-trade/quote/{symbol} - 获取实时报价

# 持仓管理
GET    /api/v1/positions/summary          - 获取持仓汇总
GET    /api/v1/positions/strategy/{id}    - 获取策略持仓
GET    /api/v1/positions/symbol/{symbol}  - 获取股票持仓详情
```

---

## 新增文件清单

### 后端
```
backend/app/
├── schemas/
│   └── position.py        🆕
├── services/
│   ├── manual_trade_service.py  🆕
│   └── position_service.py      🆕
└── api/v1/
    ├── manual_trade.py    🆕
    └── positions.py       🆕
```

### 前端
```
frontend/src/
├── types/
│   └── position.ts        🆕
└── components/
    ├── Chart/
    │   ├── TradingViewChart.tsx  🆕
    │   ├── ChartToolbar.tsx      🆕
    │   └── SignalOverlay.tsx     🆕
    ├── Trade/
    │   └── QuickTradePanel.tsx   🆕
    └── Position/
        └── PositionPanel.tsx     🆕
```

---

## 下一步

完成后进入 **Sprint 8: 日内交易完整UI**

---

**预计完成时间**: 7天
