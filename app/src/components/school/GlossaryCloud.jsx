import { useState } from 'react';
import { FONT, SPACE } from './tokens';

export default function GlossaryCloud({ cihai = [] }) {
  const [hovered, setHovered] = useState(null);

  return (
    <section style={{ padding: `${SPACE.xxxl}px 30px`, maxWidth: 900, margin: '0 auto' }}>
      <h2 style={{ fontSize: 28, fontWeight: 600, color: 'var(--ink)', marginBottom: 12, textAlign: 'center', fontFamily: FONT.serif }}>辞海</h2>
      <p style={{ fontSize: 13, color: 'var(--text-dim)', textAlign: 'center', marginBottom: 32, fontFamily: FONT.sans }}>悬停词语查看释义与出处</p>
      <div style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'center', alignItems: 'baseline', gap: '2px 12px', padding: '20px 8px' }}>
        {cihai.map((item, i) => {
          const hash = item.word.split('').reduce((s, c) => s + c.charCodeAt(0), 0);
          const si = (hash * 7919 + i * 3571) % 53;
          const ss = [10, 28, 14, 20, 32, 11, 18, 34, 12, 15, 26, 10, 13, 30, 15, 22, 11, 17, 36, 12, 14, 24, 10, 27, 13, 19, 33, 11, 16, 29, 13, 15, 25, 10, 14, 21, 12, 15, 20, 11, 14, 26, 13, 17, 10, 16, 24, 12, 15, 18, 10, 28, 14];
          const ws = [300, 800, 400, 600, 900, 300, 400, 900, 300, 500, 700, 300, 300, 800, 400, 600, 300, 500, 900, 300, 400, 700, 300, 800, 300, 500, 900, 300, 400, 800, 300, 400, 600, 300, 400, 600, 300, 400, 500, 300, 400, 700, 300, 500, 300, 400, 600, 300, 400, 500, 300, 800, 400];
          const size = ss[si % ss.length];
          const weight = ws[si % ws.length];
          const r = (hash * 3571 + i * 719) % 41 - 20;
          const rot = r / 10;
          const extraPad = size > 22 ? '6px 10px' : size > 17 ? '4px 7px' : size > 13 ? '2px 5px' : '1px 3px';
          const topShift = (hash * 79 + i * 113) % 7 - 3;
          const isHov = hovered === item.word;
          return (
            <span key={i} style={{
              fontSize: size, fontWeight: weight, padding: extraPad, cursor: 'pointer', position: 'relative',
              top: topShift + 'px', zIndex: isHov ? 20 : 1,
              color: isHov ? 'var(--ochre)' : 'var(--ink)',
              opacity: hovered ? (isHov ? 1 : 0.3) : 0.62 + (size - 10) * 0.013,
              transition: 'all 0.35s cubic-bezier(0.4,0,0.2,1)',
              fontFamily: size > 16 ? FONT.serif : FONT.sans,
              transform: isHov ? 'scale(1.3) rotate(0deg)' : `rotate(${rot}deg)`,
            }}
              onMouseEnter={() => setHovered(item.word)} onMouseLeave={() => setHovered(null)}>
              {item.word}
              {isHov && (
                <div style={{
                  position: 'absolute', bottom: '100%', left: '50%', transform: 'translateX(-50%)',
                  background: 'rgba(248,244,238,0.98)', border: '1px solid var(--border)',
                  borderRadius: 10, padding: '14px 20px', zIndex: 30, width: 320,
                  boxShadow: '0 6px 30px rgba(0,0,0,0.15)', marginBottom: 10,
                }}>
                  <div style={{ fontSize: 14, lineHeight: 1.7, color: 'var(--text)', marginBottom: 8, fontFamily: FONT.sans }}>{item.def}</div>
                  <div style={{ fontSize: 11, color: 'var(--ochre)', fontStyle: 'italic', borderTop: '1px solid var(--border)', paddingTop: 6, fontFamily: FONT.sans }}>{item.source}</div>
                </div>
              )}
            </span>
          );
        })}
      </div>
    </section>
  );
}
