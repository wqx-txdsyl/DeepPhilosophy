export function getApiBase() {
  return '';  // 同源（vite proxy /api → 8011，见 vite.config.js）
}

/** 肖像/头像 CDN（philosopher 肖像只存在于 OSS, 8011 本地不托管 92MB 全量肖像） */
export const PORTRAIT_CDN = 'https://deepphilosophy.oss-cn-shanghai.aliyuncs.com';

/** 相对肖像路径 → OSS 绝对地址（已绝对化/非 philosopher 路径原样返回） */
export function resolvePortrait(url) {
  if (!url || /^https?:\/\//.test(url) || !url.startsWith('/philosopher/')) return url;
  return PORTRAIT_CDN + url;
}

/** 阅读器跳转基址（引用来源面板与正文【出处】链接共用） */
export const DP_READER = 'https://deepphilosophy.top/reader';

/** 引用跳转解析（/api/cite）: 成功 {book_id, chapter_idx, matched,...} / 失败 {error} */
export async function resolveCite(book, chapter = '') {
  const r = await fetch(`${getApiBase()}/api/cite?book=${encodeURIComponent(book)}&chapter=${encodeURIComponent(chapter || '')}`);
  return r.json();
}
