import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate, useLocation, Link } from 'react-router-dom';
import { loadBooks } from '../data';
import CdnImage from '../components/CdnImage';
import { useSEO } from '../utils/seo';
import { loadAuthorCatalog, readableBook } from '../data/authorContent';
import { BOOK_TOPICS, classifyBook } from '../data/bookLibrary';
import { mergeBook, normalizeBookToc, groupBookToc, bookReaderPath, resumedChapter, bookAuthors, relatedBooks } from '../data/bookDetail';
import { BOOK_EDITORIAL } from '../data/bookEditorial';
import './BookDetailPage.css';

async function readDetail(id, signal) {
  const path = `/book_detail/${encodeURIComponent(id)}.json`;
  for (const url of [`https://deepphilosophy.oss-cn-shanghai.aliyuncs.com${path}`, path]) {
    try {
      const response = await fetch(url, { signal: AbortSignal.any([signal, AbortSignal.timeout(4500)]), cache: 'no-cache' });
      if (response.ok) { const value = await response.json(); if (value?.title) return value; }
    } catch { if (signal.aborted) return null; }
  }
  return null;
}
function Cover({ book, hero = false }) {
  const [failed, setFailed] = useState(false);
  return book.cover?.startsWith('/covers/') && !failed
    ? <CdnImage src={book.cover} imageWidth={hero ? 640 : 320} alt={`${book.title}封面`} loading={hero ? 'eager' : 'lazy'} decoding="async" fetchPriority={hero ? 'high' : 'auto'} onError={() => setFailed(true)} />
    : <div className="bd-cover-placeholder"><span>{book.title}</span><small>{book.author}</small></div>;
}
function TocNode({ node, book, depth = 0 }) {
  const href = bookReaderPath(book.id, node, book.chapterCount);
  if (node.type === 'part' || node.children.length) return <details className={node.type === 'part' ? 'dp-part' : 'dp-chapter'} id={`bd-toc-${node.tocIndex}`} open={depth === 0 && node.tocIndex === 0}>
    <summary>{node.title}</summary><div className="bd-toc-children">{href && <Link className="bd-chapter-start" to={href}>从本章开始阅读 ↗</Link>}{node.children.map(child => <TocNode key={child.tocIndex} node={child} book={book} depth={depth+1} />)}</div>
  </details>;
  return <div className={`bd-toc-leaf${node.type === 'section' ? ' bd-toc-section' : ''}`} id={`bd-toc-${node.tocIndex}`}>{href ? <Link to={href}><span>{node.title}</span><span aria-hidden="true">↗</span></Link> : <span>{node.title}</span>}</div>;
}
export default function BookDetailPage() {
  const { bookId } = useParams();
  return <BookDetailContent key={bookId} bookId={bookId} />;
}
function BookDetailContent({ bookId }) {
  const [data, setData] = useState(null), [authors, setAuthors] = useState(null), [retry, setRetry] = useState(0);
  const [selectedConcept, setSelectedConcept] = useState(0);
  const [tocExpanded, setTocExpanded] = useState(false);
  const [history] = useState(() => { try { return JSON.parse(localStorage.getItem('dp_userdata') || '{}').readingHistory || []; } catch { return []; } });
  const navigate = useNavigate(), location = useLocation();
  const tocRef = useRef(null);
  const editorial = BOOK_EDITORIAL[bookId];
  const book = data?.book;
  useSEO(book?.title || '书籍详情', book?.summary || `${book?.author || ''} · 哲学著作与阅读目录`);
  useEffect(() => {
    const controller = new AbortController();
    Promise.allSettled([loadBooks(), readDetail(bookId, controller.signal)]).then(([list, detail]) => {
      if (controller.signal.aborted) return;
      const catalog = list.status === 'fulfilled' && Array.isArray(list.value) ? list.value : [];
      setData({ catalog, book: mergeBook(bookId, catalog.find(b => b.id === bookId), detail.status === 'fulfilled' ? detail.value : null) });
    });
    loadAuthorCatalog().then(value => { if (!controller.signal.aborted) setAuthors(value); }).catch(() => {});
    return () => controller.abort();
  }, [bookId, retry]);
  const libraryReturn = typeof location.state?.libraryReturn === 'string' && /^\/books(?:\?|$)/.test(location.state.libraryReturn) ? location.state.libraryReturn : '/books';
  const returnLink = <Link className="dp-back" to={libraryReturn}>← 返回书库</Link>;
  if (!data) return <div id="dp-book-detail" className="bd-status" role="status"><p className="dp-eyebrow">DeepPhilosophy · Library</p><h1 className="dp-serif">正在翻开书页…</h1></div>;
  if (!book) return <div id="dp-book-detail" className="bd-status">{returnLink}<h1 className="dp-serif">暂时无法打开这本书</h1><p>书目可能暂不可用，请稍后重试。</p><button onClick={() => { setData(null); setRetry(n => n+1); }}>重新加载</button></div>;
  const readable = readableBook(book);
  const flatToc = normalizeBookToc(book), groups = groupBookToc(flatToc);
  const resume = resumedChapter(history, bookId, Number(book.chapterCount));
  const topics = classifyBook(book).topics.map(id => BOOK_TOPICS.find(t => t.id === id)).filter(Boolean);
  const authorLinks = bookAuthors(book.author, authors);
  const concepts = editorial?.concepts || [];
  const concept = concepts[selectedConcept] || concepts[0];
  const conceptTarget = concept && flatToc.find(item => item.type === 'section' && item.index === concept.ch && item.sec === concept.sec);
  const conceptLink = conceptTarget && readable ? bookReaderPath(bookId, conceptTarget, book.chapterCount) : null;
  const related = relatedBooks(book, data.catalog, editorial);
  const sections = [
    { id:'bd-intro', title:'作品简介', en:'About' },
    { id:'bd-concepts', title:concepts.length ? '核心概念' : '阅读线索', en:'Vocabulary' },
    ...(readable && groups.length ? [{ id:'bd-contents', title:'阅读与目录', en:'Reading' }] : []),
    ...(related.length ? [{ id:'bd-related', title:'延伸阅读', en:'Further reading' }] : []),
  ];
  const sectionNumber = id => String(sections.findIndex(s => s.id === id) + 1).padStart(2,'0');
  const overview = editorial?.overview || String(book.summary || '').replaceAll('\\n','\n').split(/\n+/).filter(Boolean);
  const lead = editorial?.lead || (overview[0] ? (overview[0].split('。')[0] + '。') : '从作品出发，走近它所讨论的思想与问题。');
  const routes = (editorial?.routes || []).map(route => ({ ...route, target: flatToc.find(node => node.type === 'part' && node.title === route.part) })).filter(route => route.target);
  function openPart(index) { const target = document.getElementById(`bd-toc-${index}`); if (!target) return; let current = target; while (current && current !== tocRef.current) { if (current.tagName === 'DETAILS') current.open = true; current = current.parentElement; } target.scrollIntoView({ block:'start' }); }
  const readAction = (first = false) => readable ? <Link className="dp-primary" to={`/reader/${encodeURIComponent(bookId)}?ch=${first ? 0 : (resume ?? 0)}`}>{!first && resume !== null ? `继续阅读 · 第 ${resume+1} 章` : first ? '翻开第一章' : '开始阅读'}<span aria-hidden="true">↗</span></Link> : <p className="bd-unavailable">当前仅收录书目资料，正文尚未开放阅读。</p>;
  const heading = (id, en, title) => <div className="dp-section-caption"><small>{sectionNumber(id)} / {en}</small><h2 className="dp-serif">{title}</h2></div>;
  return <article id="dp-book-detail">
    {returnLink}
    <section className="dp-detail-hero"><div className="dp-plinth"><span className="dp-volume-mark" aria-hidden="true">{editorial?.originalTitle || 'LIBRARY'}</span><Cover book={book} hero /><p>DEEP PHILOSOPHY · LIBRARY</p></div><div className="dp-detail-title"><p className="dp-eyebrow">{topics.slice(0,2).map(t=>t.label).join(' / ') || '哲学藏书馆'}</p><h1 className="dp-serif">{book.title}</h1>{editorial?.originalTitle && <p className="dp-original">{editorial.originalTitle}</p>}<div className="dp-detail-author">{authorLinks.map((author,i) => <span key={`${author.name}-${i}`}>{i>0 && ' / '}{author.path ? <Link to={author.path}>{author.name} ↗</Link> : author.name}</span>)}</div><p className="dp-lead">{lead}</p><div className="dp-meta">{editorial?.firstPublished && <span>原著初版 · {editorial.firstPublished}</span>}{readable && <span>{book.chapterCount} 个阅读章节</span>}<span>{readable ? '在线阅读' : '书目资料'}</span></div><div className="dp-actions">{readAction()}{readable && groups.length>0 && <a className="bd-text-link" href="#bd-contents">浏览目录 ↓</a>}</div></div></section>
    <nav className="dp-section-nav" aria-label="书籍详情章节">{sections.map((s,i) => <a key={s.id} href={`#${s.id}`}><small>{String(i+1).padStart(2,'0')}</small>{s.title}</a>)}</nav>
    <section className="dp-detail-section" id="bd-intro">{heading('bd-intro','About','走近这本书')}<div className="dp-prose">{editorial?.opening && <p className="dp-intro-opening">{editorial.opening}</p>}{overview.length ? overview.map((p,i)=><p key={i}>{p}</p>) : <p>这本书的简介尚待整理。可先查看书目信息与相关作品。</p>}{editorial && book.summary && <details className="bd-original-summary"><summary>查看馆藏简介</summary><p>{book.summary}</p></details>}</div></section>
    <section className="dp-concept-section" id="bd-concepts"><div className="dp-concept-heading"><div><p className="dp-eyebrow">{sectionNumber('bd-concepts')} / {concepts.length ? 'Vocabulary' : 'Reading paths'}</p><h2 className="dp-serif">{concepts.length ? '先认识几个词' : '这本书谈到什么'}</h2></div><p>{concepts.length ? '在词义之间，找到进入原文的线索。' : '从主题出发，寻找可以对照阅读的作品。'}</p></div>{concept ? <><div className="dp-concept-terms" role="group" aria-label="核心概念">{concepts.map((item,i) => <button key={item.name} aria-pressed={i===selectedConcept} onClick={() => setSelectedConcept(i)}>{item.name}</button>)}</div><div key={selectedConcept} className="dp-concept-note" aria-live="polite"><div><small>{concept.en}</small><h3 className="dp-serif">{concept.name}</h3></div><div><p>{concept.text}</p>{conceptLink && <Link to={conceptLink}>{concept.link} ↗</Link>}</div></div></> : <div className="bd-topic-links">{topics.length ? topics.map(topic=><Link key={topic.id} to={`/books?topic=${topic.id}`}>{topic.label}<span aria-hidden="true">↗</span></Link>) : <Link to={`/books?q=${encodeURIComponent(book.author)}`}>查看作者相关作品 ↗</Link>}</div>}</section>
    {readable && groups.length>0 && <section className="dp-detail-section" id="bd-contents">{heading('bd-contents','Reading',routes.length ? '从哪里开始' : '沿着目录阅读')}<div>{routes.length>0 && <><div className="dp-reading-routes">{routes.map((route,i)=><button key={route.title} onClick={()=>openPart(route.target.tocIndex)}><span>{String(i+1).padStart(2,'0')}</span><div><strong>{route.title}</strong><p>{route.note}</p></div><b aria-hidden="true">↓</b></button>)}</div><p className="dp-route-note">第一次阅读建议从导论开始；上方入口可定位对应篇章。</p></>}<div className="dp-toc-head"><span>完整目录 · 篇 / 章 / 节</span><button aria-expanded={tocExpanded} onClick={() => { const next = !tocExpanded; tocRef.current?.querySelectorAll('details').forEach(node => { node.open=next; }); setTocExpanded(next); }}>{tocExpanded ? '收起目录' : '展开目录'}</button></div><div ref={tocRef} className="bd-toc">{groups.map(node=><TocNode key={node.tocIndex} node={node} book={book} />)}</div></div></section>}
    {related.length>0 && <section className="dp-continuation" id="bd-related"><header><div><p className="dp-eyebrow">{sectionNumber('bd-related')} / Further reading</p><h2 className="dp-serif">沿着这本书，继续读</h2></div><Link to={libraryReturn}>浏览全部藏书 ↗</Link></header><div className="dp-reading-books">{related.map(item=><Link key={item.id} to={`/book/${item.id}`} state={{ libraryReturn }}><div className="dp-reading-book-art"><Cover book={item} /></div><small>{item.reason}</small><h3 className="dp-serif">{item.title}</h3><p>{item.author}</p><div>{item.note}</div></Link>)}</div><div className="dp-world-links">{authorLinks.filter(a=>a.path).slice(0,2).map(author=><Link key={author.canonical} to={author.path}><small>认识作者</small><span>{author.name} ↗</span></Link>)}{editorial?.school ? <Link to={`/school/${encodeURIComponent(editorial.school)}`}><small>走进思想传统</small><span>{editorial.school} ↗</span></Link> : <Link to="/genealogy"><small>思想之间</small><span>探索哲学谱系 ↗</span></Link>}</div></section>}
    <section className="dp-detail-ending">{(editorial?.atmosphere || book.cover) && <CdnImage src={editorial?.atmosphere || book.cover} imageWidth={1100} alt="" aria-hidden="true" loading="lazy" />}<div><p className="dp-eyebrow">{readable ? 'Return to the text' : 'Continue exploring'}</p><h2 className="dp-serif">{readable ? <>问题的下一步，<br />在书页之中。</> : <>从一本书，<br />走向更多思想。</>}</h2>{readable ? readAction(true) : <Link className="dp-primary" to={libraryReturn}>继续浏览书库 ↗</Link>}</div></section>
    <footer className="dp-bottom"><span>DeepPhilosophy · {book.title}</span><button onClick={() => navigate(libraryReturn)}>回到书库 ↑</button></footer>
  </article>;
}
