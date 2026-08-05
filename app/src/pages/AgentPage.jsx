import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getApiBase } from '../utils/api';

/**
 * AgentPage — 哲学智能体"深哲"
 * 可插拔工具集 + DeepSeek 编排: 检索 403 本原典 / 星丛图谱 / 引用溯源
 */
export default function AgentPage() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);
  const navigate = useNavigate();

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const send = async () => {
    const text = input.trim();
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

  const renderContent = (m) => {
    if (m.role === 'user') return <div style={{ whiteSpace: 'pre-wrap' }}>{m.content}</div>;
    return (
      <div>
        {/* 工具调用记录 */}
        {m.toolCalls?.length > 0 && (
          <div style={{ marginBottom: 8, display: 'flex', flexWrap: 'wrap', gap: 4 }}>
            {m.toolCalls.map((tc, i) => (
              <span key={i} title={JSON.stringify(tc.args)}
                style={{ fontSize: 11, background: 'rgba(120,140,255,.12)', color: '#8b9bff',
                         padding: '2px 8px', borderRadius: 10, border: '1px solid rgba(120,140,255,.25)' }}>
                🔧 {tc.name === 'search_books' ? '检索原典' : tc.name === 'get_chapter' ? '读章节'
                   : tc.name === 'query_graph' ? '查星丛' : tc.name === 'get_philosopher' ? '查哲人'
                   : tc.name === 'get_book_detail' ? '查书目' : tc.name}
              </span>
            ))}
          </div>
        )}
        <div style={{ whiteSpace: 'pre-wrap', lineHeight: 1.8 }}>{m.content}</div>
        {/* 引用来源 */}
        {m.citations?.length > 0 && (
          <div style={{ marginTop: 10, fontSize: 12 }}>
            <div style={{ color: 'var(--text-dim)', marginBottom: 4 }}>📚 引用来源</div>
            {m.citations.map((c, i) => (
              <div key={i}
                onClick={() => c.book_id && navigate(`/reader/${c.book_id}?ch=${c.chapter_idx || 0}`)}
                style={{ cursor: 'pointer', padding: '6px 10px', marginBottom: 4, borderRadius: 6,
                         background: 'var(--card-bg)', border: '1px solid var(--border)',
                         display: 'flex', justifyContent: 'space-between', gap: 8 }}>
                <span>《{c.book}》· {c.chapter || '正文'}</span>
                <span style={{ color: 'var(--text-dim)' }}>阅读 →</span>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div style={{ maxWidth: 860, margin: '0 auto', padding: '16px 20px 120px', minHeight: '70vh' }}>
      <h1 style={{ fontSize: 24, margin: '8px 0 4px' }}>深哲 · 哲学智能体</h1>
      <div style={{ color: 'var(--text-dim)', fontSize: 13, marginBottom: 16 }}>
        基于 403 本哲学原著检索回答，引用真实原文；可问概念、对比、师承脉络、阅读推荐。
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        {messages.length === 0 && (
          <div style={{ textAlign: 'center', color: 'var(--text-dim)', padding: '40px 0', fontSize: 14 }}>
            试着问：
            <div style={{ marginTop: 12, display: 'flex', flexDirection: 'column', gap: 8, alignItems: 'center' }}>
              {['永恒轮回是什么意思？尼采怎么说的', '休谟和康德对因果的看法有何不同？', '海德格尔受谁影响？', '推荐几本存在主义入门书'].map((q, i) => (
                <button key={i} onClick={() => setInput(q)}
                  style={{ padding: '8px 16px', borderRadius: 16, border: '1px solid var(--border)',
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
            maxWidth: '88%',
            background: m.role === 'user' ? 'rgba(120,140,255,.15)' : 'var(--card-bg)',
            border: '1px solid var(--border)',
            borderRadius: 12, padding: '10px 14px', fontSize: 14,
          }}>
            {renderContent(m)}
          </div>
        ))}
        {loading && (
          <div style={{ alignSelf: 'flex-start', color: 'var(--text-dim)', fontSize: 13 }}>
            <span style={{ display: 'inline-block', animation: 'pulse 1s infinite' }}>深哲思考中（检索原典…）</span>
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
            style={{ flex: 1, padding: '10px 14px', borderRadius: 20, border: '1px solid var(--border)',
                     background: 'var(--card-bg)', fontSize: 14, outline: 'none' }}
          />
          <button onClick={send} disabled={loading || !input.trim()}
            style={{ padding: '10px 22px', borderRadius: 20, border: 'none', cursor: 'pointer',
                     background: 'linear-gradient(135deg,#6a7bff,#8b5cf6)', color: '#fff', fontSize: 14 }}>
            发送
          </button>
        </div>
      </div>
    </div>
  );
}
