import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import fs from 'node:fs'
import path from 'node:path'

// vite 启动时对 public 目录做预索引（publicFiles Set），启动后新增/新建目录的文件
// 不在索引 → servePublic 跳过 → SPA fallback 返回 HTML（Reader 拿到的 meta 解析失败）
// 本插件在中间件链最前面实时查盘，public 下真实存在的文件直接 serve，新增章节无需重启 vite
const PUBLIC_MIME = {
  '.json': 'application/json', '.webp': 'image/webp', '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg', '.png': 'image/png', '.svg': 'image/svg+xml',
  '.gif': 'image/gif', '.ico': 'image/x-icon', '.pdf': 'application/pdf',
  '.txt': 'text/plain; charset=utf-8', '.html': 'text/html; charset=utf-8',
  '.woff2': 'font/woff2', '.css': 'text/css', '.js': 'application/javascript',
}
function publicLive() {
  return {
    name: 'public-live',
    configureServer(server) {
      // publicDir 是正斜杠（vite normalize），path.join 在 Windows 产生反斜杠 —— normalize 统一后比较
      const base = path.normalize(server.config.publicDir || '')
      server.middlewares.use((req, res, next) => {
        if (!base) return next()
        const url = decodeURIComponent((req.url || '').split('?')[0])
        // 只补 public 目录下真实文件；vite 内部路径/目录请求一律放行
        if (!url.startsWith('/') || url.includes('..') || url.startsWith('/@')) return next()
        const fp = path.normalize(path.join(base, url.replace(/^\//, '')))
        if (!fp.startsWith(base + path.sep)) return next()
        let st
        try { st = fs.statSync(fp) } catch { return next() }
        if (!st.isFile()) return next()
        res.setHeader('Content-Type', PUBLIC_MIME[path.extname(fp).toLowerCase()] || 'application/octet-stream')
        res.setHeader('Cache-Control', 'no-cache')
        res.end(fs.readFileSync(fp))
      })
    },
  }
}

// 部署 commit hash 不再在此内联（2026-08-14 解耦: 由 postbuild.mjs 注入 index.html <meta name="dp-commit">,
// 前端运行时读取; 否则每次 push 都改变 JS 包内容 → 资产 hash 变化 → OSS 未同步即白屏）

// N5（audit 2026-08-18）: 生产构建注入 meta CSP —— Cloudflare Pages 部署无后端响应头,
// meta CSP 是生产强制手段（策略与 backend/main.py 中间件同源, 修改需两处同步）。
// 仅在 build 时注入（apply:'build'）: dev 注入会拦 vite HMR WebSocket(ws://localhost:5173)
// 与用户自配 http://localhost:8000 后端（PHTI 页引用）。script-src 无 'unsafe-inline':
// 启动脚本已外置 public/config-bootstrap.js（同源 'self' 加载）; JSON-LD 为 data block（非可执行脚本,
// CSP3 不拦截, 不占 script-src 额度）; 'unsafe-eval' 从未启用, 构建产物无 eval/new Function
// （2026-08-18 核查 dist assets 0 命中）。style-src 保留 'unsafe-inline'（React 内联 style 属性,
// 组件级限制收益低, 最小可行取舍）。OSS 域保留: 构建脚本/CSS 资产经 postbuild.mjs 改写从 OSS CDN 加载。
function cspMeta() {
  const CSP = [
    "default-src 'self'",
    "script-src 'self' https://deepphilosophy.oss-cn-shanghai.aliyuncs.com",
    "style-src 'self' 'unsafe-inline' https://deepphilosophy.oss-cn-shanghai.aliyuncs.com",
    "img-src 'self' data: blob: https://deepphilosophy.oss-cn-shanghai.aliyuncs.com",
    "connect-src 'self' https:",
    "font-src 'self' data: https://deepphilosophy.oss-cn-shanghai.aliyuncs.com",
    "object-src 'none'; base-uri 'self'; frame-src 'none'; form-action 'self'",
  ].join('; ')
  return {
    name: 'inject-csp-meta',
    apply: 'build',
    transformIndexHtml(html) {
      return html.replace('</head>', `    <meta http-equiv="Content-Security-Policy" content="${CSP}" />\n  </head>`)
    },
  }
}

export default defineConfig(({ mode }) => ({
  plugins: [react(), publicLive(), cspMeta()],
  // 2026-08-11 书架提速: 生产构建产物走 OSS（用户网络对同源 CF 边缘 4-5s/220KB, OSS 0.1s）
  // 注意: vite base 会连带重写 index.html 的 public 引用（favicon/manifest/icons → OSS 404）,
  //       故 base 保持 '/', 改用 postbuild.mjs 构建后只替换 dist/index.html 的 assets 引用为 OSS URL
  //       （public 资源保持同源; 懒加载 chunk 经 mapDeps 递归, hash 以 CF 线上构建为准 → 同步走"抓 CF 产物"）
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
        // 2026-08-14: 忽略编辑器原子写临时文件（.tmpdir/*.tmp）——否则 Windows 原生
        // watcher 对锁定中的临时文件报 EBUSY 直接崩溃 dev server
        '**/.tmpdir/**',
        '**/*.tmp',
        '**/.*.tmp*',
      ],
      // Windows 稳定性兜底: 轮询模式绕开原生 fs.watch 的 EBUSY 崩溃（被忽略目录不轮询, 开销小）
      usePolling: true,
    },
    headers: {
      // dev 必须 no-cache: max-age=3600 会让浏览器缓存模块 1 小时（改代码后 F5 拿旧代码）
      'Cache-Control': 'no-cache',
    },
    proxy: {
      '/api': {
        // 2026-08-14: 统一后端端口 8011（原 8000 为 Render 遗留）
        target: 'http://localhost:8011',
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
          // 其他 node_modules → common vendor
          if (id.includes('node_modules/')) {
            return 'vendor-common';
          }
        },
      },
    },
  },
}))
