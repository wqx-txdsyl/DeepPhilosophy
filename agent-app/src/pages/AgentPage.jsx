import { useState, useRef, useEffect } from 'react';
import { getApiBase } from '../utils/api';
import Icon from '../components/Icon';
import { useAuth } from '../auth';
import { useLang } from '../utils/i18n';
import AuthModal from '../components/AuthModal';
import DrawioModal from '../components/DrawioModal';
import DrawioInline from '../components/DrawioInline';

/**
 * AgentPage — 哲学智能体"深哲"（ReAct 架构: 思考→行动→观察 循环可视化）
 * 纯对话页: 作文/生图/扮演等全部由 agent 自动触发工具, 无手动页签
 * 图标规范: 全部使用 /icons/*.png（Icon 组件）, 禁用 emoji
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
};

/* ── 工具调用卡片（ReAct: 思考 → 行动） ── */
function ToolCard({ tc, index }) {
  const { toolLabel } = useLang();
  const [open, setOpen] = useState(false);
  const meta = TOOL_META[tc.name] || { icon: 'icon-cog', label: tc.name };
  const label = toolLabel(tc.name) || meta.label;
  return (
    <div style={{ margin: '4px 0' }}>
      {/* 思考（Thought） */}
      {tc.thought && (
        <div style={{ fontSize: 12.5, color: 'var(--text-dim)', fontStyle: 'italic',
                      padding: '2px 4px 4px', lineHeight: 1.6 }}>
          {tc.thought}
        </div>
      )}
      {/* 行动（Action） */}
      <div style={{
        border: '1px solid var(--border)', borderRadius: 8,
        background: 'var(--card-bg)', overflow: 'hidden',
      }}>
        <div onClick={() => setOpen(!open)}
          style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '8px 12px',
                   cursor: 'pointer', userSelect: 'none' }}>
          <span style={{ fontSize: 11, color: 'var(--text-dim)', fontFamily: 'monospace', minWidth: 22 }}>
            {String(index + 1).padStart(2, '0')}
          </span>
          <Icon name={meta.icon} size={16} />
          <span style={{ fontSize: 13, fontWeight: 600 }}>{label}</span>
          <span style={{ flex: 1 }} />
          <span style={{ fontSize: 12, color: 'var(--text-dim)', fontFamily: 'monospace' }}>
            {Object.values(tc.args || {}).filter(v => typeof v === 'string').join(' ').slice(0, 40) || '—'}
          </span>
          <span style={{ fontSize: 10, color: 'var(--text-dim)', transform: open ? 'rotate(90deg)' : 'none', transition: 'transform .15s' }}>▶</span>
        </div>
        {open && (
          <div style={{ padding: '8px 12px', borderTop: '1px solid var(--border)', fontSize: 12 }}>
            <div style={{ color: 'var(--text-dim)', marginBottom: 4, fontFamily: 'monospace' }}>
              {JSON.stringify(tc.args, null, 2)}
            </div>
            <div style={{ color: 'var(--text-dim)', whiteSpace: 'pre-wrap', maxHeight: 160, overflow: 'auto' }}>
              {tc.result_summary}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

/* ── 出处跳转链接（【《书名》·章节】→ 点击跳 DeepPhilosophy 阅读器） ── */
const DP_READER = 'https://deepphilosophy.top/reader';
function CiteLink({ book, chapter }) {
  const { t } = useLang();
  const [loading, setLoading] = useState(false);
  const [failed, setFailed] = useState(false);
  const openCite = () => {
    if (loading) return;
    setLoading(true);
    setFailed(false);
    fetch(`${getApiBase()}/api/cite?book=${encodeURIComponent(book)}&chapter=${encodeURIComponent(chapter || '')}`)
      .then(r => r.json())
      .then(d => {
        setLoading(false);
        if (d.error) { setFailed(true); return; }
        // 跳转 DeepPhilosophy 阅读器（同源数据: book_id/chapter_idx 一致）
        window.open(`${DP_READER}/${d.book_id}?ch=${d.chapter_idx || 0}`, '_blank');
      })
      .catch(() => { setLoading(false); setFailed(true); });
  };
  return (
    <span onClick={openCite} title={failed ? t('citeFail') : t('citeOpen')}
      style={{ color: 'var(--accent)', textDecoration: 'underline dotted', cursor: 'pointer',
               textUnderlineOffset: '3px', whiteSpace: 'nowrap' }}>
      【《{book}》{chapter ? `·${chapter}` : ''}】{loading ? '…' : ''}
    </span>
  );
}

/* ── markdown 简易渲染 ── */
function renderInline(text, agent) {
  // 行内元素: **粗体** *斜体* `代码` [链接](url) ~~删除线~~ 【出处】
  const parts = (text || '').split(/(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`|\[[^\]]*\]\([^)]*\)|~~[^~]+~~|【[^】]+】)/g);
  return parts.map((p, i) => {
    if (p.startsWith('**') && p.endsWith('**')) return <strong key={i}>{p.slice(2, -2)}</strong>;
    if (p.startsWith('*') && p.endsWith('*') && p.length > 2) return <em key={i}>{p.slice(1, -1)}</em>;
    if (p.startsWith('`') && p.endsWith('`')) return <code key={i} style={{ background: 'var(--soft)', padding: '1px 5px', borderRadius: 4, fontSize: '0.92em' }}>{p.slice(1, -1)}</code>;
    const lm = p.match(/^\[([^\]]*)\]\(([^)]*)\)$/);
    if (lm) {
      const href = lm[2];
      if (/^(https?:|#|\/)/.test(href)) {
        return <a key={i} href={href} target="_blank" rel="noreferrer"
          style={{ color: 'var(--accent)', textDecoration: 'underline' }}>{lm[1]}</a>;
      }
      return lm[0];
    }
    if (p.startsWith('~~') && p.endsWith('~~')) return <del key={i} style={{ color: 'var(--text-dim)' }}>{p.slice(2, -2)}</del>;
    const cm = p.match(/^【《([^》]+)》·?([^】]*)】$/);
    if (cm) return agent !== 'general' ? null : <CiteLink key={i} book={cm[1]} chapter={cm[2]} />;
    const cm2 = p.match(/^【([^】]+)】$/);
    if (cm2) return agent !== 'general' ? null : <CiteLink key={i} book={cm2[1]} chapter="" />;
    return p;
  });
}

/* ── mermaid 代码清洗（LLM 常产出非法语法, 尽量救回来） ── */
function sanitizeMermaid(code) {
  let c = (code || '').replace(/\r/g, '');
  // 1) 引号内的裸换行 → <br/>（mermaid 节点文本不允许换行）
  c = c.replace(/"([^"]*)"/g, (m, inner) =>
    inner.includes('\n') ? '"' + inner.replace(/\n+/g, '<br/>') + '"' : m);
  // 2) 一行式 mindmap → 拆成多行（保护括号/引号内容不被空格拆碎; mindmap/root 关键字不缩进, 其余缩进为一级）
  const t = c.trim();
  if (/^mindmap\b/.test(t) && !t.includes('\n')) {
    const protectedParts = [];
    const masked = t.replace(/\(\([^)]*\)\)|"[^"]*"/g, m => {
      protectedParts.push(m);
      return `\x00${protectedParts.length - 1}\x00`;
    });
    const tokens = masked.split(/\s+/).map(tok =>
      tok.replace(/\x00(\d+)\x00/g, (_, idx) => protectedParts[+idx]));
    if (tokens.length > 1) {
      c = tokens.map((tok, idx) =>
        idx === 0 || tok.startsWith('root') ? tok : '  ' + tok).join('\n');
    }
  }
  return c;
}

const renderMermaid = (code, onEdit, drawioXml, t) => {
  if (drawioXml) {
    return <DrawioInline xml={drawioXml} onEdit={() => onEdit && onEdit(code)} />;
  }
  return (
  <div style={{ position: 'relative', margin: '10px 0' }}>
    <div className="mermaid"
      style={{ display: 'flex', justifyContent: 'center', overflowX: 'auto' }}>
      {sanitizeMermaid(code)}
    </div>
    {onEdit && (
      <button onClick={() => onEdit(code)} title={t ? t('drawioEdit') : 'draw.io edit'}
        style={{ position: 'absolute', top: 0, right: 0, fontSize: 11, cursor: 'pointer',
                 padding: '3px 8px', borderRadius: 6, border: '1px solid var(--border)',
                 background: 'var(--card-bg)', color: 'var(--text-dim)' }}>
        {t ? t('drawioEdit') : '✏️ draw.io'}
      </button>
    )}
  </div>
  );
};

/* ── markdown 表格渲染 ── */
function renderTable(headers, rows, agent) {
  return (
    <div key={`tbl${outSeq++}`} style={{ overflowX: 'auto', margin: '10px 0' }}>
      <table style={{ borderCollapse: 'collapse', width: '100%', fontSize: 13, lineHeight: 1.6 }}>
        <thead>
          <tr>{headers.map((h, i) => (
            <th key={i} style={{ border: '1px solid var(--border)', padding: '6px 10px',
                                background: 'var(--soft)', fontWeight: 600, textAlign: 'left' }}>
              {renderInline(h, agent)}
            </th>
          ))}</tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i}>{r.map((c, j) => (
              <td key={j} style={{ border: '1px solid var(--border)', padding: '6px 10px' }}>{renderInline(c, agent)}</td>
            ))}</tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

let outSeq = 0;
function renderMarkdown(text, agent, onEdit, drawioXml, t) {
  const lines = (text || '').split('\n');
  const out = [];
  let fence = null;         // 围栏语言（''=普通代码块, 'mermaid'=脑图）
  let fenceLines = [];
  const flushFence = () => {
    if (fence !== null) {
      const code = fenceLines.join('\n');
      if (fence === 'mermaid') {
        // mermaid 脑图: 由 useEffect 里 mermaid.run() 渲染成图形
        out.push(renderMermaid(code, onEdit, drawioXml, t));
      } else {
        out.push(<pre key={`p${out.length}`} style={{ background: 'var(--soft)', padding: '10px 12px', borderRadius: 8, overflowX: 'auto', fontSize: 12.5, lineHeight: 1.6 }}>{code}</pre>);
      }
      fenceLines = [];
    }
    fence = null;
  };
  let i = 0;
  while (i < lines.length) {
    const line = lines[i];
    const trimmed = line.trim();
    if (fence !== null) {
      if (trimmed.startsWith('```')) flushFence();
      else fenceLines.push(line);
      i++; continue;
    }
    const fm = trimmed.match(/^```(\w*)\s*$/);
    if (fm) { fence = fm[1] || ''; i++; continue; }
    // 裸 mermaid 块兜底: flowchart/graph/mindmap 开头 → 收集到空行为止, 按 mermaid 渲染（无围栏时）
    if (/^(flowchart|graph)\s+(TD|LR|TB|RL|BT)\b/.test(trimmed) || /^mindmap\b/.test(trimmed)) {
      const block = [trimmed];
      let j = i + 1;
      while (j < lines.length && lines[j].trim() !== '') { block.push(lines[j]); j++; }
      out.push(renderMermaid(block.join('\n'), null, null, t));
      i = j; continue;
    }
    // 表格: | 开头 + 下一行为分隔行（|---|---|）→ 收集整块渲染为 <table>
    if (trimmed.startsWith('|') && i + 1 < lines.length &&
        /^\|[\s\-:|]+\|?$/.test(lines[i + 1].trim()) && lines[i + 1].includes('-')) {
      const headers = trimmed.split('|').slice(1, -1).map(c => c.trim());
      const rows = [];
      let j = i + 2;
      while (j < lines.length && lines[j].trim().startsWith('|')) {
        rows.push(lines[j].trim().split('|').slice(1, -1).map(c => c.trim()));
        j++;
      }
      out.push(renderTable(headers, rows, agent));
      i = j; continue;
    }
    const imgMatch = trimmed.match(/^!\[([^\]]*)\]\(([^)]+)\)$/);
    if (imgMatch) {
      out.push(
        <div key={i} style={{ margin: '8px 0' }}>
          <img src={imgMatch[2]} alt={imgMatch[1]}
            style={{ maxWidth: '100%', maxHeight: 480, borderRadius: 8, border: '1px solid var(--border)' }} />
        </div>
      );
      i++; continue;
    }
    if (trimmed.startsWith('> ')) {
      out.push(<blockquote key={i} style={{ margin: '8px 0', padding: '6px 12px', borderLeft: '3px solid var(--border)', color: 'var(--text-dim)', background: 'var(--soft)', borderRadius: 4 }}>{renderInline(trimmed.slice(2), agent)}</blockquote>);
    } else if (/^[-*] \[[ xX]\] /.test(trimmed)) {
      // 任务列表 - [x] / - [ ]
      const checked = /^[-*] \[[xX]\] /.test(trimmed);
      out.push(<div key={i} style={{ paddingLeft: '1.2em', margin: '2px 0', display: 'flex', alignItems: 'baseline', gap: 6 }}>
        <span style={{ color: checked ? '#6fae6f' : 'var(--text-dim)', fontSize: 12 }}>{checked ? '☑' : '☐'}</span>
        <span style={{ textDecoration: checked ? 'line-through' : 'none', color: checked ? 'var(--text-dim)' : 'inherit' }}>
          {renderInline(trimmed.replace(/^[-*] \[[ xX]\] /, ''))}
        </span>
      </div>);
    } else if (/^\s{2,}[-*] /.test(line)) {
      // 嵌套列表（缩进子项）
      const depth = Math.min(Math.floor((line.length - line.trimStart().length) / 2), 4);
      out.push(<div key={i} style={{ paddingLeft: `${1.2 + depth * 1.2}em`, margin: '1px 0' }}>· {renderInline(trimmed.replace(/^[-*] /, ''), agent)}</div>);
    } else if (/^[-*] |^\d+\. /.test(trimmed)) {
      out.push(<div key={i} style={{ paddingLeft: '1.2em', margin: '2px 0' }}>· {renderInline(trimmed.replace(/^[-*] |^\d+\. /, ''), agent)}</div>);
    } else if (/^(-{3,}|\*{3,}|_{3,})$/.test(trimmed)) {
      // 水平分割线 --- *** ___
      out.push(<hr key={i} style={{ border: 'none', borderTop: '1px solid var(--border)', margin: '12px 0' }} />);
    } else if (trimmed.startsWith('#### ')) {
      out.push(<div key={i} style={{ fontWeight: 700, fontSize: 13, margin: '6px 0 2px', color: 'var(--text-dim)' }}>{renderInline(trimmed.slice(5), agent)}</div>);
    } else if (trimmed.startsWith('### ')) {
      out.push(<div key={i} style={{ fontWeight: 700, fontSize: 13.5, margin: '8px 0 3px', color: 'var(--text-dim)' }}>{renderInline(trimmed.slice(4), agent)}</div>);
    } else if (trimmed.startsWith('## ')) {
      out.push(<div key={i} style={{ fontWeight: 700, fontSize: 15, margin: '10px 0 4px' }}>{renderInline(trimmed.slice(3), agent)}</div>);
    } else if (trimmed.startsWith('# ')) {
      out.push(<div key={i} style={{ fontWeight: 700, fontSize: 17, margin: '12px 0 6px' }}>{renderInline(trimmed.slice(2), agent)}</div>);
    } else if (!trimmed) {
      out.push(<div key={i} style={{ height: 6 }} />);
    } else {
      out.push(<div key={i} style={{ margin: '2px 0' }}>{renderInline(trimmed, agent)}</div>);
    }
    i++;
  }
  flushFence();
  return out;
}

/* ── {t('citations')}（纯展示——PhiAgent 无阅读器路由, 不跳转） ── */
function Citations({ citations }) {
  const { t } = useLang();
  if (!citations?.length) return null;
  return (
    <div style={{ marginTop: 12, fontSize: 12 }}>
      <div style={{ color: 'var(--text-dim)', marginBottom: 6, letterSpacing: '.5px', display: 'flex', alignItems: 'center', gap: 5 }}>
        <Icon name="nav-books" size={13} /> {t('citations')}
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
        {citations.map((c, i) => (
          <div key={i}
            style={{ padding: '6px 10px', borderRadius: 6,
                     background: 'var(--soft)', border: '1px solid var(--border)' }}>
            <span>《{c.book}》· {c.chapter || t('bodyText')}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ── 对话页签 ── */
function ChatTab({ agent = 'general', questions = [] }) {
  const { t, lang, toolLabel } = useLang();
  const { token, authFetch } = useAuth();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [thoughtsOpen, setThoughtsOpen] = useState(true);   // CC 式联动折叠: 一折全折, 一展全展（默认展开）
  const [attachments, setAttachments] = useState([]);   // [{filename, kind, content}]
  const [uploading, setUploading] = useState(false);
  const [drawio, setDrawio] = useState(null);   // {xml, msgId} 当前打开的 draw.io 编辑器
  const fileInputRef = useRef(null);
  const bottomRef = useRef(null);
  const abortRef = useRef(null);   // 停止生成（AbortController）

  // draw.io 编辑: mermaid → draw.io XML → 打开编辑器; 关闭时回写编辑后的图
  const openDrawio = (msgId, mermaidCode) => {
    fetch(getApiBase() + '/api/drawio', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mermaid: mermaidCode }),
    }).then(r => r.json()).then(d => { if (d.xml) setDrawio({ xml: d.xml, msgId }); }).catch(() => {});
  };
  const closeDrawio = (editedXml) => {
    if (drawio?.msgId != null && editedXml) {
      const mid = drawio.msgId;
      setMessages(prev => prev.map(m => m.msgId === mid ? { ...m, drawioXml: editedXml } : m));
    }
    setDrawio(null);
  };

  // 附件上传: md 直读 / 其他格式 markitdown 转 / 图片 Agnes 识图
  const handleFile = async (e) => {
    const file = e.target.files?.[0];
    e.target.value = '';
    if (!file || uploading) return;
    setUploading(true);
    const fd = new FormData();
    fd.append('file', file);
    try {
      const resp = await fetch(`${getApiBase()}/api/upload`, { method: 'POST', body: fd });
      const d = await resp.json();
      if (d.error) {
        setMessages(prev => [...prev, { role: 'user', content: `⚠ ${t('attachmentNote')}《${file.name}》${t('uploadFail')}: ${d.error}`, streaming: false }]);
      } else {
        setAttachments(prev => [...prev, { filename: d.filename, kind: d.kind, content: d.content }]);
      }
    } catch (err) {
      setMessages(prev => [...prev, { role: 'user', content: `⚠ ${t('attachmentNote')}《${file.name}》${t('uploadFail')}: ${err.message}`, streaming: false }]);
    }
    setUploading(false);
  };

  // 登录后加载服务器端聊天历史（后端返回 {"messages": [...]}）
  useEffect(() => {
    if (token) {
      authFetch('/api/history/chat').then(d => {
        const list = d.messages || d.history || [];
        if (list.length) {
          setMessages(list.map(h => ({ role: h.role === 'user' ? 'user' : 'assistant', content: h.content })));
        }
      }).catch(() => {});
    } else {
      setMessages([]);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    // mermaid 脑图渲染（动态加载, 渲染新增的未处理节点; 失败静默降级为代码文本）
    const nodes = document.querySelectorAll('.mermaid:not([data-processed])');
    if (nodes.length) {
      import('mermaid').then((mod) => {
        const mermaid = mod.default || mod;
        mermaid.initialize({ startOnLoad: false, theme: 'dark', securityLevel: 'strict' });   // 2026-08-14: loose→strict 防 mermaid XSS（LLM 生成代码可含 HTML/javascript:）
        return mermaid.run({ nodes });
      }).catch(() => {});
    }
  }, [messages, loading]);

  const send = async (textOverride) => {
    const text = (textOverride ?? input).trim();
    if ((!text && !attachments.length) || loading) return;
    setInput('');
    // 附件内容注入消息（md 文本 / 识图描述）
    const attachText = attachments.length
      ? attachments.map(a => `【附件《${a.filename}》】\n${a.content}`).join('\n\n') + '\n\n'
      : '';
    const history = messages.slice(-20).map(m => ({ role: m.role, content: m.content }));
    setMessages(prev => [...prev, { role: 'user', content: attachments.length ? `[${t('attachmentNote')}：${attachments.map(a => `《${a.filename}》`).join('、')}]\n${text}` : text }]);
    setAttachments([]);   // 附件随消息发出后清空
    setLoading(true);
    // 流式: 实时{t('thoughts')} + 工具调用 + 回答打字机（支持停止）
    const controller = new AbortController();
    abortRef.current = controller;
    const msgId = Date.now();
    let finalContent = '';   // 本轮最终回答（登录后持久化用）
    setMessages(prev => [...prev, { role: 'assistant', content: '', events: [], citations: [], msgId, streaming: true }]);
    try {
      const resp = await fetch(`${getApiBase()}/api/agent/stream_lg`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json',
                    ...(token ? { 'Authorization': 'Bearer ' + token } : {}) },
        body: JSON.stringify({ message: attachText + text, history, agent, language: lang }),
        signal: controller.signal,
      });
      const reader = resp.body.getReader();
      const decoder = new TextDecoder();
      let buf = '';
      // 事件时间线: status(阶段状态) / thought_stream(实时思考) / thought(固化思考) / tool(工具卡片) / token(回答)
      const handleEvent = (evt) => {
        if (evt.type === 'status') {
          // 等待期实时状态（"{t('thinkingStatus')}"等）——DeepSeek 首块前不让用户面对空白
          setMessages(prev => prev.map(m => m.msgId === msgId ? { ...m, status: evt.content } : m));
        } else if (evt.type === 'thought') {
          setMessages(prev => prev.map(m => m.msgId === msgId ? {
            ...m, curThought: null,
            events: [...m.events, { t: 'thought', text: evt.content }],
          } : m));
        } else if (evt.type === 'thought_stream') {
          // 思考模式思维链实时追加（换行保留）
          setMessages(prev => prev.map(m => m.msgId === msgId ? { ...m, curThought: (m.curThought || '') + evt.content } : m));
        } else if (evt.type === 'tool_start') {
          // 工具开始调用（CC 风格: 先显示"调用中"卡片, 执行完再更新为完成）
          setMessages(prev => prev.map(m => m.msgId === msgId ? {
            ...m, curThought: null,
            events: [...m.events,
                     ...(m.curThought ? [{ t: 'thought', text: m.curThought }] : []),
                     { t: 'tool_start', name: evt.name }],
          } : m));
        } else if (evt.type === 'tool') {
          // 工具完成: 找到同名未完成的 tool_start 卡片, 更新为完成（带结果）
          setMessages(prev => prev.map(m => m.msgId === msgId ? {
            ...m, curThought: null,
            events: m.events.map(ev =>
              ev.t === 'tool_start' && ev.name === evt.name ? { t: 'tool', tc: { name: evt.name, args: evt.args, result_summary: evt.result, thought: evt.thought } } : ev),
          } : m));
        } else if (evt.type === 'token') {
          finalContent += evt.content;
          // 回答开始: 未固化的思考先入时间线, 再追加回答文本
          setMessages(prev => prev.map(m => m.msgId === msgId ? {
            ...m, content: m.content + evt.content,
            events: m.curThought ? [...m.events, { t: 'thought', text: m.curThought }] : m.events,
            curThought: null,
          } : m));
        } else if (evt.type === 'done') {
          setMessages(prev => prev.map(m => m.msgId === msgId ? {
            ...m, citations: evt.citations || [],
            reasoningSummary: evt.reasoning_summary || null,
            suggestions: evt.suggestions || [],
            safety: evt.safety || null,
            content: evt.safety === 'blocked' && evt.safety_reply ? evt.safety_reply : m.content,
            events: m.curThought ? [...m.events, { t: 'thought', text: m.curThought }] : m.events,
            curThought: null, streaming: false,
          } : m));
        } else if (evt.type === 'error') {
          setMessages(prev => prev.map(m => m.msgId === msgId ? { ...m, content: evt.content, streaming: false } : m));
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
        }
      }
      setMessages(prev => prev.map(m => m.msgId === msgId ? { ...m, streaming: false } : m));
    } catch (e) {
      if (e.name === 'AbortError') {
        // 用户主动停止: 保留已生成内容, 不显示错误
        setMessages(prev => prev.map(m => m.msgId === msgId ? { ...m, streaming: false } : m));
      } else {
        setMessages(prev => prev.map(m => m.msgId === msgId ? { ...m, content: `${t('reqFail')}: ${e.message}`, streaming: false } : m));
      }
    }
    abortRef.current = null;
    setLoading(false);
    // 登录后持久化本轮对话（user + assistant）
    if (token) {
      authFetch('/api/history/chat', { method: 'POST', body: JSON.stringify({ role: 'user', content: text }) }).catch(() => {});
      if (finalContent) {
        authFetch('/api/history/chat', { method: 'POST', body: JSON.stringify({ role: 'assistant', content: finalContent }) }).catch(() => {});
      }
    }
  };

  const stopGenerating = () => {
    abortRef.current?.abort();
  };

  // 剥离残留的工具调用标记（后端分块/LLM 异常时可能漏出）
  const cleanContent = (text) => (text || '')
    .replace(/<tool_calls>[\s\S]*?<\/tool_calls>/g, '')
    .replace(/<invoke name="[^"]+">[\s\S]*?<\/invoke>/g, '')
    .replace(/\{TOOL:[\s\S]*?\}/g, '');

  const renderContent = (m) => {
    if (m.role === 'user') return <div style={{ whiteSpace: 'pre-wrap', lineHeight: 1.7 }}>{m.content}</div>;
    return (
      <div>
        {/* 推理摘要（o1 风格）: 完整思考链的结构化步骤 */}
        {m.reasoningSummary && (
          <div style={{ marginBottom: 10, padding: '8px 12px', borderRadius: 8,
                        background: 'var(--soft)', border: '1px solid var(--border)', fontSize: 12.5 }}>
            <div style={{ fontSize: 11, color: 'var(--text-dim)', marginBottom: 5, letterSpacing: '.5px' }}>
              {t('reasoningSummary')}
            </div>
            {m.reasoningSummary.split('\n').filter(Boolean).map((s, i) => (
              <div key={i} style={{ margin: '2px 0', lineHeight: 1.6, color: 'var(--text-dim)' }}>{s}</div>
            ))}
          </div>
        )}
        {/* 安全提示条 */}
        {m.safety === 'warning' && (
          <div style={{ marginBottom: 10, padding: '8px 12px', borderRadius: 8, fontSize: 12,
                        background: '#fdf6e3', border: '1px solid #e8d9a0', color: '#8a6d1a' }}>
            {t('warning')}
          </div>
        )}
        {/* 事件时间线: 思考 → 工具 → 思考 → 工具 → 回答（按到达顺序穿插; 折叠全局联动, CC 式） */}
        {m.events?.map((ev, i) => ev.t === 'thought' ? (
          <details key={i} open={thoughtsOpen}
            onClick={(e) => { e.preventDefault(); setThoughtsOpen(!thoughtsOpen); }}
            style={{ margin: '4px 0', fontSize: 12.5 }}>
            <summary style={{ color: 'var(--text-dim)', cursor: 'pointer', fontStyle: 'italic',
                              borderLeft: '2px solid #d4d4d8', paddingLeft: 10,
                              padding: '2px 0', userSelect: 'none' }}>
              {thoughtsOpen ? ('▾ ' + t('thoughts')) : ('▸ ' + t('thoughts'))}
            </summary>
            <div style={{ fontSize: 12.5, color: 'var(--text-dim)', fontStyle: 'italic',
                          padding: '4px 2px', margin: '2px 0', lineHeight: 1.7,
                          borderLeft: '2px solid #d4d4d8', paddingLeft: 10,
                          whiteSpace: 'pre-wrap' }}>
              {cleanContent(ev.text)}
            </div>
          </details>
        ) : ev.t === 'tool_start' ? (
          <div key={i} style={{ margin: '6px 0' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '8px 12px',
                          border: '1px solid var(--border)', borderRadius: 8, background: 'var(--card-bg)',
                          fontSize: 13, color: 'var(--text-dim)' }}>
              <span style={{ width: 13, height: 13, borderRadius: '50%', border: '2px solid var(--border)',
                             borderTopColor: 'var(--accent)', animation: 'spin 0.8s linear infinite' }} />
              {t('calling')} {toolLabel(ev.name)}…
            </div>
          </div>
        ) : (
          <div key={i} style={{ margin: '6px 0' }}>
            <ToolCard tc={ev.tc} index={i} />
          </div>
        ))}
        {/* 等待期状态（后端 status 事件: 思考流出现前的阶段提示） */}
        {m.streaming && !m.curThought && !m.content && !m.events?.length && m.status && (
          <div style={{ fontSize: 12.5, color: 'var(--text-dim)', fontStyle: 'italic',
                        padding: '4px 2px', marginBottom: 6, lineHeight: 1.7, display: 'flex', alignItems: 'center', gap: 6 }}>
            <span style={{ width: 13, height: 13, borderRadius: '50%', border: '2px solid var(--border)',
                           borderTopColor: 'var(--accent)', animation: 'spin 0.8s linear infinite' }} />
            {m.status}…
          </div>
        )}
        {/* 实时思考（进行中）——与固化思考块样式统一 */}
        {m.curThought && (
          <div style={{ fontSize: 12.5, color: 'var(--text-dim)', fontStyle: 'italic',
                        padding: '4px 2px', marginBottom: 6, lineHeight: 1.7,
                        borderLeft: '2px solid #d4d4d8', paddingLeft: 10, whiteSpace: 'pre-wrap' }}>
            {cleanContent(m.curThought)}
            <span style={{ display: 'inline-block', width: 6, height: 14, marginLeft: 3,
                           background: 'var(--accent)', animation: 'pulse 1s infinite', verticalAlign: 'middle' }} />
          </div>
        )}
        <div style={{ lineHeight: 1.8, fontSize: 14 }}>
          {renderMarkdown(cleanContent(m.content), agent, (code) => openDrawio(m.msgId, code), m.drawioXml, t)}
          {m.streaming && !m.curThought && m.content && (
            <span style={{ display: 'inline-block', width: 6, height: 14, marginLeft: 3,
                           background: 'var(--accent)', animation: 'pulse 1s infinite', verticalAlign: 'middle' }} />
          )}
        </div>
        <Citations citations={m.citations} />
        {/* 话题延续建议（点击直接发送）——位于{t('citations')}之后 */}
        {m.suggestions?.length > 0 && !m.streaming && (
          <div style={{ marginTop: 14, paddingTop: 10, borderTop: '1px solid var(--border)' }}>
            <div style={{ fontSize: 11, color: 'var(--text-dim)', marginBottom: 6 }}>{t('explore')}</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
              {m.suggestions.map((s, i) => (
                <button key={i} onClick={() => send(s)}
                  style={{ textAlign: 'left', padding: '7px 12px', borderRadius: 8, cursor: 'pointer',
                           background: 'var(--soft)', border: '1px solid var(--border)', fontSize: 13,
                           color: 'var(--text)', transition: 'background .15s' }}>
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  };

  return (
    <>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        {messages.length === 0 && (
          <div style={{ textAlign: 'center', color: 'var(--text-dim)', padding: '40px 0', fontSize: 14 }}>
            <div style={{ marginBottom: 12 }}><Icon name="icon-brain" size={40} /></div>
            {t('tryAsk')}
            <div style={{ marginTop: 12, display: 'flex', flexDirection: 'column', gap: 8, alignItems: 'center' }}>
              {(questions.length ? questions : QUESTION_BANK[agent]?.[lang] || QUESTION_BANK.general[lang]).map((q, i) => (
                <button key={i} onClick={() => send(q)}
                  style={{ padding: '8px 18px', borderRadius: 18, border: '1px solid var(--border)',
                           background: 'var(--card-bg)', cursor: 'pointer', fontSize: 13 }}>
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}
        {messages.map((m, i) => (
          <div key={i} style={{
            alignSelf: m.role === 'user' ? 'flex-end' : 'flex-start',
            maxWidth: m.role === 'user' ? '92%' : '100%',   // 用户=紧凑气泡; 助手=全宽无框（Manus 式）
            background: m.role === 'user' ? 'var(--soft)' : 'transparent',
            border: 'none',
            borderRadius: m.role === 'user' ? '16px 16px 4px 16px' : 0,
            padding: m.role === 'user' ? '10px 14px' : '2px 0',
            fontSize: 15, lineHeight: 1.75,
          }}>
            {renderContent(m)}
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
      {drawio && <DrawioModal xml={drawio.xml} onClose={closeDrawio} />}
      <div style={{ position: 'fixed', bottom: 0, left: 216, right: 0, padding: '8px 20px 20px',
                    background: 'linear-gradient(transparent, var(--bg) 40%)' }}>
        {/* 附件 chips */}
        {attachments.length > 0 && (
          <div style={{ maxWidth: 760, margin: '0 auto 8px', display: 'flex', gap: 6, flexWrap: 'wrap' }}>
            {attachments.map((a, i) => (
              <span key={i}
                style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '4px 10px', fontSize: 12,
                         background: 'var(--soft)', border: '1px solid var(--border)', borderRadius: 12 }}>
                {a.kind === 'image' ? '🖼 ' : '📄 '}{a.filename}
                <span onClick={() => setAttachments(prev => prev.filter((_, j) => j !== i))}
                  style={{ cursor: 'pointer', color: 'var(--text-dim)' }}>✕</span>
              </span>
            ))}
          </div>
        )}
        <div style={{ maxWidth: 760, margin: '0 auto', display: 'flex', alignItems: 'center', gap: 4,
                      background: 'var(--card-bg)', border: '1px solid var(--border)', borderRadius: 26,
                      padding: '6px 6px 6px 8px', boxShadow: '0 2px 12px var(--ring)' }}>
          <input ref={fileInputRef} type="file" onChange={handleFile} style={{ display: 'none' }} />
          <button onClick={() => fileInputRef.current?.click()} title={t('attach')}
            style={{ width: 32, height: 32, borderRadius: '50%', border: 'none', cursor: 'pointer', flexShrink: 0,
                     background: 'var(--soft)', color: 'var(--accent)', fontSize: 16, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            {uploading ? '…' : '+'}
          </button>
          <input
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && send()}
            placeholder={t('placeholder')}
            style={{ flex: 1, border: 'none', background: 'transparent', fontSize: 15, outline: 'none', color: 'var(--text)' }}
          />
          {loading ? (
            <button onClick={stopGenerating} title={t('stopGenerating')}
              style={{ width: 36, height: 36, borderRadius: '50%', border: '1px solid var(--border)', cursor: 'pointer', flexShrink: 0,
                       background: 'var(--card-bg)', color: 'var(--accent)', fontSize: 12,
                       display: 'flex', alignItems: 'center', justifyContent: 'center',
                       transition: 'opacity .15s' }}>
              ■
            </button>
          ) : (
            <button onClick={() => send()} disabled={!input.trim()}
              style={{ width: 36, height: 36, borderRadius: '50%', border: 'none', cursor: 'pointer', flexShrink: 0,
                       background: 'var(--accent)', color: 'var(--bg)', fontSize: 15,
                       display: 'flex', alignItems: 'center', justifyContent: 'center',
                       opacity: !input.trim() ? 0.4 : 1, transition: 'opacity .15s' }}>
              ↑
            </button>
          )}
        </div>
      </div>
    </>
  );
}

/* ── 主页面（智能体广场: 顶栏/示例问题随智能体切换） ── */
// 示例问题（双语——agentName/agentSub 由 i18n 提供, questions 需按语言取）
const QUESTION_BANK = {
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

export default function AgentPage({ agent = 'general' }) {
  const { t, lang, agentName, agentSub } = useLang();
  const name = agentName(agent);
  const sub = agentSub(agent) || t('philoAgent');
  return (
    <div style={{ maxWidth: 860, margin: '0 auto', padding: '16px 20px 140px'  /* 底部留白防 fixed 输入框遮挡 */, minHeight: '70vh' }}>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 10, marginBottom: 4 }}>
        <h1 style={{ fontSize: 22, margin: 0 }}>{name}</h1>
        <span style={{ fontSize: 12, color: 'var(--text-dim)' }}>{sub}</span>
      </div>
      <ChatTab agent={agent} questions={QUESTION_BANK[agent]?.[lang] || []} />
    </div>
  );
}
