import assert from 'node:assert/strict';
import { createGeneralStream, reduceGeneralEvent, finishGeneralStream, readEventStream, makeFollowupContext, prepareGeneralTurn, plainText, ownsGeneralRequest, releaseGeneralAnswer, prepareGeneralRequest } from '../src/data/generalStream.js';
import { LocalConversationStore } from '../src/data/conversationStore.js';
import { normalizeMessage, toPersistedMessage } from '../src/data/conversationLogic.js';

let passed = 0;
async function test(name, fn) { await fn(); passed++; console.log(`  ✓ ${name}`); }
const reduce = events => events.reduce(reduceGeneralEvent, createGeneralStream());
const sseResponse = chunks => new Response(new ReadableStream({ start(controller) { chunks.forEach(chunk => controller.enqueue(chunk)); controller.close(); } }), { headers: { 'content-type': 'text/event-stream; charset=utf-8' } });
const bytes = text => new TextEncoder().encode(text);

await test('same-name parallel tools resolve independently and out of order', () => {
  let state = reduce([
    { type: 'tool_start', name: 'search_books', call_id: 'a', args: { query: '康德' } },
    { type: 'tool_start', name: 'search_books', call_id: 'b', args: { query: '休谟' } },
    { type: 'tool', name: 'search_books', call_id: 'b', status: 'empty', result: [] },
  ]);
  assert.equal(state.events[0].t, 'tool_start');
  assert.equal(state.events[1].status, 'empty');
  state = reduceGeneralEvent(state, { type: 'tool', name: 'search_books', call_id: 'a', status: 'success', summary: '找到原典', result: { data: 'large raw' } });
  assert.equal(state.events.length, 2);
  assert.equal(state.events[0].tc.result_summary, '找到原典');
  state = reduceGeneralEvent(state, { type: 'tool_start', name: 'search_books', call_id: 'a' });
  assert.equal(state.events[0].t, 'tool');
});
await test('legacy calls use FIFO and completion without a start remains visible', () => {
  const state = reduce([{ type: 'tool_start', name: 'search_books' }, { type: 'tool_start', name: 'search_books' }, { type: 'tool', name: 'search_books', result: 'found' }, { type: 'tool', name: 'get_chapter', result: 'read' }]);
  assert.deepEqual(state.events.map(e => e.t), ['tool', 'tool_start', 'tool']);
  assert.equal(new Set(state.events.map(e => e.call_id)).size, 3);
});
await test('public summary IDs route interleaved deltas; private reasoning is not stored', () => {
  const state = reduce([{ type: 'thinking_summary', id: 'a', content: '先' }, { type: 'thinking_summary', id: 'b', content: '再' }, { type: 'thinking_summary_delta', id: 'a', content: '澄清' }, { type: 'thought_stream', content: 'private scratchpad' }]);
  assert.deepEqual(state.events.map(e => e.content), ['先澄清', '再']);
  assert.ok(!JSON.stringify(state).includes('private'));
});
await test('authoritative done.content repairs missing final tokens', () => {
  const state = finishGeneralStream(reduce([{ type: 'token', content: '前半' }, { type: 'done', complete: true, content: '前半与完整结尾', citations: [{ book: '论语' }] }]));
  assert.equal(state.content, '前半与完整结尾');
  assert.equal(state.stream_state, 'complete');
  assert.equal(state.citations.length, 1);
  assert.equal(reduceGeneralEvent(state, { type: 'token', content: 'late stale token' }).content, state.content);
});
await test('provider reasoning preserves exact deltas, separate rounds and interrupted history', () => {
  let state = reduce([
    { type: 'provider_reasoning_delta', source: 'deepseek', id: 'r1', content: '先思考\n' },
    { type: 'tool_start', name: 'analyze_argument', call_id: 'tool1' },
    { type: 'provider_reasoning_delta', source: 'deepseek', id: 'r2', content: '第二轮' },
    { type: 'provider_reasoning_delta', source: 'deepseek', id: 'r1', content: '  保留空格 🧠 <script>' },
  ]);
  assert.equal(state.content, '');
  assert.deepEqual(state.events.filter(e => e.t === 'provider_reasoning').map(e => e.content), ['先思考\n  保留空格 🧠 <script>', '第二轮']);
  const stopped = finishGeneralStream(state, { aborted: true });
  const persisted = toPersistedMessage({ ...stopped, role: 'assistant', agent_id: 'general' });
  assert.deepEqual(persisted.tool_events.filter(e => e.t === 'provider_reasoning'), state.events.filter(e => e.t === 'provider_reasoning'));
  assert.equal(stopped.events[1].status, 'cancelled');
  state = reduceGeneralEvent(state, { type: 'done', content: '答案', complete: true });
  assert.equal(reduceGeneralEvent(state, { type: 'provider_reasoning_delta', source: 'deepseek', id: 'r1', content: 'late' }), state);
  assert.equal(reduceGeneralEvent(createGeneralStream(), { type: 'provider_reasoning_delta', source: 'unknown', id: 'r1', content: 'untrusted' }).events.length, 0);
});
await test('stop, partial EOF and explicit failure retain answer and distinguish unfinished calls', () => {
  const state = reduce([{ type: 'token', content: '已收到正文' }, { type: 'tool_start', name: 'websearch', call_id: 'a' }]);
  const stopped = finishGeneralStream(state, { aborted: true, duration: 3.4 });
  assert.equal(stopped.content, '已收到正文'); assert.equal(stopped.stream_state, 'stopped');
  assert.equal(stopped.events[0].status, 'cancelled'); assert.equal(stopped.duration_seconds, 3);
  assert.equal(finishGeneralStream(state).stream_state, 'error');
  assert.equal(finishGeneralStream(reduceGeneralEvent(state, { type: 'error', content: '限流' })).error, '限流');
});
await test('done.complete=false is incomplete; safety replacement overrides pending text', () => {
  assert.equal(finishGeneralStream(reduce([{ type: 'done', complete: false }])).stream_state, 'error');
  const state = reduce([{ type: 'token', content: '撤销的内容' }, { type: 'done', content: 'final', safety: 'blocked', safety_reply: '替代答复' }]);
  assert.equal(state.content, '替代答复');
});
await test('stopping optional metadata after a confirmed done keeps a complete answer', () => {
  const state = reduce([{ type: 'done', complete: true, content: '完成回答' }]);
  assert.equal(finishGeneralStream(state, { aborted: true }).stream_state, 'complete');
  assert.equal(finishGeneralStream(state, { error: 'metadata connection closed' }).stream_state, 'complete');
});
await test('done unlocks the next turn; late old suggestions/finalize cannot affect a new request', () => {
  const oldController = new AbortController();
  const currentController = new AbortController();
  const streams = new Map([['conversation', { messageId: 'old', controller: oldController }]]);
  let old = reduce([{ type: 'token', content: '旧回答' }]);
  assert.equal(prepareGeneralRequest(streams, 'conversation'), false, 'an unfinished answer keeps its lock');
  old = reduceGeneralEvent(old, { type: 'done', content: '完整旧回答', complete: true });
  assert.equal(old.streaming, false);
  assert.equal(releaseGeneralAnswer(streams, 'conversation', 'old'), true);
  // Optional metadata can still update the old answer before the user sends.
  if (ownsGeneralRequest(streams, 'conversation', 'old')) old = reduceGeneralEvent(old, { type: 'suggestions', suggestions: ['旧回答的追问？'] });
  assert.deepEqual(old.suggestions, ['旧回答的追问？']);
  assert.equal(prepareGeneralRequest(streams, 'conversation'), true);
  assert.equal(oldController.signal.aborted, true);
  streams.set('conversation', { messageId: 'current', controller: currentController });
  const current = reduce([{ type: 'token', content: '新回答开始' }]);
  if (ownsGeneralRequest(streams, 'conversation', 'old')) old = reduceGeneralEvent(old, { type: 'suggestions', suggestions: ['迟到建议'] });
  assert.deepEqual(old.suggestions, ['旧回答的追问？']);
  assert.equal(releaseGeneralAnswer(streams, 'conversation', 'old'), false, 'old finalization cannot unlock current answer');
  assert.equal(prepareGeneralRequest(streams, 'conversation'), false);
  assert.equal(current.content, '新回答开始'); assert.equal(currentController.signal.aborted, false);
});
await test('retraction only removes a matching answer suffix', () => {
  let state = reduce([{ type: 'token', content: '保留撤回' }, { type: 'answer_retract', content: '撤回' }]);
  assert.equal(state.content, '保留');
  state = reduceGeneralEvent(state, { type: 'answer_retract', content: 'wrong text' });
  assert.equal(state.content, '保留');
});
await test('UTF-8 bytes, CRLF boundaries, SSE comments and EOF data survive arbitrary chunks', async () => {
  const wire = ': keepalive\r\n\r\ndata:{"type":"token","content":"哲学"}\r\n\r\ndata: {"type":"done",\n' + 'data: "content":"哲学全文"}';
  const allBytes = bytes(wire);
  const events = [];
  await readEventStream(sseResponse([...allBytes].map(b => new Uint8Array([b]))), event => events.push(event));
  assert.deepEqual(events, [{ type: 'token', content: '哲学' }, { type: 'done', content: '哲学全文' }]);
});
await test('malformed data, HTTP errors and non-SSE responses do not look like success', async () => {
  await assert.rejects(readEventStream(sseResponse([bytes('data: {broken}\n\n')]), () => {}), /数据损坏/);
  await assert.rejects(readEventStream(new Response('{"detail":"rate limit"}', { status: 429 }), () => {}), /rate limit/);
  await assert.rejects(readEventStream(new Response('<html>gateway</html>'), () => {}), /流式/);
});
await test('tool outcomes do not mislabel blocked and empty results as success', () => {
  const state = reduce([{ type: 'tool', name: 'a', result: '{"error":"timeout"}' }, { type: 'tool', name: 'b', result: '{"results":[]}' }, { type: 'tool', name: 'c', status: 'blocked' }, { type: 'tool', name: 'd', status: 'reused' }]);
  assert.deepEqual(state.events.map(e => e.status), ['error', 'empty', 'blocked', 'reused']);
});
await test('no fabricated followups; explicit empty suggestions clears prior metadata', () => {
  const state = reduce([{ type: 'done', suggestions: ['进一步？', '进一步？'] }, { type: 'suggestions', suggestions: [] }]);
  assert.deepEqual(state.suggestions, []);
  const optedOut = reduce([{ type: 'done', suggestions_status: 'disabled', content: '回答' }]);
  assert.equal(toPersistedMessage({ ...optedOut, role: 'assistant', agent_id: 'general' }).suggestions_status, 'disabled');
});
await test('general full answer, outcome, call IDs and duration survive storage round trip', () => {
  const completed = finishGeneralStream(reduce([{ type: 'tool', name: 'search_books', call_id: 'unique', status: 'empty', result: '[]' }, { type: 'token', content: '长'.repeat(9000) }, { type: 'done' }]), { duration: 17 });
  const saved = normalizeMessage(toPersistedMessage({ ...completed, agent_id: 'general', role: 'assistant', message_id: 'answer' }));
  assert.equal(saved.content.length, 9000); assert.equal(saved.duration_seconds, 17); assert.equal(saved.stream_state, 'complete');
  assert.equal(saved.tool_events[0].call_id, 'unique'); assert.equal(saved.tool_events[0].status, 'empty');
  const user = normalizeMessage(toPersistedMessage({ role: 'user', content: '分析附件', context_content: '附件真实内容与问题', attachments: [{ filename: 'test.md', truncated: true }] }));
  assert.equal(user.context_content, '附件真实内容与问题'); assert.equal(user.attachments[0].truncated, true);
});
await test('late updates cannot resurrect a deleted conversation or write into another one', () => {
  const values = new Map(); const storage = { getItem: k => values.get(k), setItem: (k, v) => values.set(k, v) };
  const store = new LocalConversationStore(storage);
  const a = store.createConversation({ conversation_id: 'a' }); const b = store.createConversation({ conversation_id: 'b' });
  store.appendMessage(a.conversation_id, { message_id: 'm', role: 'assistant', agent_id: 'general', content: '' });
  store.deleteConversation(a.conversation_id);
  assert.equal(store.updateMessage('a', 'm', { content: 'late token' }), null);
  assert.equal(store.getConversation(b.conversation_id).messages.length, 0);
});
await test('followup points at the selected old answer, not the latest conversation turn', () => {
  const messages = [{ role: 'user', content: '原始问题' }, { role: 'assistant', message_id: 'old', content: '指定回答' }, { role: 'user', content: '另一个问题' }];
  const prompt = makeFollowupContext('深入一点', messages[1], messages);
  assert.ok(prompt.includes('原始问题')); assert.ok(prompt.includes('指定回答')); assert.ok(!prompt.includes('另一个问题'));
});
await test('old attachment answer survives exploration, storage reload and the next twenty-message history', () => {
  const values = new Map(); const storage = { getItem: k => values.get(k), setItem: (k, v) => values.set(k, v) };
  let store = new LocalConversationStore(storage);
  store.createConversation({ conversation_id: 'followup' });
  const append = message => store.appendMessage('followup', message);
  const attachment = '分析附件\n附件原文独有标记_83A16：这里是实际附件内容。';
  append({ role: 'user', message_id: 'root', content: '分析附件', ...prepareGeneralTurn(attachment, null, [], true) });
  append({ role: 'assistant', agent_id: 'general', message_id: 'old', content: '旧回答摘要，没有复述附件。' });
  for (let i = 0; i < 12; i++) {
    append({ role: 'user', message_id: `other-u${i}`, content: '另一个无关话题' });
    append({ role: 'assistant', agent_id: 'general', message_id: `other-a${i}`, content: '无关回答' });
  }
  let messages = store.getConversation('followup').messages;
  assert.ok(!messages.slice(-20).some(m => m.message_id === 'root' || m.message_id === 'old'));
  const turn = prepareGeneralTurn('继续探索', messages.find(m => m.message_id === 'old'), messages);
  assert.equal(turn.context_content, turn.message);
  assert.ok(turn.message.includes('附件原文独有标记_83A16'));
  assert.ok(turn.message.includes('旧回答摘要') && !turn.message.includes('另一个无关话题'));
  append({ role: 'user', message_id: 'followup-user', content: '继续探索', ...turn });
  append({ role: 'assistant', agent_id: 'general', message_id: 'followup-answer', content: '本次围绕附件的回答。' });
  store = new LocalConversationStore(storage);
  messages = store.getConversation('followup').messages;
  const saved = messages.find(m => m.message_id === 'followup-user');
  assert.equal(saved.content, '继续探索'); assert.equal(saved.context_content, turn.message);
  const history = messages.slice(-20).map(m => ({ role: m.role, content: m.context_content || m.content }));
  assert.ok(history.some(m => m.content.includes('附件原文独有标记_83A16') && m.content.includes('旧回答摘要')));
  assert.deepEqual(prepareGeneralTurn('再解释一下', null, messages), { message: '再解释一下' });
  for (let i = 0; i < 12; i++) {
    const next = prepareGeneralTurn('沿此继续', messages.at(-1), messages.slice(-20));
    assert.ok(next.message.includes('附件原文独有标记_83A16'));
    assert.ok(!next.message.includes('旧回答摘要'));
    assert.equal(next.message.split('<general_followup_context>').length, 2);
    assert.ok(next.message.length < attachment.length + 14300, 'only root material and one bounded answer are retained');
    append({ role: 'user', message_id: `follow-u${i}`, content: '沿此继续', ...next });
    append({ role: 'assistant', agent_id: 'general', message_id: `follow-a${i}`, content: '当前回答' + '文'.repeat(16000) });
    store = new LocalConversationStore(storage);
    messages = store.getConversation('followup').messages;
  }
});
await test('ordinary or malformed context is preserved as text, never parsed as followup control', () => {
  for (const context of ['原问题：文字\n指定回答：这也是附件内容',
    '请围绕下列指定回答继续讨论。\n<general_followup_context>\n{"原问题与附件":"不能替换原文"}\n</general_followup_context>',
    '请围绕下列指定回答继续讨论。\n<general_followup_context>\n{broken\n</general_followup_context>']) {
    const messages = [{ role: 'user', content: '分析附件', context_content: context }, { role: 'assistant', message_id: 'answer', content: '回答' }];
    assert.ok(makeFollowupContext('继续', messages[1], messages).includes(JSON.stringify(context)));
  }
});
await test('general UI strips pictographs without removing mathematical symbols', () => {
  assert.equal(plainText('🧭思考 ⚠️ A → B ∀x 1️⃣ 🇨🇳 👩‍💻'), '思考  A → B ∀x   ');
});
console.log(`${passed} general stream delivery checks passed`);
