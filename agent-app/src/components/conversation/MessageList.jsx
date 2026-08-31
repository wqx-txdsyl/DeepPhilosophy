import { useState, useRef, useEffect, memo } from 'react';
import {
  Check, Loader2, XCircle, ChevronRight, ChevronDown, ArrowDown, Image as ImageIcon,
  FileText, FileType, File as FileIcon, CornerDownRight, Search, Quote, ListTree,
} from 'lucide-react';
import Icon from '../Icon';
import { useLang } from '../../utils/i18n';
import { renderMarkdown } from './markdown';
import { DP_READER, resolveCite, resolvePortrait } from '../../utils/api';
import { pickUsedEvidence } from '../../utils/evidence';
import {
  resolveIdentityVisible, toolShortSummary, toolShortArgs, toolHumanSummary,
  isRetrievalTool, retrievalGroupSummary, cleanUserMessageForRender,
} from '../../data/conversationLogic';
import { getPref } from '../../data/localPrefs';

/**
 * MessageList — Conversation 消息区（spec §8/§9/§10/§18-§22）
 *
 * 身份规则: 历史回答身份只来自 message.agent_id（resolveIdentityVisible, 与全局
 * currentAgent 无关）。Tool/Evidence/Citation 全部归属单条 message。
 *
 * 2026-08-29 性能: 每条消息渲染抽成 memo 组件——流式 tick(12ms)只重渲正在变化的
 * 那条消息, 历史消息不再每 tick 重跑 renderMarkdown。
 * 2026-08-31 Codex-Parity 重构: 无 raw chain-of-thought（thought 事件不渲染文本,
 * 仅保留状态行与后端 reasoning_summary）; Tool 收敛为紧凑 trace; 引用为低干扰 chips。
 */

const TOOL_META = {
  search_books: { icon: 'icon-search', label: '检索原典' },
  get_chapter: { icon: 'icon-book-open', label: '读取章节' },
  get_book_detail: { icon: 'nav-books', label: '查书详情' },
  query_graph: { icon: 'nav-genealogy', label: '查询星丛' },
  get_philosopher: { icon: 'nav-authors', label: '查哲人资料' },
  list_books: { icon: 'nav-books', label: '筛选书目' },
  get_school: { icon: 'nav-genealogy', label: '查询流派' },
  compare_views: { icon: 'icon-calc', label: '观点对比' },
  write_essay: { icon: 'icon-clipboard', label: '撰写作文' },
  phti_test: { icon: 'icon-brain', label: '人格测试' },
  philosopher_debate: { icon: 'icon-drama', label: '哲学辩论' },
  thought_experiment: { icon: 'icon-flame', label: '思想实验' },
  advisor_council: { icon: 'icon-candle', label: '智者内阁' },
  paper_review: { icon: 'icon-edit', label: '论文评审' },
  generate_image: { icon: 'icon-candle', label: '概念生图' },
  websearch: { icon: 'icon-search', label: '上网搜索' },
  query_database: { icon: 'icon-clipboard', label: '数据库查询' },
  socratic_tutor: { icon: 'icon-thinking', label: '苏格拉底追问' },
  analyze_argument: { icon: 'icon-calc', label: '论证分析' },
  concept_trace: { icon: 'icon-link', label: '概念溯源' },
  conceptual_map: { icon: 'nav-genealogy', label: '概念脑图' },
  confrontation: { icon: 'icon-handshake', label: '原文对质' },
  dialectic: { icon: 'icon-target', label: '辩证分析' },
  essay_outline: { icon: 'icon-clipboard', label: '论文大纲' },
  history_timeline: { icon: 'icon-calendar', label: '历史脉络' },
  life_coach: { icon: 'icon-tip', label: '人生疏导' },
  profile: { icon: 'nav-authors', label: '人格档案' },
  role_play: { icon: 'icon-drama', label: '角色扮演' },
  school_arena: { icon: 'icon-crazy', label: '流派PK' },
  agent_council: { icon: 'icon-bot', label: '智能体协作' },
};

