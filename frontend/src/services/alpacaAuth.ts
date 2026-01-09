/**
 * Alpaca 认证服务
 * Sprint 8: T9 - Alpaca OAuth 流程
 *
 * 支持两种认证方式:
 * 1. API Key 认证 (简单模式)
 * 2. OAuth 2.0 认证 (第三方应用)
 */

// 环境配置
const ALPACA_PAPER_URL = 'https://paper-api.alpaca.markets'
const ALPACA_LIVE_URL = 'https://api.alpaca.markets'
const ALPACA_DATA_URL = 'https://data.alpaca.markets'
const ALPACA_OAUTH_URL = 'https://app.alpaca.markets/oauth'

// 交易环境
export type TradingEnvironment = 'paper' | 'live'

// 认证凭证
export interface AlpacaCredentials {
  apiKey: string
  secretKey: string
  environment: TradingEnvironment
}

// OAuth 配置
export interface OAuthConfig {
  clientId: string
  clientSecret: string
  redirectUri: string
  scope: string[]
}

// OAuth Token
export interface OAuthToken {
  access_token: string
  token_type: string
  scope: string
  created_at: number
  expires_in?: number
}

// 账户信息
export interface AlpacaAccount {
  id: string
  account_number: string
  status: 'ONBOARDING' | 'SUBMISSION_FAILED' | 'SUBMITTED' | 'ACCOUNT_UPDATED' | 'APPROVAL_PENDING' | 'ACTIVE' | 'REJECTED'
  currency: string
  buying_power: string
  cash: string
  portfolio_value: string
  pattern_day_trader: boolean
  trading_blocked: boolean
  transfers_blocked: boolean
  account_blocked: boolean
  created_at: string
  trade_suspended_by_user: boolean
  multiplier: string
  shorting_enabled: boolean
  equity: string
  last_equity: string
  long_market_value: string
  short_market_value: string
  initial_margin: string
  maintenance_margin: string
  last_maintenance_margin: string
  sma: string
  daytrade_count: number
  daytrading_buying_power: string
  regt_buying_power: string
}

// 存储键
const STORAGE_KEY = 'alpaca_credentials'
const TOKEN_STORAGE_KEY = 'alpaca_oauth_token'

/**
 * Alpaca 认证服务类
 */
class AlpacaAuthService {
  private credentials: AlpacaCredentials | null = null
  private oauthToken: OAuthToken | null = null
  private oauthConfig: OAuthConfig | null = null

  constructor() {
    this.loadCredentials()
  }

  /**
   * 从本地存储加载凭证
   */
  private loadCredentials(): void {
    try {
      const stored = localStorage.getItem(STORAGE_KEY)
      if (stored) {
        this.credentials = JSON.parse(stored)
      }

      const token = localStorage.getItem(TOKEN_STORAGE_KEY)
      if (token) {
        this.oauthToken = JSON.parse(token)
      }
    } catch (error) {
      console.error('[AlpacaAuth] Failed to load credentials:', error)
    }
  }

