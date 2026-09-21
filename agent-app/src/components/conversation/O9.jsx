import { useEffect, useRef } from 'react';
import { BookOpen, GraduationCap, Layers, X, Quote, ShieldCheck, ExternalLink, Compass, ScanFace, Gift, Battery, Moon, Bot, Minus, ArrowDown } from 'lucide-react';
import { plainText } from '../../data/generalStream';
import { generalAccessLabel, generalEvidenceLayer, sourceHref } from '../../utils/evidence';

/**
 * O9 UI/UX 组件集（docs/ui/O9_*）——设计定型的落地件。
 *
 * DepthControls   回答附近的深度控件（简单一点/深入一点/看原典/看学术研究）。
 *                 O9 为交互合同: 以措辞化追问发回 composer; O11 起 mapped 到 Reader State。
 * EpStarter       现实哲学入口（O8-R3 冻结 EP 六题作为设计样例）。
 * SourceDrawer    引用来源抽屉: 全量书目字段 + 原文摘录 + 核验状态 + 阅读器深链。
 * researchPhase   研究状态五态映射（工具事件 → 用户友好的相位措辞; 不暴露 raw 日志）。
 * layerOf         来源分层: primary（原典）/ scholarly（学术）/ web（网络背景）。
 */


import { useState as _useState } from 'react';
import { researchPhaseKey as _phaseKey, RESEARCH_PHASES as _PHASES, layerOf as _layerOf, layerLabel as _layerLabel } from '../../utils/o9Research';

export const RESEARCH_PHASES = _PHASES;
export function researchPhase(toolName, textOrLang, maybeLang) {
  const hasText = maybeLang !== undefined;
  const text = hasText ? textOrLang : '';
  const lang = hasText ? maybeLang : textOrLang;
  return _PHASES[_phaseKey(toolName, text)][lang === 'en' ? 'en' : 'zh'];
}
export function researchPhaseKey(toolName, text) {
  return _phaseKey(toolName, text);
}
import { resolveCite, resolvePrimaryLink, DP_READER as _DP_READER } from '../../utils/api';
function ReaderLink({ citation, fallback, zh }) {
  const [busy, setBusy] = _useState(false);
  const [failed, setFailed] = _useState(false);
  const [href, setHref] = _useState(fallback || null);
  const open = () => {
    if (href) { window.open(href, '_blank'); return; }
    if (busy || !citation.book) return;
    setBusy(true);
    resolveCite(citation.book, citation.chapter || '')
      .then((d) => {
        setBusy(false);
        if (d.error || d.matched === false) { setFailed(true); return; }
        const u = `${_DP_READER}/${d.book_id}?ch=${d.chapter_idx || 0}`;
        setHref(u);
        window.open(u, '_blank');
      })
      .catch(() => { setBusy(false); setFailed(true); });
  };
  if (failed) return null;
  return (
    <button className="o9-drawer-link" onClick={open} style={{ border: 'none', background: 'transparent', cursor: 'pointer', padding: 0 }}>
      <ExternalLink size={12} aria-hidden /> {busy ? '…' : (zh ? '在阅读器中打开原典' : 'Open primary text in reader')}
    </button>
  );
}

/* ── 来源分层（纯函数在 utils/o9Research.js） ── */
export const layerOf = _layerOf;
export const layerLabel = _layerLabel;

