import { useEffect, useRef, useState } from 'react';
import { Check, ChevronDown, ChevronRight, Copy, Loader2, Square, XCircle, Search, TriangleAlert } from 'lucide-react';
import { useLang } from '../../utils/i18n';
import { plainText, inferToolStatus } from '../../data/generalStream';
import { toolShortArgs, toolShortSummary } from '../../data/conversationLogic';
import { pickUsedEvidence } from '../../utils/evidence';
import { renderMarkdown } from './markdown';
import { DepthControls, SourceDrawer } from './O9';
import { AnswerResearch, AnswerExploration } from './AnswerResearch';
import { ToolResult } from './ToolResult';

const STATUS = {
  success: ['已完成', 'Complete'], error: ['执行失败', 'Failed'], empty: ['本次未找到结果', 'No results for this search'],
  partial: ['部分来源失败', 'Some sources failed'],
  blocked: ['未执行', 'Not executed'], reused: ['复用已有结果', 'Reused result'], cancelled: ['已停止', 'Stopped'], running: ['进行中', 'Running'],
};

export function ProviderReasoning({ message }) {
  const { lang, toolLabel } = useLang();
  return <ReasoningTimeline message={message} lang={lang} toolLabel={toolLabel} />;
}

export function ReasoningBlock({ text, active, zh }) {
  const [choice, setChoice] = useState(null);
  const open = choice?.phase === active ? choice.open : active;
  const body = useRef(null);
  const follow = useRef(true);
  useEffect(() => {
    if (open && follow.current && body.current) body.current.scrollTop = body.current.scrollHeight;
  }, [open, text]);
  const summary = text.trim().split('\n').find(line => line.trim()) || '';
  return <section className="general-think-block" data-active={active || undefined}>
    <button className="general-think-toggle" aria-expanded={open} onClick={() => setChoice({ phase: active, open: !open })}>
      {active ? <Loader2 size={13} className="cw-spinner" /> : <Check size={13} />}
      <span>{zh ? (active ? '思考中' : '已思考') : (active ? 'Thinking' : 'Thought')}</span>
      {!open && <span className="general-think-preview">{summary.replaceAll('**', '').slice(0, 90)}</span>}
      {open ? <ChevronDown size={13} /> : <ChevronRight size={13} />}
    </button>
    {open && <div className="general-think-body general-reasoning-text" ref={body} onScroll={event => {
      const el = event.currentTarget;
      follow.current = el.scrollHeight - el.scrollTop - el.clientHeight < 40;
    }}>{text}</div>}
  </section>;
}

