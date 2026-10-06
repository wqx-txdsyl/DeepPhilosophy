import { useState, useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';
import { X, Palette, MessageCircle, SlidersHorizontal, Brain, UserRound, Database, Check, Loader2, LogOut } from 'lucide-react';
import { useLang, AGENT_NAMES } from '../../utils/i18n';
import { getTheme, setTheme } from '../../utils/theme';
import { getPref, setPref } from '../../data/localPrefs';
import { useAuth } from '../../auth';
import AuthModal from '../AuthModal';
import AccountMemory from './AccountMemory';

const SECTIONS = [
  ['general', Palette, '外观与语言', 'Appearance & language'],
  ['conversation', MessageCircle, '对话', 'Conversations'],
  ['personal', SlidersHorizontal, '个性化', 'Personalization'],
  ['memory', Brain, '长期记忆', 'Memory'],
  ['account', UserRound, '账户', 'Account'],
  ['data', Database, '数据管理', 'Data'],
];
const PROFILE_KEYS = ['nickname', 'about', 'custom_instructions'];
const draftFrom = profile => Object.fromEntries(PROFILE_KEYS.map(key => [key, profile?.[key] || '']));

function SettingRow({ title, description, children }) {
  return <div className="cw-setting-row"><div className="cw-setting-copy"><div className="cw-settings-label">{title}</div>{description && <p className="cw-settings-sub">{description}</p>}</div><div className="cw-setting-control">{children}</div></div>;
}
function Switch({ value, onChange, label }) {
  return <button type="button" className="cw-toggle" role="switch" aria-label={label} aria-checked={value} onClick={() => onChange(!value)}><span className="cw-toggle-knob" /></button>;
}

/** The sole settings surface; legacy UserCenterModal delegates here. */
export default function SettingsPanel({ open, onClose, initialSection = 'general', busy = false, onExploreMemory, agents = [] }) {
  const { t, lang, setLang } = useLang();
  const auth = useAuth();
  const { username, token, profile, accountReady, logout, historyStatus, retryHistory, updateProfile, authFetch } = auth;
  const zh = lang !== 'en';
  const L = (cn, en) => zh ? cn : en;
  const [section, setSection] = useState(initialSection);
  const [theme, setThemeState] = useState(getTheme());
  const [sources, setSources] = useState(() => getPref('showCitations') !== false);
  const [tools, setTools] = useState(() => getPref('toolTraceOpen') === true);
  const [responder, setResponder] = useState(() => getPref('defaultResponder') || 'general');
  const [draft, setDraft] = useState(() => draftFrom(profile));
  const [notice, setNotice] = useState(null);
  const [operation, setOperation] = useState('');
  const [showAuth, setShowAuth] = useState(false);
  const [confirm, setConfirm] = useState(null);
  const [confirmName, setConfirmName] = useState('');
  const [passwordOpen, setPasswordOpen] = useState(false);
  const [passwords, setPasswords] = useState({ current: '', next: '', repeat: '' });
  const dialogRef = useRef(null);
  const memoryDraftRef = useRef(null);
  const closeRef = useRef(onClose); closeRef.current = onClose;
  const stateRef = useRef({}); stateRef.current = { showAuth, confirm, operation };
  const signedIn = !!token && !!username;
  const changed = PROFILE_KEYS.some(key => draft[key] !== (profile?.[key] || ''));
  const selected = SECTIONS.find(([key]) => key === section) || SECTIONS[0];

  useEffect(() => { memoryDraftRef.current=null;setDraft(draftFrom(profile)); setNotice(null); setPasswords({ current: '', next: '', repeat: '' }); }, [profile?.id]);
  useEffect(() => {
    if (!open) { setPasswords({ current: '', next: '', repeat: '' }); setPasswordOpen(false); setConfirm(null); setShowAuth(false); return; }
    setThemeState(getTheme()); setSources(getPref('showCitations') !== false); setTools(getPref('toolTraceOpen') === true);
    const previous = document.activeElement; const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    const frame = requestAnimationFrame(() => dialogRef.current?.focus());
    const keydown = event => {
      if (stateRef.current.showAuth) return;
      if (event.key === 'Escape') {
        event.preventDefault();
        if (stateRef.current.operation) return;
        if (stateRef.current.confirm) setConfirm(null); else closeRef.current();
      }
      if (event.key !== 'Tab') return;
      const items = [...(dialogRef.current?.querySelectorAll('button:not([disabled]),select,input,textarea,summary,[href]') || [])].filter(el => el.getClientRects().length);
      const first = items[0], last = items.at(-1);
      if (!first) { event.preventDefault(); return; }
      if (!dialogRef.current?.contains(document.activeElement)) { event.preventDefault(); (event.shiftKey ? last : first).focus(); }
      else if (event.shiftKey && (document.activeElement === first || document.activeElement === dialogRef.current)) { event.preventDefault(); last.focus(); }
      else if (!event.shiftKey && (document.activeElement === last || document.activeElement === dialogRef.current)) { event.preventDefault(); first.focus(); }
    };
    window.addEventListener('keydown', keydown);
    return () => { cancelAnimationFrame(frame); window.removeEventListener('keydown', keydown); document.body.style.overflow = previousOverflow; if (previous?.isConnected) previous.focus?.(); };
  }, [open]);

  useEffect(() => {
    if (!confirm) return;
    const previous = document.activeElement;
    const frame = requestAnimationFrame(() => dialogRef.current?.querySelector('.cw-settings-confirm input, .cw-settings-confirm button')?.focus());
    return () => { cancelAnimationFrame(frame); if (previous?.isConnected) previous.focus?.(); };
  }, [confirm]);

  if (!open) return null;
  const close = () => { if (!operation) onClose(); };
  const pickSection = value => {
    setSection(value); setNotice(null); setConfirm(null);
    if (value !== 'account') { setPasswordOpen(false); setPasswords({ current: '', next: '', repeat: '' }); }
  };
  const run = async (name, action, success) => {
    if (operation) return;
    setOperation(name); setNotice(null);
    try { await action(); if (success) setNotice({ text: success, error: false }); }
    catch (error) { setNotice({ error: true, text: error.message === 'HISTORY_DELETE_PENDING'
      ? L('删除请求已保存在本机，连接恢复后会继续同步。', 'The deletion is queued on this device and will sync when the connection returns.')
      : ['SYNC_PENDING', 'HISTORY_BUSY'].includes(error.message)
        ? L('请等待对话保存完成后再操作。', 'Wait for conversations to finish saving first.')
        : name === 'password' && error.status === 403
          ? L('当前密码不正确，请核对后重试。', 'The current password is incorrect. Please try again.')
          : L('操作未完成，请稍后重试。', 'The action did not complete. Please try again shortly.') }); }
    finally { setOperation(''); }
  };
  const signInCard = <div className="cw-settings-empty"><UserRound size={26} aria-hidden="true" /><h3>{L('登录后继续', 'Sign in to continue')}</h3><p>{L('资料、长期记忆和对话会随账号保存。', 'Keep your profile, memory and conversations with your account.')}</p><button className="cw-settings-button cw-settings-primary" onClick={() => setShowAuth(true)}>{t('login')}</button></div>;
  const accountWaiting = <div className="cw-settings-empty"><Loader2 size={22} className={auth.authError ? '' : 'cw-spinner'} /><h3>{auth.authError ? L('账号资料暂未加载', 'Account details unavailable') : L('正在加载账号资料…', 'Loading account details…')}</h3>{auth.authError && <button className="cw-settings-button" onClick={auth.retryAccount}>{L('重新加载', 'Retry')}</button>}</div>;
  const syncLabel = signedIn ? ({ saved: L('已同步', 'Saved'), saving: L('保存中', 'Saving'), loading: L('恢复中', 'Restoring'), offline: L('连接中断', 'Offline'), 'cache-error': L('缓存异常', 'Cache unavailable') }[historyStatus] || L('等待同步', 'Waiting to sync')) : L('保存在本机', 'Saved on this device');
  const savePersonal = () => run('profile', () => updateProfile({ ...draft }), L('个性化资料已保存', 'Personalization saved'));
  const changeLocal = (key, value, setter) => {
    if (setPref(key, value)) setter(value);
    else setNotice({ error:true, text:L('无法保存本机偏好，请检查浏览器存储空间。','Could not save this preference. Check browser storage.') });
  };
  const changePassword = event => {
    event.preventDefault();
    if (passwords.next.length < 8) { setNotice({ error: true, text: t('pwdShort') }); return; }
    if (passwords.next !== passwords.repeat) { setNotice({ error: true, text: L('两次输入的新密码不一致。', 'The new passwords do not match.') }); return; }
    run('password', async () => {
      const result = await authFetch('/api/user/password', { method: 'PUT', body: JSON.stringify({ old_password: passwords.current, new_password: passwords.next }) });
      if (result.status !== 'ok' && !result.success) throw new Error('Password update failed');
      setPasswords({ current: '', next: '', repeat: '' }); setPasswordOpen(false);
    }, t('pwdUpdated'));
  };
  const confirmedAction = () => {
    const action = confirm;
    if (action === 'account' && confirmName !== username) return;
    setConfirm(null);
    run(action, async () => {
      if (action === 'cache') { auth.clearDeviceCache(); window.location.assign('/agent'); }
      if (action === 'history') { await auth.deleteConversationHistory(); window.location.assign('/agent'); }
      if (action === 'account') {
        await auth.deleteAccount(); onClose();
      }
    });
  };

  return createPortal(<>
    <div className="cw-settings-scrim" onClick={close} />
    <div className="cw-settings" role="dialog" aria-modal="true" aria-labelledby="cw-settings-title" tabIndex={-1} ref={dialogRef}>
      <header className="cw-settings-head"><h2 id="cw-settings-title">{t('settings')}</h2><button className="cw-icon-btn" onClick={close} disabled={!!operation} aria-label={L('关闭设置', 'Close settings')}><X size={18} /></button></header>
      <div className="cw-settings-inner">
        <nav className="cw-settings-nav" aria-label={L('设置分类', 'Settings categories')}>
          {SECTIONS.map(([key, Icon, cn, en]) => <button key={key} className={`cw-settings-nav-btn${section === key ? ' cw-settings-active' : ''}`} aria-current={section === key ? 'page' : undefined} onClick={() => pickSection(key)}><Icon size={16} aria-hidden="true" />{L(cn, en)}</button>)}
          <span className="cw-settings-version">PhiAgent {__PHIAGENT_VERSION__}</span>
        </nav>
        <label className="cw-settings-mobile-nav">{L('设置分类', 'Settings categories')}<select value={section} onChange={e => pickSection(e.target.value)}>{SECTIONS.map(([key,,cn,en]) => <option key={key} value={key}>{L(cn,en)}</option>)}</select></label>
        <div className="cw-settings-body" aria-labelledby="cw-settings-section-title">
          <div className="cw-settings-section-head"><h3 id="cw-settings-section-title">{L(selected[2], selected[3])}</h3></div>
          {notice && <div className={`cw-settings-notice${notice.error ? ' cw-settings-notice-error' : ''}`} role={notice.error ? 'alert' : 'status'}>{notice.error ? null : <Check size={14} />}{notice.text}</div>}
          {section === 'general' && <>
            <SettingRow title={t('theme')} description={L('选择界面的明暗外观。', 'Choose how the interface looks.')}><select aria-label={t('theme')} value={theme} onChange={e => run('theme',() => { setTheme(e.target.value); setThemeState(e.target.value); })}>{[['light',t('themeLight')],['dark',t('themeDark')],['auto',t('themeAuto')]].map(([v,label]) => <option key={v} value={v}>{label}</option>)}</select></SettingRow>
            <SettingRow title={t('language')} description={L('用于界面、回答和思考过程。', 'Used for the interface, answers and reasoning.')}><select aria-label={t('language')} value={lang} disabled={!!operation} onChange={e => { const value=e.target.value;run('language', () => setLang(value), value==='zh' ? '语言偏好已保存' : 'Language preference saved'); }}><option value="zh">中文</option><option value="en">English</option></select></SettingRow>
          </>}
          {section === 'conversation' && <>
            <SettingRow title={t('defaultResponder')} description={t('defaultResponderDesc')}><select aria-label={t('defaultResponder')} value={responder} onChange={e => changeLocal('defaultResponder',e.target.value,setResponder)}>{(agents.length ? agents : [{key:'general'}, {key:'nietzsche'}]).map(a => <option key={a.key} value={a.key}>{AGENT_NAMES[a.key]?.[lang] || (lang === 'en' ? a.name_en : a.name) || a.name || a.key}</option>)}</select></SettingRow>
            <SettingRow title={L('显示回答来源', 'Show answer sources')} description={L('展示回答下方的原典与补充资料，正文引用仍可点击。', 'Show sources below answers. Inline citations remain available.')}><Switch label={L('显示回答来源', 'Show answer sources')} value={sources} onChange={v => changeLocal('showCitations',v,setSources)} /></SettingRow>
            <SettingRow title={L('展开工具结果', 'Expand tool results')} description={L('默认展示检索与工具调用的详细结果。', 'Show retrieval and tool results expanded by default.')}><Switch label={L('展开工具结果', 'Expand tool results')} value={tools} onChange={v => changeLocal('toolTraceOpen',v,setTools)} /></SettingRow>
          </>}
          {section === 'personal' && (signedIn && !accountReady ? accountWaiting : signedIn ? <form className="cw-settings-form" onSubmit={e => { e.preventDefault(); savePersonal(); }}>
            <p className="cw-settings-desc">{L('让深哲了解你的背景，以及你偏好的交流方式。', 'Share your background and how you prefer to discuss ideas.')}</p>
            <label>{t('nickname')}<input value={draft.nickname} onChange={e => setDraft({ ...draft, nickname:e.target.value })} placeholder={L('怎么称呼你', 'What should we call you?')} /><small>{L('用于账号入口的显示名称。', 'Shown in your account entry.')}</small></label>
            <label>{L('关于你', 'About you')}<textarea rows={3} value={draft.about} onChange={e => setDraft({ ...draft,about:e.target.value })} placeholder={L('例如：正在读康德，关注伦理与技术问题', 'For example: reading Kant, interested in ethics and technology')} /></label>
            <label>{L('回答偏好', 'Response preferences')}<textarea rows={3} value={draft.custom_instructions} onChange={e => setDraft({ ...draft,custom_instructions:e.target.value })} placeholder={L('例如：先给简洁判断，再展开理由；引用原文时注明出处', 'For example: start with a concise judgment, then explain the reasoning')} /><small>{L('适用于新请求；当前提问中的要求优先。', 'Used for new requests. Instructions in your current question take precedence.')}</small></label>
            <div className="cw-settings-form-footer"><button type="submit" className="cw-settings-button cw-settings-primary" disabled={!changed || !accountReady || !!operation}>{operation === 'profile' ? <Loader2 size={14} className="cw-spinner" /> : null}{operation === 'profile' ? L('保存中…', 'Saving…') : t('save')}</button><span>{changed ? L('有未保存的修改', 'Unsaved changes') : L('已保存到账号', 'Saved to your account')}</span></div>
          </form> : signInCard)}
          {section === 'memory' && <AccountMemory key={profile?.id || 'guest'} lang={lang} onSignIn={() => setShowAuth(true)} draftState={memoryDraftRef.current} onDraftChange={state=>{memoryDraftRef.current=state;}} onExplore={onExploreMemory} conversationBusy={busy} />}
          {section === 'account' && (signedIn ? <>
            <div className="cw-settings-account-card"><span className="cw-settings-avatar">{(profile?.nickname || username).slice(0,1).toUpperCase()}</span><div><strong>{profile?.nickname || username}</strong><span>{username}</span></div></div>
            <SettingRow title={L('对话保存', 'Conversation saving')} description={L('登录后，对话会自动同步到当前账号。', 'Conversations sync automatically to your account.')}><span className="cw-settings-status">{syncLabel}</span></SettingRow>
            <SettingRow title={t('updatePassword')} description={L('使用当前密码验证后修改。', 'Verify your current password before changing it.')}><button className="cw-settings-button" disabled={!!operation || !accountReady} onClick={() => { setPasswordOpen(v => !v); setPasswords({current:'',next:'',repeat:''}); setNotice(null); }}>{passwordOpen ? L('取消修改', 'Cancel') : L('修改', 'Change')}</button></SettingRow>
            {passwordOpen && <form className="cw-settings-form cw-settings-password-form" onSubmit={changePassword}>{[['current',L('当前密码','Current password'),'current-password'],['next',L('新密码','New password'),'new-password'],['repeat',L('再次输入新密码','Confirm new password'),'new-password']].map(([key,label,autocomplete]) => <label key={key}>{label}<input type="password" autoComplete={autocomplete} required minLength={key === 'current' ? undefined : 8} value={passwords[key]} onChange={e => setPasswords({...passwords,[key]:e.target.value})} /></label>)}<button className="cw-settings-button cw-settings-primary" disabled={!!operation}>{operation === 'password' ? L('更新中…','Updating…') : L('更新密码','Update password')}</button></form>}
            <SettingRow title={L('退出当前账号','Sign out')} description={L('账号对话与长期记忆仍会保留。','Your account conversations and memories are kept.')}><button className="cw-settings-button" disabled={!!operation} onClick={() => { logout(); onClose(); }}><LogOut size={14} />{t('logout')}</button></SettingRow>
          </> : signInCard)}
          {section === 'data' && <>
            <SettingRow title={L('对话记录','Conversations')} description={signedIn ? L('保存在账号中，并在本机保留缓存。','Saved to your account with a cache on this device.') : L('未登录的对话只保存在当前浏览器。','Guest conversations are saved only in this browser.')}><span className="cw-settings-status">{syncLabel}</span></SettingRow>
            {signedIn && ['offline','cache-error'].includes(historyStatus) && <button className="cw-settings-button" disabled={!!operation} onClick={() => run('sync',retryHistory)}>{L('重新同步','Retry sync')}</button>}
            {signedIn && <SettingRow title={L('本机缓存','Device cache')} description={L('清除后会从账号恢复对话。请先等待同步完成。','Conversations will be restored from your account. Wait for saving to finish first.')}><button className="cw-settings-button" disabled={busy || !!operation || historyStatus !== 'saved'} onClick={() => setConfirm('cache')}>{L('清除缓存','Clear cache')}</button></SettingRow>}
            <SettingRow title={signedIn ? L('删除全部对话','Delete all conversations') : L('删除本机对话','Delete device conversations')} description={signedIn ? L('删除当前账号的全部智能体对话。长期记忆单独管理。','Delete this account’s agent conversations. Memory is managed separately.') : L('删除当前浏览器里的对话与草稿。','Delete conversations and drafts from this browser.')}><button className="cw-settings-button cw-settings-danger" disabled={busy || !!operation || (signedIn && !accountReady)} onClick={() => setConfirm('history')}>{L('删除对话','Delete')}</button></SettingRow>
            {signedIn && <details className="cw-settings-danger-zone"><summary>{L('删除账户','Delete account')}</summary><p>{L('账户、对话和长期记忆将被永久删除。','Your account, conversations and memory will be permanently deleted.')}</p><button className="cw-settings-button cw-settings-danger" disabled={busy || !!operation || !accountReady} onClick={() => { setConfirmName('');setConfirm('account'); }}>{t('deleteAccount')}</button></details>}
            {busy && <p className="cw-settings-desc">{L('回答生成中，完成后可管理对话数据。','Conversation data can be managed after generation finishes.')}</p>}
          </>}
          {confirm && <div className="cw-settings-confirm" role="alertdialog" aria-labelledby="cw-settings-confirm-title">
            <h4 id="cw-settings-confirm-title">{confirm === 'cache' ? L('清除本机缓存？','Clear device cache?') : confirm === 'history' ? L('删除全部对话？','Delete all conversations?') : L('永久删除账户？','Permanently delete account?')}</h4>
            <p>{confirm === 'cache' ? L('账号中的对话会保留，下次打开时恢复。','Account conversations remain saved and will be restored next time.') : confirm === 'history' ? (signedIn ? L('账号中的对话及本机缓存都会删除，无法撤销。','Conversations in this account and its device cache will be deleted. This cannot be undone.') : L('本机对话和草稿都会删除，无法撤销。','Device conversations and drafts will be deleted. This cannot be undone.')) : L('请输入用户名确认。账户及关联数据删除后无法恢复。','Type your username to confirm. The account and associated data cannot be restored.')}</p>
            {confirm === 'account' && <input aria-label={L('输入用户名确认删除','Type username to confirm deletion')} value={confirmName} onChange={e => setConfirmName(e.target.value)} placeholder={username} />}
            <div><button className="cw-settings-button" onClick={() => setConfirm(null)}>{t('cancel')}</button><button className="cw-settings-button cw-settings-danger" disabled={confirm === 'account' && confirmName !== username} onClick={confirmedAction}>{confirm === 'cache' ? L('清除缓存','Clear cache') : L('确认删除','Confirm deletion')}</button></div>
          </div>}
        </div>
      </div>
    </div>
    {showAuth && <AuthModal onClose={() => setShowAuth(false)} />}
  </>, document.body);
}
