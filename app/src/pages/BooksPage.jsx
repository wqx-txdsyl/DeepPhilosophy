/**
 * 书籍分区 —— 按东方/西方 → 作者层级浏览
 * 支持分类标签筛选、搜索、摘要预览
 */
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getApiBase } from '../App';
import { loadBooks } from '../data';

function BooksPage() {
  const [books, setBooks] = useState([]);
  const [allTags, setAllTags] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [activeTag, setActiveTag] = useState(null);
  const [expandedAuthor, setExpandedAuthor] = useState(null);
  const [showSummary, setShowSummary] = useState(null);
  const navigate = useNavigate();

  useEffect(() => { fetchBooks(); }, []);

  const fetchBooks = async () => {
    try {
      // 尝试从服务器获取（带标签）
      const resp = await fetch(`${getApiBase()}/api/books`);
      if (resp.ok) {
        const data = await resp.json();
        setBooks(data.books || []);
        setAllTags(data.tags || []);
      } else throw new Error('Server error');
    } catch (e) {
      const data = await loadBooks();
      setBooks(data);
      // 本地模式提取标签
      const tags = new Set();
      data.forEach(b => (b.tags || []).forEach(t => tags.add(t)));
      setAllTags([...tags].sort());
    } finally {
      setLoading(false);
    }
  };

  // 筛选
  const filtered = books.filter(b => {
    if (activeTag && !(b.tags || []).includes(activeTag)) return false;
    if (search) {
      const q = search.toLowerCase();
      return b.title.toLowerCase().includes(q) ||
             b.author.toLowerCase().includes(q);
    }
    return true;
  });

  // 分组
  const grouped = {};
  filtered.forEach(b => {
    const region = b.region;
    const author = b.author;
    if (!grouped[region]) grouped[region] = {};
    if (!grouped[region][author]) grouped[region][author] = [];
    grouped[region][author].push(b);
  });

  if (loading) return <div className="loading">加载中...</div>;

  return (
    <div className="page-container">
      {/* 搜索 */}
      <input
        className="search-box"
        placeholder="🔍 搜索书名或作者..."
        value={search}
        onChange={e => setSearch(e.target.value)}
      />

      {/* 分类标签 */}
      {allTags.length > 0 && (
        <div style={{ display: 'flex', gap: 6, marginBottom: 14, flexWrap: 'wrap' }}>
          <button
            className={`tag ${!activeTag ? 'tag-active' : ''}`}
            style={{
              background: !activeTag ? 'var(--accent)' : 'var(--secondary)',
              color: !activeTag ? 'var(--primary)' : 'var(--text-dim)',
              border: 'none', borderRadius: 14, padding: '4px 12px',
              fontSize: 12, cursor: 'pointer', fontWeight: activeTag ? 400 : 600,
            }}
            onClick={() => setActiveTag(null)}>
            全部
          </button>
          {allTags.map(tag => (
            <button key={tag}
              style={{
                background: activeTag === tag ? 'var(--accent)' : 'var(--secondary)',
                color: activeTag === tag ? 'var(--primary)' : 'var(--text-dim)',
                border: 'none', borderRadius: 14, padding: '4px 12px',
                fontSize: 12, cursor: 'pointer', fontWeight: activeTag === tag ? 600 : 400,
              }}
              onClick={() => setActiveTag(activeTag === tag ? null : tag)}>
              {tag}
            </button>
          ))}
        </div>
      )}

      {/* 书籍列表 */}
      {Object.keys(grouped).sort().map(region => (
        <div key={region}>
          <h2 className="section-title">
            {region === '东方' ? '🏯' : '🏛️'} {region}哲学
          </h2>
          {Object.keys(grouped[region]).sort().map(author => {
            const authorBooks = grouped[region][author];
            const isExpanded = expandedAuthor === `${region}-${author}`;
            return (
              <div key={author} style={{ marginBottom: 6 }}>
                <div className="card"
                  style={{ marginBottom: isExpanded ? 4 : 8 }}
                  onClick={() => setExpandedAuthor(isExpanded ? null : `${region}-${author}`)}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span className="card-title">{author}</span>
                    <span style={{ fontSize: 12, color: 'var(--text-dim)' }}>
                      {authorBooks.length} 部 {isExpanded ? '▲' : '▼'}
                    </span>
                  </div>
                </div>
                {isExpanded && authorBooks.map(book => (
                  <div key={book.id}
                    className="card"
                    style={{ marginLeft: 16, padding: '10px 14px' }}
                    onClick={() => navigate(`/book/${book.id}`)}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span className="card-title" style={{ fontSize: 14 }}>{book.title}</span>
                      <span className={`badge ${book.status === 'pending' ? 'badge-pending' : 'badge-available'}`}>
                        {book.file_type.toUpperCase()}
                      </span>
                    </div>
                    {/* 标签 */}
                    {(book.tags || []).length > 0 && (
                      <div style={{ display: 'flex', gap: 4, marginTop: 4, flexWrap: 'wrap' }}>
                        {book.tags.map(t => (
                          <span key={t} className="tag" style={{ fontSize: 10, padding: '1px 6px' }}>{t}</span>
                        ))}
                      </div>
                    )}
                    {/* 摘要切换 */}
                    {showSummary === book.id ? (
                      <div className="summary-text" style={{ marginTop: 6, fontSize: 12, lineHeight: 1.5, color: 'var(--text-dim)' }}>
                        {book.summary || `${book.author}的著作。${book.file_type.toUpperCase()}格式，${(book.file_size / 1024 / 1024).toFixed(1)}MB。`}
                      </div>
                    ) : (
                      <div style={{ marginTop: 4, fontSize: 11, color: 'var(--accent)', cursor: 'pointer' }}
                        onClick={(e) => { e.stopPropagation(); setShowSummary(book.id); }}>
                        查看简介 →
                      </div>
                    )}
                  </div>
                ))}
              </div>
            );
          })}
        </div>
      ))}

      {filtered.length === 0 && (
        <div className="empty-state">
          <p style={{ fontSize: 40, marginBottom: 12 }}>📚</p>
          <p>未找到匹配的书籍</p>
        </div>
      )}
    </div>
  );
}

export default BooksPage;
