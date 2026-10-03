/** One outer title mark; a work named inside another title uses single marks. */
export function formatBookTitle(value) {
  let title = String(value || '').trim();
  if (!title) return '';
  const fullyWrapped = text => {
    if (!text.startsWith('《') || !text.endsWith('》')) return false;
    let depth = 0;
    for (let index = 0; index < text.length; index++) {
      if (text[index] === '《') depth++;
      if (text[index] === '》') depth--;
      if (depth === 0 && index < text.length - 1) return false;
    }
    return depth === 0;
  };
  while (fullyWrapped(title)) title = title.slice(1, -1).trim();
  return `《${title.replaceAll('《', '〈').replaceAll('》', '〉')}》`;
}
