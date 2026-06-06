/**
 * 问答分区 —— RAG智能问答，答案始终附带参考文献
 * 登录后自动同步聊天历史到云端
 */
import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { getApiBase } from '../App';

function QAPage() {
  const { user, getAuthHeaders } = useAuth();
  const navigate = useNavigate();
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
      const headers = { 'Content-Type': 'application/json', ...getAuthHeaders() };
      const resp = await fetch(`${getApiBase()}/api/qa`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          question,
          api_key: apiConfig.apiKey || null,
          model: apiConfig.model || 'deepseek-chat',
        }),
      });
      const data = await resp.json();

      const answer = data.answer || '抱歉，无法获取回答。';
      const sources = data.sources || [];

      setMessages(prev => [...prev, {
        role: 'assistant',
        content: answer,
        sources: sources,
      }]);
    } catch (e) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: '网络连接失败，请确认后端服务正在运行。\n\n💡 请检查：\n1. 服务器地址是否正确\n2. 网络是否连通',
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
        {!user && (
          <div style={{
            textAlign: 'center', padding: '8px 16px', marginBottom: 8,
            background: 'var(--secondary)', borderRadius: 8,
            fontSize: 12, color: 'var(--text-dim)',
          }}>
            💡 <span style={{ color: 'var(--accent)', cursor: 'pointer', textDecoration: 'underline' }}
              onClick={() => navigate('/login')}>登录</span>后可同步聊天历史到云端
          </div>
        )}
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
