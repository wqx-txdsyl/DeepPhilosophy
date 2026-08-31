import { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { X } from 'lucide-react';
import { useLang, LANGS, AGENT_NAMES } from '../../utils/i18n';
import { getTheme, setTheme, applyTheme } from '../../utils/theme';
import { getPref, setPref } from '../../data/localPrefs';
import { useAuth } from '../../auth';
import AuthModal from '../AuthModal';
import { ConfirmModal } from './Modal';

/**
 * SettingsPanel — 设置（spec §24/§25 Codex 式面板; 内容只含 PhiAgent 真实能力）
 *
 * IA: 通用（外观/语言/通知）｜回答者（默认回答者）｜阅读（阅读上下文状态）｜
 *     证据（引用显示/工具披露）｜会话与数据（本机历史清理）｜账户（登录/用户中心）
 *
 * 禁止伪造 Codex 的 SSH / sandbox / GitHub 集成等假设置（§25）。
 * 打开/关闭不 unmount Conversation/Composer → draft / 会话 / responder 不丢（§24, UAT-11）。
 */
const SECTIONS = [
  ['settingsGeneral', 'toolbar'],
  ['settingsAgent', 'bot'],
  ['settingsReading', 'bookOpen'],
  ['settingsEvidence', 'shieldCheck'],
  ['settingsData', 'database'],
  ['settingsAccount', 'userRound'],
];

export default function SettingsPanel({ open, onClose, conversation }) {
  const { t, lang, setLang } = useLang();
  const { username, authFetch, logout } = useAuth();
  const [section, setSection] = useState('settingsGeneral');
  const [theme, setThemeState] = useState(getTheme());
  const [showCitations, setShowCitations] = useState(() => getPref('showCitations') !== false);
  const [toolOpen, setToolOpen] = useState(() => getPref('toolTraceOpen') === true);
  const [defaultResponder, setDefaultResponder] = useState(() => getPref('defaultResponder') || 'general');
  const [notifEnabled, setNotifEnabled] = useState(() => Notification?.permission === 'granted');
  const [confirmClear, setConfirmClear] = useState(false);
  const [showAuth, setShowAuth] = useState(false);
  const [notice, setNotice] = useState('');

  // Escape 关闭（§32）; 打开/关闭不丢 draft（由 Composer 保持 mounted 保证, §24）
  useEffect(() => {
    if (!open) return;
    const onKey = (e) => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [open, onClose]);

  if (!open) return null;

  const flash = (msg) => { setNotice(msg); setTimeout(() => setNotice(''), 2600); };

  const applyThemePref = (v) => { setTheme(v); applyTheme(v); setThemeState(v); setPref('theme', v); };
  const toggleCitations = () => { const v = !showCitations; setShowCitations(v); setPref('showCitations', v); };
  const toggleToolOpen = () => { const v = !toolOpen; setToolOpen(v); setPref('toolTraceOpen', v); };
  const pickResponder = (k) => { setDefaultResponder(k); setPref('defaultResponder', k); };

  const requestNotif = async () => {
    if (!('Notification' in window)) { flash(t('notifUnsupported')); return; }
    const perm = await Notification.requestPermission();
    setNotifEnabled(perm === 'granted');
    flash(perm === 'granted' ? t('notifEnabled') : t('notifDenied'));
  };

  const clearLocal = () => {
    try {
      localStorage.removeItem('phiagent_conversations_v1');
      localStorage.removeItem('dp_chat_sessions');
      localStorage.removeItem('dp_current_session');
      Object.keys(localStorage).filter(k => k.startsWith('dp_agent_msgs_v2_')).forEach(k => localStorage.removeItem(k));
    } catch (e) { /* 忽略 */ }
    if (username) { authFetch('/api/history/chat', { method: 'DELETE' }).catch(() => {}); }
    window.location.reload();
  };

  const rc = conversation?.reading_context;
  const hasRc = !!(rc?.book_id || rc?.chapter_id || rc?.selected_text);

  return createPortal(
    <>
      <div className="cw-settings-scrim" onClick={onClose} />
      <div className="cw-settings" role="dialog" aria-modal="true" aria-label={t('settings')}>
        <div className="cw-settings-nav">
          <div className="cw-settings-nav-title">{t('settings')}</div>
          {SECTIONS.map(([key]) => (
            <button key={key} className={`cw-settings-nav-btn${section === key ? ' cw-settings-active' : ''}`}
              onClick={() => setSection(key)}>
              {t(key)}
            </button>
          ))}
          <button onClick={onClose} className="cw-settings-nav-btn" style={{ marginTop: 'auto', color: 'var(--text-dim)' }}>
            {t('back')}
          </button>
        </div>
        <div className="cw-settings-body">
          <button onClick={onClose} className="cw-icon-btn" style={{ position: 'absolute' }} aria-label={t('back')}>
            <X size={15} />
          </button>
          {notice && <div className="cw-settings-notice" style={{ fontSize: 12, color: 'var(--text-dim)', marginBottom: 8 }}>{notice}</div>}

          {section === 'settingsGeneral' && (
            <>
              <div className="cw-settings-sec">
                <h3 className="cw-settings-h">{t('theme')}</h3>
                <div style={{ display: 'flex', gap: 8, margin: '10px 0 4px' }}>
                  {[['light', t('themeLight')], ['dark', t('themeDark')], ['auto', t('themeAuto')]].map(([v, label]) => (
                    <button key={v} onClick={() => applyThemePref(v)}
                      style={{ padding: '7px 16px', borderRadius: 8, cursor: 'pointer', fontSize: 13,
                               border: theme === v ? '1px solid var(--accent)' : '1px solid var(--border)',
                               background: theme === v ? 'var(--soft)' : 'var(--bg)',
                               color: theme === v ? 'var(--text)' : 'var(--text-dim)' }}>
                      {label}
                    </button>
                  ))}
                </div>
              </div>
              <div className="cw-settings-sec">
                <h3 className="cw-settings-h">{t('language')}</h3>
                <p className="cw-settings-desc">{t('answerLang')}</p>
                <div style={{ display: 'flex', gap: 8 }}>
                  {LANGS.map(([v, label]) => (
                    <button key={v} onClick={() => setLang(v)}
                      style={{ padding: '7px 16px', borderRadius: 8, cursor: 'pointer', fontSize: 13,
                               border: lang === v ? '1px solid var(--accent)' : '1px solid var(--border)',
                               background: lang === v ? 'var(--soft)' : 'var(--bg)',
                               color: lang === v ? 'var(--text)' : 'var(--text-dim)' }}>
                      {label}
                    </button>
                  ))}
                </div>
              </div>
              <div className="cw-settings-sec">
                <div className="cw-toggle-row">
                  <div>
                    <div className="cw-settings-label">{t('notification')}</div>
                    <div className="cw-settings-sub">{t('notifDesc')}</div>
                  </div>
                  <button className="cw-toggle" role="switch" aria-checked={notifEnabled} onClick={requestNotif}>
                    <span className="cw-toggle-knob" />
                  </button>
                </div>
              </div>
            </>
          )}

          {section === 'settingsAgent' && (
            <div className="cw-settings-sec">
              <h3 className="cw-settings-h">{t('defaultResponder')}</h3>
              <p className="cw-settings-desc">{t('defaultResponderDesc')}</p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginTop: 10 }}>
                {['general', 'nietzsche'].map((k) => (
                  <button key={k} onClick={() => pickResponder(k)}
                    style={{ textAlign: 'left', padding: '10px 14px', borderRadius: 10, cursor: 'pointer', fontSize: 13,
                             border: defaultResponder === k ? '1px solid var(--accent)' : '1px solid var(--border)',
                             background: defaultResponder === k ? 'var(--soft)' : 'var(--bg)' }}>
                    <span style={{ fontWeight: 600 }}>{(AGENT_NAMES[k] || {})[lang] || k}</span>
                    <span style={{ display: 'block', fontSize: 11.5, color: 'var(--text-dim)', marginTop: 2 }}>
                      {lang === 'zh'
                        ? (k === 'general' ? '通用哲学智能体 · 全工具' : '查拉图斯特拉的作者 · 以尼采人格与你交谈')
                        : (k === 'general' ? 'General philosophy agent' : 'Author of Zarathustra · speak as Nietzsche')}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {section === 'settingsReading' && (
            <div className="cw-settings-sec">
              <h3 className="cw-settings-h">{t('readingContext')}</h3>
              <p className="cw-settings-desc">{t('readingContextDesc')}</p>
              {hasRc ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginTop: 10,
                              padding: 12, borderRadius: 10, border: '1px solid var(--border)', background: 'var(--soft)', fontSize: 12.5 }}>
                  {rc.book_id && <div>{t('readingContextBook')}：《{rc.book_id}》</div>}
                  {rc.chapter_id && <div>{t('readingContextChapter')}：{rc.chapter_id}</div>}
                  {rc.selected_text && <div>{t('readingContextSel')}：{String(rc.selected_text).slice(0, 80)}…</div>}
                </div>
              ) : (
                <div style={{ marginTop: 10, padding: '10px 12px', borderRadius: 10, border: '1px dashed var(--border)',
                              fontSize: 12.5, color: 'var(--text-dim)' }}>
                  {t('readingContextNone')}
                </div>
              )}
            </div>
          )}

          {section === 'settingsEvidence' && (
            <>
              <div className="cw-toggle-row">
                <div>
                  <div className="cw-settings-label">{t('citationShow')}</div>
                  <div className="cw-settings-sub">{t('citationShowDesc')}</div>
                </div>
                <button className="cw-toggle" role="switch" aria-checked={showCitations} onClick={toggleCitations} aria-label={t('citationShow')}>
                  <span className="cw-toggle-knob" />
                </button>
              </div>
              <div className="cw-toggle-row">
                <div>
                  <div className="cw-settings-label">{t('toolTraceExpand')}</div>
                  <div className="cw-settings-sub">{t('toolTraceExpandDesc')}</div>
                </div>
                <button className="cw-toggle" role="switch" aria-checked={toolOpen} onClick={toggleToolOpen} aria-label={t('toolTraceExpand')}>
                  <span className="cw-toggle-knob" />
                </button>
              </div>
            </>
          )}

          {section === 'settingsData' && (
            <div className="cw-settings-sec">
              <h3 className="cw-settings-h">{t('dataMgmt')}</h3>
              <div className="cw-toggle-row" style={{ alignItems: 'flex-start' }}>
                <div>
                  <div className="cw-settings-label">{t('clearLocalHistory')}</div>
                  <div className="cw-settings-sub">{t('clearLocalHistoryDesc')}</div>
                </div>
                <button className="cw-danger-btn" onClick={() => setConfirmClear(true)}>{t('clearHistory')}</button>
              </div>
            </div>
          )}

          {section === 'settingsAccount' && (
            <div className="cw-settings-sec">
              <h3 className="cw-settings-h">{t('account')}</h3>
              {username ? (
                <>
                  <div className="cw-toggle-row">
                    <div>
                      <div className="cw-settings-label">{t('username')}</div>
                      <div className="cw-settings-sub">{t('sessionDesc')}</div>
                    </div>
                    <b>{username}</b>
                  </div>
                  <div style={{ marginTop: 14, display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                    <button className="cw-danger-btn" onClick={logout}>{t('logout')}</button>
                  </div>
                </>
              ) : (
                <p className="cw-settings-desc">{t('login')}</p>
              )}
              <button style={{ marginTop: 8, padding: '8px 14px', borderRadius: 8, cursor: 'pointer', fontSize: 13,
                               border: '1px solid var(--border)', background: 'var(--card-bg)', color: 'var(--text)' }}
                onClick={() => { if (username) onClose(); else setShowAuth(true); }}>
                {username ? t('userCenter') : t('login')}
              </button>
            </div>
          )}
        </div>
      </div>
      {confirmClear && (
        <ConfirmModal title={t('clearHistory')} message={t('clearConfirm')}
          onClose={() => setConfirmClear(false)} onConfirm={clearLocal} />
      )}
      {showAuth && <AuthModal onClose={() => setShowAuth(false)} />}
    </>,
    document.body,
  );
}
