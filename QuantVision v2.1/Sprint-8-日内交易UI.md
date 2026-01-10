# Sprint 8: 日内交易完整UI (5天)

> **文档版本**: 1.0  
> **预计时长**: 5天  
> **前置依赖**: Sprint 7 完成  
> **PRD参考**: 4.18.0 盘前扫描器, 4.18.1 日内交易专用视图  
> **交付物**: 盘前扫描器、日内交易专用视图、止盈止损面板、时间止损

---

## 目标

实现完整的日内交易功能，包括：
1. 盘前扫描器 (Pre-market Scanner)
2. 日内交易专用视图 (简化版三栏布局)
3. 止盈止损设置面板
4. 时间止损 (收盘前自动平仓)

---

## Part A: 盘前扫描器 (2天)

### Task 8.1: 盘前扫描Schema (后端)

**文件**: `backend/app/schemas/pre_market.py`

```python
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date

class PreMarketScanFilter(BaseModel):
    """盘前扫描筛选条件"""
    min_gap: float = 0.02           # 最小Gap (默认2%)
    min_premarket_volume: float = 2.0  # 盘前成交量倍数 (默认2倍日均)
    min_volatility: float = 0.03    # 最小昨日波动率 (默认3%)
    min_liquidity: float = 5000000  # 最小流动性 (默认$5M/日)
    has_news: Optional[bool] = None # 是否有新闻
    is_earnings_day: Optional[bool] = None  # 是否财报日

class PreMarketStock(BaseModel):
    """盘前扫描股票"""
    symbol: str
    name: str
    
    # 盘前数据
    gap: float                    # 开盘跳空 (%)
    gap_direction: str            # 'up' | 'down'
    premarket_price: float        # 盘前价格
    premarket_volume: int         # 盘前成交量
    premarket_volume_ratio: float # 相对日均量倍数
    
    # 昨日数据
    prev_close: float
    prev_volume: int
    volatility: float             # 昨日波动率 (ATR%)
    
    # 流动性
    avg_daily_volume: int
    avg_daily_value: float        # 日均成交额
    
    # 新闻/事件
    has_news: bool
    news_headline: Optional[str] = None
    is_earnings_day: bool
    
    # 评分
    score: float                  # 策略评分 0-100
    score_breakdown: dict         # 评分明细

class PreMarketScanResult(BaseModel):
    """盘前扫描结果"""
    scan_time: datetime
    strategy_id: str
    strategy_name: str
    
    filters_applied: PreMarketScanFilter
    total_matched: int
    stocks: list[PreMarketStock]
    
    # AI建议
    ai_suggestion: Optional[str] = None

class IntradayWatchlist(BaseModel):
    """日内交易监控列表"""
    watchlist_id: str
    user_id: str
    strategy_id: str
    date: date
    symbols: list[str]
    created_at: datetime
    is_confirmed: bool = False
```

---

### Task 8.2: 盘前扫描服务 (后端)

**文件**: `backend/app/services/pre_market_service.py`

