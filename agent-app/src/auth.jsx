import { createContext, useContext, useState, useEffect } from 'react';
import { getApiBase } from './utils/api';

/**
 * AuthContext — 用户系统（注册/登录/档案/登出）
 * token 存 localStorage, 请求自动带 Bearer; 401 自动登出
 */
const AuthContext = createContext(null);
const TOKEN_KEY = 'phiagent_token';
const USER_KEY = 'phiagent_user';

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY));
  const [username, setUsername] = useState(() => localStorage.getItem(USER_KEY));
  const [profile, setProfile] = useState(null);

  // 启动时校验 token
  useEffect(() => {
    if (token && !profile) {
      authFetch('/api/auth/profile')
        .then(d => {
          if (d && d.username) {
            setProfile(d);
            setUsername(d.username);
            localStorage.setItem(USER_KEY, d.username);
          } else {
            logout();
          }
        })
        .catch(() => {});
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  async function authFetch(path, options = {}) {
    const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const resp = await fetch(`${getApiBase()}${path}`, { ...options, headers });
    if (resp.status === 401 && token) {
      // token 失效 → 自动登出
      logout();
      return { error: '登录已过期' };
    }
    return resp.json().catch(() => ({}));
  }

  async function login(name, pass) {
    const d = await authFetch('/api/auth/login', {
      method: 'POST', body: JSON.stringify({ username: name, password: pass }),
    });
    if (d.success) {
      setToken(d.token);
      setUsername(d.username);
      setProfile({ username: d.username });
      localStorage.setItem(TOKEN_KEY, d.token);
      localStorage.setItem(USER_KEY, d.username);
    }
    return d;
  }

  async function register(name, pass) {
    return authFetch('/api/auth/register', {
      method: 'POST', body: JSON.stringify({ username: name, password: pass }),
    });
  }

  function logout() {
    setToken(null); setUsername(null); setProfile(null);
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    // 隐私（2026-08-30）: 登出即清空本机对话痕迹（会话/草稿/legacy 键）,
    // 并广播给工作区重置内存态——退出后同浏览器他人不可见对话记录
    try {
      localStorage.removeItem('phiagent_conversations_v1');
      localStorage.removeItem('dp_chat_sessions');
      localStorage.removeItem('dp_current_session');
      Object.keys(localStorage)
        .filter((k) => k.startsWith('dp_agent_msgs_v2_'))
        .forEach((k) => localStorage.removeItem(k));
    } catch (e) { /* 隐私清理由 auth 保证, 存储异常不阻塞登出 */ }
    window.dispatchEvent(new Event('phiagent-logout'));
  }

  return (
    <AuthContext.Provider value={{ token, username, profile, login, register, logout, authFetch }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
