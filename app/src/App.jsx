/**
 * DeepPhilosophy - 哲学爱好者移动应用
 * 开发者: @txdsyl_
 * 四个分区: 书籍 | 谱图 | 问答 | 我的
 */
import { useEffect, useRef } from 'react';
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
import WorldPhilosophiesPage from './pages/WorldPhilosophiesPage';
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

  // Auto-save
  useEffect(() => { startAutoSave(); return () => stopAutoSave(); }, []);

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
    { key: 'profile', label: '👤', text: '我的', path: '/profile' },
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
  const hideNav = isReader;
  const activeTab = getActiveTab();

  return (
    <>
      {!isReader && (
        <header className="app-header">
          <h1 className="app-title" onClick={() => navigate('/genealogy')}>
            DeepPhilosophy
          </h1>
          <button className="settings-btn" onClick={() => navigate('/settings')}>⚙️</button>
        </header>
      )}

      <main className={`app-main${isReader ? ' reader-mode' : ''}`} style={isReader ? { padding: 0, minHeight: 'auto', transform: 'none' } : undefined}>
        <Routes>
          <Route path="/" element={<GenealogyPage />} />
          <Route path="/books" element={<BooksPage />} />
          <Route path="/book/:bookId" element={<BookDetailPage />} />
          <Route path="/reader/:bookId" element={<ReaderPage />} />
          <Route path="/authors" element={<AuthorsPage />} />
          <Route path="/author/:authorName" element={<AuthorDetailPage />} />
          <Route path="/genealogy" element={<GenealogyPage />} />
          <Route path="/school/:name" element={<SchoolDetailPage />} />
          <Route path="/world-philosophies" element={<WorldPhilosophiesPage />} />
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
