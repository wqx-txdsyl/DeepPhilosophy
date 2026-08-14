import { useEffect, useState } from 'react';
import { useAuth } from '../auth';
import { getTheme, setTheme } from '../utils/theme';
import { useLang, LANGS } from '../utils/i18n';

/**
 * UserCenterModal — Manus 式用户中心（点左下角用户打开）
 * 四区: 通用（{t('theme')}/语言/通知）/ {t('account')}（信息/改密/删除）/ 个性化（{t('nickname')}/{t('occupation')}/关于我/{t('customInstr')}）/ 数据（清除历史）
 */
export default function UserCenterModal({ onClose }) {
  const { username, authFetch, logout } = useAuth();
  const { lang, setLang, t } = useLang();
  const [section, setSection] = useState('secGeneral');   // 与 SECTIONS 的 key 一致, 否则内容区空白
  const [theme, setThemeState] = useState(getTheme());
  const [profile, setProfile] = useState({});
  const [notice, setNotice] = useState('');
  const [notifEnabled, setNotifEnabled] = useState(false);

  // 加载资料
  useEffect(() => {
    authFetch('/api/auth/profile').then(d => {
      if (d.profile) setProfile(d.profile);
    }).catch(() => {});
    setNotifEnabled(Notification?.permission === 'granted');
  }, []);   // eslint-disable-line

  const flash = (msg) => { setNotice(msg); setTimeout(() => setNotice(''), 2500); };

  const saveProfile = async () => {
    const d = await authFetch('/api/auth/profile', {
      method: 'PUT',
      body: JSON.stringify({
        nickname: profile.nickname || null,
        occupation: profile.occupation || null,
        about: profile.about || null,
        custom_instructions: profile.custom_instructions || null,
        language: profile.language || null,
      }),
    });
    if (d.success) flash(t('saved'));
    else flash(d.detail || t('saveFail'));
  };

  const changePassword = async () => {
    const oldP = prompt(t('oldPwdPrompt'));
    if (!oldP) return;
    const newP = prompt(t('newPwdPrompt'));
    if (!newP || newP.length < 8) { flash(t('pwdShort')); return; }
    const d = await authFetch('/api/auth/change-password', {
      method: 'POST', body: JSON.stringify({ old_password: oldP, new_password: newP }),
    });
    flash(d.success ? t('pwdUpdated') : (d.detail || t('pwdFail')));
  };

  const clearHistory = async () => {
    if (!confirm(t('clearConfirm'))) return;
    const d = await authFetch('/api/history/chat', { method: 'DELETE' });
    flash(d.success ? t('historyCleared') : (d.detail || t('saveFail')));
    window.location.reload();
  };

  const deleteAccount = async () => {
    if (!confirm(t('deleteConfirm'))) return;
    const d = await authFetch('/api/auth/account', { method: 'DELETE' });
    if (d.success) { logout(); window.location.reload(); }
    else flash(d.detail || t('deleteFail'));
  };

  const requestNotif = async () => {
    if (!('Notification' in window)) { flash(t('notifUnsupported')); return; }
    const perm = await Notification.requestPermission();
    setNotifEnabled(perm === 'granted');
    flash(perm === 'granted' ? t('notifEnabled') : t('notifDenied'));
  };

  const SECTIONS = ['secGeneral', 'secAccount', 'secPersonal', 'secData'];
  const inputStyle = { width: '100%', padding: '8px 10px', borderRadius: 8, border: '1px solid var(--border)',
                       fontSize: 13, outline: 'none', marginBottom: 10, boxSizing: 'border-box', background: 'var(--card-bg)', color: 'var(--text)' };
  const btnStyle = { padding: '6px 14px', borderRadius: 8, border: '1px solid var(--border)', cursor: 'pointer',
                     fontSize: 13, background: 'var(--accent)', color: 'var(--bg)' };

  return (
    <div onClick={onClose} style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,.35)', zIndex: 1300,
                                   display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 24 }}>
      <div onClick={e => e.stopPropagation()}
        style={{ background: 'var(--bg)', borderRadius: 16, width: '100%', maxWidth: 940, height: '84vh',
                 display: 'flex', overflow: 'hidden', boxShadow: '0 24px 80px rgba(0,0,0,.28)' }}>
        {/* 左导航 */}
        <div style={{ width: 190, flexShrink: 0, borderRight: '1px solid var(--border)', padding: '24px 14px',
                      display: 'flex', flexDirection: 'column', gap: 3 }}>
          <div style={{ padding: '0 12px 16px', fontSize: 15, fontWeight: 700 }}>{t('settings')}</div>
          {SECTIONS.map(s => (
            <button key={t(s)} onClick={() => setSection(s)}
              style={{ textAlign: 'left', padding: '11px 14px', borderRadius: 9, cursor: 'pointer', fontSize: 13.5,
                       border: 'none', background: section === s ? 'var(--soft)' : 'transparent',
                       color: section === s ? 'var(--text)' : 'var(--text-dim)', fontWeight: section === s ? 600 : 400 }}>
              {t(s)}
            </button>
          ))}
          <div style={{ marginTop: 'auto' }}>
            <button onClick={onClose} style={{ width: '100%', padding: '10px 0', borderRadius: 9, cursor: 'pointer',
                                               fontSize: 13, border: 'none', color: 'var(--text-dim)', background: 'transparent' }}>
              {t('back')}
            </button>
          </div>
        </div>
        {/* 内容区 */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '28px 40px' }}>
          {notice && <div style={{ marginBottom: 10, padding: '7px 12px', borderRadius: 8, fontSize: 12,
                                  background: '#f0f7f0', border: '1px solid #cde5cd', color: '#2c662d' }}>{notice}</div>}

          {section === 'secGeneral' && (
            <>
              <h3 style={{ fontSize: 15, margin: '0 0 6px' }}>{t('appearance')}</h3>
              <div style={{ fontSize: 12.5, color: 'var(--text-dim)', marginBottom: 10 }}>{t('theme')}</div>
              <div style={{ display: 'flex', gap: 8, marginBottom: 22 }}>
                {[['light', t('themeLight')], ['dark', t('themeDark')], ['auto', t('themeAuto')]].map(([v, label]) => (
                  <button key={v} onClick={() => { setTheme(v); setThemeState(v); }}
                    style={{ padding: '7px 18px', borderRadius: 8, cursor: 'pointer', fontSize: 13,
                             border: theme === v ? '1px solid var(--accent)' : '1px solid var(--border)',
                             background: theme === v ? 'var(--soft)' : 'var(--bg)',
                             color: theme === v ? 'var(--text)' : 'var(--text-dim)' }}>
                    {label}
                  </button>
                ))}
              </div>
              <h3 style={{ fontSize: 15, margin: '0 0 6px' }}>{t('language')}</h3>
              <div style={{ fontSize: 12.5, color: 'var(--text-dim)', marginBottom: 10 }}>{t('answerLang')}</div>
              <div style={{ display: 'flex', gap: 8, marginBottom: 22 }}>
                {LANGS.map(([v, label]) => (
                  <button key={v} onClick={() => { setLang(v); setProfile({ ...profile, language: v }); }}
                    style={{ padding: '7px 18px', borderRadius: 8, cursor: 'pointer', fontSize: 13,
                             border: lang === v ? '1px solid var(--accent)' : '1px solid var(--border)',
                             background: lang === v ? 'var(--soft)' : 'var(--bg)',
                             color: lang === v ? 'var(--text)' : 'var(--text-dim)' }}>
                    {label}
                  </button>
                ))}
              </div>
              <h3 style={{ fontSize: 15, margin: '0 0 6px' }}>{t('notification')}</h3>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                <div>
                  <div style={{ fontSize: 13 }}>{t('notification')}</div>
                  <div style={{ fontSize: 11.5, color: 'var(--text-dim)' }}>{t('notifDesc')}</div>
                </div>
                <button onClick={requestNotif}
                  style={{ width: 44, height: 24, borderRadius: 12, border: 'none', cursor: 'pointer',
                           background: notifEnabled ? 'var(--accent)' : 'var(--border)', position: 'relative' }}>
                  <span style={{ position: 'absolute', top: 3, left: notifEnabled ? 24 : 3, width: 18, height: 18,
                                 borderRadius: '50%', background: 'var(--card-bg)', transition: 'left .15s' }} />
                </button>
              </div>
            </>
          )}

          {section === 'secAccount' && (
            <>
              <h3 style={{ fontSize: 15, margin: '0 0 14px' }}>{t('account')}</h3>
              <Row label={t('username')}><b>{username}</b></Row>
              <Row label={t('session')}>{t('sessionDesc')}</Row>
              <div style={{ marginTop: 18, display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                <button onClick={changePassword} style={btnStyle}>{t('updatePassword')}</button>
                <button onClick={deleteAccount}
                  style={{ padding: '6px 14px', borderRadius: 8, cursor: 'pointer', fontSize: 13,
                           border: '1px solid #d8a0a0', background: 'var(--card-bg)', color: '#c0392b' }}>
                  {t('deleteAccount')}
                </button>
              </div>
            </>
          )}

          {section === 'secPersonal' && (
            <>
              <h3 style={{ fontSize: 15, margin: '0 0 14px' }}>{t('personal')}</h3>
              <div style={{ fontSize: 12.5, color: 'var(--text-dim)', marginBottom: 4 }}>{t('nickname')}</div>
              <input value={profile.nickname || ''} onChange={e => setProfile({ ...profile, nickname: e.target.value })}
                placeholder={t('nicknamePh')} style={inputStyle} />
              <div style={{ fontSize: 12.5, color: 'var(--text-dim)', marginBottom: 4 }}>{t('occupation')}</div>
              <input value={profile.occupation || ''} onChange={e => setProfile({ ...profile, occupation: e.target.value })}
                placeholder={t('occupationPh')} style={inputStyle} />
              <div style={{ fontSize: 12.5, color: 'var(--text-dim)', marginBottom: 4 }}>{t('about')}</div>
              <textarea value={profile.about || ''} onChange={e => setProfile({ ...profile, about: e.target.value })}
                placeholder={t('aboutPh')} rows={3} style={inputStyle} />
              <div style={{ fontSize: 12.5, color: 'var(--text-dim)', marginBottom: 4 }}>{t('customInstr')}</div>
              <textarea value={profile.custom_instructions || ''} onChange={e => setProfile({ ...profile, custom_instructions: e.target.value })}
                placeholder={t('customInstrPh')} rows={3} style={inputStyle} />
              <button onClick={saveProfile} style={btnStyle}>{t('save')}</button>
            </>
          )}

          {section === 'secData' && (
            <>
              <h3 style={{ fontSize: 15, margin: '0 0 14px' }}>{t('dataMgmt')}</h3>
              <div style={{ marginBottom: 8 }}>
                <div style={{ fontSize: 13 }}>{t('chatHistory')}</div>
                <div style={{ fontSize: 11.5, color: 'var(--text-dim)', marginBottom: 6 }}>{t('chatHistoryDesc')}</div>
                <button onClick={clearHistory}
                  style={{ padding: '6px 14px', borderRadius: 8, cursor: 'pointer', fontSize: 13,
                           border: '1px solid #d8a0a0', background: 'var(--card-bg)', color: '#c0392b' }}>
                  {t('clearHistory')}
                </button>
              </div>
              <div style={{ marginTop: 16 }}>
                <div style={{ fontSize: 13 }}>{t('attachDataTitle')}</div>
                <div style={{ fontSize: 11.5, color: 'var(--text-dim)' }}>{t('attachDataDesc')}</div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

function Row({ label, children }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', padding: '9px 0', borderBottom: '1px solid var(--border)',
                  fontSize: 13 }}>
      <span style={{ color: 'var(--text-dim)' }}>{label}</span>
      <span>{children}</span>
    </div>
  );
}
