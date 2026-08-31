import { useEffect, useMemo, useRef, useState, useCallback } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { getApiBase } from '../utils/api';
import { useAuth } from '../auth';
import { useLang } from '../utils/i18n';
import { conversationStore } from '../data/conversationStore';
import { genConversationTitle, resolveComposerAgent, resolveFollowupAgent, resolveFinalSuggestions, DRAFT_ID } from '../data/conversationLogic';
import { getPref, setPref } from '../data/localPrefs';
import useAgents from '../utils/useAgents';
import ConversationSidebar from '../components/conversation/ConversationSidebar';
import ConversationHeader from '../components/conversation/ConversationHeader';
import MessageList, { QUESTION_BANK } from '../components/conversation/MessageList';
import Composer from '../components/conversation/Composer';
import AgentPlaza from '../components/conversation/AgentPlaza';
import SettingsPanel from '../components/conversation/SettingsPanel';
import DrawioModal from '../components/DrawioModal';
import Icon from '../components/Icon';
import '../conversation.css';

/**
 * AgentWorkspace — PhiAgent「会话优先」工作区（docs/PhiAgent_Conversation_Workspace_Refactor.md）
 *
 * Routing: /agent（临时 Draft）与 /agent/c/:conversationId（稳定会话身份）
 * Streaming Ownership（§9）: 每次 Invocation 创建时冻结 {conversation_id, message_id, agent_id},
 *   所有事件按（convId, messageId）写回, 绝不依赖全局 currentAgent:
 *   - Nietzsche Streaming 中切 Selector → 当前回答仍属 Nietzsche, 下一轮才切换
 *   - A Streaming 中打开 B → token 只写回 A
 *   - 删除 Streaming 会话 → 先 abort; late event 经 deletedRef + 缺失会话守卫不复活
 */
const genId = (p) => `${p}_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 8)}`;

