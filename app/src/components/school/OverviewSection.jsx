import { FONT, SPACE, WIDTH } from './tokens';

export default function OverviewSection({ overview, subSchools = [] }) {
  return (
    <section style={{ padding: `${SPACE.xxxl}px ${SPACE.xl}px`, maxWidth: WIDTH.prose, margin: '0 auto' }}>
      <h2 style={{ fontSize: 28, fontWeight: 600, color: 'var(--ink)', marginBottom: SPACE.lg, fontFamily: FONT.serif }}>核心思想与流派脉络</h2>
      <div style={{ fontSize: 16, lineHeight: 2.0, color: 'var(--text)', whiteSpace: 'pre-line', marginBottom: 40, fontFamily: FONT.sans, fontWeight: 300 }}>
        {overview}
      </div>
      {subSchools.length > 0 && (
        <>
          <h3 style={{ fontSize: 20, fontWeight: 600, color: 'var(--ochre)', marginBottom: 20, fontFamily: FONT.serif }}>下属流派</h3>
          {subSchools.map(sub => (
            <div key={sub.name} style={{
              background: 'var(--card-bg)', borderRadius: 10, padding: '16px 20px', marginBottom: 14,
              borderLeft: '3px solid var(--ochre)',
            }}>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: 10, marginBottom: 6 }}>
                <h4 style={{ fontSize: 16, fontWeight: 700, color: 'var(--ink)', margin: 0, fontFamily: FONT.serif }}>{sub.name}</h4>
                <span style={{ fontSize: 12, color: 'var(--ochre)', fontFamily: FONT.sans }}>{sub.era}</span>
              </div>
              <p style={{ fontSize: 14, color: 'var(--text-dim)', lineHeight: 1.8, margin: 0, fontFamily: FONT.sans, fontWeight: 300 }}>{sub.desc}</p>
            </div>
          ))}
        </>
      )}
    </section>
  );
}
