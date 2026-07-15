/**
 * 个人中心 —— 用户登录/注册、阅读历史、聊天历史
 * 登录后数据云端同步，未登录本地存储
 */
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getApiBase } from '../App';
import Icon from '../components/Icon';
import AvatarUpload from '../components/AvatarUpload';
import { useToast } from '../contexts/ToastContext';
import {
  getReadingHistory, getChatHistory, clearChatHistory,
  getAllUserData, relativeTime,
} from '../data/userData';

function ProfilePage() {
  const navigate = useNavigate();
  const toast = useToast();
  const [tab, setTab] = useState('reading');
  const [readingHistory, setReadingHistory] = useState([]);
  const [chatHistory, setChatHistory] = useState([]);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loggedIn, setLoggedIn] = useState(false);
  const [loginUser, setLoginUser] = useState('');
  const [authMsg, setAuthMsg] = useState('');
  const [syncing, setSyncing] = useState(false);
  const [checking, setChecking] = useState(true);  // 正在验证登录状态

  // Restore login from token — verify with backend (只执行一次)
  useEffect(() => {
    const token = localStorage.getItem('dp_token');
    const user = localStorage.getItem('dp_username');
    if (token && user) {
      // 先验证 token 是否仍然有效
      fetch(`${getApiBase()}/api/auth/profile`, {
        headers: { 'Authorization': `Bearer ${token}` },
        signal: AbortSignal.timeout(6000),
      }).then(r => {
        setChecking(false);
        if (r.ok) {
          setLoggedIn(true);
          setLoginUser(user);
          syncFromCloud(token, false);
        } else {
          // Token 失效 → 不清除本地凭据！仅显示未登录状态
          // （后端可能刚重启，等几秒重试就能恢复；清除会导致反复登录）
          setLoggedIn(false);
          setLoginUser(user);
        }
      }).catch(() => {
        setChecking(false);
        // 网络错误 → 保持登录状态，使用本地缓存
        setLoggedIn(true);
        setLoginUser(user);
      });
    } else {
      setChecking(false);
    }
    setReadingHistory(getReadingHistory());
    setChatHistory(getChatHistory());
  }, []); // 只在挂载时运行，切换 tab 不重复请求

  const switchTab = (t) => {
    setTab(t);
    window.scrollTo(0, 0);
    const m = document.querySelector('.app-main');
    if (m) m.style.transform = 'translateY(0)';
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
      syncFromCloud(r.token, true);  // fresh login: replace with cloud data
    } catch (e) { setAuthMsg(e.message); }
  };

  const handleLogout = () => {
    localStorage.removeItem('dp_token');
    localStorage.removeItem('dp_username');
    // 清除本地用户数据
    const data = JSON.parse(localStorage.getItem('dp_userdata') || '{}');
    data.readingHistory = [];
    data.chatHistory = [];
    localStorage.setItem('dp_userdata', JSON.stringify(data));
    setLoggedIn(false);
    setLoginUser('');
    setReadingHistory([]);
    setChatHistory([]);
  };

  // ========== Cloud Sync ==========
  // isFreshLogin=true: 新登录 → 云端数据完全替换本地（切换账号场景）
  // isFreshLogin=false: token恢复 → 合并，避免云端为空时清空本地数据
  const syncFromCloud = async (token, isFreshLogin = false) => {
    setSyncing(true);
    try {
      // Pull reading history — normalize snake_case → camelCase
      const rh = await fetch(`${getApiBase()}/api/history/reading`, {
        headers: { 'Authorization': `Bearer ${token}` },
        signal: AbortSignal.timeout(10000),
      });
      if (rh.ok) {
        const d = await rh.json();
        const cloudHistory = (d.history || []).map(h => ({
          bookId: h.book_id || '',
          bookTitle: h.book_title || '',
          bookAuthor: h.book_author || '',
          page: h.progress_page || h.page || 0,
          percent: h.progress_percent || h.percent || 0,
          fileType: h.file_type || h.fileType || '',
          lastReadAt: h.last_read_at || h.lastReadAt || h.created_at || '',
        }));
        const local = JSON.parse(localStorage.getItem('dp_userdata') || '{}');
        const localHistory = local.readingHistory || [];
        if (isFreshLogin || cloudHistory.length > 0) {
          // 新登录或云端有数据 → 云端优先，但保留本地独有的
          const cloudIds = new Set(cloudHistory.map(h => h.bookId));
          const merged = [...cloudHistory];
          for (const h of localHistory) {
            if (h.bookId && !cloudIds.has(h.bookId)) {
              merged.push(h);
            }
          }
          local.readingHistory = merged;
        }
        // 云端为空且非新登录 → 保留本地数据不变
        localStorage.setItem('dp_userdata', JSON.stringify(local));
        setReadingHistory(local.readingHistory || localHistory);
      }
      // Pull chat history
      const ch = await fetch(`${getApiBase()}/api/history/chat`, {
        headers: { 'Authorization': `Bearer ${token}` },
        signal: AbortSignal.timeout(10000),
      });
      if (ch.ok) {
        const d = await ch.json();
        // 规范化 sources：云端存储的是 JSON 字符串，需转回数组
        const _normalizeSources = (src) => {
          if (Array.isArray(src)) return src;
          if (typeof src === 'string') {
            try { return JSON.parse(src); } catch { return []; }
          }
          return [];
        };
        const cloudChat = (d.messages || []).map(m => ({
          ...m,
          sources: _normalizeSources(m.sources),
        }));
        const local = JSON.parse(localStorage.getItem('dp_userdata') || '{}');
        const localChat = local.chatHistory || [];
        if (isFreshLogin || cloudChat.length > 0) {
          local.chatHistory = cloudChat;
        }
        localStorage.setItem('dp_userdata', JSON.stringify(local));
        setChatHistory(local.chatHistory || localChat);
      }
      // Pull book notes
      const notes = await fetch(`${getApiBase()}/api/notes`, {
        headers: { 'Authorization': `Bearer ${token}` },
        signal: AbortSignal.timeout(10000),
      });
      if (notes.ok) {
        const d = await notes.json();
        Object.entries(d.notes || {}).forEach(([bid, txt]) => {
          if (txt) localStorage.setItem(`dp_notes_${bid}`, txt);
        });
      }
      // Pull avatar
      try {
        const ar = await fetch(`${getApiBase()}/api/user/avatar`, {
          headers: { 'Authorization': `Bearer ${token}` },
          signal: AbortSignal.timeout(5000),
        });
        if (ar.ok) {
          const ad = await ar.json();
          if (ad.avatar) localStorage.setItem('dp_avatar', ad.avatar);
        }
      } catch {}
    } catch {}
    setSyncing(false);
  };

  const handleClearChat = () => {
    // Use browser confirm for destructive action (with toast feedback after)
    if (window.confirm('确定清空所有聊天历史？此操作不可撤销。')) {
      clearChatHistory();
      if (loggedIn) {
        const token = localStorage.getItem('dp_token');
        fetch(`${getApiBase()}/api/history/chat`, {
          method: 'DELETE',
          headers: { 'Authorization': `Bearer ${token}` },
        }).catch(() => {});
      }
      setChatHistory([]);
      toast.success('聊天历史已清空');
    }
  };

  const userData = getAllUserData();

  return (
    <div className="page-container">
      {/* Auth Card */}
      <div className="card" style={{ cursor: 'default', textAlign: 'center' }}>
        {loggedIn ? (
          <>
            <AvatarUpload size={72} onSave={(dataUrl) => {
            // 云端同步头像
            const token = localStorage.getItem('dp_token');
            if (token) {
              fetch(`${getApiBase()}/api/user/avatar`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
                body: JSON.stringify({ avatar: dataUrl }),
                signal: AbortSignal.timeout(10000),
              }).catch(() => {});
            }
          }} />
            <h2 style={{ fontSize: 18, color: 'var(--accent)' }}>{loginUser}</h2>
            <div style={{ fontSize: 11, color: 'var(--text-dim)', marginTop: 4 }}>
              {syncing ? <><Icon name="icon-refresh" size={14} /> 同步中...</> : <><Icon name="icon-cloud" size={14} /> 数据已云端同步</>}
            </div>
            <div style={{ fontSize: 12, color: 'var(--text-dim)', marginTop: 8 }}>
              <Icon name="icon-book-open" size={14} /> {userData.readingHistory.length} 条阅读 · <Icon name="nav-qa" size={14} /> {userData.chatHistory.length} 条对话
            </div>
            <button className="btn btn-secondary" style={{ marginTop: 10, padding: '6px 20px', fontSize: 12 }}
              onClick={handleLogout}>退出登录</button>
            {loginUser === 'txdsyl_' && (
              <button className="btn btn-primary" style={{ marginTop: 6, padding: '6px 20px', fontSize: 12 }}
                onClick={() => navigate('/DEVELOPER_IS_TXDSYL')}><Icon name="wrench" size={16} /> 开发者后台</button>
            )}
          </>
        ) : checking ? (
          // 正在验证 token...
          <div style={{ textAlign: 'center', padding: 20 }}>
            <div style={{ width:28, height:28, border:'2px solid var(--border)', borderTopColor:'var(--accent)', borderRadius:'50%', animation:'spin 0.8s linear infinite', margin:'0 auto 12px' }} />
            <p style={{ fontSize:13, color:'var(--text-dim)' }}>验证登录状态...</p>
          </div>
        ) : loginUser && !loggedIn ? (
          // Token 验证失败（后端可能刚重启），显示重试
          <>
            <div style={{ fontSize: 36, marginBottom: 4 }}><Icon name="icon-refresh" size={36} /></div>
            <h2 style={{ fontSize: 16, marginBottom: 8 }}>{loginUser}</h2>
            <p style={{ fontSize: 13, color: 'var(--text-dim)', marginBottom: 16, maxWidth: 260 }}>
              会话已过期，请重新登录
            </p>
            <button className="btn btn-secondary" style={{ padding: '6px 20px', fontSize: 12, marginBottom: 8 }}
              onClick={() => {
                // 重试：重新检查 token
                setChecking(true);
                const t = localStorage.getItem('dp_token');
                if (t) {
                  fetch(`${getApiBase()}/api/auth/profile`, {
                    headers: { 'Authorization': `Bearer ${t}` },
                    signal: AbortSignal.timeout(6000),
                  }).then(r => {
                    setChecking(false);
                    if (r.ok) { setLoggedIn(true); setLoginUser(localStorage.getItem('dp_username')||''); }
                    else { setLoggedIn(false); }
                  }).catch(() => { setChecking(false); setLoggedIn(true); });
                } else { setChecking(false); }
              }}><Icon name="refresh" size={16} /> 重试</button>
            <button className="btn btn-danger" style={{ padding: '6px 20px', fontSize: 12 }}
              onClick={() => {
                localStorage.removeItem('dp_token');
                localStorage.removeItem('dp_username');
                setLoginUser('');
                setLoggedIn(false);
              }}>退出并重新登录</button>
          </>
        ) : (
          // 未登录状态
          <>
            <div style={{ fontSize: 36, marginBottom: 4 }}><Icon name="icon-lock-key" size={36} /></div>
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
          onClick={() => switchTab('reading')}><Icon name="icon-book-open" size={16} /> 阅读历史</button>
        <button className={`btn ${tab === 'chat' ? 'btn-primary' : 'btn-secondary'}`}
          style={{ flex: 1, padding: '8px', fontSize: 13 }}
          onClick={() => switchTab('chat')}><Icon name="nav-qa" size={16} /> 聊天历史</button>
      </div>

      {/* Reading History */}
      {tab === 'reading' && (
        readingHistory.length === 0 ? (
          <div className="empty-state"><p>暂无阅读记录</p></div>
        ) : (
          <>
            <button className="btn btn-secondary" style={{ marginBottom: 8, padding: '4px 12px', fontSize: 12 }}
              onClick={() => {
                if (!window.confirm('确定清空所有阅读记录？此操作不可撤销。')) return;
                const d = JSON.parse(localStorage.getItem('dp_userdata') || '{}');
                d.readingHistory = [];
                localStorage.setItem('dp_userdata', JSON.stringify(d));
                setReadingHistory([]);
                toast.success('阅读记录已清空');
              }}><Icon name="icon-trash" size={14} /> 清空阅读记录</button>
            {readingHistory.map((item, i) => (
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
          ))}
          </>
        )
      )}

      {/* Chat History */}
      {tab === 'chat' && (
        <div key="chat-tab">
          {(Array.isArray(chatHistory) && chatHistory.length > 0) && (
            <button className="btn btn-secondary" style={{ marginBottom: 8, padding: '4px 12px', fontSize: 12 }}
              onClick={handleClearChat}><Icon name="icon-trash" size={14} /> 清空聊天</button>
          )}
          {(!Array.isArray(chatHistory) || chatHistory.length === 0) ? (
            <div className="empty-state"><p>暂无聊天记录</p><p style={{fontSize:12,color:'var(--text-dim)'}}>在问答页面进行的对话会自动保存在这里</p></div>
          ) : (
            chatHistory.map((msg, i) => (
              <div key={i} className={`chat-message ${msg.role}`}
                style={{ maxWidth: '100%', marginBottom: 8, alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start' }}>
                <div style={{ whiteSpace: 'pre-wrap', fontSize: 13 }}>{msg.content}</div>
                {Array.isArray(msg.sources) && msg.sources.length > 0 && (
                  <div className="chat-sources"><Icon name="icon-link" size={14} /> {msg.sources.join(', ')}</div>
                )}
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}

export default ProfilePage;
