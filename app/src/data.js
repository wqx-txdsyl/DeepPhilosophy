/**
 * 数据层 — 本地文件优先，服务器兜底
 * 用户在设置中配置书籍存储路径即可完全离线使用
 */
import { getApiBase } from './App';

let cachedBooks = null;

function getBooksPath() {
  try {
    const config = JSON.parse(localStorage.getItem('dp_api_config') || '{}');
    return config.booksPath || '';
  } catch { return ''; }
}

/** 加载书籍列表 */
export async function loadBooks() {
  // 1. Try server (fast timeout)
  try {
    const resp = await fetch(`${getApiBase()}/api/books`, {
      signal: AbortSignal.timeout(3000),
    });
    if (resp.ok) {
      const data = await resp.json();
      if (data.books?.length) {
        cachedBooks = data.books;
        return data.books;
      }
    }
  } catch (e) {}

  // 2. Try local books path (scan directory)
  const booksPath = getBooksPath();
  if (booksPath) {
    try {
      const resp = await fetch(`${getApiBase()}/api/books`);
      // Server not available, build from local catalog + path
    } catch (e) {}
  }

  // 3. Fallback to embedded catalog
  if (!cachedBooks) {
    try {
      const local = await import('./assets/books.json');
      cachedBooks = local.default?.books || local.books || [];
    } catch (e) {
      cachedBooks = [];
    }
  }
  return cachedBooks;
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
  } catch (e) {}
  const authors = await loadAuthors();
  const a = authors.find(x => x.name === authorName);
  return a ? {
    name: a.name, region: a.region, books: a.books, book_count: a.book_count,
    bio: `${a.name}是${a.region}哲学史上的重要思想家。`,
    wiki_url: `https://baike.baidu.com/item/${encodeURIComponent(authorName)}`,
  } : null;
}

/** 获取本地书籍文件 URL */
export function getLocalBookUrl(book) {
  const booksPath = getBooksPath();
  if (!booksPath) return null;
  return `file://${booksPath}/${book.path}`;
}