export function ReasoningTimeline({ message, lang = 'zh', toolLabel = name => name }) {
  const zh = lang !== 'en';
  const events = (message.events || message.tool_events || []).filter(e => (['provider_reasoning', 'assistant_commentary', 'tool_start', 'tool', 'tool_cancel'].includes(e?.t)
    || (message.runtime_profile === 'bare' && e?.t === 'thinking_summary'))
    && (e.t !== 'provider_reasoning' || e.source === 'deepseek')
    && (e.tc?.name || e.name) !== 'declare_research_need');
  if (!events.length && !message.streaming) return null;
  return <div className="general-process">
    {!events.length && <span className="general-activity-count">{zh ? '等待模型响应' : 'Waiting for model'}</span>}
      {events.map((event, i) => {
        if (event.t === 'assistant_commentary' || event.t === 'thinking_summary') {
          return <div className="general-answer general-interim-answer" key={event.id || `commentary-${i}`}>
            {renderMarkdown(event.content || '', undefined, undefined, key => key, { general: true, citations: message.citations || [] })}
          </div>;
        }
        if (event.t === 'provider_reasoning') {
          const active = !!message.streaming && !message.done_received && !message.content && i === events.length - 1;
          return <ReasoningBlock key={`${event.id}:${i}`} text={event.content} active={active} zh={zh} />;
        }
        const name = event.tc?.name || event.name;
        const args = event.tc?.args || event.args || {};
        const webLabel = name === 'websearch' ? (args.url ? (zh ? '读取网页' : 'Read webpage') : (zh ? '联网查阅' : 'Search web')) : null;
        const scholarlyLabel = { search_scholarship: zh ? '检索学术文献' : 'Search scholarship', get_scholarly_source: zh ? '读取学术资料' : 'Read scholarly source' }[name];
        const reasoningLabel = { review_answer: zh ? '核对回答论证（辅助模型）' : 'Check draft reasoning (auxiliary model)', analyze_argument: zh ? '论证分析（辅助模型）' : 'Argument analysis (auxiliary model)', paper_review: zh ? '文本评审（辅助模型）' : 'Text review (auxiliary model)' }[name];
        const label = (name === 'verify_quote' ? (zh ? '核验原文' : 'Verify quotation') : null) || reasoningLabel || webLabel || scholarlyLabel || (toolLabel(name) !== name ? toolLabel(name) : (zh ? '工具调用' : 'Tool call'));
        let query = args.quote || toolShortArgs(args);
        if (args.url) {
          try { query = new URL(args.url).hostname + (args.focus ? ` · ${args.focus}` : ''); }
          catch { query = args.url; }
        }
        const status = event.t === 'tool_start' ? 'running' : event.t === 'tool_cancel' ? 'cancelled'
          : event.status && event.status !== 'success' ? event.status : inferToolStatus(event.tc?.result_summary);
        const [statusZh, statusEn] = STATUS[status] || STATUS.success;
        const summary = message.runtime_profile === 'bare' ? event.tc?.result_summary || event.reason
          : toolShortSummary(event.tc) || toolShortArgs(event.tc?.args || event.args) || event.reason;
        return <details className={`general-tool general-tool-${status}`} key={event.call_id || `call-${i}`}>
          <summary>
            {status === 'running' ? <Loader2 size={12} className="cw-spinner" /> : ['success', 'reused'].includes(status) ? <Check size={12} /> : status === 'empty' ? <Search size={12} /> : status === 'partial' ? <TriangleAlert size={12} /> : <XCircle size={12} />}
            <span>{label}</span>
            <span className="general-tool-query">{plainText(query)}</span>
            <span className="general-tool-status">{zh ? statusZh : statusEn}</span>
            <ChevronDown size={12} />
          </summary>
          <ToolResult name={name} raw={event.tc?.result_summary || summary || (zh ? statusZh : statusEn)} zh={zh} />
        </details>;
      })}
  </div>;
}

export default function GeneralAnswer({ message: m, onSend, onDrawioEdit, busy, question, onRegenerateExploration }) {
  const { t, lang } = useLang();
  const zh = lang !== 'en';
  const [source, setSource] = useState(null);
  const [copied, setCopied] = useState(false);
  const [copyError, setCopyError] = useState(false);
  const citations = pickUsedEvidence(m.citations);
  const content = m.runtime_profile === 'bare' ? String(m.content || '')
    : plainText(m.content).replace(/<tool_calls>[\s\S]*?<\/tool_calls>/g, '').replace(/<invoke name="[^"]+">[\s\S]*?<\/invoke>/g, '');
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
    {complete && m.safety !== 'blocked' && <AnswerResearch message={m} lang={lang} busy={busy} onSend={onSend} onSource={setSource} />}
    {complete && m.safety !== 'blocked' && m.suggestions_status !== 'disabled' && <AnswerExploration message={m} lang={lang} busy={busy} onSend={onSend} onRegenerate={onRegenerateExploration ? () => onRegenerateExploration(m, question) : undefined} />}
    {!!content && !m.streaming && <div className="general-answer-actions" role="group" aria-label={zh ? '回答操作' : 'Answer actions'}>
      <button type="button" className="general-action-icon" onClick={copy} aria-label={zh ? '复制回答' : 'Copy answer'}>{copied ? <Check size={16} /> : <Copy size={16} />}<span className="general-action-tooltip">{copied ? (zh ? '已复制' : 'Copied') : (zh ? '复制' : 'Copy')}</span></button>
      {complete && m.safety !== 'blocked' && <DepthControls lang={lang} disabled={busy} onPick={prompt => onSend(prompt, m)} general kinds={['simpler', 'deeper', 'scholarly']} iconOnly />}
      {copyError && <span role="status">{zh ? '复制失败，可选择正文复制。' : 'Copy failed. Select the text to copy it.'}</span>}
    </div>}
    <SourceDrawer open={!!source} citation={source} lang={lang} onClose={() => setSource(null)} general />
  </>;
}
