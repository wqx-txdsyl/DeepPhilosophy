/**
 * Conversation 纯逻辑（无 React / 无 window 依赖, Node 可直接测试）
 *
 * 设计文档: docs/PhiAgent_Conversation_Workspace_Refactor.md
 * - §4  标题: deterministic 规则, 中文约 8~20 字, 不做额外 LLM 调用
 * - §6  打开旧会话 Composer Agent 优先级: last_used → default → general
 * - §10 "可继续探索" Agent 规则: 未主动切 Agent → 沿用来源回答的 agent_id;
 *        已主动切换 → 尊重当前 Composer Agent（稳定、可测试）
 * - §3  历史会话按 今天/昨天/过去 7 天/更早 分组, 空分组不显示
 */

export const GENERAL_AGENT = 'general';

/** 会话 id（persist 后使用）与草稿 scope（路由 /agent 上的临时 Draft） */
export const DRAFT_ID = '__draft__';

/**
 * deterministic 标题生成: 取首条用户消息, 折叠空白, 截 18 字 + '…'（含省略号约 8~20 字）
 * 剥除附件前缀标记（send 时注入的「[附件：…]」）。
 */
export function genConversationTitle(firstUserText) {
  let text = String(firstUserText || '');
  text = text.replace(/^\[[^\]]*\]\s*/, '');            // 附件注记前缀
  text = text.replace(/\s+/g, ' ').trim();              // 换行/连续空白折叠
  if (!text) return '新对话';
  return text.length > 18 ? text.slice(0, 18) + '…' : text;
}

/**
 * "可继续探索"最终建议选择（2026-08-29 闪跳修复）:
 * 后端 done 事件的 suggestions 是规则版(_suggest_next 纯内存计算, 非 LLM 生成);
 * 真正的 LLM 版稍后以 suggestions 增量事件补发（失败/超慢时可能不到）。
 * 规则: LLM 版优先; 未到达才用规则版兜底——保证建议只在屏幕上出现一次,
 * 不会"先弹格式化内容、随后闪跳替换"。
 */
export function resolveFinalSuggestions(ruleSuggestions, llmSuggestions) {
  if (Array.isArray(llmSuggestions) && llmSuggestions.length) return llmSuggestions;
  if (Array.isArray(ruleSuggestions) && ruleSuggestions.length) return ruleSuggestions;
  return [];
}

/**
 * Composer Agent 优先级（§6）: last_used_agent_id → default_agent_id → general
 */
export function resolveComposerAgent(lastUsedAgentId, defaultAgentId) {
  return lastUsedAgentId || defaultAgentId || GENERAL_AGENT;
}

/**
 * "可继续探索"的发送 Agent 规则（§10, 稳定可测试）:
 * - 用户已在本次会话中主动切换过 Selector → 尊重当前 Composer Agent
 * - 未主动切换 → 沿用来源回答的 agent_id（历史回答身份不被当前选择污染）
 */
export function resolveFollowupAgent(selectorTouched, composerAgent, sourceAgentId) {
  if (selectorTouched) return composerAgent || GENERAL_AGENT;
  return sourceAgentId || composerAgent || GENERAL_AGENT;
}

const _dayStart = (ts) => {
  const d = new Date(ts);
  d.setHours(0, 0, 0, 0);
  return d.getTime();
};

/**
 * 会话按 updated_at 分组（§3）: [ [groupKey, items], ... ] 仅含非空组, 新→旧
 * groupKey ∈ today | yesterday | last7 | earlier
 */
export function groupConversationsByDay(conversations, now = Date.now()) {
  const today0 = _dayStart(now);
  const groups = { today: [], yesterday: [], last7: [], earlier: [] };
  for (const c of [...(conversations || [])].sort((a, b) => _ts(b) - _ts(a))) {
    const t0 = _dayStart(_ts(c));
    if (t0 === today0) groups.today.push(c);
    else if (t0 === today0 - 86400000) groups.yesterday.push(c);
    else if (t0 > today0 - 7 * 86400000) groups.last7.push(c);
    else groups.earlier.push(c);
  }
  return [
    ['today', groups.today],
    ['yesterday', groups.yesterday],
    ['last7', groups.last7],
    ['earlier', groups.earlier],
  ].filter(([, items]) => items.length > 0);
}

const _ts = (c) => {
  const t = Date.parse(c?.updated_at || '');
  return Number.isFinite(t) ? t : 0;
};

