import { useState } from 'react';
import { useAuth } from '../auth';
import { useLang } from '../utils/i18n';

/**
 * AuthModal — 登录 / 注册弹窗（朴素白 UI, 双语）
 */
export default function AuthModal({ onClose }) {
  const { login, register } = useAuth();
  const { t, lang } = useLang();
  const [mode, setMode] = useState('login');   // login | register
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  // 后端错误 detail 为中文——EN 模式映射为英文
  const mapErr = (msg) => {
    if (lang !== 'en' || !msg) return msg;
    if (msg.includes('用户名已存在')) return t('userExists');
    if (msg.includes('用户名或密码错误') || msg.includes('密码错误')) return t('wrongCreds');
    return msg;
  };

  const submit = async () => {
    if (busy) return;
    setError('');
    if (!username.trim() || !password) { setError(t('needUserPwd')); return; }
    setBusy(true);
    const d = mode === 'login'
      ? await login(username.trim(), password)
      : await register(username.trim(), password);
    setBusy(false);
    if (d.success) {
      if (mode === 'register') {
        // 注册成功后自动登录
        const l = await login(username.trim(), password);
        if (l.success) onClose();
        else setError(t('regAutoLoginFail'));
      } else {
        onClose();
      }
    } else {
      setError(mapErr(d.error || d.detail) || t('unknownErr'));
    }
  };

  return (
    <div onClick={onClose}
      style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,.35)', zIndex: 1000,
               display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 24 }}>
      <div onClick={e => e.stopPropagation()}
        style={{ background: 'var(--card-bg)', borderRadius: 14, width: '100%', maxWidth: 360, padding: '24px 28px',
                 boxShadow: '0 12px 40px rgba(0,0,0,.18)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 18 }}>
          <div style={{ fontSize: 17, fontWeight: 700 }}>{mode === 'login' ? t('signIn') : t('register')}</div>
          <span onClick={onClose} style={{ cursor: 'pointer', color: 'var(--text-dim)', fontSize: 14 }}>✕</span>
        </div>
        <div style={{ display: 'flex', gap: 6, marginBottom: 16 }}>
          {['login', 'register'].map(m => (
            <button key={m} onClick={() => { setMode(m); setError(''); }}
              style={{ flex: 1, padding: '7px 0', borderRadius: 8, cursor: 'pointer', fontSize: 13,
                       border: mode === m ? '1px solid var(--accent)' : '1px solid var(--border)',
                       background: mode === m ? 'var(--soft)' : 'var(--card-bg)',
                       color: mode === m ? 'var(--accent)' : 'var(--text-dim)' }}>
              {m === 'login' ? t('signIn') : t('register')}
            </button>
          ))}
        </div>
        <input value={username} onChange={e => setUsername(e.target.value)} placeholder={t('usernamePh')}
          style={{ width: '100%', padding: '10px 12px', borderRadius: 8, border: '1px solid var(--border)',
                   fontSize: 14, outline: 'none', marginBottom: 10, boxSizing: 'border-box' }} />
        <input value={password} onChange={e => setPassword(e.target.value)} type="password"
          placeholder={t('passwordPh')}
          onKeyDown={e => e.key === 'Enter' && submit()}
          style={{ width: '100%', padding: '10px 12px', borderRadius: 8, border: '1px solid var(--border)',
                   fontSize: 14, outline: 'none', marginBottom: 12, boxSizing: 'border-box' }} />
        {error && <div style={{ color: '#c0392b', fontSize: 12.5, marginBottom: 10 }}>{error}</div>}
        <button onClick={submit} disabled={busy}
          style={{ width: '100%', padding: '10px 0', borderRadius: 8, border: 'none', cursor: 'pointer',
                   background: 'var(--accent)', color: 'var(--bg)', fontSize: 14, opacity: busy ? 0.5 : 1 }}>
          {busy ? t('busy') : (mode === 'login' ? t('signIn') : t('regLogin'))}
        </button>
      </div>
    </div>
  );
}
