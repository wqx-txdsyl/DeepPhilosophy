/**
 * 书籍详情页 — 封面 + 章节列表 + 阅读入口
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
  const [meta, setMeta] = useState(null);
  const [loading, setLoading] = useState(true);

  useSEO(book?.title || '书籍详情', book?.author ? `${book.author} · ${book.title}` : '哲学经典著作详情');

  useEffect(() => { fetchBook(); }, [bookId]);

  const fetchBook = async () => {
    // 秒开：直接从 OSS 加载预构建的轻量详情 JSON（1-30KB）
    try {
      const resp = await fetch(`${getApiBase()}/api/books/${bookId}/detail`);
      if (resp.ok) { const d = await resp.json(); setBook(d); setMeta(d); setLoading(false); return; }
    } catch {}
    // 回退
    const b = await getBookById(bookId);
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
  const openReader = () => navigate(`/reader/${bookId}?type=${book.file_type}`);
  const coverUrl = meta?.cover || null;
  const chapterTitles = meta?.chapterTitles || [];

  return (
    <div className="page-container" style={{ maxWidth: 800, margin: '0 auto', paddingBottom: 40 }}>
      <button className="btn btn-secondary" onClick={() => navigate(-1)} style={{ marginBottom: 20 }}>← 返回</button>

      {/* 封面 + 基本信息 */}
      <div style={{ display: 'flex', gap: 28, alignItems: 'flex-start', flexWrap: 'wrap', marginBottom: 28 }}>
        {/* 封面 */}
        <div style={{
          width: 160, height: 220, flexShrink: 0,
          borderRadius: 6, overflow: 'hidden',
          background: 'var(--card-bg)', border: '1px solid var(--border)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          {coverUrl ? (
            <img src={coverUrl} alt={book.title}
              style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
          ) : (
            <Icon name="nav-books" size={48} />
          )}
        </div>

        {/* 信息 */}
        <div style={{ flex: 1, minWidth: 240 }}>
          <div style={{ display: 'flex', gap: 8, marginBottom: 10 }}>
            <span className={`badge ${book.region === '东方' ? 'badge-east' : 'badge-west'}`}>{book.region}</span>
            <span className="badge badge-available">{book.file_type?.toUpperCase()}</span>
          </div>
          <h1 style={{
            fontFamily: 'var(--font-serif)', fontSize: 26, fontWeight: 400,
            color: 'var(--ink)', margin: '0 0 6px', letterSpacing: '0.03em',
          }}>{book.title}</h1>
          <p style={{ fontSize: 14, color: 'var(--text-dim)', margin: '0 0 12px' }}>
            {book.author}
          </p>
          {book.file_size > 0 && (
            <p style={{ fontSize: 12, color: 'var(--text-dim)', margin: 0 }}>
              {(book.file_size / 1024 / 1024).toFixed(1)} MB · {meta ? `${meta.estimatedPages || meta.chapterCount}页` : ''}
            </p>
          )}
          {!isTxt && (
            <button className="btn btn-primary" style={{ marginTop: 16, padding: '10px 28px', fontSize: 14 }}
              onClick={openReader}>
              <Icon name="icon-book-open" size={16} /> 开始阅读
            </button>
          )}
        </div>
      </div>

      {/* 简介 */}
      {book.summary && (
        <div style={{
          padding: '20px 0', borderTop: '1px solid var(--border)',
          fontSize: 14, color: 'var(--text-dim)', lineHeight: 1.9,
        }}>
          {book.summary}
        </div>
      )}

      {/* 章节目录 */}
      {chapterTitles.length > 0 && (
        <div style={{ marginTop: 24 }}>
          <h2 style={{
            fontFamily: 'var(--font-serif)', fontSize: 20, fontWeight: 400,
            color: 'var(--ink)', marginBottom: 16, letterSpacing: '0.03em',
          }}>目录</h2>
          <div style={{ borderTop: '1px solid var(--border)' }}>
            {chapterTitles.map((title, i) => (
              <div key={i} style={{
                display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                padding: '10px 0', borderBottom: '1px solid var(--border)',
                cursor: 'pointer', transition: 'background 0.2s',
                fontSize: 13, color: 'var(--text)',
              }} onClick={() => navigate(`/reader/${bookId}?type=${book.file_type}&ch=${i}`)}
                onMouseEnter={e => e.currentTarget.style.background = 'var(--card-bg)'}
                onMouseLeave={e => e.currentTarget.style.background = 'transparent'}>
                <span style={{ flex: 1 }}>{title}</span>
                <span style={{ color: 'var(--text-dim)', fontSize: 11 }}>→</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 待收录提示 */}
      {isTxt && (
        <div style={{ textAlign: 'center', padding: '40px 0', color: 'var(--text-dim)' }}>
          <p style={{ fontSize: 36, margin: 0 }}><Icon name="icon-edit" size={16} /></p>
          <p style={{ marginTop: 12 }}>该书籍尚未收录，正在筹备中</p>
        </div>
      )}
    </div>
  );
}

export default BookDetailPage;
