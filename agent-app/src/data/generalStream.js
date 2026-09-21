/** Main-model reasoning, public research and answer have separate event channels. */
export const plainText = value => String(value ?? '').replace(/[0-9#*]\uFE0F?\u20E3|[\p{Extended_Pictographic}\p{Regional_Indicator}\p{Emoji_Modifier}\uFE0F\u200D]/gu, '');
const callId = e => e.call_id || e.tool_call_id || e.id;
const suggestions = value => Array.isArray(value)
  ? [...new Set(value.filter(v => typeof v === 'string').map(v => plainText(v).trim()).filter(Boolean))].slice(0, 4) : [];

export function createGeneralStream() {
  return { content: '', events: [], citations: [], evidence: null, suggestions: [], streaming: true, status: '', stream_state: 'streaming' };
}

export const ownsGeneralRequest = (streams, conversationId, messageId) => streams.get(conversationId)?.messageId === messageId;

/** Optional follow-up metadata must not keep the next user turn waiting. */
export function releaseGeneralAnswer(streams, conversationId, messageId) {
  if (!ownsGeneralRequest(streams, conversationId, messageId)) return false;
  streams.get(conversationId).answerDone = true;
  return true;
}

export function prepareGeneralRequest(streams, conversationId) {
  const previous = streams.get(conversationId);
  if (!previous) return true;
  if (!previous.answerDone) return false;
  previous.controller.abort();
  if (streams.get(conversationId) === previous) streams.delete(conversationId);
  return true;
}

export function reduceGeneralEvent(state, evt) {
  if (!evt || typeof evt.type !== 'string') return state;
  const text = plainText(evt.content);
  if (evt.type === 'provider_reasoning_delta') {
    if (state.done_received || evt.source !== 'deepseek' || !evt.id || typeof evt.content !== 'string' || !evt.content) return state;
    const events = [...state.events];
    const last = events.length - 1;
    const i = events[last]?.t === 'provider_reasoning' && events[last]?.id === evt.id ? last : -1;
    // Preserve exact text and arrival order. A resumed ID after a tool is a
    // new segment, never appended above the intervening tool in the timeline.
    if (i < 0) events.push({ t: 'provider_reasoning', id: evt.id, source: evt.source, content: evt.content });
    else events[i] = { ...events[i], content: events[i].content + evt.content };
    return { ...state, events };
  }
  if (evt.type === 'token') return state.done_received ? state : { ...state, content: state.content + text };
  if (evt.type === 'answer_retract') {
    // Only retract a matching suffix. An unrelated/duplicate event must not erase a valid answer.
    return !state.done_received && text && state.content.endsWith(text) ? { ...state, content: state.content.slice(0, -text.length) } : state;
  }
  if (evt.type === 'status') return { ...state, status: text };
  if (evt.type === 'thinking_summary') {
    const id = evt.id || `research-${state.events.length}`;
    const line = { t: 'thinking_summary', id, phase: evt.phase, content: text };
    const i = state.events.findIndex(e => e.t === line.t && e.id === id);
    const events = [...state.events];
    if (i < 0) events.push(line); else events[i] = line;
    return { ...state, events };
  }
  if (evt.type === 'thinking_summary_delta') {
    const events = [...state.events];
    let i = -1;
    for (let j = events.length - 1; j >= 0; j--) {
      if (events[j].t === 'thinking_summary' && (!evt.id || evt.id === events[j].id)) { i = j; break; }
    }
    if (i < 0) events.push({ t: 'thinking_summary', id: evt.id || `research-${events.length}`, phase: evt.phase, content: text });
    else events[i] = { ...events[i], content: events[i].content + text };
    return { ...state, events };
  }
  if (evt.type === 'tool_note') return { ...state, events: [...state.events, { t: 'tool_note', text }] };
  if (['tool_start', 'tool', 'tool_cancel'].includes(evt.type)) {
    const events = [...state.events];
    const id = callId(evt);
    const i = !id && evt.type === 'tool_start' ? -1 : events.findIndex(e => id ? e.call_id === id : e.t === 'tool_start' && e.name === evt.name);
    const resolvedId = id || (i >= 0 && events[i].call_id) || `legacy-call-${events.length}`;
    const entry = evt.type === 'tool_start'
      ? { t: 'tool_start', call_id: resolvedId, name: evt.name, args: evt.args, status: 'running' }
      : evt.type === 'tool_cancel'
        ? { t: 'tool_cancel', call_id: resolvedId, name: evt.name, status: evt.status || 'cancelled', reason: plainText(evt.reason || '') }
        : { t: 'tool', call_id: resolvedId, status: evt.status || inferToolStatus(evt.result), tc: { name: evt.name, args: evt.args, result_summary: typeof (evt.summary || evt.result) === 'string' ? plainText(evt.summary || evt.result) : JSON.stringify(evt.result ?? '') } };
    // Duplicate or late start must not resurrect a completed call.
    if (i >= 0 && evt.type === 'tool_start' && events[i].t !== 'tool_start') return state;
    if (i >= 0) events[i] = entry; else events.push(entry);
    return { ...state, events };
  }
  if (evt.type === 'done') return {
    ...state, done_received: evt.complete !== false, safety: evt.safety,
    ...(evt.complete !== false ? { streaming: false, stream_state: 'complete' } : {}),
    ...(typeof evt.content === 'string' ? { content: plainText(evt.content) } : {}),
    ...(evt.safety === 'blocked' ? { content: plainText(evt.safety_reply) } : {}),
    citations: Array.isArray(evt.citations) ? evt.citations : [], evidence: evt.evidence || null,
    suggestions: suggestions(evt.suggestions), reasoning_summary: evt.reasoning_summary || null,
    suggestions_status: evt.suggestions_status || (evt.suggestions?.length ? 'ready' : 'unavailable'),
  };
  if (evt.type === 'suggestions') return { ...state, suggestions: suggestions(evt.suggestions), suggestions_status: evt.status || (evt.suggestions?.length ? 'ready' : 'unavailable') };
  if (evt.type === 'reasoning_summary') return { ...state, reasoning_summary: text };
  if (evt.type === 'error') return { ...state, error: text || '请求未完成', stream_state: 'error' };
  // Legacy thought/thought_stream do not identify a verified provider channel.
  return state;
}

export function inferToolStatus(result) {
  try {
    const data = typeof result === 'string' ? JSON.parse(result) : result;
    if (data?.error || data?.status === 'error') return 'error';
    if (data?.status === 'blocked' || data?.blocked) return 'blocked';
    if (Array.isArray(data) && data.length === 0) return 'empty';
    if (data && ['results', 'items', 'matches'].some(k => Array.isArray(data[k]) && !data[k].length)) return 'empty';
  } catch { /* Historic textual tool summaries. */ }
  return /^(?:错误|失败|error\b|failed\b)/i.test(String(result || '')) ? 'error' : 'success';
}

export function finishGeneralStream(state, { aborted = false, error = '', duration = 0 } = {}) {
  const failure = state.error || (!state.done_received ? error || (!aborted ? '连接已中断，回答可能不完整。' : '') : '');
  const stream_state = aborted && !state.done_received ? 'stopped' : failure ? 'error' : 'complete';
  return { ...state, streaming: false, status: '', stream_state, error: failure,
    suggestions_status: state.suggestions_status === 'pending' ? 'unavailable' : state.suggestions_status,
    duration_seconds: Math.max(1, Math.round(duration)),
    suggestions: stream_state === 'complete' ? state.suggestions : [],
    events: state.events.map(e => e.t === 'tool_start'
      ? { ...e, t: 'tool_cancel', status: 'cancelled', reason: aborted ? '已停止' : '未收到执行结果' } : e),
  };
}

/** SSE parser supports UTF-8 split chunks, LF/CRLF, comments, multi-line data and EOF. */
export async function readEventStream(response, onEvent) {
  if (!response.ok) {
    let detail = '';
    try { const data = await response.json(); detail = data.error || data.detail || ''; } catch { /* non-JSON gateway error */ }
    throw new Error(typeof detail === 'string' && detail ? detail : `请求失败（HTTP ${response.status}）`);
  }
  if (!response.body || !response.headers.get('content-type')?.includes('text/event-stream')) throw new Error('服务未返回可读取的流式回答。');
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  const dispatch = raw => {
    const data = raw.split(/\r?\n/).filter(line => line.startsWith('data:')).map(line => line.slice(5).replace(/^ /, '')).join('\n');
    if (!data || data === '[DONE]') return;
    let evt;
    try { evt = JSON.parse(data); } catch { throw new Error('回答数据损坏，请重试。'); }
    onEvent(evt);
  };
  try {
    while (true) {
      const { value, done } = await reader.read();
      buffer += done ? decoder.decode() : decoder.decode(value, { stream: true });
      let match;
      while ((match = /\r?\n\r?\n/.exec(buffer))) {
        dispatch(buffer.slice(0, match.index));
        buffer = buffer.slice(match.index + match[0].length);
      }
      if (done) { if (buffer.trim()) dispatch(buffer); break; }
    }
  } finally { await reader.cancel().catch(() => {}); reader.releaseLock(); }
}

const FOLLOWUP_OPEN = '请围绕下列指定回答继续讨论。\n<general_followup_context>\n';
const FOLLOWUP_CLOSE = '\n</general_followup_context>';

export function makeFollowupContext(text, source, messages = []) {
  if (!source?.message_id) return text;
  const i = messages.findIndex(m => m.message_id === source.message_id);
  const question = messages.slice(0, Math.max(0, i)).reverse().find(m => m.role === 'user');
  let root = question?.context_content || question?.content || '';
  // Only unwrap our complete envelope. An attachment or malformed envelope stays ordinary text.
  if (root.startsWith(FOLLOWUP_OPEN) && root.endsWith(FOLLOWUP_CLOSE)) {
    try {
      const prior = JSON.parse(root.slice(FOLLOWUP_OPEN.length, -FOLLOWUP_CLOSE.length));
      if (prior && Object.keys(prior).length === 4 && ['原问题与附件', '指定回答对应问题', '指定回答', '本次追问'].every(k => typeof prior[k] === 'string')) root = prior['原问题与附件'];
    } catch { /* Preserve the original content when it is not our saved context. */ }
  }
  // Keep the root attachment once and only the latest selected answer (14k chars), never prior wrappers.
  return FOLLOWUP_OPEN + JSON.stringify({ '原问题与附件': root, '指定回答对应问题': question?.content || '',
    '指定回答': String(source.content || '').slice(0, 14000), '本次追问': text }) + FOLLOWUP_CLOSE;
}

export function prepareGeneralTurn(text, source, messages, hasAttachments = false) {
  const message = makeFollowupContext(text, source, messages);
  return { message, ...(hasAttachments || source?.message_id ? { context_content: message } : {}) };
}