/** 归一化一条消息（store 读出/迁移时兜底形状, 历史回答身份只能来自 message.agent_id） */
export function normalizeMessage(raw, fallbackAgentId = GENERAL_AGENT) {
  if (!raw || typeof raw !== 'object') return null;
  const role = raw.role === 'assistant' ? 'assistant' : 'user';
  return {
    message_id: String(raw.message_id || raw.msgId || `msg_${Math.random().toString(36).slice(2, 10)}`),
    conversation_id: raw.conversation_id || null,
    role,
    ...(role === 'assistant' ? { agent_id: raw.agent_id || fallbackAgentId } : {}),
    content: typeof raw.content === 'string' ? raw.content : '',
    ...(normalizeAttachments(raw.attachments).length ? { attachments: normalizeAttachments(raw.attachments) } : {}),
    ...(role === 'assistant'
      ? {
          citations: Array.isArray(raw.citations) ? raw.citations : [],
          ...(raw.evidence ? { evidence: raw.evidence } : {}),
          tool_events: Array.isArray(raw.tool_events) ? raw.tool_events : (Array.isArray(raw.events) ? raw.events : []),
          ...(raw.suggestions?.length ? { suggestions: raw.suggestions } : {}),
          ...(raw.reasoning_summary ? { reasoning_summary: raw.reasoning_summary } : {}),
          ...(raw.safety ? { safety: raw.safety } : {}),
        }
      : {}),
    created_at: raw.created_at || new Date().toISOString(),
    ...(Number.isFinite(raw.duration_seconds) ? { duration_seconds: raw.duration_seconds } : {}),
  };
}

/** 附件元数据归一化（发送时快照的 immutable metadata; 跨会话隔离由 draft 层保证） */
export function normalizeAttachments(raw) {
  if (!Array.isArray(raw)) return [];
  return raw
    .filter((a) => a && typeof a === 'object' && a.filename)
    .map((a) => ({
      filename: String(a.filename),
      kind: ['image', 'markdown', 'text', 'document'].includes(a.kind) ? a.kind : 'document',
      ...(Number.isFinite(a.size) ? { size: a.size } : {}),
    }));
}

/**
 * Tool 行摘要（§18: 默认只显示动作名/状态/简短结果; 展开才有 args/data）:
 * result_summary 若是 JSON 载荷 → 提取常见文本字段或 N 结果; 否则截断。
 */
