import { useEffect, useLayoutEffect, useReducer, useRef } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { useSEO } from '../utils/seo';
import CdnImage from '../components/CdnImage';
import { ossImg } from '../data/ossUrls';
import { MORE_FIELDS } from '../data/moreExplorer';
import './MoreExplorer.css';

const wrap = index => ((index % 8) + 8) % 8;
function initialState(params) {
  const index = Math.max(0, MORE_FIELDS.findIndex(field => field.id === params.get('discipline')));
  const requestedTopic = MORE_FIELDS[index].id === 'religion' && ['orthodox', 'catholic', 'protestant'].includes(params.get('topic')) ? 'christianity' : params.get('topic');
  const topic = Math.max(0, MORE_FIELDS[index].topics.findIndex(t => t.id === requestedTopic));
  return { index, angle: -index * 45, expanded: params.get('album') === 'open', topic, dragging: false, visited: [index] };
}
function reducer(state, action) {
  if (action.type === 'open') return { ...state, expanded: action.value ?? !state.expanded };
  if (action.type === 'topic') return { ...state, topic: action.index };
  if (action.type === 'drag') return { ...state, angle: action.angle, dragging: true };
  const index = wrap(action.index ?? state.index + action.step);
  const target = -index * 45;
  let delta = ((target - state.angle + 180) % 360 + 360) % 360 - 180;
  if (delta === -180) delta = 180;
  return { ...state, index, angle: action.angle ?? state.angle + delta, expanded: false,
    topic: 0, dragging: false, visited: [...new Set([...state.visited, index])] };
}
function wedge(start, end) {
  const point = (r, a) => [250 + Math.cos(a * Math.PI / 180) * r, 250 + Math.sin(a * Math.PI / 180) * r];
  const [a, b, c, d] = [point(238, start), point(238, end), point(104, end), point(104, start)];
  return `M${a} A238,238 0 0 1 ${b} L${c} A104,104 0 0 0 ${d} Z`;
}