```python
from datetime import datetime, date
from typing import Optional
from app.schemas.pre_market import (
    PreMarketScanFilter, PreMarketStock, PreMarketScanResult,
    IntradayWatchlist
)
import uuid

class PreMarketService:
    """盘前扫描服务"""
    
    def __init__(self, db_session, market_data_service, news_service):
        self.db = db_session
        self.market_data = market_data_service
        self.news = news_service
    
    async def scan(
        self,
        strategy_id: str,
        filters: PreMarketScanFilter
    ) -> PreMarketScanResult:
        """执行盘前扫描"""
        
        # 1. 获取策略的候选股票池
        universe = await self._get_strategy_universe(strategy_id)
        
        # 2. 获取盘前数据
        premarket_data = await self.market_data.get_premarket_quotes(
            [s.symbol for s in universe]
        )
        
        # 3. 获取昨日数据
        prev_day_data = await self.market_data.get_previous_day_data(
            [s.symbol for s in universe]
        )
        
        # 4. 获取新闻数据
        news_data = await self.news.get_today_news(
            [s.symbol for s in universe]
        )
        
        # 5. 筛选和评分
        matched_stocks = []
        for symbol in universe:
            pm = premarket_data.get(symbol)
            prev = prev_day_data.get(symbol)
            news = news_data.get(symbol)
            
            if not pm or not prev:
                continue
            
            # 计算指标
            gap = (pm.price - prev.close) / prev.close
            vol_ratio = pm.volume / prev.avg_volume if prev.avg_volume > 0 else 0
            volatility = prev.atr / prev.close if prev.close > 0 else 0
            
            # 应用筛选条件
            if abs(gap) < filters.min_gap:
                continue
            if vol_ratio < filters.min_premarket_volume:
                continue
            if volatility < filters.min_volatility:
                continue
            if prev.avg_daily_value < filters.min_liquidity:
                continue
            if filters.has_news is not None and bool(news) != filters.has_news:
                continue
            
            # 计算评分
            score, breakdown = self._calculate_score(
                gap, vol_ratio, volatility, bool(news)
            )
            
            stock = PreMarketStock(
                symbol=symbol,
                name=universe[symbol].name,
                gap=gap,
                gap_direction='up' if gap > 0 else 'down',
                premarket_price=pm.price,
                premarket_volume=pm.volume,
                premarket_volume_ratio=vol_ratio,
                prev_close=prev.close,
                prev_volume=prev.volume,
                volatility=volatility,
                avg_daily_volume=prev.avg_volume,
                avg_daily_value=prev.avg_daily_value,
                has_news=bool(news),
                news_headline=news[0].headline if news else None,
                is_earnings_day=prev.is_earnings_day,
                score=score,
                score_breakdown=breakdown
            )
            
            matched_stocks.append(stock)
        
        # 6. 按评分排序
        matched_stocks.sort(key=lambda x: x.score, reverse=True)
        
        # 7. 生成AI建议
        ai_suggestion = self._generate_ai_suggestion(matched_stocks[:10])
        
        return PreMarketScanResult(
            scan_time=datetime.now(),
            strategy_id=strategy_id,
            strategy_name=await self._get_strategy_name(strategy_id),
            filters_applied=filters,
            total_matched=len(matched_stocks),
            stocks=matched_stocks,
            ai_suggestion=ai_suggestion
        )
    
    def _calculate_score(
        self,
        gap: float,
        vol_ratio: float,
        volatility: float,
        has_news: bool
    ) -> tuple[float, dict]:
        """
        计算策略评分 (PRD 4.18.0)
        
        评分 = w1×Gap得分 + w2×成交量得分 + w3×波动率得分 + w4×新闻加分
        """
        
        # Gap得分: |Gap%| × 10 (上限50分)
        gap_score = min(abs(gap) * 100 * 10, 50)
        
        # 成交量得分: min(盘前量%, 500) / 10 (上限50分)
        volume_score = min(vol_ratio * 100, 500) / 10
        
        # 波动率得分: 波动率% × 5 (上限25分)
        volatility_score = min(volatility * 100 * 5, 25)
        
        # 新闻加分: 有新闻+10分
        news_score = 10 if has_news else 0
        
        # 加权计算
        total = (
            gap_score * 0.3 +
            volume_score * 0.3 +
            volatility_score * 0.2 +
            news_score
        )
        
        breakdown = {
            'gap': round(gap_score, 1),
            'volume': round(volume_score, 1),
            'volatility': round(volatility_score, 1),
            'news': news_score,
            'weights': {'gap': 0.3, 'volume': 0.3, 'volatility': 0.2, 'news': 1.0}
        }
        
        return round(total, 1), breakdown
    
    def _generate_ai_suggestion(self, top_stocks: list[PreMarketStock]) -> str:
        """生成AI建议"""
        if not top_stocks:
            return "暂无符合条件的股票"
        
        news_stocks = [s for s in top_stocks if s.has_news]
        high_gap_stocks = [s for s in top_stocks if abs(s.gap) > 0.03]
        
        suggestions = []
        
        if news_stocks:
            symbols = ', '.join(s.symbol for s in news_stocks[:3])
            suggestions.append(f"{symbols} 今日有重大新闻催化，建议重点关注")
        
        if high_gap_stocks:
            symbols = ', '.join(s.symbol for s in high_gap_stocks[:2])
            suggestions.append(f"{symbols} 跳空幅度较大，注意风险控制")
        
        return '；'.join(suggestions) if suggestions else "今日候选股票波动正常"
    
    async def create_watchlist(
        self,
        user_id: str,
        strategy_id: str,
        symbols: list[str]
    ) -> IntradayWatchlist:
        """创建今日监控列表"""
        
        watchlist = IntradayWatchlist(
            watchlist_id=str(uuid.uuid4()),
            user_id=user_id,
            strategy_id=strategy_id,
            date=date.today(),
            symbols=symbols,
            created_at=datetime.now(),
            is_confirmed=True
        )
        
        await self._save_watchlist(watchlist)
        return watchlist
    
    async def get_today_watchlist(
        self,
        user_id: str,
        strategy_id: str
    ) -> Optional[IntradayWatchlist]:
        """获取今日监控列表"""
        return await self._get_watchlist(user_id, strategy_id, date.today())
```

---

### Task 8.3: 盘前扫描API (后端)

**文件**: `backend/app/api/v1/pre_market.py`

```python
from fastapi import APIRouter, Depends, Query
from typing import Optional
from app.services.pre_market_service import PreMarketService
from app.schemas.pre_market import (
    PreMarketScanFilter, PreMarketScanResult, IntradayWatchlist
)
from app.core.deps import get_current_user, get_pre_market_service

router = APIRouter(prefix="/intraday", tags=["Intraday Trading"])

@router.get("/pre-market-scanner", response_model=PreMarketScanResult)
async def scan_pre_market(
    strategy_id: str,
    min_gap: float = Query(0.02, description="最小Gap"),
    min_premarket_volume: float = Query(2.0, description="盘前成交量倍数"),
    min_volatility: float = Query(0.03, description="最小波动率"),
    min_liquidity: float = Query(5000000, description="最小流动性"),
    has_news: Optional[bool] = Query(None, description="是否有新闻"),
    is_earnings_day: Optional[bool] = Query(None, description="是否财报日"),
    current_user = Depends(get_current_user),
    service: PreMarketService = Depends(get_pre_market_service)
):
    """
    盘前扫描
    
    可用时间: 美东时间 4:00-9:30 AM
    刷新频率: 建议每5分钟刷新一次
    """
    filters = PreMarketScanFilter(
        min_gap=min_gap,
        min_premarket_volume=min_premarket_volume,
        min_volatility=min_volatility,
        min_liquidity=min_liquidity,
        has_news=has_news,
        is_earnings_day=is_earnings_day
    )
    
    return await service.scan(strategy_id, filters)

@router.post("/watchlist", response_model=IntradayWatchlist)
async def create_watchlist(
    strategy_id: str,
    symbols: list[str],
    current_user = Depends(get_current_user),
    service: PreMarketService = Depends(get_pre_market_service)
):
    """
    确认今日监控列表
    
    建议: 5-15只股票，不超过20只
    """
    if len(symbols) > 20:
        symbols = symbols[:20]
    
    return await service.create_watchlist(
        user_id=current_user.id,
        strategy_id=strategy_id,
        symbols=symbols
    )

@router.get("/watchlist", response_model=Optional[IntradayWatchlist])
async def get_today_watchlist(
    strategy_id: str,
    current_user = Depends(get_current_user),
    service: PreMarketService = Depends(get_pre_market_service)
):
    """获取今日监控列表"""
    return await service.get_today_watchlist(
        user_id=current_user.id,
        strategy_id=strategy_id
    )
```

