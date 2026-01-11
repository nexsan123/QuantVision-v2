/**
 * QuantVision Desktop - Electron Main Process
 *
 * 主进程职责:
 * - 创建和管理应用窗口
 * - 系统托盘
 * - 本地数据库 (SQLite)
 * - 文件系统操作
 * - IPC 通信
 * - 自动启动后端服务
 */

const { app, BrowserWindow, ipcMain, Tray, Menu, nativeImage, shell, dialog } = require('electron')
const path = require('path')
const fs = require('fs')
const { spawn, exec } = require('child_process')
const http = require('http')
const url = require('url')

// 前端静态文件服务器端口
const FRONTEND_PORT = 5000
let frontendServer = null

// 开发模式检测
const isDev = !app.isPackaged

// 应用路径
const APP_DATA_PATH = path.join(app.getPath('userData'), 'QuantVision')
const DB_PATH = path.join(APP_DATA_PATH, 'quantvision.db')
const LOGS_PATH = path.join(APP_DATA_PATH, 'logs')

// 后端配置
const BACKEND_PORT = 8000
const BACKEND_URL = `http://localhost:${BACKEND_PORT}`
const BACKEND_HEALTH_URL = `${BACKEND_URL}/api/v1/health/live`

// 后端进程引用
let backendProcess = null

// ============================================================================
// 前端静态文件服务器 (解决 ES modules CORS 问题)
// ============================================================================

/**
 * 启动前端静态文件服务器
 */
function startFrontendServer() {
  return new Promise((resolve, reject) => {
    const distPath = path.join(app.getAppPath(), 'dist')
    console.log('[Frontend Server] 静态文件目录:', distPath)

    // MIME 类型映射
    const mimeTypes = {
      '.html': 'text/html; charset=utf-8',
      '.js': 'application/javascript; charset=utf-8',
      '.mjs': 'application/javascript; charset=utf-8',
      '.css': 'text/css; charset=utf-8',
      '.json': 'application/json; charset=utf-8',
      '.png': 'image/png',
      '.jpg': 'image/jpeg',
      '.jpeg': 'image/jpeg',
      '.gif': 'image/gif',
      '.svg': 'image/svg+xml',
      '.ico': 'image/x-icon',
      '.woff': 'font/woff',
      '.woff2': 'font/woff2',
      '.ttf': 'font/ttf',
      '.eot': 'application/vnd.ms-fontobject',
    }

    frontendServer = http.createServer((req, res) => {
      // 解析请求路径
      let filePath = url.parse(req.url).pathname
      if (filePath === '/' || filePath === '') {
        filePath = '/index.html'
      }

      const fullPath = path.join(distPath, filePath)
      console.log('[Frontend Server] 请求:', req.url, '->', fullPath)

      // 检查文件是否存在
      if (!fs.existsSync(fullPath)) {
        // SPA 回退: 对于非静态资源请求，返回 index.html
        if (!filePath.includes('.')) {
          const indexPath = path.join(distPath, 'index.html')
          if (fs.existsSync(indexPath)) {
            res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' })
            res.end(fs.readFileSync(indexPath))
            return
          }
        }
        console.error('[Frontend Server] 文件不存在:', fullPath)
        res.writeHead(404)
        res.end('Not Found')
        return
      }

      // 读取文件
      const ext = path.extname(fullPath).toLowerCase()
      const contentType = mimeTypes[ext] || 'application/octet-stream'

      try {
        const content = fs.readFileSync(fullPath)
        res.writeHead(200, {
          'Content-Type': contentType,
          'Access-Control-Allow-Origin': '*',
        })
        res.end(content)
      } catch (error) {
        console.error('[Frontend Server] 读取文件错误:', error)
        res.writeHead(500)
        res.end('Internal Server Error')
      }
    })

    frontendServer.listen(FRONTEND_PORT, '127.0.0.1', () => {
      console.log(`[Frontend Server] 运行在 http://127.0.0.1:${FRONTEND_PORT}`)
      resolve()
    })

    frontendServer.on('error', (err) => {
      console.error('[Frontend Server] 启动失败:', err)
      reject(err)
    })
  })
}

/**
 * 停止前端服务器
 */
function stopFrontendServer() {
  if (frontendServer) {
    console.log('[Frontend Server] 停止服务器...')
    frontendServer.close()
    frontendServer = null
  }
}

// 确保数据目录存在
function ensureDirectories() {
  if (!fs.existsSync(APP_DATA_PATH)) {
    fs.mkdirSync(APP_DATA_PATH, { recursive: true })
  }
  if (!fs.existsSync(LOGS_PATH)) {
    fs.mkdirSync(LOGS_PATH, { recursive: true })
  }
}

