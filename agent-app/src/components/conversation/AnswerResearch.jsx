import { useState } from 'react';
import { BookOpen, Search, ArrowUpRight, Compass } from 'lucide-react';
import { generalAccessLabel, generalEvidenceLayer, pickUsedEvidence, primaryResearch } from '../../utils/evidence';
import { GeneralReaderLink, DepthControls } from './O9';

export const PRIMARY_PROMPT = {
  zh: '请围绕这段回答的核心问题实际检索原典，选择最相关的1～3段并读取上下文。给出原文、书名与章节，解释原文怎样支持、限制或反驳刚才的观点；找不到合适材料时如实说明。',
  en: 'Search primary texts for the central question in this answer. Read the context of 1–3 relevant passages, quote them with work and chapter, and explain how they support, limit or challenge the answer. Say clearly if no suitable passage is found.',
};

export function AnswerResearch({ message, lang, busy, onSend, onSource }) {
  const zh = lang !== 'en';
  const [expanded, setExpanded] = useState(false);
  const research = primaryResearch(message);
  const cited = pickUsedEvidence(message.citations);
  const other = cited.filter(c => generalEvidenceLayer(c) !== 'primary');
  const used = research.sources.filter(c => c.used !== false);
  const initial = (used.length ? used : research.sources).slice(0, 3);
  const visible = expanded ? research.sources : initial;
  const empty = {
    not_requested: zh ? '本轮未检索原典。可以从刚才的观点出发，查找原文并核对语境。' : 'No primary-text search was made this turn. Find passages and examine their context below.',
    empty: zh ? '本轮检索未找到合适的原典片段，可以换一个概念或线索继续查找。' : 'No suitable primary passage was found. Try another concept or lead.',
    failed: zh ? '本轮原典检索未完成，可以重试。' : 'Primary-text retrieval did not complete. You can retry.',
  }[research.status];
  return <section className="general-research-section" aria-label={zh ? '原典检索' : 'Primary-text research'}>
    <div className="general-section-head"><BookOpen size={15} /><h3>{zh ? '原典检索' : 'Primary-text research'}</h3>
      {!!research.sources.length && <span>{zh ? `${research.total || research.sources.length} 处相关材料` : `${research.total || research.sources.length} passages`}</span>}
    </div>
    {!visible.length && <p className="general-section-note">{empty || (zh ? '暂无可展示的原典片段。' : 'No primary passages to display.')}</p>}
    <div className="general-primary-grid">
      {visible.map((c, i) => <article className="general-primary-card" key={c.evidence_id || `${c.book_id || c.book}:${c.chapter_idx ?? c.chapter}:${i}`}>
        <button className="general-source-title" onClick={() => onSource(c)}>{c.book || c.title}{c.chapter ? ` · ${c.chapter}` : ''}</button>
        <div className="general-source-meta">{c.author && <span>{c.author}</span>}<span>{c.used === false ? (zh ? '相关材料 · 未引用' : 'Related · not cited') : (zh ? '本回答引用' : 'Cited in this answer')}</span>
          {generalAccessLabel(c.access_level, lang) && <span>{generalAccessLabel(c.access_level, lang)}</span>}
        </div>
        {c.excerpt && <blockquote>{c.excerpt}</blockquote>}
        <div className="general-source-actions"><button onClick={() => onSource(c)}>{zh ? '查看片段与出处' : 'Passage and source'}</button><GeneralReaderLink citation={c} zh={zh} /></div>
      </article>)}
    </div>
    {research.sources.length > initial.length && <button className="cw-cite-more" onClick={() => setExpanded(v => !v)}>{expanded ? (zh ? '收起相关材料' : 'Less') : (zh ? `另有 ${research.sources.length - initial.length} 处检索材料` : `${research.sources.length - initial.length} more retrieved passages`)}</button>}
    <button className="general-research-action" disabled={busy} onClick={() => onSend(PRIMARY_PROMPT[zh ? 'zh' : 'en'], message)}><Search size={13} />{research.sources.length ? (zh ? '继续查阅原典' : 'Explore more primary texts') : (zh ? '检索相关原典' : 'Find primary texts')}</button>
    {!!other.length && <div className="general-secondary-sources"><span>{zh ? '补充资料' : 'Additional sources'}</span>
      {other.map((c, i) => <button className="cw-cite-chip" key={c.evidence_id || i} onClick={() => onSource(c)}>{c.title || c.book || c.url}</button>)}
    </div>}
  </section>;
}

const DIRECTIONS = [
  ['检验反例', 'Test a counterexample', '请构造一个满足这段回答原有条件、却可能推翻其核心判断的具体反例，检验原判断是否需要收窄。', 'Construct a concrete counterexample that preserves the conditions in this answer. Test whether its central judgment needs narrowing.'],
  ['比较不同立场', 'Compare perspectives', '请围绕这段回答的核心分歧，比较两种有实质差异的哲学立场，说明各自最强理由与代价；涉及原文时实际查阅来源。', 'Compare two substantively different philosophical positions on the central disagreement in this answer, including their strongest reasons and costs. Consult sources when citing texts.'],
  ['联系具体处境', 'Apply to a situation', '请把这段回答用于一个具体的日常处境，说明改变哪些条件会改变判断，并区分例子与我的实际经历。', 'Apply this answer to a concrete everyday situation and show which changed conditions would change the judgment. Distinguish hypothetical examples from my actual experience.'],
];

export function AnswerExploration({ message, lang, busy, onSend }) {
  const zh = lang !== 'en';
  return <section className="general-exploration-section" aria-label={zh ? '继续探索' : 'Explore further'}>
    <div className="general-section-head"><Compass size={15} /><h3>{zh ? '继续探索' : 'Explore further'}</h3></div>
    {!!message.suggestions?.length && <div className="general-topic-questions">{message.suggestions.map((q, i) => <button key={i} disabled={busy} onClick={() => onSend(q, message)}><ArrowUpRight size={14} /><span>{q}</span></button>)}</div>}
    <div className="general-explore-directions">{DIRECTIONS.map(([label, en, prompt, promptEn]) => <button key={label} disabled={busy} onClick={() => onSend(zh ? prompt : promptEn, message)}>{zh ? label : en}</button>)}</div>
    <DepthControls lang={lang} general kinds={['scholarly']} disabled={busy} onPick={q => onSend(q, message)} />
  </section>;
}
