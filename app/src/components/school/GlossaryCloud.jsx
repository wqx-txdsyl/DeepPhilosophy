import { formatBookTitle } from '../../data/bookTitles';
import { useEffect, useId, useLayoutEffect, useMemo, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import './GlossaryCloud.css';

const plainWord = word => String(word || '').replace(/[（(].*?[)）]/g, '').trim();
const wordKey = word => plainWord(word).replace(/[\s·•—–-]/g, '').toLocaleLowerCase();
const hashWord = word => [...word].reduce((hash, character) => (hash * 31 + character.codePointAt(0)) >>> 0, 0);
function groupTerms(cihai) {
  const groups = new Map();
  cihai.filter(item => item?.word).forEach(item => {
    const key = wordKey(item.word);
    if (!groups.has(key)) groups.set(key, { key, name: plainWord(item.word), items: [] });
    groups.get(key).items.push(item);
  });
  return [...groups.values()];
}

export default function GlossaryCloud({ cihai = [], references, selectedConcept, onSelectConcept, onLocatePerson }) {
  const groups = useMemo(() => groupTerms(cihai), [cihai]);
  const [query, setQuery] = useState('');
  const [activeKey, setActiveKey] = useState(null);
  const [pinned, setPinned] = useState(false);
  const [previousConcept, setPreviousConcept] = useState(undefined);
  const [position, setPosition] = useState({ left: 8, top: 0 });
  const wrapRef = useRef(null);
  const panelRef = useRef(null);
  const wordRefs = useRef(new Map());
  const suppressFocus = useRef(false);
  const suppressHover = useRef(false);
  const suppressionTimer = useRef(null);
  useEffect(() => () => clearTimeout(suppressionTimer.current), []);
  const panelId = useId();
  const active = groups.find(group => group.key === activeKey);
  const item = active?.items[0];
  const matches = groups.filter(group => group.items.some(term => `${term.word} ${term.def || ''} ${term.source || ''}`.toLocaleLowerCase().includes(query.toLocaleLowerCase())));
  // A changed parent selection is consumed once; hover and close remain local afterwards.
  if (previousConcept !== selectedConcept) {
    setPreviousConcept(selectedConcept);
    if (selectedConcept) {
      const key = wordKey(selectedConcept);
      const match = groups.find(group => group.key === key) || groups.find(group => key.length > 1 && (group.key.includes(key) || key.includes(group.key)));
      if (match) { setActiveKey(match.key); setPinned(true); setQuery(''); }
    }
  }
  useLayoutEffect(() => {
    if (!active) return;
    function reposition() {
      const wrap = wrapRef.current;
      const panel = panelRef.current;
      const anchor = wordRefs.current.get(active.key);
      if (!wrap || !panel || !anchor) return;
      const frame = wrap.getBoundingClientRect();
      const box = anchor.getBoundingClientRect();
      const popup = panel.getBoundingClientRect();
      const left = Math.max(8, Math.min(frame.width - popup.width - 8, box.left + box.width / 2 - frame.left - popup.width / 2));
      const above = box.top - frame.top - popup.height - 12;
      const top = above >= 0 && box.bottom + popup.height > window.innerHeight ? above : box.bottom - frame.top + 12;
      setPosition(previous => Math.abs(previous.left - left) < .5 && Math.abs(previous.top - top) < .5 ? previous : { left, top });
    }
    reposition();
    const observer = new ResizeObserver(reposition);
    observer.observe(wrapRef.current);
    if (panelRef.current) observer.observe(panelRef.current);
    window.addEventListener('resize', reposition);
    return () => { observer.disconnect(); window.removeEventListener('resize', reposition); };
  }, [active, query]);
  useEffect(() => {
    if (!activeKey) return;
    const dismiss = event => {
      if (!wrapRef.current?.contains(event.target)) { setActiveKey(null); setPinned(false); }
    };
    document.addEventListener('pointerdown', dismiss);
    return () => document.removeEventListener('pointerdown', dismiss);
  }, [activeKey]);
  function show(group, pin = false) {
    if (!pin && (pinned || suppressHover.current)) return;
    setActiveKey(group.key);
    if (pin) { setPinned(true); onSelectConcept?.(group.name); }
  }
  function close(restoreFocus = false) {
    suppressHover.current = true;
    clearTimeout(suppressionTimer.current);
    suppressionTimer.current = setTimeout(() => { suppressHover.current = false; }, 500);
    if (restoreFocus) {
      suppressFocus.current = true;
      wordRefs.current.get(activeKey)?.focus({ preventScroll: true });
      queueMicrotask(() => { suppressFocus.current = false; });
    }
    setActiveKey(null);
    setPinned(false);
  }
  const sourceTitles = [...String(item?.source || '').matchAll(/《([^》]+)》/g)].map(match => match[1]);
  const sourceBook = sourceTitles.map(title => references?.findBook?.(title)).find(Boolean);
  const original = item?.word.match(/[（(](.*?)[)）]/)?.[1];
  if (!groups.length) return null;
  return <section className="school-glossary" aria-labelledby="school-glossary-title">
    <header className="school-glossary-heading"><div><span className="school-glossary-kicker">A sea of ideas</span><h2 id="school-glossary-title">词海</h2></div><label className="school-glossary-search"><span className="school-glossary-sr">查找词语</span><input type="search" placeholder="查找词语" value={query} onChange={event => { setQuery(event.target.value); setActiveKey(null); setPinned(false); }} /></label></header>
    <div className="school-glossary-wrap" ref={wrapRef} onMouseLeave={() => { if (!pinned) setActiveKey(null); }} onBlur={event => { if (!pinned && !event.currentTarget.contains(event.relatedTarget)) setActiveKey(null); }} onKeyDown={event => { if (event.key === 'Escape' && activeKey) { event.preventDefault(); close(true); } }}>
      <div className="school-glossary-cloud" aria-label="概念词云">
        {matches.map((group, index) => {
          const hash = hashWord(group.name);
          const prominent = index < 4 || hash % 7 === 0;
          const size = Math.max(17, (prominent ? 31 + hash % 9 : 18 + hash % 11) - Math.max(0, group.name.length - 7) * 1.1);
          return <button key={group.key} type="button" ref={element => { if (element) wordRefs.current.set(group.key, element); else wordRefs.current.delete(group.key); }} className={`school-glossary-word ${activeKey && activeKey !== group.key ? 'is-dimmed' : ''}`} style={{ '--word-size': `${size}px`, '--word-angle': `${((hash % 17) - 8) / 5}deg`, '--word-weight': prominent ? 500 : 400 }} aria-label={group.items[0].word} aria-expanded={activeKey === group.key} aria-controls={activeKey === group.key ? panelId : undefined} aria-pressed={pinned && activeKey === group.key} onMouseEnter={() => show(group)} onFocus={() => { if (!suppressFocus.current) show(group); }} onClick={() => show(group, true)}>{group.name}</button>;
        })}
        {!matches.length && <p className="school-glossary-empty">没有找到匹配的词语</p>}
      </div>
      {active && <aside className="school-glossary-popover" id={panelId} ref={panelRef} style={position} aria-label={`${active.name}的释义`} aria-live={pinned ? 'polite' : 'off'}>
        <button className="school-glossary-close" type="button" aria-label="关闭释义" onClick={() => close(true)}>×</button>
        <h3>{active.name}</h3>{original && <div className="school-glossary-original">{original}</div>}
        {item.def && <p className="school-glossary-definition">{item.def}</p>}
        {item.source && <p className="school-glossary-source">{item.source}</p>}
        {active.items.length > 1 && <details className="school-glossary-variants"><summary>其他解释 · {active.items.length - 1}</summary>{active.items.slice(1).map((alternative, index) => <div key={index}><h4>{alternative.word}</h4><p>{alternative.def}</p>{alternative.source && <small>{alternative.source}</small>}</div>)}</details>}
        {sourceBook?.href && <Link to={sourceBook.href} className="school-glossary-book">{sourceBook.cover && <img src={sourceBook.cover} alt="" loading="lazy" onError={event => { event.currentTarget.style.display = 'none'; }} />}<span><strong>{formatBookTitle(sourceBook.title)}</strong>{sourceBook.author && <small>{sourceBook.author}</small>}<em>{sourceBook.chapterCount > 0 ? '打开原典' : '查看书目'} <span aria-hidden="true">↗</span></em></span></Link>}
        {onLocatePerson && item.source && <button className="school-glossary-person" type="button" onClick={() => onLocatePerson(item.source)}>在星图中寻找作者 <span aria-hidden="true">→</span></button>}
      </aside>}
    </div>
  </section>;
}
