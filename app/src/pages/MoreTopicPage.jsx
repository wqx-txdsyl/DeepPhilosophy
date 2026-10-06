/**
 * 更多 — 主题详情页（三级）
 * /more/:discipline/:topic
 * 有专用详情布局的题材走 DETAIL_REGISTRY（如神话体系），
 * 其余题材回退到"规划中"占位页——新详情完成后在此登记即可。
 */
import { Link, useNavigate, useParams } from 'react-router-dom';
import { useSEO } from '../utils/seo';
import { getTopic } from '../data/moreContent';
import { ossImg, ossFallback } from '../data/ossUrls';
import { ALL_DETAILS } from '../data/moreTopics';
import ReligionDetail from '../components/more/ReligionDetail';
import MythologyDetail from '../components/more/MythologyDetail';
import './MorePage.css';
import '../components/more/more-detail.css';

/* 神话体系十二页：同一 MythologyDetail 布局，各体系数据模块驱动 */
const RELIGION_PREFIX = 'religion/';

function ChristianityHub({ data }) {
  const navigate = useNavigate();
  return (
    <div className="school-detail mtd">
      <section className="school-hero-section school-hero">
        {data.heroImage && <img className="school-hero-art" src={ossImg(data.heroImage, { w: 1280 })} alt="" fetchPriority="high" onError={ossFallback} />}
        <header className="school-masthead">
          <Link className="school-brand" to="/">DeepPhilosophy</Link>
          <Link className="school-back" to="/more/religion">← 返回宗教</Link>
        </header>
        <div className="school-hero-copy">
          <p className="school-kicker">{data.en}</p>
          <h1>{data.name}</h1>
          <p className="school-hero-quote">{data.heroQuote ? `\u201C${data.heroQuote}\u201D` : ''}</p>
          <p className="school-hero-author">{data.heroQuoteSource || ''}</p>
        </div>
        <div className="school-hero-foot">
          <span>{data.subtitle}</span>
          <a href="#branches" className="school-start" aria-label="查看三分支">↓</a>
          <span>东正 · 天主 · 新教</span>
        </div>
      </section>
      <div className="school-reading">
        <section id="branches" className="school-section">
          <header className="school-section-heading centered">
            <span className="school-kicker">THREE BRANCHES</span>
            <h2>三大分支</h2>
          </header>
          <div className="mtd-branch-cards">
            {data.branches.map(br => (
              <button key={br.id} type="button" className="mtd-branch-card"
                onClick={() => navigate(`/more/religion/${br.id}`)}>
                <div style={{ position: 'relative', height: '200px', overflow: 'hidden', flexShrink: 0 }}><img src={br.hero} alt="" loading="lazy" style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', objectFit: 'cover' }} /></div>
                <h3>{br.name}</h3>
                <small>{br.en}</small>
                <p>{br.desc}</p>
                <span className="mtd-branch-arrow">→</span>
              </button>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}

const DETAIL_REGISTRY = Object.fromEntries(
  Object.entries(ALL_DETAILS).map(([key, data]) => [
    key,
    (() => {
      if (key === 'religion/christianity') return { component: ChristianityHub, data };
      if (key.startsWith(RELIGION_PREFIX)) return { component: ReligionDetail, data };
      return { component: MythologyDetail, data };
    })(),
  ]),
);

const OUTLINE = [
  { label: '概述', desc: '它是什么、从何而来——一段足以进入语境的开场。' },
  { label: '思想脉络', desc: '关键文本、人物与演化节点，沿时间展开的谱系。' },
  { label: '与哲学的勾连', desc: '它如何回应哲学的追问——站内哲人、流派与书籍的交叉入口。' },
  { label: '延伸阅读', desc: '经典文本与站内可读著作的对照书单。' },
];

export default function MoreTopicPage() {
  const navigate = useNavigate();
  const { discipline, topic: topicId } = useParams();
  const t = getTopic(discipline, topicId);
  const entry = t ? DETAIL_REGISTRY[`${discipline}/${topicId}`] : null;

  useSEO(
    t ? `${t.name} — ${t.discipline.name} | DeepPhilosophy` : '更多 | DeepPhilosophy',
    entry ? entry.data.subtitle : (t?.note || ''),
  );

  if (!t) {
    return (
      <div className="page-container">
        <div className="empty-state" style={{ padding: '120px 20px' }}>
          <p>未找到该主题</p>
          <p style={{ marginTop: 12 }}>
            <button className="btn btn-secondary" onClick={() => navigate('/more')}>返回更多</button>
          </p>
        </div>
      </div>
    );
  }

  /* 已建成专用布局的详情（如中国神话） */
  if (entry) {
    const Detail = entry.component;
    return <Detail data={entry.data} topic={t} />;
  }

  /* 占位：详情布局尚未建设 */
  const d = t.discipline;

  return (
    <div className="page-container" style={{ paddingBottom: 0 }}>

      <section className="more-topic-hero" style={{ '--disc': d.color }}>
        <button className="more-back" onClick={() => navigate(`/more/${d.id}`)}>← 返回{d.name}</button>
        <p className="more-hero-eyebrow" style={{ color: d.color, marginTop: 26 }}>{d.en} · {d.code}</p>
        <h1>{t.name}</h1>
        <div className="more-disc-divider" style={{ background: d.color }} />
        <p>{t.note}</p>
        {t.children && (
          <div className="more-topic-children" style={{ justifyContent: 'center', marginTop: 16 }}>
            {t.children.map(c => <span key={c} className="tag">{c}</span>)}
          </div>
        )}
      </section>

      <section className="more-topic-body">
        <div className="more-topic-card">
          <h2>详情页规划中</h2>
          <p>Planned Structure — 内容将按以下四栏陆续撰写</p>
          <div className="more-outline">
            {OUTLINE.map(o => (
              <div key={o.label} className="more-outline-row">
                <span className="more-outline-label">{o.label}</span>
                <span className="more-outline-desc">{o.desc}</span>
              </div>
            ))}
          </div>
          <p className="more-topic-card-note">完整内容将在后续版本中上线</p>
        </div>
      </section>

      <p className="more-footnote">{d.name} · {d.en}</p>
    </div>
  );
}