---

### Task 8.4: 盘前扫描器组件 (前端)

**文件**: `frontend/src/components/Intraday/PreMarketScanner.tsx`

```tsx
import React, { useState, useEffect } from 'react';
import { PreMarketScanResult, PreMarketStock, PreMarketScanFilter } from '@/types/pre_market';

interface Props {
  strategyId: string;
  onConfirmWatchlist: (symbols: string[]) => void;
}

export const PreMarketScanner: React.FC<Props> = ({ strategyId, onConfirmWatchlist }) => {
  const [scanResult, setScanResult] = useState<PreMarketScanResult | null>(null);
  const [filters, setFilters] = useState<PreMarketScanFilter>({
    minGap: 0.02,
    minPremarketVolume: 2.0,
    minVolatility: 0.03,
    minLiquidity: 5000000,
    hasNews: null,
    isEarningsDay: null
  });
  const [selectedSymbols, setSelectedSymbols] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(false);
  
  // 执行扫描
  const handleScan = async () => {
    setLoading(true);
    try {
      const result = await api.preMarket.scan(strategyId, filters);
      setScanResult(result);
      
      // 默认选中高评分股票
      const topSymbols = result.stocks
        .filter(s => s.score >= 70)
        .map(s => s.symbol);
      setSelectedSymbols(new Set(topSymbols));
    } finally {
      setLoading(false);
    }
  };
  
  // 切换选中
  const toggleSymbol = (symbol: string) => {
    const newSet = new Set(selectedSymbols);
    if (newSet.has(symbol)) {
      newSet.delete(symbol);
    } else {
      newSet.add(symbol);
    }
    setSelectedSymbols(newSet);
  };
  
  // 全选/取消全选
  const toggleAll = () => {
    if (selectedSymbols.size === scanResult?.stocks.length) {
      setSelectedSymbols(new Set());
    } else {
      setSelectedSymbols(new Set(scanResult?.stocks.map(s => s.symbol)));
    }
  };
  
  // 确认监控列表
  const handleConfirm = () => {
    onConfirmWatchlist(Array.from(selectedSymbols));
  };
  
  return (
    <div className="pre-market-scanner">
      {/* 头部 */}
      <div className="scanner-header">
        <div className="scanner-title">
          <span className="icon">⏰</span>
          <h2>盘前扫描器</h2>
          <span className="time">{new Date().toLocaleTimeString()} EST</span>
        </div>
      </div>
      
      {/* 筛选条件 */}
      <div className="scanner-filters">
        <div className="filter-row">
          <label>
            <input
              type="checkbox"
              checked={filters.minGap > 0}
              onChange={e => setFilters({
                ...filters,
                minGap: e.target.checked ? 0.02 : 0
              })}
            />
            Gap &gt; 
            <select 
              value={filters.minGap * 100}
              onChange={e => setFilters({
                ...filters,
                minGap: parseFloat(e.target.value) / 100
              })}
            >
              <option value="1">1%</option>
              <option value="2">2%</option>
              <option value="3">3%</option>
              <option value="5">5%</option>
            </select>
          </label>
          
          <label>
            <input
              type="checkbox"
              checked={filters.minPremarketVolume > 0}
              onChange={e => setFilters({
                ...filters,
                minPremarketVolume: e.target.checked ? 2.0 : 0
              })}
            />
            盘前成交量 &gt;
            <select
              value={filters.minPremarketVolume * 100}
              onChange={e => setFilters({
                ...filters,
                minPremarketVolume: parseFloat(e.target.value) / 100
              })}
            >
              <option value="100">100%</option>
              <option value="200">200%</option>
              <option value="300">300%</option>
              <option value="500">500%</option>
            </select>
          </label>
        </div>
        
        <div className="filter-row">
          <label>
            <input
              type="checkbox"
              checked={filters.hasNews === true}
              onChange={e => setFilters({
                ...filters,
                hasNews: e.target.checked ? true : null
              })}
            />
            有重大新闻
          </label>
          
          <label>
            <input
              type="checkbox"
              checked={filters.isEarningsDay === true}
              onChange={e => setFilters({
                ...filters,
                isEarningsDay: e.target.checked ? true : null
              })}
            />
            财报日
          </label>
        </div>
        
        <div className="filter-actions">
          <button className="btn-scan" onClick={handleScan} disabled={loading}>
            {loading ? '扫描中...' : '应用筛选'}
          </button>
          <button 
            className="btn-reset"
            onClick={() => setFilters({
              minGap: 0.02,
              minPremarketVolume: 2.0,
              minVolatility: 0.03,
              minLiquidity: 5000000,
              hasNews: null,
              isEarningsDay: null
            })}
          >
            恢复默认
          </button>
          
          {scanResult && (
            <span className="match-count">
              符合条件: {scanResult.totalMatched} 只
            </span>
          )}
        </div>
      </div>
      
      {/* 候选股票列表 */}
      {scanResult && (
        <div className="scanner-results">
          <div className="results-header">
            <label className="select-all">
              <input
                type="checkbox"
                checked={selectedSymbols.size === scanResult.stocks.length}
                onChange={toggleAll}
              />
              全选
            </label>
          </div>
          
          <table className="scanner-table">
            <thead>
              <tr>
                <th></th>
                <th>股票</th>
                <th>Gap</th>
                <th>盘前量</th>
                <th>昨日波动</th>
                <th>流动性</th>
                <th>新闻</th>
                <th>评分</th>
              </tr>
            </thead>
            <tbody>
              {scanResult.stocks.map(stock => (
                <StockRow
                  key={stock.symbol}
                  stock={stock}
                  selected={selectedSymbols.has(stock.symbol)}
                  onToggle={() => toggleSymbol(stock.symbol)}
                />
              ))}
            </tbody>
          </table>
          
          {/* AI建议 */}
          {scanResult.aiSuggestion && (
            <div className="ai-suggestion">
              <span className="icon">💡</span>
              <span className="text">{scanResult.aiSuggestion}</span>
            </div>
          )}
        </div>
      )}
      
      {/* 底部操作 */}
      <div className="scanner-footer">
        <div className="selected-count">
          已选择: {selectedSymbols.size} 只
          <span className="suggestion">
            (建议: 5-15只，不超过20只)
          </span>
        </div>
        
        <button
          className="btn-confirm"
          onClick={handleConfirm}
          disabled={selectedSymbols.size === 0}
        >
          确认监控列表，进入交易界面 →
        </button>
      </div>
    </div>
  );
};

const StockRow: React.FC<{
  stock: PreMarketStock;
  selected: boolean;
  onToggle: () => void;
}> = ({ stock, selected, onToggle }) => {
  const gapClass = stock.gapDirection === 'up' ? 'positive' : 'negative';
  const scoreClass = stock.score >= 80 ? 'high' : stock.score >= 60 ? 'medium' : 'low';
  
  return (
    <tr className={selected ? 'selected' : ''}>
      <td>
        <input
          type="checkbox"
          checked={selected}
          onChange={onToggle}
        />
      </td>
      <td className="symbol-cell">
        <span className="symbol">{stock.symbol}</span>
        <span className="name">{stock.name}</span>
      </td>
      <td className={`gap-cell ${gapClass}`}>
        {stock.gapDirection === 'up' ? '+' : ''}{(stock.gap * 100).toFixed(1)}%
      </td>
      <td>{stock.premarketVolumeRatio.toFixed(0)}%</td>
      <td>{(stock.volatility * 100).toFixed(1)}%</td>
      <td>${(stock.avgDailyValue / 1000000).toFixed(0)}M</td>
      <td>
        {stock.hasNews && <span className="news-icon" title={stock.newsHeadline}>📰</span>}
        {stock.isEarningsDay && <span className="earnings-icon">📊</span>}
      </td>
      <td className={`score-cell ${scoreClass}`}>
        {'⭐'.repeat(Math.ceil(stock.score / 20))} {stock.score.toFixed(0)}
      </td>
    </tr>
  );
};
```