/* ── 附件卡（user message 持久化 metadata 渲染; 与 draft 卡同构低干扰） ── */
function AttachIcon({ kind }) {
  if (kind === 'image') return <ImageIcon size={14} />;
  if (kind === 'markdown') return <FileText size={14} />;
  if (kind === 'text') return <FileType size={14} />;
  return <FileIcon size={14} />;
}
function MessageAttachmentCards({ attachments }) {
  if (!attachments?.length) return null;
  return (
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, margin: '0 0 8px' }}>
      {attachments.map((a, i) => (
        <span key={i} className="cw-attach-card" style={{ padding: '5px 9px', fontSize: 12 }}>
          <span className="cw-attach-icon"><AttachIcon kind={a.kind} /></span>
          <span style={{ maxWidth: 220, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{a.filename}</span>
        </span>
      ))}
    </div>
  );
}

/* ── 工具轨迹（P0 三级披露; 无 raw CoT; 生产默认禁止 raw JSON/dict） ──
 * Level 1 默认: 用户可理解的动作摘要（检索类连续合并「已查阅了 N 项资料」）。
 * Level 2 展开: friendly name + concise result summary + evidence/source + status。
 * Level 3 Debug: raw args/result 仅开发/debug 模式（?debug=1）显示。
 */
const CAN_DEBUG = import.meta.env.DEV || /[?&]debug(?:=1)?([#&]|$)/.test(window.location.search);

function ToolTrace({ events, streaming }) {
  const { t, toolLabel } = useLang();
  const [openSet, setOpenSet] = useState(() => {
    const s = new Set();
    if (getPref('toolTraceOpen')) (events || []).forEach((ev, i) => { if (ev?.t === 'tool') s.add(i); });
    return s;
  });
  const toggle = (i) => setOpenSet(prev => { const n = new Set(prev); if (n.has(i)) n.delete(i); else n.add(i); return n; });
  if (!events.length) return null;

  const rows = events
    .map((ev, i) => (ev.t !== 'tool' && ev.t !== 'tool_start' && ev.t !== 'tool_cancel' ? null : { ev, i }))
    .filter(Boolean);
  if (!rows.length) return null;

  /* 工具名位置: tool_start/tool_cancel 在 ev.name; 完成的 tool 事件在 ev.tc.name */
  const toolName = (ev) => ev.tc?.name || ev.name;

  /* 分组: 仅消息 final 时把相邻检索类工具合并为 Level 1 摘要行;
     streaming 期间逐行渲染, tool 状态实时更新（回归 3）。 */
  const finalize = !streaming;
  const groups = [];
  let pending = null;
  const flushPending = () => { if (pending) { groups.push(pending); pending = null; } };
  for (const row of rows) {
    const { ev } = row;
    if (ev.t !== 'tool') { flushPending(); groups.push({ key: ev.i, kind: ev.t, items: [row] }); continue; }
    if (finalize && isRetrievalTool(toolName(ev))) {
      if (pending && pending.kind === 'merged') { pending.items.push(row); continue; }
      flushPending();
      pending = { key: ev.i, kind: 'merged', items: [row] };
      continue;
    }
    flushPending();
    groups.push({ key: ev.i, kind: 'tool', items: [row] });
  }
  flushPending();

  /* Level 2 展开行（friendly name + concise summary + evidence + status; raw 仅 Debug） */
  const renderDetail = (row, idx) => {
    const { ev } = row;
    const tc = ev.tc || {};
    const label = toolLabel(toolName(ev)) || toolName(ev);
    const short = toolShortSummary(tc) || toolShortArgs(tc.args);
    const evidence = _toolEvidence(tc.args);
    const isErr = /错误|失败|error|fail/i.test(tc.result_summary || '');
    return (
      <div key={ev.i} style={{ borderTop: '1px solid var(--border)', padding: '8px 12px' }}>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
          <span style={{ fontSize: 10.5, color: 'var(--text-dim)', fontFamily: 'ui-monospace, monospace', flexShrink: 0 }}>
            {String(idx + 1).padStart(2, '0')}
          </span>
          <span style={{ fontWeight: 600, fontSize: 12.5 }}>{label}</span>
          <span className="cw-tool-status">
            {isErr
              ? <span style={{ color: '#b4544a', display: 'inline-flex', alignItems: 'center', gap: 4 }}><XCircle size={11} /> {t('toolError')}</span>
              : <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4, color: 'var(--text-dim)' }}><Check size={11} /> {t('toolDone')}</span>}
          </span>
        </div>
        {short && <div className="cw-tool-summary" style={{ marginTop: 4, whiteSpace: 'normal' }}>{short}</div>}
        {evidence && (
          <div style={{ marginTop: 3, fontSize: 11.5, color: 'var(--text-dim)', display: 'flex', alignItems: 'center', gap: 4 }}>
            <Icon name="nav-books" size={11} /> {evidence}
          </div>
        )}
        {/* Level 3 Debug（仅 dev / ?debug=1）: raw args/result */}
        {CAN_DEBUG && (Object.keys(tc.args || {}).length > 0 || tc.result_summary) && (
          <details style={{ marginTop: 6 }}>
            <summary style={{ fontSize: 11, color: 'var(--text-dim)', cursor: 'pointer', userSelect: 'none' }}>
              ≡ raw ({idx + 1})
            </summary>
            {Object.keys(tc.args || {}).length > 0 && <pre className="cw-tool-detail-pre">{JSON.stringify(tc.args, null, 2)}</pre>}
            {tc.result_summary && <pre className="cw-tool-detail-pre">{tc.result_summary}</pre>}
          </details>
        )}
      </div>
    );
  };

  let count = 0;
  return (
    <div className="cw-tool-trace">
      {groups.map((g) => {
        const { ev: rEv } = g.items[0];
        const rName = toolName(rEv);
        const meta = TOOL_META[rName] || null;
        const label = toolLabel(rName) || rName;
        if (g.kind === 'tool_start') {
          return (
            <div key={rEv.i} className="cw-tool-run-row">
              <Loader2 size={13} className="cw-spinner" aria-hidden />
              <Icon name={meta?.icon || 'icon-cog'} size={14} />
              <span>{t('calling')} {label}…</span>
            </div>
          );
        }
        if (g.kind === 'tool_cancel') {
          return (
            <div key={rEv.i} className="cw-tool-run-row" style={{ borderTop: 'none' }}>
              <XCircle size={13} aria-hidden />
              <Icon name={meta?.icon || 'icon-cog'} size={14} />
              <span>{label} — {rEv.reason || t('toolSkipped')}</span>
            </div>
          );
        }
        if (g.kind === 'merged') {
          const isOpen = openSet.has(g.key);
          const idx = count;
          count += g.items.length;
          return (
            <div key={g.key}>
              <div className="cw-tool-trace-head" role="button" tabIndex={0}
                aria-expanded={isOpen}
                onClick={() => toggle(g.key)}
                onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); toggle(g.key); } }}>
                <Icon name="icon-search" size={15} />
                <span className="cw-tool-name" style={{ fontWeight: 500 }}>{retrievalGroupSummary(g.items.length)}</span>
                <span className="cw-tool-summary" />
                <span className="cw-tool-status">
                  <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4, color: 'var(--text-dim)' }}><Check size={11} /> {t('toolDone')}</span>
                </span>
                {isOpen ? <ChevronDown size={13} /> : <ChevronRight size={13} />}
              </div>
              {isOpen && g.items.map((r) => renderDetail(r, idx + 1))}
            </div>
          );
        }
        // 单工具（Level 1 人话摘要 + 可展开 Level 2）
        const isOpen = openSet.has(rEv.i);
        const tc = rEv.tc || {};
        const human = toolHumanSummary(toolName(rEv), tc.args, toolShortSummary(tc));
        const isErr = /错误|失败|error|fail/i.test(tc.result_summary || '');
        const idx = count++;
        return (
          <div key={rEv.i}>
            <div className="cw-tool-trace-head" role="button" tabIndex={0}
              aria-expanded={isOpen}
              onClick={() => toggle(rEv.i)}
              onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); toggle(rEv.i); } }}>
              <span className="cw-tool-idx">{String(idx + 1).padStart(2, '0')}</span>
              <Icon name={meta?.icon || 'icon-cog'} size={15} />
              <span className="cw-tool-name">{human || label}</span>
              <span className="cw-tool-summary">{human ? '' : (toolShortSummary(tc) || '—')}</span>
              <span className="cw-tool-status">
                {isErr
                  ? <span style={{ color: '#b4544a' }}><XCircle size={11} /> {t('toolError')}</span>
                  : <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}><Check size={11} /> {t('toolDone')}</span>}
              </span>
              {isOpen ? <ChevronDown size={13} /> : <ChevronRight size={13} />}
            </div>
            {isOpen && renderDetail(rEv, idx)}
          </div>
        );
      })}
    </div>
  );
}

