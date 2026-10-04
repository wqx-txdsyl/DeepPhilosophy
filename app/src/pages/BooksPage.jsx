import { useState, useEffect, useMemo, useRef } from 'react';
import { Link, useSearchParams, useLocation } from 'react-router-dom';
import { loadBooks } from '../data';
import CdnImage from '../components/CdnImage';
import { useSEO } from '../utils/seo';
import { BOOK_TOPICS, BOOK_TRADITIONS, BOOK_FORMS, BOOK_REGIONS, prepareLibrary, filterLibrary, sortLibrary } from '../data/bookLibrary.js';
import './BooksPage.css';

const PAGE_SIZE = 24;
const FEATURE_IDS = ['c80947d011a6', 'c5013f33fe01', 'a43cd7310a57'];
function LibrarySearch({ query, onSearch }) {
  const input = useRef(null), composing = useRef(false);
  useEffect(() => { if (!composing.current && input.current.value !== query) input.current.value = query; }, [query]);
  return <label className="dp-search"><span aria-hidden="true">⌕</span><input ref={input} type="search" defaultValue={query} aria-label="搜索书名、作者或主题" placeholder="搜索书名、作者或主题" spellCheck={false}
    onCompositionStart={() => { composing.current = true; }}
    onCompositionEnd={event => { composing.current = false; onSearch(event.currentTarget.value); }}
    onChange={event => { if (!composing.current && !event.nativeEvent.isComposing) onSearch(event.currentTarget.value); }} /></label>;
}
function BookCover({ book, featured = false }) {
  const [failed, setFailed] = useState(false);
  return book.cover?.startsWith('/covers/') && !failed
    ? <CdnImage src={book.cover} imageWidth={featured ? 420 : 320} alt={`${book.title}封面`} loading={featured ? 'eager' : 'lazy'} decoding="async" onError={() => setFailed(true)} />
    : <div className="library-cover-placeholder"><span>{book.title}</span><small>{book.author}</small></div>;
}
export default function BooksPage() {
  const [books, setBooks] = useState([]), [loading, setLoading] = useState(true), [retry, setRetry] = useState(0);
  const [params, setParams] = useSearchParams();
  const browseRef = useRef(null);
  const location = useLocation();
  const bookLinkState = { libraryReturn: location.pathname + location.search };
  useSEO('哲学书库', '浏览哲学经典与研究著作，按思想范围、讨论主题、思想传统与文献类型寻找下一本书。');
  useEffect(() => {
    let cancelled = false;
    loadBooks().then(data => { if (!cancelled) { setBooks(Array.isArray(data) ? data : []); setLoading(false); } }).catch(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [retry]);
  const catalog = useMemo(() => prepareLibrary(books), [books]);
  const filters = { q: params.get('q') || '', topic: params.get('topic') || '', tradition: params.get('tradition') || '', region: params.get('region') || '', form: params.get('form') || '', readable: params.get('readable') === '1' };
  const order = params.get('sort') || 'curated', view = params.get('view') === 'list' ? 'list' : 'grid';
  const filtered = sortLibrary(filterLibrary(catalog, filters), order);
  const pages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const page = Math.min(pages, Math.max(1, Number.parseInt(params.get('page'), 10) || 1));
  const visible = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);
  const featureBooks = FEATURE_IDS.map(id => books.find(b => b.id === id)).filter(Boolean);
  const hasFilters = Object.values(filters).some(Boolean);
  function change(key, value) {
    setParams(previous => { const next = new URLSearchParams(previous); if (value) next.set(key, value); else next.delete(key); if (key !== 'page' && key !== 'view' && key !== 'filters') next.delete('page'); return next; }, { replace: true, preventScrollReset: true });
  }
  function clear() { setParams(view === 'list' ? { view: 'list' } : {}, { replace: true, preventScrollReset: true }); }
  function turnPage(next) { change('page', String(next)); browseRef.current?.scrollIntoView({ block: 'start' }); }
  function facetSelect(key, label, definitions, field) {
    const peers = filterLibrary(catalog, { ...filters, [key]: '' });
    return <label className="library-facet"><span>{label}</span><select aria-label={label} value={filters[key]} onChange={e => change(key, e.target.value)}><option value="">全部{label}</option>{definitions.map(f => {
      const total = catalog.filter(b => b.facets[field].includes(f.id)).length;
      const count = peers.filter(b => b.facets[field].includes(f.id)).length;
      return total > 0 ? <option key={f.id} value={f.id} disabled={!count && filters[key] !== f.id}>{f.label} · {count}</option> : null;
    })}</select></label>;
  }
  return <div id="dp-library-page">
    <header className="dp-library-intro"><div><p className="dp-eyebrow">The philosophy library</p><h1 className="dp-serif">书 库</h1><p className="dp-muted">在书页之间，与思想相遇。</p></div><div className="dp-edition"><em>A place for a slower thought.</em><p className="dp-muted">{loading ? '正在整理藏书…' : `${books.length} 部馆藏 · ${catalog.filter(b => b.facets.readable).length} 部可在线阅读`}</p></div></header>
    {!hasFilters && <section className="dp-feature" aria-label="本期选读"><div className="dp-feature-copy"><p className="dp-eyebrow">本期选读 / 存在与生活</p><h2 className="dp-serif">我们如何<br />成为我们自己？</h2><p>从日常生活出发，走近此在、自由与荒诞。让一个问题，带你进入一本书。</p><Link className="dp-link" to="/book/c5013f33fe01" state={bookLinkState}>翻开《存在与时间》<span aria-hidden="true">↗</span></Link></div><div className="dp-still-life">{featureBooks.map(book => <Link key={book.id} to={`/book/${book.id}`} state={bookLinkState} aria-label={`查看《${book.title}》`}><BookCover book={book} featured /></Link>)}</div></section>}
    <section className="dp-browse" ref={browseRef} aria-label="浏览藏书"><div className="dp-browse-head"><h2 className="dp-serif">浏览藏书</h2><LibrarySearch query={filters.q} onSearch={q => change('q', q)} /></div>
      <div className="dp-filters"><div className="dp-pills" role="group" aria-label="快捷主题">{[{ id: '', label: '全部' }, ...BOOK_TOPICS.slice(0,3)].map(f => <button type="button" key={f.id} aria-pressed={filters.topic === f.id} onClick={() => change('topic', f.id)}>{f.label}</button>)}</div><select className="dp-select" aria-label="所有主题" value={filters.topic} onChange={e => change('topic', e.target.value)}><option value="">所有主题</option>{BOOK_TOPICS.map(f => <option key={f.id} value={f.id}>{f.label}</option>)}</select></div>
      <details className="library-filter-details" open={params.get('filters') === 'open'}><summary onClick={event => { event.preventDefault(); change('filters', params.get('filters') === 'open' ? '' : 'open'); }}>细分筛选 <span>{[filters.region, filters.tradition, filters.form, filters.readable].filter(Boolean).length || ''} {params.get('filters') === 'open' ? '−' : '＋'}</span></summary><div className="library-facet-grid">{facetSelect('region','思想范围',BOOK_REGIONS,'regions')}{facetSelect('tradition','思想传统',BOOK_TRADITIONS,'traditions')}{facetSelect('form','文献类型',BOOK_FORMS,'forms')}<label className="library-readable"><input type="checkbox" checked={filters.readable} onChange={e => change('readable', e.target.checked ? '1' : '')} />仅看可在线阅读</label></div><p className="library-filter-note">一本书可涉及多个主题与传统；未标注传统的作品仍收录在“全部”中。</p></details>
      {hasFilters && <div className="library-active-filters"><span>当前筛选</span>{filters.q && <button onClick={() => change('q','')}>“{filters.q}” ×</button>}{[['topic',BOOK_TOPICS],['region',BOOK_REGIONS],['tradition',BOOK_TRADITIONS],['form',BOOK_FORMS]].map(([key,defs]) => filters[key] && <button key={key} onClick={() => change(key,'')}>{defs.find(f => f.id === filters[key])?.label || filters[key]} ×</button>)}{filters.readable && <button onClick={() => change('readable','')}>可在线阅读 ×</button>}<button onClick={clear}>清除筛选</button></div>}
      <div className="dp-results-head"><p aria-live="polite">{loading ? '加载馆藏…' : `${filtered.length} 部作品${filtered.length ? ` · ${1+(page-1)*PAGE_SIZE}–${Math.min(page*PAGE_SIZE,filtered.length)}` : ''}`}</p><div className="library-display-controls"><select className="dp-select" aria-label="书籍排序" value={order} onChange={e => change('sort',e.target.value)}><option value="curated">精选优先</option><option value="title">按书名</option><option value="author">按作者</option></select><div className="dp-views" role="group" aria-label="显示方式"><button aria-pressed={view==='grid'} onClick={() => change('view','')}>封面陈列</button><button aria-pressed={view==='list'} onClick={() => change('view','list')}>目录列表</button></div></div></div>
      {loading ? <div className="dp-empty" role="status">正在打开书库…</div> : books.length === 0 ? <div className="dp-empty"><h3>暂时无法加载书库</h3><button onClick={() => { setLoading(true); setRetry(n => n+1); }}>重新加载</button></div> : filtered.length === 0 ? <div className="dp-empty"><h3>没有找到相符的书籍</h3><p>试试其他关键词，或减少筛选条件。</p><button onClick={clear}>清除筛选</button></div> : <div className="dp-books" data-view={view}>{visible.map(book => <Link className="dp-book" key={book.id} to={`/book/${book.id}`} state={bookLinkState}><div className="dp-book-art"><BookCover book={book} /></div><div><h3>{book.title}</h3><p className="dp-author">{book.author}</p><p className="dp-category">{book.facets.topics.slice(0,2).map(id => BOOK_TOPICS.find(f => f.id === id)?.label).join(' · ')}</p>{view==='list' && book.summary && <p className="dp-excerpt">{book.summary}</p>}<span className="library-book-status">{book.facets.readable ? '可在线阅读' : '书目资料'}</span></div></Link>)}</div>}
      {pages > 1 && <nav className="library-pagination" aria-label="书库分页"><button disabled={page===1} onClick={() => turnPage(page-1)}>← 上一页</button><label>第 <select className="dp-select" aria-label="选择页码" value={page} onChange={e => turnPage(Number(e.target.value))}>{Array.from({ length: pages },(_,i) => <option key={i+1} value={i+1}>{i+1}</option>)}</select> / {pages} 页</label><button disabled={page===pages} onClick={() => turnPage(page+1)}>下一页 →</button></nav>}
    </section><footer className="dp-bottom"><span>DeepPhilosophy · 哲学藏书馆</span><Link to="/genealogy">沿着思想谱系继续探索 ↗</Link></footer>
  </div>;
}
