import { useNavigate } from 'react-router-dom';
import { FONT, SPACE, WIDTH } from './tokens';

export default function EpilogueSection({ conclusion, closingQuote }) {
  const navigate = useNavigate();
  return (
    <section style={{ padding: `${SPACE.hero}px ${SPACE.xl}px`, maxWidth: WIDTH.prose, margin: '0 auto', textAlign: 'center' }}>
      {/* Ornamental divider */}
      <div style={{ width: 48, height: 1, background: 'var(--fade)', margin: '0 auto 48px', opacity: 0.4 }} />
      <div style={{ width: 4, height: 4, borderRadius: '50%', background: 'var(--ochre)', margin: '-2.5px auto 48px', opacity: 0.5 }} />

      <h2 style={{ fontSize: 20, fontWeight: 400, color: 'var(--fade)', marginBottom: 40, fontFamily: FONT.serif, letterSpacing: '0.06em', textTransform: 'uppercase' }}>Epilogue</h2>

      <div style={{ fontSize: 16, lineHeight: 2.1, color: 'var(--text)', whiteSpace: 'pre-line', marginBottom: 56, fontFamily: FONT.sans, fontWeight: 300, textAlign: 'left' }}>
        {conclusion}
      </div>

      {closingQuote && (
        <blockquote style={{
          fontSize: 'clamp(1.2rem, 2.5vw, 1.5rem)', fontStyle: 'italic', color: 'var(--text-dim)',
          maxWidth: 560, lineHeight: 1.7, margin: '0 auto 48px', fontWeight: 300, fontFamily: FONT.serif,
          border: 'none', padding: 0, position: 'relative'
        }}>
          <span style={{ color: 'var(--ochre)', fontSize: '2.5em', lineHeight: 0, verticalAlign: 'middle', opacity: 0.4 }}>&#x201C;</span>
          {closingQuote}
          <span style={{ color: 'var(--ochre)', fontSize: '2.5em', lineHeight: 0, verticalAlign: 'middle', opacity: 0.4 }}>&#x201D;</span>
        </blockquote>
      )}

      {/* Ornamental end mark */}
      <div style={{ width: 16, height: 1, background: 'var(--fade)', margin: '0 auto 40px', opacity: 0.3 }} />
      <p style={{ fontSize: 10, color: 'var(--fade)', letterSpacing: '0.2em', fontFamily: FONT.sans, fontWeight: 400, textTransform: 'uppercase' }}>Fin</p>

      <button onClick={() => navigate(-1)} style={{
        marginTop: 48, background: 'none', border: 'none', cursor: 'pointer',
        fontFamily: FONT.sans, fontSize: 13, color: 'var(--text-dim)', letterSpacing: '0.05em',
        transition: 'color 0.25s'
      }}
        onMouseEnter={e => e.currentTarget.style.color = 'var(--ink)'}
        onMouseLeave={e => e.currentTarget.style.color = 'var(--text-dim)'}>
        &larr; 返回上一页
      </button>
    </section>
  );
}
