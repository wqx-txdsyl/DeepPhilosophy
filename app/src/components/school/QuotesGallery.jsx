import { useEffect, useId, useLayoutEffect, useRef, useState } from 'react';
import './QuotesGallery.css';

export default function QuotesGallery({ quotes = [] }) {
  const [active, setActive] = useState(null);
  const [pinned, setPinned] = useState(false);
  const wrapRef = useRef(null);
  const popoverRef = useRef(null);
  const triggerRefs = useRef(new Map());
  const suppressed = useRef(null);
  const uid = useId();
  const items = quotes.filter(quote => quote?.text);
  const selected = active === null ? null : items[active];

  function show(index, pin = false) {
    if (!pin && (pinned || suppressed.current === index)) return;
    suppressed.current = null;
    setActive(index);
    if (pin) setPinned(true);
  }

  function close(restoreFocus = false) {
    suppressed.current = active;
    setActive(null);
    setPinned(false);
    if (restoreFocus) triggerRefs.current.get(active)?.focus();
  }

  useLayoutEffect(() => {
    const wrap = wrapRef.current;
    const panel = popoverRef.current;
    const anchor = triggerRefs.current.get(active);
    if (!wrap || !panel || !anchor) return;
    function position() {
      const a = anchor.getBoundingClientRect();
      const b = wrap.getBoundingClientRect();
      const p = panel.getBoundingClientRect();
      const left = Math.max(0, Math.min(b.width - p.width, a.left + a.width / 2 - b.left - p.width / 2));
      const top = a.top - b.top > p.height + 16 ? a.top - b.top - p.height - 12 : a.bottom - b.top + 12;
      panel.style.left = `${Math.round(left)}px`;
      panel.style.top = `${Math.round(top)}px`;
    }
    position();
    const observer = new ResizeObserver(position);
    observer.observe(wrap);
    observer.observe(panel);
    return () => observer.disconnect();
  }, [active]);

  useEffect(() => {
    if (active === null) return;
    function outside(event) {
      if (wrapRef.current?.contains(event.target)) return;
      suppressed.current = null;
      setActive(null);
      setPinned(false);
    }
    document.addEventListener('pointerdown', outside);
    return () => document.removeEventListener('pointerdown', outside);
  }, [active]);

  if (!items.length) return null;

  return <section className="school-quotes-section" aria-labelledby={`${uid}-heading`}>
    <div className="school-quotes-heading"><span>Golden quotes</span><h2 id={`${uid}-heading`}>金句</h2></div>
    <div ref={wrapRef} className="school-quotes-wrap"
      onMouseLeave={() => { suppressed.current = null; if (!pinned) setActive(null); }}
      onKeyDown={event => { if (event.key === 'Escape' && active !== null) { event.preventDefault(); close(true); } }}
      onBlur={event => {
        if (!event.currentTarget.contains(event.relatedTarget) && !pinned) setActive(null);
      }}>
      <div className="school-quotes-cloud">
        {items.map((quote, index) => {
          const hash = [...quote.text].reduce((sum, char) => sum + char.charCodeAt(0), 0);
          const fragment = quote.text.length > 24 ? `${quote.text.slice(0, 22)}…` : quote.text;
          const paraphrase = quote.kind === 'paraphrase';
          return <button key={`${index}-${quote.text}`} type="button" className="school-quote-fragment"
            ref={element => { if (element) triggerRefs.current.set(index, element); else triggerRefs.current.delete(index); }}
            style={{ '--quote-size': `${15 + hash % 15}px`, '--quote-tilt': `${(hash % 7 - 3) * 0.55}deg`, '--quote-weight': 300 + hash % 3 * 100 }}
            aria-label={`${quote.text}${quote.author ? ` — ${quote.author}` : ''}${paraphrase ? '，思想概述' : ''}`}
            aria-pressed={pinned && active === index}
            aria-expanded={active === index}
            aria-controls={active === index ? `${uid}-popover` : undefined}
            onMouseEnter={() => show(index)}
            onMouseLeave={() => { if (suppressed.current === index) suppressed.current = null; }}
            onFocus={() => show(index)}
            onBlur={() => { if (suppressed.current === index) suppressed.current = null; }}
            onClick={() => show(index, true)}>
            {paraphrase ? fragment : `“${fragment}”`}
          </button>;
        })}
      </div>
      {selected && <div ref={popoverRef} className="school-quote-popover" id={`${uid}-popover`} role="region" aria-label="金句释义" aria-live={pinned ? 'polite' : 'off'}>
        <button type="button" className="school-quote-close" aria-label="关闭金句释义" onClick={() => close(true)}>×</button>
        {selected.kind === 'paraphrase' && <span className="school-quote-kind">思想概述</span>}
        <blockquote>{selected.kind === 'paraphrase' ? selected.text : `“${selected.text}”`}</blockquote>
        {selected.author && <cite>— {selected.author}</cite>}
        {selected.source && <div className="school-quote-source">{selected.source}</div>}
        {selected.exp && <p>{selected.exp}</p>}
      </div>}
    </div>
  </section>;
}