**验收标准**:
- [ ] 筛选条件可调整
- [ ] 股票列表显示正确
- [ ] 评分计算正确
- [ ] 可选择多个股票
- [ ] 确认后跳转到交易界面

---

## Part B: 日内交易专用视图 (2天)

### Task 8.5: 日内交易布局

**文件**: `frontend/src/pages/IntradayTradingPage.tsx`

```tsx
import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { TradingViewChart } from '@/components/Chart/TradingViewChart';
import { SimplifiedWatchlist } from '@/components/Intraday/SimplifiedWatchlist';
import { QuickTradePanel } from '@/components/Trade/QuickTradePanel';
import { IntradayTradeLog } from '@/components/Intraday/IntradayTradeLog';
import { StopLossPanel } from '@/components/Intraday/StopLossPanel';
import { PDTWarning } from '@/components/PDT/PDTWarning';

export const IntradayTradingPage: React.FC = () => {
  const { strategyId } = useParams<{ strategyId: string }>();
  const [watchlist, setWatchlist] = useState<string[]>([]);
  const [currentSymbol, setCurrentSymbol] = useState<string>('');
  const [chartInterval, setChartInterval] = useState<'1' | '5'>('1');
  const [position, setPosition] = useState<any>(null);
  const [pdtStatus, setPdtStatus] = useState<any>(null);
  const [todayTrades, setTodayTrades] = useState<any[]>([]);
  
  // 加载今日监控列表
  useEffect(() => {
    loadWatchlist();
    loadPDTStatus();
    loadTodayTrades();
  }, [strategyId]);
  
  const loadWatchlist = async () => {
    const result = await api.intraday.getWatchlist(strategyId);
    if (result) {
      setWatchlist(result.symbols);
      setCurrentSymbol(result.symbols[0]);
    }
  };
  
  return (
    <div className="intraday-trading-page">
      {/* 顶部状态栏 */}
      <header className="intraday-header">
        <div className="header-left">
          <span className="icon">⚡</span>
          <span className="title">日内交易监控</span>
          <span className="strategy-name">{strategyId}</span>
          <span className="live-badge">🔴 LIVE</span>
        </div>
        <div className="header-right">
          <span className="pdt-status">
            PDT: {pdtStatus?.remaining}/{pdtStatus?.max}
          </span>
          <span className="account-balance">
            账户: ${pdtStatus?.balance?.toLocaleString()}
          </span>
          <span className="today-pnl positive">
            今日: +${(385).toLocaleString()}
          </span>
        </div>
      </header>
      
      {/* 主体三栏布局 */}
      <main className="intraday-main">
        {/* 左侧: 简化监控列表 (100px) */}
        <aside className="intraday-watchlist">
          <SimplifiedWatchlist
            symbols={watchlist}
            currentSymbol={currentSymbol}
            onSelect={setCurrentSymbol}
            signals={/* 实时信号数据 */}
          />
        </aside>
        
        {/* 中间: 图表区域 */}
        <section className="intraday-charts">
          {/* 1分钟主图 */}
          <div className="main-chart">
            <div className="chart-header">
              <span className="symbol">{currentSymbol}</span>
              <span className="price">$142.52</span>
              <span className="change positive">+$0.15 (+0.11%)</span>
              <span className="atr">ATR: $0.68</span>
              
              <div className="interval-buttons">
                <button 
                  className={chartInterval === '1' ? 'active' : ''}
                  onClick={() => setChartInterval('1')}
                >
                  1分钟
                </button>
                <button
                  className={chartInterval === '5' ? 'active' : ''}
                  onClick={() => setChartInterval('5')}
                >
                  5分钟
                </button>
              </div>
            </div>
            
            <TradingViewChart
              symbol={currentSymbol}
              interval={chartInterval}
              height={400}
            />
          </div>
          
          {/* 5分钟副图 (宏观趋势) */}
          <div className="secondary-chart">
            <div className="chart-header">
              <span>5分钟宏观趋势</span>
              <span className="trend-indicator positive">上升 ▲</span>
              <span className="market-info">
                VIX: 18.2 | SPY: +0.3% | QQQ: +0.5%
              </span>
            </div>
            <TradingViewChart
              symbol={currentSymbol}
              interval="5"
              height={150}
            />
          </div>
          
          {/* 今日交易记录 */}
          <div className="trade-log">
            <IntradayTradeLog trades={todayTrades} />
          </div>
        </section>
        
        {/* 右侧: 快速交易 (320px) */}
        <aside className="intraday-trade-panel">
          {/* 快速交易 */}
          <QuickTradePanel
            symbol={currentSymbol}
            price={142.52}
            position={position}
            onBuy={handleBuy}
            onSell={handleSell}
          />
          
          {/* 止盈止损设置 */}
          {position && (
            <StopLossPanel
              position={position}
              onUpdate={handleUpdateStopLoss}
            />
          )}
          
          {/* PDT警告 */}
          {pdtStatus?.remaining <= 1 && (
            <PDTWarning
              level={pdtStatus.remaining === 0 ? 'danger' : 'warning'}
              remaining={pdtStatus.remaining}
            />
          )}
          
          {/* 快捷操作 */}
          <div className="quick-actions">
            <button className="btn-danger" onClick={handleCloseAll}>
              🛑 一键平仓
            </button>
            <button className="btn-secondary" onClick={handlePauseStrategy}>
              ⏸️ 暂停策略
            </button>
          </div>
        </aside>
      </main>
    </div>
  );
};
```

