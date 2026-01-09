/**
 * 前端日志系统
 * Sprint 13: T33 - 前端日志收集
 *
 * 提供:
 * - 结构化日志
 * - 错误收集
 * - 性能监控
 * - 日志上报
 */

// ==================== 类型定义 ====================

type LogLevel = 'debug' | 'info' | 'warn' | 'error'

interface LogEntry {
  level: LogLevel
  message: string
  timestamp: string
  context?: Record<string, unknown>
  error?: {
    name: string
    message: string
    stack?: string
  }
  performance?: {
    duration_ms: number
    operation: string
  }
  user?: {
    id?: string
    session_id?: string
  }
  page?: {
    url: string
    route?: string
  }
}

interface LoggerConfig {
  minLevel: LogLevel
  enableConsole: boolean
  enableRemote: boolean
  remoteEndpoint?: string
  batchSize: number
  flushInterval: number
  maxBufferSize: number
}

// ==================== 常量 ====================

const LOG_LEVELS: Record<LogLevel, number> = {
  debug: 0,
  info: 1,
  warn: 2,
  error: 3,
}

const DEFAULT_CONFIG: LoggerConfig = {
  minLevel: import.meta.env.DEV ? 'debug' : 'info',
  enableConsole: true,
  enableRemote: import.meta.env.PROD,
  remoteEndpoint: `${import.meta.env.VITE_API_BASE_URL || ''}/api/v1/logs`,
  batchSize: 10,
  flushInterval: 30000, // 30 秒
  maxBufferSize: 100,
}

// ==================== 日志缓冲区 ====================

class LogBuffer {
  private buffer: LogEntry[] = []
  private flushTimer: ReturnType<typeof setInterval> | null = null
  private config: LoggerConfig

  constructor(config: LoggerConfig) {
    this.config = config

    if (config.enableRemote && config.flushInterval > 0) {
      this.startFlushTimer()
    }

    // 页面卸载时刷新
    if (typeof window !== 'undefined') {
      window.addEventListener('beforeunload', () => this.flush())
    }
  }

  add(entry: LogEntry): void {
    this.buffer.push(entry)

    // 缓冲区满时刷新
    if (this.buffer.length >= this.config.batchSize) {
      this.flush()
    }

    // 超过最大缓冲区时丢弃旧日志
    if (this.buffer.length > this.config.maxBufferSize) {
      this.buffer = this.buffer.slice(-this.config.maxBufferSize)
    }
  }

  private startFlushTimer(): void {
    this.flushTimer = setInterval(() => {
      this.flush()
    }, this.config.flushInterval)
  }

  async flush(): Promise<void> {
    if (this.buffer.length === 0 || !this.config.enableRemote) {
      return
    }

    const logsToSend = [...this.buffer]
    this.buffer = []

    try {
      await fetch(this.config.remoteEndpoint!, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ logs: logsToSend }),
        keepalive: true, // 页面卸载时保持请求
      })
    } catch {
      // 发送失败时恢复到缓冲区
      this.buffer = [...logsToSend, ...this.buffer].slice(-this.config.maxBufferSize)
    }
  }

  destroy(): void {
    if (this.flushTimer) {
      clearInterval(this.flushTimer)
    }
    this.flush()
  }
}

// ==================== Logger 类 ====================

class Logger {
  private config: LoggerConfig
  private buffer: LogBuffer
  private sessionId: string
  private context: Record<string, unknown> = {}

  constructor(config: Partial<LoggerConfig> = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config }
    this.buffer = new LogBuffer(this.config)
    this.sessionId = this.generateSessionId()

