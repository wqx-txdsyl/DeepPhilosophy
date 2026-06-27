import { useNavigate } from 'react-router-dom';
import { FONT, SPACE } from './tokens';

export default function HeroSection({ name, subtitle, quote, quoteAuthor, heroImage }) {
  const navigate = useNavigate();
  return (
    <section style={{
      minHeight: '100vh', display: 'flex', flexDirection: 'column', justifyContent: 'center',
      alignItems: 'center', textAlign: 'center', padding: `${SPACE.xxxl}px ${SPACE.xl}px`,
      position: 'relative', overflow: 'hidden',
      backgroundImage: heroImage, backgroundSize: 'cover', backgroundPosition: 'center',
    }}>
      <div style={{ position: 'absolute', inset: 0,
        background: 'linear-gradient(to top, rgba(244,240,235,0.88) 0%, rgba(244,240,235,0.55) 40%, rgba(244,240,235,0.3) 100%)' }} />
      <button onClick={() => navigate('/genealogy')} style={{
        position: 'absolute', top: SPACE.lg, left: SPACE.lg, zIndex: 10,
        fontFamily: FONT.sans, fontSize: 13, color: 'var(--text-dim)', background: 'none', border: 'none', cursor: 'pointer'
      }}>← 谱系</button>
      <p style={{
        fontSize: 14, color: 'var(--ochre)', letterSpacing: 2, textTransform: 'uppercase',
        marginBottom: SPACE.md, position: 'relative', fontFamily: FONT.sans
      }}>{subtitle}</p>
      <h1 style={{
        fontSize: 'clamp(2.8rem, 7vw, 4.5rem)', fontWeight: 400, fontStyle: 'italic',
        color: 'var(--ink)', margin: 0, position: 'relative', letterSpacing: '0.02em', fontFamily: FONT.serif
      }}>{name}</h1>
      <div style={{ width: 80, height: 3, background: 'var(--ochre)', margin: `${SPACE.md}px 0 ${SPACE.lg}px` }} />
      <blockquote style={{
        fontSize: 'clamp(1.2rem, 2.5vw, 1.6rem)', fontStyle: 'italic', color: 'var(--text-dim)',
        maxWidth: 620, lineHeight: 1.8, margin: '0 0 12px', position: 'relative', fontWeight: 300, fontFamily: FONT.serif
      }}>
        &ldquo;{quote}&rdquo;
      </blockquote>
      <p style={{ fontSize: 14, color: 'var(--ochre)', fontWeight: 500, fontFamily: FONT.sans }}>&mdash; {quoteAuthor}</p>
      <div style={{ position: 'absolute', bottom: 40, animation: 'pulse 1.5s infinite' }}>
        <span style={{ fontSize: 24, color: 'var(--border)' }}>↓</span>
      </div>
    </section>
  );
}
