/**
 * 股票搜索组件
 * 支持股票代码和名称搜索，点击选择后更新图表
 */
import { useState, useCallback, useRef, useEffect, memo } from 'react'
import { Input, Spin, Empty, Tag } from 'antd'
import { SearchOutlined, CloseOutlined, StarOutlined, StarFilled } from '@ant-design/icons'
import { searchSymbols, type SymbolInfo } from '@/services/polygonApi'

// 热门股票列表
const HOT_SYMBOLS = [
  { symbol: 'NVDA', name: 'NVIDIA Corporation', type: 'stock' },
  { symbol: 'AAPL', name: 'Apple Inc.', type: 'stock' },
  { symbol: 'TSLA', name: 'Tesla, Inc.', type: 'stock' },
  { symbol: 'MSFT', name: 'Microsoft Corporation', type: 'stock' },
  { symbol: 'GOOGL', name: 'Alphabet Inc.', type: 'stock' },
  { symbol: 'AMZN', name: 'Amazon.com, Inc.', type: 'stock' },
  { symbol: 'META', name: 'Meta Platforms, Inc.', type: 'stock' },
  { symbol: 'SPY', name: 'SPDR S&P 500 ETF', type: 'etf' },
  { symbol: 'QQQ', name: 'Invesco QQQ Trust', type: 'etf' },
] as SymbolInfo[]

// 主要指数
const INDICES = [
  { symbol: 'SPX', name: 'S&P 500 Index', type: 'index' },
  { symbol: 'NDX', name: 'NASDAQ 100 Index', type: 'index' },
  { symbol: 'DJI', name: 'Dow Jones Industrial Average', type: 'index' },
  { symbol: 'VIX', name: 'CBOE Volatility Index', type: 'index' },
] as SymbolInfo[]

interface StockSearchProps {
  value?: string
  onSelect: (symbol: string, info?: SymbolInfo) => void
  placeholder?: string
  className?: string
  showHotList?: boolean
}