/* Level 2 evidence/source（仅实体字段; 禁止 book_id/chapter_idx 等内部字段） */
function _toolEvidence(args) {
  const a = args || {};
  const book = typeof a.book === 'string' && a.book ? a.book
    : (typeof a.book_title === 'string' ? a.book_title : '');
  const chapter = typeof a.chapter === 'string' ? a.chapter : '';
  return book ? `《${book}${chapter ? `·${String(chapter).slice(0, 12)}` : ''}》` : '';
}

/* ── 引用来源 chips（§20/§21: 仅 used_evidence; 可点击跳阅读器; 低干扰） ── */
const EVIDENCE_PREVIEW = 5;   // 低干扰: 默认最多 5 个 chip（§21 Evidence Without Noise）

function EvidenceChips({ citations, evidence }) {
  const { t } = useLang();
  const used = pickUsedEvidence(citations);
  // 单一 source of truth（P0-2）: citationExpanded 控制 collapsed/expanded 两态
  const [citationExpanded, setCitationExpanded] = useState(false);
  if (!used.length) return null;
  const rCount = evidence?.retrieved_count;
  const shown = citationExpanded ? used : used.slice(0, EVIDENCE_PREVIEW);
  const rest = used.length - EVIDENCE_PREVIEW;
  return (
    <div className="cw-evidence">
      <span className="cw-evidence-cap">
        <Quote size={11} /> {t('citations')}
        {rCount != null && rCount !== used.length
          ? ` · ${t('verifiedCount', { a: used.length, b: rCount })}`
          : ` · ${used.length}`}
      </span>
      {shown.map((c, i) => <CiteChip key={c.evidence_id || i} c={c} />)}
      {!citationExpanded && rest > 0 && (
        <button className="cw-cite-more" onClick={() => setCitationExpanded(true)}
          aria-label={t('expandCitations', { a: used.length })}>
          +{rest}
        </button>
      )}
      {citationExpanded && rest > 0 && (
        <button className="cw-cite-more" onClick={() => setCitationExpanded(false)}
          aria-label={t('citationCollapse')}>
          {t('citationCollapse')}
        </button>
      )}
    </div>
  );
}

