import { useId, useLayoutEffect, useMemo, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { ossFallback, ossImg } from '../../data/ossUrls';
import { parseSchoolYear } from '../../data/schoolContent';
import './TimelineSection.css';

const BOOK_TYPES = new Set(['book', 'publication', '著作', '关键著作', '文献']);
const LIFE_TYPES = new Set(['birth', 'death', 'person']);
const TYPE_LABELS = { birth: '诞生', death: '辞世', book: '著作', publication: '著作', idea: '思想', event: '历史事件', era: '时代', person: '人物' };
const FILTERS = [{ id: 'all', label: '全部' }, { id: 'book', label: '著作' }, { id: 'life', label: '人物' }];

function eventPerson(event, thinkers, references) {
  const title = String(event.event || ''), detail = String(event.detail || '');
  const inTitle = thinkers.filter(person => person?.name && title.includes(person.name));
  const candidates = inTitle.length ? inTitle : thinkers.filter(person => person?.name && detail.includes(person.name));
  candidates.sort((a, b) => (inTitle.length ? title.indexOf(a.name) - title.indexOf(b.name) : 0) || b.name.length - a.name.length);
  const person = candidates[0];
  if (!person) return null;
  return { ...person, ...(references.findPerson?.(person.name, person.era) || {}), schoolName: person.name };
}

function eventBook(event, person, references) {
  return references.findBook?.(event.event, person?.name) || null;
}

function yearColor(year) {
  if (year === null) return 'var(--ochre)';
  if (year < 0) return '#a77c4f';
  if (year < 500) return '#a98e53';
  if (year < 1500) return '#738e9a';
  if (year < 1800) return '#ad7770';
  if (year < 1950) return '#778e6a';
  return '#92819d';
}

function EventArtwork({ book, person, kind }) {
  const path = book?.cover || person?.portrait;
  const [failedPath, setFailedPath] = useState(null);
  if (!path || failedPath === path) {
    return <span className="school-river-art-word" aria-hidden="true">{kind === 'book' ? '著述' : kind === 'life' ? '生平' : '思想'}</span>;
  }
  return <img
    className={book?.cover ? 'school-river-book' : 'school-river-portrait'}
    src={path.startsWith('/') ? ossImg(path, { w: 280 }) : path}
    alt={book?.cover ? `《${book.title}》封面` : person.name}
    loading="lazy"
    onError={event => {
      if (!event.currentTarget.dataset.fb && event.currentTarget.src.startsWith('https://deepphilosophy.oss-cn-shanghai.aliyuncs.com/')) ossFallback(event);
      else setFailedPath(path);
    }}
  />;
}

/** A continuous river; each event opens where it is, keeping its historical context. */
export default function TimelineSection({ timeline = [], thinkers = [], references = {}, cihai = [], onSelectPerson, onSelectConcept }) {
  const [filter, setFilter] = useState('all');
  const [openEvent, setOpenEvent] = useState(null);
  const riverRef = useRef(null);
  const svgRef = useRef(null);
  const uid = useId();
  const events = useMemo(() => timeline.filter(event => event?.event).map((event, index) => ({
    ...event,
    index,
    sortYear: parseSchoolYear(event.year),
    kind: BOOK_TYPES.has(event.type) ? 'book' : LIFE_TYPES.has(event.type) ? 'life' : 'event',
  })).sort((a, b) => a.sortYear === null || b.sortYear === null ? a.index - b.index : a.sortYear - b.sortYear || a.index - b.index), [timeline]);
  const visibleEvents = events.filter(event => filter === 'all' || event.kind === filter);

  useLayoutEffect(() => {
    const river = riverRef.current;
    const svg = svgRef.current;
    if (!river || !svg) return;
    function drawRiver() {
      const box = river.getBoundingClientRect();
      if (!box.width || !box.height) return;
      const points = [...river.querySelectorAll('.school-river-node')].map(node => {
        const rect = node.getBoundingClientRect();
        return { x: rect.left + rect.width / 2 - box.left, y: rect.top + rect.height / 2 - box.top };
      });
      if (!points.length) return;
      const mobile = box.width < 500;
      let last = { x: points[0].x, y: 0 };
      let d = `M ${last.x} 0`;
      points.forEach((point, index) => {
        const bend = mobile ? 3 : (index % 2 ? 19 : -19);
        const mid = (last.y + point.y) / 2;
        d += ` C ${last.x + bend} ${mid}, ${point.x - bend} ${mid}, ${point.x} ${point.y}`;
        last = point;
      });
      d += ` C ${last.x + (mobile ? 3 : 17)} ${last.y + 35}, ${last.x - (mobile ? 3 : 17)} ${box.height - 20}, ${last.x} ${box.height}`;
      svg.setAttribute('viewBox', `0 0 ${box.width} ${box.height}`);
      svg.querySelectorAll('path').forEach(path => path.setAttribute('d', d));
    }
    drawRiver();
    const observer = new ResizeObserver(drawRiver);
    observer.observe(river);
    return () => observer.disconnect();
  }, [visibleEvents.length, filter, openEvent]);

  if (!events.length) return null;

  return (
    <section className="school-river-section" aria-labelledby={`${uid}-heading`}>
      <div className="school-river-heading">
        <span className="school-river-eyebrow">Historical timeline</span>
        <h2 id={`${uid}-heading`}>思想史时间轴</h2>
      </div>
      <div className="school-river-filters" aria-label="筛选历史事件">
        {FILTERS.filter(item => item.id === 'all' || events.some(event => event.kind === item.id)).map(item => <button
          type="button" key={item.id} aria-pressed={filter === item.id}
          onClick={() => { setFilter(item.id); setOpenEvent(null); }}
        >{item.label}<span>{item.id === 'all' ? events.length : events.filter(event => event.kind === item.id).length}</span></button>)}
      </div>
      <div className="school-river" ref={riverRef}>
        <svg className="school-river-svg" ref={svgRef} aria-hidden="true" preserveAspectRatio="none">
          <path className="school-river-water" fill="none" />
          <path className="school-river-thread" fill="none" />
        </svg>
        <div className="school-river-events">
          {visibleEvents.map((event, index) => {
            const person = eventPerson(event, thinkers, references);
            const book = eventBook(event, person, references);
            const isOpen = openEvent === event.index;
            const priorYear = visibleEvents[index - 1]?.sortYear;
            const gap = event.sortYear !== null && priorYear != null ? Math.min(64, 15 + Math.sqrt(Math.max(0, event.sortYear - priorYear)) * 6) : 24;
            const relatedTerms = cihai.filter(item => {
              const term = String(item?.term || item?.word || '').split(/[（(]/)[0].trim();
              return term.length > 1 && `${event.event} ${event.detail || ''}`.includes(term);
            }).slice(0, 2);
            return <article key={event.index} data-person={person?.schoolName || ''} data-year={event.sortYear ?? ''} className={`school-river-event${event.kind === 'book' ? ' is-major' : ''}${isOpen ? ' is-open' : ''}`}
              style={{ '--event-gap': `${gap}px`, '--event-color': yearColor(event.sortYear) }}>
              <span className="school-river-node" aria-hidden="true" />
              <div className="school-river-exhibit">
                <button className="school-river-trigger" type="button" aria-expanded={isOpen} aria-controls={`${uid}-event-${event.index}`}
                  onClick={() => setOpenEvent(isOpen ? null : event.index)}>
                  <span className="school-river-year">{event.year || '年代未详'}</span>
                  <span className="school-river-kind">{TYPE_LABELS[event.type] || event.type || '历史事件'}</span>
                  <span className="school-river-title">{event.event}</span>
                  <span className="school-river-cue">{isOpen ? '收起详情 −' : '展开详情 ＋'}</span>
                </button>
                <div id={`${uid}-event-${event.index}`} className="school-river-reveal" inert={!isOpen} aria-hidden={!isOpen}>
                  <div className="school-river-reveal-inner"><div className="school-river-detail">
                    {event.detail && <p>{event.detail}</p>}
                    {(person || book || (onSelectConcept && relatedTerms.length > 0)) && <div className="school-river-actions">
                      {person && onSelectPerson && <button type="button" onClick={() => onSelectPerson(person.schoolName)}>{person.schoolName} · 星图 ↗</button>}
                      {person?.href && !onSelectPerson && <Link to={person.href}>认识{person.schoolName} ↗</Link>}
                      {onSelectConcept && relatedTerms.map(term => <button type="button" key={term.term || term.word} onClick={() => onSelectConcept(term.term || term.word)}>{String(term.term || term.word).split(/[（(]/)[0]} ↗</button>)}
                      {book?.href && <Link to={book.href}>{book.chapterCount > 0 ? '阅读' : '查看'}《{book.title}》 ↗</Link>}
                    </div>}
                  </div></div>
                </div>
              </div>
              <div className="school-river-art">
                <EventArtwork book={book} person={person} kind={event.kind} />
                {(person || book) && <span className="school-river-art-caption">{book?.author || person?.schoolName}</span>}
              </div>
            </article>;
          })}
        </div>
      </div>
    </section>
  );
}
