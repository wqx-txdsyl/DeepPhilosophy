import { useEffect, useRef, useState } from 'react';
import { ArrowDown, Check, ChevronDown, ChevronRight, Copy, Loader2, Search, Square, XCircle } from 'lucide-react';
import { useLang } from '../../utils/i18n';
import { plainText } from '../../data/generalStream';
import { toolShortArgs, toolShortSummary } from '../../data/conversationLogic';
import { pickUsedEvidence, generalEvidenceLayer } from '../../utils/evidence';
import { getPref } from '../../data/localPrefs';
import { renderMarkdown } from './markdown';
import { DepthControls, SourceDrawer, layerLabel } from './O9';

const STATUS = {
  success: ['已完成', 'Complete'], error: ['执行失败', 'Failed'], empty: ['没有找到相关结果', 'No relevant results'],
  blocked: ['未执行', 'Not executed'], reused: ['复用已有结果', 'Reused result'], cancelled: ['已停止', 'Stopped'], running: ['进行中', 'Running'],
};

function ResearchActivity({ message }) {
  const { lang, toolLabel } = useLang();
  const zh = lang !== 'en';
  const [open, setOpen] = useState(() => !!message.streaming || !!getPref('toolTraceOpen'));
  const answered = useRef(!!message.content);
  useEffect(() => {
    if (message.content && !answered.current) setOpen(false);
    answered.current = !!message.content;
  }, [message.content]);
  const events = (message.events || message.tool_events || []).filter(e => ['thinking_summary', 'tool_start', 'tool', 'tool_cancel', 'tool_note'].includes(e?.t)
    && (e.tc?.name || e.name) !== 'declare_research_need'
    && !(e.t === 'tool_note' && /^(登记研究需求|Registering research need|正在.*(?:…|\.\.\.)$)/i.test(e.text || '')));
  const calls = events.filter(e => e.t.startsWith('tool') && e.t !== 'tool_note');
  const running = calls.filter(e => e.t === 'tool_start').length;
  if (!message.streaming && !events.length) return null;
  const completed = calls.filter(e => e.t === 'tool' && ['success', 'reused'].includes(e.status || 'success')).length;
  const phase = events.filter(e => e.t === 'thinking_summary').at(-1)?.phase;
  const phaseLabel = {
    analysis: zh ? '正在辨析问题' : 'Examining the question',
    evidence: zh ? '正在查阅资料' : 'Consulting sources',
    synthesis: zh ? '正在组织回答' : 'Developing the answer',
    UNDERSTANDING: zh ? '正在辨析问题' : 'Examining the question',
    PRIMARY_SEARCH: zh ? '正在查找原典' : 'Searching primary texts',
    SOURCE_VERIFY: zh ? '正在核对出处' : 'Checking sources',
    SCHOLARLY_RESEARCH: zh ? '正在查阅学术研究' : 'Consulting scholarship',
    ARGUMENT_SYNTHESIS: zh ? '正在组织回答' : 'Developing the answer',
  }[phase];
  const headline = message.done_received ? (zh ? '回答已完成' : 'Answer complete') : running > 1 ? (zh ? `${running} 项查阅并行进行` : `${running} lookups running in parallel`)
    : message.streaming ? (message.content ? (zh ? '正在写下回答' : 'Writing the answer') : phaseLabel || plainText(message.status) || (zh ? '正在梳理问题' : 'Examining the question'))
      : zh ? '研究过程' : 'Research activity';
  return <div className="cw-activity general-activity">
    <button className="cw-activity-head" aria-expanded={open} onClick={() => setOpen(v => !v)}>
      {message.streaming && !message.done_received ? <Loader2 size={13} className="cw-spinner" aria-hidden /> : open ? <ChevronDown size={13} /> : <ChevronRight size={13} />}
      <span className="cw-activity-head-text" role="status">{headline}</span>
      {!message.streaming && completed > 0 && <span className="general-activity-count">{zh ? `${completed} 项查阅完成` : `${completed} lookups complete`}</span>}
    </button>
    {open && <div className="cw-activity-body">
      {!events.length && <div className="cw-think-line">{zh ? '收到问题，准备回答。' : 'Question received. Preparing an answer.'}</div>}
      {events.map((event, i) => {
        if (event.t === 'thinking_summary' || event.t === 'tool_note') {
          const content = plainText(event.content || event.text);
          return content ? <div className="cw-think-line" key={event.id || `note-${i}`}>{content}</div> : null;
        }
        const name = event.tc?.name || event.name;
        const args = event.tc?.args || event.args || {};
        const webLabel = name === 'websearch' ? (args.url ? (zh ? '读取网页' : 'Read webpage') : (zh ? '联网查阅' : 'Search web')) : null;
        const scholarlyLabel = { search_scholarship: zh ? '检索学术文献' : 'Search scholarship', get_scholarly_source: zh ? '读取学术资料' : 'Read scholarly source' }[name];
        const label = webLabel || scholarlyLabel || (toolLabel(name) !== name ? toolLabel(name) : (zh ? '查阅资料' : 'Consult source'));
        let query = toolShortArgs(args);
        if (args.url) {
          try { query = new URL(args.url).hostname + (args.focus ? ` · ${args.focus}` : ''); }
          catch { query = args.url; }
        }
        const status = event.t === 'tool_start' ? 'running' : event.status || (event.t === 'tool_cancel' ? 'cancelled' : 'success');
        const [statusZh, statusEn] = STATUS[status] || STATUS.success;
        const summary = toolShortSummary(event.tc) || toolShortArgs(event.tc?.args || event.args) || event.reason;
        return <details className={`general-tool general-tool-${status}`} key={event.call_id || `call-${i}`}>
          <summary>
            {status === 'running' ? <Loader2 size={12} className="cw-spinner" /> : ['success', 'reused'].includes(status) ? <Check size={12} /> : <XCircle size={12} />}
            <span>{label}</span>
            <span className="general-tool-query">{plainText(query)}</span>
            <span className="general-tool-status">{zh ? statusZh : statusEn}</span>
            <ChevronDown size={12} />
          </summary>
          <div>{plainText(summary) || (zh ? statusZh : statusEn)}</div>
        </details>;
      })}
    </div>}
  </div>;
}

