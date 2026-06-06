/**
 * 登录/注册页面
 */
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

function LoginPage() {
  const [isLogin, setIsLogin] = useState(true);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login, register } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    if (!username.trim() || !password.trim()) {
      setError('请填写所有字段'); return;
    }
    setLoading(true);
    try {
      if (isLogin) {
        await login(username.trim(), password);
      } else {
        await register(username.trim(), password);
        await login(username.trim(), password);
      }
      navigate('/profile');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page-container" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', paddingTop: 40 }}>
      <div style={{ fontSize: 48, marginBottom: 16 }}>📚</div>
      <h2 style={{ color: 'var(--accent)', marginBottom: 8 }}>
        {isLogin ? '登录' : '注册'}
      </h2>
      <p style={{ color: 'var(--text-dim)', fontSize: 13, marginBottom: 20 }}>同步你的阅读与聊天历史</p>

      {error && (
        <div style={{ background: 'var(--danger)', color: '#fff', padding: '8px 14px', borderRadius: 8, marginBottom: 14, fontSize: 13, width: '100%', maxWidth: 300 }}>
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} style={{ width: '100%', maxWidth: 300 }}>
        <input
          className="search-box"
          type="text"
          placeholder="用户名"
          value={username}
          onChange={e => setUsername(e.target.value)}
          autoComplete="username"
        />
        <input
          className="search-box"
          type="password"
          placeholder="密码"
          value={password}
          onChange={e => setPassword(e.target.value)}
          autoComplete={isLogin ? 'current-password' : 'new-password'}
        />
        <button className="btn btn-primary btn-block" type="submit" disabled={loading}
          style={{ marginTop: 8 }}>
          {loading ? '处理中...' : (isLogin ? '登录' : '注册')}
        </button>
      </form>

      <button
        style={{ background: 'none', border: 'none', color: 'var(--accent)', marginTop: 16, fontSize: 13, cursor: 'pointer' }}
        onClick={() => { setIsLogin(!isLogin); setError(''); }}
      >
        {isLogin ? '没有账号？去注册 →' : '已有账号？去登录 →'}
      </button>
    </div>
  );
}

export default LoginPage;
