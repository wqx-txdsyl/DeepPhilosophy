/**
 * NavBar — 统一的导航栏组件
 * variant: 'sticky' (标准header) | 'floating' (首页浮动透明) | 'hidden' (无导航)
 */
import { useNavigate, useLocation } from 'react-router-dom';
import Icon from './Icon';

const TABS = [
  { key: 'books', icon: 'nav-books', text: '书籍', path: '/books' },
  { key: 'authors', icon: 'nav-authors', text: '哲人', path: '/authors' },
  { key: 'genealogy', icon: 'nav-genealogy', text: '谱系', path: '/genealogy' },
  { key: 'qa', icon: 'nav-qa', text: '问答', path: '/qa' },
  { key: 'games', icon: 'nav-games', text: '游戏', path: '/games' },
];

function getActiveTab(pathname) {
  if (pathname === '/') return null; // 首页不高亮任何 tab
  if (pathname.startsWith('/authors') || pathname.startsWith('/author')) return 'authors';
  if (pathname.startsWith('/genealogy')) return 'genealogy';
  if (pathname.startsWith('/qa')) return 'qa';
  if (pathname.startsWith('/games')) return 'games';
  if (pathname.startsWith('/school')) return 'genealogy';
  if (pathname.startsWith('/book') || pathname === '/books') return 'books';
  return null;
}

export default function NavBar({
  variant = 'sticky',
  darkMode,
  mobileMode,
  onToggleDarkMode,
  onToggleMobileMode,
  loggedIn,
  username,
  userAvatar,
}) {
  const navigate = useNavigate();
  const location = useLocation();
  const activeTab = getActiveTab(location.pathname);

  if (variant === 'hidden') return null;

  const isFloating = variant === 'floating';

  return (
    <nav
      className={isFloating ? 'navbar-floating' : 'app-header'}
      role="navigation"
      aria-label="主导航"
    >
      <h1
        className="app-title"
        onClick={() => navigate('/')}
        style={{ marginRight: 4 }}
      >
        DeepPhilosophy
      </h1>

      <span style={{ display: 'flex', gap: 0, marginRight: 'auto', marginLeft: -2 }}>
        {TABS.map((tab) => (
          <button
            key={tab.key}
            className={`nav-btn ${activeTab === tab.key ? 'active' : ''}`}
            onClick={() => navigate(tab.path)}
            aria-current={activeTab === tab.key ? 'page' : undefined}
            style={{ flexDirection: 'row', gap: 3, fontSize: 12, padding: '4px 8px' }}
          >
            <Icon name={tab.icon} size={16} />
            <span>{tab.text}</span>
          </button>
        ))}
      </span>

      {isFloating ? (
        /* 首页浮动：仅显示登录按钮 */
        <button
          className="navbar-login-btn"
          onClick={() => navigate('/profile')}
          aria-label={loggedIn && username ? `用户: ${username}` : '登录或注册'}
        >
          {loggedIn && username ? (
            <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              {userAvatar ? (
                <img src={userAvatar} alt="" style={{ width: 24, height: 24, borderRadius: 6, objectFit: 'cover' }} />
              ) : (
                <Icon name="btn-user" size={16} />
              )}
              {username}
            </span>
          ) : (
            '登录 / 注册'
          )}
        </button>
      ) : (
        /* 标准 header：显示设置工具栏 */
        <span style={{ display: 'flex', gap: 0, flexShrink: 0 }}>
          <button
            className="settings-btn"
            onClick={onToggleMobileMode}
            title="手机版预览"
            aria-label={mobileMode ? '切换到桌面版' : '切换到手机版预览'}
          >
            <Icon name={mobileMode ? 'mode-desktop' : 'mode-mobile'} size={18} />
          </button>
          <button
            className="settings-btn"
            onClick={onToggleDarkMode}
            aria-label={darkMode ? '切换到亮色模式' : '切换到暗色模式'}
          >
            <Icon name={darkMode ? 'theme-light' : 'theme-dark'} size={18} />
          </button>
          <button
            className="settings-btn"
            onClick={() => navigate('/settings')}
            aria-label="设置"
          >
            <Icon name="btn-settings" size={18} />
          </button>
          <button
            className="settings-btn"
            onClick={() => navigate('/profile')}
            aria-label="个人中心"
          >
            <Icon name="btn-user" size={18} />
          </button>
        </span>
      )}
    </nav>
  );
}