function CiteChip({ c }) {
  const { t } = useLang();
  const [loading, setLoading] = useState(false);
  const [failed, setFailed] = useState(false);
  const openCite = () => {
    if (loading || failed) return;
    setLoading(true);
    resolveCite(c.book, c.chapter || '')
      .then(d => {
        setLoading(false);
        if (d.error || d.matched === false) { setFailed(true); return; }
        window.open(`${DP_READER}/${d.book_id}?ch=${d.chapter_idx || 0}`, '_blank');
      })
      .catch(() => { setLoading(false); setFailed(true); });
  };
  return (
    <button className={`cw-cite-chip${failed ? ' cw-cite-chip-fail' : ''}`}
      onClick={openCite} title={failed ? t('citeFail') : t('citeOpen')}
      aria-label={`${t('citeOpen')}: ${c.book}` + (c.chapter ? ` · ${c.chapter}` : '')}>
      <Search size={11} aria-hidden />
      <span className="cw-cite-chip-title">《{c.book}》{c.chapter ? `· ${c.chapter}` : ''}</span>
      {loading ? <Loader2 size={11} className="cw-spinner" /> : null}
    </button>
  );
}

/* ── 剥离残留的工具调用标记（后端分块/LLM 异常时可能漏出） ── */
const cleanContent = (text) => (text || '')
  .replace(/<tool_calls>[\s\S]*?<\/tool_calls>/g, '')
  .replace(/<invoke name="[^"]+">[\s\S]*?<\/invoke>/g, '')
  .replace(/\{TOOL:[\s\S]*?\}/g, '');

/* ── AgentIdentity（§10: 依 resolveIdentityVisible 决定是否显示; 始终来自 message.agent_id） ── */
function AgentIdentity({ agentId, agents }) {
  const { agentName, agentSub } = useLang();
  const spec = (agents || []).find((a) => a.key === agentId);
  const name = agentName(agentId) || spec?.name || agentId;
  const portrait = resolvePortrait(spec?.portrait);
  return (
    <div className="cw-agent-identity">
      {portrait ? (
        <img className="cw-agent-avatar" src={portrait} alt="" />
      ) : (
        <span className="cw-agent-avatar-fallback">{(name || '?')[0]}</span>
      )}
      <span className="cw-agent-name">{name}</span>
      {agentSub(agentId) && <span className="cw-agent-sub">{agentSub(agentId)}</span>}
    </div>
  );
}

