import { ossImg } from './ossUrls.js';

const text = value => typeof value === 'string' ? value.trim() : '';
const objects = value => Array.isArray(value) ? value.flat(Infinity).filter(item => item && typeof item === 'object' && !Array.isArray(item)) : [];
const key = value => text(value).replace(/[《》〈〉「」『』\s·・.，,:：！!？?。]/g, '').toLocaleLowerCase();

export function schoolWorkTitles(value) {
  if (Array.isArray(value)) return value.flat().map(item => typeof item === 'string' ? item : item?.title).filter(Boolean);
  if (typeof value !== 'string' || !value.trim()) return [];
  try { const parsed = JSON.parse(value); if (Array.isArray(parsed)) return schoolWorkTitles(parsed); } catch { /* Legacy Python list strings. */ }
  if (/^\s*\[/.test(value)) return [...value.matchAll(/['"]([^'"]+)['"]/g)].map(match => match[1]);
  return value.split(/[、;；]/).map(title => title.trim()).filter(Boolean);
}

/** Earliest stated year; BCE stays negative. Unknown dates remain unknown. */
export function parseSchoolYear(value) {
  const raw = String(value ?? '').replaceAll('－', '-').replaceAll('—', '-');
  const isBCE = /(?:公元)?前\s*\d|\b(?:BCE?|B\.?C\.?)\b/i.test(raw) || /^\s*-\d/.test(raw);
  const match = raw.match(/\d{1,4}/);
  if (!match) return null;
  const n = Number(match[0]);
  if (/世纪|centur/i.test(raw)) return isBCE ? -n * 100 : (n - 1) * 100 + 1;
  return isBCE ? -n : n;
}

export function normalizeSchool(raw = {}) {
  const list = field => objects(raw[field]);
  return {
    ...raw, name: text(raw.name), overview: text(raw.overview), conclusion: text(raw.conclusion),
    thinkers: list('thinkers').filter(item => text(item.name)).map(item => ({ ...item, name: text(item.name), works: schoolWorkTitles(item.works) })),
    relations: list('relations').filter(item => text(item.from) && text(item.to)),
    timeline: list('timeline').filter(item => text(item.event)).map((item, index) => ({ ...item, _order: index })).sort((a, b) => (parseSchoolYear(a.year) ?? Infinity) - (parseSchoolYear(b.year) ?? Infinity) || a._order - b._order),
    cihai: list('cihai').filter(item => text(item.word) && text(item.def)),
    quotes: list('quotes').filter(item => text(item.text)),
    works: list('works').filter(item => text(item.title)),
    subSchools: objects(Array.isArray(raw.subSchools) ? raw.subSchools : Object.values(raw.subSchools || {})).filter(item => text(item.name)),
    sources: list('sources').filter(item => /^https?:\/\//.test(item.url || '')),
  };
}

export function buildSchoolReferences({ books = [], philosophers = [], schools = [], aliases: personAliases = {} } = {}) {
  const people = Array.isArray(philosophers) ? philosophers : Object.entries(philosophers).map(([name, item]) => ({ ...item, name }));
  const exactPeople = new Map(people.map(person => [key(person.name), person]));
  const spellingAliases = { '埃马纽埃尔·列维纳斯': '伊曼纽尔·列维纳斯', '爱德蒙德·胡塞尔': '埃德蒙德·胡塞尔' };
  const aliases = new Map();
  for (const person of people) {
    const last = person.name.split(/[·・]/).at(-1);
    if (last !== person.name && last.length >= 2) aliases.set(key(last), [...(aliases.get(key(last)) || []), person]);
  }
  const findPerson = (name, era) => {
    const canonical = exactPeople.get(key(personAliases[name] || spellingAliases[name] || name));
    const matches = aliases.get(key(name)) || [];
    const person = canonical || (matches.length === 1 ? matches[0] : null);
    if (!person) return null;
    const statedYear = parseSchoolYear(era), catalogYear = parseSchoolYear(person.era);
    if (statedYear !== null && catalogYear !== null && Math.abs(statedYear - catalogYear) > 200) return null;
    return { ...person, href: person.href || `/author/${encodeURIComponent(person.name)}`, portrait: person.portrait || null };
  };
  const bookMap = new Map();
  for (const book of books) bookMap.set(key(book.title), [...(bookMap.get(key(book.title)) || []), book]);
  const findBook = (value, author) => {
    const raw = String(value || ''), titles = [raw];
    for (const match of raw.matchAll(/[《〈]([^》〉]+)[》〉]/g)) {
      const suffix = raw.slice(match.index + match[0].length).trim();
      if (!suffix || /^(?:出版|问世|发表|完成|初版|再版|出版发行)[。．.!！]?$/.test(suffix)) titles.push(match[1]);
    }
    const authorKey = key(findPerson(author)?.name || author);
    for (const title of titles) {
      let candidates = [...(bookMap.get(key(title)) || [])];
      if (authorKey) candidates = candidates.filter(book => key(book.author) === authorKey || key(findPerson(book.author)?.name) === authorKey);
      if (!candidates.length) continue;
      candidates.sort((a, b) => Number(b.chapterCount > 0) - Number(a.chapterCount > 0) || Number(b.file_type !== 'txt') - Number(a.file_type !== 'txt'));
      const book = candidates[0];
      return { ...book, href: `/book/${encodeURIComponent(book.id)}` };
    }
    return null;
  };
  const schoolMap = new Map(schools.map(school => [school.name, school]));
  return { findPerson, findBook, findSchool: name => schoolMap.get(name) || null };
}

export async function fetchSchoolJSON(path, signal) {
  const urls = import.meta.env?.DEV ? [path, ossImg(path)] : [ossImg(path), path];
  for (const url of urls) {
    try {
      const timeout = AbortSignal.timeout(6500);
      const response = await fetch(url, { signal: signal ? AbortSignal.any([signal, timeout]) : timeout, cache: 'no-cache' });
      if (!response.ok) throw new Error(`School data ${response.status}`);
      return await response.json();
    } catch (error) { if (signal?.aborted) throw error; }
  }
  throw new Error('School data unavailable');
}
