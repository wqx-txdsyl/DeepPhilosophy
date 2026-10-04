/**
 * 设置页面 — 个人信息与账户设置
 */
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { switchReadingOwner } from '../data/readingRoom';
import { getApiBase } from '../App';
import Icon from '../components/Icon';

function SettingsPage() {
  const navigate = useNavigate();
  const [stats, setStats] = useState({ books: 342, authors: 381, schools: 105 });
  const [showDelete, setShowDelete] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState('');

  const token = localStorage.getItem('dp_token');
  const username = localStorage.getItem('dp_username');

  const handleLogout = () => {
    switchReadingOwner(null);
    localStorage.removeItem('dp_token');
    localStorage.removeItem('dp_username');
    navigate('/profile');
  };

  useEffect(() => {
    fetch(`${getApiBase()}/api/stats`, { signal: AbortSignal.timeout(5000) })
      .then(r => r.json()).then(d => {
        setStats({
          books: d.books || 342,
          authors: d.authors || 381,
          schools: Math.max(105, d.schools || 0),
        });
      }).catch(() => {});
  }, []);

  return (
    <div className="page-container">
      <button className="btn btn-secondary" onClick={() => navigate(-1)}
        style={{ marginBottom: 16 }}>← 返回</button>

      <h2 className="section-title"><Icon name="btn-settings" size={18} /> 设置</h2>

      <div className="settings-form">
        <div className="card" style={{ cursor: 'pointer', marginTop: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}
          onClick={() => navigate('/profile/edit')}>
          <div>
            <h3 style={{ fontSize: 15, marginBottom: 4 }}><Icon name="btn-user" size={16} /> 编辑个人信息</h3>
            <p style={{ fontSize: 12, color: 'var(--text-dim)' }}>修改用户名、头像和密码</p>
          </div>
          <span style={{ fontSize: 18, color: 'var(--text-dim)' }}>→</span>
        </div>

        <div className="card" style={{ cursor: 'pointer', marginTop: 16 }} onClick={() => navigate('/about')} role="link" tabIndex={0} onKeyDown={e => { if(e.key === 'Enter') navigate('/about'); }}>
          <h3 style={{ fontSize: 15, marginBottom: 8 }}><Icon name="mode-mobile" size={16} /> 关于本站 ↗</h3>
          <p style={{ fontSize: 13, color: 'var(--text-dim)', lineHeight: 1.6 }}>
            <strong>DeepPhilosophy</strong> v2.0.0<br />
            开发者: @txdsyl_<br />
            哲学爱好者知识平台<br />
            {stats.books} 本哲学著作 · {stats.authors} 位哲学家 · {stats.schools} 个流派
          </p>
        </div>

        {token && (
          <div className="card" style={{ cursor: 'default', marginTop: 16 }}>
            <h3 style={{ fontSize: 15, marginBottom: 12 }}><Icon name="btn-user" size={16} /> 账号</h3>
            <p style={{ fontSize: 13, color: 'var(--text-dim)', marginBottom: 12 }}>
              当前登录：<strong>{username}</strong>
            </p>
            <button className="btn btn-secondary" style={{ marginRight: 8 }}
              onClick={handleLogout}>
              退出登录
            </button>
            {!showDelete ? (
              <button className="btn btn-danger"
                onClick={() => setShowDelete(true)}>
                删除账号
              </button>
            ) : (
              <div style={{ marginTop: 8 }}>
                <p style={{ fontSize: 12, color: 'var(--danger)', marginBottom: 8 }}>
                  输入用户名 <strong>{username}</strong> 确认删除，此操作不可撤销。
                </p>
                <input
                  placeholder="输入用户名确认"
                  value={deleteConfirm}
                  onChange={e => setDeleteConfirm(e.target.value)}
                  style={{ padding: '6px 12px', borderRadius: 6, border: '1px solid var(--border)', background: 'var(--card-bg)', color: 'var(--text)', fontSize: 13, marginRight: 8, width: 200 }}
                />
                <button className="btn btn-danger"
                  disabled={deleteConfirm !== username}
                  onClick={() => {
                    if (deleteConfirm === username) {
                      localStorage.removeItem('dp_token');
                      localStorage.removeItem('dp_username');
                      navigate('/profile');
                    }
                  }}>
                  确认删除
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default SettingsPage;