/* ── Depth Controls（§D; O11 起映射 Reader State / Answer Depth / Research Depth） ── */
const DEPTHS = [
  { key: 'simpler', zh: '简单一点', en: 'Simpler',
    promptZh: '请用更通俗的语言重新解释上面的回答，少用术语，多给例子。',
    promptEn: 'Please re-explain the answer above in plainer language, with fewer technical terms and more examples.' },
  { key: 'deeper', zh: '深入一点', en: 'Deeper',
    promptZh: '请在上面的回答基础上更深入一层：展开关键概念的哲学史脉络与核心争议。',
    promptEn: 'Go one level deeper on the answer above: unpack the historical lineage of the key concepts and the core controversies.' },
  { key: 'primary', zh: '看原典', en: 'Primary texts',
    promptZh: '请针对上面的回答，引用相关原典原文（给出书名与章节），并解释原文语境。',
    promptEn: 'For the answer above, quote relevant primary-text passages (with work and chapter) and explain their context.' },
  { key: 'scholarly', zh: '看学术研究', en: 'Scholarship',
    promptZh: '请针对上面的回答检索并综述相关学术研究（给出代表文献与争论点）。',
    promptEn: 'For the answer above, survey relevant scholarship (representative literature and points of debate).' },
];
export function DepthControls({ onPick, disabled, lang, general = false, kinds }) {
  const en = lang === 'en';
  if (disabled && !general) return null;
  const choices = general ? DEPTHS.map(d => d.key === 'deeper' ? { ...d,
    promptZh: '请沿着这段回答最关键、还没有真正解决的难点继续想下去。检验最有力的反对意见，必要时修正原判断。',
    promptEn: 'Follow the most important unresolved difficulty in this answer. Test the strongest objection and revise the judgment if needed.',
  } : d) : DEPTHS;
  return (
    <div className="o9-depth" role="group" aria-label="Depth controls">
      {choices.filter(d => !kinds || kinds.includes(d.key)).map((d) => (
        <button key={d.key} className="o9-depth-chip" disabled={disabled}
          onClick={() => onPick(en ? d.promptEn : d.promptZh)}
          aria-label={d[en ? 'en' : 'zh']}>
          {d.key === 'simpler' && (general ? <Minus size={11} aria-hidden /> : '◦ ')}
          {d.key === 'deeper' && (general ? <ArrowDown size={11} aria-hidden /> : '↧ ')}
          {d.key === 'primary' && <BookOpen size={11} style={{ verticalAlign: '-1px', marginRight: 4 }} aria-hidden />}
          {d.key === 'scholarly' && <GraduationCap size={11} style={{ verticalAlign: '-1px', marginRight: 4 }} aria-hidden />}
          {d[en ? 'en' : 'zh']}
        </button>
      ))}
    </div>
  );
}

/* ── Everyday Philosophy 入口（§5; O8-R3 冻结 EP 六题） ── */
export const EP_QUESTIONS = {
  zh: [
    { title: '导航不会责怪你', q: '导航在你走错路时绝不会责怪你，而是说「已帮你重新规划路线」。这件事有什么值得哲学思考的？' },
    { title: '期待是暴力吗', q: '对他人的期待是不是一种微妙的暴力？' },
    { title: '教师节送礼', q: '教师节快到了，要给老师送礼吗？' },
    { title: '手机没电就心慌', q: '手机没电就心慌不安——我对设备的这种「依赖」，是一种成瘾，还是说明我与工具本来就分不开？' },
    { title: '深夜倾诉的朋友', q: '好朋友总在深夜找我倾诉负面情绪，我最近很累，但怕拒绝会伤害他。一个「好朋友」应该无条件接住对方吗？' },
    { title: 'AI 安慰与真心', q: 'AI 比我更会安慰人。如果安慰的效果可以被计算和优化，「真心安慰」还有价值吗？' },
  ],
  en: [
    { title: 'The GPS never blames you', q: 'Your GPS never scolds you when you take a wrong turn — it just says "recalculating". What is philosophically interesting about this?' },
    { title: 'Expectation as violence', q: 'Is expecting things from others a subtle form of violence?' },
    { title: 'Teacher gifts', q: 'Teacher\'s Day is coming — should you give your teacher a gift?' },
    { title: 'Low-battery anxiety', q: 'My phone dying makes me anxious. Is my "dependence" on devices an addiction, or evidence that tools and selves were never separate?' },
    { title: 'The midnight friend', q: 'A friend always vents to me late at night. I am exhausted but afraid hurting them. Must a good friend always be there?' },
    { title: 'AI comfort vs sincerity', q: 'AI comforts people better than I do. If comfort can be computed and optimized, does "sincere comfort" still matter?' },
  ],
};
export function EpStarter({ lang, onPick }) {
  const items = EP_QUESTIONS[lang === 'en' ? 'en' : 'zh'] || EP_QUESTIONS.zh;
  const icons = [Compass, ScanFace, Gift, Battery, Moon, Bot];
  return (
    <div className="o9-ep" data-testid="o9-ep-entry">
      <div className="o9-ep-cap"><Layers size={12} aria-hidden /> {lang === 'en' ? 'Everyday philosophy' : '现实生活哲学'}</div>
      <div className="o9-ep-grid">
        {items.map((it, i) => {
          const EntryIcon = icons[i];
          return (
          <button key={it.title} className="o9-ep-card" onClick={() => onPick(it.q)}>
            <span className="o9-ep-icon" aria-hidden><EntryIcon size={18} strokeWidth={1.5} /></span>
            <span className="o9-ep-title">{it.title}</span>
            <span className="o9-ep-q">{it.q.length > 42 ? it.q.slice(0, 42) + '…' : it.q}</span>
          </button>
        ); })}
      </div>
    </div>
  );
}

