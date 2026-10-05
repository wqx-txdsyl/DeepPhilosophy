/**
 * 更多 — 学科索引（一级页）
 * 神话 My · 宗教 Re · 心理 Ps · 社会学 So · 历史学 Hi · 政治学 Po
 * 编辑目录式排布：与首页/世界哲学同一羊皮纸手稿语汇
 */
import { useNavigate } from 'react-router-dom';
import { useSEO } from '../utils/seo';
import { DISCIPLINES } from '../data/moreContent';
import './MorePage.css';

// Hero 六处低语水印：学科代号散落如手稿页边注
const HERO_CODES = [
  { code: 'My', top: '10%', left: '5%', rotate: '-7deg' },
  { code: 'Re', top: '6%', right: '10%', rotate: '5deg' },
  { code: 'Ps', top: '44%', left: '-2%', rotate: '3deg' },
  { code: 'So', top: '58%', right: '4%', rotate: '-4deg' },
  { code: 'Hi', bottom: '4%', left: '16%', rotate: '6deg' },
  { code: 'Po', bottom: '18%', right: '28%', rotate: '-2deg' },
];

const topicCount = DISCIPLINES.reduce((n, d) => n + (d.topics?.length || 0), 0);

export default function MorePage() {
  const navigate = useNavigate();
  useSEO('更多 — 学科探索 | DeepPhilosophy', '神话、宗教、心理、社会学、历史学、政治学——六座学科入口，探索哲学的边界之外。');

  return (
    <div className="page-container" style={{ paddingBottom: 0 }}>

      {/* ══════════ HERO ══════════ */}
      <section className="more-hero">
        <div className="more-hero-codes" aria-hidden="true">
          {HERO_CODES.map(c => (
            <span key={c.code} style={{ top: c.top, left: c.left, right: c.right, bottom: c.bottom, color: DISCIPLINES.find(d => d.code === c.code)?.color, transform: `rotate(${c.rotate})` }}>
              {c.code}
            </span>
          ))}
        </div>
        <div className="more-hero-content">
          <p className="more-hero-eyebrow">Explore · Beyond Philosophy</p>
          <h1 className="more-hero-title">更多</h1>
          <div className="more-hero-divider" />
          <p className="more-hero-subtitle">
            哲学并非孤岛。神话是它的摇篮，宗教是它的对话者，心理学自它分流——<br />
            社会、历史与政治，是它生长的土壤。
          </p>
          <div className="more-hero-stats">
            <span><b>{DISCIPLINES.length}</b>学科</span>
            <i>/</i>
            <span><b>{topicCount}</b>主题</span>
            <i>/</i>
            <span>持续扩展</span>
          </div>
        </div>
      </section>

      {/* ══════════ 学科索引 ══════════ */}
      <section className="more-index">
        <div className="more-index-head">
          <h2>Discipline Index</h2>
          <span>六座学科入口</span>
        </div>

        {DISCIPLINES.map(d => (
          <div
            key={d.id}
            className="more-row"
            style={{ '--disc': d.color }}
            onClick={() => navigate(`/more/${d.id}`)}
            role="link"
            tabIndex={0}
            onKeyDown={e => { if (e.key === 'Enter') navigate(`/more/${d.id}`); }}
            aria-label={`${d.name} ${d.en}，进入学科`}
          >
            <div className="more-row-code">{d.code}</div>

            <div className="more-row-body">
              <div className="more-row-name-line">
                <h3 className="more-row-name">{d.name}</h3>
                <span className="more-row-en">{d.en}</span>
              </div>
              <p className="more-row-desc">{d.desc}</p>
              {d.topics ? (
                <div className="more-row-chips">
                  {d.topics.slice(0, 4).map(t => (
                    <span key={t.id} className="tag">{t.name}</span>
                  ))}
                  {d.topics.length > 4 && <span className="tag tag-ghost">+{d.topics.length - 4}</span>}
                </div>
              ) : (
                <div className="more-row-chips">
                  <span className="more-row-chips-note">主题规划中，拟定方向：</span>
                  {d.seeds.slice(0, 3).map(s => (
                    <span key={s} className="tag tag-ghost">{s}</span>
                  ))}
                </div>
              )}
            </div>

            <div className="more-row-meta">
              {d.topics ? (
                <div className="more-row-count">
                  <b>{d.topics.length}</b>
                  <span>主题</span>
                </div>
              ) : (
                <span className="more-row-badge">规划中</span>
              )}
              <span className="more-row-arrow">&rarr;</span>
            </div>
          </div>
        ))}
      </section>

      <p className="more-footnote">更多学科入口持续扩展中 · My / Re / Ps / So / Hi / Po</p>
    </div>
  );
}
