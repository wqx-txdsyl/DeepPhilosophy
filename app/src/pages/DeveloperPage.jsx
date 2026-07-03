/**
 * 开发者管理后台 — 访问统计 + 用户管理
 */
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getApiBase } from '../App';
import Icon from '../components/Icon';

function DeveloperPage() {
  const navigate = useNavigate();
  const [password, setPassword] = useState('');
  const [authed, setAuthed] = useState(false);
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  const [error, setError] = useState('');

  const fetchData = async (pw) => {
    setLoading(true);
    try {
      const r = await fetch(`${getApiBase()}/api/admin/stats?password=${encodeURIComponent(pw)}`);
      if (r.ok) {
        const d = await r.json();
        setData(d);
        setAuthed(true);
        setError('');
      } else {
        setError('密码错误');
      }
    } catch { setError('无法连接后端'); }
    setLoading(false);
  };

  const handleLogin = (e) => {
    e.preventDefault();
    fetchData(password);
  };

  useEffect(() => {
    const saved = localStorage.getItem('dp_admin_pw');
    if (saved) { setPassword(saved); fetchData(saved); }
  }, []);

  useEffect(() => {
    if (authed && password) localStorage.setItem('dp_admin_pw', password);
  }, [authed]);

  if (!authed) {
    return (
      <div className="page-container" style={{ maxWidth: 400, margin: '80px auto', textAlign: 'center' }}>
        <h2 style={{ fontSize: 20, marginBottom: 16 }}>🔐 开发者后台</h2>
        <form onSubmit={handleLogin}>
          <input type="password" value={password} onChange={e => setPassword(e.target.value)}
            placeholder="管理员密码" autoFocus
            style={{ width: '100%', padding: '12px 16px', borderRadius: 8, border: '1px solid var(--border)', background: 'var(--secondary)', color: 'var(--text)', fontSize: 15, marginBottom: 12, textAlign: 'center', outline: 'none' }} />
          <button className="btn btn-primary btn-block" type="submit" disabled={loading}
            style={{ padding: '10px', fontSize: 14 }}>{loading ? '验证中...' : '进入'}</button>
        </form>
        {error && <p style={{ color: 'var(--danger)', fontSize: 13, marginTop: 8 }}>{error}</p>}
      </div>
    );
  }

  const s = data?.stats || {};
  const users = data?.users || [];
  const today = new Date().toISOString().slice(0, 10);
  const todayVisits = s.daily_visits?.[today] || 0;

  return (
    <div className="page-container">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <h2 style={{ fontSize: 18 }}>📊 开发者后台</h2>
        <button className="btn btn-secondary" onClick={() => { setAuthed(false); setData(null); localStorage.removeItem('dp_admin_pw'); }}
          style={{ fontSize: 12, padding: '4px 12px' }}>退出</button>
      </div>

      {/* Stats cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 12, marginBottom: 24 }}>
        {[
          { label: '总访问量', value: s.total_visits || 0, icon: '👁' },
          { label: '今日访问', value: todayVisits, icon: '📅' },
          { label: '注册用户', value: data?.user_count || 0, icon: '👤' },
          { label: '启动时间', value: s.started_at?.slice(0, 10) || '-', icon: '🚀' },
        ].map(card => (
          <div key={card.label} className="card" style={{ cursor: 'default', textAlign: 'center', padding: '16px 12px' }}>
            <div style={{ fontSize: 24 }}>{card.icon}</div>
            <div style={{ fontSize: 22, fontWeight: 700, color: 'var(--ink)', margin: '4px 0' }}>{card.value}</div>
            <div style={{ fontSize: 12, color: 'var(--text-dim)' }}>{card.label}</div>
          </div>
        ))}
      </div>

      {/* Page views */}
      <h3 style={{ fontSize: 15, marginBottom: 8 }}>📄 页面访问排行</h3>
      <div className="card" style={{ cursor: 'default', marginBottom: 20 }}>
        {Object.entries(s.page_views || {}).sort((a, b) => b[1] - a[1]).slice(0, 20).map(([path, count]) => (
          <div key={path} style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid var(--border)', fontSize: 13 }}>
            <span style={{ color: 'var(--text)' }}>{path}</span>
            <span style={{ color: 'var(--accent)', fontWeight: 600 }}>{count}</span>
          </div>
        ))}
        {!Object.keys(s.page_views || {}).length && <p style={{ fontSize: 13, color: 'var(--text-dim)', padding: '8px 0' }}>暂无数据</p>}
      </div>

      {/* Users */}
      <h3 style={{ fontSize: 15, marginBottom: 8 }}>👥 注册用户 ({users.length})</h3>
      <div className="card" style={{ cursor: 'default' }}>
        {users.map(u => (
          <div key={u.id} style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid var(--border)', fontSize: 13 }}>
            <span style={{ color: 'var(--text)' }}>{u.username}</span>
            <span style={{ color: 'var(--text-dim)' }}>ID:{u.id} · {u.created_at?.slice(0, 10) || '-'}</span>
          </div>
        ))}
        {!users.length && <p style={{ fontSize: 13, color: 'var(--text-dim)', padding: '8px 0' }}>暂无注册用户</p>}
      </div>
    </div>
  );
}

export default DeveloperPage;
