/**
 * API 客户端工具
 * Sprint 12: T27 - 错误处理增强 + T28 - 重试机制
 *
 * 提供统一的 API 请求处理:
 * - 自动重试
 * - 错误分类
 * - 超时处理
 * - 请求取消
 */

// ==================== 错误类型 ====================

export class ApiError extends Error {
  constructor(
    message: string,
    public statusCode: number,
    public code: string,
    public details?: Record<string, unknown>
  ) {
    super(message)
    this.name = 'ApiError'
  }

  /**
   * 是否是网络错误
   */
  isNetworkError(): boolean {
    return this.code === 'NETWORK_ERROR'
  }

  /**
   * 是否是超时错误
   */
  isTimeoutError(): boolean {
    return this.code === 'TIMEOUT'
  }

  /**
   * 是否是认证错误
   */
  isAuthError(): boolean {
    return this.statusCode === 401 || this.statusCode === 403
  }

  /**
   * 是否是客户端错误 (4xx)
   */
  isClientError(): boolean {
    return this.statusCode >= 400 && this.statusCode < 500
  }

  /**
   * 是否是服务器错误 (5xx)
   */
  isServerError(): boolean {
    return this.statusCode >= 500
  }

  /**
   * 是否可重试
   */
  isRetryable(): boolean {
    return (
      this.isNetworkError() ||
      this.isTimeoutError() ||
      this.statusCode === 429 || // Too Many Requests
      this.statusCode >= 500
    )
  }
}

// ==================== 重试配置 ====================

export interface RetryConfig {
  maxRetries: number
  baseDelay: number  // 毫秒
  maxDelay: number   // 毫秒
  backoffFactor: number
  retryCondition?: (error: ApiError) => boolean
}

const DEFAULT_RETRY_CONFIG: RetryConfig = {
  maxRetries: 3,
  baseDelay: 1000,
  maxDelay: 10000,
  backoffFactor: 2,
  retryCondition: (error) => error.isRetryable(),
}

// ==================== 请求配置 ====================

export interface RequestConfig extends RequestInit {
  timeout?: number
  retry?: Partial<RetryConfig> | boolean
  onRetry?: (attempt: number, error: ApiError) => void
}

// ==================== 工具函数 ====================

/**
 * 延迟函数
 */
function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

/**
 * 计算重试延迟 (指数退避 + 抖动)
 */
function calculateRetryDelay(attempt: number, config: RetryConfig): number {
  const exponentialDelay = config.baseDelay * Math.pow(config.backoffFactor, attempt)
  const jitter = Math.random() * 0.3 * exponentialDelay // 30% 抖动
  const totalDelay = exponentialDelay + jitter
  return Math.min(totalDelay, config.maxDelay)
}

/**
 * 带超时的 fetch
 */
async function fetchWithTimeout(
  url: string,
  options: RequestInit,
  timeout: number
): Promise<Response> {
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), timeout)

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
    })
    return response
  } finally {
    clearTimeout(timeoutId)
  }
}

/**
 * 解析错误响应
 */
async function parseErrorResponse(response: Response): Promise<ApiError> {
  let message = `HTTP ${response.status}`
  let code = 'HTTP_ERROR'
  let details: Record<string, unknown> | undefined

  try {
    const data = await response.json()
    message = data.detail || data.message || data.error || message
    code = data.code || code
    details = data
  } catch {
    // 无法解析 JSON，使用状态文本
    message = response.statusText || message
  }

  return new ApiError(message, response.status, code, details)
}

// ==================== API 客户端 ====================

/**
 * 发送 API 请求 (带重试和错误处理)
 */
