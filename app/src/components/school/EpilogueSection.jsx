import { useNavigate } from 'react-router-dom';
import { FONT, SPACE, WIDTH } from './tokens';

export default function EpilogueSection({ conclusion, closingQuote }) {
  const navigate = useNavigate();
  return (
    <section style={{ padding: `${SPACE.xxxl}px ${SPACE.xl}px`, maxWidth: WIDTH.prose, margin: '0 auto' }}>
      <h2 style={{ fontSize: 24, fontWeight: 600, color: 'var(--ink)', marginBottom: 24, fontFamily: FONT.serif }}>结语</h2>
      <div style={{ fontSize: 16, lineHeight: 2.0, color: 'var(--text)', whiteSpace: 'pre-line', marginBottom: 40, fontFamily: FONT.sans, fontWeight: 300 }}>
        {conclusion}
      </div>
      {closingQuote && (
        <blockquote style={{
          fontSize: 'clamp(1.1rem, 2vw, 1.4rem)', fontStyle: 'italic', color: 'var(--text-dim)',
          maxWidth: 620, lineHeight: 1.7, margin: '0 0 40px', fontWeight: 300, fontFamily: FONT.serif, border: 'none', padding: 0
        }}>
          &ldquo;{closingQuote}&rdquo;
        </blockquote>
      )}
      <button onClick={() => navigate('/genealogy')} style={{
        background: 'var(--card-bg)', border: '1px solid var(--border)', borderRadius: 8,
        padding: '10px 24px', cursor: 'pointer', fontFamily: FONT.sans, fontSize: 14, color: 'var(--text)',
        transition: 'all 0.25s'
      }}
        onMouseEnter={e => { e.currentTarget.style.borderColor = 'var(--ochre)'; e.currentTarget.style.color = 'var(--ochre)'; }}
        onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--border)'; e.currentTarget.style.color = 'var(--text)'; }}>
        ← 返回谱系
      </button>
    </section>
  );
}