export default function MorePage() {
  useSEO('更多 — 思想的八个入口', '转动学科圆盘，探索哲学、神话、宗教、文学、心理、社会、历史与政治。');
  const [searchParams, setSearchParams] = useSearchParams();
  const [state, dispatch] = useReducer(reducer, searchParams, initialState);
  const bounds = useRef(null), fan = useRef(null), drag = useRef(null), suppressClick = useRef(false);
  const current = useRef(state);
  const openButton = useRef(null), albumRef = useRef(null);
  useLayoutEffect(() => { current.current = state; }, [state]);
  const field = MORE_FIELDS[state.index];
  const topics = field.topics, topic = topics[state.topic];
  const philosophy = field.id === 'philosophy';

  useEffect(() => {
    const params = new URLSearchParams();
    if (state.index !== 0 || state.expanded) params.set('discipline', field.id);
    if (state.expanded) { params.set('album', 'open'); params.set('topic', topic.id); }
    if (params.toString() !== searchParams.toString()) setSearchParams(params, { replace: true });
  }, [state.index, state.expanded, field.id, topic.id, searchParams, setSearchParams]);

  useEffect(() => {
    const element = bounds.current;
    let total = 0, at = 0, lock = 0;
    const wheel = event => {
      if (event.ctrlKey || event.metaKey || drag.current) return;
      const amount = Math.abs(event.deltaX) > Math.abs(event.deltaY) ? event.deltaX : event.deltaY;
      if (!amount) return;
      event.preventDefault();
      const now = performance.now();
      if (now < lock) return;
      if (now - at > 180) total = 0;
      at = now;
      total += amount * (event.deltaMode === 1 ? 16 : event.deltaMode === 2 ? element.clientHeight : 1);
      if (Math.abs(total) >= 42) {
        dispatch({ type: 'select', step: Math.sign(total) });
        total = 0; lock = now + 210;
      }
    };
    element.addEventListener('wheel', wheel, { passive: false });
    return () => element.removeEventListener('wheel', wheel);
  }, []);

  useLayoutEffect(() => {
    if (!state.expanded || !fan.current) return;
    const element = fan.current;
    const prepare = () => Array.from(element.children).forEach(card => {
      card.style.setProperty('--from-x', `${element.clientWidth / 2 - card.offsetLeft - card.offsetWidth / 2}px`);
    });
    prepare();
    const observer = new ResizeObserver(prepare);
    observer.observe(element);
    return () => observer.disconnect();
  }, [state.expanded, state.index]);

  useEffect(() => {
    if (!state.expanded || !albumRef.current) return;
    const album = albumRef.current;
    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    let finished = false;
    const scrollToBottom = () => {
      if (finished) return;
      finished = true;
      window.scrollTo({ top: document.documentElement.scrollHeight, behavior: reducedMotion ? 'instant' : 'smooth' });
    };
    const afterExpand = event => {
      if (event.target === album && event.propertyName === 'grid-template-rows') scrollToBottom();
    };
    album.addEventListener('transitionend', afterExpand);
    const timer = setTimeout(scrollToBottom, reducedMotion ? 0 : 950);
    return () => { clearTimeout(timer); album.removeEventListener('transitionend', afterExpand); };
  }, [state.expanded, state.index]);

  const startDrag = event => {
    if (event.button !== 0) return;
    const r = bounds.current.getBoundingClientRect();
    const cx = r.left + r.width / 2, cy = r.top + r.height / 2;
    drag.current = { id: event.pointerId, x: event.clientX, y: event.clientY, cx, cy,
      angle: current.current.angle, total: 0, last: Math.atan2(event.clientY - cy, event.clientX - cx), moved: false };
    suppressClick.current = false;
  };
  const moveDrag = event => {
    const d = drag.current;
    if (!d || event.pointerId !== d.id) return;
    if (Math.hypot(event.clientX - d.x, event.clientY - d.y) > 7) {
      d.moved = true; suppressClick.current = true;
      bounds.current.setPointerCapture(event.pointerId);
    }
    if (!d.moved) return;
    const angle = Math.atan2(event.clientY - d.cy, event.clientX - d.cx);
    let delta = angle - d.last;
    if (delta > Math.PI) delta -= Math.PI * 2;
    if (delta < -Math.PI) delta += Math.PI * 2;
    d.total += delta * 180 / Math.PI; d.last = angle;
    dispatch({ type: 'drag', angle: d.angle + d.total });
  };
  const endDrag = event => {
    const d = drag.current;
    if (!d || event.pointerId !== d.id) return;
    drag.current = null;
    if (d.moved) {
      const angle = Math.round((d.angle + d.total) / 45) * 45;
      dispatch({ type: 'select', index: -Math.round(angle / 45), angle });
      setTimeout(() => { suppressClick.current = false; }, 0);
    }
  };
  const close = () => { dispatch({ type: 'open', value: false }); openButton.current?.focus(); };

  return <div id="dp-rotating-folio">
    <div className="motion-app" style={{ '--active-color': field.color }}>
      <div className="motion-shell">
        <header className="motion-heading"><div><p className="motion-kicker">DeepPhilosophy · Disciplines</p><h1>思想的八个入口</h1></div>
          <p>转动圆盘，让一个学科来到眼前。<br />Ph / My / Re / Li / Ps / So / Hi / Po</p></header>
        <section className="motion-hero">
          <div className="motion-stage">
            <div ref={bounds} className={`disc-bounds${state.dragging ? ' is-dragging' : ''}`}
              onPointerDown={startDrag} onPointerMove={moveDrag} onPointerUp={endDrag}
              onPointerCancel={() => { const d = drag.current; if (d) { drag.current = null; suppressClick.current = false; dispatch({ type: 'select', index: current.current.index, angle: d.angle }); } }}
              onKeyDown={event => { if (event.key === 'ArrowRight' || event.key === 'ArrowLeft') { event.preventDefault(); dispatch({ type: 'select', step: event.key === 'ArrowRight' ? 1 : -1 }); } }}>
              <div className="disc-rim" />
              <div className="disc-rotor" style={{ transform: `rotate(${state.angle}deg)` }}>
                <svg viewBox="0 0 500 500" aria-hidden="true"><defs>{MORE_FIELDS.map((f, i) => <clipPath id={`more-sector-${i}`} key={f.id}><path d={wedge(i * 45 - 21.7, i * 45 + 21.7)} /></clipPath>)}</defs>
                  {MORE_FIELDS.map((f, i) => <g key={f.id}><image className={`disc-sector-image${i === state.index ? ' is-selected' : ''}`}
                    href={ossImg(f.image, { w: 384 })} onError={event => { const image = event.currentTarget; if (image.getAttribute('href') !== f.image) image.setAttribute('href', f.image); }}
                    x="0" y="0" width="500" height="500" preserveAspectRatio="xMidYMid slice" clipPath={`url(#more-sector-${i})`} />
                    <path d={wedge(i * 45 - 21.7, i * 45 + 21.7)} fill="none" stroke="var(--rule)" strokeWidth="1" /></g>)}
                </svg>
                {MORE_FIELDS.map((f, i) => <button type="button" key={f.id} className="disc-code" aria-label={`选择${f.name}`} aria-pressed={i === state.index}
                  style={{ '--field': f.color, '--counter': `${-state.angle}deg`, left: `${50 + 35 * Math.cos(i * Math.PI / 4)}%`, top: `${50 + 35 * Math.sin(i * Math.PI / 4)}%` }}
                  onClick={() => { if (!suppressClick.current) dispatch({ type: 'select', index: i }); }}><strong>{f.code}</strong><small>{f.name}</small></button>)}
              </div>
              <div className="disc-hub"><strong>{field.code}</strong><span>{field.name}</span></div><span className="disc-pointer" aria-hidden="true">‹</span>
            </div>
            <div className="motion-controls"><button type="button" onClick={() => dispatch({ type: 'select', step: -1 })}>← 上一学科</button><span>{String(state.index + 1).padStart(2, '0')} / 08</span><button type="button" onClick={() => dispatch({ type: 'select', step: 1 })}>下一学科 →</button></div>
            <p className="motion-hint">滚轮旋转 · 拖动圆盘 · 点击字母选择</p>
          </div>
          <section className="folio-focus" aria-label="当前学科">
            <div className="folio-title-row"><span className="folio-code">{field.code}</span><span className="folio-status">{field.ready ? '已开放阅读' : '资料整理中'}</span></div>
            <div className="folio-photo">{state.visited.map(i => <CdnImage key={MORE_FIELDS[i].id} src={MORE_FIELDS[i].image} imageWidth={900} className={i === state.index ? 'is-current' : ''} alt={`${MORE_FIELDS[i].name}学科环境配图`} aria-hidden={i !== state.index} draggable={false} fetchPriority={i === state.index ? 'high' : 'auto'} />)}</div>
            <div className="folio-copy" aria-live="polite"><h2>{field.name}</h2><small>{field.en}</small><p>{field.description}</p>
              <button ref={openButton} type="button" className="folio-action" aria-expanded={state.expanded} aria-controls="more-topic-album" onClick={() => dispatch({ type: 'open' })}>{state.expanded ? '合上学科卡册 ↑' : field.ready ? `展开${field.name}卡册 ↗` : '查看拟定方向 ↗'}</button></div>
          </section>
        </section>
        <section ref={albumRef} id="more-topic-album" className={`folio-open${state.expanded ? ' is-open' : ''}`} aria-label="学科卡册" aria-hidden={!state.expanded} inert={!state.expanded}>
          <div className="folio-open-inner"><div className="folio-open-content" key={field.id}>
            <header className="folio-open-heading"><div><p className="motion-kicker">{field.code} / {field.en}</p><h3>{field.name} · {philosophy ? '代表流派' : field.ready ? '主题卡册' : '拟定方向'}</h3>
              <p>{philosophy ? '从几个代表流派开始，再沿时间、关系与问题继续探索。' : field.ready ? `共 ${topics.length} 个主题，选择一张画卡进入阅读。` : '本学科正在整理，以下为拟定方向。'}</p></div><button type="button" onClick={close}>合上卡册 ↑</button></header>
            <div ref={fan} className="topic-fan" aria-label={`${field.name}主题画卡`}>{topics.map((t, i) => {
              const row = Math.floor(i / 6), column = i % 6;
              const center = (Math.min(6, topics.length - row * 6) - 1) / 2;
              return <button type="button" className="topic-fan-card" key={t.id} aria-label={`选择${t.name}`} aria-pressed={state.topic === i} onClick={() => dispatch({ type: 'topic', index: i })}
                style={{ '--splay': `${(column - center) * 14}deg`, '--delay': `${column * 60 + row * 80}ms`, '--arc': `${Math.abs(column - center) / Math.max(1, center) * 28}px`, '--rest-y': state.topic === i ? '-9px' : '0px' }}>
                <div className="topic-fan-photo"><CdnImage src={t.image || field.image} imageWidth={400} alt={`${t.name}配图`} draggable={false} loading="lazy" /></div>
                <div className="topic-fan-copy"><small>{String(i + 1).padStart(2, '0')} / {field.code}</small><h4>{t.name}</h4></div></button>;
            })}</div>
            <div className="postcard-detail" aria-live="polite"><div><p className="motion-kicker">{String(state.topic + 1).padStart(2, '0')} / {field.code}</p><h4>{topic.name}</h4><p>{topic.note || '主题资料正在整理。'}</p></div>
              {field.ready ? <Link to={topic.path || `/more/${field.id}/${topic.id}`}>进入{topic.name} ↗</Link> : <span>筹备中</span>}</div>
            {philosophy && <div className="topic-fan-ending"><Link className="folio-action" to="/genealogy">探索更多 · 进入哲学谱系 ↗</Link></div>}
          </div></div>
        </section>
      </div>
    </div>
  </div>;
}