/* ── Work Panel（P0-1: Work Summary + Tool Trace 同一 compact panel） ──
 * 用户可见的 structured work summary / execution rationale（非 raw CoT）:
 * - streaming 时: status（正在理解/正在检索…）+ tool run 行实时更新, panel 默认展开
 * - final 后: 默认折叠为一行「工作摘要」, 展开可见 reasoning bullets + tool trace
 * 无工具且无 reasoning 时整个 panel 不渲染（不造假, T2）。
 */
function WorkPanel({ m, prefsTick }) {
  const { t } = useLang();
  const [open, setOpen] = useState(() => !!m.streaming);   // streaming 展示; final 折叠
  useEffect(() => { if (m.streaming) setOpen(true); }, [m.streaming]);
  const events = (m.events ?? m.tool_events ?? []).filter(ev => ev?.t !== 'thought');   // §18 无 raw CoT
  const toolRows = events.filter(ev => ev.t === 'tool' || ev.t === 'tool_start' || ev.t === 'tool_cancel').length;
  const reasoning = m.reasoning_summary ? String(m.reasoning_summary).split('\n').filter(Boolean) : [];
  if (!toolRows && !reasoning.length) return null;
  const thinking = m.streaming && !m.content;
  return (
    <div className="cw-work-panel">
      <button className="cw-work-panel-head" aria-expanded={open}
        onClick={() => setOpen(o => !o)}>
        <ListTree size={13} aria-hidden />
        <span className="cw-work-panel-title">{t('workSummary')}</span>
        {toolRows > 0 && <span className="cw-work-panel-badge">{toolRows}</span>}
        <span style={{ flex: 1 }} />
        {open ? <ChevronDown size={13} /> : <ChevronRight size={13} />}
      </button>
      {open && (
        <div className="cw-work-panel-body">
          {thinking && (
            <div className="cw-status-line" style={{ margin: 0, padding: '0 2px 8px' }}>
              <Loader2 size={12} className="cw-spinner" aria-hidden />
              {m.status ? m.status : t('startThinking')}…
            </div>
          )}
          {reasoning.length > 0 && (
            <div className="cw-work-reasoning">
              {reasoning.map((s, i) => <div key={i} className="cw-work-reasoning-line">{s}</div>)}
            </div>
          )}
          <ToolTrace events={events} streaming={!!m.streaming} key={prefsTick} />
        </div>
      )}
    </div>
  );
}

/* ── 单条消息（memo: 流式 tick 只重渲变化消息） ── */
const MessageBubble = memo(function MessageBubble({ m, agents, showIdentity, prefsTick, onDrawioEdit, onSend }) {
  const { t } = useLang();

  if (m.role === 'user') {
    // P0-3: visible content = structured attachment cards + 用户文本（legacy serialization 前缀保守 dedupe）
    const visibleText = cleanUserMessageForRender(m.content, m.attachments);
    return (
      <div className="cw-user-row">
        <div className="cw-user-bubble">
          <MessageAttachmentCards attachments={m.attachments} />
          {visibleText && renderMarkdown(visibleText, null, null, t)}
        </div>
      </div>
    );
  }

  return (
    <div className="cw-assistant">
      {showIdentity && <AgentIdentity agentId={m.agent_id} agents={agents} />}
      {m.safety === 'warning' && (
        <div className="cw-reasoning" style={{ marginTop: 0, color: 'var(--text-dim)' }}>{t('warning')}</div>
      )}
      <WorkPanel m={m} prefsTick={prefsTick} />
      <div style={{ lineHeight: 'var(--cw-line-body)', fontSize: 14.5 }}>
        {renderMarkdown(cleanContent(m.content), (code) => onDrawioEdit(m.message_id, code), m.drawioXml, t)}
        {m.streaming && m.content && (
          <span className="cw-stream-cursor" style={{ display: 'inline-block', width: 6, height: 14, marginLeft: 3,
            background: 'var(--accent)', animation: 'pulse 1s infinite', verticalAlign: 'middle' }} />
        )}
      </div>
      {getPref('showCitations') && <EvidenceChips citations={m.citations} evidence={m.evidence} />}
      {m.suggestions?.length > 0 && !m.streaming && (
        <div className="cw-followups">
          <div className="cw-followups-cap">{t('explore')}</div>
          {m.suggestions.map((s, i) => (
            <button key={i} className="cw-followup-chip" onClick={() => onSend(s, m)}>
              <CornerDownRight size={11} style={{ marginRight: 6, verticalAlign: '-2px', color: 'var(--text-dim)' }} aria-hidden />
              {s}
            </button>
          ))}
        </div>
      )}
    </div>
  );
});

