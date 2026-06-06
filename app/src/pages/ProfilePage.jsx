/**
 * 个人中心 —— 阅读历史、聊天历史同步、登出
 */
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { getApiBase } from '../App';

function ProfilePage() {
  const { user, logout, getAuthHeaders } = useAuth();
  const navigate = useNavigate();
  const [tab, setTab] = useState('reading');
  const [readingHistory, setReadingHistory] = useState([]);
  const [chatHistory, setChatHistory] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!user) { navigate('/login'); return; }
    if (tab === 'reading') loadReadingHistory();
  }, [user, tab]);

  const loadReadingHistory = async () => {
    setLoading(true);
    try {
      const resp = await fetch(`${getApiBase()}/api/history/reading`, {
        headers: getAuthHeaders(),
      });
      if (resp.ok) {
        const data = await resp.json();
        setReadingHistory(data.history || []);
      }
    } catch (e) { console.error(e); }
    setLoading(false);
  };

  const loadChatHistory = async () => {
    setLoading(true);
    try {
      const resp = await fetch(`${getApiBase()}/api/history/chat`, {
        headers: getAuthHeaders(),
      });
      if (resp.ok) {
        const data = await resp.json();
        setChatHistory(data.messages || []);
      }
    } catch (e) { console.error(e); }
    setLoading(false);
  };

  const handleLogout = () => {
    logout();
    navigate('/books');
  };

  if (!user) return null;

  return (
    <div className="page-container">
      {/* 用户信息卡 */}
      <div className="card" style={{ cursor: 'default', textAlign: 'center' }}>
        <div style={{ fontSize: 48, marginBottom: 8 }}>👤</div>
        <h2 style={{ fontSize: 18, color: 'var(--accent)' }}>{user.username}</h2>
        <p style={{ fontSize: 12, color: 'var(--text-dim)' }}>哲学爱好者</p>
        <button className="btn btn-secondary" style={{ marginTop: 12, padding: '6px 20px', fontSize: 13 }}
          onClick={handleLogout}>退出登录</button>
      </div>

      {/* 标签切换 */}
      <div style={{ display: 'flex', gap: 8, margin: '16px 0' }}>
        {[
          { key: 'reading', label: '📖 阅读历史' },
          { key: 'chat', label: '💬 聊天历史' },
        ].map(t => (
          <button key={t.key}
            className={`btn ${tab === t.key ? 'btn-primary' : 'btn-secondary'}`}
            style={{ flex: 1, padding: '8px', fontSize: 13 }}
            onClick={() => { setTab(t.key); if (t.key === 'chat') loadChatHistory(); else loadReadingHistory(); }}>
            {t.label}
          </button>
        ))}
      </div>

      {/* 阅读历史 */}
      {tab === 'reading' && (
        <div>
          {loading ? <div className="loading">加载中...</div> :
           readingHistory.length === 0 ? <div className="empty-state"><p>暂无阅读记录</p></div> :
           readingHistory.map((item, i) => (
            <div key={i} className="card"
              style={{ cursor: 'pointer' }}
              onClick={() => {
                // 搜索对应书籍ID并跳转
                navigate('/books');
              }}>
              <div className="card-title" style={{ fontSize: 14 }}>{item.book_title}</div>
              <div className="card-subtitle">
                {item.book_author} · 进度: {Math.round(item.progress_percent * 100)}%
              </div>
              <div style={{ fontSize: 11, color: 'var(--text-dim)', marginTop: 4 }}>
                上次阅读: {item.last_read_at?.slice(0, 16)}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* 聊天历史 */}
      {tab === 'chat' && (
        <div>
          {loading ? <div className="loading">加载中...</div> :
           chatHistory.length === 0 ? <div className="empty-state"><p>暂无聊天记录</p></div> :
           chatHistory.map((msg, i) => (
            <div key={i} className={`chat-message ${msg.role}`}
              style={{
                maxWidth: '100%', marginBottom: 8,
                alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
              }}>
              <div style={{ whiteSpace: 'pre-wrap', fontSize: 13 }}>{msg.content}</div>
              {msg.sources && (
                <div className="chat-sources">📎 {msg.sources}</div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default ProfilePage;
