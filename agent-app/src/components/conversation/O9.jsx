import { useEffect } from 'react';
import { BookOpen, GraduationCap, Layers, X, Quote, ShieldCheck, ExternalLink } from 'lucide-react';

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
import { resolveCite, DP_READER as _DP_READER } from '../../utils/api';
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

/* ── 来源分层（§7 Scholarly Research UX: 分层展示, 高级字段收进抽屉） ── */
export function layerOf(citation) {
  const c = citation || {};
  if (c.book) return 'primary';
  if (c.doi || c.source_record_id || /journal|press|proceedings/i.test(c.container_title || c.venue || '')) return 'scholarly';
  return 'web';
}

const LAYER_META = {
  primary: { zh: '原典', en: 'Primary' },
  scholarly: { zh: '学术', en: 'Scholarly' },
  web: { zh: '网络', en: 'Web' },
};
export function layerLabel(layer, lang) {
  return (LAYER_META[layer] || LAYER_META.web)[lang === 'en' ? 'en' : 'zh'];
}

/* ── 研究状态五态（§C Research State; 只给相位, 不给 raw 工具日志） ── */
const PHASES = [
  { zh: '正在理解问题', en: 'Understanding the question' },
  { zh: '正在查找原典', en: 'Searching primary texts' },
  { zh: '正在核验出处', en: 'Verifying sources' },
  { zh: '正在查阅学术研究', en: 'Consulting scholarship' },
  { zh: '正在整理论证', en: 'Organizing the argument' },
];
export function researchPhase(toolName, lang) {
  const i = (() => {
    switch (toolName) {
      case 'search_books': case 'get_chapter': case 'get_book_detail': case 'list_books': case 'concept_trace':
        return 1;
      case 'search_scholarship': case 'get_scholarly_source': case 'websearch':
        return 3;
      case 'query_graph': case 'query_database': case 'get_philosopher': case 'get_school':
        return 0;
      default:
        return 4;
    }
  })();
  return PHASES[i][lang === 'en' ? 'en' : 'zh'];
}

/* ── Depth Controls（§D; O11 起映射 Reader State / Answer Depth / Research Depth） ── */
const DEPTHS = [
  { key: 'simpler', zh: '简单一点', en: 'Simpler', prompt: '请用更通俗的语言重新解释上面的回答，少用术语，多给例子。' },
  { key: 'deeper', zh: '深入一点', en: 'Deeper', prompt: '请在上面的回答基础上更深入一层：展开关键概念的哲学史脉络与核心争议。' },
  { key: 'primary', zh: '看原典', en: 'Primary texts', prompt: '请针对上面的回答，引用相关原典原文（给出书名与章节），并解释原文语境。' },
  { key: 'scholarly', zh: '看学术研究', en: 'Scholarship', prompt: '请针对上面的回答检索并综述相关学术研究（给出代表文献与争论点）。' },
];
export function DepthControls({ onPick, disabled, lang }) {
  if (disabled) return null;
  return (
    <div className="o9-depth" role="group" aria-label="Depth controls">
      {DEPTHS.map((d) => (
        <button key={d.key} className="o9-depth-chip" disabled={disabled}
          onClick={() => onPick(d.prompt)}
          aria-label={d[lang === 'en' ? 'en' : 'zh']}>
          {d.key === 'simpler' && '◦ '}
          {d.key === 'deeper' && '↧ '}
          {d.key === 'primary' && <BookOpen size={11} style={{ verticalAlign: '-1px', marginRight: 4 }} aria-hidden />}
          {d.key === 'scholarly' && <GraduationCap size={11} style={{ verticalAlign: '-1px', marginRight: 4 }} aria-hidden />}
          {d[lang === 'en' ? 'en' : 'zh']}
        </button>
      ))}
    </div>
  );
}

