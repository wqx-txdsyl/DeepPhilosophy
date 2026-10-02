/**
 * 数据层 — 云端优先，sessionStorage缓存 + 本地兜底
 */
import { fetchSchoolJSON } from './data/schoolContent';
import { authorFile, canonicalAuthor, loadAuthorCatalog } from './data/authorContent';
import { cacheGet, cacheSet } from './data/cache';

/** 加载书籍列表 — OSS 双轨优先（用户网络对 OSS 实测快, 同源 CF 边缘 3-6s），API 不再使用 */
export async function loadBooks() {
  const cached = cacheGet('books');
  if (cached?.length) return cached;
  const tryFetch = async (url, timeout) => {
    try {
      const resp = await fetch(url, timeout ? { signal: AbortSignal.timeout(timeout) } : undefined);
      if (resp.ok) return await resp.json();
    } catch {
      return null;
    }
  };
  const data = (await tryFetch('https://deepphilosophy.oss-cn-shanghai.aliyuncs.com/books.json', 2500))
    || await tryFetch('/books.json');
  if (data && data.length) { cacheSet('books', data); return data; }
  // S19（audit 2026-08-17）：books.json 单一来源 = app/public/books.json（构建时复制进 dist，
  // 与 OSS 双轨）；不再维护 src/assets 本地副本，避免三份元数据漂移。
  return [];
}

/** 根据ID获取书籍 */
export async function getBookById(bookId) {
  const books = await loadBooks();
  return books.find(b => b.id === bookId) || null;
}

/** 获取作者列表 */
export async function loadAuthors() {
  const books = await loadBooks();
  const authors = {};
  books.forEach(b => {
    if (!authors[b.region]) authors[b.region] = {};
    if (!authors[b.region][b.author]) {
      authors[b.region][b.author] = { name: b.author, region: b.region, books: [] };
    }
    authors[b.region][b.author].books.push(b.title);
  });
  const result = [];
  for (const [region, authorMap] of Object.entries(authors)) {
    for (const [name, info] of Object.entries(authorMap)) {
      result.push({ name, region, book_count: info.books.length, books: info.books });
    }
  }
  return result.sort((a, b) => a.region.localeCompare(b.region) || a.name.localeCompare(b.name));
}

export async function getAuthorInfo(authorName) {
  try {
    const catalog = await loadAuthorCatalog();
    return await fetchSchoolJSON(authorFile(canonicalAuthor(authorName, catalog)));
  } catch { return null; }
}
