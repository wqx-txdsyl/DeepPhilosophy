/**
 * 思想星丛 — Museum-grade philosopher relationship constellation
 * 有机星图 · 贝塞尔连线 · 电影级视觉 · 智能聚焦
 */
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { FONT, SPACE } from './tokens';

// ─── 连线样式（保留原有分类） ───
const EDGE_STYLES = {
  '师生':        { stroke: 'rgba(196,149,106,0.55)', width: 2.0, dash: '' },
  '继承':        { stroke: 'rgba(196,149,106,0.40)', width: 1.6, dash: '' },
  '再传':        { stroke: 'rgba(196,149,106,0.30)', width: 1.2, dash: '' },
  '创立':        { stroke: 'rgba(196,149,106,0.50)', width: 1.8, dash: '' },
  '开创':        { stroke: 'rgba(196,149,106,0.50)', width: 1.8, dash: '' },
  '父子':        { stroke: 'rgba(196,149,106,0.50)', width: 1.8, dash: '' },
  '同门':        { stroke: 'rgba(196,149,106,0.30)', width: 1.0, dash: '' },
  '分化':        { stroke: 'rgba(196,149,106,0.30)', width: 1.0, dash: '' },
  '继承/发展':   { stroke: 'rgba(196,149,106,0.35)', width: 1.4, dash: '' },
  '继承/超越':   { stroke: 'rgba(196,149,106,0.35)', width: 1.4, dash: '' },
  '领导/继承':   { stroke: 'rgba(196,149,106,0.45)', width: 1.6, dash: '' },
  '领导/影响':   { stroke: 'rgba(196,149,106,0.45)', width: 1.6, dash: '' },
  '领导与影响':  { stroke: 'rgba(196,149,106,0.40)', width: 1.6, dash: '' },
  '学术传承':    { stroke: 'rgba(196,149,106,0.40)', width: 1.4, dash: '' },
  '战略':        { stroke: 'rgba(196,149,106,0.40)', width: 1.4, dash: '' },
  '影响':        { stroke: 'rgba(196,149,106,0.35)', width: 1.0, dash: '4,3' },
  '发展':        { stroke: 'rgba(196,149,106,0.28)', width: 0.9, dash: '4,3' },
  '先驱':        { stroke: 'rgba(196,149,106,0.32)', width: 0.9, dash: '4,3' },
  '经学化':      { stroke: 'rgba(196,149,106,0.28)', width: 0.9, dash: '4,3' },
  '影响/超越':   { stroke: 'rgba(196,149,106,0.33)', width: 1.0, dash: '4,3' },
  '影响与发展':  { stroke: 'rgba(196,149,106,0.33)', width: 1.0, dash: '4,3' },
  '影响与传承':  { stroke: 'rgba(196,149,106,0.33)', width: 1.0, dash: '4,3' },
  '批判':        { stroke: 'rgba(180,70,70,0.45)', width: 1.0, dash: '8,5' },
  '对立':        { stroke: 'rgba(180,70,70,0.40)', width: 0.9, dash: '8,5' },
  '批判/超越':   { stroke: 'rgba(180,70,70,0.45)', width: 1.0, dash: '8,5' },
  '批判继承':    { stroke: 'rgba(180,70,70,0.40)', width: 1.0, dash: '8,5' },
  '对立批判':    { stroke: 'rgba(180,70,70,0.43)', width: 1.0, dash: '8,5' },
  '学术对立':    { stroke: 'rgba(180,70,70,0.40)', width: 0.9, dash: '8,5' },
  '学术争论':    { stroke: 'rgba(180,70,70,0.35)', width: 0.8, dash: '8,5' },
  '学术争鸣':    { stroke: 'rgba(180,70,70,0.35)', width: 0.8, dash: '8,5' },
  '分裂':        { stroke: 'rgba(180,70,70,0.45)', width: 1.2, dash: '8,5' },
  '自我批判':    { stroke: 'rgba(180,70,70,0.30)', width: 0.8, dash: '8,5' },
  '影响与批判':  { stroke: 'rgba(180,70,70,0.40)', width: 1.0, dash: '8,5' },
  '友谊/对立':   { stroke: 'rgba(180,70,70,0.35)', width: 0.9, dash: '8,5' },
  '顿渐之争':    { stroke: 'rgba(180,70,70,0.40)', width: 1.0, dash: '8,5' },
  '学术交流':    { stroke: 'rgba(140,160,180,0.30)', width: 0.7, dash: '2,4' },
  '合作':        { stroke: 'rgba(140,160,180,0.30)', width: 0.7, dash: '2,4' },
  '友谊':        { stroke: 'rgba(140,160,180,0.25)', width: 0.6, dash: '2,4' },
  '对话':        { stroke: 'rgba(140,160,180,0.28)', width: 0.7, dash: '2,4' },
  '注释':        { stroke: 'rgba(150,140,120,0.22)', width: 0.6, dash: '2,4' },
  '战友':        { stroke: 'rgba(140,160,180,0.28)', width: 0.7, dash: '2,4' },
};
const DEFAULT_EDGE = EDGE_STYLES['影响'] || { stroke: 'rgba(196,149,106,0.35)', width: 1.0, dash: '4,3' };

