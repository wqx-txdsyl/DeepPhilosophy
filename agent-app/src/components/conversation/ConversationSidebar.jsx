import { useState } from 'react';
import { Plus, Compass, Settings, EllipsisVertical, CircleUserRound } from 'lucide-react';
import { useAuth } from '../../auth';
import { useLang } from '../../utils/i18n';
import { groupConversationsByDay } from '../../data/conversationLogic';
import { ConfirmModal, RenameModal, ContextMenu, anchorFromEvent } from './Modal';

/**
 * ConversationSidebar — 会话历史侧栏（spec §5）
 * 顶部: 品牌 + ＋新对话 + ◇探索智能体; 中部: 今天/昨天/过去 7 天/更早 分组历史
 * （空分组不显示）; 底部仅保留统一的设置与账户入口。
 * Active 仅轻微背景差异; hover 出现 ···（重命名/删除, 删除需确认）。
 * 2026-08-31 Codex-Parity: lucide 图标 + 全 aria + 设置入口（§24）。
 */
export default function ConversationSidebar({
  conversations, activeId, streamingIds, open, onClose, collapsed,
  onSelect, onNew, onExplore, onRename, onDelete, onOpenSettings,
}) {
  const { t, lang } = useLang();
  const { username, profile, token, historyStatus, retryHistory } = useAuth();
  const [menuFor, setMenuFor] = useState(null);       // 打开了菜单的会话 id
  const [menuAnchor, setMenuAnchor] = useState(null); // {left,top,bottom} fixed 锚点
  const [renaming, setRenaming] = useState(null);     // 重命名目标会话
  const [deleting, setDeleting] = useState(null);     // 删除确认目标会话
  const groups = groupConversationsByDay(conversations);

  const openMenu = (e, convId) => {
    setMenuAnchor(anchorFromEvent(e));
    setMenuFor(convId);
  };

  return (
    <>
      <div id="cw-history-sidebar" className={`cw-sidebar${open ? ' cw-sidebar-open' : ''}${collapsed ? ' cw-sidebar-hidden' : ''}`}>
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
            {!conversations.length && <div className="cw-history-empty" role="status">
              {token && ['loading','offline'].includes(historyStatus)
                ? (lang === 'zh' ? (historyStatus === 'loading' ? '正在恢复对话…' : '历史暂未加载') : 'Restoring conversation history')
                : (lang === 'zh' ? '还没有对话' : 'No conversations yet')}
              {token && historyStatus === 'offline' && <button onClick={retryHistory}>{t('retry')}</button>}
            </div>}
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
          {/* One entry for preferences and account management. */}
          <div className="cw-side-footer">
            <button className="cw-side-row cw-account-entry" aria-label={lang === 'zh' ? '设置与账户' : 'Settings and account'} onClick={() => { onClose(); onOpenSettings(); }}>
              {username ? <span className="cw-account-avatar">{(profile?.nickname || username).slice(0,1).toUpperCase()}</span> : <CircleUserRound size={23} aria-hidden="true" />}
              <span className="cw-account-entry-copy"><span>{profile?.nickname || username || t('settings')}</span><small>{lang === 'zh' ? (username ? '设置与账户' : '登录与偏好') : (username ? 'Settings and account' : 'Sign in & preferences')}</small></span>
              <Settings size={16} className="cw-account-entry-gear" aria-hidden="true" />
            </button>
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
    </>
  );
}
