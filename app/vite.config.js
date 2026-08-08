import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { execSync } from 'child_process'

// 获取当前 git commit hash（用于 CDN 缓存自动刷新）
let commitHash = 'master'
try { commitHash = execSync('git rev-parse --short HEAD', { encoding: 'utf-8' }).trim() } catch {}

export default defineConfig({
  define: {
    __COMMIT_HASH__: JSON.stringify(commitHash),
  },
  plugins: [react()],
  base: '/',
  server: {
    port: 5173,
    host: true,
    watch: {
      // 排除 public 海量数据目录（book_chapters 数万小文件），防止批量同步时 watcher 卡死
      // 数据变更只需 F5 刷新（public 静态文件直读磁盘，不走 HMR）
      ignored: [
        '**/public/backend/**',
        '**/public/book_detail/**',
        '**/public/covers/**',
        '**/public/philosopher/**',
        '**/public/schools/**',
        '**/public/gene/**',
        '**/public/icons/**',
      ],
    },
    headers: {
      // dev 必须 no-cache: max-age=3600 会让浏览器缓存模块 1 小时（改代码后 F5 拿旧代码）
      'Cache-Control': 'no-cache',
    },
    proxy: {
      '/api': {
        // 本地开发指向本地后端（book_images 313MB 在本地; 线上 Render 无图片）
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    rollupOptions: {
      output: {
        manualChunks(id) {
          // React 核心库 → vendor chunk (~160KB)
          if (id.includes('node_modules/react/') ||
              id.includes('node_modules/react-dom/') ||
              id.includes('node_modules/react-router/') ||
              id.includes('node_modules/scheduler/')) {
            return 'vendor-react';
          }
          // PDF + EPUB 重型阅读器 → reader chunk (~2MB, 仅阅读页加载)
          if (id.includes('node_modules/pdfjs-dist/') ||
              id.includes('node_modules/react-pdf/') ||
              id.includes('node_modules/epubjs/')) {
            return 'vendor-reader';
          }
          // 其他 node_modules → common vendor
          if (id.includes('node_modules/')) {
            return 'vendor-common';
          }
        },
      },
    },
  },
})
