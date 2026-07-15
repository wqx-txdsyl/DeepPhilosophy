/**
 * DeepPhilosophy - 哲学爱好者移动应用
 * 开发者: @txdsyl_
 * 四个分区: 书籍 | 谱图 | 问答 | 我的
 */
import { useEffect, useRef, useState, lazy, Suspense } from 'react';
import { BrowserRouter, Routes, Route, useNavigate, useLocation, useNavigationType } from 'react-router-dom';
import { startAutoSave, stopAutoSave } from './data/userData';
import { getApiBase } from './utils/api';
import ErrorBoundary from './components/ErrorBoundary';
import Icon from './components/Icon';
import NavBar from './components/NavBar';
import ScrollToTopButton from './components/ScrollToTop';
import ReadingProgress from './components/ReadingProgress';
import { ToastProvider } from './contexts/ToastContext';
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

// 懒加载骨架屏占位
const PageLoader = () => (
  <div style={{ padding: '24px 16px', maxWidth: 800, margin: '0 auto' }}>
    <div className="skeleton" style={{ width: '60%', height: 24, marginBottom: 16 }} />
    <div className="skeleton" style={{ width: '40%', height: 16, marginBottom: 24 }} />
    <div className="skeleton" style={{ width: '100%', height: 14, marginBottom: 10 }} />
    <div className="skeleton" style={{ width: '100%', height: 14, marginBottom: 10 }} />
    <div className="skeleton" style={{ width: '80%', height: 14, marginBottom: 10 }} />
    <div className="skeleton" style={{ width: '90%', height: 14, marginBottom: 10 }} />
    <div className="skeleton" style={{ width: '70%', height: 14 }} />
  </div>
);

export { getApiBase } from './utils/api';

const scrollMemory = new Map();
const MAX_SCROLL_ENTRIES = 30;

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
    const save = () => {
      scrollMemory.set(pathname, window.scrollY);
      // Prune old entries if exceeding limit
      if (scrollMemory.size > MAX_SCROLL_ENTRIES) {
        const keys = [...scrollMemory.keys()];
        for (let i = 0; i < keys.length - MAX_SCROLL_ENTRIES; i++) {
          scrollMemory.delete(keys[i]);
        }
      }
    };
    window.addEventListener('scroll', save, { passive: true });
    return () => window.removeEventListener('scroll', save);
  }, [pathname]);

  return null;
}

function App() {
  return (
    <ToastProvider>
    <BrowserRouter>
      <ScrollToTop />
      <div className="app-container">
        <MainLayout />
      </div>
    </BrowserRouter>
    </ToastProvider>
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

  const isReader = location.pathname.startsWith('/reader');
  const isHome = location.pathname === '/';
  const isSchool = location.pathname.startsWith('/school/');
  const isQA = location.pathname.startsWith('/qa');
  const hideHeader = isHome || isReader || isSchool;

  return (
    <>
      {/* 阅读进度条 */}
      <ReadingProgress />

      {/* 跳过导航，直达内容（可访问性） */}
      <a href="#main-content" className="skip-link">跳转到主要内容</a>

      <NavBar
        variant={hideHeader ? 'hidden' : 'sticky'}
        darkMode={darkMode}
        mobileMode={mobileMode}
        onToggleDarkMode={() => { setDarkMode(!darkMode); localStorage.setItem('dp_dark_mode', !darkMode ? '1' : '0'); }}
        onToggleMobileMode={() => { setMobileMode(!mobileMode); localStorage.setItem('dp_mobile_mode', !mobileMode ? '1' : '0'); }}
      />

      <main id="main-content" className={`app-main${isReader || isHome || isSchool ? ' reader-mode' : ''}${isQA ? ' qa-mode' : ''}`} style={(isReader || isHome || isSchool || isQA) ? { padding: 0, minHeight: 'auto', transform: 'none' } : undefined}>
        <ErrorBoundary>
        <Suspense fallback={<PageLoader />}>
        <div key={location.pathname} className="page-enter">
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
        </div>
        </Suspense>
        </ErrorBoundary>
      </main>

      {/* 返回顶部浮动按钮 */}
      <ScrollToTopButton />

    </>
  );
}

export default App;
