"""
Inject new 7-chapter dark museum theme JSX into SchoolDetailPage.
Keeps all data definitions and logic intact.
"""
import re

TARGET = r"C:\Users\wqx_0\PyCharmProjects\Q&ASystem\DeepPhilosophy\app\src\pages\SchoolDetailPage.jsx"

with open(TARGET, 'r', encoding='utf-8') as f:
    content = f.read()

# Backup
with open(TARGET + ".ui_bak", 'w', encoding='utf-8') as f:
    f.write(content)

# Find the return statement
return_start = content.find('\n  return (', content.find('const [hovered, setHovered]'))
if return_start < 0:
    print("ERROR: Could not find return statement")
    exit(1)

# Find the last line (export default)
export_line = content.rfind('\nexport default SchoolDetailPage;')

# Build new JSX
new_jsx = r"""
  return (
    <div className="school-detail-dark" style={{ position: 'relative', zIndex: 1 }}>
      {/* ══════════ Scroll Progress Bar ══════════ */}
      <div style={{ position: 'fixed', top: 0, left: 0, height: 2, zIndex: 9999,
        background: 'var(--gold)', width: 'var(--scroll-pct, 0%)', transition: 'width 0.1s' }} />

      {/* ══════════ Chapter 1: HERO ══════════ */}
      <section data-section="hero" style={{ position: 'relative', height: '100vh', width: '100%', overflow: 'hidden' }}>
        <div style={{ position: 'absolute', inset: 0, backgroundImage: heroImage, backgroundSize: 'cover', backgroundPosition: 'center' }} />
        <div style={{ position: 'absolute', inset: 0, background: 'linear-gradient(to top, #0A0908 0%, rgba(10,9,8,0.6) 40%, rgba(10,9,8,0.2) 100%)' }} />
        <div style={{ position: 'absolute', inset: 0, background: 'radial-gradient(circle at 70% 30%, rgba(201,169,110,0.08) 0%, transparent 60%)' }} />
        <button onClick={() => navigate('/genealogy')} style={{ position: 'absolute', top: 24, left: 24, zIndex: 10,
          background: 'var(--glass-bg)', border: 'var(--glass-border)', borderRadius: 8, padding: '8px 16px',
          color: 'var(--text-secondary)', fontSize: 13, cursor: 'pointer', backdropFilter: 'blur(12px)' }}>← 谱系</button>
        <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', textAlign: 'center', padding: '0 24px' }}>
          <h1 style={{ fontSize: 'clamp(2.5rem, 8vw, 7rem)', fontFamily: 'var(--font-serif)', fontWeight: 300, letterSpacing: '0.12em', color: 'var(--text-primary)', lineHeight: 1, margin: 0 }}>{data.name}</h1>
          <div style={{ width: 96, height: 1.5, background: 'linear-gradient(to right, transparent, var(--gold), transparent)', margin: '24px 0' }} />
          <blockquote style={{ maxWidth: 720, fontSize: 'clamp(1.1rem, 2.5vw, 1.6rem)', fontFamily: 'var(--font-serif)', fontStyle: 'italic', color: 'var(--text-secondary)', lineHeight: 1.7, border: 'none', padding: 0, margin: 0 }}>
            <span style={{ color: 'var(--gold)', fontSize: '3rem', lineHeight: 0, verticalAlign: 'middle', marginRight: 8 }}>“</span>
            {data.quote}
            <span style={{ color: 'var(--gold)', fontSize: '3rem', lineHeight: 0, verticalAlign: 'middle', marginLeft: 8 }}>”</span>
          </blockquote>
          <p style={{ marginTop: 16, color: 'var(--text-muted)', fontSize: 14, fontStyle: 'italic' }}>—— {data.quoteAuthor}</p>
          {data.subtitle && <p style={{ marginTop: 24, color: 'var(--text-secondary)', fontSize: 16, maxWidth: 560, fontFamily: 'var(--font-sans)', fontWeight: 300 }}>{data.subtitle}</p>}
        </div>
        <div style={{ position: 'absolute', bottom: 48, left: '50%', transform: 'translateX(-50%)', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8, color: 'rgba(201,169,110,0.5)' }}>
          <span style={{ fontSize: 11, letterSpacing: '0.2em', fontFamily: 'var(--font-sans)' }}>SCROLL</span>
          <span style={{ fontSize: 20, animation: 'pulse-ring 2s ease-out infinite' }}>↓</span>
        </div>
      </section>

      {/* ══════════ Chapter 2: OVERVIEW ══════════ */}
      <section data-section="overview" style={{ maxWidth: 1100, margin: '0 auto', padding: '96px 24px' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: 48 }}>
          <div>
            <span style={{ fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.3em', color: 'var(--gold)', fontFamily: 'var(--font-sans)' }}>关于此谱系</span>
            <div style={{ fontSize: 'clamp(1rem, 1.6vw, 1.2rem)', fontFamily: 'var(--font-sans)', fontWeight: 300, color: 'var(--text-primary)', lineHeight: 2, whiteSpace: 'pre-line', borderLeft: '2px solid rgba(201,169,110,0.4)', paddingLeft: 24, marginTop: 16 }}>
              {data.overview}
            </div>
          </div>
          {subSchools && subSchools.length > 0 && (
            <div>
              <h3 style={{ fontSize: 22, fontFamily: 'var(--font-serif)', color: 'var(--gold)', marginBottom: 20 }}>下属流派</h3>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: 12 }}>
                {subSchools.map((s, i) => (
                  <div key={i} style={{ background: 'rgba(26,24,22,0.4)', backdropFilter: 'blur(8px)', padding: 20, borderBottom: '1px solid rgba(201,169,110,0.2)', transition: 'all 0.3s' }}
                    onMouseEnter={e => e.currentTarget.style.borderBottomColor = 'rgba(201,169,110,0.7)'}
                    onMouseLeave={e => e.currentTarget.style.borderBottomColor = 'rgba(201,169,110,0.2)'}>
                    <h4 style={{ fontFamily: 'var(--font-serif)', fontSize: 18, color: 'var(--gold)', margin: '0 0 4px' }}>{s.name}</h4>
                    <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>{s.era}</span>
                    <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 8, lineHeight: 1.6 }}>{s.desc}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </section>

      {/* ══════════ Chapter 3: CONSTELLATION MAP ══════════ */}
      <section data-section="constellation" style={{ padding: '80px 24px', background: '#0A0908', position: 'relative' }}>
        <div style={{ maxWidth: 900, margin: '0 auto' }}>
          <h2 style={{ textAlign: 'center', fontSize: 28, fontFamily: 'var(--font-serif)', color: 'var(--gold)', marginBottom: 8, fontWeight: 300 }}>思想星丛</h2>
          <div style={{ width: 64, height: 1, background: 'linear-gradient(to right, transparent, var(--gold), transparent)', margin: '0 auto 40px' }} />
          <div style={{ position: 'relative', width: '100%', aspectRatio: '4/3', maxHeight: 600, background: 'radial-gradient(circle at 50% 40%, rgba(201,169,110,0.04) 0%, transparent 60%)', borderRadius: 4 }}>
            <svg viewBox="0 0 800 560" style={{ width: '100%', height: '100%' }}>
              <defs>
                <filter id="glow"><feGaussianBlur stdDeviation="2" result="blur" /><feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge></filter>
              </defs>
              {/* Relation lines */}
              {data.relations.map((r, i) => {
                const from = thinkers.find(t => t.name === r.from);
                const to = thinkers.find(t => t.name === r.to);
                if (!from || !to) return null;
                const mx = (from._x + to._x) / 2, my = (from._y + to._y) / 2 - 30;
                const dash = r.type === '对立' ? '2,6' : r.type === '友谊' ? '4,4' : 'none';
                return <path key={i} d={`M${from._x},${from._y} Q${mx},${my} ${to._x},${to._y}`}
                  fill="none" stroke={hovered === `rel-${i}` ? '#C9A96E' : 'rgba(201,169,110,0.15)'} strokeWidth={hovered === `rel-${i}` ? 2 : 1.2}
                  strokeDasharray={dash} style={{ transition: 'all 0.3s' }} onMouseEnter={() => setHovered(`rel-${i}`)} onMouseLeave={() => setHovered(null)} />;
              })}
              {/* Thinker nodes */}
              {thinkers.map((t, i) => {
                const r = 14 + (t.influence || 5) * 2.5;
                const color = SUB_COLORS[t.sub] || '#C9A96E';
                const isHovered = hovered === `t-${i}`;
                return (
                  <g key={i} style={{ cursor: 'pointer' }}
                    onMouseEnter={() => setHovered(`t-${i}`)} onMouseLeave={() => setHovered(null)}
                    onClick={() => navigate('/author/' + encodeURIComponent(t.name))}>
                    <circle cx={t._x} cy={t._y} r={r + 10} fill="none" stroke={color} strokeOpacity="0.15" strokeWidth="1" className="pulse-ring" />
                    <circle cx={t._x} cy={t._y} r={isHovered ? r * 1.3 : r} fill="#1A1816" stroke={color} strokeWidth={isHovered ? 2.5 : 1.5}
                      filter="url(#glow)" style={{ transition: 'all 0.3s' }} />
                    <text x={t._x} y={t._y + 5} textAnchor="middle" fill={color} fontSize={10} fontFamily="var(--font-serif)" fontWeight={600}>{t.name[0]}</text>
                    {isHovered && (
                      <g>
                        <rect x={t._x - 60} y={t._y - r - 48} width={120} height={40} rx={6} fill="rgba(26,24,22,0.9)" stroke={color} strokeOpacity="0.4" />
                        <text x={t._x} y={t._y - r - 30} textAnchor="middle" fill="#E8E3D9" fontSize={12} fontFamily="var(--font-serif)">{t.name}</text>
                        <text x={t._x} y={t._y - r - 16} textAnchor="middle" fill={color} fontSize={10} fontFamily="var(--font-sans)">{t.sub}</text>
                      </g>
                    )}
                  </g>
                );
              })}
            </svg>
          </div>
        </div>
      </section>

      {/* ══════════ Chapter 4: TIMELINE ══════════ */}
      <section data-section="timeline" style={{ padding: '96px 24px', background: 'rgba(26,24,22,0.15)', position: 'relative', maxWidth: 1100, margin: '0 auto' }}>
        <h2 style={{ textAlign: 'center', fontSize: 28, fontFamily: 'var(--font-serif)', color: 'var(--gold)', marginBottom: 8, fontWeight: 300 }}>思想史时间轴</h2>
        <div style={{ width: 64, height: 1, background: 'linear-gradient(to right, transparent, var(--gold), transparent)', margin: '0 auto 56px' }} />
        <div style={{ position: 'relative' }}>
          <div style={{ position: 'absolute', left: '50%', top: 0, bottom: 0, width: 1.5, background: 'linear-gradient(to bottom, transparent, rgba(201,169,110,0.5), transparent)', transform: 'translateX(-50%)' }} />
          {data.timeline.map((ev, i) => {
            const colorMap = { birth: '#C9A96E', death: '#A06050', book: '#6B8E6B', idea: '#7B8EA0', event: '#B8A080' };
            const color = colorMap[ev.type] || '#C9A96E';
            const isLeft = i % 2 === 0;
            return (
              <div key={i} style={{ display: 'flex', alignItems: 'flex-start', marginBottom: 32, flexDirection: isLeft ? 'row' : 'row-reverse' }}>
                <div style={{ flex: '1 1 45%', padding: isLeft ? '0 32px 0 0' : '0 0 0 32px', textAlign: isLeft ? 'right' : 'left' }}>
                  <div style={{ background: 'rgba(26,24,22,0.6)', backdropFilter: 'blur(8px)', padding: 20, borderBottom: '2px solid ' + color,
                    transition: 'all 0.3s', cursor: 'default' }}
                    onMouseEnter={e => e.currentTarget.style.borderBottomColor = '#C9A96E'}
                    onMouseLeave={e => e.currentTarget.style.borderBottomColor = color}>
                    <span style={{ fontSize: '2rem', fontFamily: 'var(--font-serif)', fontWeight: 300, color: 'var(--gold)', lineHeight: 1, display: 'block' }}>{ev.year}</span>
                    <h4 style={{ fontSize: 16, fontFamily: 'var(--font-serif)', color: 'var(--text-primary)', margin: '8px 0 4px' }}>{ev.event}</h4>
                    <p style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.6, margin: 0 }}>{ev.detail}</p>
                  </div>
                </div>
                <div style={{ flexShrink: 0, width: 16, display: 'flex', flexDirection: 'column', alignItems: 'center', paddingTop: 24 }}>
                  <div style={{ width: 12, height: 12, borderRadius: '50%', border: '2px solid ' + color, background: '#0A0908', position: 'relative', zIndex: 1 }} />
                </div>
                <div style={{ flex: '1 1 45%' }} />
              </div>
            );
          })}
        </div>
      </section>

      {/* ══════════ Chapter 5: GLOSSARY ══════════ */}
      <section data-section="glossary" style={{ padding: '96px 24px', maxWidth: 1100, margin: '0 auto' }}>
        <h2 style={{ textAlign: 'center', fontSize: 28, fontFamily: 'var(--font-serif)', color: 'var(--gold)', marginBottom: 8, fontWeight: 300 }}>辞海</h2>
        <div style={{ width: 64, height: 1, background: 'linear-gradient(to right, transparent, var(--gold), transparent)', margin: '0 auto 40px' }} />
        <p style={{ textAlign: 'center', color: 'var(--text-muted)', fontSize: 13, marginBottom: 32 }}>悬停词语查看释义与出处</p>
        <div style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'center', gap: '12px 20px', padding: '0 16px', background: 'radial-gradient(circle at 40% 30%, rgba(201,169,110,0.04) 0%, transparent 60%)' }}>
          {cihai.map((item, i) => {
            const size = 14 + (item.word.length > 4 ? 4 : item.word.length * 2);
            const weight = size > 22 ? 600 : size > 18 ? 500 : 400;
            const color = size > 22 ? 'var(--gold)' : size > 18 ? '#D4C5A0' : 'var(--text-secondary)';
            const isHovered = hovered === `ci-${i}`;
            return (
              <span key={i} style={{ fontSize: size, fontWeight: weight, color: isHovered ? '#C9A96E' : color,
                fontFamily: 'var(--font-serif)', cursor: 'pointer', transition: 'all 0.3s', transform: isHovered ? 'scale(1.2)' : 'scale(1)',
                filter: isHovered ? 'drop-shadow(0 0 10px rgba(201,169,110,0.6))' : 'none', position: 'relative', padding: '4px 8px' }}
                onMouseEnter={() => setHovered(`ci-${i}`)} onMouseLeave={() => setHovered(null)}>
                {item.word}
                {isHovered && (
                  <span style={{ position: 'absolute', bottom: '100%', left: '50%', transform: 'translateX(-50%)', marginBottom: 8,
                    background: 'rgba(26,24,22,0.95)', backdropFilter: 'blur(12px)', border: '1px solid rgba(201,169,110,0.3)',
                    borderRadius: 8, padding: '10px 14px', fontSize: 12, color: 'var(--text-secondary)', whiteSpace: 'nowrap', maxWidth: 280, zIndex: 10 }}>
                    <p style={{ margin: 0, lineHeight: 1.5, whiteSpace: 'normal' }}>{item.def}</p>
                    <p style={{ margin: '4px 0 0', color: 'var(--text-muted)', fontSize: 10 }}>{item.source}</p>
                  </span>
                )}
              </span>
            );
          })}
        </div>
      </section>

      {/* ══════════ Chapter 6: GOLDEN QUOTES ══════════ */}
      <section data-section="quotes" style={{ padding: '96px 24px', maxWidth: 900, margin: '0 auto' }}>
        <h2 style={{ textAlign: 'center', fontSize: 28, fontFamily: 'var(--font-serif)', color: 'var(--gold)', marginBottom: 8, fontWeight: 300 }}>金句荟萃</h2>
        <div style={{ width: 64, height: 1, background: 'linear-gradient(to right, transparent, var(--gold), transparent)', margin: '0 auto 56px' }} />
        <div style={{ columnCount: 2, columnGap: 48 }}>
          {data.quotes.map((q, i) => {
            const isHovered = hovered === `q-${i}`;
            return (
              <div key={i} style={{ breakInside: 'avoid', marginBottom: 32, borderLeft: '3px solid rgba(201,169,110,0.4)', paddingLeft: 20, paddingRight: 8,
                transition: 'all 0.3s', transform: isHovered ? 'translateX(6px)' : 'translateX(0)', cursor: 'default' }}
                onMouseEnter={() => setHovered(`q-${i}`)} onMouseLeave={() => setHovered(null)}>
                <p style={{ fontSize: 'clamp(1rem, 1.4vw, 1.2rem)', fontFamily: 'var(--font-serif)', fontStyle: 'italic', color: 'var(--text-primary)', lineHeight: 1.7, margin: 0 }}>
                  <span style={{ color: 'var(--gold)', fontSize: '1.4em', lineHeight: 0 }}>“</span>{q.text}<span style={{ color: 'var(--gold)', fontSize: '1.4em', lineHeight: 0 }}>”</span>
                </p>
                <p style={{ fontSize: 13, fontFamily: 'var(--font-sans)', color: 'var(--text-muted)', marginTop: 8, textAlign: 'right' }}>—— {q.author}</p>
                {isHovered && <p style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.6, marginTop: 8, opacity: 0.8 }}>{q.exp}</p>}
              </div>
            );
          })}
        </div>
      </section>

      {/* ══════════ Chapter 6.5: KEY WORKS ══════════ */}
      {data.works && data.works.length > 0 && (
        <section data-section="works" style={{ padding: '64px 24px 96px', maxWidth: 900, margin: '0 auto' }}>
          <h2 style={{ textAlign: 'center', fontSize: 28, fontFamily: 'var(--font-serif)', color: 'var(--gold)', marginBottom: 8, fontWeight: 300 }}>重要著作</h2>
          <div style={{ width: 64, height: 1, background: 'linear-gradient(to right, transparent, var(--gold), transparent)', margin: '0 auto 56px' }} />
          <div style={{ display: 'grid', gap: 16 }}>
            {data.works.map((work, i) => {
              const isOpen = hovered === `work-${i}`;
              return (
                <div key={i} style={{ background: 'rgba(26,24,22,0.4)', padding: 20, borderBottom: '1px solid rgba(201,169,110,0.2)', cursor: 'pointer', transition: 'all 0.3s' }}
                  onClick={() => setHovered(isOpen ? null : `work-${i}`)}
                  onMouseEnter={e => { if (!isOpen) e.currentTarget.style.borderBottomColor = 'rgba(201,169,110,0.5)'; }}
                  onMouseLeave={e => { if (!isOpen) e.currentTarget.style.borderBottomColor = 'rgba(201,169,110,0.2)'; }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
                    <h4 style={{ fontFamily: 'var(--font-serif)', fontSize: 18, color: 'var(--text-primary)', margin: 0, fontStyle: 'italic' }}>《{work.title}》</h4>
                    <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>{work.author} · {work.era}</span>
                  </div>
                  {isOpen && <p style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.7, marginTop: 12 }}>{work.desc}</p>}
                </div>
              );
            })}
          </div>
        </section>
      )}

      {/* ══════════ Chapter 7: EPILOGUE ══════════ */}
      <section data-section="epilogue" style={{ padding: '128px 24px', textAlign: 'center', borderTop: '1px solid rgba(201,169,110,0.15)', background: 'linear-gradient(to bottom, transparent, #0A0908)' }}>
        <div style={{ width: 64, height: 1, background: 'var(--gold)', margin: '0 auto 48px', opacity: 0.6 }} />
        <div style={{ maxWidth: 640, margin: '0 auto', fontSize: 'clamp(1rem, 1.3vw, 1.1rem)', fontFamily: 'var(--font-sans)', fontWeight: 300, color: 'var(--text-secondary)', lineHeight: 2, whiteSpace: 'pre-line' }}>
          {data.conclusion}
        </div>
        <div style={{ width: 32, height: 1, background: 'rgba(201,169,110,0.5)', margin: '48px auto' }} />
        {data.closingQuote && (
          <blockquote style={{ maxWidth: 720, margin: '0 auto', fontSize: 'clamp(1.5rem, 3vw, 2.2rem)', fontFamily: 'var(--font-serif)', fontWeight: 300, color: 'var(--text-primary)', lineHeight: 1.4, border: 'none', padding: 0 }}>
            <span style={{ color: 'var(--gold)', fontSize: '3rem', lineHeight: 0, verticalAlign: 'middle' }}>“</span>
            {data.closingQuote}
            <span style={{ color: 'var(--gold)', fontSize: '3rem', lineHeight: 0, verticalAlign: 'middle' }}>”</span>
          </blockquote>
        )}
        <p style={{ marginTop: 40, fontSize: 12, color: 'var(--text-muted)', letterSpacing: '0.2em' }}>—— 思想长河中的一颗星辰 · 完</p>
        <button onClick={() => navigate('/genealogy')} style={{ marginTop: 48, background: 'transparent', border: '1px solid rgba(201,169,110,0.3)', borderRadius: 24,
          padding: '10px 28px', color: 'var(--gold)', fontSize: 14, cursor: 'pointer', fontFamily: 'var(--font-sans)', transition: 'all 0.3s' }}
          onMouseEnter={e => { e.target.style.borderColor = 'var(--gold)'; e.target.style.background = 'rgba(201,169,110,0.1)'; }}
          onMouseLeave={e => { e.target.style.borderColor = 'rgba(201,169,110,0.3)'; e.target.style.background = 'transparent'; }}>
          ← 返回谱系
        </button>
      </section>
    </div>
  );
}

export default SchoolDetailPage;
"""

# Replace
content = content[:return_start] + new_jsx

with open(TARGET, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"Written: {len(content)} bytes")
print("DONE! New 7-chapter layout injected.")
