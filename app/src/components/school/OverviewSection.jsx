import { useNavigate } from 'react-router-dom';
import { FONT, SPACE, WIDTH } from './tokens';

export default function OverviewSection({ overview, subSchools = [] }) {
  const navigate = useNavigate();
  return (
    <section style={{ padding: `${SPACE.xxxl}px ${SPACE.xl}px`, maxWidth: WIDTH.prose, margin: '0 auto' }}>
      {/* Editorial heading — numbered chapter feel */}
      <div style={{ marginBottom: SPACE.xl }}>
        <span style={{ fontSize: 11, fontWeight: 500, letterSpacing: '0.2em', textTransform: 'uppercase', color: 'var(--fade)', fontFamily: FONT.sans }}>Chapter 1</span>
        <h2 style={{ fontSize: 26, fontWeight: 400, color: 'var(--ink)', margin: '4px 0 0', fontFamily: FONT.serif, letterSpacing: '0.03em' }}>核心思想与流派脉络</h2>
        <div style={{ width: 32, height: 1.5, background: 'var(--ochre)', marginTop: SPACE.md, opacity: 0.5 }} />
      </div>
      <div style={{ fontSize: 16, lineHeight: 2.0, color: 'var(--text)', whiteSpace: 'pre-line', fontFamily: FONT.sans, fontWeight: 300 }}>
        {overview}
      </div>

      {subSchools.length > 0 && (
        <div style={{ marginTop: SPACE.xxxl }}>
          <h3 style={{ fontSize: 18, fontWeight: 400, color: 'var(--ink)', marginBottom: SPACE.lg, fontFamily: FONT.serif, letterSpacing: '0.04em' }}>下属流派</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: SPACE.md }}>
            {subSchools.map(sub => (
              <div key={sub.name} onClick={() => navigate('/school/' + encodeURIComponent(sub.name))} style={{
                padding: '20px 0', borderBottom: '1px solid var(--border)', transition: 'border-color 0.3s', cursor: 'pointer'
              }}
                onMouseEnter={e => e.currentTarget.style.borderBottomColor = 'var(--ochre)'}
                onMouseLeave={e => e.currentTarget.style.borderBottomColor = 'var(--border)'}>
                <div style={{ display: 'flex', alignItems: 'baseline', gap: 10, marginBottom: 6 }}>
                  <h4 style={{ fontSize: 16, fontWeight: 500, color: 'var(--ink)', margin: 0, fontFamily: FONT.serif }}>{sub.name}</h4>
                  <span style={{ fontSize: 11, color: 'var(--fade)', fontFamily: FONT.sans, fontWeight: 400 }}>{sub.era}</span>
                </div>
                <p style={{ fontSize: 13, color: 'var(--text-dim)', lineHeight: 1.8, margin: 0, fontFamily: FONT.sans, fontWeight: 300 }}>{sub.desc}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </section>
  );
}