export default function MessageList({
  messages, agents, emptyState, onSend, onDrawioEdit,
  conversationKey, prefsTick,
}) {
  const { t } = useLang();
  const bottomRef = useRef(null);
  const stickBottomRef = useRef(true);   // 用户上滑回读时不强行拽回（§29）
  const [stick, setStick] = useState(true);

  // 流式/打字机进行中自动跟随底部; 用户主动上滑 → 暂停; 回到底部附近 → 恢复
  useEffect(() => {
    if (stickBottomRef.current && messages.some(m => m.streaming || m.typing)) {
      bottomRef.current?.scrollIntoView({ behavior: 'auto' });
    }
    // mermaid 脑图渲染（动态加载; 补发事件也可能带来新节点）
    const nodes = document.querySelectorAll('.mermaid:not([data-processed])');
    if (nodes.length) {
      import('mermaid').then((mod) => {
        const mermaid = mod.default || mod;
        mermaid.initialize({ startOnLoad: false, theme: 'dark', securityLevel: 'strict' });
        return mermaid.run({ nodes });
      }).catch(() => {});
    }
  }, [messages]);

  // 切换会话 → 落到底部一次
  useEffect(() => {
    stickBottomRef.current = true; setStick(true);
    requestAnimationFrame(() => bottomRef.current?.scrollIntoView({ behavior: 'auto' }));
  }, [conversationKey]);

  // 用户主动上滑 → 暂停跟随; 回到底部附近 → 恢复（window 层滚动）
  useEffect(() => {
    const handleScroll = () => {
      const el = bottomRef.current;
      if (!el) return;
      const rect = el.getBoundingClientRect();
      const nearBottom = rect.top < window.innerHeight + 80;
      stickBottomRef.current = nearBottom;
      setStick(nearBottom);
    };
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // identity 计算: 依历史 assistant agent 序列（与当前选择无关, §10）
  let prevAssistants = [];
  const identityFlags = (messages || []).map((m) => {
    if (m.role !== 'assistant') return false;
    const flag = resolveIdentityVisible(prevAssistants, m.agent_id);
    prevAssistants = [...prevAssistants, m.agent_id];
    return flag;
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
      {!messages?.length && emptyState}
      {(messages || []).map((m, i) => (
        <MessageBubble key={m.message_id || i} m={m} agents={agents}
          showIdentity={identityFlags[i]} prefsTick={prefsTick}
          onDrawioEdit={onDrawioEdit} onSend={onSend} />
      ))}
      <div ref={bottomRef} />
      {!stick && messages?.length > 0 && (
        <button className="cw-jump-bottom" onClick={() => { stickBottomRef.current = true; setStick(true); bottomRef.current?.scrollIntoView({ behavior: 'auto' }); }}
          title={t('backToBottom')} aria-label={t('backToBottom')}>
          <ArrowDown size={15} />
        </button>
      )}
    </div>
  );
}

export { TOOL_META };

export const QUESTION_BANK = {
  general: {
    zh: ['永恒轮回是什么意思？尼采怎么说的', '休谟和康德对因果的看法有何不同？', '海德格尔受谁影响？', '推荐几本存在主义入门书'],
    en: ['What does the eternal recurrence mean? What did Nietzsche say about it?',
         'How do Hume and Kant differ on causality?', 'Who influenced Heidegger?',
         'Recommend a few books to start with existentialism'],
  },
  nietzsche: {
    zh: ['你怎么看待孤独？', '权力意志到底是什么？', '你会如何评价这个时代？', '永恒轮回意味着什么？'],
    en: ['How do you see solitude?', 'What exactly is the will to power?',
         'How would you judge this age?', 'What does eternal recurrence mean?'],
  },
};
