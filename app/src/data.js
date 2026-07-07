/**
 * 数据层 — 云端优先，sessionStorage缓存 + 本地兜底
 */
import { getApiBase } from './App';
import { cacheGet, cacheSet } from './data/cache';

/** 加载书籍列表 — 缓存10分钟，服务器优先，本地兜底 */
export async function loadBooks() {
  // 1. 检查缓存
  const cached = cacheGet('books');
  if (cached?.length) return cached;

  // 2. 优先从服务器获取
  try {
    const resp = await fetch(`${getApiBase()}/api/books`, {
      signal: AbortSignal.timeout(5000),
    });
    if (resp.ok) {
      const data = await resp.json();
      if (data.books?.length) {
        cacheSet('books', data.books);
        return data.books;
      }
    }
  } catch (e) { console.error('Books API unavailable, using local fallback:', e.message); }

  // 2. 兜底：嵌入式本地书目（离线可用）
  try {
    const local = await import('./assets/books.json');
    return local.default?.books || local.books || [];
  } catch (e) {
    console.error('Local books fallback failed:', e);
    return [];
  }
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
    const resp = await fetch(`${getApiBase()}/api/authors/${encodeURIComponent(authorName)}`, {
      signal: AbortSignal.timeout(3000),
    });
    if (resp.ok) return await resp.json();
  } catch (e) { console.error('Author API unavailable:', e.message); }
  const authors = await loadAuthors();
  const a = authors.find(x => x.name === authorName);
  return a ? {
    name: a.name, region: a.region, books: a.books, book_count: a.book_count,
    bio: `${a.name}是${a.region}哲学史上的重要思想家。详情请连接网络后查看。`,
    wiki_url: `https://baike.baidu.com/item/${encodeURIComponent(authorName)}`,
  } : null;
}

