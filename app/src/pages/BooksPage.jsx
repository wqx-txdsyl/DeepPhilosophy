/**
 * 书籍分区 —— 按东方/西方 → 作者层级浏览
 * 支持分类标签筛选、搜索、摘要预览
 */
import { useState, useEffect, useRef } from 'react';

function FadeCard({ children, style }) {
  const ref = useRef(null);
  const [visible, setVisible] = useState(false);
  useEffect(() => {
    const el = ref.current; if (!el) return;
    const obs = new IntersectionObserver(([e]) => setVisible(e.isIntersecting), { threshold:0.1, rootMargin:'-30px 0px' });
    obs.observe(el);
    return () => obs.disconnect();
  }, []);
  return (
    <div ref={ref} style={{ opacity:visible?1:0, transform:visible?'translateY(0)':'translateY(20px)',
      transition:'opacity 0.55s ease, transform 0.55s ease', ...style }}>{children}</div>
  );
}
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
  const [showAllTags, setShowAllTags] = useState(false);
  const navigate = useNavigate();

  useEffect(() => { fetchBooks(); }, []);

  const fetchBooks = async () => {
    try {
      // 尝试从服务器获取（带标签），1.5s超时快速fallback
      const resp = await fetch(`${getApiBase()}/api/books`, {
        signal: AbortSignal.timeout(1500),
      });
      if (resp.ok) {
        const data = await resp.json();
        setBooks(data.books || []);
        setAllTags(data.tags || []);
      } else throw new Error('Server error');
    } catch (e) {
      console.error('Books API unavailable, using local data:', e.message);
      const data = await loadBooks();
      setBooks(data);
      const tags = new Set();
      data.forEach(b => (b.tags || []).forEach(t => tags.add(t)));
      setAllTags([...tags].sort());
    } finally {
      setLoading(false);
    }
  };

  // Tag normalization
  const normMap = {
    '古希腊哲学':'古希腊哲学','柏拉图主义':'古希腊哲学','亚里士多德主义':'古希腊哲学',
    '伊壁鸠鲁学派':'古希腊哲学','斯多葛学派':'斯多葛学派','斯多葛主义':'斯多葛学派',
    '存在主义':'存在主义','存在哲学':'存在主义','荒诞哲学':'存在主义',
    '德国古典哲学':'德国古典哲学','德国唯心论':'德国古典哲学','德国哲学':'德国古典哲学',
    '分析哲学':'分析哲学','语言哲学':'分析哲学','逻辑哲学':'分析哲学',
    '现象学':'现象学','欧陆哲学':'现象学','意识哲学':'现象学',
    '西方马克思主义':'西方马克思主义','马克思主义哲学':'西方马克思主义','批判理论':'西方马克思主义','法兰克福学派':'西方马克思主义',
    '法国哲学':'法国哲学','当代法国哲学':'法国哲学',
  };
  const normalize = (t) => normMap[t] || t;

  // Dedup + normalize tags from all books
  const normalizedTags = [...new Set(allTags.map(normalize))].sort();

  // 筛选
  const filtered = books.filter(b => {
    if (activeTag && !(b.tags || []).some(t => normalize(t) === activeTag)) return false;
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
      {/* 统计 */}
      <div style={{ fontSize: 13, color: 'var(--text-dim)', marginBottom: 10 }}>
        📚 共 {books.length} 本书，{Object.keys(grouped).reduce((s, r) => s + Object.keys(grouped[r]).filter(a => a !== '合集&概述').length, 0)} 位作者
      </div>

      {/* 搜索 */}
      <input
        className="search-box"
        placeholder="🔍 搜索书名或作者..."
        value={search}
        onChange={e => setSearch(e.target.value)}
      />

      {/* 分类标签 */}
      {normalizedTags.length > 0 && (
        <div style={{ marginBottom: 14 }}>
          <div style={{ fontSize: 12, color: 'var(--text-dim)', marginBottom: 8 }}>
            标签 ({normalizedTags.length})
            {normalizedTags.length > 20 && (
              <span onClick={() => setShowAllTags(!showAllTags)} style={{ cursor: 'pointer', color: 'var(--ochre)', marginLeft: 8 }}>
                {showAllTags ? '收起' : '展开全部'}
              </span>
            )}
          </div>
          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
            <button
              onClick={() => setActiveTag(null)}
              style={{
                background: !activeTag ? 'var(--ink)' : 'transparent',
                color: !activeTag ? 'var(--bone)' : 'var(--text-dim)',
                border: '1px solid var(--border)',
                borderRadius: 4, padding: '4px 14px',
                fontSize: 12, cursor: 'pointer', fontWeight: !activeTag ? 600 : 400,
                fontFamily: 'inherit',
              }}>
              全部
            </button>
            {(showAllTags ? normalizedTags : normalizedTags.slice(0, 20)).map(tag => (
              <button key={tag}
                onClick={() => setActiveTag(activeTag === tag ? null : tag)}
                style={{
                  background: activeTag === tag ? 'var(--ink)' : 'transparent',
                  color: activeTag === tag ? 'var(--bone)' : 'var(--text-dim)',
                  border: activeTag === tag ? '1px solid var(--ink)' : '1px solid var(--border)',
                  borderRadius: 4, padding: '4px 14px',
                  fontSize: 12, cursor: 'pointer', fontWeight: activeTag === tag ? 600 : 400,
                  fontFamily: 'inherit',
                }}>
                {tag}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* 书籍列表（东方优先，区域内按时序） */}
      {Object.keys(grouped).sort((a, b) => {
        if (a === '东方') return -1;
        if (b === '东方') return 1;
        return a.localeCompare(b);
      }).map(region => (
        <div key={region}>
          <h2 className="section-title">
            {region === '东方' ? '🏯' : '🏛️'} {region}哲学
          </h2>
          {Object.keys(grouped[region]).map(author => {
            const authorBooks = grouped[region][author];
            const isExpanded = expandedAuthor === `${region}-${author}`;
            return (
              <FadeCard key={author} style={{ marginBottom: 6 }}>
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
                  <FadeCard key={book.id}>
                  <div
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
                  </FadeCard>
                ))}
              </FadeCard>
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
