/**
 * 作者详情页 —— 人物信息卡片（年代/国家/流派/生平）、作品列表
 * 优先使用内置数据库，其次维基百科/百度百科
 */
import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Icon from '../components/Icon';
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
      return;
    }
    // 中文用户优先百度百科，回落 Wikipedia
    const baikeUrl = `https://baike.baidu.com/item/${encodeURIComponent(authorName)}`;
    const wikiUrl = `https://en.wikipedia.org/wiki/${encodeURIComponent(authorName)}`;
    const isZh = navigator.language?.startsWith('zh');
    window.open(isZh ? baikeUrl : wikiUrl, '_blank');
  };

  if (loading) return <div className="loading">加载中...</div>;
  if (!author) return (
    <div className="page-container">
      <button className="btn btn-secondary" onClick={() => navigate(-1)} style={{ marginBottom: 16 }}>← 返回</button>
      <div className="empty-state">
        <p style={{ fontSize: 40 }}><Icon name="icon-error" size={16} /></p>
        <p>作者信息未找到</p>
      </div>
    </div>
  );

  return (
    <div className="page-container">
      <button className="btn btn-secondary" onClick={() => navigate(-1)} style={{ marginBottom: 16 }}>← 返回</button>

      {/* 人物信息卡片 */}
      <div className="card" style={{ cursor: 'default' }}>
        {/* 姓名 */}
        <h2 style={{ fontSize: 24, fontWeight: 500, marginBottom: 16, fontFamily: '"Playfair Display","PingFang SC",serif', letterSpacing: '0.03em' }}>
          {author.name}
        </h2>

        {/* 标签 + 头像 横排 */}
        <div style={{ display: 'flex', gap: 20, marginBottom: 20, alignItems: 'flex-start', flexWrap: 'wrap' }}>
          {/* 左侧：标签 */}
          <div style={{ flex: 1, minWidth: 200, display: 'flex', flexDirection: 'column', gap: 8, justifyContent: 'center' }}>
            {/* 第一行：区域 + 年代 + 国家 + 流派 */}
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
              {(() => {
                const r = author.region || '未知';
                const display = r === '未知' ? (author.country && /中国/.test(author.country) ? '东方哲学' : '西方哲学') : (r + '哲学');
                const regionKey = display.startsWith('东方') ? '东方' : display.startsWith('世界') ? '世界' : '西方';
                return (
                <span style={{
                  background: regionKey === '东方' ? 'rgba(59,90,150,0.1)' : regionKey === '世界' ? 'rgba(90,138,90,0.1)' : 'rgba(145,118,71,0.1)',
                  color: regionKey === '东方' ? 'var(--prussian)' : regionKey === '世界' ? '#5A8A5A' : 'var(--ochre)',
                  padding: '4px 12px', borderRadius: 14, fontSize: 12, fontWeight: 500, whiteSpace: 'nowrap',
                  border: '1px solid ' + (regionKey === '东方' ? 'rgba(59,90,150,0.2)' : regionKey === '世界' ? 'rgba(90,138,90,0.2)' : 'rgba(145,118,71,0.2)'),
                }}>{display}</span>
                );
              })()}
              {author.era && (
                <span style={{
                  background: 'var(--ochre)', color: '#fff', padding: '4px 12px',
                  borderRadius: 14, fontSize: 12, fontWeight: 500, whiteSpace: 'nowrap',
                }}>{author.era}</span>
              )}
              {author.country && (
                <span style={{
                  background: 'var(--prussian)', color: '#fff', padding: '4px 12px',
                  borderRadius: 14, fontSize: 12, fontWeight: 500, whiteSpace: 'nowrap',
                }}>{author.country}</span>
              )}
              {author.school && author.school.split(/[/,，、]/).map((s, i) => (
                <span key={i} style={{
                  background: 'var(--secondary)', color: 'var(--ochre)', padding: '4px 12px',
                  borderRadius: 14, fontSize: 12, fontWeight: 500, border: '1px solid rgba(145,118,71,0.15)',
                  whiteSpace: 'nowrap',
                }}>{s.trim()}</span>
              ))}
            </div>
            {/* 第二行：著作数 */}
            {author.book_count > 0 && (
              <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                <span style={{
                  color: 'var(--text-dim)', fontSize: 12,
                  display: 'flex', alignItems: 'center', gap: 4,
                }}>
                  <Icon name="nav-books" size={14} />
                  {author.book_count} 部著作
                </span>
                {author.source && (
                  <span style={{ fontSize: 10, color: 'var(--text-dim)', opacity: 0.6 }}>
                    · 数据: {author.source === 'builtin_database' ? '内置库' : author.source === 'baidu_baike' ? '百度百科' : author.source === 'wikipedia' ? '维基百科' : '基础'}
                  </span>
                )}
              </div>
            )}
          </div>

          {/* 右侧：头像（长椭圆框） */}
          <div style={{
            flexShrink: 0,
            width: 140, height: 180,
            borderRadius: '70px / 90px',
            overflow: 'hidden',
            background: 'rgba(145,118,71,0.06)',
            border: '2px solid rgba(145,118,71,0.12)',
            boxShadow: '0 2px 12px rgba(0,0,0,0.06)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <img
              src={`/philosopher/${encodeURIComponent(author.name)}.jpg`}
              alt={author.name}
              style={{ width: '100%', height: '100%', objectFit: 'contain' }}
              onError={(e) => {
                e.currentTarget.style.display = 'none';
                e.currentTarget.parentElement.innerHTML = '<span style=\"font-size:40px;opacity:0.3\">?</span>';
              }}
            />
          </div>
        </div>

        {/* 生平简介 */}
        <div style={{ lineHeight: 1.9, fontSize: 14, color: 'var(--text)', whiteSpace: 'pre-line', clear: 'both' }}>
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
          <h3 className="section-title"><Icon name="nav-books" size={16} /> 作品 ({author.books.length})</h3>
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
                  <span style={{ color: 'var(--text-dim)', fontSize: 14 }}><Icon name="icon-book-open" size={16} /></span>
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
