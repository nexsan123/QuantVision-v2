/**
 * 平台检测和环境工具
 *
 * 用于检测当前运行环境 (Electron 桌面 vs Web 浏览器)
 * 并提供统一的 API 抽象
 */

// 检测是否在 Electron 环境中运行
export const isElectron = (): boolean => {
  return typeof window !== 'undefined' && window.electronAPI?.isElectron === true
}

// 获取平台类型
export const getPlatform = (): 'electron' | 'web' => {
  return isElectron() ? 'electron' : 'web'
}

// 获取操作系统
export const getOS = (): 'win32' | 'darwin' | 'linux' | 'unknown' => {
  if (isElectron() && window.electronAPI) {
    return window.electronAPI.platform
  }

  // Web 环境下通过 userAgent 检测
  const ua = navigator.userAgent.toLowerCase()
  if (ua.includes('win')) return 'win32'
  if (ua.includes('mac')) return 'darwin'
  if (ua.includes('linux')) return 'linux'
  return 'unknown'
}

// 获取应用信息
export const getAppInfo = async () => {
  if (isElectron() && window.electronAPI) {
    return window.electronAPI.getAppInfo()
  }

  // Web 环境返回默认值
  return {
    version: import.meta.env.VITE_APP_VERSION || '2.1.0',
    name: 'QuantVision',
    dataPath: '',
    platform: getOS(),
    isDev: import.meta.env.DEV,
  }
}

// 打开外部链接
export const openExternal = async (url: string) => {
  if (isElectron() && window.electronAPI) {
    return window.electronAPI.shell.openExternal(url)
  }

  // Web 环境直接打开新窗口
  window.open(url, '_blank', 'noopener,noreferrer')
}

// 数据存储抽象 (Electron 使用文件系统, Web 使用 localStorage)
export const storage = {
  get: async <T = any>(key: string): Promise<T | null> => {
    if (isElectron() && window.localStore) {
      return window.localStore.get<T>(key)
    }

    // Web 环境使用 localStorage
    const value = localStorage.getItem(`qv_${key}`)
    if (value) {
      try {
        return JSON.parse(value) as T
      } catch {
        return value as unknown as T
      }
    }
    return null
  },

  set: async (key: string, value: any): Promise<boolean> => {
    if (isElectron() && window.localStore) {
      const result = await window.localStore.set(key, value)
      return result.success
    }

    // Web 环境使用 localStorage
    try {
      const content = typeof value === 'string' ? value : JSON.stringify(value)
      localStorage.setItem(`qv_${key}`, content)
      return true
    } catch {
      return false
    }
  },

  delete: async (key: string): Promise<boolean> => {
    if (isElectron() && window.localStore) {
      const result = await window.localStore.delete(key)
      return result.success
    }

    // Web 环境
    localStorage.removeItem(`qv_${key}`)
    return true
  },
}

// 日志工具
export const logger = {
  info: (...args: any[]) => {
    console.log('[QuantVision]', ...args)
  },
  warn: (...args: any[]) => {
    console.warn('[QuantVision]', ...args)
  },
  error: (...args: any[]) => {
    console.error('[QuantVision]', ...args)
  },
  debug: (...args: any[]) => {
    if (import.meta.env.DEV) {
      console.debug('[QuantVision]', ...args)
    }
  },
}

// 导出平台信息
export const platformInfo = {
  isElectron: isElectron(),
  platform: getPlatform(),
  os: getOS(),
}

export default {
  isElectron,
  getPlatform,
  getOS,
  getAppInfo,
  openExternal,
  storage,
  logger,
  platformInfo,
}
