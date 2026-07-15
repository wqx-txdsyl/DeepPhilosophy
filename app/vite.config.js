import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  base: '/',
  server: {
    port: 5173,
    host: true,
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
