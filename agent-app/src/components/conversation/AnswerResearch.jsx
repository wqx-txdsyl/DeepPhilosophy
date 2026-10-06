import { useState } from 'react';
import { BookOpen, Search, ArrowUpRight, Compass, FileText, ChevronRight, RefreshCw, Loader2 } from 'lucide-react';
import { generalAccessLabel, generalEvidenceLayer, pickUsedEvidence, primaryResearch } from '../../utils/evidence';
import { GeneralReaderLink } from './O9';
import useCompactViewport from '../../utils/useCompactViewport';

export const PRIMARY_PROMPT = {
  zh: '请围绕这段回答的核心问题实际检索原典，选择最相关的1～3段并读取上下文。给出原文、书名与章节，解释原文怎样支持、限制或反驳刚才的观点；找不到合适材料时如实说明。',
  en: 'Search primary texts for the central question in this answer. Read the context of 1–3 relevant passages, quote them with work and chapter, and explain how they support, limit or challenge the answer. Say clearly if no suitable passage is found.',
};

function sourcePublication(citation) {
  if (citation.container_title || citation.venue) return citation.container_title || citation.venue;
  try {
    const url = new URL(citation.url || citation.reader_url);
    return ['http:', 'https:'].includes(url.protocol) ? url.hostname.replace(/^www\./, '') : '';
  } catch { return ''; }
}

export function SupplementarySources({ sources, zh, onSource }) {
  if (!sources.length) return null;
  return <section className="general-secondary-sources" aria-label={zh ? '补充资料' : 'Additional sources'}>
    <div className="general-secondary-head"><h4>{zh ? '补充资料' : 'Additional sources'}</h4><span>{zh ? `${sources.length} 条来源` : `${sources.length} sources`}</span></div>
    <ul className="general-secondary-list">
      {sources.map((c, i) => {
        const title = c.title || c.book || c.url || (zh ? '查看来源' : 'View source');
        const meta = [sourcePublication(c), c.publication_year || c.year].filter(Boolean).join(' · ');
        return <li key={c.evidence_id || `${c.url || c.title}:${i}`}>
          <button type="button" className="general-secondary-link" onClick={() => onSource(c)} title={title}>
            <FileText size={15} className="general-secondary-icon" aria-hidden="true" />
            <span className="general-secondary-copy"><span className="general-secondary-title">{title}</span>
              {meta && <span className="general-secondary-meta">{meta}</span>}
            </span>
            <ChevronRight size={14} className="general-secondary-chevron" aria-hidden="true" />
          </button>
        </li>;
      })}
    </ul>
  </section>;
}

