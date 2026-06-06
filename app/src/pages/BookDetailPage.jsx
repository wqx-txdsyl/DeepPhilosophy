/**
 * 书籍详情页 — 内嵌阅读器入口
 * 离线可用（内置数据兜底）
 */
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getBookById } from '../data';
import { getApiBase } from '../App';

function BookDetailPage() {
  const { bookId } = useParams();
  const navigate = useNavigate();
  const [book, setBook] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchBook();
  }, [bookId]);

  const fetchBook = async () => {
    try {
      const resp = await fetch(`${getApiBase()}/api/books/${bookId}`);
      if (resp.ok) {
        const data = await resp.json();
        setBook(data);
        setLoading(false);
        return;
      }
    } catch (e) {}
    const b = await getBookById(bookId);
    setBook(b);
    setLoading(false);
  };

  if (loading) return <div className="loading">加载中...</div>;
  if (!book) return <div className="loading">书籍未找到</div>;

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
            📦 {(book.file_size / 1024 / 1024).toFixed(1)} MB
          </div>
        )}
      </div>

      {isTxt ? (
        <div className="pending-notice">
          <p style={{ fontSize: 48 }}>📝</p>
          <p>该书籍尚未收录</p>
          <p style={{ fontSize: 13, color: 'var(--text-dim)', marginTop: 8 }}>
            《{book.title}》的文件正在筹备中，<br />
            当前仅有占位标记（.txt），敬请期待。
          </p>
        </div>
      ) : (
        <div style={{ marginTop: 16 }}>
          <button className="btn btn-primary btn-block" onClick={openReader}>
            📖 打开阅读
          </button>
          <p style={{ fontSize: 12, color: 'var(--text-dim)', marginTop: 8, textAlign: 'center' }}>
            文件类型: {book.file_type.toUpperCase()} · {(book.file_size / 1024 / 1024).toFixed(1)} MB
          </p>
          <p style={{ fontSize: 11, color: 'var(--text-dim)', marginTop: 4, textAlign: 'center' }}>
            💡 提示：在线阅读需要连接服务器
          </p>
        </div>
      )}
    </div>
  );
}

export default BookDetailPage;
