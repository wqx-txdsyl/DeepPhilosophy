import { useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { useSEO } from '../utils/seo';
import { fetchSchoolJSON } from '../data/schoolContent';
import { layoutConstellation, constellationCurve } from '../data/schoolConstellationLayout';
import { AUTHOR_KINDS, authorFile, authorPath, authorBooks, bibliography, canonicalAuthor, loadAuthorCatalog, normalizeAuthor, readableBook } from '../data/authorContent';
import './AuthorDetailPage.css';

function Portrait({ person, className = '', priority = false }) {
  const [failed, setFailed] = useState(false);
  if (!person?.portrait || failed) return <div className={`hp-portrait-placeholder ${className}`} aria-label={`${person?.displayName || person?.name || ''}暂无已确认肖像`}><span>{person?.name?.split('·').at(-1)?.slice(0, 2)}</span><small>人物与思想</small></div>;
  return <img className={className} src={person.portrait} alt={`${person.displayName || person.name}肖像`} loading={priority ? 'eager' : 'lazy'} fetchPriority={priority ? 'high' : 'auto'} decoding="async" onError={() => setFailed(true)} />;
}
function HeroVisual({ author, english }) {
  const [failed, setFailed] = useState(false);
  const background = !author.portrait && author.listingKind !== 'review' ? author.profile.schoolLinks[0] : null;
  const useBackground = background && !failed;
  return <figure className="hp-hero-photo">{useBackground ? <img src={background.image} alt={`${background.name}思想背景图`} fetchPriority="high" onError={() => setFailed(true)} /> : <Portrait person={author} priority />}<figcaption className="hp-photo-caption">{useBackground ? `思想背景图 · ${background.name}` : author.listingKind === 'thinker' ? '人物 / 思想 / 原典' : AUTHOR_KINDS[author.listingKind]}</figcaption><span className="hp-photo-edge">{english || 'DEEP PHILOSOPHY'}</span></figure>;
}
function Cover({ book, className }) {
  const [failed, setFailed] = useState(false);
  return book.cover && !failed ? <img className={className} src={book.cover} alt={`《${book.title}》封面`} loading="lazy" onError={() => setFailed(true)} /> : <div className={`hp-cover-placeholder ${className}`}>{book.title}</div>;
}
function Section({ id, title, subtitle, number, children, className = '' }) {
  return <section className={`hp-section ${className}`} id={`hp-${id}`}><header className="hp-section-heading"><span className="hp-chapter-number">{String(number).padStart(2, '0')}</span><div><div className="hp-kicker">{subtitle}</div><h2>{title}</h2></div></header>{children}</section>;
}
function AuthorGraph({ author, catalog }) {
  const profile = author.profile;
  const [page, setPage] = useState(0);
  const [selected, setSelected] = useState(author.name);
  const mapRef = useRef(null);
  const [width, setWidth] = useState(620);
  const allPeople = useMemo(() => profile.people.filter(person => person.name !== author.name && catalog.people[person.name] && catalog.people[person.name].listingKind !== 'review'), [profile.people, author.name, catalog.people]);
  const pages = Math.ceil(allPeople.length / 12);
  const people = useMemo(() => [{ name: author.name, era: author.era, influence: 100, role: '本专题人物', summary: profile.question || '' }, ...allPeople.slice(page * 12, (page + 1) * 12)], [author.name, author.era, profile.question, allPeople, page]);
  const relations = useMemo(() => { const names = new Set(people.map(person => person.name)); return profile.relations.filter(relation => names.has(relation.from) && names.has(relation.to)); }, [people, profile.relations]);
  const layout = useMemo(() => layoutConstellation(people, relations, width, { centerSubject: true }), [people, relations, width]);
  useLayoutEffect(() => {
    const observer = new ResizeObserver(([entry]) => setWidth(Math.max(220, Math.round(entry.contentRect.width))));
    observer.observe(mapRef.current);
    return () => observer.disconnect();
  }, []);
  const chosen = people.find(person => person.name === selected) || people[0];
  const person = { ...catalog.people[chosen.name], ...chosen };
  const nodes = new Map(layout.nodes.map(node => [node.name, node]));
  const contextOnly = relations.every(relation => relation.type === 'context');
  return <><p className="hp-section-note">{contextOnly ? '连线表示共同的思想背景；不表示个人交往或师承。' : '连线保留其所属专题的关系描述；共同思想背景不表示个人交往。点击人物，展开语境与阅读入口。'}</p><div className="hp-relation-layout"><div><div className="hp-map" ref={mapRef} style={{ height: layout.height }}><svg className="hp-map-svg" viewBox={`0 0 ${layout.width} ${layout.height}`} aria-hidden="true">{relations.map((relation, i) => {
    const from = nodes.get(relation.from), to = nodes.get(relation.to);
    return from && to ? <path key={i} d={constellationCurve(from, to)} fill="none" stroke={relation.type === 'reading' ? 'var(--hp-clay)' : 'var(--hp-gold)'} strokeWidth="1.2" opacity={selected === relation.from || selected === relation.to ? .7 : .25} strokeDasharray={relation.type === 'teacher' ? undefined : relation.type === 'reading' ? '2 5' : '6 5'} /> : null;
  })}</svg><div className="hp-node-layer">{layout.nodes.map(node => <button key={node.name} type="button" className={`hp-node ${selected === node.name ? 'is-selected' : ''}`} style={{ left: node.x, top: node.top, width: node.width, '--hp-node-size': `${node.markerSize}px` }} onClick={() => setSelected(node.name)} aria-pressed={selected === node.name}><span className="hp-node-mark">{node.markerSize > 12 ? <Portrait person={catalog.people[node.name]} /> : <i />}</span><strong>{catalog.people[node.name]?.displayName || node.name}</strong><small>{node.era}</small></button>)}</div></div><div className="hp-map-legend">{[...new Set(relations.map(relation => relation.label || relation.type))].map(label => <span key={label}><i />{label}</span>)}</div>{pages > 1 && <div className="hp-graph-pages"><button disabled={page === 0} onClick={() => { setPage(page - 1); setSelected(author.name); }}>← 上一组</button><span>{page + 1} / {pages} · 共{allPeople.length}位相关人物</span><button disabled={page + 1 >= pages} onClick={() => { setPage(page + 1); setSelected(author.name); }}>下一组 →</button></div>}</div><aside className="hp-person" aria-live="polite"><Portrait person={person} className="hp-person-photo" /><div className="hp-person-role">{person.role}</div><h3>{person.displayName || person.name}</h3><div className="hp-person-era">{person.era}</div><p className="hp-person-summary">{person.summary}</p>{person.sourceSchool && <Link className="hp-quiet-action" to={`/school/${encodeURIComponent(person.sourceSchool)}`}>思想背景 · {person.sourceSchool} ↗</Link>}{person.name !== author.name && <Link className="hp-person-link" to={authorPath(person.name)}>进入人物详情 ↗</Link>}</aside></div></>;
}
function ConceptCloud({ concepts, books, onLocate, selection }) {
  const [active, setActive] = useState(selection?.index ?? null);
  const [pinned, setPinned] = useState(Boolean(selection));
  const [position, setPosition] = useState({ left: 8, top: 0 });
  const [query, setQuery] = useState('');
  const wrap = useRef(null), panel = useRef(null), anchors = useRef(new Map()), suppressed = useRef(false), timer = useRef(null);
  useEffect(() => () => clearTimeout(timer.current), []);
  const item = active !== null ? concepts[active] : null;
  useLayoutEffect(() => {
    if (!item) return;
    const reposition = () => {
      const frame = wrap.current?.getBoundingClientRect(), target = anchors.current.get(active)?.getBoundingClientRect(), popup = panel.current?.getBoundingClientRect();
      if (frame && target && popup) setPosition({ left: Math.max(8, Math.min(frame.width - popup.width - 8, target.left + target.width / 2 - frame.left - popup.width / 2)), top: target.bottom - frame.top + 12 });
    };
    reposition();
    window.addEventListener('resize', reposition);
    return () => window.removeEventListener('resize', reposition);
  }, [active, query, item]);
  useEffect(() => {
    const dismiss = event => { if (!wrap.current?.contains(event.target)) { setActive(null); setPinned(false); } };
    document.addEventListener('pointerdown', dismiss);
    return () => document.removeEventListener('pointerdown', dismiss);
  }, []);
  const show = (index, pin = false) => { if (!pin && (pinned || suppressed.current)) return; setActive(index); if (pin) setPinned(true); };
  const close = () => { setActive(null); setPinned(false); suppressed.current = true; clearTimeout(timer.current); timer.current = setTimeout(() => { suppressed.current = false; }, 500); };
  const foundBook = item?.book ? books.find(book => book.id === 'c5013f33fe01') : books.find(book => item?.source?.includes(book.title));
  return <>{concepts.length > 16 && <input className="hp-concept-search" aria-label="查找概念" placeholder="查找概念…" value={query} onChange={event => { setQuery(event.target.value); setActive(null); setPinned(false); }} />}<div className="hp-concept-field" ref={wrap} onKeyDown={event => { if (event.key === 'Escape') close(); }}><div className="hp-concept-cloud">{concepts.map((concept, index) => `${concept.name} ${concept.definition}`.includes(query) && <button ref={element => { if (element) anchors.current.set(index, element); else anchors.current.delete(index); }} key={`${concept.name}-${index}`} style={{ fontSize: `clamp(20px, 4.5vw, ${concept.size || [45, 29, 35, 25, 40][index % 5]}px)`, '--hp-tilt': `${index % 3 - 1}deg` }} aria-pressed={active === index && pinned} onPointerEnter={() => show(index)} onFocus={() => show(index)} onClick={() => show(index, true)}>{concept.name.replace(/[（(].*?[)）]/g, '')}</button>)}</div>{item && <aside className="hp-term-popover" ref={panel} style={position} aria-label="概念释义" aria-live="polite"><button className="hp-close" type="button" aria-label="关闭概念释义" onClick={close}>×</button><h3>{item.name.replace(/[（(].*?[)）]/g, '')}</h3><div className="hp-term-original">{item.original || item.name.match(/[（(](.*)[)）]/)?.[1]}</div><p className="hp-term-definition">{item.definition}</p><div className="hp-term-source">{item.source}</div><div className="hp-life-links">{foundBook && <Link to={`/book/${foundBook.id}`}>回到原典 ↗</Link>}{item.year && <button onClick={() => { close(); onLocate(item.year); }}>在思想路径中定位 →</button>}{item.sourceSchool && <Link to={`/school/${encodeURIComponent(item.sourceSchool)}#school-concepts`}>流派概念 · {item.sourceSchool} ↗</Link>}</div></aside>}</div></>;
}
export default function AuthorDetailPage() {
  const { authorName } = useParams();
  return <AuthorPortraitPage key={authorName} authorName={authorName} />;
}
function AuthorPortraitPage({ authorName }) {
  const [state, setState] = useState({ loading: true });
  const [openEvent, setOpenEvent] = useState(null);
  const [chapter, setChapter] = useState('overview');
  const [night, setNight] = useState(false);
  const [route, setRoute] = useState(0);
  const [conceptSelection, setConceptSelection] = useState(null);
  const eventRefs = useRef(new Map());
  useSEO(state.author?.displayName || state.author?.name || authorName, state.author?.bio?.slice(0, 160) || `${authorName}的思想与著作`);
  useEffect(() => {
    const controller = new AbortController();
    (async () => {
      try {
        const catalog = await loadAuthorCatalog();
        let name = canonicalAuthor(authorName, catalog);
        let raw = await fetchSchoolJSON(authorFile(name), controller.signal);
        if (raw.aliasOf) { name = raw.aliasOf; raw = await fetchSchoolJSON(authorFile(name), controller.signal); }
        if (controller.signal.aborted) return;
        const author = normalizeAuthor(raw);
        setState({ author, catalog, loading: false });
        const preferred = author.profile.life.findIndex(event => String(event.year) === '1927');
        setOpenEvent(preferred >= 0 ? preferred : author.profile.life.length ? 0 : null);
      } catch { if (!controller.signal.aborted) setState({ loading: false, error: true }); }
    })();
    return () => controller.abort();
  }, [authorName]);
  const jump = id => { setChapter(id); document.getElementById(`hp-${id}`)?.scrollIntoView({ behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth', block: 'start' }); };
  const locate = year => {
    const index = state.author.profile.life.findIndex(event => String(event.year) === String(year));
    if (index < 0) return;
    setOpenEvent(index); setChapter('life');
    requestAnimationFrame(() => eventRefs.current.get(index)?.scrollIntoView({ behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth', block: 'center' }));
  };
  if (state.loading) return <div className="loading">正在打开人物专题…</div>;
  if (!state.author) return <div className="page-container hp-error"><h1>暂时无法打开人物资料</h1><p>资料加载失败，请稍后再试。</p><Link to="/authors">返回哲人列表 →</Link></div>;
  const { author, catalog } = state, profile = author.profile;
  const books = authorBooks(author, catalog), otherWorks = bibliography(author, catalog);
  const relatedBooks = (profile.relatedBooks || []).map(id => catalog.books.find(book => book.id === id)).filter(Boolean);
  const displayName = author.displayName || author.name;
  const surname = displayName.includes('·') ? displayName.split('·').at(-1) : displayName;
  const prefix = displayName.includes('·') ? displayName.slice(0, displayName.lastIndexOf('·') + 1) : '';
  const english = profile.englishName || author.englishName || author.bio?.match(/[（(]([A-Za-zÀ-ž][A-Za-zÀ-ž .,'’–-]{3,70})[，,)）]/)?.[1] || '';
  const isReview = author.listingKind === 'review';
  const chapters = [{ id: 'overview', name: '人物', title: isReview ? '资料状态' : author.listingKind === 'tradition' ? '文本与传统' : '人物与思想', subtitle: 'LIFE & WORK' }, ...(profile.life.length && !isReview ? [{ id: 'life', name: '思想路径', title: '思想的路径', subtitle: 'A PATH OF THOUGHT' }] : []), ...(profile.concepts.length && !isReview ? [{ id: 'concepts', name: '概念', title: '概念与语境', subtitle: 'CONCEPTS IN CONTEXT' }] : []), ...(profile.people.length && !isReview ? [{ id: 'relations', name: '关系', title: '思想的关系', subtitle: 'THOUGHT & CONNECTIONS' }] : []), { id: 'works', name: '著述', title: '从著述走入思想', subtitle: 'WORKS & READING' }, ...(profile.debate ? [{ id: 'debate', name: '争议', title: profile.debate.title, subtitle: 'HISTORY & CONTROVERSY' }] : []), { id: 'sources', name: '参考资料', title: '参考资料与阅读', subtitle: 'SOURCES & FURTHER READING' }];
  const section = (id, children, className) => { const data = chapters.find(item => item.id === id); return data ? <Section key={id} {...data} number={chapters.indexOf(data) + 1} className={className}>{children}</Section> : null; };
  return <div id="author-portrait" data-night={night} style={{ '--hp-watermark': JSON.stringify(english || surname) }}><div className="hp-grain" /><div className="hp-shell"><header className="hp-masthead"><Link className="hp-brand" to="/">DeepPhilosophy</Link><nav className="hp-top-links"><Link to="/authors">← 哲人</Link><Link to="/genealogy">思想谱系</Link><button aria-label={night ? '切换日间模式' : '切换夜间模式'} onClick={() => setNight(!night)}>{night ? '日间' : '夜间'}</button></nav></header><section className="hp-hero"><div className="hp-hero-copy"><div className="hp-kicker">{author.listingKind === 'thinker' ? 'PORTRAIT OF A THINKER' : AUTHOR_KINDS[author.listingKind]}</div><h1 className={surname.length > 7 ? 'hp-long-name' : ''}>{prefix && <span>{prefix}</span>}{surname}</h1>{english && <p className="hp-english">{english}</p>}<p className="hp-hero-question">{isReview ? '在可靠的文献中，重新确认他的身份。' : profile.question || author.school?.split(/[/、，;]/).slice(0, 2).join(' · ')}</p><div className="hp-hero-meta"><span>{author.dateKind === 'tradition' ? '神话与传说背景' : isReview ? '身份待核实' : author.era}</span><span>{isReview ? '' : author.country}</span>{profile.schoolLinks.slice(0, 2).map(school => <Link key={school.name} to={`/school/${encodeURIComponent(school.name)}`}>{school.name} ↗</Link>)}</div><div className="hp-hero-actions"><button className="hp-main-action" onClick={() => jump(books.length ? 'works' : 'overview')}>{books.length ? '从著述开始' : '走进人物'} ↘</button>{profile.life.length > 0 && !isReview && <button className="hp-quiet-action" onClick={() => jump('life')}>沿思想路径阅读 →</button>}</div></div><HeroVisual author={author} english={english} /></section><div className="hp-main"><nav className="hp-chapters" aria-label="专题章节">{chapters.map((item, index) => <button key={item.id} onClick={() => jump(item.id)} aria-pressed={chapter === item.id}><small>{['I','II','III','IV','V','VI','VII'][index]}</small>{item.name}</button>)}</nav>
  {section('overview', <div className="hp-reading-grid"><aside className="hp-margin-notes"><p>{AUTHOR_KINDS[author.listingKind]}</p>{!isReview && <p>{author.school?.replaceAll('/', ' / ')}</p>}{profile.schoolLinks.map(school => <p key={school.name}><Link to={`/school/${encodeURIComponent(school.name)}`}>进入{school.name} ↗</Link></p>)}</aside><div className="hp-prose">{isReview ? <><p>{author.reviewReason}</p><p>资料暂缓收录，确认可靠的身份资料后再恢复到哲人名单。</p></> : profile.overview.map((paragraph, index) => <p key={index}>{paragraph}</p>)}{profile.sources.length > 0 && <div className="hp-source-note">{profile.sources.map(source => <a key={source.url} href={source.url} target="_blank" rel="noopener noreferrer">{source.title} ↗ </a>)}</div>}</div></div>)}
  {section('life', <div className="hp-life">{profile.life.map((event, index) => <article ref={element => { if (element) eventRefs.current.set(index, element); }} key={index} data-year={event.year} className={`hp-milestone ${openEvent === index ? 'is-open' : ''}`}><div className="hp-life-year">{event.year}</div><i className="hp-life-dot" /><div><button className="hp-life-trigger" aria-expanded={openEvent === index} aria-controls={`hp-event-${index}`} onClick={() => setOpenEvent(openEvent === index ? null : index)}><span className="hp-life-title">{event.title}</span><small>{openEvent === index ? '收起 −' : '展开 ＋'}</small></button><div className="hp-life-tag">{event.tag || (event.sourceSchool ? `思想背景 · ${event.sourceSchool}` : '')}</div><div className="hp-life-reading" inert={openEvent !== index}><div className="hp-life-inner" id={`hp-event-${index}`}><div className="hp-life-detail">{event.image === 'being' && books[0] && <Cover book={books[0]} />}<div><p>{event.body}</p><div className="hp-life-links">{event.book && <Link to={event.book.replace('https://deepphilosophy.top', '')}>查看原著 ↗</Link>}{event.sourceSchool && <Link to={`/school/${encodeURIComponent(event.sourceSchool)}#school-timeline`}>回到流派时间轴 ↗</Link>}{event.debate && <button onClick={() => jump('debate')}>阅读政治经历与争议 →</button>}{event.term !== undefined && <button onClick={() => { setConceptSelection(previous => ({ index: event.term, revision: (previous?.revision || 0) + 1 })); jump('concepts'); }}>相关概念 · {profile.concepts[event.term]?.name} →</button>}</div></div></div></div></div></div></article>)}</div>)}
  {section('concepts', <ConceptCloud key={conceptSelection?.revision || 0} concepts={profile.concepts} books={books} onLocate={locate} selection={conceptSelection} />)}
  {section('relations', <AuthorGraph key={author.name} author={author} catalog={catalog} />)}
  {section('works', <>{books.map((book, index) => <article className={index === 0 ? 'hp-feature-work' : 'hp-related-work'} key={book.id}><Cover book={book} className={index === 0 ? 'hp-main-cover' : 'hp-related-cover'} /><div><div className="hp-work-type">著作 · {readableBook(book) ? '站内可读' : '书目收录'}</div><h3>《{book.title}》</h3><div className="hp-work-meta">{book.author} {readableBook(book) ? `· 站内${book.chapterCount}章` : ''}</div><div className="hp-work-actions">{readableBook(book) && <Link className="hp-main-action" to={`/reader/${book.id}?ch=0`}>开始阅读 ↗</Link>}<Link className="hp-quiet-action" to={`/book/${book.id}`}>{readableBook(book) ? '查看目录' : '查看书目信息'} →</Link></div></div></article>)}{relatedBooks.map(book => <article className="hp-related-work" key={book.id}><Cover book={book} className="hp-related-cover" /><div><div className="hp-work-type">研究与导读</div><h3>{book.title}</h3><div className="hp-work-meta">{book.author} · {readableBook(book) ? `${book.chapterCount}章` : '书目收录'}</div><Link className="hp-quiet-action" to={`/book/${book.id}`}>打开导读 →</Link></div></article>)}{otherWorks.length > 0 && <div className="hp-bibliography" aria-label="其他著述">{otherWorks.map(work => <details key={work.title}><summary><span>《{work.title}》</span><small>{work.year || '书目'} ＋</small></summary><p>{work.description || '作为相关著述列入书目，站内暂未提供可读版本。'}{work.sourceSchool && <Link to={`/school/${encodeURIComponent(work.sourceSchool)}`}> 来源：{work.sourceSchool} ↗</Link>}</p></details>)}</div>}{!books.length && !otherWorks.length && <div className="hp-uncollected"><p>站内暂未收录{author.listingKind === 'tradition' ? '相关文本的可读版本' : '这位人物的著作'}。</p><Link className="hp-quiet-action" to="/books">浏览哲学书库 →</Link></div>}{profile.readingRoutes && <div className="hp-reading-route"><h4>选择一个阅读起点</h4><div className="hp-route-buttons">{profile.readingRoutes.map((item, index) => <button key={index} aria-pressed={route === index} onClick={() => setRoute(index)}>{item.title} →</button>)}</div><p className="hp-route-note" aria-live="polite">{profile.readingRoutes[route].description}</p></div>}</>)}
  {profile.debate && section('debate', <div className="hp-debate-reading"><div className="hp-debate-year">{profile.debate.year}</div><div>{profile.debate.paragraphs.map((paragraph, index) => <p key={index}>{paragraph}</p>)}<div className="hp-source-note">{profile.sources.filter(source => /大学|斯坦福/.test(source.title)).map(source => <a key={source.url} href={source.url} target="_blank" rel="noopener noreferrer">{source.title} ↗ </a>)}</div></div></div>, 'hp-debate')}
  {section('sources', <><div className="hp-source-grid">{profile.sources.map(source => <a key={source.url} href={source.url} target="_blank" rel="noopener noreferrer">{source.title} ↗</a>)}{profile.schoolLinks.map(school => <Link key={school.name} to={`/school/${encodeURIComponent(school.name)}`}>流派专题 · {school.name}<br />简介、概念与参考资料 ↗</Link>)}{books.map(book => <Link key={book.id} to={`/book/${book.id}`}>DeepPhilosophy 书目<br />《{book.title}》 ↗</Link>)}</div>{!profile.sources.length && <p className="hp-source-note">人物简介整理自站内资料；有明确出处的思想路径与概念，标示其所属流派或著述。</p>}<div className="hp-ending"><p>{author.listingKind === 'thinker' ? '从一个人的思想，走向你的阅读。' : '在文献与历史之间，继续追问。'}</p><Link className="hp-main-action" to={books.find(readableBook) ? `/reader/${books.find(readableBook).id}?ch=0` : profile.schoolLinks[0] ? `/school/${encodeURIComponent(profile.schoolLinks[0].name)}` : '/authors'}>{books.find(readableBook) ? '打开原著' : profile.schoolLinks[0] ? '继续阅读思想背景' : '返回哲人列表'} ↗</Link></div></>, 'hp-sources')}
  <footer className="hp-footer"><span>DeepPhilosophy · {english || author.name}</span><Link to="/authors">人物 / 思想 / 原典</Link></footer></div></div></div>;
}