/* ── Source Drawer（§B Citation UX: 点击引用 → 全量来源 + 核验状态 + 原典深链） ── */
export function GeneralReaderLink({ citation, zh }) {
  const scholarly = generalEvidenceLayer(citation) === 'scholarly';
  const direct = sourceHref(citation);
  const [resolved, setResolved] = _useState(null);
  const [error, setError] = _useState(false);
  const [attempt, setAttempt] = _useState(0);
  useEffect(() => {
    if (direct || !citation.book || scholarly) return;
    let active = true;
    setError(false); setResolved(null);
    resolvePrimaryLink(citation.book, citation.chapter || '').then(data => {
      if (!active) return;
      if (!data.matched || !data.url) { setError(true); return; }
      const link = sourceHref({ book: citation.book, reader_url: data.url });
      if (!link) { setError(true); return; }
      setResolved({ book: citation.book, chapter: citation.chapter, url: link });
    }).catch(() => { if (active) setError(true); });
    return () => { active = false; };
  }, [direct, citation.book, citation.chapter, scholarly, attempt]);
  const href = direct || (resolved?.book === citation.book && resolved?.chapter === citation.chapter ? resolved.url : null);
  if (href) return <a className="o9-drawer-link" href={href} target="_blank" rel="noopener noreferrer"><ExternalLink size={12} />{generalEvidenceLayer(citation) === 'primary' ? (zh ? '阅读原典' : 'Read primary text') : (zh ? '打开来源' : 'Open source')}</a>;
  if (!citation.book || scholarly) return <span>{zh ? '此来源未提供可打开的链接' : 'No usable link is available for this source'}</span>;
  if (error) return <button className="cw-cite-more" onClick={() => setAttempt(v => v + 1)}>{zh ? '暂未定位到原文，点击重试' : 'Source unavailable. Retry'}</button>;
  return <span role="status">{zh ? '正在定位原文…' : 'Locating source…'}</span>;
}

