const normal = value => String(value || '').replace(/[\s《》·・—–]/g, '').trim();
const chineseNumber = value => {
  if (/^\d+$/.test(value)) return Number(value);
  const digits = {零:0,〇:0,一:1,二:2,两:2,三:3,四:4,五:5,六:6,七:7,八:8,九:9};
  let total = 0, digit = 0;
  for (const char of value) {
    if (char in digits) digit = digits[char];
    else if (char === '十' || char === '百' || char === '千') { total += (digit || 1) * ({十:10,百:100,千:1000}[char]); digit = 0; }
    else return null;
  }
  return total + digit;
};

export function parsePrimaryReference(value) {
  if (!((value.startsWith('【') && value.endsWith('】')) || (value.startsWith('[') && value.endsWith(']')))) return null;
  const m = value.slice(1,-1).trim().match(/^《((?:[^《》\n]|《[^《》\n]*》)+)》\s*[·・]?\s*(.*)$/);
  return m ? {book:m[1].trim(), chapter:m[2].trim()} : null;
}

function locator(value) {
  const s = String(value || '').trim();
  const range = s.match(/^(?:§+\s*|第\s*)?(\d+)\s*[-—–~]\s*§*\s*(\d+)\s*节?$/);
  if (range && (/§/.test(s) || /节$/.test(s))) return {unit:'节', lo:Number(range[1]), hi:Number(range[2])};
  const section = s.match(/^§+\s*(\d+)$/);
  if (section) return {unit:'节',lo:Number(section[1]),hi:Number(section[1])};
  const named = s.match(/^第\s*([\d一二三四五六七八九十百千零〇两]+)\s*([章卷篇节编讲部])/);
  if (named) { const n=chineseNumber(named[1]); return {unit:named[2],lo:n,hi:n}; }
  const numbered = s.match(/^(\d+)(?:\s|[.、]|$)/);
  return numbered ? {unit:'章',lo:Number(numbered[1]),hi:Number(numbered[1])} : null;
}

export function primaryChapterMatches(actual, requested) {
  if (!requested) return true;
  if (normal(actual) === normal(requested)) return true;
  const a=locator(actual), b=locator(requested);
  return !!(a && b && a.unit===b.unit && a.lo <= b.lo && b.hi <= a.hi);
}

export function findPrimaryCitation(citations, reference) {
  const matches=(citations || []).filter(c => c.used !== false && !['web','scholarly','secondary'].includes(c.source_type)
    && !c.source_record_id && !c.doi && normal(c.book || c.work || c.title) === normal(reference.book)
    && primaryChapterMatches(c.chapter,reference.chapter));
  const unique=new Map(matches.map(c => [`${c.book_id || c.book}:${c.chapter_idx ?? c.chapter}`,c]));
  return unique.size === 1 ? [...unique.values()][0] : null;
}