function StockSearchComponent({
  value,
  onSelect,
  placeholder = '搜索股票代码或名称 (Ctrl+K)',
  className = '',
  showHotList = true,
}: StockSearchProps) {
  const [searchText, setSearchText] = useState('')
  const [results, setResults] = useState<SymbolInfo[]>([])
  const [loading, setLoading] = useState(false)
  const [showDropdown, setShowDropdown] = useState(false)
  const [favorites, setFavorites] = useState<string[]>(() => {
    const saved = localStorage.getItem('stock-favorites')
    return saved ? JSON.parse(saved) : ['NVDA', 'AAPL', 'TSLA']
  })

  const inputRef = useRef<any>(null)
  const dropdownRef = useRef<HTMLDivElement>(null)
  const searchTimeoutRef = useRef<NodeJS.Timeout>()

  // 保存收藏
  useEffect(() => {
    localStorage.setItem('stock-favorites', JSON.stringify(favorites))
  }, [favorites])

  // 键盘快捷键 Ctrl+K
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault()
        inputRef.current?.focus()
        setShowDropdown(true)
      }
      if (e.key === 'Escape') {
        setShowDropdown(false)
        inputRef.current?.blur()
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [])

  // 点击外部关闭
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setShowDropdown(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  // 搜索处理
  const handleSearch = useCallback(async (text: string) => {
    setSearchText(text)

    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current)
    }

    if (!text.trim()) {
      setResults([])
      return
    }

    // 防抖 300ms
    searchTimeoutRef.current = setTimeout(async () => {
      setLoading(true)
      try {
        const searchResults = await searchSymbols(text.toUpperCase())
        setResults(searchResults.slice(0, 10))
      } catch (error) {
        console.error('Search failed:', error)
        // 本地搜索作为后备
        const localResults = [...HOT_SYMBOLS, ...INDICES].filter(
          s => s.symbol.includes(text.toUpperCase()) ||
               s.name.toLowerCase().includes(text.toLowerCase())
        )
        setResults(localResults)
      } finally {
        setLoading(false)
      }
    }, 300)
  }, [])

  // 选择股票
  const handleSelect = useCallback((info: SymbolInfo) => {
    onSelect(info.symbol, info)
    setSearchText('')
    setShowDropdown(false)
    setResults([])
  }, [onSelect])

  // 切换收藏
  const toggleFavorite = useCallback((symbol: string, e: React.MouseEvent) => {
    e.stopPropagation()
    setFavorites(prev =>
      prev.includes(symbol)
        ? prev.filter(s => s !== symbol)
        : [...prev, symbol]
    )
  }, [])

  // 渲染股票项
  const renderSymbolItem = (info: SymbolInfo, showFavorite = true) => {
    const isFavorite = favorites.includes(info.symbol)
    const isSelected = value === info.symbol

    return (
      <div
        key={info.symbol}
        className={`flex items-center justify-between px-3 py-2 cursor-pointer hover:bg-gray-700/50 transition-colors ${
          isSelected ? 'bg-blue-600/20 border-l-2 border-blue-500' : ''
        }`}
        onClick={() => handleSelect(info)}
      >
        <div className="flex items-center gap-3">
          <span className="font-mono font-medium text-white w-16">{info.symbol}</span>
          <span className="text-gray-400 text-sm truncate max-w-[180px]">{info.name}</span>
        </div>
        <div className="flex items-center gap-2">
          {info.type && (
            <Tag
              className="text-xs border-0"
              color={info.type === 'etf' ? 'blue' : info.type === 'index' ? 'purple' : 'default'}
            >
              {info.type.toUpperCase()}
            </Tag>
          )}
          {showFavorite && (
            <button
              className="text-gray-500 hover:text-yellow-400 transition-colors"
              onClick={(e) => toggleFavorite(info.symbol, e)}
            >
              {isFavorite ? <StarFilled className="text-yellow-400" /> : <StarOutlined />}
            </button>
          )}
        </div>
      </div>
    )
  }

  // 收藏的股票
  const favoriteSymbols = HOT_SYMBOLS.filter(s => favorites.includes(s.symbol))

  return (
    <div className={`relative ${className}`} ref={dropdownRef}>
      <Input
        ref={inputRef}
        placeholder={placeholder}
        prefix={<SearchOutlined className="text-gray-500" />}
        suffix={
          searchText ? (
            <CloseOutlined
              className="text-gray-500 cursor-pointer hover:text-gray-300"
              onClick={() => { setSearchText(''); setResults([]) }}
            />
          ) : (
            <kbd className="text-gray-600 text-xs bg-gray-800 px-1.5 py-0.5 rounded">Ctrl+K</kbd>
          )
        }
        value={searchText}
        onChange={(e) => handleSearch(e.target.value)}
        onFocus={() => setShowDropdown(true)}
        className="w-48 focus:w-72 transition-all"
        size="small"
        style={{
          background: '#1a1a3a',
          borderColor: showDropdown ? '#3b82f6' : '#3a3a5a',
        }}
      />

      {/* 下拉列表 */}
      {showDropdown && (
        <div
          className="absolute top-full left-0 mt-1 w-96 max-h-[400px] overflow-y-auto bg-[#1a1a2e] border border-gray-700 rounded-lg shadow-xl z-50"
        >
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <Spin size="small" />
              <span className="ml-2 text-gray-400">搜索中...</span>
            </div>
          ) : searchText && results.length > 0 ? (
            <div>
              <div className="px-3 py-2 text-xs text-gray-500 border-b border-gray-700">
                搜索结果
              </div>
              {results.map(info => renderSymbolItem(info))}
            </div>
          ) : searchText && results.length === 0 ? (
            <Empty
              image={Empty.PRESENTED_IMAGE_SIMPLE}
              description="未找到匹配的股票"
              className="py-6"
            />
          ) : showHotList ? (
            <>
              {/* 收藏列表 */}
              {favoriteSymbols.length > 0 && (
                <div>
                  <div className="px-3 py-2 text-xs text-gray-500 border-b border-gray-700 flex items-center gap-1">
                    <StarFilled className="text-yellow-400" /> 我的收藏
                  </div>
                  {favoriteSymbols.map(info => renderSymbolItem(info))}
                </div>
              )}

              {/* 热门股票 */}
              <div>
                <div className="px-3 py-2 text-xs text-gray-500 border-b border-gray-700">
                  热门股票
                </div>
                {HOT_SYMBOLS.slice(0, 6).map(info => renderSymbolItem(info))}
              </div>

              {/* 主要指数 */}
              <div>
                <div className="px-3 py-2 text-xs text-gray-500 border-b border-gray-700">
                  主要指数
                </div>
                {INDICES.map(info => renderSymbolItem(info, false))}
              </div>
            </>
          ) : null}
        </div>
      )}
    </div>
  )
}

export const StockSearch = memo(StockSearchComponent)
export default StockSearch
