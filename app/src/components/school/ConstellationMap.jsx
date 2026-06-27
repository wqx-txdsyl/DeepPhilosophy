import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { FONT, SPACE, WIDTH } from './tokens';

export default function ConstellationMap({ thinkers, relations, SUB_COLORS = {} }) {
  const [hovered, setHovered] = useState(null);
  const navigate = useNavigate();

  return (
    <section style={{ padding: `${SPACE.hero}px 20px`, background: 'var(--card-bg)', position: 'relative' }}>
      <div style={{ textAlign: 'center', marginBottom: 48 }}>
        <span style={{ fontSize: 11, fontWeight: 500, letterSpacing: '0.2em', textTransform: 'uppercase', color: 'var(--fade)', fontFamily: FONT.sans }}>Chapter 2</span>
        <h2 style={{ fontSize: 26, fontWeight: 400, color: 'var(--ink)', margin: '4px 0 0', fontFamily: FONT.serif, letterSpacing: '0.03em' }}>思想星丛</h2>
        <div style={{ width: 24, height: 1.5, background: 'var(--ochre)', margin: '12px auto 0', opacity: 0.5 }} />
      </div>
      <div style={{ width: '100%', maxWidth: WIDTH.wide, height: 600, margin: '0 auto', position: 'relative', overflow: 'hidden' }}>
        <div style={{ position: 'absolute', inset: 0, background: 'radial-gradient(ellipse at 50% 50%, rgba(196,149,106,0.06) 0%, transparent 70%)' }} />
        <svg viewBox="0 0 800 560" style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%' }}>
          {/* Explicit relations */}
          {relations.map((r, i) => {
            const from = thinkers.find(t => t.name === r.from);
            const to = thinkers.find(t => t.name === r.to);
            if (!from || !to) return null;
            const mx = (from._x + to._x) / 2, my = (from._y + to._y) / 2 - 20;
            const dash = r.type === '对立' ? '6,4' : r.type === '友谊' ? '4,4' : '';
            const isHov = hovered === `rel-${i}`;
            return (
              <g key={i} onMouseEnter={() => setHovered(`rel-${i}`)} onMouseLeave={() => setHovered(null)}>
                <path d={`M${from._x},${from._y} Q${mx},${my} ${to._x},${to._y}`}
                  fill="none" stroke={isHov ? 'var(--ochre)' : 'rgba(196,149,106,0.25)'}
                  strokeWidth={isHov ? 2 : 1.2} strokeDasharray={dash} style={{ transition: 'all 0.3s' }} />
                {isHov && <text x={mx} y={my - 8} textAnchor="middle" fontSize={9} fill="var(--text-dim)" fontStyle="italic">{r.type}</text>}
              </g>
            );
          })}
          {/* Auto sub-school lines */}
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
                      d={`M${group[a]._x},${group[a]._y} Q${(group[a]._x + group[b]._x) / 2},${(group[a]._y + group[b]._y) / 2 - 15} ${group[b]._x},${group[b]._y}`}
                      fill="none" stroke="rgba(196,149,106,0.1)" strokeWidth="0.8" strokeDasharray="5,6" />);
            });
            return lines;
          })()}
          {/* Nodes */}
          {thinkers.map((t, i) => {
            const r = 14 + (t.influence || 5) * 2;
            const color = SUB_COLORS[t.sub] || 'var(--ochre)';
            const isHov = hovered === `t-${i}`;
            const size = isHov ? r * 1.3 + 6 : r + 6;
            const showBelow = t._y < 350;
            return (
              <g key={i} style={{ cursor: 'pointer' }}
                onMouseEnter={() => setHovered(`t-${i}`)} onMouseLeave={() => setHovered(null)}
                onClick={() => navigate('/author/' + encodeURIComponent(t.name))}>
                <circle cx={t._x} cy={t._y} r={size} fill="var(--bone)" stroke={color}
                  strokeWidth={isHov ? 2.5 : 1.5} filter={isHov ? 'drop-shadow(0 0 6px rgba(196,149,106,0.4))' : 'none'}
                  style={{ transition: 'all 0.4s cubic-bezier(0.4,0,0.2,1)' }} />
                <text x={t._x} y={t._y + 4} textAnchor="middle" fill="var(--ink)" fontSize={10}
                  fontFamily={FONT.serif} fontWeight={600}>{t.name[0]}</text>
                <span style={{ position: 'absolute', left: t._x - 40, top: t._y + size + 4, width: 80, textAlign: 'center',
                  fontSize: 10, color: 'var(--ink)', fontWeight: isHov ? 600 : 400, transition: 'all 0.3s' }}>
                  {t.name}
                </span>
                {isHov && (
                  <foreignObject x={t._x - 65} y={showBelow ? t._y + size + 16 : t._y - size - 48} width={130} height={40}>
                    <div style={{ background: 'rgba(248,244,238,0.98)', border: '1px solid var(--border)', borderRadius: 8,
                      padding: '6px 12px', textAlign: 'center', fontSize: 11, fontFamily: FONT.sans }}>
                      <div style={{ color: 'var(--text-dim)' }}>{t.sub} &middot; {t.era}</div>
                      <div style={{ color: 'var(--ochre)', fontStyle: 'italic' }}>&ldquo;{t.key}&rdquo;</div>
                    </div>
                  </foreignObject>
                )}
              </g>
            );
          })}
        </svg>
      </div>
    </section>
  );
}
