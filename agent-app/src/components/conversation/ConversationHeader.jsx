import { useState } from 'react';
import { PanelLeft, PanelLeftOpen, Menu, EllipsisVertical } from 'lucide-react';
import { useLang } from '../../utils/i18n';
import { ConfirmModal, RenameModal, ContextMenu, anchorFromEvent } from './Modal';

/**
 * ConversationHeader — 右侧顶部（spec §6）: conversation.title 而非巨大标题;
 * 上下文状态（streaming dot）+ 少量会话操作（··· 重命名/删除）。
 * 2026-08-31: 桌面侧栏收起/展开开关 + 移动端抽屉按钮, 全 aria（§32）。
 */
export default function ConversationHeader({
  title, isDraft, streaming, onOpenNav, onToggleSidebar, onRename, onDelete,
}) {
  const { t } = useLang();
  const [menuAnchor, setMenuAnchor] = useState(null);
  const [renaming, setRenaming] = useState(false);
  const [deleting, setDeleting] = useState(false);
  return (
    <div className="cw-header">
      <button className="cw-nav-btn cw-icon-btn" onClick={onOpenNav} title={t('conversations')} aria-label={t('conversations')}>
        <Menu size={16} />
      </button>
      <button className="cw-side-toggle cw-icon-btn" onClick={onToggleSidebar}
        title={t('collapseSidebar')} aria-label={t('collapseSidebar')}>
        <PanelLeft size={16} />
      </button>
      <div style={{ flex: 1, minWidth: 0, display: 'flex', alignItems: 'center', gap: 8 }}>
        <span className="cw-header-title">{title || t('untitled')}</span>
        {streaming && <span className="cw-stream-dot" title={t('streaming')} aria-label={t('streaming')} />}
      </div>
      {!isDraft && (
        <button className="cw-icon-btn" onClick={(e) => setMenuAnchor(anchorFromEvent(e))}
          aria-label={t('convMenu')} title={t('convMenu')}>
          <EllipsisVertical size={15} />
        </button>
      )}
      {!isDraft && menuAnchor && (
        <ContextMenu
          anchor={menuAnchor}
          onClose={() => setMenuAnchor(null)}
          items={[
            { label: t('rename'), onClick: () => setRenaming(true) },
            { label: t('del'), danger: true, onClick: () => setDeleting(true) },
          ]}
        />
      )}
      {!isDraft && renaming && (
        <RenameModal title={t('rename')} initial={title}
          onClose={() => setRenaming(false)}
          onConfirm={(newTitle) => { onRename(newTitle); setRenaming(false); }} />
      )}
      {!isDraft && deleting && (
        <ConfirmModal title={t('del')} message={t('delConvConfirm')}
          onClose={() => setDeleting(false)}
          onConfirm={() => { onDelete(); setDeleting(false); }} />
      )}
    </div>
  );
}
