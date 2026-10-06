import CdnImage from '../../components/CdnImage';
/**
 * ReligionDetail — 宗教体系详情页（"更多"三级页，宗教专用布局）
 * 区别于神话（故事→谱系→母题），宗教的核心维度是：
 *   I 概述 → II 创始与传承 → III 教义体系 → IV 经典文献
 *   → V 仪式与实践 → VI 宗派与分支 → VII 哲学勾连 → VIII 交叉入口
 * 共用 school-detail 主题（与流派/神话同一设计语言）
 */
import { Link, useNavigate } from 'react-router-dom';
import { useSEO } from '../../utils/seo';
import '../../pages/SchoolDetailPage.css';
import './more-detail.css';

const CHAPTERS = [
  { id: 'sec-overview', num: 'I', name: '概述', en: 'Overview' },
  { id: 'sec-lineage', num: 'II', name: '创始与传承', en: 'Founding & Lineage' },
  { id: 'sec-doctrine', num: 'III', name: '教义体系', en: 'Doctrine' },
  { id: 'sec-scripture', num: 'IV', name: '经典文献', en: 'Scripture' },
  { id: 'sec-ritual', num: 'V', name: '仪式与实践', en: 'Practice' },
  { id: 'sec-branch', num: 'VI', name: '宗派与分支', en: 'Denominations' },
  { id: 'sec-bridge', num: 'VII', name: '哲学勾连', en: 'Philosophy' },
  { id: 'sec-cross', num: 'VIII', name: '交叉入口', en: 'Crossroads' },
];

function SectionHeading({ num, en, title, note }) {
  return (
    <header className="school-section-heading centered mtd-sec-head">
      <span className="school-kicker">{num} · {en}</span>
      <h2>{title}</h2>
      {note && <p className="mtd-sec-note">{note}</p>}
    </header>
  );
}

function LinkChip({ link, navigate }) {
  const path = link.type === 'school' ? `/school/${encodeURIComponent(link.name)}` : `/author/${encodeURIComponent(link.name)}`;
  return (
    <button type="button" className="mtd-relation-link" onClick={() => navigate(path)}>
      <span>{link.name}</span>
      <small>{link.type === 'school' ? '流派' : '哲人'}</small>
      <i aria-hidden="true">↗</i>
    </button>
  );
}

