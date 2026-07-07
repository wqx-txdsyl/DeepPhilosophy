import { FONT, SPACE, WIDTH } from './tokens';

const TIMELINE_COLORS = { birth: '#C4956A', death: '#8B5A5A', book: '#3A5A7C', idea: '#5A8A5A', event: '#C4956A' };

export default function TimelineSection({ timeline = [] }) {
  return (
    <section style={{ padding: `${SPACE.hero}px 20px`, background: 'var(--card-bg)' }}>
      <div style={{ maxWidth: WIDTH.wide, margin: '0 auto' }}>
        <div style={{ textAlign: 'center', marginBottom: 56 }}>
          <span style={{ fontSize: 11, fontWeight: 500, letterSpacing: '0.2em', textTransform: 'uppercase', color: 'var(--fade)', fontFamily: FONT.sans }}>Chapter 3</span>
          <h2 style={{ fontSize: 26, fontWeight: 400, color: 'var(--ink)', margin: '4px 0 0', fontFamily: FONT.serif, letterSpacing: '0.03em' }}>思想史时间轴</h2>
          <div style={{ width: 32, height: 1.5, background: 'var(--ochre)', margin: '16px auto 0', opacity: 0.5 }} />
        </div>

        <div style={{ position: 'relative' }}>
          {/* Thin center line — more elegant */}
          <div style={{ position: 'absolute', left: '50%', top: 0, bottom: 0, width: 1, background: 'var(--border)', transform: 'translateX(-50%)' }} />

          <div style={{ display: 'flex', flexDirection: 'column', gap: 40 }}>
            {(timeline || []).filter(Boolean).map((ev, i) => {
              const isLeft = i % 2 === 0;
              const color = TIMELINE_COLORS[ev.type] || '#C4956A';
              return (
                <div key={i} style={{ display: 'flex', alignItems: 'flex-start', position: 'relative' }}>
                  {/* Left side */}
                  <div style={{ flex: 1, display: 'flex', justifyContent: 'flex-end', paddingRight: 32 }}>
                    {isLeft && <TimelineCard ev={ev} color={color} />}
                  </div>
                  {/* Center dot */}
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: 80, flexShrink: 0, paddingTop: 8 }}>
                    <div style={{ width: 8, height: 8, borderRadius: '50%', background: color, border: '2px solid var(--card-bg)', zIndex: 1,
                      boxShadow: `0 0 6px ${color}40` }} />
                  </div>
                  {/* Right side */}
                  <div style={{ flex: 1, paddingLeft: 32 }}>
                    {!isLeft && <TimelineCard ev={ev} color={color} />}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </section>
  );
}

function TimelineCard({ ev, color }) {
  return (
    <div style={{
      maxWidth: 360, padding: '16px 20px',
      borderLeft: `2px solid ${color}`,
      transition: 'all 0.3s cubic-bezier(0.22,1,0.36,1)', cursor: 'default',
      background: 'transparent',
    }}
      onMouseEnter={e => { e.currentTarget.style.background = 'rgba(244,240,235,0.6)'; }}
      onMouseLeave={e => { e.currentTarget.style.background = 'transparent'; }}>
      <span style={{ fontSize: 10, fontWeight: 500, color: 'var(--ochre)', fontFamily: FONT.sans, letterSpacing: '0.08em', textTransform: 'uppercase' }}>{ev.year}</span>
      <div style={{ fontSize: 14, fontWeight: 500, color: 'var(--ink)', margin: '4px 0 4px', fontFamily: FONT.serif }}>{ev.event}</div>
      <div style={{ fontSize: 12, color: 'var(--text-dim)', lineHeight: 1.7, fontFamily: FONT.sans, fontWeight: 300 }}>{ev.detail}</div>
    </div>
  );
}
