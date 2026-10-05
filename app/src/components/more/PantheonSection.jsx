/**
 * PantheonSection — 神谱星丛（完全对标流派页 ConstellationMap）
 * 复用 layoutConstellation 布局引擎与 school-star-* 样式：
 * 星尘底纹 + 曲线关系边 + 星位节点（大节点带画像）+ 右侧档案面板 + 全量名册
 * 关系类型映射：亲缘→lineage（金实线）· 战争→criticism（陶虚线）· 天命信物→context（点线）
 */
import { useMemo, useRef, useState, useLayoutEffect } from 'react';
import { layoutConstellation, constellationCurve } from '../../data/schoolConstellationLayout';
import '../school/ConstellationMap.css';

const KIND = { kin: 'lineage', war: 'criticism', mandate: 'context' };
const LEGEND = [['lineage', '亲缘'], ['criticism', '战争'], ['context', '天命 · 信物']];

export default function PantheonSection({ pantheon, deities, categories }) {
  const canvasRef = useRef(null);
  const panelRef = useRef(null);
  const [width, setWidth] = useState(740);
  const [hovered, setHovered] = useState(null);
  const [selectedName, setSelectedName] = useState(null);

  useLayoutEffect(() => {
    const el = canvasRef.current;
    if (!el) return;
    const observer = new ResizeObserver(entries => {
      const next = Math.round(entries[0].contentRect.width);
      if (next > 0) setWidth(old => old === next ? old : next);
    });
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  const nodeById = useMemo(() => new Map(pantheon.nodes.map(n => [n.id, n])), [pantheon.nodes]);
  const deityByName = useMemo(() => new Map(deities.map(d => [d.name, d])), [deities]);
  const iconByName = useMemo(() => new Map(deities.map(d => [d.name, d.icon].filter(Boolean))), [deities]);

  const thinkers = useMemo(() => pantheon.nodes.map(n => ({
    name: n.name,
    era: n.domain,
    deityId: n.id,
    portrait: iconByName.get(n.name) || null,
    influence: [9, 8, 6, 7][n.tier] || 5,
  })), [pantheon.nodes, iconByName]);

  const relations = useMemo(() => pantheon.edges.map(e => {
    const from = nodeById.get(e.from), to = nodeById.get(e.to);
    return from && to ? { from: from.name, to: to.name, label: e.label, kind: KIND[e.type] || 'influence' } : null;
  }).filter(Boolean), [pantheon.edges, nodeById]);

  const layout = useMemo(() => layoutConstellation(thinkers, relations, width), [thinkers, relations, width]);
  const nodesByName = useMemo(() => new Map(layout.nodes.map(n => [n.name, n])), [layout]);

  const selected = selectedName ? deityByName.get(selectedName) : null;
  const selectedNode = selectedName ? nodesByName.get(selectedName) : null;
  const activeName = nodesByName.has(hovered) ? hovered : selectedNode?.name;
  const related = new Set([activeName]);
  relations.forEach(r => { if (r.from === activeName || r.to === activeName) { related.add(r.from); related.add(r.to); } });
  const selectedRelations = relations.filter(r => r.from === selectedName || r.to === selectedName);

  function choose(name, { scroll = false } = {}) {
    setSelectedName(name);
    setHovered(null);
    if (scroll) requestAnimationFrame(() => panelRef.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' }));
  }

  return (
    <div className="school-constellation mtd-star">
      <header className="school-star-heading">
        <div>
          <span className="school-star-kicker">Mythological constellation</span>
          <h2>神谱</h2>
        </div>
        <span className="school-star-count">{layout.nodes.length} 个节点 · {relations.length} 道联系</span>
      </header>

      <div className="school-star-layout">
        <div>
          <div className="school-star-canvas" ref={canvasRef} style={{ height: layout.height }} aria-label="神谱星图">
            <svg className="school-star-lines" viewBox={`0 0 ${layout.width} ${layout.height}`} aria-hidden="true">
              {Array.from({ length: 55 }, (_, index) => <circle key={`dust-${index}`} cx={10 + ((index * 137.1) % Math.max(1, layout.width - 20))} cy={12 + ((index * 79.7) % Math.max(1, layout.height - 24))} r={index % 7 === 0 ? 1.25 : 0.65} className="school-star-dust" />)}
              {relations.map((r, index) => <path key={`${r.from}-${r.to}-${index}`} className={`school-star-edge school-star-edge--${r.kind} ${r.from === activeName || r.to === activeName ? 'is-connected' : ''}`} d={constellationCurve(nodesByName.get(r.from), nodesByName.get(r.to), index)} />)}
            </svg>
            {layout.nodes.map((node, index) => {
              const deity = deityByName.get(node.name);
              const icon = node.portrait;
              return (
                <button key={node.name} type="button"
                  className={`school-star-node ${related.has(node.name) ? 'is-connected' : ''} ${node.rank < 4 ? 'is-major' : ''}`}
                  style={{ left: node.x, top: node.top, width: node.width, '--star-size': `${node.markerSize}px` }}
                  aria-label={`查看${node.name}`} aria-pressed={selectedName === node.name}
                  onClick={() => choose(node.name)}
                  onMouseEnter={() => setHovered(node.name)} onMouseLeave={() => setHovered(null)}>
                  <span className="school-star-marker">
                    {icon ? <img className="school-star-photo" src={icon} alt="" loading="lazy" /> : <span className={`school-star-orbit ${node.rank >= 4 ? 'is-dot' : ''}`} aria-hidden="true"><i /></span>}
                  </span>
                  <strong>{node.name}</strong>
                  {node.era && <small>{node.era}</small>}
                </button>
              );
            })}
          </div>
          <div className="school-star-legend" aria-label="关系图例">
            {LEGEND.map(([kind, label]) => <span key={kind}><i className={`school-star-swatch school-star-swatch--${kind}`} />{label}</span>)}
          </div>
        </div>

        {/* ═══ 档案面板（同流派星图：画像 + 词条 + 关系跳转） ═══ */}
        <aside className="school-star-profile" ref={panelRef} aria-live="polite" aria-label="神祇词条">
          {!selected ? (
            <p className="mtd-deity-empty">
              点击星图节点，或在下方名册中选择神祇——<br />展开完整词条。共 {deities.length} 位收录。
            </p>
          ) : (
            <>
              {selected.icon && <img className="school-star-profile-photo" src={selected.icon} alt={selected.name} loading="lazy" />}
              {!selected.icon && <span className="school-star-placeholder school-star-profile-photo" aria-hidden="true"><i /></span>}
              <div className="school-star-profile-intro">
                <span className="school-star-profile-school">{selected.title}</span>
                <h3>{selected.name}</h3>
                {selected.aka && <span className="school-star-profile-era">{selected.aka}</span>}
              </div>
              <p className="mtd-deity-story">{selected.story}</p>
              <div className="school-star-profile-block">
                <h4>出处</h4>
                <ul className="school-star-works"><li>{selected.source}</li></ul>
              </div>
              {selectedRelations.length > 0 && (
                <div className="school-star-profile-block">
                  <h4>神谱关系</h4>
                  <div className="school-star-connections">
                    {selectedRelations.map((r, index) => {
                      const name = r.from === selectedName ? r.to : r.from;
                      return <button key={`${name}-${index}`} type="button" onClick={() => choose(name, { scroll: true })}><span>{name}</span><small>{r.from === selectedName ? '→ ' : '← '}{r.label}</small></button>;
                    })}
                  </div>
                </div>
              )}
              <div className="school-star-profile-block">
                <h4>名签</h4>
                <div className="mtd-deity-tags">{selected.tags.map(t => <span key={t} className="tag">{t}</span>)}</div>
              </div>
            </>
          )}
        </aside>
      </div>

      {/* ═══ 全量名册 ═══ */}
      <div className="mtd-roster">
        {categories.map(cat => {
          const list = deities.filter(d => d.category === cat.id);
          if (!list.length) return null;
          return (
            <div key={cat.id} className="mtd-roster-row">
              <div className="mtd-roster-head">
                <span className="mtd-roster-name">{cat.name}</span>
                <span className="mtd-roster-note">{cat.note}</span>
                <span className="mtd-roster-count">{list.length}</span>
              </div>
              <div className="mtd-roster-chips">
                {list.map(d0 => (
                  <button key={d0.id} type="button"
                    className={`mtd-roster-chip${selectedName === d0.name ? ' active' : ''}`}
                    onClick={() => choose(d0.name, { scroll: true })}>
                    {d0.name}
                  </button>
                ))}
              </div>
            </div>
          );
        })}
      </div>

      <p className="mtd-pantheon-note">{pantheon.note}</p>
    </div>
  );
}
