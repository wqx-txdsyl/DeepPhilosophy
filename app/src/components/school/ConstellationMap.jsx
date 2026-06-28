import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { FONT, SPACE } from './tokens';

const EDGE_STYLES = {
  '师生': { stroke: 'rgba(58,90,124,0.5)', width: 2, dash: '' },
  '继承': { stroke: 'rgba(58,90,124,0.35)', width: 1.4, dash: '' },
  '影响': { stroke: 'rgba(196,149,106,0.4)', width: 1.2, dash: '' },
  '再传': { stroke: 'rgba(58,90,124,0.3)', width: 1, dash: '4,3' },
  '批判': { stroke: 'rgba(160,80,80,0.45)', width: 1.2, dash: '6,4' },
  '对立': { stroke: 'rgba(160,80,80,0.4)', width: 1, dash: '6,4' },
  '批判/超越': { stroke: 'rgba(160,80,80,0.45)', width: 1.2, dash: '6,4' },
  '友谊': { stroke: 'rgba(196,149,106,0.3)', width: 0.8, dash: '3,5' },
  '注释': { stroke: 'rgba(196,149,106,0.25)', width: 0.8, dash: '2,4' },
  '合作': { stroke: 'rgba(196,149,106,0.3)', width: 0.8, dash: '3,5' },
  '学术交流': { stroke: 'rgba(196,149,106,0.3)', width: 0.8, dash: '3,5' },
};

