/**
 * 问答分区 —— 直连 DeepSeek API，支持 Render RAG 作为优先源
 * 聊天历史本地自动保存
 */
import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getApiBase } from '../App';
import Icon from '../components/Icon';
import { ensureSession, updateSession, newConversation } from '../data/chatSessions';
import { saveChatMessage } from '../data/userData';

const WELCOME_MSG = {
  role: 'assistant',
  content: <>你好！我是 DeepPhilosophy 哲学助手，由 DeepSeek 驱动。你可以向我提问任何哲学问题，我会基于知识库中的文献为你解答，并附上参考文献。{'\n\n'}<Icon name="icon-tip" size={14} /> 如需更快响应速度，可在设置页绑定你自己的 API Key。</>,
};

function QAPage() {
  const navigate = useNavigate();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [thinkingPhase, setThinkingPhase] = useState('');
  const [showConfirmClear, setShowConfirmClear] = useState(false);
  const [thinkingMode, setThinkingMode] = useState(false);
  const sessionIdRef = useRef(null);
  const chatRef = useRef(null);
  const thinkingTimer = useRef(null);

  // 思考阶段动画
  const thinkingPhases = [
    <><Icon name="icon-search" size={14} /> 检索相关文献...</>,
    <><Icon name="icon-book-open" size={14} /> 分析文档内容...</>,
    <><Icon name="icon-thinking" size={14} /> 深度思考中...</>,
    <><Icon name="icon-writing" size={14} /> 组织回答...</>,
  ];

  const startThinking = () => {
    let i = 0;
    setThinkingPhase(thinkingPhases[0]);
    thinkingTimer.current = setInterval(() => {
      i = (i + 1) % thinkingPhases.length;
      setThinkingPhase(thinkingPhases[i]);
    }, 1200);
  };

  const stopThinking = () => {
    if (thinkingTimer.current) {
      clearInterval(thinkingTimer.current);
      thinkingTimer.current = null;
    }
    setThinkingPhase('');
  };

  // 会话管理：保持对话不丢失
  useEffect(() => {
    const session = ensureSession();
    sessionIdRef.current = session.id;
    if (session.messages.length > 0) {
      setMessages(session.messages);
    } else {
      setMessages([WELCOME_MSG]);
    }
  }, []);

  // 消息变化时自动保存到当前会话（过滤 JSX 欢迎消息）
  useEffect(() => {
    if (sessionIdRef.current && messages.length > 1) {
      const saveable = messages
        .filter(m => typeof m.content === 'string')
        .map(m => ({ role: m.role, content: m.content, sources: m.sources || [] }));
      if (saveable.length > 0) {
        updateSession(sessionIdRef.current, saveable);
      }
    }
  }, [messages]);

  useEffect(() => {
    return () => {
      if (thinkingTimer.current) clearInterval(thinkingTimer.current);
    };
  }, []);

  const [apiConfig, setApiConfig] = useState({});
  useEffect(() => {
    import('../data/crypto').then(({ loadConfig }) => loadConfig().then(setApiConfig));
  }, []);

  // 自动滚动到底部（流式输出时逐字跟随）
  const bottomRef = useRef(null);
  useEffect(() => {
    if (bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    const question = input.trim();
    setInput('');

    // 先构建 API 消息（用当前 messages state + 新问题），再更新 UI
    const historyMessages = messages
      .filter(m => !m._streaming && m.role !== 'system')
      .filter(m => typeof m.content === 'string' && m.content.trim().length > 0)
      .slice(-30);

    const apiMessages = [
      { role: 'system', content: '你是一个哲学知识助手，精通中西方哲学。请用中文回答，回答要准确、有深度。如果用户询问特定著作或哲学家，请详细阐述其核心思想。' },
      ...historyMessages.map(m => ({ role: m.role, content: m.content })), // reasoning_content 不传入上下文
      { role: 'user', content: question },
    ];

    // 更新 UI
    const userMsg = { role: 'user', content: question };
    setMessages(prev => [...prev, userMsg]);
    setMessages(prev => [...prev, { role: 'assistant', content: '', sources: [], _streaming: true }]);
    setLoading(true);
    startThinking();

    let answer = '';
    let reasoning = '';
    let sources = [];

    const baseUrl = (apiConfig.apiUrl || 'https://api.deepseek.com').replace(/\/+$/, '');

    // 官方文档: deepseek-v4-pro + thinking:{type:"enabled"} + reasoning_effort:"high"
    const model = thinkingMode ? 'deepseek-v4-pro' : (apiConfig.model || 'deepseek-chat');
    const streamBody = {
      model, messages: apiMessages, stream: true,
      max_tokens: thinkingMode ? 4096 : 1024,
    };
    if (thinkingMode) {
      streamBody.thinking = { type: 'enabled' };
      streamBody.reasoning_effort = 'high';
    } else {
      streamBody.temperature = 0.7;
    }

    // RAG 检索：后台异步，不阻塞对话流
    const ragPromise = fetch(`${getApiBase()}/api/qa`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, api_key: apiConfig.apiKey || null }),
      signal: AbortSignal.timeout(8000),
    }).then(r => r.ok ? r.json() : null)
      .then(d => { if (d?.sources?.length > 0) sources = d.sources; })
      .catch(() => {});

    // 流式调用 DeepSeek API（有用户Key直连，无Key走服务器代理）
    try {
      const useProxy = !apiConfig.apiKey;
      const resp = useProxy
        ? await fetch(`${getApiBase()}/api/ai/stream`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(streamBody),
            signal: AbortSignal.timeout(60000),
          })
        : await fetch(`${baseUrl}/v1/chat/completions`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${apiConfig.apiKey}` },
            body: JSON.stringify(streamBody),
            signal: AbortSignal.timeout(60000),
          });

      if (resp.ok) {
        const reader = resp.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        const streamStart = Date.now();
        const STREAM_TIMEOUT = 90000; // 90s hard timeout

        while (true) {
          if (Date.now() - streamStart > STREAM_TIMEOUT) {
            if (!answer) answer = '回答生成超时，请重试。';
            break;
          }
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || '';

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const data = line.slice(6).trim();
              if (data === '[DONE]') continue;
              try {
                const json = JSON.parse(data);
                const delta = json.choices?.[0]?.delta;
                const textChunk = delta?.content || '';
                const reasonChunk = delta?.reasoning_content || '';
                if (textChunk) answer += textChunk;
                if (reasonChunk) reasoning += reasonChunk;
                if (textChunk || reasonChunk) {
                  setMessages(prev => {
                    const updated = [...prev];
                    const last = { ...updated[updated.length - 1] };
                    last.content = answer;
                    last.reasoning = reasoning;
                    last.sources = sources;
                    updated[updated.length - 1] = last;
                    return updated;
                  });
                }
              } catch {}
            }
          }
        }
      }
    } catch (e) { console.error('QA stream failed:', e); }

    if (!answer) {
      answer = '无法获取回答。\n\n请检查网络连接或在设置中配置 API Key。';
    }

    // 思考模式下，API 若返回 reasoning_content 会自动显示在折叠面板中

    // 等待 RAG 检索完成（不阻塞流式输出，仅补充参考文献）
    await ragPromise;

    stopThinking();
    setLoading(false);
    // 最终更新，移除流式标记
    setMessages(prev => {
      const updated = [...prev];
      const last = { ...updated[updated.length - 1] };
      last.content = answer;
      last.reasoning = reasoning;
      last.sources = sources;
      delete last._streaming;
      updated[updated.length - 1] = last;
      return updated;
    });

    // 云端同步（后台，不阻塞 UI）
    saveChatMessage('user', question);
    saveChatMessage('assistant', answer, sources);

  };

  const handleClearChat = () => {
    const session = newConversation();
    sessionIdRef.current = session.id;
    setMessages([WELCOME_MSG]);
    setShowConfirmClear(false);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100dvh - 56px)', overflow: 'hidden' }}>
      {/* Top bar with clear button */}
      <div style={{ flexShrink: 0, display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '2px 12px', borderBottom: '1px solid var(--border)' }}>
        <span style={{ fontSize: 13, color: 'var(--text-dim)' }}>
          {messages.length > 1 ? `${messages.length} 条消息` : '新对话'}
        </span>
        <button className="btn btn-secondary" style={{ padding: '2px 8px', fontSize: 10 }}
          onClick={() => setThinkingMode(!thinkingMode)}
          title={thinkingMode ? '关闭思考模式' : '开启思考模式 (deepseek-r1)'}>
          {thinkingMode ? <><Icon name="brain" size={14} /> 思考中</> : <><Icon name="idea" size={14} /> 思考</>}
        </button>
        {messages.length > 1 && (
          showConfirmClear ? (
            <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
              <span style={{ fontSize: 12, color: 'var(--text-dim)' }}>清空对话？</span>
              <button className="btn btn-primary" style={{ padding: '2px 10px', fontSize: 11 }}
                onClick={handleClearChat}>确认</button>
              <button className="btn btn-secondary" style={{ padding: '2px 10px', fontSize: 11 }}
                onClick={() => setShowConfirmClear(false)}>取消</button>
            </div>
          ) : (
            <button className="btn btn-secondary" style={{ padding: '4px 10px', fontSize: 11 }}
              onClick={() => setShowConfirmClear(true)}><Icon name="icon-trash" size={16} /> 新对话</button>
          )
        )}
      </div>

      {/* 未配置 API Key 时显示加速提示 */}
      {!apiConfig.apiKey && (
        <div style={{ flexShrink: 0, padding: '6px 14px', fontSize: 12, color: 'var(--ochre)', background: 'color-mix(in srgb, var(--ochre) 6%, var(--bg))', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer' }}
          onClick={() => navigate('/settings')}>
          <Icon name="icon-tip" size={14} />
          当前使用服务器中转，响应较慢。点此配置你自己的 API Key 获得极速体验 →
        </div>
      )}

      <div className="chat-container" ref={chatRef} style={{ flex: 1, overflow: 'auto' }}>
        {messages.map((msg, i) => (
          <div key={i} className={`chat-message ${msg.role}`}>
            {msg.reasoning && (
              <details style={{ marginBottom: 8 }}>
                <summary style={{ fontSize: 11, color: 'var(--ochre)', cursor: 'pointer', userSelect: 'none' }}>
                  思考过程 {msg._streaming ? '...' : ''}
                </summary>
                <div style={{ fontSize: 11, color: 'var(--text-dim)', whiteSpace: 'pre-wrap', marginTop: 6, padding: '8px 10px', background: 'var(--bg)', borderRadius: 6, borderLeft: '2px solid var(--ochre)', maxHeight: 200, overflow: 'auto' }}>
                  {msg.reasoning}
                </div>
              </details>
            )}
            <div style={{ whiteSpace: 'pre-wrap' }}>{msg.content}</div>
            {Array.isArray(msg.sources) && msg.sources.length > 0 && (
              <div style={{
                marginTop: 10, paddingTop: 10,
                borderTop: '1px solid var(--border)',
                fontSize: 11, color: 'var(--text-dim)',
              }}>
                <Icon name="icon-link" size={16} /> <strong>参考文献：</strong>
                {msg.sources.map((s, j) => (
                  <span key={j} style={{
                    display: 'inline-block',
                    background: 'var(--secondary)',
                    padding: '2px 8px', borderRadius: 4,
                    margin: '2px 4px', color: 'var(--accent)',
                  }}>《{s}》</span>
                ))}
              </div>
            )}
          </div>
        ))}
        {loading && (
          <div className="chat-message assistant">
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{
                  width: 8, height: 8, borderRadius: '50%',
                  background: 'var(--accent)',
                  animation: 'pulse 0.8s ease-in-out infinite',
                }} />
                <span style={{
                  width: 8, height: 8, borderRadius: '50%',
                  background: 'var(--accent)',
                  animation: 'pulse 0.8s ease-in-out 0.2s infinite',
                }} />
                <span style={{
                  width: 8, height: 8, borderRadius: '50%',
                  background: 'var(--accent)',
                  animation: 'pulse 0.8s ease-in-out 0.4s infinite',
                }} />
              </div>
              <span style={{
                color: 'var(--text-dim)', fontSize: 12,
                transition: 'opacity 0.3s',
              }}>
                {thinkingPhase}
              </span>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="chat-input-area" style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '6px 12px', paddingBottom: 12, flexShrink: 0, background: 'var(--bg)', borderTop: '1px solid var(--border)' }}>
        <input
          className="chat-input"
          placeholder="输入哲学问题..."
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={loading}
          style={{ flex: 1, height: 42, lineHeight: '42px', padding: '0 16px', borderRadius: 20, border: '1px solid var(--border)', background: 'var(--card-bg)', color: 'var(--text)', fontSize: 14, fontFamily: 'inherit', outline: 'none' }}
        />
        <button
          className="chat-send-btn"
          onClick={sendMessage} disabled={loading}
          aria-label="发送"
          style={{ width: 42, height: 42, minWidth: 42, maxWidth: 42, minHeight: 42, maxHeight: 42, borderRadius: '50%', border: 'none', background: 'var(--ink)', color: 'var(--bone)', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, padding: 0 }}
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}><line x1="12" y1="19" x2="12" y2="5"/><polyline points="5 12 12 5 19 12"/></svg>
        </button>
      </div>
    </div>
  );
}

export default QAPage;
