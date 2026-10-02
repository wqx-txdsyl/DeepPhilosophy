// Display prose, not HTML, from a user-editable memory document.
export function memorySections(text = '') {
  const sections = [];
  let current = { title: '', body: '' };
  for (const line of String(text).split('\n')) {
    const heading = line.match(/^#{1,3}\s+(.+)$/);
    if (heading) {
      if (current.body.trim() || current.title) sections.push(current);
      current = { title: heading[1], body: '' };
    } else current.body += (current.body ? '\n' : '') + line;
  }
  if (current.body.trim() || current.title) sections.push(current);
  return sections.map(s => ({ title: s.title, paragraphs: s.body.trim().split(/\n\s*\n/).filter(Boolean) }));
}
export function memoryDirty(profile, text, enabled) {
  return !!profile && (text !== profile.text || enabled !== profile.enabled);
}
