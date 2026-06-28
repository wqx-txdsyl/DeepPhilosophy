/**
 * DeepPhilosophy - 哲学爱好者移动应用
 * 开发者: @txdsyl_
 * 四个分区: 书籍 | 谱图 | 问答 | 我的
 */
import { useEffect, useRef, useState } from 'react';
import { BrowserRouter, Routes, Route, useNavigate, useLocation } from 'react-router-dom';
import { startAutoSave, stopAutoSave } from './data/userData';
import BooksPage from './pages/BooksPage';
import BookDetailPage from './pages/BookDetailPage';
import AuthorsPage from './pages/AuthorsPage';
import AuthorDetailPage from './pages/AuthorDetailPage';
import GenealogyPage from './pages/GenealogyPage';
import SchoolDetailPage from './pages/SchoolDetailPage';
import QAPage from './pages/QAPage';
import SettingsPage from './pages/SettingsPage';
import ReaderPage from './pages/ReaderPage';
import ProfilePage from './pages/ProfilePage';
import HomePage from './pages/HomePage';
import WorldPhilosophiesPage from './pages/WorldPhilosophiesPage';
import WesternPhilosophiesPage from './pages/WesternPhilosophiesPage';
import EasternPhilosophiesPage from './pages/EasternPhilosophiesPage';
import './App.css';

export function getApiBase() {
  try {
    const config = JSON.parse(localStorage.getItem('dp_api_config') || '{}');
    if (config.apiUrl) return config.apiUrl;
  } catch {}
  return import.meta.env.VITE_API_URL || 'http://localhost:8000';
}

function App() {
  return (
    <BrowserRouter>
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

  // Parallax slow scroll
  useEffect(() => {
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
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  const tabs = [
    { key: 'books', label: '📚', text: '书籍', path: '/books' },
    { key: 'authors', label: '✒️', text: '作家', path: '/authors' },
    { key: 'genealogy', label: '🧬', text: '谱系', path: '/genealogy' },
    { key: 'qa', label: '💬', text: '问答', path: '/qa' },
  ];

  const getActiveTab = () => {
    const p = location.pathname;
    if (p.startsWith('/authors') || p.startsWith('/author')) return 'authors';
    if (p.startsWith('/genealogy')) return 'genealogy';
    if (p.startsWith('/qa')) return 'qa';
    if (p.startsWith('/profile')) return 'profile';
    if (p === '/' || p.startsWith('/genealogy') || p.startsWith('/school')) return 'genealogy';
    return 'books';
  };

  const isReader = location.pathname.startsWith('/reader');
  const isHome = location.pathname === '/';
  const isSchool = location.pathname.startsWith('/school/');
  const hideNav = isReader || isHome || isSchool;
  const hideHeader = isHome || isReader || isSchool;
  const activeTab = getActiveTab();

  return (
    <>
      {!hideHeader && (
        <header className="app-header">
          <h1 className="app-title" onClick={() => navigate('/')}>
            DeepPhilosophy
          </h1>
          <span style={{ display: 'flex', gap: 0 }}>
            <button className="settings-btn" onClick={() => { setMobileMode(!mobileMode); localStorage.setItem('dp_mobile_mode', !mobileMode ? '1' : '0'); }} title="手机版">{mobileMode ? '💻' : '📱'}</button>
            <button className="settings-btn" onClick={() => { setDarkMode(!darkMode); localStorage.setItem('dp_dark_mode', !darkMode ? '1' : '0'); }}>{darkMode ? '☀️' : '🌙'}</button>
            <button className="settings-btn" onClick={() => navigate('/settings')}>⚙️</button>
            <button className="settings-btn" onClick={() => navigate('/profile')}>👤</button>
          </span>
        </header>
      )}

      <main className={`app-main${isReader || isHome || isSchool ? ' reader-mode' : ''}`} style={isReader || isHome || isSchool ? { padding: 0, minHeight: 'auto', transform: 'none' } : undefined}>
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
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="/profile" element={<ProfilePage />} />
        </Routes>
      </main>

      {!hideNav && (
        <nav className="bottom-nav">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              className={`nav-btn ${activeTab === tab.key ? 'active' : ''}`}
              onClick={() => navigate(tab.path)}
            >
              <span className="nav-icon">{tab.label}</span>
              <span className="nav-label">{tab.text}</span>
            </button>
          ))}
        </nav>
      )}
    </>
  );
}

export default App;
