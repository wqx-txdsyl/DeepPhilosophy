/**
 * PhiAgent Conversation Workspace — 纯逻辑回归测试（无框架, node 直接运行）
 * 覆盖设计文档 §4 标题 / §6 Composer 优先级 / §10 可继续探索 Agent 规则 /
 * §5 消息 agent_id / §12 Store 接口 / §9 删除后不复活 / legacy 迁移
 *
 * 运行: npm test （agent-app/ 下; 或 node tests/conversationLogic.test.mjs）
 */
import assert from 'node:assert/strict';
import {
  genConversationTitle, resolveComposerAgent, resolveFollowupAgent, resolveFinalSuggestions,
  groupConversationsByDay, legacyMessagesToConversations, toPersistedMessage, normalizeMessage,
  resolveIdentityVisible, normalizeAttachments, toolShortSummary, toolShortArgs,
} from '../src/data/conversationLogic.js';
import { LocalConversationStore } from '../src/data/conversationStore.js';
import { pickUsedEvidence } from '../src/utils/evidence.js';

let passed = 0;
const ok = (name, fn) => { fn(); passed += 1; console.log('  ✓', name); };

/* ── mock localStorage（Map 实现 length/key 语义） ── */
function mockStorage() {
  const m = new Map();
  return {
    getItem: (k) => (m.has(String(k)) ? m.get(String(k)) : null),
    setItem: (k, v) => { m.set(String(k), String(v)); },
    removeItem: (k) => { m.delete(String(k)); },
    key: (i) => [...m.keys()][i] ?? null,
    get length() { return m.size; },
  };
}

console.log('conversationLogic:');

ok('genConversationTitle 截 18 字 + …', () => {
  const long = '永恒轮回的意思是什么，尼采究竟怎么论述这个思想';
  const t = genConversationTitle(long);
  assert.equal(t.length <= 19, true, `too long: ${t.length}`);
  assert.equal(t.endsWith('…'), true);
  assert.equal(genConversationTitle('   \n  '), '新对话');
  assert.equal(genConversationTitle('[附件：《x.md》]\n你好'), '你好');
  assert.equal(genConversationTitle('你好\n世界'), '你好 世界');
});

ok('resolveComposerAgent: last_used → default → general', () => {
  assert.equal(resolveComposerAgent('nietzsche', 'general'), 'nietzsche');
  assert.equal(resolveComposerAgent(null, 'nietzsche'), 'nietzsche');
  assert.equal(resolveComposerAgent(null, null), 'general');
  assert.equal(resolveComposerAgent('', ''), 'general');
});

ok('resolveFollowupAgent: 主动切换 → composer; 未切换 → 来源回答 agent_id（§10）', () => {
  assert.equal(resolveFollowupAgent(true, 'general', 'nietzsche'), 'general');   // 已切换 → 尊重当前
  assert.equal(resolveFollowupAgent(false, 'general', 'nietzsche'), 'nietzsche'); // 未切换 → 沿用来源
  assert.equal(resolveFollowupAgent(false, 'general', null), 'general');
});

ok('resolveFinalSuggestions: LLM 版优先, 未到达才用规则版兜底（2026-08-29 闪跳修复）', () => {
  const rule = ['规则建议A', '规则建议B'];
  const llm = ['LLM 建议X', 'LLM 建议Y'];
  assert.deepEqual(resolveFinalSuggestions(rule, llm), llm);      // LLM 版到达 → 用 LLM 版
  assert.deepEqual(resolveFinalSuggestions(rule, []), rule);      // LLM 版未到 → 规则版兜底
  assert.deepEqual(resolveFinalSuggestions(['x'], null), ['x']);
  assert.deepEqual(resolveFinalSuggestions([], null), []);
});