---

### Task 8.6: 简化监控列表组件

**文件**: `frontend/src/components/Intraday/SimplifiedWatchlist.tsx`

```tsx
import React from 'react';

interface Props {
  symbols: string[];
  currentSymbol: string;
  onSelect: (symbol: string) => void;
  signals: Record<string, SignalStatus>;
}

type SignalStatus = {
  type: 'buy' | 'sell' | 'none';
  change: number;
  changePct: number;
};

export const SimplifiedWatchlist: React.FC<Props> = ({
  symbols,
  currentSymbol,
  onSelect,
  signals
}) => {
  return (
    <div className="simplified-watchlist">
      <div className="watchlist-header">今日监控</div>
      
      <div className="watchlist-items">
        {symbols.map(symbol => {
          const signal = signals[symbol];
          const isActive = symbol === currentSymbol;
          const changeClass = signal?.changePct >= 0 ? 'positive' : 'negative';
          
          return (
            <div
              key={symbol}
              className={`watchlist-item ${isActive ? 'active' : ''}`}
              onClick={() => onSelect(symbol)}
            >
              <div className="item-symbol">
                {symbol}
                {signal?.type === 'buy' && <span className="signal buy">🟢</span>}
                {signal?.type === 'sell' && <span className="signal sell">🟠</span>}
              </div>
              <div className={`item-change ${changeClass}`}>
                {signal?.changePct >= 0 ? '+' : ''}{signal?.changePct?.toFixed(2)}%
              </div>
            </div>
          );
        })}
      </div>
      
      <button className="btn-add-symbol">+ 添加股票</button>
    </div>
  );
};
```

**特点 (vs 完整信号雷达)**:
- 宽度仅100px (vs 280px)
- 无搜索框
- 无股票池选择
- 无状态分布统计
- 仅显示今日选定股票

---

### Task 8.7: 止盈止损面板

**文件**: `frontend/src/components/Intraday/StopLossPanel.tsx`

