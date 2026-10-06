/**
 * MythologyDetail — 神话体系详情页（"更多"三级页，数据驱动，适用于全部神话体系）
 * 全部采用流派页（SchoolDetailPage）的设计语言：
 *   hero = school-hero · 章节导航 = school-chapter-nav
 *   II 创世叙事 = school-branch 幽灵概念字网格（可展开文言与母题）
 *   III 神谱 = school 星丛（PantheonSection）
 *   IV 母题 = school-branch 手风琴（按类分组）
 *   V 文献层累 = school-river 河流时间轴（左右交替 + 展开贡献）
 *   VI 哲学勾连 = 居中对话体 · VII 交叉入口 = school-sources/ending-links
 * 关键词 = 辞海辞条（悬停浮现释义 · 点击钉住 · 卡内定位）
 * 无滚动浮现动画
 */
import { Fragment, useEffect, useState } from 'react';
import { createPortal } from 'react-dom';
import { Link, useNavigate } from 'react-router-dom';
import { useSEO } from '../../utils/seo';
import PantheonSection from './PantheonSection';
import '../school/ConstellationMap.css';
import '../school/TimelineSection.css';
import '../../pages/SchoolDetailPage.css';
import './more-detail.css';

const CHAPTERS = [
  { id: 'sec-overview', num: 'I', name: '概述', en: 'Overview' },
  { id: 'sec-cosmogony', num: 'II', name: '创世叙事', en: 'Cosmogony' },
  { id: 'sec-pantheon', num: 'III', name: '神谱与神祇', en: 'Pantheon' },
  { id: 'sec-motifs', num: 'IV', name: '神话母题', en: 'Motifs' },
  { id: 'sec-strata', num: 'V', name: '文献层累', en: 'Stratigraphy' },
  { id: 'sec-bridges', num: 'VI', name: '哲学勾连', en: 'Myth ↔ Philosophy' },
  { id: 'sec-cross', num: 'VII', name: '交叉入口', en: 'Crossroads' },
];

/* 河流时间轴年代色轮（各体系条目可自带 color 覆盖） */
const ERA_PALETTE = ['#a77c4f', '#a98e53', '#738e9a', '#ad7770', '#778e6a', '#92819d'];

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

const hintOf = text => {
  const clean = String(text || '').replace(/^[""]|[""]$/g, '');
  return clean.length > 15 ? clean.slice(0, 15) + '…' : clean;
};