ok('groupConversationsByDay: 分组空组过滤 + 新→旧', () => {
  const now = new Date(2026, 7, 29, 12).getTime();    // 本地 2026-08-29 12:00
  const convs = [
    { conversation_id: 'a', updated_at: new Date(2026, 7, 28, 23).toISOString() },  // 昨天
    { conversation_id: 'b', updated_at: new Date(2026, 7, 29, 12).toISOString() },  // 今天
    { conversation_id: 'c', updated_at: new Date(2026, 7, 25, 12).toISOString() },  // 过去 7 天
    { conversation_id: 'd', updated_at: new Date(2026, 7, 10, 12).toISOString() },  // 更早
  ];
  const groups = groupConversationsByDay(convs, now);
  const keys = groups.map(([k]) => k).join(',');
  assert.equal(keys, 'today,yesterday,last7,earlier');
  assert.deepEqual(groups.find(([k]) => k === 'today')[1].map(c => c.conversation_id), ['b']);
});

ok('groupConversationsByDay: 空分组不显示', () => {
  const now = new Date(2026, 7, 29, 12).getTime();
  const groups = groupConversationsByDay([
    { conversation_id: 'b', updated_at: new Date(2026, 7, 29, 12).toISOString() },
  ], now);
  assert.equal(groups.map(([k]) => k).join(','), 'today');
});

ok('legacyMessagesToConversations: 每 Agent 一键 + assistant 标注来源 agent_id（§5）', () => {
  const now = new Date('2026-08-29T00:00:00Z');
  const convs = legacyMessagesToConversations({
    general: [{ role: 'user', content: 'A' }, { role: 'assistant', content: 'B' }],
    nietzsche: [{ role: 'user', content: 'C' }],
  }, now);
  assert.equal(convs.length, 2);
  const gen = convs.find(c => c.conversation_id === 'conv_legacy_general');
  assert.equal(gen.default_agent_id, 'general');
  assert.equal(gen.messages[1].agent_id, 'general');
  const nie = convs.find(c => c.conversation_id === 'conv_legacy_nietzsche');
  assert.equal(nie.default_agent_id, 'nietzsche');
  assert.equal(nie.messages[0].role, 'user');
  assert.ok(!('agent_id' in nie.messages[0]));       // user 消息不带 agent_id
});

ok('toPersistedMessage: tool_start→tool_cancel + 截断 + citation/agent 保留', () => {
  const out = toPersistedMessage({
    message_id: 'm1', conversation_id: 'c1', role: 'assistant', agent_id: 'nietzsche',
    content: 'hi', citations: [{ book: '查拉图斯特拉如是说', chapter: '序言' }],
    events: [{ t: 'thought', text: '嗯' }, { t: 'tool_start', name: 'search_books' },
             { t: 'tool', tc: { name: 'search_books', args: {}, result_summary: 'x'.repeat(900) } }],
    streaming: true, curThought: 'pending', status: 'thinking',
  });
  assert.equal(out.streaming, undefined);
  assert.equal(out.curThought, undefined);
  assert.ok(out.tool_events.find(e => e.t === 'tool_cancel'));
  assert.ok(out.tool_events.find(e => e.t === 'tool' && e.tc.result_summary.length === 400));
  assert.equal(out.citations.length, 1);
  assert.equal(out.agent_id, 'nietzsche');
  assert.equal(out.tool_events.find(e => e.t === 'thought').text, '嗯');
});

console.log('LocalConversationStore:');

ok('CRUD + 排序 + 标题/默认/最后使用 Agent', () => {
  const s = new LocalConversationStore(mockStorage());
  const c1 = s.createConversation({ title: 'T1', default_agent_id: 'nietzsche' });
  const c2 = s.createConversation({ title: 'T2' });
  assert.equal(s.listConversations().length, 2);
  assert.ok(s.listConversations()[0].conversation_id === c2.conversation_id);   // 新在前
  s.setConversationTitle(c1.conversation_id, '改名');
  assert.equal(s.getConversation(c1.conversation_id).title, '改名');
  s.setDefaultAgent(c1.conversation_id, 'general');
  s.setLastUsedAgent(c1.conversation_id, 'nietzsche');
  const got = s.getConversation(c1.conversation_id);
  assert.equal(got.default_agent_id, 'general');
  assert.equal(got.last_used_agent_id, 'nietzsche');
  assert.ok(s.deleteConversation(c2.conversation_id));
  assert.equal(s.listConversations().length, 1);
  assert.ok(!s.deleteConversation('nope'));
});