```tsx
import React, { useState, useEffect } from 'react';

interface Position {
  symbol: string;
  quantity: number;
  entryPrice: number;
  currentPrice: number;
  pnl: number;
  pnlPct: number;
}

interface Props {
  position: Position;
  onUpdate: (config: StopLossConfig) => void;
}

interface StopLossConfig {
  stopLossType: 'atr' | 'fixed' | 'percentage' | 'technical';
  stopLossValue: number;
  takeProfitType: 'atr' | 'fixed' | 'percentage' | 'technical';
  takeProfitValue: number;
  timeStopEnabled: boolean;
  timeStopTime: string;  // HH:mm format
  trailingStopEnabled: boolean;
  trailingTriggerPct: number;
  trailingDistancePct: number;
}

const DEFAULT_CONFIG: StopLossConfig = {
  stopLossType: 'atr',
  stopLossValue: 1.5,
  takeProfitType: 'atr',
  takeProfitValue: 2.5,
  timeStopEnabled: true,
  timeStopTime: '15:55',
  trailingStopEnabled: false,
  trailingTriggerPct: 0.5,
  trailingDistancePct: 0.3,
};

export const StopLossPanel: React.FC<Props> = ({ position, onUpdate }) => {
  const [config, setConfig] = useState<StopLossConfig>(DEFAULT_CONFIG);
  const [atr, setAtr] = useState(0.68);  // 当前ATR
  
  // 计算止损止盈价格
  const stopLossPrice = calculatePrice('stop', config, position, atr);
  const takeProfitPrice = calculatePrice('profit', config, position, atr);
  const riskRewardRatio = (takeProfitPrice - position.entryPrice) / 
                          (position.entryPrice - stopLossPrice);
  
  const handleUpdate = (updates: Partial<StopLossConfig>) => {
    const newConfig = { ...config, ...updates };
    setConfig(newConfig);
    onUpdate(newConfig);
  };
  
  return (
    <div className="stop-loss-panel">
      <div className="panel-header">
        <span className="icon">🛡️</span>
        <span className="title">止盈止损设置</span>
      </div>
      
      {/* 当前持仓信息 */}
      <div className="position-info">
        <span>持仓: {position.symbol} {position.quantity}股 @${position.entryPrice.toFixed(2)}</span>
        <span className={position.pnl >= 0 ? 'positive' : 'negative'}>
          浮盈: {position.pnl >= 0 ? '+' : ''}${position.pnl.toFixed(2)} 
          ({position.pnlPct.toFixed(2)}%)
        </span>
      </div>
      
      {/* 止损设置 */}
      <div className="config-section">
        <h4>🛑 止损</h4>
        
        <div className="type-selector">
          <label>方式:</label>
          <select
            value={config.stopLossType}
            onChange={e => handleUpdate({ stopLossType: e.target.value as any })}
          >
            <option value="atr">ATR动态</option>
            <option value="fixed">固定价格</option>
            <option value="percentage">百分比</option>
            <option value="technical">技术位</option>
          </select>
        </div>
        
        {config.stopLossType === 'atr' && (
          <div className="atr-config">
            <label>ATR倍数:</label>
            <select
              value={config.stopLossValue}
              onChange={e => handleUpdate({ stopLossValue: parseFloat(e.target.value) })}
            >
              <option value="1.0">1.0x</option>
              <option value="1.5">1.5x</option>
              <option value="2.0">2.0x</option>
              <option value="2.5">2.5x</option>
            </select>
            <span className="atr-info">当前ATR: ${atr.toFixed(2)}</span>
          </div>
        )}
        
        <div className="calculated-price">
          <label>止损价:</label>
          <input
            type="number"
            value={stopLossPrice.toFixed(2)}
            onChange={e => handleUpdate({
              stopLossType: 'fixed',
              stopLossValue: parseFloat(e.target.value)
            })}
            step={0.01}
          />
          <span className="support-hint">💡 支撑位: $141.00</span>
        </div>
      </div>
      
      {/* 止盈设置 */}
      <div className="config-section">
        <h4>🎯 止盈</h4>
        
        <div className="type-selector">
          <label>方式:</label>
          <select
            value={config.takeProfitType}
            onChange={e => handleUpdate({ takeProfitType: e.target.value as any })}
          >
            <option value="atr">ATR动态</option>
            <option value="fixed">固定价格</option>
            <option value="percentage">百分比</option>
            <option value="technical">技术位</option>
          </select>
        </div>
        
        {config.takeProfitType === 'atr' && (
          <div className="atr-config">
            <label>ATR倍数:</label>
            <select
              value={config.takeProfitValue}
              onChange={e => handleUpdate({ takeProfitValue: parseFloat(e.target.value) })}
            >
              <option value="1.5">1.5x</option>
              <option value="2.0">2.0x</option>
              <option value="2.5">2.5x</option>
              <option value="3.0">3.0x</option>
            </select>
            <span className="ratio-info">盈亏比: 1:{riskRewardRatio.toFixed(1)}</span>
          </div>
        )}
        
        <div className="calculated-price">
          <label>止盈价:</label>
          <input
            type="number"
            value={takeProfitPrice.toFixed(2)}
            onChange={e => handleUpdate({
              takeProfitType: 'fixed',
              takeProfitValue: parseFloat(e.target.value)
            })}
            step={0.01}
          />
          <span className="resistance-hint">💡 阻力位: $143.80</span>
        </div>
      </div>
      
      {/* 时间止损 (日内专属) */}
      <div className="config-section time-stop">
        <h4>⏰ 时间止损</h4>
        
        <label className="toggle">
          <input
            type="checkbox"
            checked={config.timeStopEnabled}
            onChange={e => handleUpdate({ timeStopEnabled: e.target.checked })}
          />
          启用收盘前自动平仓
        </label>
        
        {config.timeStopEnabled && (
          <div className="time-config">
            <label>平仓时间:</label>
            <select
              value={config.timeStopTime}
              onChange={e => handleUpdate({ timeStopTime: e.target.value })}
            >
              <option value="15:45">15:45 (收盘前15分钟)</option>
              <option value="15:50">15:50 (收盘前10分钟)</option>
              <option value="15:55">15:55 (收盘前5分钟)</option>
            </select>
            <p className="warning">⚠️ 到达时间后自动市价平仓</p>
          </div>
        )}
      </div>
      
      {/* 移动止损 */}
      <div className="config-section trailing-stop">
        <h4>📈 移动止损 (可选)</h4>
        
        <label className="toggle">
          <input
            type="checkbox"
            checked={config.trailingStopEnabled}
            onChange={e => handleUpdate({ trailingStopEnabled: e.target.checked })}
          />
          启用移动止损 (Trailing Stop)
        </label>
        
        {config.trailingStopEnabled && (
          <div className="trailing-config">
            <div className="config-row">
              <label>触发条件: 盈利达</label>
              <input
                type="number"
                value={config.trailingTriggerPct}
                onChange={e => handleUpdate({ 
                  trailingTriggerPct: parseFloat(e.target.value) 
                })}
                step={0.1}
              />
              <span>%</span>
            </div>
            <div className="config-row">
              <label>跟踪距离:</label>
              <input
                type="number"
                value={config.trailingDistancePct}
                onChange={e => handleUpdate({
                  trailingDistancePct: parseFloat(e.target.value)
                })}
                step={0.1}
              />
              <span>%</span>
            </div>
          </div>
        )}
      </div>
      
      {/* 应用按钮 */}
      <button className="btn-apply" onClick={() => onUpdate(config)}>
        应用止盈止损设置
      </button>
    </div>
  );
};

function calculatePrice(
  type: 'stop' | 'profit',
  config: StopLossConfig,
  position: Position,
  atr: number
): number {
  const isStop = type === 'stop';
  const configType = isStop ? config.stopLossType : config.takeProfitType;
  const configValue = isStop ? config.stopLossValue : config.takeProfitValue;
  const direction = isStop ? -1 : 1;
  
  switch (configType) {
    case 'atr':
      return position.entryPrice + direction * configValue * atr;
    case 'percentage':
      return position.entryPrice * (1 + direction * configValue / 100);
    case 'fixed':
      return configValue;
    default:
      return position.entryPrice;
  }
}
```

