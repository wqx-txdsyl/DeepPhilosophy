const atomicTokens = /\{\{n:\d+\}\}|\[IMG\]/g;
const boundary = (text, at) => !(at > 0 && at < text.length
  && /[\uD800-\uDBFF]/.test(text[at - 1]) && /[\uDC00-\uDFFF]/.test(text[at]));

/** Explicit source typography only; invalid metadata never becomes markup. */
export function validSourceInlineStyles(text, styles) {
  if (typeof text !== 'string' || !Array.isArray(styles)) return [];
  const tokens = [...text.matchAll(atomicTokens)].map(m => [m.index, m.index + m[0].length]);
  let end = 0;
  for (const style of styles) {
    if (!style || !['sub', 'sup'].includes(style.kind)
      || !Number.isInteger(style.start) || !Number.isInteger(style.end)
      || style.start < end || style.end <= style.start || style.end > text.length
      || !boundary(text, style.start) || !boundary(text, style.end)
      || tokens.some(([from, to]) => style.start < to && style.end > from)) return [];
    end = style.end;
  }
  return styles;
}

/** Slice by original UTF-16 positions, including across note/image/TOC cuts. */
export function sourceInlineSegments(text, styles, offset = 0) {
  const parts = [];
  let cursor = 0;
  for (const style of styles || []) {
    const start = Math.max(0, style.start - offset), end = Math.min(text.length, style.end - offset);
    if (end <= start) continue;
    if (start > cursor) parts.push({ text: text.slice(cursor, start) });
    parts.push({ text: text.slice(start, end), kind: style.kind });
    cursor = end;
  }
  if (cursor < text.length) parts.push({ text: text.slice(cursor) });
  return parts;
}
