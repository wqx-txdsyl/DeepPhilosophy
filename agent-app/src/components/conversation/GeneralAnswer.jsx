import { useEffect, useRef, useState } from 'react';
import { Check, ChevronDown, ChevronRight, Copy, Loader2, Square, XCircle } from 'lucide-react';
import { useLang } from '../../utils/i18n';
import { plainText } from '../../data/generalStream';
import { toolShortArgs, toolShortSummary } from '../../data/conversationLogic';
import { pickUsedEvidence } from '../../utils/evidence';
import { getPref } from '../../data/localPrefs';
import { renderMarkdown } from './markdown';
import { DepthControls, SourceDrawer } from './O9';
import { AnswerResearch, AnswerExploration } from './AnswerResearch';

const STATUS = {
  success: ['已完成', 'Complete'], error: ['执行失败', 'Failed'], empty: ['没有找到相关结果', 'No relevant results'],
  blocked: ['未执行', 'Not executed'], reused: ['复用已有结果', 'Reused result'], cancelled: ['已停止', 'Stopped'], running: ['进行中', 'Running'],
};

export function ProviderReasoning({ message }) {
  const { lang, toolLabel } = useLang();
  return <ReasoningTimeline message={message} lang={lang} toolLabel={toolLabel} />;
}

export function ReasoningTimeline({ message, lang = 'zh', toolLabel = name => name }) {
  const zh = lang !== 'en';
  const [open, setOpen] = useState(() => !!message.streaming || !!getPref('toolTraceOpen'));
  const body = useRef(null);
  const follow = useRef(true);
  const events = (message.events || message.tool_events || []).filter(e => ['provider_reasoning', 'thinking_summary', 'tool_start', 'tool', 'tool_cancel', 'tool_note'].includes(e?.t)
    && (e.t !== 'provider_reasoning' || e.source === 'deepseek')
    && (e.tc?.name || e.name) !== 'declare_research_need'
    && !(e.t === 'tool_note' && /^(登记研究需求|Registering research need|正在.*(?:…|\.\.\.)$)/i.test(e.text || '')));
  const calls = events.filter(e => e.t.startsWith('tool') && e.t !== 'tool_note');
  const running = calls.filter(e => e.t === 'tool_start').length;
  const hasReasoning = (message.events || message.tool_events || []).some(e => e.t === 'provider_reasoning');
  const progress = events.reduce((n, e) => n + (e.content?.length || e.text?.length || 0) + 1, 0);
  useEffect(() => {
    if (open && follow.current && body.current) body.current.scrollTop = body.current.scrollHeight;
  }, [open, progress]);
  if (!events.length && !message.streaming) return null;
  const completed = calls.filter(e => e.t === 'tool' && ['success', 'reused'].includes(e.status || 'success')).length;
  const headline = events.length ? (zh ? (hasReasoning ? '思考与工具' : '研究过程') : (hasReasoning ? 'Reasoning and tools' : 'Research'))
    : message.content ? (zh ? '正在写下回答' : 'Writing the answer') : (zh ? '等待模型响应' : 'Waiting for the model');
  return <div className="cw-activity general-activity general-timeline">
    <button className="cw-activity-head" aria-expanded={open} onClick={() => setOpen(v => !v)}>
      {message.streaming && !message.done_received ? <Loader2 size={13} className="cw-spinner" aria-hidden /> : open ? <ChevronDown size={13} /> : <ChevronRight size={13} />}
      <span className="cw-activity-head-text" role="status">{headline}</span>
      {running > 0 ? <span className="general-activity-count">{zh ? `${running} 项执行中` : `${running} running`}</span>
        : completed > 0 && <span className="general-activity-count">{zh ? `${completed} 项工具完成` : `${completed} tools complete`}</span>}
    </button>
    {open && <div className="cw-activity-body general-timeline-body" ref={body} onScroll={event => {
      const el = event.currentTarget;
      follow.current = el.scrollHeight - el.scrollTop - el.clientHeight < 40;
    }}>
      {!events.length && <div className="cw-think-line">{zh ? '收到问题，准备回答。' : 'Question received. Preparing an answer.'}</div>}
      {events.map((event, i) => {
        if (event.t === 'provider_reasoning') return <div className="general-reasoning-text" key={`${event.id}:${i}`}>{event.content}</div>;
        if (event.t === 'thinking_summary' || event.t === 'tool_note') {
          const content = plainText(event.content || event.text);
          return content ? <div className="cw-think-line" key={event.id || `note-${i}`}>{event.t === 'thinking_summary' && <span>{zh ? '研究说明：' : 'Research note: '}</span>}{content}</div> : null;
        }
        const name = event.tc?.name || event.name;
        const args = event.tc?.args || event.args || {};
        const webLabel = name === 'websearch' ? (args.url ? (zh ? '读取网页' : 'Read webpage') : (zh ? '联网查阅' : 'Search web')) : null;
        const scholarlyLabel = { search_scholarship: zh ? '检索学术文献' : 'Search scholarship', get_scholarly_source: zh ? '读取学术资料' : 'Read scholarly source' }[name];
        const reasoningLabel = { analyze_argument: zh ? '论证分析（辅助模型）' : 'Argument analysis (auxiliary model)', paper_review: zh ? '文本评审（辅助模型）' : 'Text review (auxiliary model)' }[name];
        const label = reasoningLabel || webLabel || scholarlyLabel || (toolLabel(name) !== name ? toolLabel(name) : (zh ? '工具调用' : 'Tool call'));
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
    <ProviderReasoning message={m} />
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
    {!!content && !m.streaming && <div className="general-answer-actions">
      <button className="general-copy" onClick={copy} aria-label={zh ? '复制回答' : 'Copy answer'}>{copied ? <Check size={13} /> : <Copy size={13} />}{copied ? (zh ? '已复制' : 'Copied') : (zh ? '复制' : 'Copy')}</button>
      {copyError && <span role="status">{zh ? '复制失败，可选择正文复制。' : 'Copy failed. Select the text to copy it.'}</span>}
      {complete && <DepthControls lang={lang} disabled={busy} onPick={prompt => onSend(prompt, m)} general kinds={['simpler', 'deeper']} />}
    </div>}
    {complete && m.safety !== 'blocked' && <AnswerResearch message={m} lang={lang} busy={busy} onSend={onSend} onSource={setSource} />}
    {complete && m.safety !== 'blocked' && m.suggestions_status !== 'disabled' && <AnswerExploration message={m} lang={lang} busy={busy} onSend={onSend} />}
    <SourceDrawer open={!!source} citation={source} lang={lang} onClose={() => setSource(null)} general />
  </>;
}
