/**
 * 番茄小说式分页引擎 —— 公式计算 + 图文混排
 */

/** 估算每页字符数（公式，瞬间） */
export function measurePageCapacity(width, height, fontSize = 18, lineHeight = 1.9) {
  const cols = Math.floor(width / fontSize);
  const rows = Math.floor(height / (fontSize * lineHeight));
  return Math.max(200, Math.floor(cols * rows * 0.75));
}

/** 纯文本分页 */
export function paginateText(text, charsPerPage) {
  const pages = [];
  let offset = 0, pageNum = 1;
  while (offset < text.length) {
    let end = Math.min(offset + charsPerPage, text.length);
    if (end < text.length) {
      const s = text.slice(Math.max(offset + Math.floor(charsPerPage * 0.7), offset), end);
      const bi = s.search(/[\n]{2,}|[。！？.!?\n]/);
      if (bi >= 0) end = Math.max(offset + Math.floor(charsPerPage * 0.7), offset) + bi + 1;
    }
    pages.push({ page: pageNum++, start: offset, end, text: text.slice(offset, end) });
    offset = end;
  }
  return pages;
}

/** 图文混排分页 */
export function paginateContent(blocks, charsPerPage) {
  const IMG_COST = Math.floor(charsPerPage * 0.45);
  const pages = [];
  let cur = { page: 1, blocks: [], chars: 0 };
  for (const b of blocks) {
    if (b.type === 'image') {
      if (cur.chars + IMG_COST > charsPerPage && cur.blocks.length > 0) {
        pages.push(cur); cur = { page: pages.length + 1, blocks: [], chars: 0 };
      }
      cur.blocks.push(b); cur.chars += IMG_COST;
    } else {
      let t = b.value || '';
      while (t.length > 0) {
        const space = charsPerPage - cur.chars;
        if (space <= 8) { pages.push(cur); cur = { page: pages.length + 1, blocks: [], chars: 0 }; continue; }
        const chunk = t.slice(0, space);
        t = t.slice(space);
        cur.blocks.push({ type: 'text', value: chunk }); cur.chars += chunk.length;
        if (t.length > 0) { pages.push(cur); cur = { page: pages.length + 1, blocks: [], chars: 0 }; }
      }
    }
  }
  if (cur.blocks.length > 0) pages.push(cur);
  return pages;
}

/** 字符偏移 → 页码 */
export function getPageFromOffset(pageBreaks, charOffset) {
  for (let i = 0; i < pageBreaks.length; i++)
    if (charOffset < pageBreaks[i].end) return i;
  return pageBreaks.length - 1;
}