export async function apiRequest<T>(
  url: string,
  config: RequestConfig = {}
): Promise<T> {
  const {
    timeout = 30000,
    retry = true,
    onRetry,
    ...fetchOptions
  } = config

  // 合并重试配置
  const retryConfig: RetryConfig = {
    ...DEFAULT_RETRY_CONFIG,
    ...(typeof retry === 'object' ? retry : {}),
  }

  const shouldRetry = retry !== false

  let lastError: ApiError | null = null
  let attempt = 0

  while (attempt <= (shouldRetry ? retryConfig.maxRetries : 0)) {
    try {
      const response = await fetchWithTimeout(url, {
        ...fetchOptions,
        headers: {
          'Content-Type': 'application/json',
          ...fetchOptions.headers,
        },
      }, timeout)

      if (!response.ok) {
        throw await parseErrorResponse(response)
      }

      // 204 No Content
      if (response.status === 204) {
        return undefined as T
      }

      return await response.json()

    } catch (error) {
      // 处理 AbortError (超时)
      if (error instanceof Error && error.name === 'AbortError') {
        lastError = new ApiError('Request timeout', 0, 'TIMEOUT')
      }
      // 处理网络错误
      else if (error instanceof TypeError && error.message.includes('fetch')) {
        lastError = new ApiError('Network error', 0, 'NETWORK_ERROR')
      }
      // 处理 ApiError
      else if (error instanceof ApiError) {
        lastError = error
      }
      // 其他错误
      else {
        lastError = new ApiError(
          error instanceof Error ? error.message : 'Unknown error',
          0,
          'UNKNOWN'
        )
      }

      // 检查是否应该重试
      const shouldRetryThis =
        shouldRetry &&
        attempt < retryConfig.maxRetries &&
        (retryConfig.retryCondition?.(lastError) ?? lastError.isRetryable())

      if (shouldRetryThis) {
        const retryDelay = calculateRetryDelay(attempt, retryConfig)
        console.warn(
          `[API] Retry ${attempt + 1}/${retryConfig.maxRetries} for ${url} in ${retryDelay}ms`,
          lastError.message
        )
        onRetry?.(attempt + 1, lastError)
        await delay(retryDelay)
        attempt++
      } else {
        break
      }
    }
  }

  throw lastError
}

// ==================== 便捷方法 ====================

/**
 * GET 请求
 */
export function get<T>(url: string, config?: RequestConfig): Promise<T> {
  return apiRequest<T>(url, { ...config, method: 'GET' })
}

/**
 * POST 请求
 */
export function post<T>(url: string, data?: unknown, config?: RequestConfig): Promise<T> {
  return apiRequest<T>(url, {
    ...config,
    method: 'POST',
    body: data ? JSON.stringify(data) : undefined,
  })
}

/**
 * PUT 请求
 */
export function put<T>(url: string, data?: unknown, config?: RequestConfig): Promise<T> {
  return apiRequest<T>(url, {
    ...config,
    method: 'PUT',
    body: data ? JSON.stringify(data) : undefined,
  })
}

/**
 * PATCH 请求
 */
export function patch<T>(url: string, data?: unknown, config?: RequestConfig): Promise<T> {
  return apiRequest<T>(url, {
    ...config,
    method: 'PATCH',
    body: data ? JSON.stringify(data) : undefined,
  })
}

/**
 * DELETE 请求
 */
export function del<T>(url: string, config?: RequestConfig): Promise<T> {
  return apiRequest<T>(url, { ...config, method: 'DELETE' })
}

// ==================== 错误处理 Hook ====================

/**
 * 用于组件中统一处理 API 错误
 */
export function handleApiError(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.isNetworkError()) {
      return '网络连接失败，请检查网络'
    }
    if (error.isTimeoutError()) {
      return '请求超时，请稍后重试'
    }
    if (error.isAuthError()) {
      return '认证失败，请重新登录'
    }
    if (error.statusCode === 429) {
      return '请求过于频繁，请稍后重试'
    }
    if (error.isServerError()) {
      return '服务器错误，请稍后重试'
    }
    return error.message
  }

  if (error instanceof Error) {
    return error.message
  }

  return '未知错误'
}

export default {
  request: apiRequest,
  get,
  post,
  put,
  patch,
  del,
  handleApiError,
  ApiError,
}