**验收标准**:
- [ ] ATR动态止损计算正确
- [ ] 固定/百分比止损可设置
- [ ] 时间止损功能正常
- [ ] 移动止损可配置

---

### Task 8.8: 今日交易记录组件

**文件**: `frontend/src/components/Intraday/IntradayTradeLog.tsx`

```tsx
import React from 'react';

interface Trade {
  time: string;
  symbol: string;
  side: 'buy' | 'sell';
  quantity: number;
  price: number;
  stopLoss?: number;
  takeProfit?: number;
  pnl?: number;
  isOpen: boolean;
}

interface Props {
  trades: Trade[];
}

export const IntradayTradeLog: React.FC<Props> = ({ trades }) => {
  return (
    <div className="intraday-trade-log">
      <div className="log-header">
        <span>今日交易记录</span>
        <span className="trade-count">{trades.length} 笔</span>
      </div>
      
      <table className="trade-table">
        <thead>
          <tr>
            <th>时间</th>
            <th>股票</th>
            <th>方向</th>
            <th>数量</th>
            <th>价格</th>
            <th>止损</th>
            <th>止盈</th>
            <th>盈亏</th>
          </tr>
        </thead>
        <tbody>
          {trades.map((trade, i) => (
            <tr key={i} className={trade.isOpen ? 'open' : 'closed'}>
              <td>{trade.time}</td>
              <td>{trade.symbol}</td>
              <td className={trade.side === 'buy' ? 'buy' : 'sell'}>
                {trade.side === 'buy' ? '买入' : '卖出'}
              </td>
              <td>{trade.quantity}</td>
              <td>${trade.price.toFixed(2)}</td>
              <td>{trade.stopLoss ? `$${trade.stopLoss.toFixed(2)}` : '-'}</td>
              <td>{trade.takeProfit ? `$${trade.takeProfit.toFixed(2)}` : '-'}</td>
              <td className={trade.pnl !== undefined ? (trade.pnl >= 0 ? 'positive' : 'negative') : ''}>
                {trade.pnl !== undefined 
                  ? `${trade.pnl >= 0 ? '+' : ''}$${trade.pnl.toFixed(2)}`
                  : (trade.isOpen ? '🔴 持仓中' : '-')
                }
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
```

---

## Part C: 时间止损服务 (1天)

### Task 8.9: 时间止损后台任务 (后端)

**文件**: `backend/app/tasks/time_stop_task.py`