export function AnswerResearch({ message, lang, busy, onSend, onSource }) {
  const zh = lang !== 'en';
  const [expanded, setExpanded] = useState(false);
  const compact = useCompactViewport();
  const research = primaryResearch(message);
  const cited = pickUsedEvidence(message.citations);
  const other = cited.filter(c => generalEvidenceLayer(c) !== 'primary');
  const used = research.sources.filter(c => c.used !== false);
  const initial = (used.length ? used : research.sources).slice(0, compact ? 1 : 3);
  const visible = expanded ? research.sources : initial;
  const quoteChecks = research.quote_checks || [];
  const empty = {
    not_requested: zh ? '本轮未检索原典。可以从刚才的观点出发，查找原文并核对语境。' : 'No primary-text search was made this turn. Find passages and examine their context below.',
    empty: zh ? '本轮检索未找到合适的原典片段，可以换一个概念或线索继续查找。' : 'No suitable primary passage was found. Try another concept or lead.',
    failed: zh ? '本轮原典检索未完成，可以重试。' : 'Primary-text retrieval did not complete. You can retry.',
  }[research.status];
  if (compact && !visible.length && !quoteChecks.length && !other.length) return <details className="general-research-section general-empty-research">
    <summary><BookOpen size={15} /><span>{zh ? '原典检索' : 'Primary texts'}</span><span className="general-section-note">{zh ? '暂无原文片段' : 'No passages'}</span><ChevronRight size={14} /></summary>
    <p className="general-section-note">{empty}</p>
    <button className="general-research-action" disabled={busy} onClick={()=>onSend(PRIMARY_PROMPT[zh ? 'zh' : 'en'],message)}><Search size={13} />{zh ? '检索相关原典' : 'Find primary texts'}</button>
  </details>;
  return <section className="general-research-section" aria-label={zh ? '原典检索' : 'Primary-text research'}>
    <div className="general-section-head"><BookOpen size={15} /><h3>{zh ? '原典检索' : 'Primary-text research'}</h3>
      {!!research.sources.length && <span>{zh ? `${research.total || research.sources.length} 处相关材料` : `${research.total || research.sources.length} passages`}</span>}
    </div>
    {!visible.length && !quoteChecks.length && <p className="general-section-note">{empty || (zh ? '暂无可展示的原典片段。' : 'No primary passages to display.')}</p>}
    {quoteChecks.filter(check => check.found === false).map((check, i) => <div className="general-primary-card" key={`quote-check-${i}`}>
      <strong>{zh ? `《${check.book_title}》：未找到原句匹配` : `${check.book_title}: no quotation match`}</strong>
      <blockquote>{check.quote}</blockquote>
      <p className="general-section-note">{zh ? `已检索本库该版本的 ${check.coverage?.searched_chapters ?? 0} 个文本单元，未以近义句替代。` : `Searched ${check.coverage?.searched_chapters ?? 0} local text units; no similar sentence was substituted.`}
        {check.coverage?.directory_consistent === false && (zh ? ' 当前目录范围不完整，不能排除缺失部分。' : 'The local directory is incomplete.')}</p>
    </div>)}
    <div className="general-primary-grid">
      {visible.map((c, i) => <article className="general-primary-card" key={c.evidence_id || `${c.book_id || c.book}:${c.chapter_idx ?? c.chapter}:${i}`}>
        <button className="general-source-title" onClick={() => onSource(c)}>{c.book || c.title}{c.chapter ? ` · ${c.chapter}` : ''}</button>
        <div className="general-source-meta">{c.author && <span>{c.author}</span>}<span>{c.used === false ? (zh ? '相关材料 · 未引用' : 'Related · not cited') : (zh ? '本回答引用' : 'Cited in this answer')}</span>
          {c.material_role && c.material_role !== 'UNCLASSIFIED' && <span>{zh ? ({COMMENTARY_CANDIDATE:'可能为解读材料',EDITORIAL_CANDIDATE:'可能为译注或导读',PARATEXT_CANDIDATE:'书目附属材料'}[c.material_role] || '来源类型待核') : 'Source role requires review'}</span>}
          {generalAccessLabel(c.access_level, lang) && <span>{generalAccessLabel(c.access_level, lang)}</span>}
        </div>
        {c.excerpt && <blockquote>{c.excerpt}</blockquote>}
        <div className="general-source-actions"><button onClick={() => onSource(c)}>{zh ? '查看片段与出处' : 'Passage and source'}</button><GeneralReaderLink citation={c} zh={zh} /></div>
      </article>)}
    </div>
    {research.sources.length > initial.length && <button className="cw-cite-more" onClick={() => setExpanded(v => !v)}>{expanded ? (zh ? '收起相关材料' : 'Less') : (zh ? `另有 ${research.sources.length - initial.length} 处检索材料` : `${research.sources.length - initial.length} more retrieved passages`)}</button>}
    <button className="general-research-action" disabled={busy} onClick={() => onSend(PRIMARY_PROMPT[zh ? 'zh' : 'en'], message)}><Search size={13} />{research.sources.length ? (zh ? '继续查阅原典' : 'Explore more primary texts') : (zh ? '检索相关原典' : 'Find primary texts')}</button>
    <SupplementarySources sources={other} zh={zh} onSource={onSource} />
  </section>;
}

export function AnswerExploration({ message, lang, busy, onSend, onRegenerate }) {
  const zh = lang !== 'en';
  const questions = (message.suggestions || []).filter(q => typeof q === 'string' && /[?？]$/.test(q.trim()));
  const pending = message.suggestions_status === 'pending';
  return <section className="general-exploration-section" aria-label={zh ? '继续探索' : 'Explore further'}>
    <div className="general-section-head"><Compass size={15} /><h3>{zh ? '继续探索' : 'Explore further'}</h3>
      {onRegenerate && <button type="button" className="general-exploration-refresh" disabled={busy || pending} onClick={onRegenerate} aria-label={zh ? (questions.length ? '重新生成探索问题' : '生成探索问题') : 'Generate new exploration questions'} title={zh ? (questions.length ? '换一组问题' : '生成问题') : 'Generate questions'}>{pending ? <Loader2 size={14} className="cw-spinner" /> : <RefreshCw size={14} />}</button>}
    </div>
    {pending && <p className="general-section-note" role="status">{zh ? '正在围绕本轮讨论生成深入问题…' : 'Generating questions for this discussion…'}</p>}
    {!pending && questions.length > 0 && message.suggestions_status === 'unavailable' && <p className="general-section-note" role="status">{zh ? '本次生成未成功，保留上一组问题。' : 'Generation failed; the previous questions are retained.'}</p>}
    {!!questions.length && <div className="general-topic-questions">{questions.map((q, i) => <button key={i} disabled={busy} onClick={() => onSend(q, message)}><ArrowUpRight size={14} /><span>{q}</span></button>)}</div>}
    {!pending && !questions.length && <p className="general-section-note">{zh ? '暂未生成探索问题，可点击右侧图标重试。' : 'No questions generated yet. Use the icon to retry.'}</p>}
  </section>;
}