export default function MythologyDetail({ data, topic }) {
  const navigate = useNavigate();
  const d = topic.discipline;
  useSEO(`${data.name} — ${d.name} | DeepPhilosophy`, data.subtitle);

  const [openAct, setOpenAct] = useState(null);
  const [openMotif, setOpenMotif] = useState(null);
  const [openStratum, setOpenStratum] = useState(null);

  /* 关键词辞海：悬停浮现释义，点击钉住；「在正文中定位」执行跳转 */
  const [kwPop, setKwPop] = useState(null);
  const glossOf = word => (data.keywordGlosses || {})[word] || null;
  const placePop = (buttonEl, word, pinned) => {
    const gloss = glossOf(word);
    if (!gloss) return;
    const r = buttonEl.getBoundingClientRect();
    const above = r.bottom + 240 > window.innerHeight;
    setKwPop({ word, gloss, left: Math.min(Math.max(r.left + r.width / 2, 190), window.innerWidth - 190), top: above ? r.top - 12 : r.bottom + 12, above, pinned });
  };
  const showKw = e => { if (kwPop?.pinned || !glossOf(e.currentTarget.textContent)) return; placePop(e.currentTarget, e.currentTarget.textContent, false); };
  const hideKw = () => setKwPop(prev => prev?.pinned ? prev : null);
  const pinKw = e => {
    e.stopPropagation();
    const word = e.currentTarget.textContent;
    if (!glossOf(word)) { goKeyword(word); return; }
    if (kwPop?.word === word && kwPop.pinned) { setKwPop(null); return; }
    placePop(e.currentTarget, word, true);
  };
  useEffect(() => {
    if (!kwPop?.pinned) return;
    const close = () => setKwPop(null);
    document.addEventListener('click', close);
    return () => document.removeEventListener('click', close);
  }, [kwPop?.pinned]);

  const goKeyword = keyword => {
    const target = (data.keywordTargets || {})[keyword];
    if (!target) return;
    if (target.motif) setOpenMotif(target.motif);
    const jump = () => {
      const el = document.getElementById(target.sec);
      if (el) window.scrollTo({ top: el.getBoundingClientRect().top + window.scrollY - 16, behavior: 'smooth' });
    };
    requestAnimationFrame(jump);
    setTimeout(jump, 380);
  };

  return (
    <div className="school-detail mtd">

      {/* ═══ HERO ═══ */}
      <section className="school-hero-section school-hero" aria-label={`${data.name}封面`}>
        <img className="school-hero-art" src={data.heroImage || '/schools/default.webp'} alt="" fetchPriority="high" />
        <header className="school-masthead">
          <Link className="school-brand" to="/">DeepPhilosophy</Link>
          <Link className="school-back" to={`/more/${d.id}`}>← 返回{d.name}</Link>
        </header>
        <div className="school-hero-copy">
          <p className="school-kicker">{data.en}</p>
          <h1>{data.name}</h1>
          <p className="school-hero-quote">{data.heroQuote ? `“${data.heroQuote}”` : ''}</p>
          <p className="school-hero-author">{data.heroQuoteAuthor || data.subtitle}</p>
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

        {/* ═══ II · 创世叙事 ═══ */}
        <section id={CHAPTERS[1].id} className="school-section">
          <SectionHeading num={CHAPTERS[1].num} en={CHAPTERS[1].en} title="创世叙事" note={data.cosmogony.intro} />
          <div className="school-branch-parent">{data.cosmogony.parent || '混沌 · 天地开辟'}</div>
          <div className="school-branch-grid">
            {data.cosmogony.acts.map(a => {
              const open = openAct === a.act;
              return (
                <article key={a.act} className={`school-branch ${open ? 'is-open' : ''}`}>
                  <button type="button" className="school-branch-trigger" aria-expanded={open}
                    onClick={() => setOpenAct(open ? null : a.act)}>
                    <span className="school-branch-focus" aria-hidden="true">{a.focus || a.act.slice(0, 2)}</span>
                    <small>{a.source}</small>
                    <h3>{a.act}</h3>
                    <p>{a.text}</p>
                    <span className="school-branch-hint"><span>{a.hint || '文言原句 · 母题注解'}</span><span aria-hidden="true">{open ? '−' : '＋'}</span></span>
                  </button>
                  <div className="school-branch-detail" hidden={!open}>
                    {a.quote && <p className="mtd-act-quote">“{a.quote}”</p>}
                    <p className="mtd-act-meaning"><i>母题</i>{a.meaning}</p>
                  </div>
                </article>
              );
            })}
          </div>
        </section>

        {/* ═══ III · 神谱与神祇 ═══ */}
        <section id={CHAPTERS[2].id} className="school-section">
          <SectionHeading num={CHAPTERS[2].num} en={CHAPTERS[2].en} title="神谱与神祇" note={data.pantheon.intro} />
          <PantheonSection pantheon={data.pantheon} deities={data.deities} categories={data.deityCategories} />
        </section>

        {/* ═══ IV · 神话母题 ═══ */}
        <section id={CHAPTERS[3].id} className="school-section">
          <SectionHeading num={CHAPTERS[3].num} en={CHAPTERS[3].en} title="神话母题" note={data.motifs.intro} />
          {data.motifs.categories.map(cat => {
            const list = data.motifs.items.filter(m => m.category === cat.id);
            if (!list.length) return null;
            return (
              <div key={cat.id} className="mtd-motif-cat">
                <div className="school-branch-parent">{cat.name}</div>
                <div className="school-branch-grid">
                  {list.map(m => {
                    const open = openMotif === m.id;
                    return (
                      <article key={m.id} className={`school-branch ${open ? 'is-open' : ''}`}>
                        <button type="button" className="school-branch-trigger" aria-expanded={open}
                          onClick={() => setOpenMotif(open ? null : m.id)}>
                          <span className="school-branch-focus" aria-hidden="true">{m.focus || m.name.slice(0, 2)}</span>
                          <small>{hintOf(m.motif)}</small>
                          <h3>{m.name}</h3>
                          <p>{m.story}</p>
                          <span className="school-branch-hint"><span>母题 · 哲学勾连</span><span aria-hidden="true">{open ? '−' : '＋'}</span></span>
                        </button>
                        <div className="school-branch-detail" hidden={!open}>
                          <p className="mtd-motif-line"><i>母题</i>{m.motif}</p>
                          <p className="mtd-motif-line"><i>哲学勾连</i>{m.philosophy}</p>
                          {m.links && m.links.length > 0 && (
                            <div className="school-branch-terms">
                              {m.links.map(l => <LinkChip key={l.type + l.name} link={l} navigate={navigate} />)}
                            </div>
                          )}
                        </div>
                      </article>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </section>

        {/* ═══ V · 文献层累 ═══ */}
        <section id={CHAPTERS[4].id} className="school-section">
          <SectionHeading num={CHAPTERS[4].num} en={CHAPTERS[4].en} title="文献层累" note={data.strata.intro} />
          <div className="school-river mtd-river">
            <div className="mtd-river-spine" aria-hidden="true" />
            <div className="school-river-events">
              {data.strata.items.map((s, idx) => {
                const open = openStratum === s.source;
                const color = s.color || ERA_PALETTE[idx % ERA_PALETTE.length];
                return (
                  <div key={s.source} className={`school-river-event ${s.major ? 'is-major' : ''} ${open ? 'is-open' : ''}`} style={{ '--event-color': color }}>
                    <span className="school-river-node" />
                    <div className="school-river-exhibit">
                      <button type="button" className="school-river-trigger" aria-expanded={open}
                        onClick={() => setOpenStratum(open ? null : s.source)}>
                        <span className="school-river-year mtd-era">{s.era}</span>
                        <span className="school-river-kind">“{s.quote}”</span>
                        <span className="school-river-title">{s.source}</span>
                        <span className="school-river-cue">{open ? '收起' : (s.cue || '它为神话体系贡献了什么')} ＋</span>
                      </button>
                      <div className="school-river-reveal">
                        <div className="school-river-reveal-inner">
                          <div className="school-river-detail"><p>{s.contribution}</p></div>
                        </div>
                      </div>
                    </div>
                    <div className="school-river-art">
                      <span className="school-river-art-word">{s.glyph || s.source[1]}</span>
                      <span className="school-river-art-caption">{s.major ? '层累之柱' : '文献一层'}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </section>

        {/* ═══ VI · 哲学勾连 ═══ */}
        <section id={CHAPTERS[5].id} className="school-section">
          <SectionHeading num={CHAPTERS[5].num} en={CHAPTERS[5].en} title="哲学勾连" note={data.bridges.intro} />
          <div className="mtd-dialogues">
            {data.bridges.items.map((b, i) => (
              <div key={b.myth} className="mtd-dialogue">
                <span className="school-kicker">对照 · {String(i + 1).padStart(2, '0')}</span>
                <p className="mtd-dialogue-myth">{b.myth}</p>
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

        {/* ═══ VII · 交叉入口 ═══ */}
        <section id={CHAPTERS[6].id} className="school-section">
          <SectionHeading num={CHAPTERS[6].num} en={CHAPTERS[6].en} title="关键词与交叉入口" />
          <div className="mtd-colophon">
            <span className="school-kicker">Keywords · 名物关键词 · 点击定位</span>
            <p className="mtd-colophon-line">
              {data.keywords.map((k, i) => (
                <Fragment key={k}>
                  {i > 0 && <span className="mtd-kw-sep" aria-hidden="true">·</span>}
                  <button type="button" className="mtd-keyword" aria-label={`辞条：${k}`}
                    onMouseEnter={showKw} onMouseLeave={hideKw} onClick={pinKw}>{k}</button>
                </Fragment>
              ))}
            </p>
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
          {data.heroImage && <img className="school-ending-art" src={data.heroImage} alt="" />}
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

      {/* ═══ 关键词辞条浮层（悬停浮现 · 点击钉住；portal 到 body，避开 transform 祖先） ═══ */}
      {kwPop && createPortal(
        <div className={`mtd-kw-pop${kwPop.above ? ' is-above' : ''}${kwPop.pinned ? ' is-pinned' : ''}`}
          style={{ left: kwPop.left, top: kwPop.top }} role="tooltip"
          onClick={e => e.stopPropagation()}>
          <h4>{kwPop.word}</h4>
          <p>{kwPop.gloss}</p>
          <div className="mtd-kw-pop-foot">
            <button type="button" onClick={() => { goKeyword(kwPop.word); setKwPop(null); }}>在正文中定位 →</button>
            <button type="button" onClick={() => setKwPop(null)}>收起</button>
          </div>
        </div>,
        document.body,
      )}
    </div>
  );
}