    // 设置全局错误处理
    this.setupGlobalErrorHandlers()
  }

  private generateSessionId(): string {
    return `${Date.now()}-${Math.random().toString(36).substring(2, 9)}`
  }

  private shouldLog(level: LogLevel): boolean {
    return LOG_LEVELS[level] >= LOG_LEVELS[this.config.minLevel]
  }

  private createEntry(
    level: LogLevel,
    message: string,
    context?: Record<string, unknown>,
    error?: Error,
    performance?: { duration_ms: number; operation: string },
  ): LogEntry {
    return {
      level,
      message,
      timestamp: new Date().toISOString(),
      context: { ...this.context, ...context },
      error: error ? {
        name: error.name,
        message: error.message,
        stack: error.stack,
      } : undefined,
      performance,
      user: {
        session_id: this.sessionId,
      },
      page: typeof window !== 'undefined' ? {
        url: window.location.href,
        route: window.location.pathname,
      } : undefined,
    }
  }

  private log(
    level: LogLevel,
    message: string,
    context?: Record<string, unknown>,
    error?: Error,
  ): void {
    if (!this.shouldLog(level)) return

    const entry = this.createEntry(level, message, context, error)

    // 控制台输出
    if (this.config.enableConsole) {
      const consoleMethod = level === 'error' ? console.error :
                           level === 'warn' ? console.warn :
                           level === 'debug' ? console.debug :
                           console.info

      const prefix = `[${level.toUpperCase()}]`
      if (error) {
        consoleMethod(prefix, message, context, error)
      } else if (context) {
        consoleMethod(prefix, message, context)
      } else {
        consoleMethod(prefix, message)
      }
    }

    // 添加到缓冲区
    this.buffer.add(entry)
  }

  // ==================== 公共方法 ====================

  debug(message: string, context?: Record<string, unknown>): void {
    this.log('debug', message, context)
  }

  info(message: string, context?: Record<string, unknown>): void {
    this.log('info', message, context)
  }

  warn(message: string, context?: Record<string, unknown>): void {
    this.log('warn', message, context)
  }

  error(message: string, error?: Error | unknown, context?: Record<string, unknown>): void {
    const err = error instanceof Error ? error : error ? new Error(String(error)) : undefined
    this.log('error', message, context, err)
  }

  /**
   * 设置全局上下文
   */
  setContext(context: Record<string, unknown>): void {
    this.context = { ...this.context, ...context }
  }

  /**
   * 设置用户 ID
   */
  setUserId(userId: string): void {
    this.context.user_id = userId
  }

  /**
   * 性能测量
   */
  time(operation: string): () => void {
    const start = performance.now()

    return () => {
      const duration_ms = performance.now() - start
      const entry = this.createEntry(
        'info',
        `Operation completed: ${operation}`,
        undefined,
        undefined,
        { duration_ms, operation },
      )

      if (this.config.enableConsole) {
        console.info(`[PERF] ${operation}: ${duration_ms.toFixed(2)}ms`)
      }

      this.buffer.add(entry)
    }
  }

  /**
   * 异步操作性能包装
   */
  async measure<T>(operation: string, fn: () => Promise<T>): Promise<T> {
    const end = this.time(operation)
    try {
      return await fn()
    } finally {
      end()
    }
  }

  /**
   * 页面事件记录
   */
  pageView(route: string, params?: Record<string, unknown>): void {
    this.info('page_view', { route, ...params })
  }

  /**
   * 用户操作记录
   */
  action(action: string, details?: Record<string, unknown>): void {
    this.info('user_action', { action, ...details })
  }

  /**
   * 手动刷新日志
   */
  async flush(): Promise<void> {
    await this.buffer.flush()
  }

  // ==================== 全局错误处理 ====================

  private setupGlobalErrorHandlers(): void {
    if (typeof window === 'undefined') return

    // 未捕获的 JavaScript 错误
    window.addEventListener('error', (event) => {
      this.error('Uncaught error', event.error, {
        filename: event.filename,
        lineno: event.lineno,
        colno: event.colno,
      })
    })

    // 未处理的 Promise 拒绝
    window.addEventListener('unhandledrejection', (event) => {
      this.error('Unhandled promise rejection', event.reason, {
        type: 'unhandledrejection',
      })
    })

    // 资源加载错误
    window.addEventListener('error', (event) => {
      const target = event.target as HTMLElement
      if (target && (target.tagName === 'SCRIPT' || target.tagName === 'LINK' || target.tagName === 'IMG')) {
        this.error('Resource load failed', undefined, {
          type: 'resource_error',
          tagName: target.tagName,
          src: (target as HTMLImageElement).src || (target as HTMLLinkElement).href,
        })
      }
    }, true)
  }
}

// ==================== 导出单例 ====================

export const logger = new Logger()

export default logger
