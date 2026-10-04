import { classifyBook, BOOK_TOPICS } from './bookLibrary.js';

export function mergeBook(id, catalogBook, detail) {
  if (!catalogBook && !detail?.title) return null;
  return { ...catalogBook, ...detail, id, title: detail?.title || catalogBook?.title || '', author: detail?.author || catalogBook?.author || '', summary: detail?.summary || catalogBook?.summary || '', tags: detail?.tags?.length ? detail.tags : (catalogBook?.tags || []), cover: detail?.cover || catalogBook?.cover || '' };
}
export function normalizeBookToc(book) {
  const original = Array.isArray(book.toc) && book.toc.length ? book.toc : (book.chapterTitles || []);
  return original.map((item, tocIndex) => typeof item === 'string' ? { type: 'chapter', title: item, index: tocIndex, tocIndex } : { ...item, tocIndex }).filter(item => item.title);
}
/** Keep source tocIndex even when nesting, so the reader's &toc anchor remains exact. */
export function groupBookToc(items) {
  const roots = [], stack = [];
  let chapter = null;
  for (const item of items) {
    const node = { ...item, children: [] };
    if (item.type === 'part') {
      const level = Number(item.level) || 0;
      while (stack.length && (Number(stack.at(-1).level) || 0) >= level) stack.pop();
      (stack.at(-1)?.children || roots).push(node); stack.push(node); chapter = null;
    } else if (item.type === 'section' && chapter && item.index === chapter.index) chapter.children.push(node);
    else { (stack.at(-1)?.children || roots).push(node); chapter = item.type === 'section' ? null : node; }
  }
  return roots;
}
export function bookReaderPath(id, item, chapterCount) {
  if (!item || item.type === 'part' || !Number.isInteger(item.index) || item.index < 0 || item.index >= Number(chapterCount)) return null;
  return `/reader/${encodeURIComponent(id)}?ch=${item.index}${item.type === 'section' ? `&toc=${item.tocIndex}` : ''}`;
}
export function resumedChapter(history, id, chapterCount) {
  const saved = Array.isArray(history) ? history.find(entry => entry.bookId === id) : null;
  const page = Number(saved?.page);
  return saved && Number.isFinite(page) && page >= 1 && chapterCount > 0 ? Math.min(Math.floor(page) - 1, chapterCount - 1) : null;
}
export function bookAuthors(author, catalog) {
  const names = catalog?.people?.[catalog?.aliases?.[author] || author] ? [author] : String(author || '').split(/[／/、]/);
  return names.map(name => { name = name.trim(); const canonical = catalog?.aliases?.[name] || name; return { name, canonical, path: catalog?.people?.[canonical] ? `/author/${encodeURIComponent(canonical)}` : null }; }).filter(x => x.name);
}
export function relatedBooks(book, catalog, editorial) {
  const chosen = (editorial?.related || []).map(item => { const found = catalog.find(b => b.id === item.id && b.id !== book.id); return found ? { ...found, reason: item.reason, note: item.note } : null; }).filter(Boolean);
  const topics = classifyBook(book).topics;
  const ranked = catalog.filter(b => b.id !== book.id && !chosen.some(x => x.id === b.id)).map(b => {
    const sameAuthor = b.author === book.author && book.author && !['佚名','合集&概述'].includes(book.author);
    const shared = classifyBook(b).topics.filter(t => topics.includes(t));
    const topic = BOOK_TOPICS.find(t => t.id === shared[0]);
    return { ...b, score: (sameAuthor ? 10 : 0) + shared.length, reason: sameAuthor ? '同一作者' : `同一主题 · ${topic?.label || ''}`, note: sameAuthor ? `继续阅读${b.author}的其他著作。` : `同属“${topic?.label || ''}”阅读主题。` };
  }).filter(b => b.score > 0).sort((a,b) => b.score - a.score || (b.rank || 0) - (a.rank || 0));
  return [...chosen, ...ranked].slice(0,3);
}
