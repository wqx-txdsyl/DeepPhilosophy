/**
 * 编辑个人信息 —— 用户名、头像、密码
 */
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getApiBase } from '../App';
import Icon from '../components/Icon';
import AvatarUpload from '../components/AvatarUpload';

function ProfileEditPage() {
  const navigate = useNavigate();
  const token = localStorage.getItem('dp_token');
  const [username, setUsername] = useState(localStorage.getItem('dp_username') || '');
  const [newUsername, setNewUsername] = useState(username);
  const [oldPw, setOldPw] = useState('');
  const [newPw, setNewPw] = useState('');
  const [confirmPw, setConfirmPw] = useState('');
  const [showPwSection, setShowPwSection] = useState(false);
  const [msg, setMsg] = useState('');
  const [msgType, setMsgType] = useState('');

  const showMsg = (text, type = 'info') => { setMsg(text); setMsgType(type); setTimeout(() => setMsg(''), 3000); };

  const handleSaveUsername = async () => {
    if (!newUsername.trim()) return showMsg('用户名不能为空', 'error');
    if (!token) return showMsg('请先登录', 'error');
    try {
      const r = await fetch(`${getApiBase()}/api/user/profile`, {
        method: 'PUT', headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({ username: newUsername.trim() }),
        signal: AbortSignal.timeout(8000),
      });
      if (r.ok) {
        localStorage.setItem('dp_username', newUsername.trim());
        setUsername(newUsername.trim());
        showMsg('✅ 用户名已更新', 'success');
      } else {
        const d = await r.json().catch(() => ({}));
        showMsg(d.detail || '更新失败', 'error');
      }
    } catch { showMsg('网络错误', 'error'); }
  };

  const handleChangePw = async () => {
    if (!oldPw) return showMsg('请输入原密码', 'error');
    if (!newPw || newPw.length < 4) return showMsg('新密码至少4位', 'error');
    if (newPw !== confirmPw) return showMsg('两次密码不一致', 'error');
    if (!token) return showMsg('请先登录', 'error');
    try {
      const r = await fetch(`${getApiBase()}/api/user/password`, {
        method: 'PUT', headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({ old_password: oldPw, new_password: newPw }),
        signal: AbortSignal.timeout(8000),
      });
      if (r.ok) {
        showMsg('✅ 密码已修改，请重新登录', 'success');
        setOldPw(''); setNewPw(''); setConfirmPw('');
        localStorage.removeItem('dp_token');
        setTimeout(() => navigate('/profile'), 1500);
      } else {
        const d = await r.json().catch(() => ({}));
        showMsg(d.detail || '原密码错误', 'error');
      }
    } catch { showMsg('网络错误', 'error'); }
  };

  return (
    <div className="page-container">
      <button className="btn btn-secondary" onClick={() => navigate(-1)} style={{ marginBottom: 16 }}>← 返回</button>
      <h2 className="section-title"><Icon name="btn-settings" size={18} /> 编辑个人信息</h2>

      {/* Avatar */}
      <div className="card" style={{ cursor: 'default', textAlign: 'center', padding: '20px' }}>
        <AvatarUpload size={80} />
        <p style={{ fontSize: 12, color: 'var(--text-dim)', marginTop: 8 }}>点击头像更换</p>
      </div>

      {/* Username */}
      <div className="card" style={{ cursor: 'default', padding: '16px 0' }}>
        <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 8, color: 'var(--text)' }}>用户名</div>
        <div style={{ display: 'flex', gap: 8 }}>
          <input value={newUsername} onChange={e => setNewUsername(e.target.value)}
            placeholder={username} style={{ flex: 1, padding: '8px 12px', borderRadius: 6, border: '1px solid var(--border)', background: 'var(--secondary)', color: 'var(--text)', fontSize: 14, outline: 'none' }} />
          <button className="btn btn-primary" onClick={handleSaveUsername} style={{ padding: '8px 16px', fontSize: 13, whiteSpace: 'nowrap' }}>保存</button>
        </div>
      </div>

      {/* Password section */}
      <div className="card" style={{ cursor: 'default', padding: '16px 0' }}>
        <div onClick={() => setShowPwSection(!showPwSection)}
          style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', cursor: 'pointer' }}>
          <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--text)' }}>🔒 修改密码</span>
          <span style={{ fontSize: 18, color: 'var(--text-dim)', transition: 'transform 0.2s', transform: showPwSection ? 'rotate(90deg)' : '' }}>›</span>
        </div>
        {showPwSection && (
          <div style={{ marginTop: 12, display: 'flex', flexDirection: 'column', gap: 8 }}>
            <input type="password" value={oldPw} onChange={e => setOldPw(e.target.value)}
              placeholder="原密码" style={{ padding: '8px 12px', borderRadius: 6, border: '1px solid var(--border)', background: 'var(--secondary)', color: 'var(--text)', fontSize: 14, outline: 'none' }} />
            <input type="password" value={newPw} onChange={e => setNewPw(e.target.value)}
              placeholder="新密码（至少4位）" style={{ padding: '8px 12px', borderRadius: 6, border: '1px solid var(--border)', background: 'var(--secondary)', color: 'var(--text)', fontSize: 14, outline: 'none' }} />
            <input type="password" value={confirmPw} onChange={e => setConfirmPw(e.target.value)}
              placeholder="确认新密码" style={{ padding: '8px 12px', borderRadius: 6, border: '1px solid var(--border)', background: 'var(--secondary)', color: 'var(--text)', fontSize: 14, outline: 'none' }} />
            <button className="btn btn-primary" onClick={handleChangePw} style={{ padding: '8px 16px', fontSize: 13 }}>修改密码</button>
          </div>
        )}
      </div>

      {/* Message */}
      {msg && (
        <div style={{ marginTop: 12, padding: '10px 16px', borderRadius: 8, fontSize: 13, textAlign: 'center',
          background: msgType === 'success' ? 'rgba(90,122,90,0.15)' : 'rgba(160,64,64,0.15)',
          color: msgType === 'success' ? 'var(--success)' : 'var(--danger)' }}>
          {msg}
        </div>
      )}
    </div>
  );
}

export default ProfileEditPage;
