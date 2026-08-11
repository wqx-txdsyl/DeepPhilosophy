import React from 'react'
import { createRoot } from 'react-dom/client'
import App from './App.jsx'

// PWA: 生产注册 Service Worker（壳缓存 + 网络优先; dev 跳过避免 HMR 干扰）
if (import.meta.env.PROD && 'serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js').catch((err) => console.warn('SW 注册失败:', err.message));
  });
}

createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