// ============================================================================
// 后端服务管理
// ============================================================================

/**
 * 检查后端是否已经运行
 */
function checkBackendHealth() {
  return new Promise((resolve) => {
    const options = {
      hostname: '127.0.0.1',  // 使用 IPv4 避免 Windows 上 localhost 解析为 IPv6
      port: BACKEND_PORT,
      path: '/api/v1/health/live',
      method: 'GET',
      timeout: 3000,
    }

    const req = http.request(options, (res) => {
      let data = ''
      res.on('data', (chunk) => { data += chunk })
      res.on('end', () => {
        console.log(`健康检查响应: ${res.statusCode}`)
        resolve(res.statusCode === 200)
      })
    })

    req.on('error', (err) => {
      console.log(`健康检查失败: ${err.message}`)
      resolve(false)
    })

    req.on('timeout', () => {
      console.log('健康检查超时')
      req.destroy()
      resolve(false)
    })

    req.end()
  })
}

/**
 * 等待后端启动完成
 */
async function waitForBackend(maxAttempts = 30, interval = 1000) {
  console.log('等待后端服务启动...')

  for (let i = 0; i < maxAttempts; i++) {
    const isHealthy = await checkBackendHealth()
    if (isHealthy) {
      console.log('后端服务已就绪!')
      return true
    }
    console.log(`等待后端... (${i + 1}/${maxAttempts})`)
    await new Promise(resolve => setTimeout(resolve, interval))
  }

  console.error('后端服务启动超时')
  return false
}

/**
 * 启动后端服务
 */
async function startBackend() {
  // 先检查后端是否已经运行
  const alreadyRunning = await checkBackendHealth()
  if (alreadyRunning) {
    console.log('后端服务已在运行')
    return true
  }

  console.log('启动后端服务...')

  if (isDev) {
    // 开发模式: 使用 Python 运行
    const backendPath = path.join(__dirname, '../../backend')

    if (!fs.existsSync(backendPath)) {
      console.error('后端目录不存在:', backendPath)
      dialog.showErrorBox(
        'QuantVision 启动错误',
        `后端服务目录不存在: ${backendPath}`
      )
      return false
    }

    const pythonCmd = process.platform === 'win32' ? 'python' : 'python3'
    const uvicornArgs = [
      '-m', 'uvicorn',
      'app.main:app',
      '--host', '127.0.0.1',
      '--port', String(BACKEND_PORT),
    ]

    try {
      backendProcess = spawn(pythonCmd, uvicornArgs, {
        cwd: backendPath,
        env: { ...process.env },
        stdio: ['ignore', 'pipe', 'pipe'],
        detached: false,
        shell: true,
      })
    } catch (error) {
      console.error('启动后端失败:', error)
      return false
    }
  } else {
    // 生产模式: 使用打包的 EXE
    const possiblePaths = [
      path.join(process.resourcesPath, 'backend', 'QuantVisionBackend.exe'),
      path.join(path.dirname(app.getPath('exe')), 'backend', 'QuantVisionBackend.exe'),
      path.join(app.getAppPath(), 'backend', 'QuantVisionBackend.exe'),
    ]

    const backendExe = possiblePaths.find(p => fs.existsSync(p))

    if (!backendExe) {
      console.error('后端EXE不存在，尝试的路径:', possiblePaths)
      dialog.showErrorBox(
        'QuantVision 启动错误',
        `后端服务不存在。\n\n尝试的路径:\n${possiblePaths.join('\n')}`
      )
      return false
    }

    console.log('使用后端EXE:', backendExe)

    try {
      backendProcess = spawn(backendExe, [], {
        cwd: path.dirname(backendExe),
        env: { ...process.env, PORT: String(BACKEND_PORT) },
        stdio: ['ignore', 'pipe', 'pipe'],
        detached: false,
      })
    } catch (error) {
      console.error('启动后端EXE失败:', error)
      dialog.showErrorBox(
        'QuantVision 启动错误',
        `无法启动后端服务: ${error.message}`
      )
      return false
    }
  }

  // 记录后端输出
  if (backendProcess.stdout) {
    backendProcess.stdout.on('data', (data) => {
      console.log('[Backend]', data.toString().trim())
    })
  }

  if (backendProcess.stderr) {
    backendProcess.stderr.on('data', (data) => {
      console.error('[Backend Error]', data.toString().trim())
    })
  }

  backendProcess.on('error', (err) => {
    console.error('后端进程错误:', err)
  })

  backendProcess.on('exit', (code, signal) => {
    console.log(`后端进程退出: code=${code}, signal=${signal}`)
    backendProcess = null
  })

  // 等待后端启动完成
  const started = await waitForBackend()
  if (!started) {
    dialog.showErrorBox(
      'QuantVision 启动错误',
      '后端服务启动超时。\n\n请检查数据库服务是否运行。'
    )
    return false
  }

  return true
}

