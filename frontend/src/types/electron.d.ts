/**
 * Electron API TypeScript 类型定义
 */

interface ElectronAPI {
  // 应用信息
  getAppInfo: () => Promise<{
    version: string
    name: string
    dataPath: string
    platform: string
    isDev: boolean
  }>

  // 数据库操作
  db: {
    query: <T = any>(sql: string, params?: any[]) => Promise<{ success: boolean; data: T[] }>
    execute: (sql: string, params?: any[]) => Promise<{ success: boolean; changes: number }>
  }

  // 文件操作
  file: {
    read: (filePath: string) => Promise<{ success: boolean; content?: string; error?: string }>
    write: (filePath: string, content: string) => Promise<{ success: boolean; error?: string }>
  }

  // 系统操作
  shell: {
    openExternal: (url: string) => Promise<void>
  }

  // 事件监听
  on: (channel: string, callback: (...args: any[]) => void) => void
  removeListener: (channel: string, callback: (...args: any[]) => void) => void

  // 平台信息
  platform: 'win32' | 'darwin' | 'linux'
  isElectron: true
}

interface LocalStore {
  get: <T = any>(key: string) => Promise<T | null>
  set: (key: string, value: any) => Promise<{ success: boolean; error?: string }>
  delete: (key: string) => Promise<{ success: boolean; error?: string }>
}

declare global {
  interface Window {
    electronAPI?: ElectronAPI
    localStore?: LocalStore
  }
}

export {}
