/**
 * 问答分区 —— 直连 DeepSeek API，支持 Render RAG 作为优先源
 * 聊天历史本地自动保存
 */
import { useState, useRef, useEffect } from 'react';
import { getApiBase } from '../App';
import { saveChatMessage } from '../data/userData';

function QAPage() {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: '你好！我是 DeepPhilosophy 哲学助手。你可以向我提问任何哲学问题，我会基于知识库中的文献为你解答，并附上参考文献。\n\n💡 提示：在设置页面可以配置你自己的 API Key。',
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const chatRef = useRef(null);

  const getApiConfig = () => {
    try {
      return JSON.parse(localStorage.getItem('dp_api_config') || '{}');
    } catch { return {}; }
  };

  useEffect(() => {
    if (chatRef.current) {
      chatRef.current.scrollTop = chatRef.current.scrollHeight;
    }
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    const question = input.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: question }]);
    setLoading(true);

    try {
      const apiConfig = getApiConfig();
      const headers = { 'Content-Type': 'application/json' };
      let answer, sources = [];

      // Strategy 1: Local RAG backend (knowledge base retrieval + DeepSeek generation)
      try {
        const resp = await fetch(`${getApiBase()}/api/qa`, {
          method: 'POST', headers,
          body: JSON.stringify({
            question,
            api_key: apiConfig.apiKey || null,
            model: apiConfig.model || 'deepseek-chat',
          }),
          signal: AbortSignal.timeout(30000),
        });
        if (resp.ok) {
          const data = await resp.json();
          // Only accept if it's a real answer (not an error message)
          if (data.answer && !data.answer.includes('问答服务暂不可用') && !data.answer.includes('知识库尚未初始化')) {
            answer = data.answer;
            sources = data.sources || [];
          }
        }
      } catch (serverErr) {
        // Backend unavailable, fall through
      }

      // Strategy 2: Direct DeepSeek API (fallback, no knowledge base retrieval)
      if (!answer && apiConfig.apiKey) {
        try {
          const baseUrl = (apiConfig.apiUrl || 'https://api.deepseek.com').replace(/\/+$/, '');
          const directResp = await fetch(`${baseUrl}/v1/chat/completions`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${apiConfig.apiKey}` },
            body: JSON.stringify({
              model: apiConfig.model || 'deepseek-chat',
              messages: [
                { role: 'system', content: '你是一个哲学知识助手，精通中西方哲学。请用中文回答，回答要准确、有深度。' },
                { role: 'user', content: question },
              ],
              temperature: 0.7, max_tokens: 1024,
            }),
            signal: AbortSignal.timeout(30000),
          });
          if (directResp.ok) {
            const d = await directResp.json();
            answer = d.choices?.[0]?.message?.content;
          }
        } catch (directErr) {}
      }

      if (!answer) {
        answer = '无法获取回答。\n\n💡 请检查：\n1. 网络是否连通\n2. 在设置中填写 DeepSeek API Key\n3. 服务器是否可用';
      }

      // Save to local history
      saveChatMessage('user', question);
      saveChatMessage('assistant', answer, sources);

      setMessages(prev => [...prev, {
        role: 'assistant', content: answer, sources,
      }]);
    } catch (e) {
      setMessages(prev => [...prev, {
        role: 'assistant', content: '发生错误，请重试。',
        sources: [],
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - var(--header-height) - var(--nav-height))' }}>
      <div className="chat-container" ref={chatRef}>
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
            <span style={{ color: 'var(--text-dim)' }}>思考中...</span>
          </div>
        )}
      </div>

      <div className="chat-input-area">
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
