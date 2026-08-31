import { useState, useEffect, useRef } from 'react';
import { Check, ChevronsUpDown } from 'lucide-react';
import { useLang } from '../../utils/i18n';

/**
 * AgentSelector — 回答者选择器（spec §13）
 * 标签: 「回答者：尼采」；切换只影响下一次 invocation（§14）, 由父级实现快照。
 * 分组: 通用 / 作者 / 分隔「探索更多智能体」（§7 Plaza 从导航降级为发现）。
 * a11y: aria-haspopup / aria-expanded / aria-checked / Escape 关闭 / 点击外部关闭。
 */
export default function AgentSelector({ agents, value, onChange, onExplore, unavailable }) {
  const { t, agentName, agentSub } = useLang();
  const [open, setOpen] = useState(false);
  const rootRef = useRef(null);
  const current = (agents || []).find(a => a.key === value);

  useEffect(() => {
    if (!open) return;
    const onKey = (e) => { if (e.key === 'Escape') setOpen(false); };
    const onDown = (e) => { if (rootRef.current && !rootRef.current.contains(e.target)) setOpen(false); };
    window.addEventListener('keydown', onKey);
    document.addEventListener('mousedown', onDown);
    return () => { window.removeEventListener('keydown', onKey); document.removeEventListener('mousedown', onDown); };
  }, [open]);

  const general = (agents || []).find(a => a.key === 'general');
  const authors = (agents || []).filter(a => a.key !== 'general');

  const entry = (a) => (
    <button key={a.key} role="menuitemcheckbox" aria-checked={a.key === value}
      onClick={() => { setOpen(false); onChange(a.key); }}
      className="cw-selector-item">
      <span style={{ flex: 1, minWidth: 0 }}>
        <span className="cw-selector-name">
          {agentName(a.key) || a.name}
          {a.key === value && <Check size={12} style={{ color: 'var(--text-dim)' }} aria-hidden />}
        </span>
        <span className="cw-selector-desc">{agentSub(a.key) || a.subtitle || a.tagline || ''}</span>
      </span>
    </button>
  );

  return (
    <div ref={rootRef} style={{ position: 'relative', flexShrink: 0, minWidth: 0 }}>
      <button className={`cw-responder${unavailable ? ' cw-responder-disabled' : ''}`}
        onClick={() => setOpen(o => !o)}
        aria-haspopup="menu" aria-expanded={open} aria-label={t('agentSelector')}
        title={unavailable ? t('agentUnavailable') : `${t('responder')}：${agentName(value) || current?.name || value}`}>
        <span className="cw-responder-label" style={{ flexShrink: 0 }}>{t('responder')}</span>
        <span className="cw-responder-name">{unavailable ? `${agentName(value) || current?.name || value}` : (agentName(value) || current?.name || value)}</span>
        <ChevronsUpDown size={11} aria-hidden />
      </button>
      {open && (
        <div className="cw-selector-menu" role="menu" aria-label={t('agentSelector')}>
          {general && (
            <>
              <div className="cw-selector-group">{t('secGeneral')}</div>
              {entry(general)}
            </>
          )}
          {authors.length > 0 && (
            <>
              <div className="cw-selector-group">{t('secAuthors')}</div>
              {authors.map(entry)}
            </>
          )}
          <button className="cw-selector-foot" onClick={() => { setOpen(false); onExplore(); }}>
            {t('exploreMore')} →
          </button>
        </div>
      )}
    </div>
  );
}
