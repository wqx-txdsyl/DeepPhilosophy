import { FONT, SPACE, WIDTH } from './tokens';

const TIMELINE_COLORS = { birth: '#C4956A', death: '#8B5A5A', book: '#3A5A7C', idea: '#5A8A5A', event: '#C4956A' };

export default function TimelineSection({ timeline = [] }) {
  return (
    <section style={{ padding: `${SPACE.xxxl}px 20px` }}>
      <h2 style={{ fontSize: 28, fontWeight: 600, color: 'var(--ink)', marginBottom: 40, textAlign: 'center', fontFamily: FONT.serif }}>思想史时间轴</h2>
      <div style={{ position: 'relative', maxWidth: WIDTH.wide, margin: '0 auto' }}>
        <div style={{ position: 'absolute', left: '50%', top: 0, bottom: 0, width: 1, background: 'var(--border)', transform: 'translateX(-50%)' }} />
        <div style={{ display: 'flex', flexDirection: 'column', gap: 32 }}>
          {timeline.map((ev, i) => {
            const isLeft = i % 2 === 0;
            const color = TIMELINE_COLORS[ev.type] || '#C4956A';
            return (
              <div key={i} style={{ display: 'flex', alignItems: 'center', position: 'relative', minHeight: 80 }}>
                <div style={{ flex: 1, display: 'flex', justifyContent: 'flex-end', paddingRight: 30 }}>
                  {isLeft && <TimelineCard ev={ev} color={color} />}
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: 80, flexShrink: 0 }}>
                  <div style={{ width: 10, height: 10, borderRadius: '50%', background: color, border: '2px solid var(--bg)', zIndex: 1 }} />
                  <span style={{ fontSize: 10, fontWeight: 600, color: 'var(--ochre)', marginTop: 4, textAlign: 'center', fontFamily: FONT.sans }}>{ev.year}</span>
                </div>
                <div style={{ flex: 1, paddingLeft: 30 }}>
                  {!isLeft && <TimelineCard ev={ev} color={color} />}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}

function TimelineCard({ ev, color }) {
  return (
    <div style={{
      maxWidth: 340, background: 'var(--card-bg)', borderRadius: 10, padding: '10px 16px',
      borderLeft: `3px solid ${color}`,
    }}>
      <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--ink)', marginBottom: 2, fontFamily: FONT.serif }}>{ev.event}</div>
      <div style={{ fontSize: 11, color: 'var(--text-dim)', lineHeight: 1.5, fontFamily: FONT.sans, fontWeight: 300 }}>{ev.detail}</div>
    </div>
  );
}