export function toolShortSummary(tc) {
  const rs = tc?.result_summary;
  const s = typeof rs === 'string' ? rs.trim() : '';
  if (!s) return '';
  if (s[0] === '{' || s[0] === '[') {
    try {
      const parsed = JSON.parse(s);
      let text = '';
      if (typeof parsed === 'string') text = parsed;
      else if (Array.isArray(parsed)) text = `${parsed.length} results`;
      else if (parsed && typeof parsed === 'object') {
        for (const k of ['summary', 'text', 'snippet', 'content', 'error', 'title', 'answer', 'result', 'results', 'items', 'data']) {
          const v = parsed[k];
          if (typeof v === 'string' && v) { text = v; break; }
          if (Array.isArray(v) && v.length) { text = `${v.length} results`; break; }
        }
        if (!text) text = `${Object.keys(parsed).length} fields`;
      }
      return text.split('\n')[0].slice(0, 56);
    } catch {
      // Python dict/单引号 repr 等不可安全解析 → 绝不回退 raw（P0: 生产默认禁止内部字段）
      return '';
    }
  }
  // 类 dict 文本（python repr 首字符可能不是 {, 但内部含 `'key':`）→ 隐藏
  if (/^\{\s*['"]?\w+['"]?\s*:/.test(s)) return '';
  return s.split('\n')[0].slice(0, 56);
}

/** args 摘要: 优先人类可读字段（query/q/title/…）, 否则首个 string 值;
 *  跳过 dict/JSON 字形（P0 禁止 raw 形状泄漏） */
const _looksLikeDict = (s) => /^\{|^\[|^\[?\{/.test(String(s).trim()) || /^\{\s*['"]?\w+['"]?\s*:/.test(String(s).trim());
export function toolShortArgs(args) {
  const a = args || {};
  const keys = ['query', 'q', 'title', 'prompt', 'topic', 'book', 'question', 'skill', 'instruction', 'command', 'name', 'id'];
  for (const k of keys) {
    const v = a[k];
    if (typeof v === 'string' && v && !_looksLikeDict(v)) return v.replace(/\s+/g, ' ').slice(0, 40);
  }
  const first = Object.values(a).find((v) => typeof v === 'string' && v && !_looksLikeDict(v));
  return first ? first.replace(/\s+/g, ' ').slice(0, 40) : '';
}

/* ── P0 Tool Trace 三级披露（Level 1 人话摘要） ── */

/** 检索/查阅类工具: Level 1 可合并为「查阅了 N 项资料」 */
export const RETRIEVAL_TOOLS = new Set([
  'search_books', 'get_chapter', 'get_book_detail', 'get_philosopher', 'get_school',
  'list_books', 'query_graph', 'query_database', 'concept_trace',
]);

export const isRetrievalTool = (name) => RETRIEVAL_TOOLS.has(name);

const _str = (v) => (typeof v === 'string' ? v.trim() : '');

/**
 * Level 1 摘要（人话; 禁止渲染内部字段）:
 * 从 args 的“实体字段”（书名/章/人/主题）与结果条数生成用户可理解的句子;
 * 不匹配则返回 ''（由组件回退到是否合并态/一般动作名）。
 */
export function toolHumanSummary(name, args, shortResult) {
  const a = args || {};
  const book = _str(a.book || a.book_title || a.title);
  const chapter = _str(a.chapter || a.chapter_name || a.section).slice(0, 12);
  const query = _str(a.query || a.q || a.topic || a.question || a.keyword);
  const person = _str(a.name || a.philosopher || a.author);
  const m = typeof shortResult === 'string' ? shortResult.match(/^(\d+) results?$/) : null;
  const n = m ? Number(m[1]) : null;
  const cut = (s, max = 22) => (s.length > max ? s.slice(0, max) + '…' : s);
  switch (name) {
    case 'search_books':
      return query ? `已检索《${cut(query)}》` : (n != null ? `已检索到 ${n} 项资料` : '已检索原典');
    case 'get_chapter':
      return book ? `已读取《${cut(book)}${chapter ? `·${chapter}` : ''}》` : '已定位相关章节';
    case 'get_book_detail':
      return book ? `已查书详情《${cut(book)}》` : '已查书详情';
    case 'get_philosopher':
      return person ? `已确认${cut(person)}人物信息` : '已确认哲人人物信息';
    case 'get_school':
      return person ? `已确认「${cut(person)}」流派信息` : '已查询流派信息';
    case 'list_books':
      return n != null ? `已筛选书目 ${n} 项` : '已筛选书目';
    case 'query_graph':
      return person ? `已查询「${cut(person)}」思想星丛` : (n != null ? `已查询星丛 ${n} 项` : '已查询思想星丛');
    case 'query_database':
      return n != null ? `已查询数据库 ${n} 项` : '已查询数据库';
    case 'concept_trace':
      return query ? `已溯源「${cut(query)}」` : '已概念溯源';
    default:
      return '';
  }
}

/** Level 1 合并文案: 「查阅了 N 项资料」 */
export const retrievalGroupSummary = (n) => `已查阅了 ${n} 项资料`;

/**
 * User 消息可见文本清洗（P0-3 Attachment 重复渲染）:
 * 新数据 content 已是纯用户文本; 旧历史数据若存在系统生成的附件 serialization 前缀
 * （[附件：《x》] / 【附件《x》】 / 附件：），在做渲染前保守剥离——
 * 仅当该消息存在同名 structured attachments 时才 dedupe，绝不删除用户手写普通文本。
 */
export function cleanUserMessageForRender(content, attachments) {
  if (!Array.isArray(attachments) || !attachments.length) return content;
  let c = String(content || '');
  // [附件：《a》·《b》]\n（系统 display 前缀）
  c = c.replace(/^\[附件[^\]]*\]\s*\n?/, '');
  // 【附件《a》】 行内标记前缀（旧 attachText 头）
  c = c.replace(/^【附件《[^】]*》】\s*\n?/, '');
  // 附件： / Attached file: 前缀
  c = c.replace(/^(附件|Attached file|附件文件)[：:]\s*\n?/, '');
  return c;
}

/**
 * Agent Identity 显示规则（§10, 纯函数可测; 与全局 currentAgent 无关）:
 * 同一会话出现 ≥2 种回答者 → 每条 assistant 都显示身份;
 * 单回答者会话但与前一条 assistant 不同（切换回来）→ 显示;
 * 否则隐藏（连续同一 Agent 时身份弱化, §10）。
 */
export function resolveIdentityVisible(prevAssistantAgentIds, agentId) {
  const seen = prevAssistantAgentIds || [];
  if (!agentId) return false;
  if (seen.length >= 1 && seen[seen.length - 1] !== agentId) return true;   // 上一个回答者不同
  const distinct = new Set(seen);
  distinct.add(agentId);
  return distinct.size > 1;                                                  // 会话内出现过多回答者
}

/**
 * 流式消息 → 可持久化消息: 剥离瞬态字段, 未完成 tool_start 收敛为 tool_cancel,
 * result_summary 截断防 localStorage 膨胀（tool info 属于 message, 允许持久化 §12）。
 */
export function toPersistedMessage(m) {
  if (!m || typeof m !== 'object') return null;
  const base = {
    message_id: m.message_id,
    conversation_id: m.conversation_id || null,
    role: m.role,
    content: m.content || '',
    created_at: m.created_at || new Date().toISOString(),
  };
  const attachments = normalizeAttachments(m.attachments);
  if (attachments.length) base.attachments = attachments;
  if (m.role !== 'assistant') return base;
  const events = (m.events || m.tool_events || []).map((ev) => {
    if (ev?.t === 'tool_start') return { t: 'tool_cancel', name: ev.name, reason: '未执行，已跳过' };
    if (ev?.t === 'tool' && ev.tc) {
      return { t: 'tool', tc: { ...ev.tc, result_summary: String(ev.tc.result_summary || '').slice(0, 400) } };
    }
    return ev;
  });
  return {
    ...base,
    agent_id: m.agent_id || GENERAL_AGENT,
    citations: Array.isArray(m.citations) ? m.citations : [],
    ...(m.evidence ? { evidence: m.evidence } : {}),
    tool_events: events,
    ...(m.suggestions?.length ? { suggestions: m.suggestions } : {}),
    ...(m.reasoning_summary ? { reasoning_summary: m.reasoning_summary } : {}),
    ...(m.safety ? { safety: m.safety } : {}),
  };
}

/** 归一化整个会话（store 读取兜底） */
export function normalizeConversation(raw) {
  if (!raw || typeof raw !== 'object' || !raw.conversation_id) return null;
  return {
    conversation_id: String(raw.conversation_id),
    title: typeof raw.title === 'string' && raw.title ? raw.title : '新对话',
    default_agent_id: raw.default_agent_id || GENERAL_AGENT,
    last_used_agent_id: raw.last_used_agent_id || null,
    created_at: raw.created_at || new Date().toISOString(),
    updated_at: raw.updated_at || raw.created_at || new Date().toISOString(),
    reading_context: {
      book_id: raw.reading_context?.book_id ?? null,
      chapter_id: raw.reading_context?.chapter_id ?? null,
      selected_text: raw.reading_context?.selected_text ?? null,
    },
    messages: Array.isArray(raw.messages)
      ? raw.messages.map((m) => normalizeMessage(m, raw.last_used_agent_id || raw.default_agent_id || GENERAL_AGENT)).filter(Boolean)
      : [],
  };
}

/**
 * legacy 迁移（纯函数部分）: 旧版按 agent 分键的 localStorage 消息数组
 * （dp_agent_msgs_v2_{agent} = [{role, content}, ...]）→ 会话对象数组。
 * 历史回答身份按其来源 agent 标注 agent_id（§5）。
 */
export function legacyMessagesToConversations(legacyByAgent, now = new Date()) {
  const out = [];
  for (const [agentKey, msgs] of Object.entries(legacyByAgent || {})) {
    if (!Array.isArray(msgs) || !msgs.length) continue;
    const iso = (typeof now === 'string' ? now : now.toISOString());
    out.push(normalizeConversation({
      conversation_id: `conv_legacy_${agentKey}`,
      title: agentKey === GENERAL_AGENT ? '深哲 · 历史对话' : `${agentKey} · 历史对话`,
      default_agent_id: agentKey,
      last_used_agent_id: agentKey,
      created_at: iso,
      updated_at: iso,
      messages: msgs.map((m, i) => ({
        message_id: `msg_legacy_${agentKey}_${i}`,
        role: m?.role,
        content: m?.content,
        ...(m?.role === 'assistant' ? { agent_id: agentKey } : {}),
        created_at: iso,
      })),
    }));
  }
  return out;
}
