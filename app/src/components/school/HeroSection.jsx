import { useNavigate } from 'react-router-dom';
import { FONT, SPACE } from './tokens';

export default function HeroSection({ name, subtitle, quote, quoteAuthor, heroImage, englishName }) {
  const navigate = useNavigate();
  return (
    <section style={{
      minHeight: '100vh', display: 'flex', flexDirection: 'column', justifyContent: 'center',
      alignItems: 'center', textAlign: 'center', padding: `${SPACE.xxxl}px ${SPACE.xl}px`,
      position: 'relative', overflow: 'hidden',
      backgroundImage: heroImage, backgroundSize: 'cover', backgroundPosition: 'center',
    }}>
      {/* Lighter overlay — let the architecture breathe */}
      <div style={{ position: 'absolute', inset: 0,
        background: 'linear-gradient(to top, rgba(244,240,235,0.82) 0%, rgba(244,240,235,0.45) 35%, rgba(244,240,235,0.15) 100%)' }} />

      <button onClick={() => navigate('/genealogy')} style={{
        position: 'absolute', top: SPACE.lg, left: SPACE.lg, zIndex: 10,
        fontFamily: FONT.sans, fontSize: 13, color: 'var(--ochre)', background: 'rgba(244,240,235,0.5)',
        border: '1px solid rgba(196,149,106,0.3)', borderRadius: 4,
        cursor: 'pointer', letterSpacing: '0.04em', transition: 'all 0.25s', padding: '6px 14px'
      }}
        onMouseEnter={e => { e.currentTarget.style.background = 'rgba(244,240,235,0.8)'; e.currentTarget.style.borderColor = 'var(--ochre)'; }}
        onMouseLeave={e => { e.currentTarget.style.background = 'rgba(244,240,235,0.5)'; e.currentTarget.style.borderColor = 'rgba(196,149,106,0.3)'; }}
      >← 谱系</button>

      {/* Editorial kicker */}
      <p style={{
        fontSize: 11, fontWeight: 500, letterSpacing: '0.25em', textTransform: 'uppercase',
        color: 'var(--ochre)', marginBottom: SPACE.lg, position: 'relative', fontFamily: FONT.sans
      }}>{englishName || 'PHILOSOPHICAL SCHOOL'}</p>

      {/* Dramatic title — larger, bolder letter spacing */}
      <h1 style={{
        fontSize: 'clamp(3rem, 8vw, 5.5rem)', fontWeight: 400, fontStyle: 'italic',
        color: 'var(--ink)', margin: 0, position: 'relative', letterSpacing: '0.015em',
        lineHeight: 1.05, fontFamily: FONT.serif
      }}>{name}</h1>

      {/* Refined divider — thinner, more elegant */}
      <div style={{ width: 60, height: 1.5, background: 'var(--ochre)', margin: `${SPACE.lg}px 0`, opacity: 0.7 }} />

      {/* Quote as visual pause — larger, more breathing room */}
      <blockquote style={{
        fontSize: 'clamp(1.3rem, 2.8vw, 1.8rem)', fontStyle: 'italic', color: 'var(--text-dim)',
        maxWidth: 640, lineHeight: 1.75, margin: '0 0 16px', position: 'relative', fontWeight: 300,
        fontFamily: FONT.serif, letterSpacing: '0.01em'
      }}>
        <span style={{ color: 'var(--ochre)', fontSize: '2em', lineHeight: 0, verticalAlign: 'middle', opacity: 0.6, marginRight: 6 }}>&#x201C;</span>
        {quote}
        <span style={{ color: 'var(--ochre)', fontSize: '2em', lineHeight: 0, verticalAlign: 'middle', opacity: 0.6, marginLeft: 6 }}>&#x201D;</span>
      </blockquote>
      <p style={{ fontSize: 14, color: 'var(--ink)', fontWeight: 500, fontFamily: FONT.sans, letterSpacing: '0.04em' }}>{quoteAuthor}</p>

      {/* Scroll indicator — softer */}
      <div style={{ position: 'absolute', bottom: 36, opacity: 0.5 }}>
        <span style={{ fontSize: 20, color: 'var(--text-dim)', display: 'block', animation: 'pulse 2s ease-in-out infinite' }}>&darr;</span>
      </div>
    </section>
  );
}