ok('appendMessage 保留 agent_id / citations / tool_events; 缺失会话不复活（§9）', () => {
  const s = new LocalConversationStore(mockStorage());
  const c = s.createConversation({ default_agent_id: 'nietzsche' });
  s.appendMessage(c.conversation_id, {
    message_id: 'm1', role: 'user', content: 'Q', created_at: new Date().toISOString(),
  });
  s.appendMessage(c.conversation_id, {
    message_id: 'm2', role: 'assistant', agent_id: 'nietzsche', content: 'A',
    citations: [{ book: 'B', chapter: '序' }], suggestions: ['再问'],
    events: [{ t: 'tool', tc: { name: 'search_books', args: { q: 'x' }, result_summary: 'r' } }],
    created_at: new Date().toISOString(),
  });
  const conv = s.getConversation(c.conversation_id);
  assert.equal(conv.messages.length, 2);
  assert.equal(conv.messages[1].agent_id, 'nietzsche');
  assert.equal(conv.messages[1].citations.length, 1);
  assert.equal(conv.messages[1].suggestions[0], '再问');
  assert.equal(conv.messages[1].tool_events.length, 1);
  // 删除后 late write 不得复活
  s.deleteConversation(c.conversation_id);
  s.appendMessage(c.conversation_id, { message_id: 'm3', role: 'assistant', agent_id: 'general', content: 'late' });
  s.updateMessage(c.conversation_id, 'm1', { content: 'x' });
  assert.equal(s.listConversations().length, 0);
});

ok('updateMessage: 仅更新指定消息; reasoning_summary 保留', () => {
  const s = new LocalConversationStore(mockStorage());
  const c = s.createConversation({});
  s.appendMessage(c.conversation_id, { message_id: 'm1', role: 'assistant', agent_id: 'general', content: 'a', suggestions: ['s'] });
  s.updateMessage(c.conversation_id, 'm1', { suggestions: ['s2'], reasoning_summary: '摘要' });
  const m = s.getConversation(c.conversation_id).messages[0];
  assert.deepEqual(m.suggestions, ['s2']);
  assert.equal(m.reasoning_summary, '摘要');
  s.updateMessage(c.conversation_id, 'missing', { content: 'no' });
  assert.equal(s.getConversation(c.conversation_id).messages.length, 1);
});

ok('migrateLegacy: 旧键迁移 + 一键一 Agent + 旧键清理 + 幂等', () => {
  const st = mockStorage();
  st.setItem('dp_agent_msgs_v2_general', JSON.stringify([{ role: 'user', content: 'hi' }]));
  st.setItem('dp_agent_msgs_v2_nietzsche', JSON.stringify([{ role: 'user', content: 'q' }, { role: 'assistant', content: 'a' }]));
  st.setItem('dp_agent_msgs_v1_other', JSON.stringify([{ role: 'user', content: 'old' }]));
  const s = new LocalConversationStore(st);
  const r = s.migrateLegacy();
  assert.equal(r.migrated, 2);
  const list = s.listConversations();
  assert.equal(list.length, 2);
  const nie = list.find(c => c.conversation_id === 'conv_legacy_nietzsche');
  assert.equal(nie.default_agent_id, 'nietzsche');
  assert.equal(nie.messages[1].content, 'a');
  assert.equal(st.getItem('dp_agent_msgs_v2_general'), null);   // 旧键已删
  assert.equal(st.getItem('dp_agent_msgs_v1_other'), null);
  // 幂等: v1 已存在不再迁移
  st.setItem('dp_agent_msgs_v2_general', JSON.stringify([{ role: 'user', content: 'B' }]));
  const r2 = s.migrateLegacy();
  assert.equal(r2.migrated, 0);
});

ok('Phase 3: 引用面板只展示 used_evidence（used:false 的检索候选不进面板）', () => {
  const citations = [
    { evidence_id: 'ev_1', book: '查拉图斯特拉如是说', used: true },
    { evidence_id: 'ev_2', book: '西西弗斯神话', used: false },   // 检索过但回答未用
    { evidence_id: 'ev_3', book: '理想国' },                      // 旧数据无 used 字段 → 兼容显示
  ];
  const used = pickUsedEvidence(citations);
  assert.deepEqual(used.map(c => c.book), ['查拉图斯特拉如是说', '理想国']);
  assert.deepEqual(pickUsedEvidence('bad'), []);                  // 非数组防御
});

