import { useLang } from '../../utils/i18n';
import { resolvePortrait } from '../../utils/api';
import Icon from '../Icon';

/**
 * AgentPlaza — 智能体广场（§7: 从主导航降级为独立 Discovery 入口）
 * 点击"开始对话" → 创建临时 Conversation 并把所选 Agent 设为默认 Composer Agent
 * （不进入永久 /nietzsche 聊天孤岛）。由前端调用方处理会话创建, 本组件只负责展示与回调。
 */
export default function AgentPlaza({ open, onClose, agents, loading, onPick }) {
  const { t, agentName, agentSub } = useLang();
  if (!open) return null;
  const cards = (agents || []).filter(a => a.key !== 'general');
  const general = (agents || []).find(a => a.key === 'general');
  return (
    <>
      <div className="cw-plaza-scrim" onClick={onClose} />
      <div className="cw-plaza">
        <div style={{ borderBottom: '1px solid var(--border)', padding: '14px 18px',
                      display: 'flex', alignItems: 'center', gap: 10 }}>
          <span style={{ flex: 1, fontSize: 14.5, fontWeight: 700 }}>{t('plazaTitle')}</span>
          <span onClick={onClose} style={{ cursor: 'pointer', color: 'var(--text-dim)', fontSize: 15, padding: '2px 6px' }}>✕</span>
        </div>
        <div className="cw-plaza-body">
          <div style={{ fontSize: 12, color: 'var(--text-dim)', margin: '2px 0 12px' }}>{t('plazaSub')}</div>
          {loading && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '12px 4px',
                          fontSize: 12.5, color: 'var(--text-dim)' }}>
              <span style={{ width: 12, height: 12, borderRadius: '50%', border: '2px solid var(--border)',
                             borderTopColor: 'var(--accent)', animation: 'spin .8s linear infinite' }} />
              {t('loadingAgents')}…
            </div>
          )}
          {general && (
            <div className="cw-plaza-card">
              {renderAvatar(general)}
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: 13.5, fontWeight: 600 }}>{agentName('general') || general.name}</div>
                <div style={{ fontSize: 11.5, color: 'var(--text-dim)', marginTop: 2, lineHeight: 1.5 }}>
                  {agentSub('general') || general.subtitle}
                </div>
                {general.tagline && (
                  <div style={{ fontSize: 10.5, color: 'var(--text-dim)', marginTop: 6, lineHeight: 1.5 }}>
                    {general.tagline}
                  </div>
                )}
              </div>
              <button className="cw-btn" onClick={() => onPick('general')}
                style={{ padding: '6px 12px', borderRadius: 16, cursor: 'pointer', fontSize: 12.5,
                         border: '1px solid var(--border)', background: 'var(--accent)', color: 'var(--bg)', flexShrink: 0 }}>
                {t('startChat')}
              </button>
            </div>
          )}
          {cards.map((a) => (
            <div key={a.key} className="cw-plaza-card">
              {renderAvatar(a)}
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: 13.5, fontWeight: 600 }}>{agentName(a.key) || a.name}</div>
                <div style={{ fontSize: 11.5, color: 'var(--text-dim)', marginTop: 2, lineHeight: 1.5 }}>
                  {agentSub(a.key) || a.subtitle || '·'}
                </div>
                {a.tagline && (
                  <div style={{ fontSize: 10.5, color: 'var(--text-dim)', marginTop: 6, lineHeight: 1.5 }}>
                    {a.tagline}
                  </div>
                )}
              </div>
              <button className="cw-btn" onClick={() => onPick(a.key)}
                style={{ padding: '6px 12px', borderRadius: 16, cursor: 'pointer', fontSize: 12.5,
                         border: '1px solid var(--border)', background: 'var(--card-bg)', color: 'var(--text)', flexShrink: 0 }}>
                {t('startChat')}
              </button>
            </div>
          ))}
        </div>
      </div>
    </>
  );
}

function renderAvatar(a) {
  if (a.portrait) {
    return <img src={resolvePortrait(a.portrait)} alt="" style={{ width: 42, height: 42, borderRadius: '50%', objectFit: 'cover',
                   border: '1px solid var(--border)', flexShrink: 0 }} />;
  }
  return <span style={{ width: 42, height: 42, borderRadius: '50%', background: 'var(--soft)',
                        border: '1px solid var(--border)', display: 'inline-flex', alignItems: 'center',
                        justifyContent: 'center', flexShrink: 0 }}>
    <Icon name="icon-brain" size={20} />
  </span>;
}
