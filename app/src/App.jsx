/**
 * DeepPhilosophy - 哲学爱好者移动应用
 * 开发者: @txdsyl_
 * 四个分区: 书籍 | 谱图 | 问答 | 我的
 */
import { useEffect } from 'react';
import { BrowserRouter, Routes, Route, useNavigate, useLocation } from 'react-router-dom';
import { startAutoSave, stopAutoSave } from './data/userData';
import BooksPage from './pages/BooksPage';
import BookDetailPage from './pages/BookDetailPage';
import GenealogyPage from './pages/GenealogyPage';
import AuthorDetailPage from './pages/AuthorDetailPage';
import QAPage from './pages/QAPage';
import SettingsPage from './pages/SettingsPage';
import ReaderPage from './pages/ReaderPage';
import ProfilePage from './pages/ProfilePage';
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

  // Auto-save user data every 10 min
  useEffect(() => {
    startAutoSave();
    return () => stopAutoSave();
  }, []);

  const tabs = [
    { key: 'books', label: '📚', text: '书籍', path: '/books' },
    { key: 'genealogy', label: '🔗', text: '谱图', path: '/genealogy' },
    { key: 'qa', label: '💬', text: '问答', path: '/qa' },
    { key: 'profile', label: '👤', text: '我的', path: '/profile' },
  ];

  const getActiveTab = () => {
    const p = location.pathname;
    if (p.startsWith('/genealogy') || p.startsWith('/author')) return 'genealogy';
    if (p.startsWith('/qa')) return 'qa';
    if (p.startsWith('/profile')) return 'profile';
    return 'books';
  };

  const isReader = location.pathname.startsWith('/reader');
  const hideNav = isReader;
  const activeTab = getActiveTab();

  return (
    <>
      {!isReader && (
        <header className="app-header">
          <h1 className="app-title" onClick={() => navigate('/books')}>
            DeepPhilosophy
          </h1>
          <button className="settings-btn" onClick={() => navigate('/settings')}>⚙️</button>
        </header>
      )}

      <main className="app-main" style={isReader ? { paddingBottom: 0 } : undefined}>
        <Routes>
          <Route path="/" element={<BooksPage />} />
          <Route path="/books" element={<BooksPage />} />
          <Route path="/book/:bookId" element={<BookDetailPage />} />
          <Route path="/reader/:bookId" element={<ReaderPage />} />
          <Route path="/genealogy" element={<GenealogyPage />} />
          <Route path="/author/:authorName" element={<AuthorDetailPage />} />
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