export default function ReligionDetail({ data, topic }) {
  const navigate = useNavigate();
  const d = topic.discipline;
  useSEO(`${data.name} — ${d.name} | DeepPhilosophy`, data.subtitle);

  return (
    <div className="school-detail mtd">

      {/* ═══ HERO ═══ */}
      <section className="school-hero-section school-hero" aria-label={`${data.name}封面`}>
        {data.heroImage && <CdnImage className="school-hero-art" src={data.heroImage} imageWidth={1600} alt="" fetchPriority="high" />}
        <header className="school-masthead">
          <Link className="school-brand" to="/">DeepPhilosophy</Link>
          <Link className="school-back" to={`/more/${d.id}`}>← 返回{d.name}</Link>
        </header>
        <div className="school-hero-copy">
          <p className="school-kicker">{data.en}</p>
          <h1>{data.name}</h1>
          <p className="school-hero-quote">{data.heroQuote ? `“${data.heroQuote}”` : ''}</p>
          <p className="school-hero-author">{data.heroQuoteSource || ''}</p>
        </div>
        <div className="school-hero-foot">
          <span>{data.subtitle}</span>
          <a href={`#${CHAPTERS[0].id}`} className="school-start" aria-label="开始阅读概述">↓</a>
          <span>{(data.meta || []).map(m => m.value).slice(0, 2).join(' · ')}</span>
        </div>
      </section>

      <div className="school-reading">
        <nav className="school-chapter-nav" aria-label="章节导航">
          {CHAPTERS.map(c => <a key={c.id} href={`#${c.id}`}><small>{c.num}</small>{c.name}</a>)}
        </nav>

        {/* ═══ I · 概述 ═══ */}
        <section id={CHAPTERS[0].id} className="school-section school-overview">
          <SectionHeading num={CHAPTERS[0].num} en={CHAPTERS[0].en} title="概述" />
          <div className="school-prose">
            {data.overview.lead.map((p, i) => <p key={`l${i}`}>{p}</p>)}
          </div>
          {data.overview.sections.map(sec => (
            <div key={sec.title} className="mtd-overview-sec">
              <h3>{sec.title}</h3>
              <div className="school-prose">
                {sec.paras.map((p, i) => <p key={i}>{p}</p>)}
              </div>
            </div>
          ))}
        </section>

        {/* ═══ II · 创始与传承（时间轴式） ═══ */}
        <section id={CHAPTERS[1].id} className="school-section">
          <SectionHeading num={CHAPTERS[1].num} en={CHAPTERS[1].en} title="创始与传承" note={data.lineage.intro} />
          <div className="school-river mtd-river">
            <div className="mtd-river-spine" aria-hidden="true" />
            <div className="school-river-events">
              {data.lineage.events.map(ev => {
                const open = false; // static for now
                return (
                  <div key={ev.title} className={`school-river-event ${ev.major ? 'is-major' : ''}`} style={{ '--event-color': ev.color || 'var(--ochre)' }}>
                    <span className="school-river-node" />
                    <div className="school-river-exhibit">
                      <span className="school-river-year mtd-era">{ev.period}</span>
                      <span className="school-river-kind">{ev.source ? `“${ev.source}”` : ''}</span>
                      <span className="school-river-title">{ev.title}</span>
                      <span className="school-river-cue">{ev.cue || ''}</span>
                    </div>
                    <div className="school-river-art">
                      <span className="school-river-art-word">{ev.glyph || ev.title[0]}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </section>

        {/* ═══ III · 教义体系（概念卡组） ═══ */}
        <section id={CHAPTERS[2].id} className="school-section">
          <SectionHeading num={CHAPTERS[2].num} en={CHAPTERS[2].en} title="教义体系" note={data.doctrines.intro} />
          <div className="mtd-doctrine-grid">
            {data.doctrines.items.map(dv => (
              <article key={dv.name} className="mtd-doctrine-card">
                {dv.sanskrit && <small className="mtd-doctrine-sanskrit">{dv.sanskrit}</small>}
                <h3>{dv.name}</h3>
                <p className="mtd-doctrine-explain">{dv.explanation}</p>
                <p className="mtd-doctrine-significance"><i>教义意义</i>{dv.significance}</p>
              </article>
            ))}
          </div>
        </section>

        {/* ═══ IV · 经典文献（书册列表） ═══ */}
        <section id={CHAPTERS[3].id} className="school-section">
          <SectionHeading num={CHAPTERS[3].num} en={CHAPTERS[3].en} title="经典文献" note={data.scriptures.intro} />
          <div className="mtd-scripture-list">
            {data.scriptures.items.map(s => (
              <div key={s.name} className="mtd-scripture-item">
                <span className="mtd-scripture-era">{s.era}</span>
                <div>
                  <h3 className="mtd-scripture-name">{s.name}</h3>
                  {s.type && <small className="mtd-scripture-type">{s.type}</small>}
                  <p className="mtd-scripture-sig">{s.significance}</p>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* ═══ V · 仪式与实践 ═══ */}
        <section id={CHAPTERS[4].id} className="school-section">
          <SectionHeading num={CHAPTERS[4].num} en={CHAPTERS[4].en} title="仪式与实践" note={data.rituals.intro} />
          <div className="mtd-ritual-grid">
            {data.rituals.items.map(r => (
              <div key={r.name} className="mtd-ritual-item">
                <h4>{r.name}</h4>
                <p>{r.description}</p>
                <p className="mtd-ritual-purpose"><i>意义</i>{r.purpose}</p>
              </div>
            ))}
          </div>
        </section>

        {/* ═══ VI · 宗派与分支 ═══ */}
        <section id={CHAPTERS[5].id} className="school-section">
          <SectionHeading num={CHAPTERS[5].num} en={CHAPTERS[5].en} title="宗派与分支" note={data.branches.intro} />
          <div className="school-branch-grid">
            {data.branches.items.map(br => (
              <article key={br.name} className="school-branch">
                <div className="school-branch-trigger" style={{ cursor: 'default' }}>
                  <small>{br.era}</small>
                  <h3>{br.name}</h3>
                  <p>{br.coreBelief}</p>
                  <span className="school-branch-hint"><span>{br.regions}</span></span>
                </div>
                <div className="school-branch-detail">
                  <p className="mtd-branch-distinction">{br.distinction}</p>
                </div>
              </article>
            ))}
          </div>
        </section>

        {/* ═══ VII · 哲学勾连（居中对话体） ═══ */}
        <section id={CHAPTERS[6].id} className="school-section">
          <SectionHeading num={CHAPTERS[6].num} en={CHAPTERS[6].en} title="哲学勾连" note={data.bridges.intro} />
          <div className="mtd-dialogues">
            {data.bridges.items.map((b, i) => (
              <div key={b.myth || b.religion} className="mtd-dialogue">
                <span className="school-kicker">对照 · {String(i + 1).padStart(2, '0')}</span>
                <p className="mtd-dialogue-myth">{b.religion || b.myth}</p>
                <span className="mtd-dialogue-x" aria-hidden="true">⇄</span>
                <p className="mtd-dialogue-philo">{b.philosophy}</p>
                <p className="mtd-dialogue-note">{b.note}</p>
                {b.links && b.links.length > 0 && (
                  <div className="mtd-dialogue-links">
                    {b.links.map(l => <LinkChip key={l.type + l.name} link={l} navigate={navigate} />)}
                  </div>
                )}
              </div>
            ))}
          </div>
        </section>

        {/* ═══ VIII · 交叉入口 ═══ */}
        <section id={CHAPTERS[7].id} className="school-section">
          <SectionHeading num={CHAPTERS[7].num} en={CHAPTERS[7].en} title="关键词与交叉入口" />
          <div className="mtd-colophon">
            <span className="school-kicker">Keywords · 名物关键词 · 点击定位</span>
            <p className="mtd-colophon-line">{data.keywords.join('　·　')}</p>
          </div>
          <div className="mtd-cross-links">
            <span className="school-kicker">Schools · 相关流派</span>
            <div className="school-ending-links">
              {data.crossLinks.schools.map(s => (
                <button key={s} type="button" className="mtd-relation-link" onClick={() => navigate(`/school/${encodeURIComponent(s)}`)}>
                  <span>{s}</span><small>流派</small><i aria-hidden="true">↗</i>
                </button>
              ))}
            </div>
          </div>
          <div className="mtd-cross-links">
            <span className="school-kicker">Thinkers · 相关哲人</span>
            <div className="school-ending-links">
              {data.crossLinks.authors.map(a => (
                <button key={a} type="button" className="mtd-relation-link" onClick={() => navigate(`/author/${encodeURIComponent(a)}`)}>
                  <span>{a}</span><small>哲人</small><i aria-hidden="true">↗</i>
                </button>
              ))}
            </div>
          </div>
          <div className="school-sources">
            <span className="school-kicker">Texts · 核心文献</span>
            <ul>
              {data.crossLinks.books.map(b => <li key={b.title}>{b.title}<small>{b.note}</small></li>)}
            </ul>
          </div>
        </section>

        {/* ═══ 尾声 ═══ */}
        <section className="school-ending">
          {data.heroImage && <CdnImage className="school-ending-art" src={data.heroImage} imageWidth={1200} alt="" />}
          <p className="school-kicker">EPILOGUE · 尾声</p>
          <p className="school-closing-quote">{data.epilogue}</p>
          <div className="school-ending-links">
            <a href="#sec-overview">回到概述 ↑</a>
            <a href="#" onClick={e => { e.preventDefault(); navigate('/more'); }}>更多索引 →</a>
            <a href="#" onClick={e => { e.preventDefault(); navigate(`/more/${d.id}`); }}>返回{d.name} →</a>
          </div>
        </section>

        <div className="school-footer">
          <span>{data.name} · {data.en}</span>
          <span>DeepPhilosophy — 更多 · {d.name}</span>
        </div>
      </div>
    </div>
  );
}

