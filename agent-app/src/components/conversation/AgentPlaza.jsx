import { useState } from 'react';
import { useLang } from '../../utils/i18n';
import { resolvePortrait } from '../../utils/api';
import Icon from '../Icon';

/**
 * AgentPlaza — 智能体广场（§7: 从主导航降级为独立 Discovery 入口）
 * 点击"开始对话" → 创建临时 Conversation 并把所选 Agent 设为默认 Composer Agent
 * （不进入永久 /nietzsche 聊天孤岛）。由前端调用方处理会话创建, 本组件只负责展示与回调。
 */
export default function AgentPlaza({ open, onClose, agents, loading, onPick }) {
  const { t, lang, agentName, agentSub } = useLang();
  const [query, setQuery] = useState('');
  const [tradition, setTradition] = useState('');
  if (!open) return null;
  const philosophers = (agents || []).filter(a => a.key !== 'general');
  const groupOf = a => (a.tradition || (a.key === 'nietzsche' ? '欧洲·十九世纪' : '')).split('·')[0];
  const traditions = [...new Set(philosophers.map(groupOf).filter(Boolean))];
  const cards = philosophers.filter(a => (!tradition || groupOf(a) === tradition)
    && `${a.name} ${a.name_en || ''} ${a.tradition || ''} ${a.tagline || ''} ${(a.works || []).join(' ')}`.toLowerCase().includes(query.trim().toLowerCase()));
  const general = (agents || []).find(a => a.key === 'general');
  return (
    <>
      <div className="cw-plaza-scrim" onClick={onClose} />
      <div className="cw-plaza" role="dialog" aria-modal="true" aria-label={t('plazaTitle')}>
        <div style={{ borderBottom: '1px solid var(--border)', padding: '14px 18px',
                      display: 'flex', alignItems: 'center', gap: 10 }}>
          <span style={{ flex: 1, fontSize: 14.5, fontWeight: 700 }}>{t('plazaTitle')}</span>
          <span className="cw-agent-count">{agents?.length || 0} {lang === 'en' ? 'agents' : '个智能体'}</span>
          <button type="button" className="cw-icon-btn" onClick={onClose} aria-label={lang === 'en' ? 'Close' : '关闭'}>✕</button>
        </div>
        <div className="cw-plaza-body">
          <div style={{ fontSize: 12, color: 'var(--text-dim)', margin: '2px 0 12px' }}>
            {lang === 'en' ? 'Explore ideas with philosophers across traditions. Preview agents consult original texts.' : '与古今中外的哲学家讨论。测试版以原典为依据，保留各自的立场与思考方式。'}
          </div>
          <input className="cw-agent-search" aria-label={t('searchAgents')} placeholder={t('searchAgents')}
            value={query} onChange={e => setQuery(e.target.value)} />
          <select className="cw-agent-search" aria-label={lang === 'en' ? 'Filter traditions' : '筛选思想传统'} value={tradition} onChange={e => setTradition(e.target.value)}>
            <option value="">{lang === 'en' ? 'All traditions' : '全部思想传统'}</option>
            {traditions.map(value => <option key={value} value={value}>{value}</option>)}
          </select>
          <div className="cw-agent-count">{cards.length} / {philosophers.length} {lang === 'en' ? 'philosophers' : '位哲学家'}</div>
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
                <div style={{ fontSize: 13.5, fontWeight: 600 }}>{agentName(a.key, a) || a.name}
                  {a.status === 'preview' && <span className="cw-preview-badge">{t('preview')}</span>}
                </div>
                {a.status !== 'preview' && <div style={{ fontSize: 11.5, color: 'var(--text-dim)', marginTop: 2, lineHeight: 1.5 }}>
                  {agentSub(a.key) || a.subtitle || '·'}
                </div>}
                {a.status === 'preview' && <div className="cw-agent-count">
                  {a.tradition} · {a.local_primary_book_count > 0
                    ? (lang === 'en' ? `${a.local_primary_book_count} local texts` : `${a.local_primary_book_count} 本本地可读原典`)
                    : (lang === 'en' ? 'Find original texts online' : '需在线查找原典')}
                </div>}
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
          {!loading && !cards.length && <p className="cw-agent-count">{lang === 'en' ? 'No matching philosopher. Try another name, work or tradition.' : '没有匹配的哲学家，试试其他名字、著作或思想传统。'}</p>}
        </div>
      </div>
    </>
  );
}

function renderAvatar(a) {
  if (a.portrait) {
    return <img src={resolvePortrait(a.portrait)} alt="" loading="lazy" onError={e => { e.currentTarget.style.visibility = 'hidden'; }} style={{ width: 42, height: 42, borderRadius: '50%', objectFit: 'cover',
                   border: '1px solid var(--border)', flexShrink: 0 }} />;
  }
  return <span style={{ width: 42, height: 42, borderRadius: '50%', background: 'var(--soft)',
                        border: '1px solid var(--border)', display: 'inline-flex', alignItems: 'center',
                        justifyContent: 'center', flexShrink: 0 }}>
    <Icon name="icon-brain" size={20} />
  </span>;
}
