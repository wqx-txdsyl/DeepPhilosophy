/**
 * 思想史时间轴 — Cinematic river-of-time timeline
 * 博物馆级事件卡片 · 年代色系 · 因果连线
 */
import { FONT, SPACE, WIDTH } from './tokens';

const ERA_COLORS = {
  ancient:     { bg: '#F5EDE0', line: '#C4956A', dot: '#C4956A', label: '远古' },
  classical:   { bg: '#FAF3E8', line: '#D4A84B', dot: '#D4A84B', label: '古典' },
  medieval:    { bg: '#EFF3F7', line: '#5A7A9A', dot: '#5A7A9A', label: '中世纪' },
  renaissance: { bg: '#F8EDF0', line: '#A56A7A', dot: '#A56A7A', label: '近代' },
  modern:      { bg: '#EEF5EE', line: '#5A8A6A', dot: '#5A8A6A', label: '现代' },
  contemporary:{ bg: '#F3EEF7', line: '#7A5A9A', dot: '#7A5A9A', label: '当代' },
};
const DEFAULT_ERA = ERA_COLORS.classical;

const TYPE_ICONS = {
  birth:  '✦',
  death:  '✧',
  book:   '◆',
  idea:   '◇',
  event:  '●',
};

function getEra(yearStr) {
  if (!yearStr) return DEFAULT_ERA;
  if (yearStr.includes('公元前') || parseInt(yearStr) < 0) return ERA_COLORS.ancient;
  const y = parseInt(yearStr);
  if (isNaN(y)) return DEFAULT_ERA;
  if (y < 500) return ERA_COLORS.classical;
  if (y < 1500) return ERA_COLORS.medieval;
  if (y < 1800) return ERA_COLORS.renaissance;
  if (y < 1950) return ERA_COLORS.modern;
  return ERA_COLORS.contemporary;
}

export default function TimelineSection({ timeline = [] }) {
  return (
    <section style={{ padding: `${SPACE.hero}px 20px 60px`, background: 'var(--bg)', position: 'relative', overflow: 'hidden' }}>
      {/* Section header */}
      <div style={{ textAlign: 'center', marginBottom: 48 }}>
        <span style={{ fontSize: 10, fontWeight: 500, letterSpacing: '0.24em', textTransform: 'uppercase', color: 'var(--ochre)', fontFamily: FONT.sans }}>Historical Timeline</span>
        <h2 style={{ fontSize: 28, fontWeight: 400, color: 'var(--ink)', margin: '6px 0 0', fontFamily: FONT.serif, letterSpacing: '0.04em' }}>思想史时间轴</h2>
        <div style={{ width: 28, height: 1, background: 'var(--ochre)', margin: '14px auto 0', opacity: 0.4 }} />
      </div>

      <div style={{ maxWidth: WIDTH.wide, margin: '0 auto', position: 'relative' }}>
        {/* River of time — central spine with gradient */}
        <div style={{ position: 'absolute', left: '50%', top: 20, bottom: 20, width: 2, transform: 'translateX(-50%)',
          background: 'linear-gradient(to bottom, var(--ochre) 0%, var(--prussian) 50%, var(--ochre) 100%)', opacity: 0.2, borderRadius: 1 }} />

        <div style={{ display: 'flex', flexDirection: 'column', gap: 32 }}>
          {(timeline || []).filter(Boolean).map((ev, i) => {
            const isLeft = i % 2 === 0;
            const era = getEra(ev.year);
            const icon = TYPE_ICONS[ev.type] || '●';

            return (
              <div key={i} className="school-timeline-row" style={{ display: 'flex', alignItems: 'flex-start', position: 'relative' }}>
                {/* Left column */}
                <div style={{ flex: 1, display: 'flex', justifyContent: 'flex-end', paddingRight: 36 }}>
                  {isLeft && <TimelineCard ev={ev} era={era} icon={icon} />}
                </div>

                {/* Center node — era dot on the river */}
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: 80, flexShrink: 0, paddingTop: 10 }}>
                  <div style={{
                    width: 12, height: 12, borderRadius: '50%',
                    background: era.dot, border: '2px solid var(--bg)',
                    zIndex: 1, boxShadow: `0 0 8px ${era.dot}40`,
                    position: 'relative',
                  }}>
                    <div style={{ position: 'absolute', inset: -4, borderRadius: '50%', border: `1px solid ${era.dot}`, opacity: 0.2 }} />
                  </div>
                </div>

                {/* Right column */}
                <div style={{ flex: 1, paddingLeft: 36 }}>
                  {!isLeft && <TimelineCard ev={ev} era={era} icon={icon} />}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}

function TimelineCard({ ev, era, icon }) {
  return (
    <div style={{
      maxWidth: 380, padding: '18px 22px',
      borderLeft: `3px solid ${era.line}`,
      background: 'var(--card-bg)',
      borderRadius: '0 6px 6px 0',
      transition: 'all 0.35s cubic-bezier(0.22,1,0.36,1)',
      cursor: 'default',
      boxShadow: '0 1px 3px rgba(0,0,0,0.03)',
    }}
      onMouseEnter={e => {
        e.currentTarget.style.transform = 'translateX(4px)';
        e.currentTarget.style.boxShadow = '0 2px 12px rgba(0,0,0,0.06)';
      }}
      onMouseLeave={e => {
        e.currentTarget.style.transform = 'translateX(0)';
        e.currentTarget.style.boxShadow = '0 1px 3px rgba(0,0,0,0.03)';
      }}>
      {/* Year + era badge */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
        <span style={{ fontSize: 11, fontWeight: 600, color: era.dot, fontFamily: FONT.sans, letterSpacing: '0.06em' }}>
          {ev.year}
        </span>
        <span style={{ fontSize: 8, fontWeight: 500, color: '#fff', background: era.line, padding: '1px 7px', borderRadius: 10, letterSpacing: '0.06em', textTransform: 'uppercase', fontFamily: FONT.sans }}>
          {era.label}
        </span>
        <span style={{ fontSize: 10, color: 'var(--fade)', fontFamily: FONT.sans, marginLeft: 'auto' }}>{icon}</span>
      </div>

      {/* Event title */}
      <div style={{ fontSize: 15, fontWeight: 500, color: 'var(--ink)', fontFamily: FONT.serif, lineHeight: 1.4 }}>
        {ev.event}
      </div>

      {/* Detail */}
      {ev.detail && (
        <div style={{ fontSize: 12, color: 'var(--text-dim)', lineHeight: 1.7, fontFamily: FONT.sans, fontWeight: 300, marginTop: 5 }}>
          {ev.detail}
        </div>
      )}
    </div>
  );
}
