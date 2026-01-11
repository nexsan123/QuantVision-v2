/**
 * QuantVision Desktop - Preload Script
 *
 * 预加载脚本职责:
 * - 安全地暴露 Node.js API 给渲染进程
 * - IPC 通信桥接
 * - 本地数据库操作封装
 */

const { contextBridge, ipcRenderer } = require('electron')

// ============================================================================
// 暴露给渲染进程的 API
// ============================================================================

contextBridge.exposeInMainWorld('electronAPI', {
  // === 应用信息 ===
  getAppInfo: () => ipcRenderer.invoke('app:getInfo'),

  // === 数据库操作 ===
  db: {
    query: (sql, params) => ipcRenderer.invoke('db:query', sql, params),
    execute: (sql, params) => ipcRenderer.invoke('db:execute', sql, params),
  },

  // === 文件操作 ===
  file: {
    read: (filePath) => ipcRenderer.invoke('file:read', filePath),
    write: (filePath, content) => ipcRenderer.invoke('file:write', filePath, content),
  },

  // === 系统操作 ===
  shell: {
    openExternal: (url) => ipcRenderer.invoke('shell:openExternal', url),
  },

  // === 后端服务管理 ===
  backend: {
    getStatus: () => ipcRenderer.invoke('backend:status'),
    restart: () => ipcRenderer.invoke('backend:restart'),
  },

  // === 事件监听 ===
  on: (channel, callback) => {
    const validChannels = [
      'market:status',
      'strategy:signal',
      'order:update',
      'alert:new',
    ]
    if (validChannels.includes(channel)) {
      ipcRenderer.on(channel, (event, ...args) => callback(...args))
    }
  },

  // === 移除事件监听 ===
  removeListener: (channel, callback) => {
    ipcRenderer.removeListener(channel, callback)
  },

  // === 平台信息 ===
  platform: process.platform,
  isElectron: true,
})

// ============================================================================
// 本地存储增强 (使用文件系统替代 localStorage 限制)
// ============================================================================

contextBridge.exposeInMainWorld('localStore', {
  // 获取数据
  get: async (key) => {
    const result = await ipcRenderer.invoke('file:read', `store/${key}.json`)
    if (result.success) {
      try {
        return JSON.parse(result.content)
      } catch {
        return result.content
      }
    }
    return null
  },

  // 设置数据
  set: async (key, value) => {
    const content = typeof value === 'string' ? value : JSON.stringify(value, null, 2)
    return ipcRenderer.invoke('file:write', `store/${key}.json`, content)
  },

  // 删除数据
  delete: async (key) => {
    return ipcRenderer.invoke('file:delete', `store/${key}.json`)
  },
})

console.log('QuantVision preload script loaded')
