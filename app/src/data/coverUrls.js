/**
 * 封面 URL 映射 — 模块级预加载，组件渲染时同步读取（零 fetch，零 useEffect）
 * 用法：import { getCoverUrl } from '../data/coverUrls';
 *       const src = getCoverUrl(bookId); // 同步返回 "/covers/xxx.webp" 或 null
 */

let manifest = null;
let loaded = false;

// 立即发起加载（不阻塞渲染）
if (typeof window !== 'undefined') {
  fetch('/covers.json')
    .then(r => r.ok ? r.json() : {})
    .then(d => { manifest = d; loaded = true; })
    .catch(() => { manifest = {}; loaded = true; });
}

/**
 * 同步获取封面静态路径
 * - 如果 covers.json 已加载 → 立即返回
 * - 如果尚未加载 → 返回 null（等下次渲染就有了）
 */
export function getCoverUrl(bookId) {
  if (!manifest || !manifest[bookId]) return null;
  return manifest[bookId];
}

/**
 * 从 API 格式的 cover URL 提取静态路径
 * "/api/books/{bid}/image/{name}.webp" → "/covers/{name}.webp"
 */
export function toStaticCover(apiUrl) {
  if (!apiUrl) return null;
  if (apiUrl.startsWith('/covers/')) return apiUrl;
  const name = apiUrl.split('/').pop();
  return `/covers/${name}`;
}

export function isCoverLoaded() {
  return loaded;
}