export default function ConstellationMap({ thinkers, relations, SUB_COLORS = {} }) {
  const [hovered, setHovered] = useState(null);
  const [selected, setSelected] = useState(null);
  const navigate = useNavigate();

  const focusNode = selected || hovered;
  const isFocused = (name) => !focusNode || name === focusNode;
  const isConnected = (name) => {
    if (!focusNode) return true;
    const rels = relations.filter(r => r.from === focusNode || r.to === focusNode);
    const connected = new Set(rels.flatMap(r => [r.from, r.to]));
    return connected.has(name) || name === focusNode;
  };

  const getNodeSize = (t) => {
    const inf = t.influence || 5;
    if (inf >= 10) return 28;
    if (inf >= 9) return 24;
    if (inf >= 8) return 20;
    if (inf >= 7) return 17;
    return 14;
  };

  return (
    <section style={{ padding: `${SPACE.hero}px 20px`, background: 'var(--card-bg)', position: 'relative' }}>
      <div style={{ textAlign: 'center', marginBottom: 48 }}>
        <span style={{ fontSize: 11, fontWeight: 500, letterSpacing: '0.2em', textTransform: 'uppercase', color: 'var(--fade)', fontFamily: FONT.sans }}>Chapter 2</span>
        <h2 style={{ fontSize: 26, fontWeight: 400, color: 'var(--ink)', margin: '4px 0 0', fontFamily: FONT.serif, letterSpacing: '0.03em' }}>思想星丛</h2>
        <div style={{ width: 24, height: 1.5, background: 'var(--ochre)', margin: '12px auto 0', opacity: 0.5 }} />
        <p style={{ fontSize: 11, color: 'var(--fade)', marginTop: 8, fontFamily: FONT.sans, fontWeight: 300 }}>
          悬停探索思想谱系 · 点击固定焦点 · 再次点击跳转作者页
        </p>
      </div>

      {/* Legend */}
      <div style={{ maxWidth: 900, margin: '0 auto 20px', display: 'flex', gap: 20, justifyContent: 'center', flexWrap: 'wrap', fontFamily: FONT.sans, fontSize: 10, color: 'var(--fade)' }}>
        <span>── 师生/继承</span>
        <span>- - 再传/影响</span>
        <span style={{ opacity: 0.7 }}>··· 批判/对立</span>
        <span style={{ opacity: 0.5 }}>··· 学术交流</span>
      </div>

      <div style={{ width: '100%', maxWidth: 1000, height: 640, margin: '0 auto', position: 'relative', overflow: 'hidden' }}>
        <div style={{ position: 'absolute', inset: 0, background: 'radial-gradient(ellipse at 50% 50%, rgba(196,149,106,0.05) 0%, transparent 65%)' }} />

        <svg viewBox="0 0 800 560" style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%' }} onClick={() => { setSelected(null); setHovered(null); }}>
          <defs>
            <marker id="arrowhead" markerWidth="6" markerHeight="4" refX="6" refY="2" orient="auto">
              <polygon points="0,0 6,2 0,4" fill="rgba(58,90,124,0.4)" />
            </marker>
          </defs>

          {/* EDGES — typed by relationship */}
          {relations.map((r, i) => {
            const from = thinkers.find(t => t.name === r.from);
            const to = thinkers.find(t => t.name === r.to);
            if (!from || !to) return null;

            const style = EDGE_STYLES[r.type] || EDGE_STYLES['影响'];
            const isRelevant = focusNode
              ? (r.from === focusNode || r.to === focusNode)
              : true;
            const opacity = focusNode ? (isRelevant ? 1 : 0.06) : 1;

            const midX = (from._x + to._x) / 2, midY = (from._y + to._y) / 2;

            return (
              <g key={i}>
                {isRelevant && focusNode && (
                  <path d={`M${from._x},${from._y} L${to._x},${to._y}`}
                    fill="none" stroke={style.stroke} strokeWidth={style.width + 3} opacity={0.15}
                    strokeDasharray={style.dash} />
                )}
                <path d={`M${from._x},${from._y} L${to._x},${to._y}`}
                  fill="none" stroke={style.stroke} strokeWidth={style.width}
                  strokeDasharray={style.dash} opacity={opacity}
                  markerEnd={style.dash ? undefined : 'url(#arrowhead)'}
                  style={{ transition: 'opacity 0.35s' }} />
                {isRelevant && focusNode && (
                  <text x={midX} y={midY - 6} textAnchor="middle" fontSize={8} fill="var(--ochre)" fontStyle="italic" opacity={0.7}>{r.type}</text>
                )}
              </g>
            );
          })}

          {/* Auto sub-school lines — even fainter */}
          {(() => {
            const existing = new Set(relations.map(r => `${r.from}||${r.to}`));
            const lines = [];
            const groups = {};
            thinkers.forEach(t => { const g = t.sub || '__d__'; if (!groups[g]) groups[g] = []; groups[g].push(t); });
            Object.values(groups).forEach(group => {
              for (let a = 0; a < group.length; a++)
                for (let b = a + 1; b < group.length; b++)
                  if (!existing.has(`${group[a].name}||${group[b].name}`) && !existing.has(`${group[b].name}||${group[a].name}`))
                    lines.push(<path key={`auto-${a}-${b}`}
                      d={`M${group[a]._x},${group[a]._y} L${group[b]._x},${group[b]._y}`}
                      fill="none" stroke="rgba(196,149,106,0.06)" strokeWidth="0.6" strokeDasharray="4,8"
                      opacity={focusNode ? 0.02 : 1} style={{ transition: 'opacity 0.35s' }} />);
            });
            return lines;
          })()}

          {/* NODES — hierarchical sizing, focus mode */}
          {thinkers.map((t, i) => {
            const baseSize = getNodeSize(t);
            const isFoc = t.name === focusNode;
            const isConn = isConnected(t.name);
            const color = SUB_COLORS[t.sub] || 'var(--ochre)';
            const dimmed = focusNode && !isFoc && !isConn;

            return (
              <g key={i} style={{ cursor: 'pointer', transition: 'opacity 0.35s' }}
                opacity={dimmed ? 0.22 : 1}
                onClick={(e) => { e.stopPropagation(); if (selected === t.name) { setSelected(null); navigate('/author/' + encodeURIComponent(t.name)); } else { setSelected(selected === t.name ? null : t.name); } }}
                onMouseEnter={() => setHovered(t.name)}
                onMouseLeave={() => setHovered(null)}>

                {/* Pulse ring for selected */}
                {selected === t.name && (
                  <circle cx={t._x} cy={t._y} r={baseSize + 16} fill="none" stroke={color} strokeWidth="1" opacity="0.25"
                    style={{ animation: 'pulse 2s ease-out infinite' }} />
                )}

                {/* Main circle */}
                <circle cx={t._x} cy={t._y} r={isFoc ? baseSize * 1.2 : baseSize}
                  fill="var(--bone)" stroke={color}
                  strokeWidth={isFoc ? 2.2 : (t.influence >= 9 ? 1.8 : 1.2)}
                  filter={isFoc ? `drop-shadow(0 0 8px ${color}60)` : 'none'}
                  style={{ transition: 'all 0.4s cubic-bezier(0.22,1,0.36,1)' }} />

                {/* Initial */}
                <text x={t._x} y={t._y + (baseSize > 20 ? 5 : 3)} textAnchor="middle"
                  fill={isFoc ? color : 'var(--ink)'} fontSize={baseSize > 22 ? 13 : 10}
                  fontFamily={FONT.serif} fontWeight={600} style={{ transition: 'all 0.3s' }}>
                  {t.name[0]}
                </text>

                {/* Name label — visible for large nodes or focused */}
                {(baseSize >= 22 || isFoc) && (
                  <text x={t._x} y={t._y + baseSize + 14} textAnchor="middle"
                    fill="var(--ink)" fontSize={isFoc ? 11 : 9} fontFamily={FONT.sans}
                    fontWeight={isFoc ? 500 : 300} style={{ transition: 'all 0.3s' }}>
                    {t.name}
                  </text>
                )}

                {/* Detail panel rendered in TOP LAYER below */}
              </g>
            );
          })}
        
          {/* TOP LAYER — focused node detail panel, renders above all nodes, positioned smartly */}
          {focusNode && thinkers.filter(t => t.name === focusNode).map(t => {
            const bs = getNodeSize(t);
            const co = SUB_COLORS[t.sub] || 'var(--ochre)';
            const panelH = 82;
            const panelW = 180;
            const above = t._y - bs - panelH - 12;
            const below = t._y + bs + 12;
            const showBelow = above < 10;
            const py = showBelow ? below : above;
            const px = Math.max(panelW/2 + 4, Math.min(800 - panelW/2 - 4, t._x));
            return (
              <g key="top-detail">
                <rect x={px - panelW/2} y={py} width={panelW} height={panelH} rx={6}
                  fill="rgba(248,244,238,0.97)" stroke={co} strokeWidth="0.8" strokeOpacity="0.5"
                  filter="drop-shadow(0 2px 12px rgba(0,0,0,0.08))" />
                <text x={px} y={py + 16} textAnchor="middle" fill="var(--ink)"
                  fontSize={12} fontFamily={FONT.serif} fontWeight={600}>{t.name}</text>
                <foreignObject x={px - panelW/2 + 8} y={py + 24} width={panelW - 16} height={54}>
                  <div style={{ fontFamily: FONT.sans, fontSize: 9, color: 'var(--text-dim)', lineHeight: 1.5, wordBreak: 'break-word', textAlign: 'center' }}>
                    <span style={{ color: co, fontWeight: 500 }}>{t.sub}</span><br/>
                    <span>{t.era}{t.key ? ' · ' + t.key : ''}</span>
                    {Array.isArray(t.works) && t.works.length > 0 && <><br/><span style={{ color: 'var(--fade)', fontSize: 8 }}>{t.works.length} 部著作</span></>}
                  </div>
                </foreignObject>
              </g>
            );
          })}
</svg>
      </div>
    </section>
  );
}