export function SourceDrawer({ open, citation, lang, onClose, general = false }) {
  const zh = lang !== 'en';
  const drawerRef = useRef(null);
  const closeRef = useRef(onClose);
  closeRef.current = onClose;
  useEffect(() => {
    if (!open || !general) return;
    const previous = document.activeElement;
    const root = drawerRef.current;
    root?.querySelector('button')?.focus();
    const trap = e => {
      if (e.key !== 'Tab') return;
      const nodes = [...(root?.querySelectorAll('button:not(:disabled), a[href], [tabindex="0"]') || [])];
      if (!nodes.length) return;
      if (e.shiftKey && document.activeElement === nodes[0]) { e.preventDefault(); nodes.at(-1).focus(); }
      else if (!e.shiftKey && document.activeElement === nodes.at(-1)) { e.preventDefault(); nodes[0].focus(); }
    };
    const overflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    root?.addEventListener('keydown', trap);
    return () => { root?.removeEventListener('keydown', trap); document.body.style.overflow = overflow; previous?.focus?.(); };
  }, [open, general]);

  useEffect(() => {
    if (!open) return;
    const onKey = (e) => { if (e.key === 'Escape') closeRef.current(); };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [open]);
  if (!open || !citation) return null;
  const c = general ? Object.fromEntries(Object.entries(citation).map(([key, value]) => [key, typeof value === 'string' ? plainText(value) : value])) : citation;
  const link = c.reader_url || c.url || null;
  const excerpt = general ? (c.excerpt || c.quote || c.passage || c.abstract_text) : (c.quote || c.passage || c.abstract_text);
  const rows = [
    ...(general ? [
      [zh ? '资料类型' : 'Source type', layerLabel(generalEvidenceLayer(c), lang)],
      [zh ? '读取范围' : 'Reading scope', generalAccessLabel(c.access_level, lang)],
    ] : []),
    [zh ? '作者' : 'Author', (Array.isArray(c.authors) ? c.authors.map(a => a?.name || a).filter(Boolean).join(', ') : c.author) || null],
    [zh ? '著作' : 'Work', c.work || c.book || null],
    [zh ? '章节/页' : 'Chapter/Pages', c.chapter || c.page || null],
    [zh ? '出版信息' : 'Venue', c.container_title || c.venue || null],
    [zh ? '年份' : 'Year', c.publication_year || c.year || null],
    [zh ? 'DOI' : 'DOI', c.doi || null],
  ].filter(([, v]) => v);
  return (
    <div className="o9-drawer-mask" onClick={onClose}>
      <aside ref={drawerRef} className="o9-drawer" role="dialog" aria-modal="true" aria-label={zh ? '引用来源' : 'Citation source'}
        onClick={(e) => e.stopPropagation()}>
        <header className="o9-drawer-head">
          <span className="o9-drawer-cap"><Quote size={13} aria-hidden /> {zh ? '引用来源' : 'Citation source'}</span>
          <button className="o9-drawer-close" onClick={onClose} aria-label="close"><X size={15} /></button>
        </header>
        <div className="o9-drawer-body">
          <div className="o9-drawer-title">{c.title || c.book || c.work || '—'}</div>
          {rows.map(([k, v]) => (
              <div key={k} className="o9-drawer-row"><span className="o9-drawer-k">{k}</span><span>{general ? plainText(v) : v}</span></div>
          ))}
          {excerpt && (general ? <section className="general-source-excerpt" aria-label={zh ? '来源片段' : 'Source excerpt'}>
            <div className="cw-evidence-cap"><Quote size={11} aria-hidden />{zh ? '来源片段' : 'Source excerpt'}</div>
            <blockquote className="o9-drawer-quote">{excerpt}</blockquote>
          </section> : <blockquote className="o9-drawer-quote"><Quote size={11} aria-hidden />{excerpt.slice(0, 420)}</blockquote>)}
          <div className="o9-drawer-verify">
            <ShieldCheck size={12} aria-hidden />
            {general ? (c.used === false ? (zh ? '检索相关材料，未被本回答引用' : 'Retrieved material, not cited in this answer') : (zh ? '本回答使用的来源' : 'Source used in this answer')) : c.used === false ? (zh ? '检索到但未被本回答引用' : 'Retrieved but not cited by this answer')
              : (zh ? '已核验：本回答实际引用的证据' : 'Verified: actually cited by this answer')}
          </div>
          {(link || citation.book || (general && citation.doi)) && (
            general ? <GeneralReaderLink key={c.evidence_id || c.book || c.url} citation={c} zh={zh} /> : <ReaderLink citation={citation} fallback={link} zh={zh} />
          )}
        </div>
      </aside>
    </div>
  );
}
