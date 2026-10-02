import { useEffect, useMemo, useRef, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { createPortal } from 'react-dom';
import { ossImg, ossFallback } from '../data/ossUrls';
import { useSEO } from '../utils/seo';
import { QUESTIONS, TRADITIONS, schoolTopics, filterSchools, schoolPath, riverLayout, constellationLayout, visibleEdges } from '../data/genealogyAtlas';
import { loadGenealogyCatalog } from '../data/genealogyCatalog';
import './GenealogyPage.css';

const MODES = [{ id: 'time', title: '按时间' }, { id: 'relation', title: '按关联' }, { id: 'question', title: '按问题' }];
const HEADINGS = { time: ['思想长河', 'THE RIVER OF THOUGHT'], relation: ['思想星图', 'CONSTELLATIONS OF THOUGHT'], question: ['思想之问', 'QUESTIONS OF PHILOSOPHY'] };
const QUICK_QUESTIONS = ['being', 'knowledge', 'freedom', 'justice', 'faith', 'nature', 'technology', 'colonialism'];

function SchoolArtwork({ node, selected, related, focused, onSelect, onHover }) {
  const school = node.school;
  return (
    <button type="button" className={`atlas-node${selected ? ' is-selected' : ''}${focused && !related ? ' is-muted' : ''}`}
      data-school-id={school.id} aria-label={`${school.name}，${school.century}`} aria-pressed={selected} onClick={() => onSelect(school.id)}
      onMouseEnter={() => onHover(school.id)} onMouseLeave={() => onHover(null)}
      onFocus={() => onHover(school.id)} onBlur={() => onHover(null)}
      style={{ left: node.x, top: node.y, width: node.width, height: node.height }}>
      <span className="atlas-artwork"><img key={school.id} src={ossImg(school.image, { w: 380 })} alt="" loading="lazy" decoding="async" onError={ossFallback} /><span className="atlas-artwork-mark" aria-hidden="true">已选</span></span>
      <span className="atlas-school-name">{school.name}</span>
      <span className="atlas-school-date">{school.century}</span>
    </button>
  );
}

export default function GenealogyPage() {
  const [params, setParams] = useSearchParams();
  const latestParams = useRef(params);
  useEffect(() => { latestParams.current = params; }, [params]);
  const mode = MODES.some(item => item.id === params.get('view')) ? params.get('view') : 'time';
  const question = QUESTIONS.find(item => item.id === params.get('question')) || QUESTIONS[0];
  const tradition = TRADITIONS.some(item => item.id === params.get('region')) ? params.get('region') : 'all';
  const query = params.get('q') || '';
  const [catalog, setCatalog] = useState([]);
  const [loadError, setLoadError] = useState(false);
  const [reload, setReload] = useState(0);
  const schoolById = useMemo(() => new Map(catalog.map(school => [school.id, school])), [catalog]);
  const selected = schoolById.get(params.get('focus')) || null;
  const [hovered, setHovered] = useState(null);
  const [width, setWidth] = useState(960);
  const canvasRef = useRef(null);
  const focusId = hovered || selected?.id;
  useSEO('哲学谱系', '按时间、关联与哲学问题浏览哲学流派。');

  function update(values) {
    const next = new URLSearchParams(latestParams.current);
    for (const [key, value] of Object.entries(values)) {
      if (value === null || value === '' || (key === 'region' && value === 'all')) next.delete(key);
      else next.set(key, value);
    }
    latestParams.current = next;
    setParams(next, { replace: true });
    setHovered(null);
  }

  useEffect(() => {
    const controller = new AbortController();
    let active = true;
    loadGenealogyCatalog(controller.signal).then(data => {
      if (active) { setCatalog(data); setLoadError(false); }
    }).catch(() => { if (active) setLoadError(true); });
    return () => { active = false; controller.abort(); };
  }, [reload]);

  useEffect(() => {
    const element = canvasRef.current;
    if (!element) return;
    const observer = new ResizeObserver(([entry]) => setWidth(Math.max(240, Math.round(entry.contentRect.width))));
    observer.observe(element);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    if (!selected) return;
    const close = event => {
      if (event.key === 'Escape') setParams(current => { const next = new URLSearchParams(current); next.delete('focus'); return next; }, { replace: true });
    };
    window.addEventListener('keydown', close);
    return () => window.removeEventListener('keydown', close);
  }, [selected, setParams]);

  const schools = useMemo(() => filterSchools(catalog, { query, tradition, question: mode === 'question' ? question.id : null }), [catalog, query, tradition, mode, question.id]);
  const layout = useMemo(() => mode === 'time' ? riverLayout(schools, width) : constellationLayout(schools, width, mode === 'question' ? question : null), [schools, width, mode, question]);
  const edges = mode === 'time' ? [] : visibleEdges(layout, focusId, mode === 'question' ? question : null);
  const related = new Set([focusId, ...edges.flatMap(edge => [edge.from, edge.to])]);
  const [heading, kicker] = HEADINGS[mode];
  const questionCategories = [...new Set(QUESTIONS.map(item => item.category))];

  return (
    <div className={`genealogy-atlas${selected ? ' has-selection' : ''}`}>
      <div className="atlas-grain" aria-hidden="true" />
      <section className="atlas-hero">
        <img className="atlas-hero-image" src={ossImg('/schools/理性主义.webp', { w: 1400 })} onError={ossFallback} alt="" fetchPriority="high" />
        <div className="atlas-hero-wash" aria-hidden="true" />
        <div className="atlas-kicker">{kicker}</div>
        <h1>{heading}</h1>
        <p className="atlas-hero-count">{catalog.length || '—'} 个流派 <span>·</span> {QUESTIONS.length} 个问题</p>
      </section>

      <div className="atlas-content">
        <div className="atlas-toolbar">
          <div className="atlas-mode-options" role="group" aria-label="浏览方式">
            {MODES.map(item => <button type="button" key={item.id} className="atlas-mode" aria-pressed={mode === item.id} onClick={() => update({ view: item.id })}>{item.title}</button>)}
          </div>
          <div className="atlas-filters">
            <label className="atlas-search"><span className="sr-only">查找流派、哲人或关键词</span><input type="search" placeholder="流派、哲人、关键词" value={query} onChange={event => update({ q: event.target.value })} /></label>
            <label><span className="sr-only">筛选地区</span><select aria-label="筛选地区" value={tradition} onChange={event => update({ region: event.target.value })}>{TRADITIONS.map(item => <option key={item.id} value={item.id}>{item.label}</option>)}</select></label>
          </div>
        </div>

        {mode === 'question' && <div className="atlas-question-bar">
          <label className="atlas-question-select"><span>哲学问题</span><select aria-label="选择哲学问题" value={question.id} onChange={event => update({ question: event.target.value })}>{questionCategories.map(category => <optgroup key={category} label={category}>{QUESTIONS.filter(item => item.category === category).map(item => <option key={item.id} value={item.id}>{item.title}</option>)}</optgroup>)}</select></label>
          <div className="atlas-quick-questions" role="group" aria-label="常见哲学问题">{QUICK_QUESTIONS.map(id => { const item = QUESTIONS.find(topic => topic.id === id); return <button type="button" key={id} aria-pressed={question.id === id} onClick={() => update({ question: id })}>{item.title}</button>; })}</div>
        </div>}

        <div className="atlas-map-meta"><span aria-live="polite">{mode === 'question' ? '相关流派' : tradition === 'all' ? '全部谱系' : TRADITIONS.find(item => item.id === tradition)?.label} <span className="atlas-result-count">{schools.length} / {catalog.length || '—'}</span></span>
          {mode === 'relation' && <span className="atlas-legend"><span>实线：共同哲人</span><span>虚线：共同问题</span></span>}
          {mode === 'time' && <span className="atlas-map-note">从早期传统到当代</span>}
        </div>

        <div ref={canvasRef} className={`atlas-canvas atlas-${mode}`} style={{ height: layout.height }}>
          {loadError ? <div className="atlas-empty"><p>谱系数据暂时不可用</p><button type="button" onClick={() => setReload(value => value + 1)}>重试</button></div> : catalog.length === 0 ? <div className="atlas-empty" role="status">正在载入谱系</div> : schools.length === 0 ? <div className="atlas-empty"><p>没有匹配的流派</p><button type="button" onClick={() => update({ q: null, region: null })}>清除筛选</button>{mode === 'question' && <button type="button" onClick={() => update({ view: 'time' })}>查看全部谱系</button>}</div> : <>
            <svg className="atlas-lines" width={width} height={layout.height} viewBox={`0 0 ${width} ${layout.height}`} role="img" aria-label={mode === 'time' ? '按年代排列的连续思想长河' : mode === 'relation' ? '按共同哲人与共同问题连接的流派星图' : question.title}>
              {mode === 'time' ? <>
                <path d={layout.path} className="atlas-river-bed" />
                <path d={layout.path} className="atlas-river-inner" />
                <path d={layout.path} className="atlas-river-line" />
                {layout.nodes.map(node => <g key={node.school.id} className={selected?.id === node.school.id ? 'atlas-river-pin is-active' : 'atlas-river-pin'}><path d={`M ${node.x} ${node.y + node.height - 8} L ${node.x} ${node.y + node.height + 16}`} /><circle cx={node.x} cy={node.y + node.height + 16} r={selected?.id === node.school.id ? 4 : 2.5} /></g>)}
              </> : <>
                {Array.from({ length: Math.min(160, Math.ceil(layout.height / 18)) }, (_, index) => <circle key={index} cx={12 + ((index * 137.13) % (width - 24))} cy={14 + ((index * 97.41) % (layout.height - 28))} r={index % 7 === 0 ? 1.3 : .7} className="atlas-star-dust" />)}
                {edges.map(edge => <path key={edge.id} d={edge.path} className={`atlas-edge atlas-edge-${edge.type}${focusId ? ' is-active' : ''}`}><title>{edge.label}</title></path>)}
              </>}
            </svg>
            {layout.labels.map((label, index) => <span key={index} className="atlas-era-label" style={{ left: label.x, top: label.y }}>{label.text}</span>)}
            {layout.groups.map(group => <span key={group.label} className="atlas-group-label" style={{ left: group.x, top: group.y }}>{group.label}</span>)}
            {layout.nodes.map(node => <SchoolArtwork key={node.school.id} node={node} selected={selected?.id === node.school.id} related={related.has(node.school.id)} focused={mode !== 'time' && Boolean(focusId)} onSelect={id => update({ focus: id })} onHover={setHovered} />)}
          </>}
        </div>
        <footer className="atlas-footer"><span>DeepPhilosophy</span><div><Link to="/western-philosophies">西方哲学</Link><Link to="/eastern-philosophies">东方哲学</Link><Link to="/world-philosophies">世界哲学</Link></div></footer>
      </div>

      {selected && createPortal(<aside className="genealogy-atlas atlas-detail" aria-label="流派预览" aria-live="polite">
        <img key={selected.id} className="atlas-detail-image" src={ossImg(selected.image, { w: 320 })} onError={ossFallback} alt={selected.name} />
        <div className="atlas-detail-copy"><span className="atlas-detail-period">{selected.century} · {selected.traditionLabel}</span><h2>{selected.name}</h2><p>{selected.desc}</p><div className="atlas-detail-thinkers">{selected.thinkers.slice(0, 3).map(thinker => thinker.name).join(' · ')}</div><div className="atlas-detail-topics">{schoolTopics(selected).slice(0, 3).map(topic => <button type="button" key={topic.id} onClick={() => update({ view: 'question', question: topic.id, q: null, region: null })}>{topic.title}</button>)}</div></div>
        <Link className="atlas-detail-link" to={schoolPath(selected)}>进入流派详情 <span aria-hidden="true">↗</span></Link>
        <button type="button" className="atlas-detail-close" aria-label="关闭流派预览" onClick={() => update({ focus: null })}>×</button>
      </aside>, document.body)}
    </div>
  );
}
