/// <reference types="vite/client" />

/**
 * Vite 环境变量类型定义
 * 修复 import.meta.env 类型错误 (TS2339)
 */
interface ImportMetaEnv {
  // API 配置
  readonly VITE_API_BASE_URL: string
  readonly VITE_WS_URL: string

  // Polygon API
  readonly VITE_POLYGON_API_KEY: string
  readonly VITE_POLYGON_WS_URL: string

  // Alpaca API
  readonly VITE_ALPACA_API_KEY: string
  readonly VITE_ALPACA_SECRET_KEY: string
  readonly VITE_ALPACA_BASE_URL: string
  readonly VITE_ALPACA_DATA_URL: string
  readonly VITE_ALPACA_OAUTH_CLIENT_ID: string
  readonly VITE_ALPACA_OAUTH_REDIRECT_URI: string

  // AI 配置
  readonly VITE_AI_API_KEY: string
  readonly VITE_AI_MODEL: string

  // 环境标识
  readonly VITE_ENV: 'development' | 'production' | 'test'
  readonly DEV: boolean
  readonly PROD: boolean
  readonly MODE: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

// 全局 process 定义 (用于某些库)
declare namespace NodeJS {
  interface ProcessEnv {
    NODE_ENV: 'development' | 'production' | 'test'
  }
}

declare const process: {
  env: NodeJS.ProcessEnv
}
