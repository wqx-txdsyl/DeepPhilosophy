/**
 * 书籍详情页 — 内嵌阅读器入口
 * 离线可用（内置数据兜底）
 */
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Icon from '../components/Icon';
import { getBookById } from '../data';
import { getApiBase } from '../App';
import { useSEO } from '../utils/seo';
import { cacheGet, cacheSet } from '../data/cache';

function BookDetailPage() {
  const { bookId } = useParams();
  const navigate = useNavigate();
  const [book, setBook] = useState(null);
  const [loading, setLoading] = useState(true);

  useSEO(book?.title || '书籍详情', book?.author ? `${book.author} · ${book.title}` : '哲学经典著作详情');

  useEffect(() => {
    fetchBook();
  }, [bookId]);

  const fetchBook = async () => {
    const ck = 'book_' + bookId;
    const cached = cacheGet(ck);
    if (cached) { setBook(cached); setLoading(false); return; }
    // 1. 优先本地 JSON（CDN 秒级加载）
    try {
      const resp = await fetch(`/books/data/${bookId}.json`);
      if (resp.ok) { const data = await resp.json(); cacheSet(ck, data); setBook(data); setLoading(false); return; }
    } catch {}
    // 2. 回退 Render API
    try {
      const resp = await fetch(`${getApiBase()}/api/books/${bookId}`, { signal: AbortSignal.timeout(10000) });
      if (resp.ok) { const data = await resp.json(); cacheSet(ck, data); setBook(data); setLoading(false); return; }
    } catch (e) { console.error('Book API unavailable:', e); }
    // 3. 本地兜底
    const b = await getBookById(bookId);
    if (b) cacheSet(ck, b);
    setBook(b);
    setLoading(false);
  };

  if (loading) return <div className="loading">加载中...</div>;
  if (!book) return (
    <div className="page-container" style={{ textAlign: 'center' }}>
      <button className="btn btn-secondary" onClick={() => navigate(-1)} style={{ marginBottom: 16 }}>← 返回</button>
      <div className="empty-state"><p><Icon name="nav-books" size={16} /></p><p>书籍未找到</p></div>
    </div>
  );

  const isTxt = book.file_type === 'txt';
  const regionBadge = book.region === '东方' ? 'badge-east' : 'badge-west';

  const openReader = () => {
    navigate(`/reader/${bookId}?type=${book.file_type}`);
  };

  return (
    <div className="page-container">
      <button className="btn btn-secondary" onClick={() => navigate(-1)}
        style={{ marginBottom: 16 }}>
        ← 返回
      </button>

      <div className="card" style={{ cursor: 'default' }}>
        <div style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
          <span className={`badge ${regionBadge}`}>{book.region}</span>
          <span className="badge badge-available">{book.file_type.toUpperCase()}</span>
          {isTxt && <span className="badge badge-pending">待收录</span>}
        </div>

        <h2 style={{ fontSize: 20, marginBottom: 4 }}>{book.title}</h2>
        <p className="card-subtitle" style={{ fontSize: 14, marginBottom: 8 }}>
          {book.author}
        </p>

        {book.file_size > 0 && (
          <div style={{ fontSize: 13, color: 'var(--text-dim)' }}>
            <Icon name="icon-file-size" size={16} /> {(book.file_size / 1024 / 1024).toFixed(1)} MB
          </div>
        )}
      </div>

      {/* Keywords */}
      {book.keywords && book.keywords.length > 0 && (
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginTop: 12 }}>
          {book.keywords.map((kw, i) => (
            <span key={i} className="tag" style={{
              fontSize: 12, padding: '4px 10px',
              background: 'var(--secondary)', color: 'var(--accent)',
              borderRadius: 12, border: '1px solid var(--border)',
            }}>
              {kw.word || kw}
            </span>
          ))}
        </div>
      )}

      {/* Summary */}
      {book.summary && (
        <div className="card" style={{ cursor: 'default', marginTop: 10 }}>
          <div style={{ fontSize: 13, color: 'var(--text-dim)', lineHeight: 1.7 }}>
            {book.summary}
          </div>
        </div>
      )}

      {isTxt ? (
        <div className="pending-notice">
          <p style={{ fontSize: 48 }}><Icon name="icon-edit" size={16} /></p>
          <p>该书籍尚未收录</p>
          <p style={{ fontSize: 13, color: 'var(--text-dim)', marginTop: 8 }}>
            《{book.title}》的文件正在筹备中，<br />
            当前仅有占位标记（.txt），敬请期待。
          </p>
        </div>
      ) : (
        <div style={{ marginTop: 16 }}>
          <button className="btn btn-primary btn-block" onClick={openReader}>
            <Icon name="icon-book-open" size={16} /> 打开阅读
          </button>
          <p style={{ fontSize: 12, color: 'var(--text-dim)', marginTop: 8, textAlign: 'center' }}>
            文件类型: {book.file_type.toUpperCase()} · {(book.file_size / 1024 / 1024).toFixed(1)} MB
          </p>
          <p style={{ fontSize: 11, color: 'var(--text-dim)', marginTop: 4, textAlign: 'center' }}>
            <Icon name="icon-tip" size={16} /> 提示：在线阅读需要连接服务器
          </p>
        </div>
      )}
    </div>
  );
}

export default BookDetailPage;