```python
from datetime import datetime, time
from typing import List
import asyncio
from app.services.manual_trade_service import ManualTradeService
from app.services.position_service import PositionService
from app.schemas.alert import AlertType

class TimeStopTask:
    """时间止损定时任务"""
    
    def __init__(
        self,
        trade_service: ManualTradeService,
        position_service: PositionService,
        alert_service
    ):
        self.trade_service = trade_service
        self.position_service = position_service
        self.alert_service = alert_service
    
    async def check_and_execute(self):
        """检查并执行时间止损"""
        
        current_time = datetime.now().time()
        
        # 获取所有启用了时间止损的日内持仓
        positions = await self._get_intraday_positions_with_time_stop()
        
        for pos in positions:
            # 检查是否到达平仓时间
            stop_time = time.fromisoformat(pos.time_stop_config.time)
            
            if current_time >= stop_time:
                await self._execute_time_stop(pos)
    
    async def _execute_time_stop(self, position):
        """执行时间止损"""
        
        try:
            # 市价卖出
            order = await self.trade_service.place_order(
                user_id=position.user_id,
                account_id=position.account_id,
                symbol=position.symbol,
                side='sell',
                order_type='market',
                quantity=position.quantity,
                strategy_id=position.strategy_id,
            )
            
            # 发送通知
            await self.alert_service.create_manual_alert(
                user_id=position.user_id,
                alert_type=AlertType.SYSTEM_ERROR,
                severity='info',
                title=f"⏰ 时间止损触发: {position.symbol}",
                message=f"持仓 {position.symbol} {position.quantity}股已于收盘前自动平仓",
                strategy_id=position.strategy_id,
                details={
                    'symbol': position.symbol,
                    'quantity': position.quantity,
                    'filled_price': order.filled_price,
                    'pnl': (order.filled_price - position.avg_cost) * position.quantity
                }
            )
            
        except Exception as e:
            # 平仓失败，发送紧急通知
            await self.alert_service.create_manual_alert(
                user_id=position.user_id,
                alert_type=AlertType.SYSTEM_ERROR,
                severity='critical',
                title=f"❌ 时间止损失败: {position.symbol}",
                message=f"自动平仓失败，请立即手动处理！错误: {str(e)}",
                strategy_id=position.strategy_id
            )

# 定时任务调度 (每分钟执行)
async def run_time_stop_checker():
    """运行时间止损检查"""
    task = TimeStopTask(
        trade_service=get_trade_service(),
        position_service=get_position_service(),
        alert_service=get_alert_service()
    )
    
    while True:
        # 只在交易时段执行 (9:30-16:00 EST)
        now = datetime.now()
        market_open = now.replace(hour=9, minute=30, second=0)
        market_close = now.replace(hour=16, minute=0, second=0)
        
        if market_open <= now <= market_close:
            await task.check_and_execute()
        
        await asyncio.sleep(60)  # 每分钟检查一次
```

---

## Sprint 8 完成检查清单

### Part A: 盘前扫描器
- [ ] pre_market.py Schema完整
- [ ] pre_market_service.py 服务完整
- [ ] pre_market.py API可调用
- [ ] PreMarketScanner.tsx 扫描器组件正常
- [ ] 评分计算正确
- [ ] AI建议生成正确

### Part B: 日内交易专用视图
- [ ] IntradayTradingPage.tsx 布局正确
- [ ] SimplifiedWatchlist.tsx 简化列表正常
- [ ] StopLossPanel.tsx 止盈止损面板正常
- [ ] IntradayTradeLog.tsx 交易记录正常
- [ ] 双图表布局正常 (1分钟主图+5分钟副图)

### Part C: 时间止损
- [ ] time_stop_task.py 定时任务正常
- [ ] 到达时间自动平仓正常
- [ ] 平仓通知发送正常

### 集成测试
- [ ] 盘前扫描→确认列表→进入交易界面流程顺畅
- [ ] 止盈止损设置生效
- [ ] 时间止损在预定时间触发
- [ ] PDT状态实时显示

---

## 新增API端点

```
# 盘前扫描
GET  /api/v1/intraday/pre-market-scanner    - 盘前扫描
POST /api/v1/intraday/watchlist             - 确认监控列表
GET  /api/v1/intraday/watchlist             - 获取今日监控列表
```

---

## 新增文件清单

### 后端
```
backend/app/
├── schemas/
│   └── pre_market.py      🆕
├── services/
│   └── pre_market_service.py  🆕
├── api/v1/
│   └── pre_market.py      🆕
└── tasks/
    └── time_stop_task.py  🆕
```

### 前端
```
frontend/src/
├── types/
│   └── pre_market.ts      🆕
├── pages/
│   └── IntradayTradingPage.tsx  🆕
└── components/
    └── Intraday/          🆕
        ├── PreMarketScanner.tsx
        ├── SimplifiedWatchlist.tsx
        ├── StopLossPanel.tsx
        └── IntradayTradeLog.tsx
```

---

## 日内交易与长线策略UI对比

| 功能 | 长线策略 | 日内交易 |
|------|----------|----------|
| 左侧面板 | 信号雷达 280px | 简化列表 100px |
| 监控范围 | 500+ 股票 | 5-20 只 |
| 图表时间框架 | 15分/日线 | 1分/5分 |
| 止盈止损 | 可选 | 必选 |
| 时间止损 | 无 | 有 (收盘前平仓) |
| PDT状态 | 隐藏/小字 | 显著显示 |

---

## 下一步

Sprint 0-8 全部完成后，进入 **v2.1.0 发布准备**

---

**预计完成时间**: 5天
