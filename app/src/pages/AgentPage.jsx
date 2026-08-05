import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getApiBase } from '../utils/api';

/**
 * AgentPage — 哲学智能体"深哲"（Claude Code 风格: 工具调用可视化 + 思考过程时间线）
 */
const TOOL_META = {
  search_books: { icon: '🔎', label: '检索原典' },
  get_chapter: { icon: '📖', label: '读取章节' },
  get_book_detail: { icon: '📚', label: '查书详情' },
  query_graph: { icon: '🕸️', label: '查询星丛' },
  get_philosopher: { icon: '👤', label: '查哲人资料' },
  list_books: { icon: '🗂️', label: '筛选书目' },
};

function ToolCard({ tc, index }) {
  const [open, setOpen] = useState(false);
  const meta = TOOL_META[tc.name] || { icon: '🔧', label: tc.name };
  return (
    <div style={{
      border: '1px solid var(--border)', borderRadius: 8, margin: '6px 0',
      background: 'var(--card-bg)', overflow: 'hidden',
    }}>
      <div onClick={() => setOpen(!open)}
        style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '8px 12px',
                 cursor: 'pointer', userSelect: 'none' }}>
        <span style={{ fontSize: 11, color: 'var(--text-dim)', fontFamily: 'monospace', minWidth: 22 }}>
          {String(index + 1).padStart(2, '0')}
        </span>
        <span style={{ fontSize: 14 }}>{meta.icon}</span>
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
  );
}

export default function AgentPage() {
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
    const userMsg = { role: 'user', content: text };
    setMessages(prev => [...prev, userMsg]);
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

  const renderMarkdown = (text) => {
    // 简易渲染: 引用块 / 列表 / 加粗 / 换行
    const lines = (text || '').split('\n');
    const out = [];
    let inQuote = false;
    let inList = false;
    lines.forEach((line, i) => {
      const trimmed = line.trim();
      if (trimmed.startsWith('> ')) {
        if (!inQuote) { inQuote = true; out.push(<blockquote key={i} style={{ margin: '8px 0', padding: '6px 12px', borderLeft: '3px solid var(--border)', color: 'var(--text-dim)', background: 'rgba(120,140,255,.06)', borderRadius: 4 }}>{[]}</blockquote>); }
        out[out.length - 1] = <blockquote key={i} style={{ margin: '8px 0', padding: '6px 12px', borderLeft: '3px solid var(--border)', color: 'var(--text-dim)', background: 'rgba(120,140,255,.06)', borderRadius: 4 }}>{renderInline(trimmed.slice(2))}</blockquote>;
      } else {
        inQuote = false;
        if (/^[-*] |^\d+\. /.test(trimmed)) {
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
      }
    });
    return out;
  };

  const renderInline = (text) => {
    // **加粗** 和 `代码`
    const parts = text.split(/(\*\*[^*]+\*\*|`[^`]+`)/g);
    return parts.map((p, i) => {
      if (p.startsWith('**') && p.endsWith('**')) return <strong key={i}>{p.slice(2, -2)}</strong>;
      if (p.startsWith('`') && p.endsWith('`')) return <code key={i} style={{ background: 'rgba(120,140,255,.1)', padding: '1px 5px', borderRadius: 4, fontSize: '0.92em' }}>{p.slice(1, -1)}</code>;
      return p;
    });
  };

  const renderContent = (m) => {
    if (m.role === 'user') return <div style={{ whiteSpace: 'pre-wrap', lineHeight: 1.7 }}>{m.content}</div>;
    return (
      <div>
        {/* 思考过程（工具调用时间线） */}
        {m.toolCalls?.length > 0 && (
          <div style={{ marginBottom: 10 }}>
            <div style={{ fontSize: 11, color: 'var(--text-dim)', marginBottom: 4, letterSpacing: '.5px' }}>
              ── 思考过程 · {m.toolCalls.length} 次工具调用 ──
            </div>
            {m.toolCalls.map((tc, i) => <ToolCard key={i} tc={tc} index={i} />)}
          </div>
        )}
        {/* 回答 */}
        <div style={{ lineHeight: 1.8, fontSize: 14 }}>{renderMarkdown(m.content)}</div>
        {/* 引用来源 */}
        {m.citations?.length > 0 && (
          <div style={{ marginTop: 12, fontSize: 12 }}>
            <div style={{ color: 'var(--text-dim)', marginBottom: 6, letterSpacing: '.5px' }}>📚 引用来源</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              {m.citations.map((c, i) => (
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
        )}
      </div>
    );
  };

  return (
    <div style={{ maxWidth: 860, margin: '0 auto', padding: '16px 20px 130px', minHeight: '70vh' }}>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 10, marginBottom: 4 }}>
        <h1 style={{ fontSize: 22, margin: 0 }}>深哲</h1>
        <span style={{ fontSize: 12, color: 'var(--text-dim)' }}>哲学智能体 · 基于 403 本原典检索回答</span>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        {messages.length === 0 && (
          <div style={{ textAlign: 'center', color: 'var(--text-dim)', padding: '48px 0', fontSize: 14 }}>
            <div style={{ fontSize: 34, marginBottom: 12 }}>🏛️</div>
            试着问：
            <div style={{ marginTop: 14, display: 'flex', flexDirection: 'column', gap: 8, alignItems: 'center' }}>
              {['永恒轮回是什么意思？尼采怎么说的', '休谟和康德对因果的看法有何不同？', '海德格尔受谁影响？', '推荐几本存在主义入门书'].map((q, i) => (
                <button key={i} onClick={() => send(q)}
                  style={{ padding: '8px 18px', borderRadius: 18, border: '1px solid var(--border)',
                           background: 'var(--card-bg)', cursor: 'pointer', fontSize: 13,
                           transition: 'all .15s' }}
                  onMouseEnter={e => e.target.style.borderColor = '#8b9bff'}
                  onMouseLeave={e => e.target.style.borderColor = 'var(--border)'}>
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
      {/* 输入区 */}
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
    </div>
  );
}
