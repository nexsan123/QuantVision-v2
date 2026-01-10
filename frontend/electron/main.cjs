/**
 * QuantVision Desktop - Electron Main Process
 *
 * 主进程职责:
 * - 创建和管理应用窗口
 * - 系统托盘
 * - 本地数据库 (SQLite)
 * - 文件系统操作
 * - IPC 通信
 */

const { app, BrowserWindow, ipcMain, Tray, Menu, nativeImage, shell } = require('electron')
const path = require('path')
const fs = require('fs')

// 开发模式检测
const isDev = !app.isPackaged

// 应用路径
const APP_DATA_PATH = path.join(app.getPath('userData'), 'QuantVision')
const DB_PATH = path.join(APP_DATA_PATH, 'quantvision.db')
const LOGS_PATH = path.join(APP_DATA_PATH, 'logs')

// 确保数据目录存在
function ensureDirectories() {
  if (!fs.existsSync(APP_DATA_PATH)) {
    fs.mkdirSync(APP_DATA_PATH, { recursive: true })
  }
  if (!fs.existsSync(LOGS_PATH)) {
    fs.mkdirSync(LOGS_PATH, { recursive: true })
  }
}

// 主窗口引用
let mainWindow = null
let tray = null

// 创建主窗口
function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1600,
    height: 1000,
    minWidth: 1200,
    minHeight: 800,
    title: 'QuantVision - 量化交易平台',
    icon: path.join(__dirname, 'assets', 'icon.ico'),
    backgroundColor: '#0a0a1a',
    show: false, // 等待 ready-to-show
    webPreferences: {
      preload: path.join(__dirname, 'preload.cjs'),
      nodeIntegration: false,
      contextIsolation: true,
      sandbox: true,
    },
  })

  // 加载应用
  if (isDev) {
    // 开发模式: 连接 Vite 开发服务器
    mainWindow.loadURL('http://localhost:5173')
    mainWindow.webContents.openDevTools()
  } else {
    // 生产模式: 加载打包后的文件
    mainWindow.loadFile(path.join(__dirname, '../dist/index.html'))
  }

  // 窗口准备好后显示
  mainWindow.once('ready-to-show', () => {
    mainWindow.show()
  })

  // 外部链接用浏览器打开
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url)
    return { action: 'deny' }
  })

  // 窗口关闭时最小化到托盘
  mainWindow.on('close', (event) => {
    if (!app.isQuitting) {
      event.preventDefault()
      mainWindow.hide()
    }
  })

  return mainWindow
}

// 创建系统托盘
function createTray() {
  // 托盘图标 (使用简单的占位图标，实际应用需要真实图标)
  const iconPath = path.join(__dirname, 'assets', 'tray-icon.png')

  // 如果图标不存在，创建一个默认的
  if (!fs.existsSync(iconPath)) {
    // 使用 Electron 默认图标或创建一个简单的
    tray = new Tray(nativeImage.createEmpty())
  } else {
    tray = new Tray(iconPath)
  }

  const contextMenu = Menu.buildFromTemplate([
    {
      label: '显示主窗口',
      click: () => {
        mainWindow.show()
        mainWindow.focus()
      }
    },
    { type: 'separator' },
    {
      label: '市场状态',
      enabled: false,
      sublabel: '美股盘前'
    },
    {
      label: '策略运行中: 3',
      enabled: false
    },
    { type: 'separator' },
    {
      label: '快捷交易',
      submenu: [
        { label: '买入 AAPL', click: () => { /* TODO */ } },
        { label: '买入 TSLA', click: () => { /* TODO */ } },
        { label: '买入 NVDA', click: () => { /* TODO */ } },
      ]
    },
    { type: 'separator' },
    {
      label: '退出 QuantVision',
      click: () => {
        app.isQuitting = true
        app.quit()
      }
    }
  ])

  tray.setToolTip('QuantVision - 量化交易平台')
  tray.setContextMenu(contextMenu)

  // 点击托盘图标显示窗口
  tray.on('click', () => {
    if (mainWindow.isVisible()) {
      mainWindow.focus()
    } else {
      mainWindow.show()
    }
  })
}

// ============================================================================
// IPC 处理器 - 与渲染进程通信
// ============================================================================

// 获取应用信息
ipcMain.handle('app:getInfo', () => {
  return {
    version: app.getVersion(),
    name: app.getName(),
    dataPath: APP_DATA_PATH,
    platform: process.platform,
    isDev: isDev,
  }
})

// 数据库操作 (将在后续集成 better-sqlite3)
ipcMain.handle('db:query', async (event, sql, params) => {
  // TODO: 集成 SQLite
  console.log('DB Query:', sql, params)
  return { success: true, data: [] }
})

ipcMain.handle('db:execute', async (event, sql, params) => {
  // TODO: 集成 SQLite
  console.log('DB Execute:', sql, params)
  return { success: true, changes: 0 }
})

// 文件操作
ipcMain.handle('file:read', async (event, filePath) => {
  try {
    const fullPath = path.join(APP_DATA_PATH, filePath)
    const content = fs.readFileSync(fullPath, 'utf-8')
    return { success: true, content }
  } catch (error) {
    return { success: false, error: error.message }
  }
})

ipcMain.handle('file:write', async (event, filePath, content) => {
  try {
    const fullPath = path.join(APP_DATA_PATH, filePath)
    const dir = path.dirname(fullPath)
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true })
    }
    fs.writeFileSync(fullPath, content, 'utf-8')
    return { success: true }
  } catch (error) {
    return { success: false, error: error.message }
  }
})

// 打开外部链接
ipcMain.handle('shell:openExternal', async (event, url) => {
  await shell.openExternal(url)
})

// ============================================================================
// 应用生命周期
// ============================================================================

app.whenReady().then(() => {
  ensureDirectories()
  createWindow()
  createTray()

  // macOS: 点击 dock 图标时重新创建窗口
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow()
    } else {
      mainWindow.show()
    }
  })
})

// 所有窗口关闭时的处理
app.on('window-all-closed', () => {
  // macOS 上保持应用运行
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

// 应用退出前清理
app.on('before-quit', () => {
  app.isQuitting = true
})

// 阻止多实例
const gotTheLock = app.requestSingleInstanceLock()
if (!gotTheLock) {
  app.quit()
} else {
  app.on('second-instance', () => {
    if (mainWindow) {
      if (mainWindow.isMinimized()) mainWindow.restore()
      mainWindow.focus()
    }
  })
}

console.log('QuantVision Desktop starting...')
console.log('Data path:', APP_DATA_PATH)
console.log('Dev mode:', isDev)
