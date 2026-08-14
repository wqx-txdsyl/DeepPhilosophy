import { useEffect, useState } from 'react';
import { createPortal } from 'react-dom';
import { getApiBase } from '../utils/api';
import { useAuth } from '../auth';
import { useLang } from '../utils/i18n';
import AuthModal from './AuthModal';
import UserCenterModal from './UserCenterModal';

/**
 * AgentSidebar — {t('sidebarTitle')}（侧边栏）
 * 切换智能体: 通用深哲 / 哲学家智能体（尼采等, 后端注册表驱动）
 */
export default function AgentSidebar({ current, onSelect }) {
  const { username, logout } = useAuth();
  const { t, lang, agentName, agentSub } = useLang();
  const [showAuth, setShowAuth] = useState(false);
  const [showCenter, setShowCenter] = useState(false);
  const [agents, setAgents] = useState([{ key: 'general', name: '深哲', subtitle: '通用哲学智能体', portrait: null }]);

  // 拉取智能体列表: 带超时 + 自动重试（服务器启动期后端未就绪时自动等待）
  useEffect(() => {
    let cancelled = false;
    let retries = 0;
    const load = () => {
      const ctrl = new AbortController();
      const timer = setTimeout(() => ctrl.abort(), 5000);
      fetch(`${getApiBase()}/api/agents`, { signal: ctrl.signal })
        .then(r => r.json())
        .then(d => {
          clearTimeout(timer);
          if (!cancelled && d.agents?.length) setAgents(d.agents);
        })
        .catch(() => {
          clearTimeout(timer);
          if (!cancelled && retries < 10) {
            retries += 1;
            setTimeout(load, 2000);   // 2s 后重试（最多 10 次, 覆盖后端启动窗口）
          }
        });
    };
    load();
    return () => { cancelled = true; };
  }, []);

  return (
    <div style={{
      width: 216, flexShrink: 0, borderRight: '1px solid var(--border)',
      background: 'var(--bg)', display: 'flex', flexDirection: 'column', height: '100vh',
      position: 'sticky', top: 0, overflowY: 'auto',
    }}>
      <div style={{ padding: '18px 16px 10px', fontSize: 13, fontWeight: 700, letterSpacing: '1px', color: 'var(--text-dim)' }}>
        {t('sidebarTitle')}
      </div>
      {agents.map(a => {
        const active = a.key === current;
        const sub = agentSub(a.key) || a.subtitle || a.tagline || '';   // 双语优先, 后端 subtitle 兜底
        const hideTagline = lang === 'en' && agentSub(a.key);           // EN 下已显示双语副标题, 隐藏中文 tagline
        return (
          <div key={a.key} onClick={() => onSelect(a.key)}
            style={{
              margin: '4px 10px', padding: '10px 12px', borderRadius: 10, cursor: 'pointer',
              border: active ? '1px solid #d4d4d8' : '1px solid transparent',
              background: active ? 'var(--soft)' : 'transparent',
              transition: 'all .15s',
            }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              {a.portrait ? (
                <img src={a.portrait} alt={agentName(a.key) || a.name} style={{ width: 34, height: 34, borderRadius: '50%', objectFit: 'cover', border: '1px solid var(--border)' }} />
              ) : (
                <div style={{ width: 34, height: 34, borderRadius: '50%', background: 'var(--accent)',
                              display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 15, color: 'var(--card-bg)' }}>
                  {(a.name || a.key)[0]}
                </div>
              )}
              <div style={{ minWidth: 0 }}>
                <div style={{ fontSize: 14, fontWeight: 600 }}>{agentName(a.key) || a.name}</div>
                <div style={{ fontSize: 11, color: 'var(--text-dim)', marginTop: 1, lineHeight: 1.4, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {sub}
                </div>
              </div>
            </div>
            {a.tagline && a.key !== 'general' && !hideTagline && (
              <div style={{ fontSize: 10.5, color: 'var(--text-dim)', marginTop: 6, lineHeight: 1.4 }}>
                {a.tagline}
              </div>
            )}
          </div>
        );
      })}
      <div style={{ marginTop: 'auto', padding: '10px 12px', borderTop: '1px solid var(--border)' }}>
        {/* 用户区（侧边栏底部, 点击打开{t('userCenter')}） */}
        {username ? (
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '4px 2px' }}>
            <div onClick={() => setShowCenter(true)} title={t('userCenter')}
              style={{ display: 'flex', alignItems: 'center', gap: 8, flex: 1, cursor: 'pointer', minWidth: 0 }}>
              <div style={{ width: 26, height: 26, borderRadius: '50%', background: 'var(--accent)', color: 'var(--bg)',
                            display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 12, flexShrink: 0 }}>
                {username[0]}
              </div>
              <span style={{ fontSize: 13, color: 'var(--text)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {username}
              </span>
            </div>
            <button onClick={logout} title={t('logout')}
              style={{ fontSize: 11, color: 'var(--text-dim)', cursor: 'pointer', padding: '3px 8px',
                       borderRadius: 6, border: '1px solid var(--border)', background: 'var(--card-bg)' }}>
              {t('logout')}
            </button>
          </div>
        ) : (
          <button onClick={() => setShowAuth(true)}
            style={{ width: '100%', padding: '8px 0', borderRadius: 8, cursor: 'pointer', fontSize: 13,
                     border: 'none', background: 'var(--accent)', color: 'var(--bg)' }}>
            {t('login')}
          </button>
        )}
        <div style={{ padding: '10px 4px 2px', fontSize: 10.5, color: 'var(--text-dim)', lineHeight: 1.5 }}>
          {t('agentNote')}
        </div>
      </div>
      {/* Portal 渲染: 脱离 sticky 侧边栏的层叠上下文, 遮罩覆盖全屏 */}
      {showAuth && createPortal(<AuthModal onClose={() => setShowAuth(false)} />, document.body)}
      {showCenter && createPortal(<UserCenterModal onClose={() => setShowCenter(false)} />, document.body)}
    </div>
  );
}