ok('Codex-Parity: resolveIdentityVisible（§10 消息级身份规则, 不依赖全局 currentAgent）', () => {
  // 连续同 Agent → 不显示（弱化, §10）
  assert.equal(resolveIdentityVisible([], 'nietzsche'), false);
  assert.equal(resolveIdentityVisible(['nietzsche'], 'nietzsche'), false);
  // 上一个回答者不同 → 显示
  assert.equal(resolveIdentityVisible(['nietzsche'], 'general'), true);
  // 会话已出现 ≥2 种回答者 → 全部显示（含连续段）
  assert.equal(resolveIdentityVisible(['nietzsche', 'general', 'nietzsche'], 'nietzsche'), true);
  // 无 agent_id → 不显示
  assert.equal(resolveIdentityVisible([], null), false);
});

ok('Codex-Parity: normalizeAttachments 过滤非法 + 保留 size/kind', () => {
  assert.deepEqual(normalizeAttachments([{ filename: 'a.md', kind: 'markdown', size: 12 }]),
    [{ filename: 'a.md', kind: 'markdown', size: 12 }]);
  assert.deepEqual(normalizeAttachments([{ filename: 'b.png', kind: 'image', size: 0 }]),
    [{ filename: 'b.png', kind: 'image', size: 0 }]);   // size 0 也保留（空文件）
  assert.deepEqual(normalizeAttachments([{ filename: '' }, { filename: 'x', kind: 'weird' }, null]),
    [{ filename: 'x', kind: 'document' }]);    // 未知 kind → document
  assert.deepEqual(normalizeAttachments('bad'), []);
});

ok('Codex-Parity: toolShortSummary/toolShortArgs（§18 紧凑 trace, 无 JSON 噪音）', () => {
  const j = toolShortSummary({ result_summary: '{"results":[{"book_id":"x"}]}' });
  assert.equal(j, '1 results');
  assert.equal(toolShortSummary({ result_summary: '{"summary":"找到 3 本书"}' }), '找到 3 本书');
  assert.equal(toolShortSummary({ result_summary: '普通文本结果' }), '普通文本结果');
  assert.equal(toolShortSummary({}), '');
  assert.equal(toolShortSummary({ result_summary: 'x'.repeat(300) }).length <= 60, true);
  assert.equal(toolShortArgs({ role: 'x', instruction: '用户要求以尼采第一人称回答' }), '用户要求以尼采第一人称回答');
  assert.equal(toolShortArgs({}), '');
});

ok('Codex-Parity: user 消息 attachments 持久化往返（发送瞬间 snapshot, §12）', () => {
  const p = toPersistedMessage({
    message_id: 'm1', conversation_id: 'c1', role: 'user', content: '你好',
    attachments: [{ filename: '论文.md', kind: 'markdown', size: 2048 }],
  });
  assert.equal(p.attachments.length, 1);
  assert.equal(p.attachments[0].filename, '论文.md');
  const n = normalizeMessage(p);
  assert.equal(n.attachments[0].kind, 'markdown');
});

ok('Phase 3: 非 general 消息保留 citations + evidence（历史引用不丢, UAT-06 门控回归）', () => {
  const m = normalizeMessage({
    role: 'assistant', agent_id: 'nietzsche', content: '人在彼岸是应当被超越的。',
    citations: [{ evidence_id: 'ev_1', book: '查拉图斯特拉如是说', chapter: '前言·4', used: true }],
    evidence: { retrieved_count: 5, used_count: 1 },
  });
  assert.equal(m.agent_id, 'nietzsche');
  assert.equal(m.citations.length, 1);
  assert.equal(m.citations[0].used, true);
  assert.equal(m.evidence.used_count, 1);       // evidence 契约随消息持久化
  const p = toPersistedMessage({
    message_id: 'm1', conversation_id: 'c1', role: 'assistant', agent_id: 'nietzsche',
    content: 'x', citations: [], evidence: { retrieved_count: 2, used_count: 0 },
  });
  assert.equal(p.evidence.retrieved_count, 2);
  assert.equal(p.evidence.used_count, 0);
});

console.log(`\n${passed} checks passed`);
