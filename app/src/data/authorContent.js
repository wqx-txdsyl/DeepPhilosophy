import { fetchSchoolJSON } from './schoolContent.js';

export const AUTHOR_KINDS = { thinker: '哲学家与思想家', context: '历史与文化', tradition: '文本与传统', review: '待核实条目' };
export const authorPath = name => `/author/${encodeURIComponent(name)}`;
export const authorFile = name => `/philosopher/data/${encodeURIComponent(name.replaceAll('/', '-').replaceAll(':', '：'))}.json`;
export const readableBook = book => Number(book?.chapterCount) > 0 && book?.file_type !== 'txt';
const key = text => String(text || '').replace(/[\s·•・.《》〈〉]/g, '').toLocaleLowerCase();
let catalogPromise;
export function loadAuthorCatalog() {
  if (!catalogPromise) catalogPromise = fetchSchoolJSON('/philosopher/catalog.json').catch(error => { catalogPromise = null; throw error; });
  return catalogPromise;
}
export function canonicalAuthor(name, catalog) {
  return catalog?.aliases?.[name] || name;
}
export async function loadAuthorPage(name, signal, { catalogLoader = loadAuthorCatalog, jsonLoader = fetchSchoolJSON, onDetail } = {}) {
  const detail = (async () => {
    let raw = await jsonLoader(authorFile(name), signal);
    if (raw.aliasOf) raw = await jsonLoader(authorFile(raw.aliasOf), signal);
    if (!signal?.aborted) onDetail?.(raw);
    return raw;
  })();
  const [raw, catalog] = await Promise.all([detail, catalogLoader()]);
  return { raw, catalog };
}
export function authorBooks(author, catalog) {
  const matches = (catalog?.books || []).filter(book => key(canonicalAuthor(book.author, catalog)) === key(author.name));
  for (const item of author.books || []) {
    const found = (catalog?.books || []).find(book => (typeof item === 'object' && item.id === book.id) || (key(typeof item === 'string' ? item : item.title) === key(book.title) && key(canonicalAuthor(book.author, catalog)) === key(author.name)));
    if (found && !matches.some(book => book.id === found.id)) matches.push(found);
  }
  return matches.sort((a, b) => Number(readableBook(b)) - Number(readableBook(a)));
}
export function bibliography(author, catalog) {
  const owned = new Set(authorBooks(author, catalog).map(book => key(book.title)));
  const items = [...(author.profile?.bibliography || []), ...(author.books || []).map(item => typeof item === 'string' ? { title: item } : item)];
  return [...new Map(items.filter(item => item?.title && !owned.has(key(item.title))).map(item => [key(item.title), item])).values()];
}
export function normalizeAuthor(raw) {
  const profile = raw.profile || {};
  return { ...raw, listingKind: raw.listingKind || 'thinker', profile: {
    ...profile, overview: Array.isArray(profile.overview) ? profile.overview : String(raw.bio || '').replaceAll('\\n', '\n').split(/\n+/).filter(Boolean),
    life: profile.life || [], concepts: profile.concepts || [], people: profile.people || [], relations: profile.relations || [],
    schoolLinks: profile.schoolLinks || [], sources: profile.sources || raw.sources || [],
  } };
}
