/**
 * 封面 URL 映射 — 模块级预加载，组件渲染时同步读取（零 fetch，零 useEffect）
 * 双轨（2026-08-11）: covers.json 从 OSS 上海拉取（用户网络实测快 ~80ms, 同源 CF 边缘慢 3-6s）
 *   OSS 优先 2.5s 超时 → 同源兜底
 * 用法：import { getCoverUrl } from '../data/coverUrls';
 *       const src = getCoverUrl(bookId); // 同步返回 "/covers/xxx.webp" 或 null
 *       const o = getCoverOssUrl(bookId); // OSS 绝对直链（封面 <img> 用, onError 回退同源）
 */

const OSS_COVER_BASE = 'https://deepphilosophy.oss-cn-shanghai.aliyuncs.com';

let manifest = null;
let loaded = false;
const readyListeners = [];

// manifest 就绪后通知订阅者（首屏封面在就绪前渲染 → 需重渲染拿 src）
function emitReady() {
  readyListeners.forEach(fn => { try { fn(); } catch {} });
}

/** 订阅 manifest 就绪（已就绪则立即回调）— BookCover 用它触发重渲染 */
export function onCoverManifestReady(fn) {
  if (loaded) fn();
  else readyListeners.push(fn);
}

// 立即发起加载（不阻塞渲染）— OSS 优先, 同源兜底
if (typeof window !== 'undefined') {
  const load = async () => {
    try {
      const resp = await fetch(`${OSS_COVER_BASE}/covers.json`, { signal: AbortSignal.timeout(2500) });
      if (resp.ok) {
        manifest = await resp.json();
        loaded = true;
        emitReady();
        return;
      }
    } catch {}
    try {
      const resp = await fetch('/covers.json');
      if (resp.ok) {
        manifest = await resp.json();
        loaded = true;
        emitReady();
      }
    } catch {}
    if (!loaded) { manifest = {}; loaded = true; emitReady(); }
  };
  load();
}

/**
 * 同步获取封面静态路径（同源相对路径，全站通用）
 * - 如果 covers.json 已加载 → 立即返回
 * - 如果尚未加载 → 返回 null（等下次渲染就有了）
 */
export function getCoverUrl(bookId) {
  if (!manifest || !manifest[bookId]) return null;
  return manifest[bookId];
}

/**
 * OSS 绝对直链（书架网格/卡片用, 48×64 缩略图）— 用户网络对 OSS 快, 同源 CF 边缘慢
 * 带 resize 压缩（w_240 足够 2x 显示, 20KB→~5KB/张, 首访 402 张总量 12.7MB→~2MB）
 * 图片加载失败时由组件 onError 回退到同源相对路径
 */
export function getCoverOssUrl(bookId) {
  const rel = getCoverUrl(bookId);
  if (!rel) return null;
  return `${OSS_COVER_BASE}${rel}?x-oss-process=image/resize,w_240`;
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
