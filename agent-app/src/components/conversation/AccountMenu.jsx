import { useEffect, useLayoutEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { ChevronDown, CircleUserRound, LogOut, Settings } from 'lucide-react';
import { useAuth } from '../../auth';
import { useLang } from '../../utils/i18n';
import PwaInstall from './PwaInstall';

/** One quiet footer row; account actions appear only when requested. */
export default function AccountMenu({ onOpenSettings, onCloseSidebar, collapsed, sidebarOpen }) {
  const { username, profile, token, logout } = useAuth();
  const { lang, t } = useLang();
  const [open, setOpen] = useState(false);
  const [position, setPosition] = useState({ left: 8, bottom: 60, width: 260 });
  const trigger = useRef(null), menu = useRef(null);
  const focusLast = useRef(false);
  const name = profile?.nickname || username;
  const zh = lang !== 'en';
  const dismiss = (restoreFocus = false) => {
    setOpen(false);
    if (restoreFocus) trigger.current?.focus();
  };
  const items = () => [...(menu.current?.querySelectorAll('[role="menuitem"]:not([disabled])') || [])];
  const reveal = (last = false) => {
    const r = trigger.current.getBoundingClientRect();
    const width = Math.min(272, window.innerWidth - 16);
    setPosition({ width, left: Math.max(8, Math.min(r.left, window.innerWidth - width - 8)),
      bottom: Math.max(8, window.innerHeight - r.top + 6) });
    focusLast.current = last;
    if (open) (last ? items().at(-1) : items()[0])?.focus();
    else setOpen(true);
  };
  useLayoutEffect(() => { if (open) (focusLast.current ? items().at(-1) : items()[0])?.focus(); }, [open]);
  useEffect(() => { setOpen(false); }, [collapsed, sidebarOpen, token, profile?.id]);
  useEffect(() => {
    if (!open) return;
    const outside = e => { if (!menu.current?.contains(e.target) && !trigger.current?.contains(e.target)) dismiss(); };
    const escape = e => { if (e.key === 'Escape') { e.preventDefault(); dismiss(true); } };
    const resize = () => dismiss(true);
    const tabAway = e => { if (!menu.current?.contains(e.target) && !trigger.current?.contains(e.target)) dismiss(); };
    document.addEventListener('pointerdown', outside);
    document.addEventListener('focusin', tabAway);
    window.addEventListener('keydown', escape);
    window.addEventListener('resize', resize);
    return () => {
      document.removeEventListener('pointerdown', outside);
      document.removeEventListener('focusin', tabAway);
      window.removeEventListener('keydown', escape);
      window.removeEventListener('resize', resize);
    };
  }, [open]);
  function navigateItems(e) {
    const list = items();
    if (!list.length) return;
    const current = list.indexOf(document.activeElement);
    const next = e.key === 'ArrowDown' ? (current + 1) % list.length
      : e.key === 'ArrowUp' ? (current - 1 + list.length) % list.length
        : e.key === 'Home' ? 0 : e.key === 'End' ? list.length - 1 : null;
    if (next !== null) { e.preventDefault(); list[next].focus(); }
  }
  return <>
    <button ref={trigger} className="cw-account-entry" aria-label={zh ? '账户菜单' : 'Account menu'}
      aria-haspopup="menu" aria-expanded={open} aria-controls="cw-account-menu" title={name || (zh ? '账户与设置' : 'Account & settings')}
      onClick={() => open ? dismiss(true) : reveal()}
      onKeyDown={e => { if (e.key === 'ArrowDown' || e.key === 'ArrowUp') { e.preventDefault(); reveal(e.key === 'ArrowUp'); } }}>
      {name ? <span className="cw-account-avatar" aria-hidden="true">{[...name][0].toUpperCase()}</span> : <CircleUserRound size={20} aria-hidden="true" />}
      <span className="cw-account-name">{name || (zh ? '未登录' : 'Guest')}</span>
      <span className="cw-account-product" aria-hidden="true">· PhiAgent</span>
      <ChevronDown size={14} className="cw-account-chevron" aria-hidden="true" />
    </button>
    {createPortal(<div id="cw-account-menu" ref={menu} role="menu" aria-label={zh ? '账户操作' : 'Account actions'}
      className="cw-account-menu" hidden={!open} style={position} onKeyDown={navigateItems}>
      <div className="cw-account-menu-heading" role="presentation"><strong>{name || (zh ? '欢迎使用' : 'Welcome')}</strong><span>PhiAgent</span></div>
      <button role="menuitem" className="cw-account-menu-item" onClick={() => { dismiss(true); onCloseSidebar(); onOpenSettings(); }}><Settings size={16} aria-hidden="true"/><span>{t('settings')}</span></button>
      {/* Keep installation state mounted so its help dialog survives closing this menu. */}
      <PwaInstall className="cw-account-menu-item" role="menuitem" onActivate={() => dismiss(true)} />
      {token && <><div className="cw-account-menu-separator" role="separator"/><button role="menuitem" className="cw-account-menu-item" onClick={() => { dismiss(true); onCloseSidebar(); logout(); }}><LogOut size={16} aria-hidden="true"/><span>{zh ? '退出登录' : 'Sign out'}</span></button></>}
    </div>, document.body)}
  </>;
}
