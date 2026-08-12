// postbuild.mjs — 构建后把 dist/index.html 的 assets 引用改写为 OSS URL（书架提速 2026-08-11）
//
// 背景: vite base 指向 OSS 会连带重写 index.html 的 public 资源引用（favicon/manifest/icons → OSS 404）,
//       所以 vite base 保持 '/'，构建完成后只改 assets 引用：
//         <script src="/assets/index-xxx.js">  →  https://deepphilosophy.oss-cn-shanghai.aliyuncs.com/app/assets/index-xxx.js
//       public 资源（favicon/manifest/icons）保持同源，不再 404。
// 注意: OSS 上的 assets 必须与 CF git 构建产物 hash 一致 → 部署流程「push → 等 CF 构建 → 抓 pages.dev 产物传 OSS」，
//       见 _tmp_grab_cf.py 流程 / dp_sync_oss_static.py（本地构建 hash ≠ CF 构建 hash 的坑在记忆 oss-static-dual-track）。
import fs from 'node:fs'
import path from 'node:path'

const OSS_ASSETS = 'https://deepphilosophy.oss-cn-shanghai.aliyuncs.com/app/assets/'
const distDir = path.join(import.meta.dirname, 'dist')

// 1) 改写 index.html 的 assets 引用
const htmlPath = path.join(distDir, 'index.html')
const html = fs.readFileSync(htmlPath, 'utf-8')

const replaced = html
  // 只替换 /assets/ 前缀引用（vite 默认 assets 目录；public 资源引用保持 /favicon.png 等原样）
  .replace(/(src|href)="\/assets\//g, `$1="${OSS_ASSETS}`)
  // 顺带兜底相对引用形式（不应出现, 防御）
  .replace(/(src|href)="(\.\/)?assets\//g, `$1="${OSS_ASSETS}`)

if (replaced === html) {
  console.warn('[postbuild] dist/index.html 未发现 /assets/ 引用, 未做任何替换')
} else {
  const n = (html.match(/(src|href)="\/assets\//g) || []).length
  fs.writeFileSync(htmlPath, replaced)
  console.log(`[postbuild] 已改写 ${n} 处 assets 引用 → ${OSS_ASSETS}`)
}

// 2) 改写构建 CSS 内部 url(/assets/...) — 2026-08-12 自托管字体 @font-face 走这条路,
//    vite 产物里 url() 是绝对路径 /assets/xxx.woff2, 不同源则走 CF 边缘(慢)
let cssReplaced = 0
for (const f of fs.readdirSync(path.join(distDir, 'assets'))) {
  if (!f.endsWith('.css')) continue
  const p = path.join(distDir, 'assets', f)
  const css = fs.readFileSync(p, 'utf-8')
  const out = css.replace(/url\(\/assets\//g, `url(${OSS_ASSETS}`)
  if (out !== css) {
    fs.writeFileSync(p, out)
    cssReplaced += (css.match(/url\(\/assets\//g) || []).length
  }
}
if (cssReplaced > 0) {
  console.log(`[postbuild] 已改写 ${cssReplaced} 处 CSS url() 引用 → ${OSS_ASSETS}`)
}

// 断言 public 资源引用未被改写（回归保护: 若 vite base 再次指向 OSS 会改坏这两处）
for (const probe of ['/favicon.png', '/manifest.json']) {
  if (!replaced.includes(`"${probe}`)) {
    console.error(`[postbuild] ❌ public 引用被改写: 找不到 "${probe}" — 检查 vite.config.js base`)
    process.exit(1)
  }
}
console.log('[postbuild] public 资源引用保持同源 ✓')