/* ── Everyday Philosophy 入口（§5; O8-R3 冻结 EP 六题） ── */
export const EP_QUESTIONS = {
  zh: [
    { icon: '🧭', title: '导航不会责怪你', q: '导航在你走错路时绝不会责怪你，而是说「已帮你重新规划路线」。这件事有什么值得哲学思考的？' },
    { icon: '🪞', title: '期待是暴力吗', q: '对他人的期待是不是一种微妙的暴力？' },
    { icon: '🎁', title: '教师节送礼', q: '教师节快到了，要给老师送礼吗？' },
    { icon: '🔋', title: '手机没电就心慌', q: '手机没电就心慌不安——我对设备的这种「依赖」，是一种成瘾，还是说明我与工具本来就分不开？' },
    { icon: '🌙', title: '深夜倾诉的朋友', q: '好朋友总在深夜找我倾诉负面情绪，我最近很累，但怕拒绝会伤害他。一个「好朋友」应该无条件接住对方吗？' },
    { icon: '🤖', title: 'AI 安慰与真心', q: 'AI 比我更会安慰人。如果安慰的效果可以被计算和优化，「真心安慰」还有价值吗？' },
  ],
  en: [
    { icon: '🧭', title: 'The GPS never blames you', q: 'Your GPS never scolds you when you take a wrong turn — it just says "recalculating". What is philosophically interesting about this?' },
    { icon: '🪞', title: 'Expectation as violence', q: 'Is expecting things from others a subtle form of violence?' },
    { icon: '🎁', title: 'Teacher gifts', q: 'Teacher\'s Day is coming — should you give your teacher a gift?' },
    { icon: '🔋', title: 'Low-battery anxiety', q: 'My phone dying makes me anxious. Is my "dependence" on devices an addiction, or evidence that tools and selves were never separate?' },
    { icon: '🌙', title: 'The midnight friend', q: 'A friend always vents to me late at night. I am exhausted but afraid hurting them. Must a good friend always be there?' },
    { icon: '🤖', title: 'AI comfort vs sincerity', q: 'AI comforts people better than I do. If comfort can be computed and optimized, does "sincere comfort" still matter?' },
  ],
};
export function EpStarter({ lang, onPick }) {
  const items = EP_QUESTIONS[lang === 'en' ? 'en' : 'zh'] || EP_QUESTIONS.zh;
  return (
    <div className="o9-ep" data-testid="o9-ep-entry">
      <div className="o9-ep-cap"><Layers size={12} aria-hidden /> {lang === 'en' ? 'Everyday philosophy' : '现实生活哲学'}</div>
      <div className="o9-ep-grid">
        {items.map((it) => (
          <button key={it.title} className="o9-ep-card" onClick={() => onPick(it.q)}>
            <span className="o9-ep-icon" aria-hidden>{it.icon}</span>
            <span className="o9-ep-title">{it.title}</span>
            <span className="o9-ep-q">{it.q.length > 42 ? it.q.slice(0, 42) + '…' : it.q}</span>
          </button>
        ))}
      </div>
    </div>
  );
}

/* ── Source Drawer（§B Citation UX: 点击引用 → 全量来源 + 核验状态 + 原典深链） ── */
export function SourceDrawer({ open, citation, lang, onClose }) {
  const zh = lang !== 'en';

  useEffect(() => {
    if (!open) return;
    const onKey = (e) => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [open, onClose]);
  if (!open || !citation) return null;
  const c = citation;
  const link = c.reader_url || c.url || null;
  const rows = [
    [zh ? '作者' : 'Author', (Array.isArray(c.authors) ? c.authors.map(a => a?.name || a).filter(Boolean).join(', ') : c.author) || null],
    [zh ? '著作' : 'Work', c.work || c.book || null],
    [zh ? '章节/页' : 'Chapter/Pages', c.chapter || c.page || null],
    [zh ? '出版信息' : 'Venue', c.container_title || c.venue || null],
    [zh ? '年份' : 'Year', c.publication_year || c.year || null],
    [zh ? 'DOI' : 'DOI', c.doi || null],
  ].filter(([, v]) => v);
  return (
    <div className="o9-drawer-mask" onClick={onClose}>
      <aside className="o9-drawer" role="dialog" aria-modal="true" aria-label={zh ? '引用来源' : 'Citation source'}
        onClick={(e) => e.stopPropagation()}>
        <header className="o9-drawer-head">
          <span className="o9-drawer-cap"><Quote size={13} aria-hidden /> {zh ? '引用来源' : 'Citation source'}</span>
          <button className="o9-drawer-close" onClick={onClose} aria-label="close"><X size={15} /></button>
        </header>
        <div className="o9-drawer-body">
          <div className="o9-drawer-title">{c.title || c.book || c.work || '—'}</div>
          {rows.map(([k, v]) => (
            <div key={k} className="o9-drawer-row"><span className="o9-drawer-k">{k}</span><span>{v}</span></div>
          ))}
          {(c.quote || c.passage || c.abstract_text) && (
            <blockquote className="o9-drawer-quote">
              <Quote size={11} aria-hidden /> {(c.quote || c.passage || c.abstract_text || '').slice(0, 420)}
            </blockquote>
          )}
          <div className="o9-drawer-verify">
            <ShieldCheck size={12} aria-hidden />
            {c.used === false ? (zh ? '检索到但未被本回答引用' : 'Retrieved but not cited by this answer')
              : (zh ? '已核验：本回答实际引用的证据' : 'Verified: actually cited by this answer')}
          </div>
          {(link || citation.book) && (
            <ReaderLink citation={citation} fallback={link} zh={zh} />
          )}
        </div>
      </aside>
    </div>
  );
}
