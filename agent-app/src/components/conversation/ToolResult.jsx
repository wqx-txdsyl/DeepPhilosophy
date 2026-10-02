import { useMemo, useState } from 'react';
import { ChevronRight, ArrowUpRight } from 'lucide-react';
import { toolResultView } from '../../data/toolResultView';

export function ToolResult({ name, raw, zh = true }) {
  const [expanded, setExpanded] = useState(false);
  const [rawOpen, setRawOpen] = useState(false);
  const view = useMemo(() => toolResultView(name, raw, zh), [name, raw, zh]);
  const shown = expanded ? view.items : view.items.slice(0, 3);
  return <div className="general-tool-result">
    {view.headline && <p className="general-result-headline">{view.headline}</p>}
    {!!view.meta.length && <p className="general-result-meta">{view.meta.join(' · ')}</p>}
    {!!view.warnings.length && <div className="general-result-warning">{view.warnings.map(w => <p key={w}>{w}</p>)}</div>}
    {!!shown.length && <ul className="general-result-items">{shown.map((r, i) => <li key={`${r.url || r.title}:${i}`}>
      {r.title && (r.url ? <a href={r.url} target="_blank" rel="noopener noreferrer">{r.title}<ArrowUpRight size={12} aria-hidden="true" /></a> : <span className="general-result-item-title">{r.title}</span>)}
      {r.meta && <span className="general-result-meta">{r.meta}</span>}
      {r.excerpt && <p className="general-result-excerpt">{r.excerpt}</p>}
    </li>)}</ul>}
    {view.items.length > 3 && <button type="button" className="general-result-more" onClick={() => setExpanded(v => !v)}>{expanded ? (zh ? '收起' : 'Show less') : (zh ? `展开其余 ${view.items.length - 3} 条` : `Show ${view.items.length - 3} more`)}</button>}
    {view.note && <p className="general-result-note">{view.note}</p>}
    {view.rawText && <details className="general-result-raw" onToggle={event => setRawOpen(event.currentTarget.open)}><summary><ChevronRight size={12} aria-hidden="true" />{zh ? '原始返回' : 'Raw return'}</summary>{rawOpen && <pre>{view.rawText}</pre>}</details>}
  </div>;
}
