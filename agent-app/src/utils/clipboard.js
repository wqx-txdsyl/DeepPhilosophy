/** Preserve user activation on mobile/in-app browsers; never report a false success. */
export function legacyCopyText(text, doc = document) {
  const previous = doc.activeElement;
  const selection = doc.getSelection?.();
  const ranges = selection ? Array.from({length:selection.rangeCount},(_,i)=>selection.getRangeAt(i).cloneRange()) : [];
  const area = doc.createElement('textarea');
  area.value = text; area.readOnly = true;
  area.setAttribute('aria-hidden','true');
  Object.assign(area.style,{position:'fixed',top:'0',left:'0',width:'1px',height:'1px',opacity:'0',fontSize:'16px'});
  doc.body.appendChild(area);
  try {
    area.focus({preventScroll:true}); area.select(); area.setSelectionRange(0,text.length);
    return doc.execCommand?.('copy') === true;
  } catch { return false; }
  finally {
    area.remove();
    previous?.focus?.({preventScroll:true});
    if (selection && ranges.length) { selection.removeAllRanges(); for (const range of ranges) selection.addRange(range); }
  }
}

export async function copyAnswerText(text, { nav = navigator, doc = document } = {}) {
  // Run the selection-based fallback synchronously inside the tap gesture.
  if (legacyCopyText(text,doc)) return true;
  try { if (!nav.clipboard?.writeText) return false; await nav.clipboard.writeText(text); return true; }
  catch { return false; }
}
