/**
 * 作者详情页 —— 人物信息卡片（年代/国家/流派/生平）、作品列表
 * 优先使用内置数据库，其次维基百科/百度百科
 */
import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getAuthorInfo } from '../data';
import { getApiBase } from '../App';

function AuthorDetailPage() {
  const { authorName } = useParams();
  const navigate = useNavigate();
  const [author, setAuthor] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => { fetchAuthor(); }, [authorName]);

  const fetchAuthor = async () => {
    try {
      // 尝试从服务器获取（含爬虫数据）
      const resp = await fetch(`${getApiBase()}/api/authors/${encodeURIComponent(authorName)}`);
      if (resp.ok) {
        setAuthor(await resp.json());
        setLoading(false);
        return;
      }
    } catch (e) { console.error('Author API unavailable:', e); }
    // 本地兜底
    const data = await getAuthorInfo(authorName);
    setAuthor(data);
    setLoading(false);
  };

  const openWiki = () => {
    if (author?.wiki_url) {
      window.open(author.wiki_url, '_blank');
    } else {
      window.open(`https://en.wikipedia.org/wiki/${encodeURIComponent(authorName)}`, '_blank');
    }
  };

  if (loading) return <div className="loading">加载中...</div>;
  if (!author) return (
    <div className="page-container">
      <button className="btn btn-secondary" onClick={() => navigate(-1)} style={{ marginBottom: 16 }}>← 返回</button>
      <div className="empty-state">
        <p style={{ fontSize: 40 }}>😞</p>
        <p>作者信息未找到</p>
      </div>
    </div>
  );

  return (
    <div className="page-container">
      <button className="btn btn-secondary" onClick={() => navigate(-1)} style={{ marginBottom: 16 }}>← 返回</button>

      {/* 人物信息卡片 */}
      <div className="card" style={{ cursor: 'default' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 }}>
          <div>
            <h2 style={{ fontSize: 22, marginBottom: 4 }}>{author.name}</h2>
            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
              <span className={`badge ${author.region === '东方' ? 'badge-east' : 'badge-west'}`}>
                {author.region}
              </span>
              {author.source && (
                <span className="badge badge-available" style={{ fontSize: 10 }}>
                  数据: {author.source === 'builtin_database' ? '内置库' :
                         author.source === 'baidu_baike' ? '百度百科' :
                         author.source === 'wikipedia' ? '维基百科' : '基础'}
                </span>
              )}
            </div>
          </div>
        </div>

        {/* 信息碎片 */}
        <div style={{
          display: 'grid', gridTemplateColumns: '1fr 1fr',
          gap: 8, marginBottom: 12,
        }}>
          {author.era && (
            <div style={{ background: 'var(--secondary)', padding: '8px 12px', borderRadius: 8 }}>
              <div style={{ fontSize: 10, color: 'var(--text-dim)', marginBottom: 2 }}>年代</div>
              <div style={{ fontSize: 13 }}>{author.era}</div>
            </div>
          )}
          {author.country && (
            <div style={{ background: 'var(--secondary)', padding: '8px 12px', borderRadius: 8 }}>
              <div style={{ fontSize: 10, color: 'var(--text-dim)', marginBottom: 2 }}>国家</div>
              <div style={{ fontSize: 13 }}>{author.country}</div>
            </div>
          )}
          {author.school && (
            <div style={{ background: 'var(--secondary)', padding: '8px 12px', borderRadius: 8 }}>
              <div style={{ fontSize: 10, color: 'var(--text-dim)', marginBottom: 2 }}>思想流派</div>
              <div style={{ fontSize: 13 }}>{author.school}</div>
            </div>
          )}
          {author.book_count > 0 && (
            <div style={{ background: 'var(--secondary)', padding: '8px 12px', borderRadius: 8 }}>
              <div style={{ fontSize: 10, color: 'var(--text-dim)', marginBottom: 2 }}>收录作品</div>
              <div style={{ fontSize: 13 }}>{author.book_count} 部</div>
            </div>
          )}
        </div>

        {/* 生平简介 */}
        <div style={{ lineHeight: 1.9, fontSize: 14, color: 'var(--text)', whiteSpace: 'pre-line' }}>
          {typeof author.bio === 'string' ? author.bio.replace(/\\n/g, '\n') : author.bio}
        </div>

        <div style={{ marginTop: 14, display: 'flex', gap: 8 }}>
          <button className="btn btn-secondary" onClick={openWiki} style={{ padding: '8px 16px', fontSize: 13 }}>
            维基百科
          </button>
          <button className="btn btn-secondary" style={{ padding: '8px 16px', fontSize: 13 }}
            onClick={() => window.open(`https://baike.baidu.com/item/${encodeURIComponent(authorName)}`, '_blank')}>
            百度百科
          </button>
        </div>
      </div>

      {/* 作品列表 */}
      {author.books && author.books.length > 0 && (
        <>
          <h3 className="section-title">📚 作品 ({author.books.length})</h3>
          {author.books.map((book, i) => {
            const bookTitle = typeof book === 'string' ? book : book.title;
            const bookId = typeof book === 'string' ? null : book.id;
            return (
              <div key={i} className="card" style={{ padding: '10px 14px' }}
                onClick={() => {
                  if (bookId) {
                    navigate(`/reader/${bookId}?type=${book.file_type}`);
                  }
                }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span className="card-title" style={{ fontSize: 14 }}>
                    {bookTitle}
                  </span>
                  {book.file_type && (
                    <span className={`badge ${book.file_type === 'txt' ? 'badge-pending' : 'badge-available'}`}
                      style={{ fontSize: 10 }}>
                      {book.file_type.toUpperCase()}
                    </span>
                  )}
                  <span style={{ color: 'var(--text-dim)', fontSize: 14 }}>📖</span>
                </div>
              </div>
            );
          })}
        </>
      )}
    </div>
  );
}

export default AuthorDetailPage;
