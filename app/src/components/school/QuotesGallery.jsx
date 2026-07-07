import { useState } from 'react';
import { FONT, SPACE, WIDTH } from './tokens';

export default function QuotesGallery({ quotes = [] }) {
  const [hovered, setHovered] = useState(null);
  if (!quotes.length) return null;

  return (
    <section style={{ padding: `${SPACE.xxxl}px 30px`, maxWidth: WIDTH.wide, margin: '0 auto' }}>
      <div style={{ textAlign: 'center', marginBottom: 48 }}>
        <span style={{ fontSize: 11, fontWeight: 500, letterSpacing: '0.2em', textTransform: 'uppercase', color: 'var(--fade)', fontFamily: FONT.sans }}>Golden Quotes</span>
        <h2 style={{ fontSize: 26, fontWeight: 400, color: 'var(--ink)', margin: '4px 0 0', fontFamily: FONT.serif, letterSpacing: '0.03em' }}>金句</h2>
        <div style={{ width: 24, height: 1.5, background: 'var(--ochre)', margin: '12px auto 0', opacity: 0.5 }} />
      </div>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 14, justifyContent: 'center', alignItems: 'center' }}>
        {(quotes || []).filter(Boolean).map((q, i) => {
          const hash = q.text.split('').reduce((s, c) => s + c.charCodeAt(0), 0);
          const sz = 14 + (hash % 14);
          const wt = 300 + (hash % 4) * 100;
          const rot = (hash % 7 - 3);
          const isHov = hovered === i;
          return (
            <div key={i} style={{ position: 'relative' }}
              onMouseEnter={() => setHovered(i)} onMouseLeave={() => setHovered(null)}>
              <div style={{
                fontSize: sz, fontWeight: wt, fontFamily: FONT.serif, fontStyle: 'italic',
                color: isHov ? 'var(--ochre)' : 'var(--ink)', cursor: 'pointer',
                opacity: hovered != null && !isHov ? 0.35 : 0.75,
                transition: 'all 0.35s cubic-bezier(0.4,0,0.2,1)',
                transform: `rotate(${isHov ? 0 : rot}deg) scale(${isHov ? 1.25 : 1})`,
                padding: '4px 10px', lineHeight: 1.4,
              }}>
                &ldquo;{q.text.length > 20 ? q.text.substring(0, 18) + '…' : q.text}&rdquo;
              </div>
              {isHov && (
                <div style={{
                  position: 'absolute', bottom: '100%', left: '50%', transform: 'translateX(-50%)',
                  background: 'rgba(248,244,238,0.98)', border: '1px solid var(--border)',
                  borderRadius: 10, padding: '14px 20px', zIndex: 30, width: 320,
                  boxShadow: '0 6px 30px rgba(0,0,0,0.15)', marginBottom: 10,
                }}>
                  <div style={{ fontSize: 14, lineHeight: 1.7, color: 'var(--text)', marginBottom: 8, fontFamily: FONT.serif, fontStyle: 'italic' }}>&ldquo;{q.text}&rdquo;</div>
                  <div style={{ fontSize: 11, color: 'var(--ochre)', marginBottom: 6, fontFamily: FONT.sans }}>&mdash; {q.author}</div>
                  <div style={{ fontSize: 12, color: 'var(--text-dim)', lineHeight: 1.6, fontFamily: FONT.sans, fontWeight: 300 }}>{q.exp}</div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </section>
  );
}
