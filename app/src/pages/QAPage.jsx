/**
 * 问答分区 —— 直连 DeepSeek API，支持 Render RAG 作为优先源
 * 聊天历史本地自动保存
 */
import { useState, useRef, useEffect } from 'react';
import { getApiBase } from '../App';
import { saveChatMessage, getChatHistory, clearChatHistory } from '../data/userData';

const WELCOME_MSG = {
  role: 'assistant',
  content: '你好！我是 DeepPhilosophy 哲学助手。你可以向我提问任何哲学问题，我会基于知识库中的文献为你解答，并附上参考文献。\n\n💡 提示：在设置页面可以配置你自己的 API Key。',
};

function QAPage() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [thinkingPhase, setThinkingPhase] = useState('');
  const [showConfirmClear, setShowConfirmClear] = useState(false);
  const chatRef = useRef(null);
  const thinkingTimer = useRef(null);

  // 思考阶段动画
  const thinkingPhases = [
    '🔍 检索相关文献...',
    '📖 分析文档内容...',
    '💭 深度思考中...',
    '✍️ 组织回答...',
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

  // Load saved chat history on mount (behaves like all normal AI clients)
  useEffect(() => {
    const history = getChatHistory();
    if (history.length > 0) {
      const msgs = history.map(m => ({
        role: m.role,
        content: m.content,
        sources: m.sources || [],
      }));
      setMessages(msgs);
    } else {
      setMessages([WELCOME_MSG]);
    }
  }, []);

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
    const userMsg = { role: 'user', content: question };
    setMessages(prev => [...prev, userMsg]);
    // 占位消息，后续流式更新
    setMessages(prev => [...prev, { role: 'assistant', content: '', sources: [], _streaming: true }]);
    setLoading(true);
    startThinking();

    let answer = '';
    let sources = [];

    const baseUrl = (apiConfig.apiUrl || 'https://api.deepseek.com').replace(/\/+$/, '');
    const streamBody = {
      model: apiConfig.model || 'deepseek-chat',
      messages: [
        { role: 'system', content: '你是一个哲学知识助手，精通中西方哲学。请用中文回答，回答要准确、有深度。如果用户询问特定著作或哲学家，请详细阐述其核心思想。' },
        { role: 'user', content: question },
      ],
      temperature: 0.7, max_tokens: 1024,
      stream: true,
    };

    // 尝试 RAG 后端（非流式，快速获取检索来源）, then 直接流式 API
    try {
      const ragResp = await fetch(`${getApiBase()}/api/qa`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question, api_key: apiConfig.apiKey || null }),
        signal: AbortSignal.timeout(10000),
      });
      if (ragResp.ok) {
        const d = await ragResp.json();
        if (d.sources?.length > 0) sources = d.sources;
      }
    } catch {}

    // 流式调用 DeepSeek API
    try {
      if (apiConfig.apiKey) {
        const resp = await fetch(`${baseUrl}/v1/chat/completions`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${apiConfig.apiKey}` },
          body: JSON.stringify(streamBody),
          signal: AbortSignal.timeout(60000),
        });

        if (resp.ok) {
          const reader = resp.body.getReader();
          const decoder = new TextDecoder();
          let buffer = '';

          while (true) {
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
                  const delta = json.choices?.[0]?.delta?.content || '';
                  if (delta) {
                    answer += delta;
                    // 逐字更新最后一条消息
                    setMessages(prev => {
                      const updated = [...prev];
                      const last = { ...updated[updated.length - 1] };
                      last.content = answer;
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
      }
    } catch (e) {}

    if (!answer) {
      answer = '无法获取回答。\n\n请检查网络连接或在设置中配置 API Key。';
    }

    stopThinking();
    setLoading(false);
    // 最终更新，移除流式标记
    setMessages(prev => {
      const updated = [...prev];
      const last = { ...updated[updated.length - 1] };
      last.content = answer;
      last.sources = sources;
      delete last._streaming;
      updated[updated.length - 1] = last;
      return updated;
    });

    // Save history
    saveChatMessage('user', question);
    saveChatMessage('assistant', answer, sources);
  };

  const handleClearChat = () => {
    clearChatHistory();
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
    <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100dvh - 116px)', overflow: 'hidden', margin: '-16px -32px' }}>
      {/* Top bar with clear button */}
      <div style={{ flexShrink: 0, display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '2px 12px', borderBottom: '1px solid var(--border)' }}>
        <span style={{ fontSize: 13, color: 'var(--text-dim)' }}>
          {messages.length > 1 ? `${messages.length} 条消息` : '新对话'}
        </span>
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
              onClick={() => setShowConfirmClear(true)}>🗑 新对话</button>
          )
        )}
      </div>

      <div className="chat-container" ref={chatRef} style={{ flex: 1, overflow: 'auto' }}>
        {messages.map((msg, i) => (
          <div key={i} className={`chat-message ${msg.role}`}>
            <div style={{ whiteSpace: 'pre-wrap' }}>{msg.content}</div>
            {msg.sources && msg.sources.length > 0 && (
              <div style={{
                marginTop: 10, paddingTop: 10,
                borderTop: '1px solid var(--border)',
                fontSize: 11, color: 'var(--text-dim)',
              }}>
                📎 <strong>参考文献：</strong>
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

      <div className="chat-input-area" style={{ position: 'static', flexShrink: 0, padding: '6px 12px', paddingBottom: 12 }}>
        <input
          className="chat-input"
          placeholder="输入哲学问题..."
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={loading}
        />
        <button className="chat-send-btn" onClick={sendMessage} disabled={loading}>
          ↑
        </button>
      </div>
    </div>
  );
}

export default QAPage;
