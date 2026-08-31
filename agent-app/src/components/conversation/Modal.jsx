import { useState } from 'react';
import { createPortal } from 'react-dom';
import { useLang } from '../../utils/i18n';

/**
 * 自研弹窗/菜单（2026-08-29 重构反馈修复）:
 * - 重命名/删除 不再用浏览器原生 prompt/confirm: 黑白灰风格 Modal（用户中心/登出同风格）
 * - ··· 菜单用 fixed 定位 + portal 到 body: 不被侧栏滚动容器(.cw-conv-scroll overflow)裁剪,
 *   层级在页面最顶端, 不再出现"渲染位置不对/被遮挡"
 */

export function OverlayModal({ children, onClose, width = 360, zIndex = 1500 }) {
  return createPortal(
    <>
      <div onClick={onClose} style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,.35)', zIndex }} />
      <div onClick={(e) => e.stopPropagation()}
        style={{ position: 'fixed', left: '50%', top: '48%', transform: 'translate(-50%,-50%)',
                 width, maxWidth: 'calc(100vw - 40px)', maxHeight: 'calc(100vh - 60px)', overflowY: 'auto',
                 background: 'var(--card-bg)', border: '1px solid var(--border)', borderRadius: 14,
                 boxShadow: '0 12px 40px rgba(0,0,0,.18)', zIndex: zIndex + 1, padding: 16 }}>
        {children}
      </div>
    </>,
    document.body,
  );
}

/* ── 确认弹窗（删除等危险操作）── */
export function ConfirmModal({ title, message, confirmText, cancelText, danger = true, onConfirm, onClose }) {
  const { t } = useLang();
  return (
    <OverlayModal onClose={onClose} width={340}>
      <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 8 }}>{title}</div>
      <div style={{ fontSize: 13, color: 'var(--text-dim)', lineHeight: 1.7, marginBottom: 16, whiteSpace: 'pre-wrap' }}>
        {message}
      </div>
      <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
        <button onClick={onClose}
          style={{ padding: '7px 14px', borderRadius: 8, cursor: 'pointer', fontSize: 13,
                   border: '1px solid var(--border)', background: 'var(--card-bg)', color: 'var(--text)' }}>
          {cancelText || t('cancel')}
        </button>
        <button onClick={onConfirm}
          style={{ padding: '7px 14px', borderRadius: 8, cursor: 'pointer', fontSize: 13, border: 'none',
                   background: danger ? '#b4544a' : 'var(--accent)', color: '#fff' }}>
          {confirmText || t('confirm')}
        </button>
      </div>
    </OverlayModal>
  );
}

/* ── 重命名弹窗（自动聚焦, Enter 确认 / Esc 取消）── */
export function RenameModal({ title, initial, onConfirm, onClose }) {
  const { t } = useLang();
  const [value, setValue] = useState(initial || '');
  return (
    <OverlayModal onClose={onClose} width={340}>
      <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 8 }}>{title}</div>
      <input value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === 'Enter' && value.trim()) onConfirm(value.trim());
          if (e.key === 'Escape') onClose();
        }}
        autoFocus
        placeholder={t('untitled')}
        style={{ width: '100%', padding: '8px 10px', borderRadius: 8, fontSize: 13, outline: 'none',
                 border: '1px solid var(--border)', background: 'var(--soft)', color: 'var(--text)' }} />
      <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end', marginTop: 14 }}>
        <button onClick={onClose}
          style={{ padding: '7px 14px', borderRadius: 8, cursor: 'pointer', fontSize: 13,
                   border: '1px solid var(--border)', background: 'var(--card-bg)', color: 'var(--text)' }}>
          {t('cancel')}
        </button>
        <button onClick={() => value.trim() && onConfirm(value.trim())}
          style={{ padding: '7px 14px', borderRadius: 8, cursor: 'pointer', fontSize: 13, border: 'none',
                   background: 'var(--accent)', color: 'var(--bg)' }}>
          {t('confirm')}
        </button>
      </div>
    </OverlayModal>
  );
}

/* ── ··· 上下文菜单（fixed 定位 + portal: 不被滚动容器裁剪, 始终最顶） ── */
export function ContextMenu({ anchor, items, onClose, minWidth = 132 }) {
  if (!anchor) return null;
  const itemH = 34;
  const estH = items.length * itemH + 8;
  const left = Math.min(anchor.left, window.innerWidth - minWidth - 8);
  const top = anchor.bottom + 4 + estH > window.innerHeight
    ? Math.max(8, anchor.top - 4 - estH)
    : anchor.bottom + 4;
  return createPortal(
    <>
      <div onClick={onClose} style={{ position: 'fixed', inset: 0, zIndex: 1590 }} />
      <div onClick={(e) => e.stopPropagation()}
        style={{ position: 'fixed', left, top, minWidth, zIndex: 1595,
                 background: 'var(--card-bg)', border: '1px solid var(--border)', borderRadius: 10,
                 boxShadow: '0 8px 28px rgba(0,0,0,.16)', padding: 4, display: 'flex', flexDirection: 'column' }}>
        {items.map((it, i) => (
          <button key={i} onClick={() => { onClose(); it.onClick(); }}
            style={{ display: 'block', width: '100%', textAlign: 'left', padding: '8px 12px',
                     fontSize: 12.5, border: 'none', background: 'transparent', borderRadius: 6,
                     cursor: 'pointer', color: it.danger ? '#b4544a' : 'var(--text)' }}>
            {it.label}
          </button>
        ))}
      </div>
    </>,
    document.body,
  );
}

/** 读取触发元素 rect 作为锚点（点击 ··· 时调用） */
export function anchorFromEvent(e) {
  const r = e.currentTarget.getBoundingClientRect();
  return { left: r.left, top: r.top, bottom: r.bottom };
}
