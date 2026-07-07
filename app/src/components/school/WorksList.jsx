import { useState } from 'react';
import { FONT, SPACE, WIDTH } from './tokens';

export default function WorksList({ works = [] }) {
  const [hovered, setHovered] = useState(null);
  if (!works.length) return null;

  return (
    <section style={{ padding: `${SPACE.xl}px 24px`, maxWidth: WIDTH.prose, margin: '0 auto' }}>
      <div style={{ marginBottom: 36 }}>
        <span style={{ fontSize: 11, fontWeight: 500, letterSpacing: '0.2em', textTransform: 'uppercase', color: 'var(--fade)', fontFamily: FONT.sans }}>Chapter 5</span>
        <h2 style={{ fontSize: 26, fontWeight: 400, color: 'var(--ink)', margin: '4px 0 0', fontFamily: FONT.serif, letterSpacing: '0.03em' }}>重要著作</h2>
        <div style={{ width: 24, height: 1.5, background: 'var(--ochre)', margin: '12px 0 0', opacity: 0.5 }} />
      </div>
      {(works || []).filter(Boolean).map((work, i) => {
        const isOpen = hovered === i;
        return (
          <div key={i} style={{
            padding: '14px 0', borderBottom: '1px solid var(--border)', cursor: 'pointer',
            transition: 'border-color 0.25s'
          }}
            onClick={() => setHovered(isOpen ? null : i)}
            onMouseEnter={e => e.currentTarget.style.borderBottomColor = 'var(--accent)'}
            onMouseLeave={e => e.currentTarget.style.borderBottomColor = 'var(--border)'}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', flexWrap: 'wrap', gap: 8 }}>
              <h4 style={{ fontSize: 17, fontWeight: 400, fontStyle: 'italic', color: 'var(--ink)', margin: 0, fontFamily: FONT.serif }}>
                《{String(work.title).replace(/^《|》$/g, '')}》
              </h4>
              <span style={{ fontSize: 12, color: 'var(--fade)', fontFamily: FONT.sans }}>{work.author}{work.era ? ' · ' + work.era : ''}</span>
            </div>
            {isOpen && work.desc && (
              <p style={{ fontSize: 13, fontWeight: 300, color: 'var(--text-dim)', lineHeight: 1.8, margin: '10px 0 0', fontFamily: FONT.sans }}>{work.desc}</p>
            )}
          </div>
        );
      })}
    </section>
  );
}
