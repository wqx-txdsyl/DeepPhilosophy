/**
 * 更多 — 主题详情页（三级）
 * /more/:discipline/:topic
 * 有专用详情布局的题材走 DETAIL_REGISTRY（如神话体系），
 * 其余题材回退到"规划中"占位页——新详情完成后在此登记即可。
 */
import { useNavigate, useParams } from 'react-router-dom';
import { useSEO } from '../utils/seo';
import { getTopic } from '../data/moreContent';
import { MYTH_DETAILS } from '../data/moreTopics';
import MythologyDetail from '../components/more/MythologyDetail';
import './MorePage.css';

/* 神话体系十二页：同一 MythologyDetail 布局，各体系数据模块驱动 */
const DETAIL_REGISTRY = Object.fromEntries(
  Object.entries(MYTH_DETAILS).map(([key, data]) => [key, { component: MythologyDetail, data }]),
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
