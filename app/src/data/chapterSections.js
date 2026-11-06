const compact = value => (value || '').replace(/\{\{n:[1-9]\d*\}\}/g, '').replace(/\s/g, '');

// Keep a mapping to the original string: whitespace-tolerant matching must
// still place an anchor between complete source characters.
function titleOffsets(text, title) {
  let joined = '';
  const offsets = [];
  for (let i = 0; i < text.length; i++) {
    if (text.startsWith('{{n:', i)) {
      const note = /^\{\{n:[1-9]\d*\}\}/.exec(text.slice(i));
      if (note) { i += note[0].length - 1; continue; }
    }
    if (/\s/.test(text[i])) continue;
    joined += text[i];
    offsets.push(i);
  }
  const needle = compact(title);
  const result = [];
  if (!needle) return result;
  for (let from = 0; from < joined.length;) {
    const at = joined.indexOf(needle, from);
    if (at < 0) break;
    result.push(offsets[at]);
    from = at + needle.length;
  }
  return result;
}

export function locateChapterSections(content, paragraphs, sections) {
  const byParagraph = new Map();
  const used = new Set();
  let previous = { pi: -1, off: -1 };
  for (const { item, tocIdx } of sections) {
    const needle = compact(item.title);
    if (!needle) continue;
    const validSec = Number.isInteger(item.sec) && item.sec >= 0 && item.sec < content.length;
    const candidates = [];
    paragraphs.forEach((paragraph, pi) => {
      if (typeof paragraph.text !== 'string') return;
      const heading = compact(paragraph.text).replace(/^§/, '') === needle
        || ['section-title', 'chapter-title'].includes(content[paragraph._block]?.role);
      for (const off of titleOffsets(paragraph.text, item.title)) {
        // Numerals such as “一” occur throughout ordinary prose. They are
        // headings only as a complete heading or at an explicit source block.
        if (needle.length < 4 && !heading && !(validSec && paragraph._block === item.sec && off === 0)) continue;
        candidates.push({ pi, off, block: paragraph._block, heading });
      }
    });
    const unused = candidates.filter(c => !used.has(`${c.pi}:${c.off}:${needle}`));
    const pool = unused.length ? unused : candidates;
    const headings = pool.filter(c => c.heading);
    const options = headings.length ? headings : pool;
    const afterPrevious = options.filter(c => c.pi > previous.pi || c.pi === previous.pi && c.off >= previous.off);
    let target = validSec ? options.find(c => c.block === item.sec) : null;
    if (!target) target = afterPrevious[0] || (options.length === 1 ? options[0] : null);
    if (!target && validSec) {
      const pi = paragraphs.findIndex(p => p._block === item.sec && typeof p.text === 'string');
      if (pi >= 0) target = { pi, off: 0 };
    }
    // No title and no usable block means the data needs repair. Never invent
    // a destination by interpolating a percentage through the chapter.
    if (!target) continue;
    if (!byParagraph.has(target.pi)) byParagraph.set(target.pi, []);
    byParagraph.get(target.pi).push({ tocIdx, off: target.off });
    used.add(`${target.pi}:${target.off}:${needle}`);
    previous = target;
  }
  for (const hits of byParagraph.values()) hits.sort((a, b) => a.off - b.off);
  return byParagraph;
}
