import { createContext, useContext, useState, useEffect, useRef } from 'react';
import { getApiBase } from './utils/api';
import { conversationStore } from './data/conversationStore';
import { ConversationSync } from './data/conversationSync';
import { accountProfile, profilePatch, clearDeviceCache, deleteConversationHistory } from './data/accountSettings';

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
  const [accountReady, setAccountReady] = useState(false);
  const [historyStatus, setHistoryStatus] = useState('local');
  const [authError, setAuthError] = useState(false);
  const [verifyAttempt, setVerifyAttempt] = useState(0);
  const syncRef = useRef(null);
  const legacyUser = useRef(localStorage.getItem(USER_KEY));
  const tokenRef = useRef(token);
  tokenRef.current = token;

  useEffect(() => {
    if (token && !profile?.id) { setAccountReady(false); return; }
    const owner = token ? `local-user:${profile.id}` : 'guest';
    conversationStore.setScope(owner, token ? legacyUser.current === profile.username : !legacyUser.current);
    conversationStore.migrateLegacy();
    setAccountReady(true);
    window.dispatchEvent(new Event('phiagent-account-changed'));
    if (!token) { setHistoryStatus('local'); return; }
    const session = new ConversationSync(conversationStore, {
      owner, token, onStatus: setHistoryStatus,
      onChange: () => window.dispatchEvent(new Event('phiagent-history-restored')),
    });
    syncRef.current = session;
    session.hydrate();
    const retry = () => { if (session.active()) session.hydrate(); };
    const flush = () => session.flush().catch(() => {});
    const onVisibility = () => document.visibilityState === 'hidden' ? flush() : retry();
    window.addEventListener('online', retry);
    window.addEventListener('pagehide', flush);
    document.addEventListener('visibilitychange', onVisibility);
    return () => {
      session.close(); syncRef.current = null;
      window.removeEventListener('online', retry);
      window.removeEventListener('pagehide', flush);
      document.removeEventListener('visibilitychange', onVisibility);
    };
  }, [token, profile?.id]);

  // 启动时校验 token
  useEffect(() => {
    const controller = new AbortController();
    setAuthError(false);
    if (token) {
      authFetch('/api/auth/profile', { signal: controller.signal })
        .then(d => {
          if (controller.signal.aborted || tokenRef.current !== token) return;
          if (d && d.username && d.id) {
            setProfile(accountProfile(d));
            setUsername(d.username);
            localStorage.setItem(USER_KEY, d.username);
          } else {
            logout();
          }
        })
        .catch(() => { if (!controller.signal.aborted && tokenRef.current === token) setAuthError(true); });
    }
    return () => controller.abort();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token, verifyAttempt]);

  async function authFetch(path, options = {}) {
    const requestToken = token;
    const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const resp = await fetch(`${getApiBase()}${path}`, { ...options, headers });
    if (resp.status === 401 && requestToken) {
      // token 失效 → 自动登出
      if (tokenRef.current === requestToken) logout();
      return { error: '登录已过期' };
    }
    const data = await resp.json().catch(() => ({}));
    if (!resp.ok && !path.endsWith('/login') && !path.endsWith('/register')) {
      const error = new Error('Account request failed');
      error.status = resp.status;
      throw error;
    }
    return data;
  }

  async function login(name, pass) {
    const d = await authFetch('/api/auth/login', {
      method: 'POST', body: JSON.stringify({ username: name, password: pass }),
    });
    if (d.success) {
      tokenRef.current = d.token;
      setToken(d.token);
      setUsername(d.username);
      setProfile(null);
      setAccountReady(false);
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
    tokenRef.current = null;
    window.dispatchEvent(new Event('phiagent-logout'));
    syncRef.current?.close();
    syncRef.current = null;
    setToken(null); setUsername(null); setProfile(null);
    setAccountReady(false);
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    // Account caches/outboxes remain owner-scoped until server save succeeds.
    // Guest and other accounts never read them. Never erase unsaved history.
  }

  async function updateProfile(fields) {
    const ownerToken = tokenRef.current;
    if (!ownerToken || !accountReady) throw new Error('Account not ready');
    const values = profilePatch(fields);
    const result = await authFetch('/api/auth/profile', { method: 'PUT', body: JSON.stringify(values) });
    if (tokenRef.current !== ownerToken) throw new Error('Account changed');
    if (!result.success) throw new Error('Could not save profile');
    setProfile(previous => ({ ...previous, ...values, ...profilePatch(result.profile) }));
    return result;
  }

  async function deleteAccount() {
    const ownerToken = tokenRef.current;
    if (!ownerToken || !accountReady) throw new Error('Account not ready');
    const ownedSync = syncRef.current;
    const ownedKey = conversationStore.key;
    const ownedMeta = ownedSync?.metaKey || `phiagent_sync_v2:${conversationStore.owner}`;
    const result = await authFetch('/api/auth/account', { method: 'DELETE' });
    if (!result.success) throw new Error('Account deletion failed');
    await ownedSync?.discard();
    localStorage.removeItem(ownedKey);
    localStorage.removeItem(ownedMeta);
    if (tokenRef.current === ownerToken) logout();
  }

  return (
    <AuthContext.Provider value={{ token, username, profile, accountReady, historyStatus, authError,
      retryAccount: () => setVerifyAttempt(n => n + 1), login, register, logout, authFetch, updateProfile, deleteAccount,
      clearDeviceCache: () => {
        if (token && !syncRef.current) throw new Error('SYNC_PENDING');
        return clearDeviceCache(conversationStore, syncRef.current, localStorage);
      },
      deleteConversationHistory: () => {
        if (token && !syncRef.current) return Promise.reject(new Error('HISTORY_BUSY'));
        return deleteConversationHistory(conversationStore, syncRef.current);
      },
      ensureConversation: id => syncRef.current ? syncRef.current.ensureConversation(id) : Promise.reject(new Error('Account not ready')),
      beginHistoryStream: id => syncRef.current?.beginStream(id),
      endHistoryStream: id => syncRef.current?.endStream(id),
      retryHistory: () => syncRef.current?.hydrate() }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
