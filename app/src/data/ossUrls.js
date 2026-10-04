/**
 * ossUrls.js — 通用静态资源 OSS 双轨（2026-08-11）
 *
 * 背景: 用户网络访问同源 CF 边缘 3-6s/请求, OSS 上海 0.07-0.15s。
 *       书架（covers/books.json）已双轨; 本 helper 覆盖 schools/（流派图+背景）、gene/（谱系素材）等。
 *
 * 用法:
 *   <img src={ossImg('/schools/xx.webp', { w: 300 })} onError={ossFallback} />
 *   style={{ backgroundImage: `url(${ossImg('/schools/xx.webp', { w: 1280 })})` }}  // 背景无兜底, OSS 极稳可接受
 */
import { SCHOOL_ARTWORK_VERSIONS } from './schoolArtworkVersions.js';

export const OSS_BASE = 'https://deepphilosophy.oss-cn-shanghai.aliyuncs.com';

function versionedImagePath(rel) {
  const [path, query] = rel.split('?');
  const version = SCHOOL_ARTWORK_VERSIONS[path];
  if (!version) return rel;
  const params = new URLSearchParams(query);
  params.set('v', version);
  return `${path}?${params}`;
}

/** OSS 直链（可选 resize 压缩） */
export function ossImg(rel, { w } = {}) {
  const path = versionedImagePath(rel);
  return `${OSS_BASE}${path}${w ? `${path.includes('?') ? '&' : '?'}x-oss-process=image/resize,w_${w}` : ''}`;
}

export function staticImageSources(src, width = 192) {
  const local = src?.startsWith(OSS_BASE + '/') ? src.slice(OSS_BASE.length).split('?')[0] : src;
  if (!local?.startsWith('/') || local.startsWith('//')) return { primary: src, fallback: src };
  return { primary: `${ossImg(local, { w: width })}/format,webp/quality,q_82`, fallback: versionedImagePath(local) };
}

/** <img> onError 兜底: OSS 失败 → 换同源相对路径（只换一次, 已是同源即停） */
export function ossFallback(e) {
  const el = e.currentTarget;
  if (!el || el.dataset.fb) return;
  if (el.src && el.src.startsWith(OSS_BASE)) {
    el.dataset.fb = '1';
    const url = new URL(el.src);
    url.searchParams.delete('x-oss-process');
    el.src = url.pathname + url.search;
  }
}
