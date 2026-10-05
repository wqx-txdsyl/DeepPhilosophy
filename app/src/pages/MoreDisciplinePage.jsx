/**
 * 更多 — 学科页（二级）
 * /more/:discipline → 神话 / 宗教 / 心理 / 社会学 / 历史学 / 政治学
 * 主题以编辑画廊网格排布（与世界哲学页同一语汇），规划中学科学科显示拟定方向
 */
import { useNavigate, useParams } from 'react-router-dom';
import { useSEO } from '../utils/seo';
import Icon from '../components/Icon';
import { getDiscipline, DISCIPLINES } from '../data/moreContent';
import './MorePage.css';

export default function MoreDisciplinePage() {
  const navigate = useNavigate();
  const { discipline } = useParams();
  const d = getDiscipline(discipline);
  useSEO(
    d ? `${d.name} ${d.en} — 更多 | DeepPhilosophy` : '更多 | DeepPhilosophy',
    d?.desc || '',
  );

  if (!d) {
    return (
      <div className="page-container">
        <div className="empty-state" style={{ padding: '120px 20px' }}>
          <p>未找到该学科</p>
          <p style={{ marginTop: 12 }}>
            <button className="btn btn-secondary" onClick={() => navigate('/more')}>返回更多</button>
          </p>
        </div>
      </div>
    );
  }

  const siblings = DISCIPLINES.filter(x => x.id !== d.id);

  return (
    <div className="page-container" style={{ paddingBottom: 0 }}>

      {/* ══════════ HERO ══════════ */}
      <section className="more-disc-hero" style={{ '--disc': d.color }}>
        <span className="more-disc-hero-codes" aria-hidden="true" style={{ color: d.color }}>{d.code}</span>
        <button className="more-back" onClick={() => navigate('/more')}>← 返回更多</button>
        <p className="more-hero-eyebrow" style={{ color: d.color }}>{d.en} · {d.code}</p>
        <h1 className="more-hero-title">{d.name}</h1>
        <div className="more-disc-divider" style={{ background: d.color }} />
        <p className="more-disc-subtitle">{d.desc}</p>
      </section>

      {/* ══════════ 主题列表 ══════════ */}
      {d.topics ? (
        <section className="more-topics">
          <div className="more-topics-grid">
            {d.topics.map(t => (
              <div
                key={t.id}
                className="more-topic"
                style={{ '--disc': d.color }}
                onClick={() => navigate(`/more/${d.id}/${t.id}`)}
                role="link"
                tabIndex={0}
                onKeyDown={e => { if (e.key === 'Enter') navigate(`/more/${d.id}/${t.id}`); }}
              >
                <h3 className="more-topic-name">
                  {t.name}
                  {t.philosophyLink && <span className="more-topic-flag">哲学勾连</span>}
                </h3>
                <p className="more-topic-note">{t.note}</p>
                {t.children && (
                  <div className="more-topic-children">
                    {t.children.map(c => <span key={c} className="tag">{c}</span>)}
                  </div>
                )}
              </div>
            ))}
          </div>
        </section>
      ) : (
        <section className="more-planned">
          <div className="more-planned-icon"><Icon name="icon-scroll" size={38} /></div>
          <h3>主题规划中</h3>
          <p>
            {d.name}的入口已在此设立，具体主题正在拟定与撰写。
            以下是初步拟定的方向，欢迎在开发过程中调整。
          </p>
          <div className="more-planned-chips">
            {d.seeds.map(s => <span key={s} className="tag tag-ghost">{s}</span>)}
          </div>
        </section>
      )}

      {/* ══════════ 同区其他学科 ══════════ */}
      <section className="more-index" style={{ paddingTop: 0 }}>
        <div className="more-index-head">
          <h2>Also Explore</h2>
          <span>其他学科</span>
        </div>
        {siblings.map(s => (
          <div
            key={s.id}
            className="more-row"
            style={{ '--disc': s.color }}
            onClick={() => navigate(`/more/${s.id}`)}
            role="link"
            tabIndex={0}
            onKeyDown={e => { if (e.key === 'Enter') navigate(`/more/${s.id}`); }}
          >
            <div className="more-row-code">{s.code}</div>
            <div className="more-row-body">
              <div className="more-row-name-line">
                <h3 className="more-row-name">{s.name}</h3>
                <span className="more-row-en">{s.en}</span>
              </div>
            </div>
            <div className="more-row-meta">
              <span className="more-row-arrow">&rarr;</span>
            </div>
          </div>
        ))}
      </section>

      <p className="more-footnote">{d.en} · 主题持续收录中</p>
    </div>
  );
}