const BG_STARS = Array.from({ length: 40 }, () => ({
  cx: Math.random() * 800, cy: Math.random() * 560,
  r: Math.random() * 1.2 + 0.3,
  opacity: Math.random() * 0.25 + 0.05,
}));

export default function ConstellationMap({ thinkers, relations, SUB_COLORS = {} }) {
  const [hovered, setHovered] = useState(null);
  const [selected, setSelected] = useState(null);
  const navigate = useNavigate();

  const focusNode = selected || hovered;
  const isConnected = (name) => {
    if (!focusNode) return true;
    const connected = new Set();
    (relations || []).forEach(r => {
      if (r.from === focusNode || r.to === focusNode) { connected.add(r.from); connected.add(r.to); }
    });
    return connected.has(name) || name === focusNode;
  };

  const getNodeSize = (t) => {
    const inf = t.influence || 5;
    if (inf >= 10) return 26;
    if (inf >= 9) return 22;
    if (inf >= 8) return 18;
    if (inf >= 7) return 15;
    return 13;
  };

  // Bezier curve midpoint offset
  const bezierMid = (x1, y1, x2, y2, curvature = 0.12) => {
    const mx = (x1 + x2) / 2;
    const my = (y1 + y2) / 2;
    const dx = x2 - x1;
    const dy = y2 - y1;
    const len = Math.sqrt(dx * dx + dy * dy) || 1;
    return { cx: mx - (dy / len) * len * curvature, cy: my + (dx / len) * len * curvature };
  };

  return (
    <section style={{ padding: `${SPACE.hero}px 20px 40px`, background: 'var(--bg)', position: 'relative', overflow: 'hidden' }}>
      {/* Section header */}
      <div style={{ textAlign: 'center', marginBottom: 36 }}>
        <span style={{ fontSize: 10, fontWeight: 500, letterSpacing: '0.24em', textTransform: 'uppercase', color: 'var(--ochre)', fontFamily: FONT.sans }}>Intellectual Constellation</span>
        <h2 style={{ fontSize: 28, fontWeight: 400, color: 'var(--ink)', margin: '6px 0 0', fontFamily: FONT.serif, letterSpacing: '0.04em' }}>思想星丛</h2>
        <div style={{ width: 28, height: 1, background: 'var(--ochre)', margin: '14px auto 0', opacity: 0.4 }} />
      </div>

      {/* Legend */}
      <div style={{ maxWidth: 700, margin: '0 auto 20px', display: 'flex', gap: 20, justifyContent: 'center', flexWrap: 'wrap', fontFamily: FONT.sans, fontSize: 10, color: 'var(--fade)', alignItems: 'center' }}>
        {[
          { label: '传承', ds: '', sw: 2.0, sc: 'rgba(196,149,106,0.55)' },
          { label: '影响', ds: '4,3', sw: 1.2, sc: 'rgba(196,149,106,0.35)' },
          { label: '批判', ds: '8,5', sw: 1.2, sc: 'rgba(180,70,70,0.45)' },
          { label: '交流', ds: '2,4', sw: 0.8, sc: 'rgba(140,160,180,0.30)' },
        ].map((item, i) => (
          <span key={i} style={{ display: 'inline-flex', alignItems: 'center', gap: 5, opacity: 0.55 }}>
            <svg width={24} height={8}><line x1={0} y1={4} x2={22} y2={4} stroke={item.sc} strokeWidth={item.sw} strokeDasharray={item.ds} /></svg>
            {item.label}
          </span>
        ))}
      </div>

      {/* Constellation canvas */}
      <div style={{ width: '100%', maxWidth: 960, height: 620, margin: '0 auto', position: 'relative', overflow: 'hidden', borderRadius: 12, border: '1px solid var(--border)' }}>
        {/* Starfield background */}
        <div style={{ position: 'absolute', inset: 0, background: 'radial-gradient(ellipse at 50% 45%, rgba(196,149,106,0.06) 0%, rgba(20,16,10,0.03) 50%, transparent 80%)' }} />
        <div style={{ position: 'absolute', inset: 0, background: 'radial-gradient(ellipse at 30% 60%, rgba(58,90,124,0.04) 0%, transparent 50%)' }} />

        <svg viewBox="0 0 800 560" style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%' }}
          onClick={() => { setSelected(null); setHovered(null); }}>
          <defs>
            <radialGradient id="starGlow" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="rgba(255,220,160,0.15)"/>
              <stop offset="100%" stopColor="rgba(255,220,160,0)"/>
            </radialGradient>
            <filter id="nodeGlow"><feGaussianBlur stdDeviation="2.5" result="blur"/><feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
          </defs>

          {/* Background stars */}
          {BG_STARS.map((s, i) => (
            <circle key={`star-${i}`} cx={s.cx} cy={s.cy} r={s.r} fill="var(--ochre)" opacity={s.opacity} />
          ))}

          {/* EDGES — Bézier curves */}
          {(relations || []).filter(Boolean).map((r, i) => {
            const from = thinkers.find(t => t.name === r.from);
            const to = thinkers.find(t => t.name === r.to);
            if (!from || !to) return null;
            const style = EDGE_STYLES[r.type] || DEFAULT_EDGE;
            const isRelevant = focusNode ? (r.from === focusNode || r.to === focusNode) : true;
            const opacity = focusNode ? (isRelevant ? 1 : 0.04) : 1;
            const { cx, cy } = bezierMid(from._x, from._y, to._x, to._y);

            return (
              <g key={`edge-${i}`}>
                {isRelevant && focusNode && (
                  <path d={`M${from._x},${from._y} Q${cx},${cy} ${to._x},${to._y}`}
                    fill="none" stroke={style.stroke} strokeWidth={style.width + 3} opacity={0.12}
                    strokeDasharray={style.dash} />
                )}
                <path d={`M${from._x},${from._y} Q${cx},${cy} ${to._x},${to._y}`}
                  fill="none" stroke={style.stroke} strokeWidth={style.width}
                  strokeDasharray={style.dash} opacity={opacity}
                  style={{ transition: 'opacity 0.4s ease' }} />
              </g>
            );
          })}

          {/* NODES */}
          {thinkers.map((t, i) => {
            const baseSize = getNodeSize(t);
            const isFoc = t.name === focusNode;
            const isConn = isConnected(t.name);
            const color = SUB_COLORS[t.sub] || 'var(--ochre)';
            const dimmed = focusNode && !isFoc && !isConn;

            return (
              <g key={`node-${i}`} style={{ cursor: 'pointer' }}
                opacity={dimmed ? 0.18 : 1}
                onClick={(e) => {
                  e.stopPropagation();
                  if (selected === t.name) { setSelected(null); navigate('/author/' + encodeURIComponent(t.name)); }
                  else { setSelected(selected === t.name ? null : t.name); }
                }}
                onMouseEnter={() => setHovered(t.name)}
                onMouseLeave={() => setHovered(null)}>

                {/* Outer glow ring (focus only) */}
                {isFoc && <circle cx={t._x} cy={t._y} r={baseSize + 10} fill="url(#starGlow)" opacity={0.6} />}

                {/* Main node circle */}
                <circle cx={t._x} cy={t._y} r={isFoc ? baseSize * 1.2 : baseSize}
                  fill={isFoc ? color : 'var(--bg)'}
                  stroke={color}
                  strokeWidth={isFoc ? 2 : 1.2}
                  filter={isFoc ? 'url(#nodeGlow)' : 'none'}
                  style={{ transition: 'all 0.5s cubic-bezier(0.22,1,0.36,1)' }} />

                {/* Inner accent ring for high-influence nodes */}
                {t.influence >= 9 && (
                  <circle cx={t._x} cy={t._y} r={baseSize - 4} fill="none" stroke={color} strokeWidth={0.4} opacity={0.5} />
                )}

                {/* Initial letter */}
                <text x={t._x} y={t._y + (baseSize > 18 ? 4.5 : 3)} textAnchor="middle"
                  fill={isFoc ? '#fff' : 'var(--ink)'} fontSize={baseSize > 20 ? 12 : 9}
                  fontFamily={FONT.serif} fontWeight={700}
                  style={{ transition: 'all 0.3s', pointerEvents: 'none' }}>
                  {t.name[0]}
                </text>

                {/* Name label — hover/click only */}
                {isFoc && (
                  <g style={{ pointerEvents: 'none' }}>
                    <text x={t._x} y={t._y + baseSize + 16} textAnchor="middle"
                      fill="var(--ink)" fontSize={11} fontFamily={FONT.sans}
                      fontWeight={500}>{t.name}</text>
                    {t.sub && (
                      <text x={t._x} y={t._y + baseSize + 29} textAnchor="middle"
                        fill={color} fontSize={9} fontFamily={FONT.sans}
                        fontWeight={400} opacity={0.8}>{t.sub}</text>
                    )}
                  </g>
                )}
              </g>
            );
          })}

          {/* Detail card — top layer */}
          {focusNode && thinkers.filter(t => t.name === focusNode).map(t => {
            const bs = getNodeSize(t);
            const co = SUB_COLORS[t.sub] || 'var(--ochre)';
            const panelH = 78, panelW = 170;
            const aboveY = t._y - bs - panelH - 14;
            const belowY = t._y + bs + 14;
            const showBelow = aboveY < 12;
            const py = showBelow ? belowY : aboveY;
            const px = Math.max(panelW / 2 + 6, Math.min(800 - panelW / 2 - 6, t._x));
            const key = `detail-${t.name}`;
            return (
              <g key={key} style={{ pointerEvents: 'none' }}>
                <rect x={px - panelW / 2} y={py} width={panelW} height={panelH} rx={7}
                  fill="var(--bg)" stroke={co} strokeWidth={0.6} strokeOpacity={0.35}
                  filter="drop-shadow(0 4px 16px rgba(0,0,0,0.06))" />
                <text x={px} y={py + 16} textAnchor="middle" fill="var(--ink)"
                  fontSize={12} fontFamily={FONT.serif} fontWeight={600}>{t.name}</text>
                <foreignObject x={px - panelW / 2 + 10} y={py + 22} width={panelW - 20} height={50}>
                  <div style={{ fontFamily: FONT.sans, fontSize: 9, color: 'var(--text-dim)', lineHeight: 1.55, textAlign: 'center' }}>
                    <span style={{ color: co, fontWeight: 500 }}>{t.sub || ''}</span>
                    <br/><span>{t.era || ''}{t.key ? ' · ' + t.key : ''}</span>
                    {Array.isArray(t.works) && t.works.length > 0 && (
                      <><br/><span style={{ color: 'var(--fade)', fontSize: 8 }}>{t.works.length} 部著作</span></>
                    )}
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
