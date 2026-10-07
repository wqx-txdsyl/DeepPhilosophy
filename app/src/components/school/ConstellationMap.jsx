import { formatBookTitle } from '../../data/bookTitles';
import { useMemo, useRef, useState, useLayoutEffect } from 'react';
import { Link } from 'react-router-dom';
import { layoutConstellation, constellationRelationKind, constellationCurve } from '../../data/schoolConstellationLayout';
import './ConstellationMap.css';
import CdnImage from '../CdnImage';

function Portrait({ src, name, className = '' }) {
  const [failedSrc, setFailedSrc] = useState(null);
  if (!src || failedSrc === src) return <span className={`school-star-placeholder ${className}`} aria-hidden="true"><i /></span>;
  return <CdnImage imageWidth={192} className={className} src={src} alt={name || ''} loading="lazy" onError={() => setFailedSrc(src)} />;
}

export default function ConstellationMap({ thinkers = [], relations = [], references, cihai = [], selectedPerson, onSelectPerson, onSelectConcept, onLocatePerson }) {
  const canvasRef = useRef(null);
  const nodeRefs = useRef(new Map());
  const [width, setWidth] = useState(740);
  const [selection, setSelection] = useState(null);
  const [hovered, setHovered] = useState(null);
  useLayoutEffect(() => {
    const element = canvasRef.current;
    if (!element) return;
    const observer = new ResizeObserver(entries => {
      const next = Math.round(entries[0].contentRect.width);
      if (next > 0) setWidth(old => old === next ? old : next);
    });
    observer.observe(element);
    return () => observer.disconnect();
  }, []);
  const layout = useMemo(() => layoutConstellation(thinkers, relations, width), [thinkers, relations, width]);
  const nodesByName = useMemo(() => new Map(layout.nodes.map(node => [node.name, node])), [layout]);
  const selected = nodesByName.get(selectedPerson) || nodesByName.get(selection) || layout.nodes[0];
  const activeName = nodesByName.has(hovered) ? hovered : selected?.name;
  const related = new Set([activeName]);
  const validRelations = relations.filter(relation => relation && nodesByName.has(relation.from) && nodesByName.has(relation.to));
  validRelations.forEach(relation => {
    if (relation.from === activeName || relation.to === activeName) { related.add(relation.from); related.add(relation.to); }
  });
  function choose(name) {
    setSelection(name);
    setHovered(null);
    onSelectPerson?.(name);
  }
  function navigateNodes(event, index) {
    if (!['ArrowRight', 'ArrowDown', 'ArrowLeft', 'ArrowUp', 'Home', 'End'].includes(event.key)) return;
    event.preventDefault();
    const direction = ['ArrowLeft', 'ArrowUp'].includes(event.key) ? -1 : 1;
    const next = event.key === 'Home' ? 0 : event.key === 'End' ? layout.nodes.length - 1 : (index + direction + layout.nodes.length) % layout.nodes.length;
    nodeRefs.current.get(layout.nodes[next].name)?.focus();
  }
  const person = selected && references?.findPerson?.(selected.name, selected.era);
  const concept = selected && (cihai.find(term => term?.word && selected.key && selected.key.replace(/[\s·—-]/g, '').includes(term.word.replace(/[（(].*?[)）]/g, '').replace(/[\s·—-]/g, ''))) || cihai.find(term => term?.word && term.source?.includes(selected.name)));
  const selectedRelations = validRelations.filter(relation => relation.from === selected?.name || relation.to === selected?.name);
  if (!layout.nodes.length) return null;
  return (
    <section className="school-constellation" aria-labelledby="school-constellation-title">
      <header className="school-star-heading">
        <div><span className="school-star-kicker">Intellectual constellation</span><h2 id="school-constellation-title">思想星丛</h2></div>
        <span className="school-star-count">{layout.nodes.length} 个节点 · {validRelations.length} 道联系</span>
      </header>
      <div className="school-star-layout">
        <div>
          <div className="school-star-canvas" ref={canvasRef} style={{ height: layout.height }} aria-label="思想关系星图">
            <svg className="school-star-lines" viewBox={`0 0 ${layout.width} ${layout.height}`} aria-hidden="true">
              {Array.from({ length: 55 }, (_, index) => <circle key={`dust-${index}`} cx={10 + ((index * 137.1) % Math.max(1, layout.width - 20))} cy={12 + ((index * 79.7) % Math.max(1, layout.height - 24))} r={index % 7 === 0 ? 1.25 : .65} className="school-star-dust" />)}
              {validRelations.map((relation, index) => <path key={`${relation.from}-${relation.to}-${index}`} className={`school-star-edge school-star-edge--${constellationRelationKind(relation)} ${relation.from === activeName || relation.to === activeName ? 'is-connected' : ''}`} d={constellationCurve(nodesByName.get(relation.from), nodesByName.get(relation.to), index)} />)}
            </svg>
            {layout.nodes.map((node, index) => {
              const reference = references?.findPerson?.(node.name, node.era);
              const showPortrait = node.rank < 4 && reference?.portrait;
              return <button key={node.name} ref={element => { if (element) nodeRefs.current.set(node.name, element); else nodeRefs.current.delete(node.name); }} type="button" className={`school-star-node ${related.has(node.name) ? 'is-connected' : ''} ${node.rank < 4 ? 'is-major' : ''}`} style={{ left: node.x, top: node.top, width: node.width, '--star-size': `${node.markerSize}px` }} aria-label={`查看${node.name}`} aria-pressed={selected?.name === node.name} onClick={() => choose(node.name)} onMouseEnter={() => setHovered(node.name)} onMouseLeave={() => setHovered(null)} onFocus={() => setHovered(node.name)} onBlur={() => setHovered(null)} onKeyDown={event => navigateNodes(event, index)}>
                <span className="school-star-marker">{showPortrait ? <Portrait src={reference.portrait} className="school-star-photo" /> : <span className={`school-star-orbit ${node.rank >= 4 ? 'is-dot' : ''}`} aria-hidden="true"><i /></span>}</span>
                <strong>{node.name}</strong>{node.era && <small>{node.era}</small>}
              </button>;
            })}
          </div>
          <div className="school-star-legend" aria-label="关系图例">{[['lineage', '师承'], ['influence', '影响'], ['criticism', '批判'], ['context', '交流与关联']].map(([kind, label]) => <span key={kind}><i className={`school-star-swatch school-star-swatch--${kind}`} />{label}</span>)}</div>
        </div>
        <aside key={selected.name} className={`school-star-profile ${person?.portrait ? 'has-portrait' : ''}`} aria-live="polite" aria-label="节点详情">
          {person?.portrait && <Portrait key={person.portrait} src={person.portrait} name={selected.name} className="school-star-profile-photo" />}
          <div className="school-star-profile-intro"><span className="school-star-profile-school">{selected.sub || (selected.relatedOnly ? '相关节点' : '')}</span><h3>{selected.name}</h3>{selected.era && <span className="school-star-profile-era">{selected.era}</span>}{selected.key && <p className="school-star-key">{selected.key}</p>}</div>
          {selectedRelations.length > 0 && <div className="school-star-profile-block"><h4>思想联系</h4><div className="school-star-connections">{selectedRelations.map((relation, index) => {
            const name = relation.from === selected.name ? relation.to : relation.from;
            return <button key={`${name}-${index}`} type="button" onClick={() => choose(name)}><span>{name}</span><small>{relation.from === selected.name ? '→ ' : '← '}{relation.label || relation.type || '联系'}</small></button>;
          })}</div></div>}
          {Array.isArray(selected.works) && selected.works.length > 0 && <div className="school-star-profile-block"><h4>代表著作</h4><ul className="school-star-works">{selected.works.map((work, index) => {
            const title = typeof work === 'string' ? work : work.title;
            const book = references?.findBook?.(title, selected.name);
            return <li key={`${title}-${index}`}>{book?.href ? <Link to={book.href}>{formatBookTitle(title)}<span aria-hidden="true">↗</span></Link> : formatBookTitle(title)}</li>;
          })}</ul></div>}
          {person?.href && <Link className="school-star-detail-link" to={person.href}>进入人物详情 <span aria-hidden="true">↗</span></Link>}
          {!person?.href && references?.findSchool?.(selected.name) && <Link className="school-star-detail-link" to={`/school/${encodeURIComponent(selected.name)}`}>进入流派详情 <span aria-hidden="true">↗</span></Link>}
          {(onLocatePerson || (onSelectConcept && concept)) && <div className="school-star-crosslinks">{onLocatePerson && <button type="button" onClick={() => onLocatePerson(selected.name)}>在时间轴中定位 <span aria-hidden="true">→</span></button>}{onSelectConcept && concept && <button type="button" onClick={() => onSelectConcept(concept.word)}>阅读相关概念 <span aria-hidden="true">→</span></button>}</div>}
        </aside>
      </div>
    </section>
  );
}
