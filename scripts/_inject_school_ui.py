"""
Replace SchoolDetailPage JSX with academic scholarly design.
Keeps all data/logic intact.
"""
import re

TARGET = r"C:\Users\wqx_0\PyCharmProjects\Q&ASystem\DeepPhilosophy\app\src\pages\SchoolDetailPage.jsx"

with open(TARGET, 'r', encoding='utf-8') as f:
    content = f.read()

# Backup
with open(TARGET + ".acad_bak", 'w', encoding='utf-8') as f:
    f.write(content)

return_start = content.find('\n  return (', content.find('const [hovered, setHovered]'))

new_jsx = r"""
  return (
    <div style={{ background: 'var(--bone)', color: 'var(--ink)', fontFamily: '"Playfair Display","PingFang SC",serif', minHeight: '100vh' }}>

      {/* ══════════ 1. HERO — restrained ══════════ */}
      <section style={{
        padding: '80px 32px 56px', textAlign: 'center', maxWidth: 720, margin: '0 auto',
        position: 'relative'
      }}>
        {/* Subtle background wash */}
        <div style={{
          position: 'absolute', top: 0, left: 0, right: 0, bottom: 0,
          backgroundImage: heroImage, backgroundSize: 'cover', backgroundPosition: 'center',
          opacity: 0.06, zIndex: 0
        }} />
        <div style={{ position: 'relative', zIndex: 1 }}>
          <button onClick={() => navigate('/genealogy')} style={{
            background: 'none', border: 'none', cursor: 'pointer', fontFamily: 'var(--font-sans)', fontSize: 13,
            color: 'var(--text-dim)', letterSpacing: '0.04em', marginBottom: 40, padding: 0
          }}>← 返回谱系</button>
          <h1 style={{
            fontFamily: 'var(--font-serif)', fontSize: 'clamp(2.2rem, 6vw, 3.6rem)', fontWeight: 400,
            color: 'var(--ink)', letterSpacing: '0.05em', lineHeight: 1.2, margin: '0 0 16px'
          }}>{data.name}</h1>
          {data.subtitle && (
            <p style={{ fontFamily: 'var(--font-sans)', fontSize: 15, color: 'var(--text-dim)', fontWeight: 300, maxWidth: 480, margin: '0 auto 28px', lineHeight: 1.6 }}>
              {data.subtitle}
            </p>
          )}
          <div style={{ width: 48, height: 1, background: 'var(--border)', margin: '0 auto 28px' }} />
          <blockquote style={{ maxWidth: 560, margin: '0 auto', border: 'none', padding: 0 }}>
            <p style={{
              fontFamily: 'var(--font-serif)', fontStyle: 'italic', fontSize: 'clamp(1.1rem, 2vw, 1.3rem)',
              color: 'var(--text-dim)', lineHeight: 1.8, fontWeight: 300, margin: 0
            }}>
              &ldquo;{data.quote}&rdquo;
            </p>
            <footer style={{ fontFamily: 'var(--font-sans)', fontSize: 12, color: 'var(--fade)', marginTop: 12, fontStyle: 'normal' }}>
              &mdash; {data.quoteAuthor}
            </footer>
          </blockquote>
        </div>
      </section>

      {/* ══════════ 2. OVERVIEW + SUB-SCHOOLS ══════════ */}
      <section style={{ maxWidth: 680, margin: '0 auto', padding: '64px 32px' }}>
        <h2 style={{
          fontFamily: 'var(--font-serif)', fontSize: 22, fontWeight: 400, color: 'var(--ink)',
          letterSpacing: '0.04em', margin: '0 0 32px'
        }}>
          概述
        </h2>
        <div style={{
          fontFamily: 'var(--font-sans)', fontSize: 15, fontWeight: 300, color: 'var(--text)',
          lineHeight: 1.9, whiteSpace: 'pre-line'
        }}>
          {data.overview}
        </div>

        {subSchools && subSchools.length > 0 && (
          <div style={{ marginTop: 48 }}>
            <h3 style={{
              fontFamily: 'var(--font-serif)', fontSize: 18, fontWeight: 400, color: 'var(--ink)',
              letterSpacing: '0.04em', margin: '0 0 20px'
            }}>
              下属流派
            </h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 16 }}>
              {subSchools.map((s, i) => (
                <div key={i} style={{
                  padding: '18px 20px', border: '1px solid var(--border)', background: 'var(--bone)',
                  transition: 'border-color 0.25s'
                }}
                  onMouseEnter={e => e.currentTarget.style.borderColor = 'var(--accent)'}
                  onMouseLeave={e => e.currentTarget.style.borderColor = 'var(--border)'}
                >
                  <h4 style={{ fontFamily: 'var(--font-serif)', fontSize: 16, fontWeight: 400, color: 'var(--ink)', margin: '0 0 4px' }}>{s.name}</h4>
                  <span style={{ fontSize: 11, color: 'var(--fade)', fontFamily: 'var(--font-sans)' }}>{s.era}</span>
                  <p style={{ fontSize: 13, color: 'var(--text-dim)', fontFamily: 'var(--font-sans)', fontWeight: 300, lineHeight: 1.7, margin: '8px 0 0' }}>{s.desc}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </section>

      {/* ══════════ 3. CONSTELLATION MAP ══════════ */}
      <section style={{ padding: '64px 32px', background: 'var(--card-bg)' }}>
        <div style={{ maxWidth: 850, margin: '0 auto' }}>
          <h2 style={{
            fontFamily: 'var(--font-serif)', fontSize: 22, fontWeight: 400, color: 'var(--ink)',
            letterSpacing: '0.04em', margin: '0 0 32px', textAlign: 'center'
          }}>
            思想星丛
          </h2>
          <div style={{ width: '100%', height: 560, position: 'relative' }}>
            <svg viewBox="0 0 800 560" style={{ width: '100%', height: '100%' }}>
              {/* Relation lines — thin, academic */}
              {data.relations.map((r, i) => {
                const from = thinkers.find(t => t.name === r.from);
                const to = thinkers.find(t => t.name === r.to);
                if (!from || !to) return null;
                const mx = (from._x + to._x) / 2, my = (from._y + to._y) / 2 - 25;
                const dash = r.type === '对立' ? '6,4' : r.type === '友谊' ? '4,4' : '';
                const isHovered = hovered === `rel-${i}`;
                return (
                  <g key={i} onMouseEnter={() => setHovered(`rel-${i}`)} onMouseLeave={() => setHovered(null)}>
                    <path d={`M${from._x},${from._y} Q${mx},${my} ${to._x},${to._y}`}
                      fill="none" stroke={isHovered ? 'var(--accent)' : 'var(--border)'}
                      strokeWidth={isHovered ? 1.5 : 0.8} strokeDasharray={dash}
                      style={{ transition: 'all 0.3s' }} />
                    {isHovered && (
                      <text x={mx} y={my - 6} textAnchor="middle" fontSize={9} fill="var(--text-dim)" fontStyle="italic">{r.type}</text>
                    )}
                  </g>
                );
              })}
              {/* Auto-generate lines for same-sub thinkers without explicit relations */}
              {(() => {
                const existing = new Set(data.relations.map(r => `${r.from}||${r.to}`));
                const lines = [];
                const groups = {};
                thinkers.forEach(t => { const g = t.sub || '__d__'; if (!groups[g]) groups[g] = []; groups[g].push(t); });
                Object.values(groups).forEach(group => {
                  for (let a = 0; a < group.length; a++) {
                    for (let b = a + 1; b < group.length; b++) {
                      if (!existing.has(`${group[a].name}||${group[b].name}`) && !existing.has(`${group[b].name}||${group[a].name}`)) {
                        const mx = (group[a]._x + group[b]._x) / 2;
                        const my = (group[a]._y + group[b]._y) / 2 - 15;
                        lines.push(
                          <path key={`auto-${a}-${b}`}
                            d={`M${group[a]._x},${group[a]._y} Q${mx},${my} ${group[b]._x},${group[b]._y}`}
                            fill="none" stroke="var(--border)" strokeWidth="0.5" strokeDasharray="4,6" />
                        );
                      }
                    }
                  }
                });
                return lines;
              })()}
              {/* Thinker nodes */}
              {thinkers.map((t, i) => {
                const r = 14 + (t.influence || 5) * 2;
                const color = SUB_COLORS[t.sub] || 'var(--accent)';
                const isHovered = hovered === `t-${i}`;
                return (
                  <g key={i} style={{ cursor: 'pointer' }}
                    onMouseEnter={() => setHovered(`t-${i}`)} onMouseLeave={() => setHovered(null)}
                    onClick={() => navigate('/author/' + encodeURIComponent(t.name))}>
                    <circle cx={t._x} cy={t._y} r={isHovered ? r * 1.25 : r}
                      fill="var(--bone)" stroke={color} strokeWidth={isHovered ? 2 : 1.2}
                      style={{ transition: 'all 0.25s' }} />
                    <text x={t._x} y={t._y + 4} textAnchor="middle" fill="var(--ink)" fontSize={9}
                      fontFamily="var(--font-serif)" fontWeight={500}>{t.name[0]}</text>
                    <text x={t._x} y={t._y + r + 12} textAnchor="middle" fill="var(--text-dim)"
                      fontSize={isHovered ? 10 : 8} fontFamily="var(--font-sans)" fontWeight={300}
                      style={{ transition: 'all 0.25s', opacity: isHovered ? 1 : 0.6 }}>{t.name}</text>
                    {isHovered && (
                      <g>
                        <rect x={t._x - 72} y={t._y - r - 52} width={144} height={44} rx={4}
                          fill="var(--bone)" stroke="var(--border)" strokeWidth="0.5" />
                        <text x={t._x} y={t._y - r - 36} textAnchor="middle" fill="var(--ink)" fontSize={11}
                          fontFamily="var(--font-serif)" fontWeight={500}>{t.name}</text>
                        <text x={t._x} y={t._y - r - 22} textAnchor="middle" fill="var(--text-dim)" fontSize={9}
                          fontFamily="var(--font-sans)">{t.sub}{t.era ? ' · ' + t.era : ''}</text>
                      </g>
                    )}
                  </g>
                );
              })}
            </svg>
          </div>
        </div>
      </section>

      {/* ══════════ 4. TIMELINE — vertical, minimal ══════════ */}
      <section style={{ padding: '64px 32px', maxWidth: 680, margin: '0 auto' }}>
        <h2 style={{
          fontFamily: 'var(--font-serif)', fontSize: 22, fontWeight: 400, color: 'var(--ink)',
          letterSpacing: '0.04em', margin: '0 0 40px'
        }}>
          时间轴
        </h2>
        <div style={{ position: 'relative', paddingLeft: 32 }}>
          <div style={{
            position: 'absolute', left: 8, top: 0, bottom: 0, width: 1,
            background: 'var(--border)'
          }} />
          {data.timeline.map((ev, i) => {
            const colorMap = { birth: 'var(--ochre)', death: 'var(--fade)', book: 'var(--prussian)', idea: 'var(--accent)', event: 'var(--text-dim)' };
            const color = colorMap[ev.type] || 'var(--text-dim)';
            return (
              <div key={i} style={{ position: 'relative', marginBottom: 36, paddingLeft: 24 }}>
                <div style={{
                  position: 'absolute', left: -27, top: 4, width: 9, height: 9, borderRadius: '50%',
                  background: 'var(--bone)', border: '2px solid ' + color, zIndex: 2
                }} />
                <span style={{
                  display: 'block', fontFamily: 'var(--font-serif)', fontSize: 15, fontWeight: 400,
                  color: color, letterSpacing: '0.04em', marginBottom: 4
                }}>
                  {ev.year}
                </span>
                <h4 style={{
                  fontFamily: 'var(--font-serif)', fontSize: 16, fontWeight: 400, color: 'var(--ink)',
                  margin: '0 0 4px', letterSpacing: '0.02em'
                }}>
                  {ev.event}
                </h4>
                <p style={{
                  fontFamily: 'var(--font-sans)', fontSize: 13, fontWeight: 300, color: 'var(--text-dim)',
                  lineHeight: 1.7, margin: 0
                }}>
                  {ev.detail}
                </p>
              </div>
            );
          })}
        </div>
      </section>

      {/* ══════════ 5. GLOSSARY ══════════ */}
      <section style={{ padding: '64px 32px', background: 'var(--card-bg)' }}>
        <div style={{ maxWidth: 680, margin: '0 auto' }}>
          <h2 style={{
            fontFamily: 'var(--font-serif)', fontSize: 22, fontWeight: 400, color: 'var(--ink)',
            letterSpacing: '0.04em', margin: '0 0 8px'
          }}>
            辞海
          </h2>
          <p style={{ fontFamily: 'var(--font-sans)', fontSize: 12, color: 'var(--fade)', marginBottom: 32, fontWeight: 300 }}>
            悬停查看释义
          </p>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px 16px' }}>
            {cihai.map((item, i) => {
              let hash = 0; for (let c = 0; c < item.word.length; c++) hash = ((hash << 5) - hash) + item.word.charCodeAt(c); hash = Math.abs(hash);
              const size = 13 + (hash % 18);
              const isHovered = hovered === `ci-${i}`;
              const weight = size > 26 ? 500 : size > 20 ? 400 : 300;
              return (
                <span key={i} style={{
                  fontSize: size, fontWeight: weight, fontFamily: 'var(--font-serif)',
                  color: isHovered ? 'var(--accent)' : 'var(--text)',
                  cursor: 'pointer', transition: 'color 0.25s', position: 'relative', padding: '2px 6px',
                  borderBottom: isHovered ? '1px solid var(--accent)' : '1px solid transparent'
                }}
                  onMouseEnter={() => setHovered(`ci-${i}`)} onMouseLeave={() => setHovered(null)}
                >
                  {item.word}
                  {isHovered && (
                    <span style={{
                      position: 'absolute', bottom: '100%', left: '50%', transform: 'translateX(-50%)', marginBottom: 8,
                      background: 'var(--bone)', border: '1px solid var(--border)', padding: '10px 14px',
                      fontSize: 12, color: 'var(--text-dim)', whiteSpace: 'nowrap', maxWidth: 280, zIndex: 10,
                      fontFamily: 'var(--font-sans)', fontWeight: 300, lineHeight: 1.6, boxShadow: '0 2px 12px rgba(0,0,0,0.06)'
                    }}>
                      {item.def}
                      <br /><span style={{ color: 'var(--fade)', fontSize: 10 }}>{item.source}</span>
                    </span>
                  )}
                </span>
              );
            })}
          </div>
        </div>
      </section>

      {/* ══════════ 6. GOLDEN QUOTES ══════════ */}
      <section style={{ padding: '64px 32px 48px', maxWidth: 680, margin: '0 auto' }}>
        <h2 style={{
          fontFamily: 'var(--font-serif)', fontSize: 22, fontWeight: 400, color: 'var(--ink)',
          letterSpacing: '0.04em', margin: '0 0 40px'
        }}>
          金句
        </h2>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 32 }}>
          {data.quotes.map((q, i) => {
            const isHovered = hovered === `q-${i}`;
            return (
              <div key={i} style={{
                borderLeft: '2px solid', borderColor: isHovered ? 'var(--ochre)' : 'var(--border)',
                paddingLeft: 20, transition: 'all 0.3s', cursor: 'default'
              }}
                onMouseEnter={() => setHovered(`q-${i}`)} onMouseLeave={() => setHovered(null)}
              >
                <p style={{
                  fontFamily: 'var(--font-serif)', fontStyle: 'italic', fontSize: 'clamp(0.95rem, 1.3vw, 1.1rem)',
                  color: isHovered ? 'var(--ink)' : 'var(--text)', lineHeight: 1.8, margin: 0,
                  transition: 'color 0.3s', fontWeight: 300
                }}>
                  &ldquo;{q.text}&rdquo;
                </p>
                <p style={{
                  fontFamily: 'var(--font-sans)', fontSize: 12, color: 'var(--fade)', margin: '6px 0 0',
                  fontWeight: 300
                }}>
                  &mdash; {q.author}
                </p>
                {isHovered && (
                  <p style={{
                    fontFamily: 'var(--font-sans)', fontSize: 12, color: 'var(--text-dim)', margin: '8px 0 0',
                    fontWeight: 300, lineHeight: 1.7
                  }}>
                    {q.exp}
                  </p>
                )}
              </div>
            );
          })}
        </div>
      </section>

      {/* ══════════ 7. KEY WORKS ══════════ */}
      {data.works && data.works.length > 0 && (
        <section style={{ padding: '48px 32px 64px', maxWidth: 680, margin: '0 auto' }}>
          <h2 style={{
            fontFamily: 'var(--font-serif)', fontSize: 22, fontWeight: 400, color: 'var(--ink)',
            letterSpacing: '0.04em', margin: '0 0 36px'
          }}>
            重要著作
          </h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {data.works.map((work, i) => {
              const isOpen = hovered === `work-${i}`;
              const title = typeof work === 'string' ? work : (work.title || '');
              return (
                <div key={i} style={{
                  padding: '14px 0', borderBottom: '1px solid var(--border)', cursor: 'pointer',
                  transition: 'border-color 0.25s'
                }}
                  onClick={() => setHovered(isOpen ? null : `work-${i}`)}
                  onMouseEnter={e => e.currentTarget.style.borderBottomColor = 'var(--accent)'}
                  onMouseLeave={e => e.currentTarget.style.borderBottomColor = 'var(--border)'}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', flexWrap: 'wrap', gap: 8 }}>
                    <h4 style={{
                      fontFamily: 'var(--font-serif)', fontSize: 17, fontWeight: 400, fontStyle: 'italic',
                      color: 'var(--ink)', margin: 0
                    }}>
                      {title.includes('《') ? title : '《' + title + '》'}
                    </h4>
                    {typeof work !== 'string' && (
                      <span style={{ fontSize: 12, color: 'var(--fade)', fontFamily: 'var(--font-sans)' }}>
                        {work.author}{work.era ? ' · ' + work.era : ''}
                      </span>
                    )}
                  </div>
                  {isOpen && typeof work !== 'string' && work.desc && (
                    <p style={{
                      fontFamily: 'var(--font-sans)', fontSize: 13, fontWeight: 300, color: 'var(--text-dim)',
                      lineHeight: 1.8, margin: '10px 0 0'
                    }}>
                      {work.desc}
                    </p>
                  )}
                </div>
              );
            })}
          </div>
        </section>
      )}

      {/* ══════════ 8. EPILOGUE ══════════ */}
      <section style={{ padding: '64px 32px 80px', maxWidth: 680, margin: '0 auto', borderTop: '1px solid var(--border)' }}>
        <h2 style={{
          fontFamily: 'var(--font-serif)', fontSize: 22, fontWeight: 400, color: 'var(--ink)',
          letterSpacing: '0.04em', margin: '0 0 32px'
        }}>
          结语
        </h2>
        <div style={{
          fontFamily: 'var(--font-sans)', fontSize: 15, fontWeight: 300, color: 'var(--text)',
          lineHeight: 1.9, whiteSpace: 'pre-line', marginBottom: 40
        }}>
          {data.conclusion}
        </div>
        {data.closingQuote && (
          <blockquote style={{ border: 'none', padding: 0, margin: '0 0 40px' }}>
            <p style={{
              fontFamily: 'var(--font-serif)', fontStyle: 'italic', fontSize: 'clamp(1.1rem, 2vw, 1.4rem)',
              color: 'var(--text-dim)', lineHeight: 1.7, fontWeight: 300, margin: 0
            }}>
              &ldquo;{data.closingQuote}&rdquo;
            </p>
          </blockquote>
        )}
        <button onClick={() => navigate('/genealogy')} style={{
          background: 'none', border: '1px solid var(--border)', cursor: 'pointer',
          fontFamily: 'var(--font-sans)', fontSize: 13, color: 'var(--text-dim)',
          padding: '8px 20px', letterSpacing: '0.04em', transition: 'all 0.25s'
        }}
          onMouseEnter={e => { e.target.style.borderColor = 'var(--accent)'; e.target.style.color = 'var(--accent)'; }}
          onMouseLeave={e => { e.target.style.borderColor = 'var(--border)'; e.target.style.color = 'var(--text-dim)'; }}
        >
          ← 返回谱系
        </button>
      </section>
    </div>
  );
}

export default SchoolDetailPage;
"""

content = content[:return_start] + new_jsx

with open(TARGET, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"Written: {len(content)} bytes")
print("DONE!")
