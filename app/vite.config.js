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
    headers: {
      'Cache-Control': 'public, max-age=3600',
    },
    proxy: {
      '/api': {
        target: 'https://deepphilosophy-7g7m.onrender.com',
        changeOrigin: true,
        secure: true,
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