export default function AgentWorkspace() {
  const { pathname } = useLocation();
  const navigate = useNavigate();
  // /agent（草稿）与 /agent/c/:conversationId（稳定会话）同一组件实例解析
  const conversationId = pathname.startsWith('/agent/c/')
    ? decodeURIComponent(pathname.slice('/agent/c/'.length))
    : null;
  const { t, lang, agentName, agentSub } = useLang();
  const { token } = useAuth();
  const { agents, agentsLoading } = useAgents();

  const [conversations, setConversations] = useState([]);
  const [hydrated, setHydrated] = useState(false);
  const [hydrateError, setHydrateError] = useState(false);
  const [plazaOpen, setPlazaOpen] = useState(false);
  const [navOpen, setNavOpen] = useState(false);          // 移动端侧栏抽屉
  const [settingsOpen, setSettingsOpen] = useState(false); // 设置面板（§24; portal, 不卸载会话）
  const [prefsTick, setPrefsTick] = useState(0);           // 设置变更后消息区即时生效（引用/工具披露）
  const [sidebarCollapsed, setSidebarCollapsed] = useState(() => getPref('sidebarCollapsed') === true);
  const [composerAgent, setComposerAgent] = useState('general');
  const [selectorTouched, setSelectorTouched] = useState(false);
  const [draftAgent, setDraftAgent] = useState(null);     // Plaza 开始对话 → 临时会话默认 Agent
  const [streamingIds, setStreamingIds] = useState(() => new Set());
  const [drawio, setDrawio] = useState(null);             // {xml, convId, messageId}

  const streamsRef = useRef(new Map());   // convId → {controller, messageId}
  const thinkQueueRef = useRef(new Map());   // convId → {list:[text]}: 思考打字机队列（逐字, 与回答同节奏）
  const thinkPlayingRef = useRef(new Set()); // convId → 正在播放
  const deletedRef = useRef(new Set());   // 已删除会话: late event 一律丢弃
  const composerAgentRef = useRef(composerAgent);
  composerAgentRef.current = composerAgent;

  const activeConv = useMemo(
    () => (conversationId ? conversations.find(c => c.conversation_id === conversationId) : null),
    [conversations, conversationId],
  );
  const isDraft = !conversationId;
  const activeStreaming = isDraft ? false : streamingIds.has(conversationId);
  const scopeKey = isDraft ? DRAFT_ID : conversationId;

  /* ── hydrate: legacy 迁移 + 会话列表（§12/§13 加载失败可重试） ── */
  const loadConversations = () => {
    setHydrateError(false);
    try {
      conversationStore.migrateLegacy();
      setConversations(conversationStore.listConversations());
      setHydrated(true);
    } catch (e) {
      setHydrateError(true);
    }
  };
  useEffect(() => { loadConversations(); }, []);

  /* ── 登出（auth.jsx 广播）: 清内存会话 + 回草稿页（隐私, §auth）── */
  useEffect(() => {
    const onLogout = () => {
      for (const { controller } of streamsRef.current.values()) {
        try { controller.abort(); } catch (e) { /* 已中断 */ }
      }
      streamsRef.current.clear();
      setConversations([]);
      navigate('/agent', { replace: true });   // 回草稿页（conversationId 由路由派生）
    };
    window.addEventListener('phiagent-logout', onLogout);
    return () => window.removeEventListener('phiagent-logout', onLogout);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  /* ── 打开会话 → Composer Agent 优先级（§6）: last_used → default → general ── */
  useEffect(() => {
    setSelectorTouched(false);
    if (conversationId) {
      // 会话不存在(已删除/失效): 交给 notFound 视图, 不得让异常卸载整棵树（§13）
      try {
        const c = conversationStore.getConversation(conversationId);
        setComposerAgent(resolveComposerAgent(c.last_used_agent_id, c.default_agent_id));
      } catch (e) { /* notFound 分支处理 */ }
    } else {
      setComposerAgent(draftAgent || conversations[0]?.last_used_agent_id || conversations[0]?.default_agent_id || 'general');
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [conversationId]);

  /* ── 本地状态变更（内存即真相; store 只做写穿持久化） ── */
  const addConversationLocal = (conv) =>
    setConversations(prev => [conv, ...prev.filter(c => c.conversation_id !== conv.conversation_id)]);

  const patchConvMeta = (convId, patch) =>
    setConversations(prev => prev.map(c => (c.conversation_id === convId ? { ...c, ...patch } : c)));

  const appendMessageLocal = (convId, msg) =>
    setConversations(prev => prev.map(c => c.conversation_id === convId
      ? { ...c, messages: [...c.messages, msg], updated_at: new Date().toISOString() }
      : c));

  // 关键守卫: 会话已被删除时不得复生（§14.4 / §9 Late Event）
  const patchMessageLocal = (convId, messageId, fn) =>
    setConversations(prev => {
      if (!prev.some(c => c.conversation_id === convId)) return prev;
      return prev.map(c => c.conversation_id === convId
        ? { ...c, messages: c.messages.map(m => (m.message_id === messageId ? fn(m) : m)) }
        : c);
    });

  const markStream = (convId, mid, controller) => {
    streamsRef.current.set(convId, { controller, messageId: mid });
    setStreamingIds(prev => new Set(prev).add(convId));
  };
  const unmarkStream = (convId) => {
    streamsRef.current.delete(convId);
    setStreamingIds(prev => { const n = new Set(prev); n.delete(convId); return n; });
  };

  /* ── 会话操作 ── */
  const handleNew = () => {
    setDraftAgent(null);
    // 新对话默认 responder（§25 设置项）; 稍后空状态/发送沿用 Composer Agent 状态
    const pref = getPref('defaultResponder');
    setComposerAgent(pref === 'nietzsche' ? 'nietzsche' : pref || 'general');
    setSelectorTouched(false);
    navigate('/agent');
  };
  const handleToggleSidebar = () => {
    setSidebarCollapsed(prev => { setPref('sidebarCollapsed', !prev); return !prev; });
  };
  const handleSelect = (id) => {
    if (id !== conversationId) navigate(`/agent/c/${id}`);
  };
  const handleRename = (conv, newTitle) => {
    const title = String(newTitle || '').trim();
    if (!title || !conv) return;
    patchConvMeta(conv.conversation_id, { title });
    conversationStore.setConversationTitle(conv.conversation_id, title);
  };
  const handleDelete = (conv) => {
    const id = conv?.conversation_id;
    if (!id) return;
    const stream = streamsRef.current.get(id);
    if (stream) { stream.controller.abort(); }       // 先中止再删（§9）
    unmarkStream(id);
    deletedRef.current.add(id);
    conversationStore.deleteConversation(id);
    setConversations(prev => prev.filter(c => c.conversation_id !== id));
    if (conversationId === id) navigate('/agent');
  };
  const handlePickAgent = (key) => {                  // Plaza 开始对话（§7）
    setPlazaOpen(false);
    setDraftAgent(key);
    setComposerAgent(key);
    setSelectorTouched(false);
    navigate('/agent');
  };
  const handleSelectorChange = (key) => {
    setComposerAgent(key);
    setSelectorTouched(true);   // 主动切换: 下一轮发送用该 Agent（历史消息不变, §6）
  };

  /* ── draw.io ── */
  const openDrawio = useCallback((messageId, code) => {
    fetch(getApiBase() + '/api/drawio', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mermaid: code }),
    }).then(r => r.json()).then(d => {
      if (d.xml) setDrawio({ xml: d.xml, convId: conversationId, messageId });
    }).catch(() => {});
  }, [conversationId]);
  const closeDrawio = (editedXml) => {
    if (drawio?.messageId && editedXml && drawio.convId) {
      patchMessageLocal(drawio.convId, drawio.messageId, m => ({ ...m, drawioXml: editedXml }));
    }
    setDrawio(null);
  };

  /* ── 发送（Streaming Ownership 冻结点） ── */
  const dispatchSend = async ({ message, display, localOnly = false, agentOverride = null, sourceMsg = null, attachments = [] }) => {
    const agent = agentOverride || composerAgentRef.current;
    const text = typeof message === 'string' ? message : String(message || '');
    const shown = typeof display === 'string' ? display : text;
    const hasAttach = Array.isArray(attachments) && attachments.length > 0;

    if (!shown.trim() && !hasAttach) return;   // 仅附件发送允许空文本（T6）
    // 同步锁（streamsRef 是同步结构; streamingIds 状态更新是异步的, 防双击产生双会话/双流）
    if (!localOnly && streamsRef.current.has(scopeKey)) return;

    let convId = conversationId;
    const isNewConv = !convId;
    if (isNewConv) {
      const created = conversationStore.createConversation({
        title: genConversationTitle(shown),
        default_agent_id: agent,
      });
      convId = created.conversation_id;
      addConversationLocal(created);
      navigate(`/agent/c/${convId}`);
    } else {
      conversationStore.setLastUsedAgent(convId, agent);
      patchConvMeta(convId, { last_used_agent_id: agent });
    }

    const nowIso = new Date().toISOString();
    const _sendT0 = performance.now();   // Thinking UI: 最终「思考了 X 秒」用
    // 发送瞬间 snapshot attachments → immutable metadata（§12）; draft 由 Composer 清空
    const attachMeta = (attachments || []).filter(a => a && a.filename);
    const userMsg = {
      message_id: genId('msg'), conversation_id: convId, role: 'user', content: shown, created_at: nowIso,
      ...(attachMeta.length ? { attachments: attachMeta } : {}),
    };
    appendMessageLocal(convId, userMsg);
    conversationStore.appendMessage(convId, userMsg);
    if (localOnly) return;

    const mid = genId('msg');
    const assistantMsg = {
      message_id: mid, conversation_id: convId, role: 'assistant', agent_id: agent,
      content: '', events: [], citations: [], suggestions: [], streaming: true,
      status: null, created_at: nowIso,
    };
    appendMessageLocal(convId, assistantMsg);

    // 历史快照: 发送前 20 条（含两种 Agent 的公开回答, §8 共享）
    const convNow = conversations.find(c => c.conversation_id === convId);
    const history = (convNow?.messages || []).slice(-20).map(m => ({ role: m.role, content: m.content }));

    const controller = new AbortController();
    markStream(convId, mid, controller);

    /* ── 本轮流式快照（事件按 convId+msgId 归属; 与全局 agent 无关） ── */
    const snap = { content: '', events: [], citations: [], evidence: null, suggestions: [], reasoning_summary: null, safety: null, curThought: null };
    let tokenBuf = '';
    let streamEnded = false;
    let doneArrived = false;
    // 2026-08-29: 引用/建议的显示时机 = 正文打字机渲染完成(而非连接关闭)。
    // 连接关闭由后端 LLM 后处理速度决定(2s~30s 不定), 若早于正文打完 → "提前跳出, 时有时无"。
    // flushMeta 由打字机排空时刻触发; 元数据未到时(建议事件晚于正文打完)再补一次。
    let metaFlushed = false;
    const renderMeta = () => {
      patchMessageLocal(convId, mid, m => ({
        ...m,
        citations: snap.citations,
        evidence: snap.evidence,
        suggestions: snap.suggestions,
        reasoning_summary: snap.reasoning_summary,
      }));
    };
    const flushMeta = () => {
      if (metaFlushed) return;
      metaFlushed = true;
      renderMeta();
    };
    const typingTimer = setInterval(() => {
      if (tokenBuf) {
        // 2026-08-29 提速: 固定 12ms/字(83 字/s)对长回答太慢, 打字机感被放大。
        // 改为自适应批渲染——队列越厚每 tick 批字越多(≤12 字), 积压超 300 字直接放闸:
        //   · 常态 100~400 字/s(可读又不等待)
        //   · 网络合包/积压时快速追平, 长回答总时长大幅缩短
        const burst = tokenBuf.length > 300 ? tokenBuf.length : Math.max(1, Math.min(12, Math.ceil(tokenBuf.length / 40)));
        const chunk = tokenBuf.slice(0, burst);
        tokenBuf = tokenBuf.slice(burst);
        snap.content += chunk;
        patchMessageLocal(convId, mid, m => ({
          ...m, typing: true,   // 正文打字机工作期间: 滚动继续跟随（streaming 在 done 已释放）
          content: m.content + chunk,
          events: m.curThought ? [...m.events, { t: 'thought', text: m.curThought }] : m.events,
          curThought: null,
        }));
      } else if (doneArrived || streamEnded) {
        clearInterval(typingTimer);
        flushMeta();   // 正文渲染完成: 此刻才显示引用/建议/推理摘要（不依赖连接关闭时刻）
      }
    }, 12);

    const finalize = (extra = {}) => {
      streamEnded = true;
      unmarkStream(convId);
      // 兜底: 连接关闭时 LLM 版建议仍未到达(失败/超慢)→ 用规则版, 至少不空白
      snap.suggestions = resolveFinalSuggestions(snap.ruleSuggestions, snap.suggestions);
      const finalMsg = {
        message_id: mid, conversation_id: convId, role: 'assistant', agent_id: agent,
        content: snap.content, events: snap.events, citations: snap.citations,
        evidence: snap.evidence,
        suggestions: snap.suggestions, reasoning_summary: snap.reasoning_summary,
        safety: snap.safety, created_at: nowIso,
        duration_seconds: Math.max(1, Math.round((performance.now() - _sendT0) / 1000)),
      };
      if (!deletedRef.current.has(convId)) {
        // 持久化写入最终值; UI 的引用/建议/摘要由 flushMeta(正文打字机完成)显示,
        // 不以连接关闭时刻为准(后处理 LLM 快慢不定 => "提前跳出, 时有时无"根因)
        patchMessageLocal(convId, mid, m => ({ ...m, ...extra, typing: false, streaming: false, curThought: null, duration_seconds: finalMsg.duration_seconds }));
        conversationStore.appendMessage(convId, finalMsg);
        if (metaFlushed) renderMeta();   // 正文已打完: 最终值(含规则版兜底)同步到 UI, 与持久化一致
      }
    };

    try {
      const resp = await fetch(`${getApiBase()}/api/agent/stream_lg`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...(token ? { 'Authorization': 'Bearer ' + token } : {}) },
        body: JSON.stringify({ message: text, history, agent, language: lang, conversation_id: convId, message_id: mid }),
        signal: controller.signal,
      });
      const reader = resp.body.getReader();
      const decoder = new TextDecoder();
      let buf = '';
      // 事件: status / thought_stream / thought / tool_start / tool / tool_cancel /
      //        token / answer_retract / done / suggestions / reasoning_summary / error
      /* 思考打字机泵: 队列串行播放（下一条等上一条打完）; 逐字流写入 UI 占位行 */
      const pumpThinkQueue = (convId, mid) => {
        if (thinkPlayingRef.current.has(convId)) return;
        const q = thinkQueueRef.current.get(convId);
        if (!q || !q.list.length) return;
        thinkPlayingRef.current.add(convId);
        let text = q.list.shift();
        let i = 0;
        const timer = setInterval(() => {
          if (deletedRef.current.has(convId)) { clearInterval(timer); thinkPlayingRef.current.delete(convId); return; }
          i += Math.max(1, Math.min(8, Math.ceil((text.length - i) / 40)));
          const slice = text.slice(0, Math.min(i, text.length));
          patchMessageLocal(convId, mid, m => {
            const evs = (m.events || []).slice();
            let idx = -1;
            for (let k = evs.length - 1; k >= 0; k--) {
              if (evs[k] && evs[k].t === 'thinking_summary' && evs[k].content === '') { idx = k; break; }
            }
            if (idx < 0) return m;
            evs[idx] = { t: 'thinking_summary', content: slice, phase: evs[idx].phase };
            return { ...m, events: evs };
          });
          if (i >= text.length) {
            clearInterval(timer);
            thinkPlayingRef.current.delete(convId);
            setTimeout(() => pumpThinkQueue(convId, mid), 0);
          }
        }, 16);
      };

      const handleEvent = (evt) => {
        if (evt.type === 'status') {
          snap.status = evt.content;
          patchMessageLocal(convId, mid, m => ({ ...m, status: evt.content }));
        } else if (evt.type === 'thought') {
          snap.events = [...snap.events, { t: 'thought', text: evt.content }];
          patchMessageLocal(convId, mid, m => ({ ...m, curThought: null, events: [...m.events, { t: 'thought', text: evt.content }] }));
        } else if (evt.type === 'thought_stream') {
          snap.curThought = (snap.curThought || '') + evt.content;
          patchMessageLocal(convId, mid, m => ({ ...m, curThought: (m.curThought || '') + evt.content }));
        } else if (evt.type === 'tool_start') {
          snap.events = [...snap.events.filter(e => !(e.t === 'tool_start' && e.name === evt.name)), { t: 'tool_start', name: evt.name }];
          patchMessageLocal(convId, mid, m => ({
            ...m, curThought: null,
            events: [...m.events, ...(m.curThought ? [{ t: 'thought', text: m.curThought }] : []), { t: 'tool_start', name: evt.name }],
          }));
        } else if (evt.type === 'tool') {
          const done = { t: 'tool', tc: { name: evt.name, args: evt.args, result_summary: evt.result, thought: evt.thought } };
          snap.events = [...snap.events.filter(e => !(e.t === 'tool_start' && e.name === evt.name)), done];
          patchMessageLocal(convId, mid, m => ({ ...m, curThought: null, events: m.events.map(ev =>
            ev.t === 'tool_start' && ev.name === evt.name ? done : ev) }));
        } else if (evt.type === 'tool_cancel') {
          snap.events = [...snap.events.filter(e => !(e.t === 'tool_start' && e.name === evt.name)), { t: 'tool_cancel', name: evt.name, reason: evt.reason || '未执行，已跳过' }];
          patchMessageLocal(convId, mid, m => ({ ...m, events: m.events.map(ev =>
            ev.t === 'tool_start' && ev.name === evt.name ? { t: 'tool_cancel', name: evt.name, reason: evt.reason || '未执行，已跳过' } : ev) }));
        } else if (evt.type === 'answer_retract') {
          const retracted = evt.content || '';
          if (!retracted) return;
          if (tokenBuf.length >= retracted.length) {
            tokenBuf = tokenBuf.slice(0, tokenBuf.length - retracted.length);
          } else {
            const renderedPart = retracted.length - tokenBuf.length;
            tokenBuf = '';
            snap.content = snap.content.slice(0, Math.max(0, snap.content.length - renderedPart));
            snap.events = [...snap.events, { t: 'thought', text: retracted }];
            patchMessageLocal(convId, mid, m => ({
              ...m,
              content: m.content.slice(0, Math.max(0, m.content.length - renderedPart)),
              events: [...m.events, { t: 'thought', text: retracted }],
            }));
          }
        } else if (evt.type === 'token') {
          tokenBuf += evt.content;   // 入队, 打字机节奏渲染
        } else if (evt.type === 'done') {
          doneArrived = true;
          if (evt.safety === 'blocked') {
            tokenBuf = '';
            snap.content = evt.safety_reply || '';
          }
          // 2026-08-29: done 到达时正文打字机仍在渲染——citations/建议此时挂载会"提前悬空弹出"。
          // 引用与建议均暂存, 等连接关闭(finalize, 正文渲染完整)后一次性显示 + 持久化。
          snap.citations = evt.citations || [];
          snap.evidence = evt.evidence || null;
          snap.reasoning_summary = evt.reasoning_summary || null;
          snap.ruleSuggestions = evt.suggestions || [];
          snap.suggestions = [];
          snap.safety = evt.safety || null;
          patchMessageLocal(convId, mid, m => ({
            ...m,
            citations: [],
            evidence: snap.evidence,
            reasoning_summary: snap.reasoning_summary,
            suggestions: snap.suggestions,
            safety: snap.safety,
            content: evt.safety === 'blocked' && evt.safety_reply ? evt.safety_reply : m.content,
            events: (m.curThought ? [...m.events, { t: 'thought', text: m.curThought }] : m.events).map(ev =>
              ev.t === 'tool_start' ? { t: 'tool_cancel', name: ev.name, reason: '未执行，已跳过' } : ev),
            curThought: null, streaming: false,
          }));
        } else if (evt.type === 'suggestions') {
          // 先暂存; 正文打字机完成(flushMeta)时统一显示; 正文已打完则幂等直接显示(非空才渲染, 防覆盖)
          snap.suggestions = evt.suggestions || [];
          if (metaFlushed && snap.suggestions.length) renderMeta();
        } else if (evt.type === 'reasoning_summary') {
          snap.reasoning_summary = evt.content || null;
          if (metaFlushed) renderMeta();
        } else if (evt.type === 'thinking_summary') {
          // 开条（后端流式首事件; content 可能为空占位, 后续 delta 逐字填充）
          const line = { t: 'thinking_summary', phase: evt.phase || undefined, content: String(evt.content || '') };
          snap.events = [...snap.events, line];
          patchMessageLocal(convId, mid, m => ({ ...m, curThought: null, events: [...m.events, line] }));
        } else if (evt.type === 'thinking_summary_delta') {
          // 逐字增量: 追加到最后一条 thinking_summary（与回答打字机同节奏流式流入）
          const delta = String(evt.content || '');
          if (!delta) return;
          snap.events = snap.events.map((e, k, arr) => {
            let li = -1;
            for (let j = arr.length - 1; j >= 0; j--) if (arr[j] && arr[j].t === 'thinking_summary') { li = j; break; }
            return (k === li) ? { ...e, content: (e.content || '') + delta } : e;
          });
          patchMessageLocal(convId, mid, m => {
            const evs = (m.events || []).slice();
            let li = -1;
            for (let j = evs.length - 1; j >= 0; j--) if (evs[j] && evs[j].t === 'thinking_summary') { li = j; break; }
            if (li < 0) return m;
            evs[li] = { ...evs[li], content: (evs[li].content || '') + delta };
            return { ...m, events: evs };
          });
        } else if (evt.type === 'tool_note') {
          // 工具动作弱级注记（确定性意图/结果解读; 非 thinking 冒充）
          const line = { t: 'tool_note', text: evt.content };
          snap.events = [...snap.events, line];
          patchMessageLocal(convId, mid, m => ({ ...m, curThought: null, events: [...m.events, line] }));
        } else if (evt.type === 'error') {
          snap.content = evt.content;
          patchMessageLocal(convId, mid, m => ({ ...m, content: evt.content, streaming: false }));
        }
      };
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buf += decoder.decode(value, { stream: true });
        let idx;
        while ((idx = buf.indexOf('\n\n')) >= 0) {
          const raw = buf.slice(0, idx); buf = buf.slice(idx + 2);
          if (!raw.startsWith('data: ')) continue;
          try { handleEvent(JSON.parse(raw.slice(6))); } catch (e) { /* 忽略坏事件 */ }
          await new Promise(r => setTimeout(r, 0));   // 每个事件单独渲染（打字机节奏）
        }
      }
      finalize();
    } catch (e) {
      if (e.name === 'AbortError') {
        finalize();   // 主动停止: 保留已生成内容
      } else {
        snap.content = `${t('reqFail')}: ${e.message}`;
        finalize();
      }
    }
  };

  // "可继续探索"（§10）: 未主动切换 → 沿用来源回答的 agent_id; 已切换 → 当前 Composer Agent
  const handleSuggestion = (text, sourceMsg) => {
    const agent = resolveFollowupAgent(selectorTouched, composerAgent, sourceMsg?.agent_id);
    setComposerAgent(agent);
    dispatchSend({ message: text, display: text, agentOverride: agent });
  };

  // 稳定回调引用: MessageBubble 是 memo 组件, 流式 tick 期间若 onSend 引用每帧重建,
  // 所有历史消息都会随之重渲染(流式卡顿源之一)
  const sendRef = useRef(null);
  sendRef.current = (text, sourceMsg) =>
    sourceMsg ? handleSuggestion(text, sourceMsg) : dispatchSend({ message: text, display: text, agentOverride: composerAgent });
  const stableOnSend = useCallback((text, sourceMsg) => sendRef.current(text, sourceMsg), []);

  const handleComposerSend = ({ message, display, localOnly = false, attachments = [] }) =>
    dispatchSend({ message, display, localOnly, attachments });

  /* ── 空状态（§23: 简洁, Composer 近中心; Agent 依 Composer 选择变化） ── */
  const emptyState = (() => {
    const name = agentName(composerAgent) || '深哲';
    const sub = agentSub(composerAgent) || '';
    if (composerAgent !== 'general') {
      return (
        <div className="cw-empty">
          <Icon name="icon-brain" size={38} />
          <div className="cw-empty-title" style={{ marginTop: 12 }}>{name}</div>
          {sub && <div className="cw-empty-sub">{sub}</div>}
          <div className="cw-empty-starters" style={{ flexDirection: 'column', maxWidth: 420 }}>
            {(QUESTION_BANK[composerAgent]?.[lang] || []).map((q, i) => (
              <button key={i} className="cw-empty-chip" onClick={() => dispatchSend({ message: q, display: q })}>
                {q}
              </button>
            ))}
          </div>
        </div>
      );
    }
    const starters = [
      ['oneConcept', t('emptyConcept')],
      ['book', t('emptyBook')],
      ['compare', t('emptyCompare')],
    ];
    return (
      <div className="cw-empty">
        <Icon name="icon-brain" size={38} />
        <div className="cw-empty-title" style={{ marginTop: 12 }}>{name}</div>
        <div className="cw-empty-sub">{t('emptyGreeting')}</div>
        <div className="cw-empty-starters">
          {starters.map(([k, label]) => (
            <button key={k} className="cw-empty-chip" onClick={() => document.querySelector('.cw-composer textarea')?.focus()}>
              {label}
            </button>
          ))}
        </div>
      </div>
    );
  })();

  /* ── 渲染 ── */
  if (hydrateError) {
    return (
      <div style={{ padding: '60px 20px', textAlign: 'center', color: 'var(--text-dim)' }}>
        <div>{t('loadFail')}</div>
        <button onClick={loadConversations} style={{ marginTop: 12, padding: '8px 18px', borderRadius: 8,
                 cursor: 'pointer', border: '1px solid var(--border)', background: 'var(--card-bg)', color: 'var(--text)' }}>
          {t('retry')}
        </button>
      </div>
    );
  }
  if (!hydrated) {
    return <div style={{ padding: '60px 20px', textAlign: 'center', color: 'var(--text-dim)' }}>…</div>;
  }
  if (conversationId && !activeConv) {
    return (
      <div className="cw-root">
        <ConversationSidebar conversations={conversations} activeId={conversationId} streamingIds={streamingIds}
          collapsed={sidebarCollapsed} open={navOpen} onClose={() => setNavOpen(false)} onSelect={handleSelect} onNew={handleNew}
          onExplore={() => setPlazaOpen(true)} onRename={handleRename} onDelete={handleDelete}
          onOpenSettings={() => setSettingsOpen(true)} />
        <div className="cw-main" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }}>
          <div style={{ textAlign: 'center', color: 'var(--text-dim)' }}>
            <div style={{ fontSize: 16, marginBottom: 8 }}>{t('convNotFound')}</div>
            <button onClick={handleNew} style={{ padding: '8px 18px', borderRadius: 8, cursor: 'pointer',
                     border: '1px solid var(--border)', background: 'var(--card-bg)', color: 'var(--text)' }}>
              ＋ {t('newChat')}
            </button>
          </div>
        </div>
        <AgentPlaza open={plazaOpen} onClose={() => setPlazaOpen(false)} agents={agents} loading={agentsLoading} onPick={handlePickAgent} />
        <SettingsPanel open={settingsOpen} onClose={() => setSettingsOpen(false)} conversation={null} />
      </div>
    );
  }

  const messages = (activeConv?.messages || []).filter(m => m && m.content !== undefined);
  const unavailable = !agentsLoading && !(agents || []).some(a => a.key === composerAgent);

  return (
    <div className="cw-root">
      <ConversationSidebar conversations={conversations} activeId={conversationId || null} streamingIds={streamingIds}
        collapsed={sidebarCollapsed} open={navOpen} onClose={() => setNavOpen(false)} onSelect={handleSelect} onNew={handleNew}
        onExplore={() => setPlazaOpen(true)} onRename={handleRename} onDelete={handleDelete}
        onOpenSettings={() => setSettingsOpen(true)} />
      <div className="cw-main">
        <ConversationHeader title={activeConv?.title || (isDraft ? t('newChat') : '')} isDraft={isDraft}
          streaming={activeStreaming} onOpenNav={() => setNavOpen(true)} onToggleSidebar={handleToggleSidebar}
          onRename={(newTitle) => activeConv && handleRename(activeConv, newTitle)}
          onDelete={() => activeConv && handleDelete(activeConv)} />
        <div className="cw-messages">
          {unavailable && (
            <div style={{ marginBottom: 10, padding: '8px 12px', borderRadius: 8, fontSize: 12.5,
                          border: '1px solid var(--border)', background: 'var(--soft)', color: 'var(--text-dim)' }}>
              ⚠ {t('agentUnavailable')}
            </div>
          )}
          <MessageList
            messages={messages}
            agents={agents}
            emptyState={emptyState}
            conversationKey={conversationId || DRAFT_ID}
            prefsTick={prefsTick}
            onSend={stableOnSend}
            onDrawioEdit={openDrawio}
          />
        </div>
      </div>
      <Composer agents={agents} agent={composerAgent} onAgentChange={handleSelectorChange}
        onSend={handleComposerSend} streaming={activeStreaming}
        onStop={() => streamsRef.current.get(conversationId)?.controller.abort()}
        onExplore={() => setPlazaOpen(true)}
        unavailable={unavailable} resetKey={scopeKey} autoFocus={isDraft}
        dockLeft={sidebarCollapsed ? 0 : undefined} />
      <AgentPlaza open={plazaOpen} onClose={() => setPlazaOpen(false)} agents={agents} loading={agentsLoading} onPick={handlePickAgent} />
      <SettingsPanel open={settingsOpen} onClose={() => { setSettingsOpen(false); setPrefsTick(v => v + 1); }} conversation={activeConv} />
      {drawio && <DrawioModal xml={drawio.xml} onClose={closeDrawio} />}
    </div>
  );
}
