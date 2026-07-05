/**
 * DeepPhilosophy - 哲学爱好者移动应用
 * 开发者: @txdsyl_
 * 四个分区: 书籍 | 谱图 | 问答 | 我的
 */
import { useEffect, useRef, useState, lazy, Suspense } from 'react';
import { BrowserRouter, Routes, Route, useNavigate, useLocation, useNavigationType } from 'react-router-dom';
import { startAutoSave, stopAutoSave } from './data/userData';
import ErrorBoundary from './components/ErrorBoundary';
import Icon from './components/Icon';
// 首屏+常用页面（eager：小文件，即时响应）
import BooksPage from './pages/BooksPage';
import AuthorsPage from './pages/AuthorsPage';
import GenealogyPage from './pages/GenealogyPage';
import QAPage from './pages/QAPage';
import HomePage from './pages/HomePage';
import SettingsPage from './pages/SettingsPage';       // 3.5KB, 常用
import ProfilePage from './pages/ProfilePage';         // 9KB, 常用
// 中型页面（lazy：点击才加载）
const BookDetailPage = lazy(() => import('./pages/BookDetailPage'));
const AuthorDetailPage = lazy(() => import('./pages/AuthorDetailPage'));
const SchoolDetailPage = lazy(() => import('./pages/SchoolDetailPage'));
const DeveloperPage = lazy(() => import('./pages/DeveloperPage'));
const ProfileEditPage = lazy(() => import('./pages/ProfileEditPage'));
const GamesPage = lazy(() => import('./pages/GamesPage'));
const WorldPhilosophiesPage = lazy(() => import('./pages/WorldPhilosophiesPage'));
const WesternPhilosophiesPage = lazy(() => import('./pages/WesternPhilosophiesPage'));
const EasternPhilosophiesPage = lazy(() => import('./pages/EasternPhilosophiesPage'));
// 重型页面（lazy：PDF/EPUB reader + 游戏）
const ReaderPage = lazy(() => import('./pages/ReaderPage'));
const AnswerBookPage = lazy(() => import('./pages/AnswerBookPage'));
const PHTIPage = lazy(() => import('./pages/PHTIPage'));
const PHTISillyPage = lazy(() => import('./pages/PHTISillyPage'));
import './App.css';

// 懒加载后 Loading 占位
const PageLoader = () => (
  <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '60vh', color: 'var(--ink-muted)' }}>
    加载中...
  </div>
);

export function getApiBase() {
  try {
    const config = JSON.parse(localStorage.getItem('dp_api_config') || '{}');
    // If user set a custom URL, use it (for local dev pointing to remote)
    if (config.apiUrl && config.apiUrl !== window.location.origin) return config.apiUrl;
  } catch (e) { console.error('Failed to parse dp_api_config:', e); }
  // Same-origin deployment: use relative URL (no CORS issues)
  if (import.meta.env.PROD) return '';
  return import.meta.env.VITE_API_URL || 'http://localhost:8000';
}

const scrollMemory = new Map();

function ScrollToTop() {
  const { pathname } = useLocation();
  const navType = useNavigationType();

  useEffect(() => {
    if (navType === 'POP') {
      // Back/forward: restore saved position
      const y = scrollMemory.get(pathname) || 0;
      window.scrollTo(0, y);
    } else {
      // New navigation or refresh: save current then scroll top
      scrollMemory.set(pathname, 0);
      window.scrollTo(0, 0);
    }
  }, [pathname]); // eslint-disable-line

  // Save scroll position on scroll
  useEffect(() => {
    const save = () => scrollMemory.set(pathname, window.scrollY);
    window.addEventListener('scroll', save, { passive: true });
    return () => window.removeEventListener('scroll', save);
  }, [pathname]);

  return null;
}

function App() {
  return (
    <BrowserRouter>
      <ScrollToTop />
      <div className="app-container">
        <MainLayout />
      </div>
    </BrowserRouter>
  );
}

function MainLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  const [darkMode, setDarkMode] = useState(() => localStorage.getItem('dp_dark_mode') === '1');
  const [mobileMode, setMobileMode] = useState(() => localStorage.getItem('dp_mobile_mode') === '1');

  // Auto-save
  useEffect(() => { startAutoSave(); return () => stopAutoSave(); }, []);
  useEffect(() => { if (darkMode) document.documentElement.classList.add('dark-mode'); else document.documentElement.classList.remove('dark-mode'); }, [darkMode]);
  useEffect(() => { if (mobileMode) document.documentElement.classList.add('mobile-mode'); else document.documentElement.classList.remove('mobile-mode'); }, [mobileMode]);
  useEffect(() => { window.scrollTo(0, 0); const m = document.querySelector('.app-main'); if (m) m.style.transform = 'translateY(0)'; }, [location.pathname]);

  // Candlelight cursor glow
  const glowRef = useRef(null);
  useEffect(() => {
    const el = document.createElement('div');
    el.className = 'candle-glow';
    document.body.appendChild(el);
    glowRef.current = el;
    const onMove = (e) => { el.style.left = e.clientX + 'px'; el.style.top = e.clientY + 'px'; el.style.opacity = '1'; };
    const onLeave = () => { el.style.opacity = '0'; };
    window.addEventListener('mousemove', onMove);
    document.addEventListener('mouseleave', onLeave);
    return () => { window.removeEventListener('mousemove', onMove); document.removeEventListener('mouseleave', onLeave); el.remove(); };
  }, []);

  // Parallax slow scroll (homepage only)
  useEffect(() => {
    if (location.pathname !== '/') return;
    let ticking = false;
    const onScroll = () => {
      if (!ticking) {
        requestAnimationFrame(() => {
          const scrollY = window.scrollY;
          const main = document.querySelector('.app-main');
          if (main) main.style.transform = `translateY(${scrollY * 0.3}px)`;
          ticking = false;
        });
        ticking = true;
      }
    };
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => { window.removeEventListener('scroll', onScroll); };
  }, [location.pathname]);

  const tabs = [
    { key: 'books', label: <Icon name="nav-books" size={16} />, text: '书籍', path: '/books' },
    { key: 'authors', label: <Icon name="nav-authors" size={16} />, text: '哲人', path: '/authors' },
    { key: 'genealogy', label: <Icon name="nav-genealogy" size={16} />, text: '谱系', path: '/genealogy' },
    { key: 'qa', label: <Icon name="nav-qa" size={16} />, text: '问答', path: '/qa' },
    { key: 'games', label: <Icon name="nav-games" size={16} />, text: '游戏', path: '/games' },
  ];

  const getActiveTab = () => {
    const p = location.pathname;
    if (p.startsWith('/authors') || p.startsWith('/author')) return 'authors';
    if (p.startsWith('/genealogy')) return 'genealogy';
    if (p.startsWith('/qa')) return 'qa';
    if (p.startsWith('/games')) return 'games';
    if (p.startsWith('/profile')) return 'profile';
    if (p === '/' || p.startsWith('/school')) return 'genealogy';
    return 'books';
  };

  const isReader = location.pathname.startsWith('/reader');
  const isHome = location.pathname === '/';
  const isSchool = location.pathname.startsWith('/school/');
  const isQA = location.pathname.startsWith('/qa');
  const hideHeader = isHome || isReader || isSchool;
  const activeTab = getActiveTab();

  return (
    <>
      {!hideHeader && (
        <header className="app-header">
          <h1 className="app-title" onClick={() => navigate('/')} style={{ marginRight: 4 }}>
            DeepPhilosophy
          </h1>
          <span style={{ display: 'flex', gap: 0, marginRight: 'auto', marginLeft: -2 }}>
            {tabs.map((tab) => (
              <button key={tab.key} className={`nav-btn ${activeTab === tab.key ? 'active' : ''}`}
                onClick={() => navigate(tab.path)}
                style={{ flexDirection: 'row', gap: 3, fontSize: 12, padding: '4px 8px' }}>
                {tab.label}
                <span>{tab.text}</span>
              </button>
            ))}
          </span>
          <span style={{ display: 'flex', gap: 0, flexShrink: 0 }}>
            <button className="settings-btn" onClick={() => { setMobileMode(!mobileMode); localStorage.setItem('dp_mobile_mode', !mobileMode ? '1' : '0'); }} title="手机版"><Icon name={mobileMode ? 'mode-desktop' : 'mode-mobile'} size={18} /></button>
            <button className="settings-btn" onClick={() => { setDarkMode(!darkMode); localStorage.setItem('dp_dark_mode', !darkMode ? '1' : '0'); }}><Icon name={darkMode ? 'theme-light' : 'theme-dark'} size={18} /></button>
            <button className="settings-btn" onClick={() => navigate('/settings')}><Icon name="btn-settings" size={18} /></button>
            <button className="settings-btn" onClick={() => navigate('/profile')}><Icon name="btn-user" size={18} /></button>
          </span>
        </header>
      )}

      <main className={`app-main${isReader || isHome || isSchool ? ' reader-mode' : ''}${isQA ? ' qa-mode' : ''}`} style={(isReader || isHome || isSchool || isQA) ? { padding: 0, minHeight: 'auto', transform: 'none' } : undefined}>
        <ErrorBoundary>
        <Suspense fallback={<PageLoader />}>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/books" element={<BooksPage />} />
          <Route path="/book/:bookId" element={<BookDetailPage />} />
          <Route path="/reader/:bookId" element={<ReaderPage />} />
          <Route path="/authors" element={<AuthorsPage />} />
          <Route path="/author/:authorName" element={<AuthorDetailPage />} />
          <Route path="/genealogy" element={<GenealogyPage />} />
          <Route path="/school/:name" element={<SchoolDetailPage />} />
          <Route path="/world-philosophies" element={<WorldPhilosophiesPage />} />
          <Route path="/western-philosophies" element={<WesternPhilosophiesPage />} />
          <Route path="/eastern-philosophies" element={<EasternPhilosophiesPage />} />
          <Route path="/qa" element={<QAPage />} />
          <Route path="/games" element={<GamesPage />} />
          <Route path="/games/answer-book" element={<AnswerBookPage />} />
          <Route path="/games/phti" element={<PHTIPage />} />
          <Route path="/games/phti-silly" element={<PHTISillyPage />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="/DEVELOPER_IS_TXDSYL" element={<DeveloperPage />} />
          <Route path="/profile" element={<ProfilePage />} />
          <Route path="/profile/edit" element={<ProfileEditPage />} />
        </Routes>
        </Suspense>
        </ErrorBoundary>
      </main>

    </>
  );
}

export default App;
