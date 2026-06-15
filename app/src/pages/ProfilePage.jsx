/**
 * 个人中心 —— 用户登录/注册、阅读历史、聊天历史
 * 登录后数据云端同步，未登录本地存储
 */
import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { getApiBase } from '../App';
import {
  getReadingHistory, getChatHistory, clearChatHistory,
  getAllUserData, relativeTime,
} from '../data/userData';

function ProfilePage() {
  const navigate = useNavigate();
  const [tab, setTab] = useState('reading');
  const [readingHistory, setReadingHistory] = useState([]);
  const [chatHistory, setChatHistory] = useState([]);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loggedIn, setLoggedIn] = useState(false);
  const [loginUser, setLoginUser] = useState('');
  const [authMsg, setAuthMsg] = useState('');
  const [syncing, setSyncing] = useState(false);

  // Restore login from token
  useEffect(() => {
    const token = localStorage.getItem('dp_token');
    const user = localStorage.getItem('dp_username');
    if (token && user) {
      setLoggedIn(true);
      setLoginUser(user);
      syncFromCloud(token);
    }
    loadLocalData();
  }, [tab]);

  const loadLocalData = () => {
    if (tab === 'reading') setReadingHistory(getReadingHistory());
    else setChatHistory(getChatHistory());
  };

  // ========== Auth ==========
  const api = (path, body) =>
    fetch(`${getApiBase()}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(10000),
    }).then(r => r.ok ? r.json() : r.json().then(e => { throw new Error(e.detail || '失败'); }));

  const handleRegister = async () => {
    if (!username.trim() || !password.trim()) { setAuthMsg('请填写用户名和密码'); return; }
    try {
      setAuthMsg('');
      const r = await api('/api/auth/register', { username, password });
      setAuthMsg(`注册成功！请登录 — ${r.username}`);
      setPassword('');
    } catch (e) { setAuthMsg(e.message); }
  };

  const handleLogin = async () => {
    if (!username.trim() || !password.trim()) { setAuthMsg('请填写用户名和密码'); return; }
    try {
      setAuthMsg('');
      const r = await api('/api/auth/login', { username, password });
      localStorage.setItem('dp_token', r.token);
      localStorage.setItem('dp_username', username);
      setLoggedIn(true);
      setLoginUser(username);
      setPassword('');
      setAuthMsg('');
      syncFromCloud(r.token);
    } catch (e) { setAuthMsg(e.message); }
  };

  const handleLogout = () => {
    localStorage.removeItem('dp_token');
    localStorage.removeItem('dp_username');
    setLoggedIn(false);
    setLoginUser('');
    setReadingHistory(getReadingHistory());
    setChatHistory(getChatHistory());
  };

  // ========== Cloud Sync ==========
  const syncFromCloud = async (token) => {
    setSyncing(true);
    try {
      // Pull reading history — normalize snake_case → camelCase
      const rh = await fetch(`${getApiBase()}/api/history/reading`, {
        headers: { 'Authorization': `Bearer ${token}` },
        signal: AbortSignal.timeout(10000),
      });
      if (rh.ok) {
        const d = await rh.json();
        const normalized = (d.history || []).map(h => ({
          bookId: h.book_id || h.id,
          bookTitle: h.book_title || '',
          bookAuthor: h.book_author || '',
          page: h.page || 0,
          percent: h.percent || 0,
          fileType: h.file_type || h.fileType || '',
          lastReadAt: h.last_read_at || h.lastReadAt || h.created_at || '',
        }));
        const local = JSON.parse(localStorage.getItem('dp_userdata') || '{}');
        local.readingHistory = normalized;
        localStorage.setItem('dp_userdata', JSON.stringify(local));
        if (tab === 'reading') setReadingHistory(normalized);
      }
      // Pull chat history
      const ch = await fetch(`${getApiBase()}/api/history/chat`, {
        headers: { 'Authorization': `Bearer ${token}` },
        signal: AbortSignal.timeout(10000),
      });
      if (ch.ok) {
        const d = await ch.json();
        const local = JSON.parse(localStorage.getItem('dp_userdata') || '{}');
        local.chatHistory = d.messages || [];
        localStorage.setItem('dp_userdata', JSON.stringify(local));
        if (tab === 'chat') setChatHistory(d.messages || []);
      }
    } catch {}
    setSyncing(false);
  };

  // Sync when logged in (called from reader/qa pages)
  useEffect(() => {
    window.syncReadingToCloud = async (bookId, bookTitle, bookAuthor, page, percent, fileType) => {
      const token = localStorage.getItem('dp_token');
      if (!token) return;
      try {
        await fetch(`${getApiBase()}/api/history/reading`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
          body: JSON.stringify({ book_id: bookId, book_title: bookTitle, book_author: bookAuthor, page, percent }),
          signal: AbortSignal.timeout(5000),
        });
      } catch {}
    };
    window.syncChatToCloud = async (role, content, sources) => {
      const token = localStorage.getItem('dp_token');
      if (!token) return;
      try {
        await fetch(`${getApiBase()}/api/history/chat`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
          body: JSON.stringify({ role, content, sources: sources ? JSON.stringify(sources) : '' }),
          signal: AbortSignal.timeout(5000),
        });
      } catch {}
    };
  }, [loggedIn]);

  const handleClearChat = () => {
    if (confirm('确定清空所有聊天历史？')) {
      clearChatHistory();
      if (loggedIn) {
        const token = localStorage.getItem('dp_token');
        fetch(`${getApiBase()}/api/history/chat`, {
          method: 'DELETE',
          headers: { 'Authorization': `Bearer ${token}` },
        }).catch(() => {});
      }
      setChatHistory([]);
    }
  };

  const userData = getAllUserData();

  return (
    <div className="page-container">
      {/* Auth Card */}
      <div className="card" style={{ cursor: 'default', textAlign: 'center' }}>
        {loggedIn ? (
          <>
            <div style={{ fontSize: 36, marginBottom: 4 }}>👤</div>
            <h2 style={{ fontSize: 18, color: 'var(--accent)' }}>{loginUser}</h2>
            <div style={{ fontSize: 11, color: 'var(--text-dim)', marginTop: 4 }}>
              {syncing ? '🔄 同步中...' : '☁️ 数据已云端同步'}
            </div>
            <div style={{ fontSize: 12, color: 'var(--text-dim)', marginTop: 8 }}>
              📖 {userData.readingHistory.length} 条阅读 · 💬 {userData.chatHistory.length} 条对话
            </div>
            <button className="btn btn-secondary" style={{ marginTop: 10, padding: '6px 20px', fontSize: 12 }}
              onClick={handleLogout}>退出登录</button>
          </>
        ) : (
          <>
            <div style={{ fontSize: 36, marginBottom: 4 }}>🔐</div>
            <h2 style={{ fontSize: 16, marginBottom: 12 }}>登录 / 注册</h2>
            <input
              placeholder="用户名"
              value={username}
              onChange={e => setUsername(e.target.value)}
              style={{ width: '100%', maxWidth: 260, padding: '8px 12px', borderRadius: 8,
                border: '1px solid var(--border)', background: 'var(--secondary)',
                color: 'var(--text)', fontSize: 14, marginBottom: 8, textAlign: 'center' }}
            />
            <input
              type="password"
              placeholder="密码"
              value={password}
              onChange={e => setPassword(e.target.value)}
              style={{ width: '100%', maxWidth: 260, padding: '8px 12px', borderRadius: 8,
                border: '1px solid var(--border)', background: 'var(--secondary)',
                color: 'var(--text)', fontSize: 14, marginBottom: 10, textAlign: 'center' }}
            />
            <div style={{ display: 'flex', gap: 8, justifyContent: 'center' }}>
              <button className="btn btn-primary" style={{ padding: '8px 24px', fontSize: 13 }}
                onClick={handleLogin}>登录</button>
              <button className="btn btn-secondary" style={{ padding: '8px 24px', fontSize: 13 }}
                onClick={handleRegister}>注册</button>
            </div>
            {authMsg && (
              <div style={{ fontSize: 12, marginTop: 8, color: authMsg.includes('成功') ? 'var(--success, #4caf50)' : 'var(--danger, #f44336)' }}>
                {authMsg}
              </div>
            )}
            <p style={{ fontSize: 11, color: 'var(--text-dim)', marginTop: 8 }}>
              一次注册，多设备同步阅读进度
            </p>
          </>
        )}
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 8, margin: '16px 0' }}>
        <button className={`btn ${tab === 'reading' ? 'btn-primary' : 'btn-secondary'}`}
          style={{ flex: 1, padding: '8px', fontSize: 13 }}
          onClick={() => setTab('reading')}>📖 阅读历史</button>
        <button className={`btn ${tab === 'chat' ? 'btn-primary' : 'btn-secondary'}`}
          style={{ flex: 1, padding: '8px', fontSize: 13 }}
          onClick={() => setTab('chat')}>💬 聊天历史</button>
      </div>

      {/* Reading History */}
      {tab === 'reading' && (
        readingHistory.length === 0 ? (
          <div className="empty-state"><p>暂无阅读记录</p></div>
        ) : (
          readingHistory.map((item, i) => (
            <div key={i} className="card" style={{ cursor: 'pointer' }}
              onClick={() => navigate('/reader/' + item.bookId)}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div className="card-title" style={{ fontSize: 14, flex: 1 }}>{item.bookTitle}</div>
                {item.fileType && (
                  <span style={{ fontSize: 10, padding: '2px 6px', borderRadius: 8,
                    background: item.fileType === 'pdf' ? 'var(--accent)' : 'var(--secondary)',
                    color: item.fileType === 'pdf' ? '#fff' : 'var(--text-dim)',
                  }}>{item.fileType.toUpperCase()}</span>
                )}
              </div>
              <div className="card-subtitle">
                {item.bookAuthor} 进度: {Math.round((item.percent || 0) * 100)}%
              </div>
              <div style={{ fontSize: 11, color: 'var(--text-dim)', marginTop: 4 }}>
                {relativeTime(item.lastReadAt)}
              </div>
            </div>
          ))
        )
      )}

      {/* Chat History */}
      {tab === 'chat' && (
        <>
          {chatHistory.length > 0 && (
            <button className="btn btn-secondary" style={{ marginBottom: 8, padding: '4px 12px', fontSize: 12 }}
              onClick={handleClearChat}>🗑 清空聊天</button>
          )}
          {chatHistory.length === 0 ? (
            <div className="empty-state"><p>暂无聊天记录</p></div>
          ) : (
            chatHistory.map((msg, i) => (
              <div key={i} className={`chat-message ${msg.role}`}
                style={{ maxWidth: '100%', marginBottom: 8, alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start' }}>
                <div style={{ whiteSpace: 'pre-wrap', fontSize: 13 }}>{msg.content}</div>
                {msg.sources?.length > 0 && (
                  <div className="chat-sources">📎 {msg.sources.join(', ')}</div>
                )}
              </div>
            ))
          )}
        </>
      )}
    </div>
  );
}

export default ProfilePage;