  /**
   * 保存凭证到本地存储
   */
  private saveCredentials(): void {
    try {
      if (this.credentials) {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(this.credentials))
      } else {
        localStorage.removeItem(STORAGE_KEY)
      }

      if (this.oauthToken) {
        localStorage.setItem(TOKEN_STORAGE_KEY, JSON.stringify(this.oauthToken))
      } else {
        localStorage.removeItem(TOKEN_STORAGE_KEY)
      }
    } catch (error) {
      console.error('[AlpacaAuth] Failed to save credentials:', error)
    }
  }

  /**
   * 设置 API Key 认证
   */
  setApiKeyAuth(apiKey: string, secretKey: string, environment: TradingEnvironment = 'paper'): void {
    this.credentials = { apiKey, secretKey, environment }
    this.oauthToken = null
    this.saveCredentials()
  }

  /**
   * 配置 OAuth
   */
  configureOAuth(config: OAuthConfig): void {
    this.oauthConfig = config
  }

  /**
   * 获取 OAuth 授权 URL
   */
  getOAuthUrl(state?: string): string {
    if (!this.oauthConfig) {
      throw new Error('OAuth not configured')
    }

    const params = new URLSearchParams({
      response_type: 'code',
      client_id: this.oauthConfig.clientId,
      redirect_uri: this.oauthConfig.redirectUri,
      scope: this.oauthConfig.scope.join(' '),
      ...(state && { state }),
    })

    return `${ALPACA_OAUTH_URL}/authorize?${params.toString()}`
  }

  /**
   * 使用授权码交换 Token
   */
  async exchangeCodeForToken(code: string): Promise<OAuthToken> {
    if (!this.oauthConfig) {
      throw new Error('OAuth not configured')
    }

    const response = await fetch(`${ALPACA_OAUTH_URL}/token`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: new URLSearchParams({
        grant_type: 'authorization_code',
        code,
        client_id: this.oauthConfig.clientId,
        client_secret: this.oauthConfig.clientSecret,
        redirect_uri: this.oauthConfig.redirectUri,
      }),
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({}))
      throw new Error(error.message || 'Token exchange failed')
    }

    this.oauthToken = await response.json()
    this.credentials = null
    this.saveCredentials()

    return this.oauthToken!
  }

  /**
   * 获取认证头
   */
  getAuthHeaders(): Record<string, string> {
    if (this.oauthToken) {
      return {
        'Authorization': `Bearer ${this.oauthToken.access_token}`,
      }
    }

    if (this.credentials) {
      return {
        'APCA-API-KEY-ID': this.credentials.apiKey,
        'APCA-API-SECRET-KEY': this.credentials.secretKey,
      }
    }

    throw new Error('Not authenticated')
  }

  /**
   * 获取 API 基础 URL
   */
  getBaseUrl(): string {
    if (this.oauthToken) {
      return ALPACA_PAPER_URL // OAuth 默认使用 paper
    }

    if (this.credentials) {
      return this.credentials.environment === 'live'
        ? ALPACA_LIVE_URL
        : ALPACA_PAPER_URL
    }

    return ALPACA_PAPER_URL
  }

  /**
   * 获取数据 API URL
   */
  getDataUrl(): string {
    return ALPACA_DATA_URL
  }

  /**
   * 获取当前环境
   */
  getEnvironment(): TradingEnvironment {
    return this.credentials?.environment || 'paper'
  }

  /**
   * 切换交易环境
   */
  setEnvironment(environment: TradingEnvironment): void {
    if (this.credentials) {
      this.credentials.environment = environment
      this.saveCredentials()
    }
  }

  /**
   * 检查是否已认证
   */
  isAuthenticated(): boolean {
    return !!(this.credentials || this.oauthToken)
  }

  /**
   * 验证凭证
   */
  async validateCredentials(): Promise<AlpacaAccount> {
    const headers = this.getAuthHeaders()
    const baseUrl = this.getBaseUrl()

    const response = await fetch(`${baseUrl}/v2/account`, {
      headers,
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({}))
      throw new Error(error.message || 'Invalid credentials')
    }

    return response.json()
  }

  /**
   * 登出
   */
  logout(): void {
    this.credentials = null
    this.oauthToken = null
    this.saveCredentials()
  }

  /**
   * 获取凭证信息 (脱敏)
   */
  getCredentialsInfo(): { type: 'api_key' | 'oauth' | 'none'; environment: TradingEnvironment; maskedKey?: string } {
    if (this.oauthToken) {
      return { type: 'oauth', environment: 'paper' }
    }

    if (this.credentials) {
      return {
        type: 'api_key',
        environment: this.credentials.environment,
        maskedKey: `${this.credentials.apiKey.slice(0, 4)}...${this.credentials.apiKey.slice(-4)}`,
      }
    }

    return { type: 'none', environment: 'paper' }
  }
}

// 单例实例
export const alpacaAuth = new AlpacaAuthService()

// 从环境变量初始化 (如果有)
const envApiKey = import.meta.env.VITE_ALPACA_API_KEY
const envSecretKey = import.meta.env.VITE_ALPACA_SECRET_KEY
const envEnvironment = (import.meta.env.VITE_ALPACA_ENV as TradingEnvironment) || 'paper'

if (envApiKey && envSecretKey && !alpacaAuth.isAuthenticated()) {
  alpacaAuth.setApiKeyAuth(envApiKey, envSecretKey, envEnvironment)
}

export default AlpacaAuthService
