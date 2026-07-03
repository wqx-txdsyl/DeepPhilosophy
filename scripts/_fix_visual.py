"""
Fix 7 visual issues in SchoolDetailPage new UI.
"""
import re

TARGET = r"C:\Users\wqx_0\PyCharmProjects\Q&ASystem\DeepPhilosophy\app\src\pages\SchoolDetailPage.jsx"

with open(TARGET, 'r', encoding='utf-8') as f:
    content = f.read()

# Backup
with open(TARGET + ".vis_bak", 'w', encoding='utf-8') as f:
    f.write(content)

# Find the return statement
return_start = content.find('\n  return (', content.find('const [hovered, setHovered]'))

new_jsx = r"""
  return (
    <div className="school-detail-dark" style={{ position: 'relative', zIndex: 1, maxWidth: '100vw', overflowX: 'hidden' }}>
      {/* ══════════ Scroll Progress Bar ══════════ */}
      <div style={{ position: 'fixed', top: 0, left: 0, height: 2, zIndex: 9999,
        background: 'var(--gold)', width: 'var(--scroll-pct, 0%)', transition: 'width 0.1s' }} />

      {/* ══════════ Chapter 1: HERO — full bleed ══════════ */}
      <section data-section="hero" style={{ position: 'relative', height: '100vh', width: '100vw', overflow: 'hidden', marginLeft: 'calc(-50vw + 50%)' }}>
        <div style={{ position: 'absolute', inset: 0, backgroundImage: heroImage, backgroundSize: 'cover', backgroundPosition: 'center' }} />
        <div style={{ position: 'absolute', inset: 0, background: 'linear-gradient(to top, #0A0908 0%, rgba(10,9,8,0.5) 35%, rgba(10,9,8,0.15) 100%)' }} />
        <div style={{ position: 'absolute', inset: 0, background: 'radial-gradient(circle at 70% 30%, rgba(201,169,110,0.06) 0%, transparent 60%)' }} />
        <button onClick={() => navigate('/genealogy')} style={{ position: 'absolute', top: 24, left: 24, zIndex: 10,
          background: 'rgba(26,24,22,0.6)', backdropFilter: 'blur(16px)', border: '1px solid rgba(201,169,110,0.2)', borderRadius: 24,
          padding: '10px 22px', color: 'var(--text-secondary)', fontSize: 13, cursor: 'pointer', fontFamily: 'var(--font-sans)', fontWeight: 400,
          letterSpacing: '0.04em' }}>← 返回谱系</button>
        <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', textAlign: 'center', padding: '0 32px' }}>
          <h1 style={{ fontSize: 'clamp(3rem, 9vw, 8rem)', fontFamily: 'var(--font-serif)', fontWeight: 400, letterSpacing: '0.14em', color: 'var(--text-primary)', lineHeight: 1, margin: 0, textShadow: '0 0 80px rgba(201,169,110,0.2)' }}>{data.name}</h1>
          <div style={{ width: 120, height: 1.5, background: 'linear-gradient(to right, transparent, var(--gold), transparent)', margin: '28px 0' }} />
          <blockquote style={{ maxWidth: 780, fontSize: 'clamp(1.2rem, 2.8vw, 1.8rem)', fontFamily: 'var(--font-serif)', fontStyle: 'italic', color: 'var(--text-secondary)', lineHeight: 1.7, border: 'none', padding: 0, margin: 0 }}>
            <span style={{ color: 'var(--gold)', fontSize: '3.5rem', lineHeight: 0, verticalAlign: 'middle', marginRight: 10 }}>&#x201C;</span>
            {data.quote}
            <span style={{ color: 'var(--gold)', fontSize: '3.5rem', lineHeight: 0, verticalAlign: 'middle', marginLeft: 10 }}>&#x201D;</span>
          </blockquote>
          <p style={{ marginTop: 18, color: 'var(--text-muted)', fontSize: 15, fontStyle: 'italic', fontFamily: 'var(--font-sans)', fontWeight: 300 }}>&#x2014;&#x2014; {data.quoteAuthor}</p>
          {data.subtitle && <p style={{ marginTop: 28, color: 'var(--text-secondary)', fontSize: 17, maxWidth: 600, fontFamily: 'var(--font-sans)', fontWeight: 300, opacity: 0.8 }}>{data.subtitle}</p>}
        </div>
        <div style={{ position: 'absolute', bottom: 48, left: '50%', transform: 'translateX(-50%)', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 10, color: 'rgba(201,169,110,0.4)' }}>
          <span style={{ fontSize: 10, letterSpacing: '0.25em', fontFamily: 'var(--font-sans)', fontWeight: 400 }}>SCROLL</span>
          <span style={{ fontSize: 22 }}>⌄</span>
        </div>
      </section>

      {/* ══════════ Chapter 2: OVERVIEW ══════════ */}
      <section data-section="overview" style={{ maxWidth: 1440, margin: '0 auto', padding: '96px 40px' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: 48 }}>
          <div>
            <span style={{ fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.35em', color: 'var(--gold)', fontFamily: 'var(--font-sans)', fontWeight: 500 }}>关于此谱系</span>
            <div style={{ fontSize: 'clamp(1.05rem, 1.7vw, 1.25rem)', fontFamily: 'var(--font-sans)', fontWeight: 300, color: 'var(--text-primary)', lineHeight: 2, whiteSpace: 'pre-line', borderLeft: '2px solid rgba(201,169,110,0.5)', paddingLeft: 28, marginTop: 20 }}>
              {data.overview}
            </div>
          </div>
          {subSchools && subSchools.length > 0 && (
            <div>
              <h3 style={{ fontSize: 24, fontFamily: 'var(--font-serif)', color: 'var(--gold)', marginBottom: 24, fontWeight: 400 }}>下属流派</h3>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 16 }}>
                {subSchools.map((s, i) => (
                  <div key={i} style={{ background: 'rgba(26,24,22,0.35)', backdropFilter: 'blur(10px)', padding: 24, borderBottom: '1px solid rgba(201,169,110,0.15)', transition: 'all 0.35s', cursor: 'default' }}
                    onMouseEnter={e => { e.currentTarget.style.borderBottomColor = 'rgba(201,169,110,0.7)'; e.currentTarget.style.background = 'rgba(26,24,22,0.55)'; }}
                    onMouseLeave={e => { e.currentTarget.style.borderBottomColor = 'rgba(201,169,110,0.15)'; e.currentTarget.style.background = 'rgba(26,24,22,0.35)'; }}>
                    <h4 style={{ fontFamily: 'var(--font-serif)', fontSize: 20, color: 'var(--gold)', margin: '0 0 6px', fontWeight: 500 }}>{s.name}</h4>
                    <span style={{ fontSize: 11, color: 'var(--text-muted)', fontFamily: 'var(--font-sans)', fontWeight: 400 }}>{s.era}</span>
                    <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 10, lineHeight: 1.7, fontFamily: 'var(--font-sans)', fontWeight: 300 }}>{s.desc}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </section>

      {/* ══════════ Chapter 3: CONSTELLATION — names always visible, rich hover ══════════ */}
      <section data-section="constellation" style={{ padding: '80px 24px', background: '#0A0908', position: 'relative' }}>
        <div style={{ maxWidth: 1440, margin: '0 auto' }}>
          <h2 style={{ textAlign: 'center', fontSize: 30, fontFamily: 'var(--font-serif)', color: 'var(--gold)', marginBottom: 8, fontWeight: 400 }}>思想星丛</h2>
          <div style={{ width: 80, height: 1, background: `linear-gradient(to right, transparent, var(--gold), transparent)`, margin: '0 auto 48px' }} />
          <div style={{ position: 'relative', width: '100%', aspectRatio: '4/3', minHeight: 500, maxHeight: 700, background: 'radial-gradient(circle at 50% 35%, rgba(201,169,110,0.05) 0%, transparent 65%)', borderRadius: 4 }}>
            <svg viewBox="0 0 800 560" style={{ width: '100%', height: '100%' }}>
              <defs>
                <filter id="glow2"><feGaussianBlur stdDeviation="3" result="blur" /><feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge></filter>
                <filter id="glowStrong"><feGaussianBlur stdDeviation="5" result="blur" /><feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge></filter>
              </defs>
              {/* Relation lines — thicker, more visible */}
              {data.relations.map((r, i) => {
                const from = thinkers.find(t => t.name === r.from);
                const to = thinkers.find(t => t.name === r.to);
                if (!from || !to) return null;
                const mx = (from._x + to._x) / 2, my = (from._y + to._y) / 2 - 35;
                const dash = r.type === '对立' ? '3,8' : r.type === '友谊' ? '5,5' : r.type === '批判/超越' ? '2,4' : 'none';
                const isRelHovered = hovered === `rel-${i}`;
                return <path key={i} d={`M${from._x},${from._y} Q${mx},${my} ${to._x},${to._y}`}
                  fill="none" stroke={isRelHovered ? '#C9A96E' : 'rgba(201,169,110,0.3)'} strokeWidth={isRelHovered ? 2.5 : 1.5}
                  strokeDasharray={dash} style={{ transition: 'all 0.3s' }}
                  onMouseEnter={() => setHovered(`rel-${i}`)} onMouseLeave={() => setHovered(null)} />;
              })}
              {/* Auto-generate sub-school lines if relations is sparse */}
              {(() => {
                const existingPairs = new Set(data.relations.map(r => `${r.from}||${r.to}`));
                const extraLines = [];
                const groups = {};
                thinkers.forEach(t => { const g = t.sub || 'default'; if (!groups[g]) groups[g] = []; groups[g].push(t); });
                Object.values(groups).forEach(group => {
                  for (let a = 0; a < group.length; a++) {
                    for (let b = a + 1; b < group.length; b++) {
                      const key1 = `${group[a].name}||${group[b].name}`;
                      const key2 = `${group[b].name}||${group[a].name}`;
                      if (!existingPairs.has(key1) && !existingPairs.has(key2)) {
                        const mx2 = (group[a]._x + group[b]._x) / 2, my2 = (group[a]._y + group[b]._y) / 2 - 20;
                        extraLines.push(<path key={`auto-${a}-${b}`} d={`M${group[a]._x},${group[a]._y} Q${mx2},${my2} ${group[b]._x},${group[b]._y}`}
                          fill="none" stroke="rgba(201,169,110,0.08)" strokeWidth="0.8" strokeDasharray="6,8" />);
                      }
                    }
                  }
                });
                return extraLines;
              })()}
              {/* Thinker nodes — full name always visible */}
              {thinkers.map((t, i) => {
                const r = 16 + (t.influence || 5) * 2.2;
                const color = SUB_COLORS[t.sub] || '#C9A96E';
                const isHovered = hovered === `t-${i}`;
                return (
                  <g key={i} style={{ cursor: 'pointer' }}
                    onMouseEnter={() => setHovered(`t-${i}`)} onMouseLeave={() => setHovered(null)}
                    onClick={() => navigate('/author/' + encodeURIComponent(t.name))}>
                    {/* Pulsing ring */}
                    <circle cx={t._x} cy={t._y} r={r + 12} fill="none" stroke={color} strokeOpacity="0.1" strokeWidth="1.5" style={{ animation: 'pulse-ring 3s ease-out infinite' }} />
                    {/* Main node */}
                    <circle cx={t._x} cy={t._y} r={isHovered ? r * 1.35 : r} fill="#1A1816" stroke={color} strokeWidth={isHovered ? 3 : 1.8}
                      filter={isHovered ? 'url(#glowStrong)' : 'url(#glow2)'} style={{ transition: 'all 0.35s' }} />
                    {/* Initial letter */}
                    <text x={t._x} y={t._y + 5} textAnchor="middle" fill={isHovered ? '#FFF' : color} fontSize={12} fontFamily="var(--font-serif)" fontWeight={700}>{t.name[0]}</text>
                    {/* Full name — ALWAYS visible below node */}
                    <text x={t._x} y={t._y + r + 14} textAnchor="middle" fill={isHovered ? '#E8E3D9' : 'var(--text-secondary)'}
                      fontSize={isHovered ? 12 : 9} fontFamily="var(--font-serif)" fontWeight={isHovered ? 600 : 400}
                      style={{ transition: 'all 0.3s', opacity: isHovered ? 1 : 0.7 }}>{t.name}</text>
                    {/* Hover tooltip — rich detail */}
                    {isHovered && (
                      <g>
                        <rect x={t._x - 80} y={t._y - r - 72} width={160} height={56} rx={8} fill="rgba(20,18,16,0.95)" stroke={color} strokeOpacity="0.5" strokeWidth="1" />
                        <text x={t._x} y={t._y - r - 54} textAnchor="middle" fill="#E8E3D9" fontSize={13} fontFamily="var(--font-serif)" fontWeight={600}>{t.name}</text>
                        <text x={t._x} y={t._y - r - 38} textAnchor="middle" fill={color} fontSize={10} fontFamily="var(--font-sans)" fontWeight={500}>{t.sub}</text>
                        <text x={t._x} y={t._y - r - 24} textAnchor="middle" fill="var(--text-muted)" fontSize={9} fontFamily="var(--font-sans)">{t.era} · {t.key}</text>
                      </g>
                    )}
                  </g>
                );
              })}
            </svg>
          </div>
        </div>
      </section>

      {/* ══════════ Chapter 4: TIMELINE — diamond nodes, double glow line ══════════ */}
      <section data-section="timeline" style={{ padding: '96px 40px', background: 'rgba(26,24,22,0.1)', position: 'relative', maxWidth: 1440, margin: '0 auto' }}>
        {/* Subtle scroll texture overlay */}
        <div style={{ position: 'absolute', inset: 0, opacity: 0.03, pointerEvents: 'none',
          backgroundImage: 'repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(201,169,110,0.3) 2px, rgba(201,169,110,0.3) 3px)' }} />
        <h2 style={{ textAlign: 'center', fontSize: 30, fontFamily: 'var(--font-serif)', color: 'var(--gold)', marginBottom: 8, fontWeight: 400, position: 'relative', zIndex: 1 }}>思想史时间轴</h2>
        <div style={{ width: 80, height: 1, background: `linear-gradient(to right, transparent, var(--gold), transparent)`, margin: '0 auto 64px', position: 'relative', zIndex: 1 }} />
        <div style={{ position: 'relative' }}>
          {/* Double-layer center line */}
          <div style={{ position: 'absolute', left: '50%', top: 0, bottom: 0, width: 1, background: 'rgba(201,169,110,0.2)', transform: 'translateX(-50%)' }} />
          <div style={{ position: 'absolute', left: '50%', top: 0, bottom: 0, width: 2, transform: 'translateX(-50%)',
            background: 'repeating-linear-gradient(to bottom, rgba(201,169,110,0.5) 0px, rgba(201,169,110,0.5) 6px, transparent 6px, transparent 12px)',
            filter: 'drop-shadow(0 0 6px rgba(201,169,110,0.3))' }} />
          {data.timeline.map((ev, i) => {
            const colorMap = { birth: '#C9A96E', death: '#C07060', book: '#7BA87B', idea: '#8B9EB8', event: '#C0A880' };
            const color = colorMap[ev.type] || '#C9A96E';
            const isLeft = i % 2 === 0;
            return (
              <div key={i} style={{ display: 'flex', alignItems: 'flex-start', marginBottom: 40, flexDirection: isLeft ? 'row' : 'row-reverse', position: 'relative' }}>
                <div style={{ flex: '1 1 46%', padding: isLeft ? '0 40px 0 0' : '0 0 0 40px', textAlign: isLeft ? 'right' : 'left' }}>
                  <div style={{ background: 'rgba(26,24,22,0.5)', backdropFilter: 'blur(10px)', padding: 24, borderBottom: '2px solid ' + color,
                    transition: 'all 0.35s', cursor: 'default', position: 'relative' }}
                    onMouseEnter={e => { e.currentTarget.style.borderBottomColor = '#C9A96E'; e.currentTarget.style.background = 'rgba(26,24,22,0.7)'; }}
                    onMouseLeave={e => { e.currentTarget.style.borderBottomColor = color; e.currentTarget.style.background = 'rgba(26,24,22,0.5)'; }}>
                    {/* Diamond marker */}
                    <span style={{ position: 'absolute', top: 12, [isLeft ? 'right' : 'left']: -6, fontSize: 8, color }}>&#x25C6;</span>
                    <span style={{ fontSize: '2.2rem', fontFamily: 'var(--font-serif)', fontWeight: 600, color: 'var(--gold)', lineHeight: 1, display: 'block' }}>{ev.year}</span>
                    <h4 style={{ fontSize: 17, fontFamily: 'var(--font-serif)', color: 'var(--text-primary)', margin: '10px 0 6px', fontWeight: 500 }}>{ev.event}</h4>
                    <p style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.7, margin: 0, fontFamily: 'var(--font-sans)', fontWeight: 300 }}>{ev.detail}</p>
                  </div>
                  {/* Connector line to center */}
                  <div style={{ position: 'absolute', top: 36, [isLeft ? 'right' : 'left']: 0, width: 40, height: 1,
                    borderTop: '1px dashed rgba(201,169,110,0.2)', [isLeft ? 'right' : 'left']: 0 }} />
                </div>
                {/* Diamond node on center line */}
                <div style={{ flexShrink: 0, width: 20, display: 'flex', justifyContent: 'center', paddingTop: 28, position: 'relative', zIndex: 2 }}>
                  <svg width="14" height="14" viewBox="0 0 14 14">
                    <polygon points="7,0 11,7 7,14 3,7" fill="#0A0908" stroke={color} strokeWidth="1.5"
                      style={{ filter: 'drop-shadow(0 0 4px ' + color + ')' }} />
                  </svg>
                </div>
                <div style={{ flex: '1 1 46%' }} />
              </div>
            );
          })}
        </div>
      </section>

      {/* ══════════ Chapter 5: GLOSSARY — chaotic word cloud ══════════ */}
      <section data-section="glossary" style={{ padding: '96px 40px', maxWidth: 1440, margin: '0 auto' }}>
        <h2 style={{ textAlign: 'center', fontSize: 30, fontFamily: 'var(--font-serif)', color: 'var(--gold)', marginBottom: 8, fontWeight: 400 }}>辞海</h2>
        <div style={{ width: 80, height: 1, background: 'linear-gradient(to right, transparent, 'var(--gold)', transparent)', margin: '0 auto 48px' }} />
        <p style={{ textAlign: 'center', color: 'var(--text-muted)', fontSize: 12, marginBottom: 40, fontFamily: 'var(--font-sans)', fontWeight: 300 }}>悬停词语查看释义与出处</p>
        <div style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'center', alignItems: 'center', gap: '10px 22px', padding: '0 10px', minHeight: 300,
          background: 'radial-gradient(circle at 35% 40%, rgba(201,169,110,0.05) 0%, transparent 65%)', borderRadius: 12 }}>
          {cihai.map((item, i) => {{
            // Deterministic pseudo-random from word hash
            let hash = 0; for (let c = 0; c < item.word.length; c++) hash = ((hash << 5) - hash) + item.word.charCodeAt(c); hash = Math.abs(hash);
            const size = 12 + (hash % 40);
            const weight = (hash % 4) * 100 + 300;
            const rot = (hash % 10) - 5;
            const color = size > 36 ? 'var(--gold)' : size > 28 ? '#D4C5A0' : size > 20 ? '#B8B0A0' : 'var(--text-muted)';
            const isHovered = hovered === `ci-${i}`;
            return (
              <span key={i} style={{{ fontSize: size, fontWeight: weight, color: isHovered ? '#C9A96E' : color,
                fontFamily: 'var(--font-serif)', cursor: 'pointer', transition: 'all 0.35s', transform: (isHovered ? 'scale(1.35)' : 'scale(1)') + ' rotate(' + rot + 'deg)',
                filter: isHovered ? 'drop-shadow(0 0 14px rgba(201,169,110,0.7))' : 'none', position: 'relative', padding: '4px 10px', lineHeight: 1.2 }}
                onMouseEnter={() => setHovered(`ci-${i}`)} onMouseLeave={() => setHovered(null)}>
                {item.word}
                {isHovered && (
                  <span style={{{ position: 'absolute', bottom: '100%', left: '50%', transform: 'translateX(-50%) rotate(0deg)', marginBottom: 10,
                    background: 'rgba(20,18,16,0.97)', backdropFilter: 'blur(16px)', border: '1px solid rgba(201,169,110,0.4)',
                    borderRadius: 10, padding: '12px 16px', fontSize: 12, color: 'var(--text-secondary)', whiteSpace: 'nowrap', maxWidth: 300, zIndex: 20, fontWeight: 300, fontFamily: 'var(--font-sans)' }}}>
                    <p style={{{ margin: 0, lineHeight: 1.6, whiteSpace: 'normal' }}}>{item.def}</p>
                    <p style={{{ margin: '6px 0 0', color: 'var(--text-muted)', fontSize: 10 }}}>{item.source}</p>
                  </span>
                )}
              </span>
            );
          }})}
        </div>
      </section>

      {/* ══════════ Chapter 6: GOLDEN QUOTES — floating word cloud ══════════ */}
      <section data-section="quotes" style={{ padding: '96px 40px', maxWidth: 1440, margin: '0 auto' }}>
        <h2 style={{ textAlign: 'center', fontSize: 30, fontFamily: 'var(--font-serif)', color: 'var(--gold)', marginBottom: 8, fontWeight: 400 }}>金句回响</h2>
        <div style={{ width: 80, height: 1, background: 'linear-gradient(to right, transparent, 'var(--gold)', transparent)', margin: '0 auto 48px' }} />
        <div style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'center', alignItems: 'center', gap: '14px 28px', padding: '0 10px', minHeight: 350,
          background: 'radial-gradient(circle at 55% 45%, rgba(201,169,110,0.04) 0%, transparent 60%)', borderRadius: 12 }}>
          {data.quotes.map((q, i) => {{
            let hash = 0; const txt = q.text.substring(0, 12); for (let c = 0; c < txt.length; c++) hash = ((hash << 5) - hash) + txt.charCodeAt(c); hash = Math.abs(hash);
            const size = 11 + (hash % 36);
            const weight = 300 + (hash % 4) * 100;
            const rot = (hash % 14) - 7;
            const color = size > 34 ? 'var(--gold)' : size > 26 ? '#D4C5A0' : size > 19 ? '#C0B090' : 'var(--text-muted)';
            const isHovered = hovered === `q-${i}`;
            return (
              <span key={i} style={{{ fontSize: size, fontWeight: weight, color: isHovered ? '#C9A96E' : color,
                fontFamily: 'var(--font-serif)', fontStyle: 'italic', cursor: 'pointer', transition: 'all 0.35s',
                transform: (isHovered ? 'scale(1.35)' : 'scale(1)') + ' rotate(' + rot + 'deg)',
                filter: isHovered ? 'drop-shadow(0 0 14px rgba(201,169,110,0.6))' : 'none',
                position: 'relative', padding: '6px 12px', lineHeight: 1.3, whiteSpace: 'nowrap',
                borderBottom: isHovered ? '1px solid rgba(201,169,110,0.4)' : '1px solid transparent' }}
                onMouseEnter={() => setHovered(`q-${i}`)} onMouseLeave={() => setHovered(null)}>
                &#x201C;{q.text.length > 18 ? q.text.substring(0, 16) + '...' : q.text}&#x201D;
                {isHovered && (
                  <span style={{{ position: 'absolute', bottom: '100%', left: '50%', transform: 'translateX(-50%) rotate(0deg)', marginBottom: 10,
                    background: 'rgba(20,18,16,0.97)', backdropFilter: 'blur(16px)', border: '1px solid rgba(201,169,110,0.4)',
                    borderRadius: 10, padding: '14px 18px', fontSize: 13, color: 'var(--text-primary)', whiteSpace: 'normal', maxWidth: 360, zIndex: 20, fontWeight: 300,
                    fontFamily: 'var(--font-serif)', fontStyle: 'italic', lineHeight: 1.7, textAlign: 'center' }}}>
                    <p style={{{ margin: 0, lineHeight: 1.7, whiteSpace: 'normal', fontFamily: 'var(--font-serif)', fontStyle: 'italic', fontSize: 15 }}}>&#x201C;{q.text}&#x201D;</p>
                    <p style={{{ margin: '10px 0 6px', color: 'var(--text-muted)', fontSize: 11, fontFamily: 'var(--font-sans)', fontStyle: 'normal' }}}>&#x2014;&#x2014; {q.author}</p>
                    <p style={{{ margin: 0, color: 'var(--text-secondary)', fontSize: 11, fontFamily: 'var(--font-sans)', fontStyle: 'normal', lineHeight: 1.5, whiteSpace: 'normal' }}}>{q.exp}</p>
                  </span>
                )}
              </span>
            );
          }})}
        </div>
      </section>

      {/* ══════════ Chapter 6.5: KEY WORKS ══════════ */}
      {data.works && data.works.length > 0 && (
        <section data-section="works" style={{ padding: '64px 40px 96px', maxWidth: 1440, margin: '0 auto' }}>
          <h2 style={{ textAlign: 'center', fontSize: 30, fontFamily: 'var(--font-serif)', color: 'var(--gold)', marginBottom: 8, fontWeight: 400 }}>重要著作</h2>
          <div style={{ width: 80, height: 1, background: 'linear-gradient(to right, transparent, 'var(--gold)', transparent)', margin: '0 auto 64px' }} />
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(360px, 1fr))', gap: 20 }}>
            {data.works.map((work, i) => {
              const isOpen = hovered === `work-${i}`;
              return (
                <div key={i} style={{ background: 'rgba(26,24,22,0.35)', backdropFilter: 'blur(10px)', padding: 24, borderBottom: '1px solid rgba(201,169,110,0.2)', cursor: 'pointer', transition: 'all 0.35s' }}
                  onClick={() => setHovered(isOpen ? null : `work-${i}`)}
                  onMouseEnter={e => { if (!isOpen) { e.currentTarget.style.borderBottomColor = 'rgba(201,169,110,0.6)'; e.currentTarget.style.background = 'rgba(26,24,22,0.55)'; } }}
                  onMouseLeave={e => { if (!isOpen) { e.currentTarget.style.borderBottomColor = 'rgba(201,169,110,0.2)'; e.currentTarget.style.background = 'rgba(26,24,22,0.35)'; } }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', flexWrap: 'wrap', gap: 8 }}>
                    <h4 style={{ fontFamily: 'var(--font-serif)', fontSize: 19, color: 'var(--text-primary)', margin: 0, fontStyle: 'italic', fontWeight: 500 }}>&#x300A;{work.title}&#x300B;</h4>
                    <span style={{ fontSize: 11, color: 'var(--text-muted)', fontFamily: 'var(--font-sans)', fontWeight: 400 }}>{work.author} &#xB7; {work.era}</span>
                  </div>
                  {isOpen && <p style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.8, marginTop: 14, fontFamily: 'var(--font-sans)', fontWeight: 300 }}>{work.desc}</p>}
                </div>
              );
            })}
          </div>
        </section>
      )}

      {/* ══════════ Chapter 7: EPILOGUE ══════════ */}
      <section data-section="epilogue" style={{ padding: '128px 40px', textAlign: 'center', borderTop: '1px solid rgba(201,169,110,0.12)', background: 'linear-gradient(to bottom, transparent, #0A0908)' }}>
        <div style={{ width: 80, height: 1, background: 'var(--gold)', margin: '0 auto 56px', opacity: 0.5 }} />
        <div style={{ maxWidth: 720, margin: '0 auto', fontSize: 'clamp(1rem, 1.4vw, 1.15rem)', fontFamily: 'var(--font-sans)', fontWeight: 300, color: 'var(--text-secondary)', lineHeight: 2.1, whiteSpace: 'pre-line' }}>
          {data.conclusion}
        </div>
        <div style={{ width: 40, height: 1, background: 'rgba(201,169,110,0.4)', margin: '56px auto' }} />
        {data.closingQuote && (
          <blockquote style={{ maxWidth: 800, margin: '0 auto', fontSize: 'clamp(1.5rem, 3.5vw, 2.5rem)', fontFamily: 'var(--font-serif)', fontWeight: 300, color: 'var(--text-primary)', lineHeight: 1.4, border: 'none', padding: 0 }}>
            <span style={{ color: 'var(--gold)', fontSize: '4rem', lineHeight: 0, verticalAlign: 'middle', marginRight: 6 }}>&#x201C;</span>
            {data.closingQuote}
            <span style={{ color: 'var(--gold)', fontSize: '4rem', lineHeight: 0, verticalAlign: 'middle', marginLeft: 6 }}>&#x201D;</span>
          </blockquote>
        )}
        <p style={{ marginTop: 48, fontSize: 11, color: 'var(--text-muted)', letterSpacing: '0.25em', fontFamily: 'var(--font-sans)', fontWeight: 400 }}>&#x2014;&#x2014; 思想长河中的一颗星辰 &#xB7; 完</p>
        <button onClick={() => navigate('/genealogy')} style={{ marginTop: 56, background: 'transparent', border: '1px solid rgba(201,169,110,0.25)', borderRadius: 24,
          padding: '12px 32px', color: 'var(--gold)', fontSize: 14, cursor: 'pointer', fontFamily: 'var(--font-sans)', fontWeight: 400, transition: 'all 0.35s', letterSpacing: '0.04em' }}
          onMouseEnter={e => { e.target.style.borderColor = 'var(--gold)'; e.target.style.background = 'rgba(201,169,110,0.08)'; }}
          onMouseLeave={e => { e.target.style.borderColor = 'rgba(201,169,110,0.25)'; e.target.style.background = 'transparent'; }}>
          &#x2190; 返回谱系
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
print("DONE! All 6 visual fixes applied.")