/**
 * 停止后端服务
 */
function stopBackend() {
  if (backendProcess) {
    console.log('停止后端服务...')

    if (process.platform === 'win32') {
      // Windows: 使用 taskkill 终止进程树
      exec(`taskkill /pid ${backendProcess.pid} /T /F`, (err) => {
        if (err) console.error('停止后端失败:', err)
      })
    } else {
      // Unix: 发送 SIGTERM
      backendProcess.kill('SIGTERM')
    }

    backendProcess = null
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
      sandbox: false,  // 关闭沙盒以允许加载本地文件
      webSecurity: false,  // 允许跨域请求（开发用）
    },
  })

  // 加载应用
  if (isDev) {
    // 开发模式: 连接 Vite 开发服务器
    mainWindow.loadURL('http://localhost:5173')
    mainWindow.webContents.openDevTools()
  } else {
    // 生产模式: 使用本地 HTTP 服务器（解决 ES modules CORS 问题）
    console.log('使用本地 HTTP 服务器加载前端')
    console.log('App 路径:', app.getAppPath())
    console.log('Dist 路径:', path.join(app.getAppPath(), 'dist'))
    mainWindow.loadURL(`http://127.0.0.1:${FRONTEND_PORT}`)

    // 打开开发者工具调试（发布时可移除）
    mainWindow.webContents.openDevTools()
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

// 获取后端状态
ipcMain.handle('backend:status', async () => {
  const isHealthy = await checkBackendHealth()
  return {
    running: isHealthy,
    url: BACKEND_URL,
    pid: backendProcess?.pid || null,
  }
})

// 重启后端
ipcMain.handle('backend:restart', async () => {
  stopBackend()
  await new Promise(resolve => setTimeout(resolve, 1000))
  return await startBackend()
})

// ============================================================================
// 应用生命周期
// ============================================================================

app.whenReady().then(async () => {
  ensureDirectories()

  // 创建启动窗口显示加载状态
  const splashWindow = new BrowserWindow({
    width: 400,
    height: 300,
    frame: false,
    transparent: true,
    alwaysOnTop: true,
    skipTaskbar: true,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
    },
  })

  // 显示简单的加载界面
  splashWindow.loadURL(`data:text/html;charset=utf-8,
    <html>
      <head>
        <style>
          body {
            margin: 0;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100vh;
            background: linear-gradient(135deg, #1a1a2e 0%, #0a0a1a 100%);
            color: white;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            border-radius: 12px;
          }
          .title { font-size: 28px; font-weight: bold; margin-bottom: 20px; }
          .status { font-size: 14px; color: #888; margin-top: 20px; }
          .spinner {
            width: 40px;
            height: 40px;
            border: 3px solid #333;
            border-top: 3px solid #4ade80;
            border-radius: 50%;
            animation: spin 1s linear infinite;
          }
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
        </style>
      </head>
      <body>
        <div class="title">QuantVision</div>
        <div class="spinner"></div>
        <div class="status">正在启动服务...</div>
      </body>
    </html>
  `)

  // 启动后端
  console.log('正在启动后端服务...')
  const backendStarted = await startBackend()

  // 生产模式下启动前端静态文件服务器
  if (!isDev) {
    console.log('正在启动前端服务器...')
    try {
      await startFrontendServer()
      console.log('前端服务器启动成功')
    } catch (error) {
      console.error('前端服务器启动失败:', error)
      dialog.showErrorBox('QuantVision 启动错误', `前端服务器启动失败: ${error.message}`)
      app.quit()
      return
    }
  }

  // 关闭启动窗口
  splashWindow.close()

  if (!backendStarted) {
    const response = await dialog.showMessageBox({
      type: 'error',
      title: 'QuantVision',
      message: '后端服务启动失败',
      detail: '是否继续启动应用？（部分功能可能不可用）',
      buttons: ['继续启动', '退出'],
      defaultId: 1,
    })

    if (response.response === 1) {
      app.quit()
      return
    }
  }

  // 创建主窗口
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
  // 停止服务
  stopBackend()
  stopFrontendServer()
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
