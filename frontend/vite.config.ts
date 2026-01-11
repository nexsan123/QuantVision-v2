import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  // Electron 需要相对路径
  base: './',
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
      },
    },
  },
  build: {
    // 代码分割配置
    rollupOptions: {
      output: {
        manualChunks: {
          // React 核心
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          // UI 库
          'antd-vendor': ['antd', '@ant-design/icons'],
          // 图表库
          'reactflow-vendor': ['reactflow'],
          // 工具库
          'utils-vendor': ['dayjs', 'date-fns'],
        },
      },
    },
    // 提高分块警告阈值
    chunkSizeWarningLimit: 800,
  },
})
