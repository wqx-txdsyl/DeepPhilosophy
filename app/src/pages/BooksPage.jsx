/**
 * 书籍分区 —— 按东方/西方 → 作者层级浏览
 * 支持分类标签筛选、搜索、摘要预览
 */
import { useState, useEffect, useRef, useMemo } from 'react';
import Icon from '../components/Icon';

function BookCover({ bookId }) {
  const [src, setSrc] = useState(null);
  useEffect(() => {
    fetch(`/book_detail/${bookId}.json`).then(r => r.ok && r.json()).then(d => {
      if (d?.cover) setSrc(d.cover);
    }).catch(() => {});
  }, [bookId]);
  if (!src) return <Icon name="nav-books" size={20} />;
  return <img src={src} alt="" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />;
}

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
import { getApiBase } from '../utils/api';
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
    // 1. 优先本地 JSON（CDN 秒级加载）
    try {
      const resp = await fetch('/books.json');
      if (resp.ok) {
        const books = await resp.json();
        setBooks(books);
        const tags = new Set();
        books.forEach(b => (b.tags || []).forEach(t => tags.add(t)));
        setAllTags([...tags].sort());
        setLoading(false);
        return;
      }
    } catch {}
    // 2. 回退 Render API
    try {
      const resp = await fetch(`${getApiBase()}/api/books`, { signal: AbortSignal.timeout(3000) });
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

  // 分组（memoized 避免每次渲染重算）
  const grouped = useMemo(() => {
    const g = {};
    filtered.forEach(b => {
      const region = b.region;
      const author = b.author;
      if (!g[region]) g[region] = {};
      if (!g[region][author]) g[region][author] = [];
      g[region][author].push(b);
    });
    return g;
  }, [filtered]);

  if (loading) return <div className="loading">加载中...</div>;

  return (
    <div className="page-container">
      {/* 统计 */}
      <div style={{ fontSize: 13, color: 'var(--text-dim)', marginBottom: 10 }}>
        <Icon name="nav-books" size={16} /> 共 {books.length} 本书，{Object.keys(grouped).reduce((s, r) => s + Object.keys(grouped[r]).filter(a => a !== '合集&概述').length, 0)} 位作者
      </div>

      {/* 搜索 */}
      <input
        className="search-box"
        placeholder="搜索书名或作者..."
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

      {/* 书籍列表 — 笔趣阁风格网格 */}
      {['东方', '西方'].filter(r => grouped[r]).map(region => (
        <div key={region} style={{ marginBottom: 32 }}>
          <h2 className="section-title" style={{ marginBottom: 16 }}>
            {region === '东方' ? <Icon name='region-east-pagoda' size={18} /> : <Icon name='region-west' size={18} />} {region}哲学
          </h2>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
            gap: 10,
          }}>
            {Object.keys(grouped[region]).sort().map(author => (
              Object.values(grouped[region][author]).flat().map(book => (
                <div key={book.id} className="card" style={{
                  padding: '12px 16px', cursor: 'pointer',
                  display: 'flex', gap: 12, alignItems: 'flex-start',
                }} onClick={() => navigate(`/book/${book.id}`)}>
                  {/* 封面缩略图 */}
                  <div style={{
                    width: 48, height: 64, flexShrink: 0,
                    borderRadius: 3, overflow: 'hidden',
                    background: 'var(--bg)', border: '1px solid var(--border)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                  }}>
                    <BookCover bookId={book.id} />
                  </div>
                  {/* 信息 */}
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: 14, fontWeight: 500, color: 'var(--ink)', fontFamily: 'var(--font-serif)', marginBottom: 2, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {book.title}
                    </div>
                    <div style={{ fontSize: 11, color: 'var(--text-dim)', marginBottom: 4 }}>{book.author}</div>
                    <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                      <span className={`badge ${book.file_type === 'txt' ? 'badge-pending' : 'badge-available'}`} style={{ fontSize: 9, padding: '1px 6px' }}>
                        {book.file_type?.toUpperCase()}
                      </span>
                      {(book.tags || []).slice(0, 2).map(t => (
                        <span key={t} className="tag" style={{ fontSize: 9, padding: '1px 6px' }}>{t}</span>
                      ))}
                    </div>
                  </div>
                </div>
              ))
            ))}
          </div>
        </div>
      ))}

      {filtered.length === 0 && (
        <div className="empty-state">
          <p style={{ fontSize: 40, marginBottom: 12 }}><Icon name="nav-books" size={16} /></p>
          <p>未找到匹配的书籍</p>
        </div>
      )}
    </div>
  );
}

export default BooksPage;
