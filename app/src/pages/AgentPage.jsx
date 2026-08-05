import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getApiBase } from '../utils/api';
import Icon from '../components/Icon';

/**
 * AgentPage — 哲学智能体"深哲"（ReAct 架构: 思考→行动→观察 循环可视化）
 * 工具页签: 对话 / 作文 / 生图
 * 图标规范: 全部使用 /icons/*.png（Icon 组件）, 禁用 emoji
 */
const TOOL_META = {
  search_books: { icon: 'icon-search', label: '检索原典' },
  get_chapter: { icon: 'icon-book-open', label: '读取章节' },
  get_book_detail: { icon: 'nav-books', label: '查书详情' },
  query_graph: { icon: 'nav-genealogy', label: '查询星丛' },
  get_philosopher: { icon: 'nav-authors', label: '查哲人资料' },
  list_books: { icon: 'nav-books', label: '筛选书目' },
};

const TABS = [
  { key: 'chat', icon: 'nav-qa', label: '对话' },
  { key: 'essay', icon: 'icon-clipboard', label: '作文' },
  { key: 'image', icon: 'icon-candle', label: '生图' },
];

/* ── 工具调用卡片（ReAct: 思考 → 行动） ── */
function ToolCard({ tc, index }) {
  const [open, setOpen] = useState(false);
  const meta = TOOL_META[tc.name] || { icon: 'icon-cog', label: tc.name };
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
          <span style={{ fontSize: 13, fontWeight: 600 }}>{meta.label}</span>
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

/* ── markdown 简易渲染 ── */
function renderInline(text) {
  const parts = (text || '').split(/(\*\*[^*]+\*\*|`[^`]+`)/g);
  return parts.map((p, i) => {
    if (p.startsWith('**') && p.endsWith('**')) return <strong key={i}>{p.slice(2, -2)}</strong>;
    if (p.startsWith('`') && p.endsWith('`')) return <code key={i} style={{ background: 'rgba(120,140,255,.1)', padding: '1px 5px', borderRadius: 4, fontSize: '0.92em' }}>{p.slice(1, -1)}</code>;
    return p;
  });
}

function renderMarkdown(text) {
  const lines = (text || '').split('\n');
  const out = [];
  lines.forEach((line, i) => {
    const trimmed = line.trim();
    if (trimmed.startsWith('> ')) {
      out.push(<blockquote key={i} style={{ margin: '8px 0', padding: '6px 12px', borderLeft: '3px solid var(--border)', color: 'var(--text-dim)', background: 'rgba(120,140,255,.06)', borderRadius: 4 }}>{renderInline(trimmed.slice(2))}</blockquote>);
    } else if (/^[-*] |^\d+\. /.test(trimmed)) {
      out.push(<div key={i} style={{ paddingLeft: '1.2em', margin: '2px 0' }}>· {renderInline(trimmed.replace(/^[-*] |^\d+\. /, ''))}</div>);
    } else if (trimmed.startsWith('## ')) {
      out.push(<div key={i} style={{ fontWeight: 700, fontSize: 15, margin: '10px 0 4px' }}>{renderInline(trimmed.slice(3))}</div>);
    } else if (trimmed.startsWith('# ')) {
      out.push(<div key={i} style={{ fontWeight: 700, fontSize: 17, margin: '12px 0 6px' }}>{renderInline(trimmed.slice(2))}</div>);
    } else if (!trimmed) {
      out.push(<div key={i} style={{ height: 6 }} />);
    } else {
      out.push(<div key={i} style={{ margin: '2px 0' }}>{renderInline(trimmed)}</div>);
    }
  });
  return out;
}

/* ── 引用来源 ── */
function Citations({ citations, navigate }) {
  if (!citations?.length) return null;
  return (
    <div style={{ marginTop: 12, fontSize: 12 }}>
      <div style={{ color: 'var(--text-dim)', marginBottom: 6, letterSpacing: '.5px', display: 'flex', alignItems: 'center', gap: 5 }}>
        <Icon name="nav-books" size={13} /> 引用来源
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
        {citations.map((c, i) => (
          <div key={i}
            onClick={() => c.book_id && navigate(`/reader/${c.book_id}?ch=${c.chapter_idx || 0}`)}
            style={{ cursor: 'pointer', padding: '6px 10px', borderRadius: 6,
                     background: 'rgba(120,140,255,.06)', border: '1px solid var(--border)',
                     display: 'flex', justifyContent: 'space-between', gap: 8, alignItems: 'center' }}>
            <span>《{c.book}》· {c.chapter || '正文'}</span>
            <span style={{ color: 'var(--text-dim)', fontSize: 11 }}>阅读 →</span>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ── 对话页签 ── */
function ChatTab() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);
  const navigate = useNavigate();

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const send = async (textOverride) => {
    const text = (textOverride ?? input).trim();
    if (!text || loading) return;
    setInput('');
    const history = messages.slice(-6).map(m => ({ role: m.role, content: m.content }));
    setMessages(prev => [...prev, { role: 'user', content: text }]);
    setLoading(true);
    try {
      const resp = await fetch(`${getApiBase()}/api/agent/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, history }),
      });
      const d = await resp.json();
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: d.reply || '（无回答）',
        toolCalls: d.tool_calls || [],
        citations: d.citations || [],
      }]);
    } catch (e) {
      setMessages(prev => [...prev, { role: 'assistant', content: `请求失败: ${e.message}` }]);
    }
    setLoading(false);
  };

  const renderContent = (m) => {
    if (m.role === 'user') return <div style={{ whiteSpace: 'pre-wrap', lineHeight: 1.7 }}>{m.content}</div>;
    return (
      <div>
        {m.toolCalls?.length > 0 && (
          <div style={{ marginBottom: 10 }}>
            <div style={{ fontSize: 11, color: 'var(--text-dim)', marginBottom: 4, letterSpacing: '.5px' }}>
              ── 思考与行动 · {m.toolCalls.length} 步 ──
            </div>
            {m.toolCalls.map((tc, i) => <ToolCard key={i} tc={tc} index={i} />)}
          </div>
        )}
        <div style={{ lineHeight: 1.8, fontSize: 14 }}>{renderMarkdown(m.content)}</div>
        <Citations citations={m.citations} navigate={navigate} />
      </div>
    );
  };

  return (
    <>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        {messages.length === 0 && (
          <div style={{ textAlign: 'center', color: 'var(--text-dim)', padding: '40px 0', fontSize: 14 }}>
            <div style={{ marginBottom: 12 }}><Icon name="icon-brain" size={40} /></div>
            试着问：
            <div style={{ marginTop: 12, display: 'flex', flexDirection: 'column', gap: 8, alignItems: 'center' }}>
              {['永恒轮回是什么意思？尼采怎么说的', '休谟和康德对因果的看法有何不同？', '海德格尔受谁影响？', '推荐几本存在主义入门书'].map((q, i) => (
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
            maxWidth: '92%',
            background: m.role === 'user' ? 'rgba(120,140,255,.13)' : 'var(--card-bg)',
            border: '1px solid var(--border)',
            borderRadius: 12, padding: '12px 16px', fontSize: 14,
          }}>
            {renderContent(m)}
          </div>
        ))}
        {loading && (
          <div style={{ alignSelf: 'flex-start', display: 'flex', alignItems: 'center', gap: 8, color: 'var(--text-dim)', fontSize: 13, padding: '6px 4px' }}>
            <span style={{ width: 14, height: 14, borderRadius: '50%', border: '2px solid var(--border)', borderTopColor: '#8b9bff', animation: 'spin 0.8s linear infinite' }} />
            深哲思考中（检索原典…）
          </div>
        )}
        <div ref={bottomRef} />
      </div>
      <div style={{ position: 'fixed', bottom: 0, left: 0, right: 0, padding: '12px 20px',
                    background: 'var(--bg)', borderTop: '1px solid var(--border)', backdropFilter: 'blur(8px)' }}>
        <div style={{ maxWidth: 860, margin: '0 auto', display: 'flex', gap: 8 }}>
          <input
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && send()}
            placeholder="问一个哲学问题…（回答将引用原典原文）"
            style={{ flex: 1, padding: '11px 16px', borderRadius: 22, border: '1px solid var(--border)',
                     background: 'var(--card-bg)', fontSize: 14, outline: 'none' }}
          />
          <button onClick={() => send()} disabled={loading || !input.trim()}
            style={{ padding: '11px 26px', borderRadius: 22, border: 'none', cursor: 'pointer',
                     background: 'linear-gradient(135deg,#6a7bff,#8b5cf6)', color: '#fff', fontSize: 14,
                     opacity: loading || !input.trim() ? 0.5 : 1 }}>
            发送
          </button>
        </div>
      </div>
    </>
  );
}

/* ── 主页面（单一对话流: 作文/生图在对话中自然触发） ── */
export default function AgentPage() {
  return (
    <div style={{ maxWidth: 860, margin: '0 auto', padding: '16px 20px 0', minHeight: '70vh' }}>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 10, marginBottom: 4 }}>
        <h1 style={{ fontSize: 22, margin: 0 }}>深哲</h1>
        <span style={{ fontSize: 12, color: 'var(--text-dim)' }}>哲学智能体 · 基于 403 本原典</span>
      </div>
      <ChatTab />
    </div>
  );
}