export default function GeneralAnswer({ message: m, onSend, onDrawioEdit, busy }) {
  const { t, lang } = useLang();
  const zh = lang !== 'en';
  const [source, setSource] = useState(null);
  const [expanded, setExpanded] = useState(false);
  const [copied, setCopied] = useState(false);
  const [copyError, setCopyError] = useState(false);
  const citations = pickUsedEvidence(m.citations);
  const content = plainText(m.content).replace(/<tool_calls>[\s\S]*?<\/tool_calls>/g, '').replace(/<invoke name="[^"]+">[\s\S]*?<\/invoke>/g, '');
  const interrupted = ['stopped', 'error', 'interrupted'].includes(m.stream_state);
  const complete = !m.streaming && !!content && !interrupted;
  const copy = async () => {
    try { await navigator.clipboard.writeText(content); setCopied(true); setCopyError(false); }
    catch { setCopyError(true); }
  };
  useEffect(() => { if (!copied) return; const timer = setTimeout(() => setCopied(false), 1800); return () => clearTimeout(timer); }, [copied]);
  return <>
    <ResearchActivity message={m} />
    <div className="general-answer" aria-busy={!!m.streaming}>
      {renderMarkdown(content, code => onDrawioEdit(m.message_id, code), m.drawioXml, key => plainText(t(key)), {
        citations, onCitation: setSource, streaming: !!m.streaming, general: true,
      })}
      {m.streaming && !m.done_received && !!content && <span className="cw-stream-cursor" aria-hidden />}
    </div>
    {interrupted && <div className="general-stream-notice" role="status">
      {m.stream_state === 'stopped' ? <Square size={12} /> : <XCircle size={13} />}
      <span>{m.error || (m.stream_state === 'stopped' ? (zh ? '已停止，已生成的内容保留在此。' : 'Stopped. The answer so far has been kept.') : (zh ? '上次回答未完成，已保留收到的内容。' : 'The previous answer was interrupted. Received text was saved.'))}</span>
      <button disabled={busy} onClick={() => onSend(zh ? '请继续完成刚才未完成的回答；如果存在错误，请先修正。' : 'Please complete this interrupted answer, correcting any errors first.', m)}>{zh ? '继续回答' : 'Continue'}</button>
    </div>}
    {!!citations.length && getPref('showCitations') && <div className="cw-evidence general-sources">
      <div className="cw-evidence-cap"><Search size={12} /> {zh ? '引用来源' : 'Sources'} · {citations.length}</div>
      {(expanded ? citations : citations.slice(0, 5)).map((citation, index) => <button
        key={citation.evidence_id || `${index}-${citation.title || citation.book}`} className="cw-cite-chip o9-cite-numbered"
        onClick={() => setSource(citation)} aria-label={`${zh ? '查看来源' : 'Open source'} ${index + 1}: ${plainText(citation.title || citation.book)}`}>
        <sup className="o9-cite-n">[{index + 1}]</sup>
        <span className="cw-cite-chip-title">{plainText(citation.title || (citation.book ? `${citation.book}${citation.chapter ? ` · ${citation.chapter}` : ''}` : citation.work || citation.url || (zh ? '来源' : 'Source')))}</span>
        <span className="general-source-kind">{layerLabel(generalEvidenceLayer(citation), lang)}</span>
      </button>)}
      {citations.length > 5 && <button className="cw-cite-more" onClick={() => setExpanded(v => !v)}>{expanded ? (zh ? '收起' : 'Less') : (zh ? `还有 ${citations.length - 5} 项` : `${citations.length - 5} more`)}</button>}
    </div>}
    {!!content && !m.streaming && <div className="general-answer-actions">
      <button className="general-copy" onClick={copy} aria-label={zh ? '复制回答' : 'Copy answer'}>{copied ? <Check size={13} /> : <Copy size={13} />}{copied ? (zh ? '已复制' : 'Copied') : (zh ? '复制' : 'Copy')}</button>
      {copyError && <span role="status">{zh ? '复制失败，可选择正文复制。' : 'Copy failed. Select the text to copy it.'}</span>}
      {complete && <DepthControls lang={lang} disabled={busy} onPick={prompt => onSend(prompt, m)} general />}
    </div>}
    {complete && !!m.suggestions?.length && <div className="cw-followups">
      <div className="cw-followups-cap">{zh ? '继续探索' : 'Explore further'}</div>
      {m.suggestions.map((question, i) => <button key={i} className="cw-followup-chip" disabled={busy} onClick={() => onSend(question, m)}><ArrowDown size={12} aria-hidden />{plainText(question)}</button>)}
    </div>}
    <SourceDrawer open={!!source} citation={source} lang={lang} onClose={() => setSource(null)} general />
  </>;
}
