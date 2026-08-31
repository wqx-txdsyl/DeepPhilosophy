import { useState } from 'react';
import { createPortal } from 'react-dom';
import { Plus, Compass, Settings, EllipsisVertical, LogOut, CircleUserRound } from 'lucide-react';
import { useAuth } from '../../auth';
import { useLang } from '../../utils/i18n';
import { groupConversationsByDay } from '../../data/conversationLogic';
import AuthModal from '../AuthModal';
import UserCenterModal from '../UserCenterModal';
import { ConfirmModal, RenameModal, ContextMenu, anchorFromEvent } from './Modal';

/**
 * ConversationSidebar — 会话历史侧栏（spec §5）
 * 顶部: 品牌 + ＋新对话 + ◇探索智能体; 中部: 今天/昨天/过去 7 天/更早 分组历史
 * （空分组不显示）; 底部固定: 设置 + 登录/用户。
 * Active 仅轻微背景差异; hover 出现 ···（重命名/删除, 删除需确认）。
 * 2026-08-31 Codex-Parity: lucide 图标 + 全 aria + 设置入口（§24）。
 */
export default function ConversationSidebar({
  conversations, activeId, streamingIds, open, onClose, collapsed,
  onSelect, onNew, onExplore, onRename, onDelete, onOpenSettings,
}) {
  const { t } = useLang();
  const { username, logout } = useAuth();
  const [menuFor, setMenuFor] = useState(null);       // 打开了菜单的会话 id
  const [menuAnchor, setMenuAnchor] = useState(null); // {left,top,bottom} fixed 锚点
  const [renaming, setRenaming] = useState(null);     // 重命名目标会话
  const [deleting, setDeleting] = useState(null);     // 删除确认目标会话
  const [showAuth, setShowAuth] = useState(false);
  const [showCenter, setShowCenter] = useState(false);
  const groups = groupConversationsByDay(conversations);

  const openMenu = (e, convId) => {
    setMenuAnchor(anchorFromEvent(e));
    setMenuFor(convId);
  };

  return (
    <>
      <div className={`cw-sidebar${open ? ' cw-sidebar-open' : ''}${collapsed ? ' cw-sidebar-hidden' : ''}`}>
        <div className="cw-sidebar-inner">
          {/* 品牌 */}
          <div className="cw-brand">
            <div className="cw-brand-name">DeepPhilosophy</div>
            <div className="cw-brand-sub">PHIAGENT</div>
          </div>
          {/* 主操作 */}
          <div className="cw-side-actions">
            <button className="cw-btn cw-btn-primary" onClick={() => { onClose(); onNew(); }}>
              <Plus size={15} aria-hidden /> {t('newChat')}
            </button>
            <button className="cw-btn cw-btn-ghost" onClick={() => { onClose(); onExplore(); }}>
              <Compass size={15} aria-hidden /> {t('exploreAgents')}
            </button>
          </div>
          {/* 历史会话（独立滚动） */}
          <div className="cw-conv-scroll">
            {groups.map(([key, items]) => (
              <div key={key}>
                <div className="cw-group-label">{t(`grp_${key}`)}</div>
                {items.map((c) => {
                  const active = c.conversation_id === activeId;
                  return (
                    <div key={c.conversation_id} role="button" tabIndex={0}
                      className={`cw-conv-item${active ? ' cw-conv-active' : ''}`}
                      onClick={() => { onClose(); onSelect(c.conversation_id); }}
                      onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onClose(); onSelect(c.conversation_id); } }}
                      aria-current={active ? 'true' : undefined}>
                      {streamingIds?.has(c.conversation_id) && (
                        <span className="cw-stream-dot" title={t('streaming')} aria-label={t('streaming')} />
                      )}
                      <span className="cw-conv-title">{c.title || t('untitled')}</span>
                      <span className="cw-item-menu"
                        role="button" tabIndex={0} aria-label={`${t('convMenu')}: ${c.title || t('untitled')}`}
                        onClick={(e) => { e.stopPropagation(); openMenu(e, c.conversation_id); }}
                        onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); e.stopPropagation(); openMenu(e, c.conversation_id); } }}
                        title={t('convMenu')}>
                        <EllipsisVertical size={14} />
                      </span>
                    </div>
                  );
                })}
              </div>
            ))}
          </div>
          {/* 底部固定: 设置 + 用户（§24 设置入口） */}
          <div className="cw-side-footer">
            <button className="cw-side-row" onClick={onOpenSettings}>
              <Settings size={15} aria-hidden /> {t('settings')}
            </button>
            {username ? (
              <>
                <button className="cw-side-row" onClick={() => setShowCenter(true)}>
                  <CircleUserRound size={15} aria-hidden />
                  <span style={{ flex: 1, minWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{username}</span>
                </button>
                <button className="cw-side-row" onClick={logout} style={{ color: 'var(--text-dim)' }}>
                  <LogOut size={15} aria-hidden /> {t('logout')}
                </button>
              </>
            ) : (
              <button className="cw-side-row" onClick={() => setShowAuth(true)}>
                <CircleUserRound size={15} aria-hidden /> {t('login')}
              </button>
            )}
          </div>
        </div>
      </div>
      {/* 移动端抽屉遮罩 */}
      {open && <div className="cw-scrim" onClick={onClose} />}
      {/* ··· 菜单（fixed + portal, 不被侧栏滚动容器裁剪） */}
      {menuFor && menuAnchor && (
        <ContextMenu
          anchor={menuAnchor}
          onClose={() => { setMenuFor(null); setMenuAnchor(null); }}
          items={[
            { label: t('rename'), onClick: () => {
                const conv = conversations.find(c => c.conversation_id === menuFor);
                if (conv) setRenaming(conv);
              } },
            { label: t('del'), danger: true, onClick: () => {
                const conv = conversations.find(c => c.conversation_id === menuFor);
                if (conv) setDeleting(conv);
              } },
          ]}
        />
      )}
      {/* 自研弹窗（重命名/删除确认） */}
      {renaming && (
        <RenameModal title={t('rename')} initial={renaming.title}
          onClose={() => setRenaming(null)}
          onConfirm={(newTitle) => { onRename(renaming, newTitle); setRenaming(null); }} />
      )}
      {deleting && (
        <ConfirmModal title={t('del')} message={t('delConvConfirm')}
          onClose={() => setDeleting(null)}
          onConfirm={() => { onDelete(deleting); setDeleting(null); }} />
      )}
      {showAuth && createPortal(<AuthModal onClose={() => setShowAuth(false)} />, document.body)}
      {showCenter && createPortal(<UserCenterModal onClose={() => setShowCenter(false)} />, document.body)}
    </>
  );
}
