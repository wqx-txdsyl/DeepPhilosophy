import { useNavigate } from 'react-router-dom';
import { FONT, SPACE } from './tokens';

export default function HeroSection({ name, subtitle, quote, quoteAuthor, heroImage, englishName }) {
  const navigate = useNavigate();
  return (
    <section className="school-hero-section" style={{
      minHeight: '100vh', display: 'flex', flexDirection: 'column', justifyContent: 'center',
      alignItems: 'center', textAlign: 'center', padding: `${SPACE.xxxl}px ${SPACE.xl}px`,
      position: 'relative', overflow: 'hidden',
      backgroundImage: heroImage, backgroundSize: 'cover', backgroundPosition: 'center',
    }}>
      {/* Lighter overlay — let the architecture breathe */}
      <div style={{ position: 'absolute', inset: 0,
        background: 'linear-gradient(to top, rgba(244,240,235,0.82) 0%, rgba(244,240,235,0.45) 35%, rgba(244,240,235,0.15) 100%)' }} />

      <button onClick={() => navigate(-1)} style={{
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
        fontSize: 16, fontWeight: 800, letterSpacing: '0.3em', textTransform: 'uppercase',
        color: 'var(--ochre)', marginBottom: SPACE.lg, position: 'relative', fontFamily: FONT.sans
      }}>{englishName || 'PHILOSOPHICAL SCHOOL'}</p>

      {/* Dramatic title — size adapts to name length */}
      <h1 style={{
        fontSize: name.length > 12 ? 'clamp(2rem, 6vw, 3.5rem)' : name.length > 8 ? 'clamp(2.5rem, 8vw, 5rem)' : 'clamp(3rem, 10vw, 6rem)',
        fontWeight: 600, fontStyle: 'italic',
        color: 'var(--ink)', margin: 0, position: 'relative', letterSpacing: '0.015em',
        lineHeight: 1.15, fontFamily: FONT.serif, whiteSpace: 'nowrap'
      }}>{name}</h1>

      {/* Refined divider — thinner, more elegant */}
      <div style={{ width: 60, height: 1.5, background: 'var(--ochre)', margin: `${SPACE.lg}px 0`, opacity: 0.7 }} />

      {/* Quote as visual pause — larger, more breathing room */}
      <blockquote style={{
        fontSize: 'clamp(1.2rem, 2.5vw, 1.6rem)', fontStyle: 'italic', color: 'var(--ink)',
        maxWidth: 680, lineHeight: 1.7, margin: '0 0 16px', position: 'relative', fontWeight: 500,
        textShadow: '0 0 40px rgba(244,240,235,0.8)',
        fontFamily: FONT.serif, letterSpacing: '0.01em'
      }}>
        <span style={{ color: 'var(--ochre)', fontSize: '2em', lineHeight: 0, verticalAlign: 'middle', opacity: 0.7, marginRight: 6 }}>&#x201C;</span>{quote}<span style={{ color: 'var(--ochre)', fontSize: '2em', lineHeight: 0, verticalAlign: 'middle', opacity: 0.7, marginLeft: 6 }}>&#x201D;</span>
      </blockquote>
      <p style={{ fontSize: 16, color: 'var(--ochre)', fontWeight: 600, fontFamily: FONT.sans, letterSpacing: '0.04em' }}>{quoteAuthor}</p>

      <button onClick={() => document.getElementById('school-content')?.scrollIntoView({ behavior: 'smooth' })} style={{
        fontFamily: FONT.sans, fontSize: 14, fontWeight: 500, letterSpacing: '0.08em',
        color: '#fff', background: 'var(--ink)', border: 'none', borderRadius: 4,
        padding: '14px 36px', cursor: 'pointer', transition: 'all 0.25s', marginTop: 24, position: 'relative', zIndex: 1,
      }}
        onMouseEnter={e => { e.currentTarget.style.background = 'var(--ochre)'; }}
        onMouseLeave={e => { e.currentTarget.style.background = 'var(--ink)'; }}>
        开始探索 ↓
      </button>
    </section>
  );
}
