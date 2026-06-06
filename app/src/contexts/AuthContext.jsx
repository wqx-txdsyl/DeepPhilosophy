/**
 * AuthContext —— 全局认证状态管理
 * 提供登录/注册/登出/用户信息 给所有子组件
 */
import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { getApiBase } from '../App';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);

  // 启动时从 localStorage 恢复登录状态
  useEffect(() => {
    const saved = localStorage.getItem('dp_user');
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        setToken(parsed.token);
        setUser({ username: parsed.username });
      } catch {}
    }
    setLoading(false);
  }, []);

  const login = useCallback(async (username, password) => {
    const resp = await fetch(`${getApiBase()}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });
    const data = await resp.json();
    if (!resp.ok) throw new Error(data.detail || '登录失败');
    setToken(data.token);
    setUser({ username: data.username });
    localStorage.setItem('dp_user', JSON.stringify({ token: data.token, username: data.username }));
    return data;
  }, []);

  const register = useCallback(async (username, password) => {
    const resp = await fetch(`${getApiBase()}/api/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });
    const data = await resp.json();
    if (!resp.ok) throw new Error(data.detail || '注册失败');
    return data;
  }, []);

  const logout = useCallback(() => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('dp_user');
    localStorage.removeItem('dp_chat_history');
  }, []);

  const getAuthHeaders = useCallback(() => {
    return token ? { Authorization: `Bearer ${token}` } : {};
  }, [token]);

  return (
    <AuthContext.Provider value={{ user, token, loading, login, register, logout, getAuthHeaders }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
