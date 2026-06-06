/**
 * 谱图分区 —— 作者列表、多维筛选（区域/年代/国家/流派）、人物关系图
 * 过滤"合集&概述"等非人物条目
 */
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getApiBase } from '../App';
import { loadAuthors } from '../data';

function GenealogyPage() {
  const [authors, setAuthors] = useState([]);
  const [filters, setFilters] = useState({});
  const [loading, setLoading] = useState(true);
  const [region, setRegion] = useState('all');
  const [schoolFilter, setSchoolFilter] = useState(null);
  const [search, setSearch] = useState('');
  const navigate = useNavigate();

  useEffect(() => { fetchData(); }, []);

  const fetchData = async () => {
    try {
      // 获取作者列表
      const resp = await fetch(`${getApiBase()}/api/authors`);
      if (resp.ok) {
        const data = await resp.json();
        setAuthors(data.authors || []);
      } else throw new Error('Server error');
      // 获取筛选选项
      const fresp = await fetch(`${getApiBase()}/api/authors/filters`);
      if (fresp.ok) {
        setFilters(await fresp.json());
      }
    } catch (e) {
      const data = await loadAuthors();
      // 本地模式：过滤合集
      setAuthors(data.filter(a => !a.name.includes('合集&概述') && !a.name.includes('合集')));
    } finally {
      setLoading(false);
    }
  };

  // 过滤作者
  const filtered = authors.filter(a => {
    if (region === 'east' && a.region !== '东方') return false;
    if (region === 'west' && a.region !== '西方') return false;
    if (schoolFilter && !(a.school || '').includes(schoolFilter)) return false;
    if (search) {
      const q = search.toLowerCase();
      return a.name.toLowerCase().includes(q) ||
             a.books.some(b => b.toLowerCase().includes(q));
    }
    return true;
  });

  // 收集所有流派用于筛选按钮
  const allSchools = new Set();
  filtered.forEach(a => { if (a.school) allSchools.add(a.school); });

  if (loading) return <div className="loading">加载中...</div>;

  return (
    <div className="page-container">
      {/* 搜索 */}
      <input
        className="search-box"
        placeholder="🔍 搜索作者..."
        value={search}
        onChange={e => setSearch(e.target.value)}
      />

      {/* 区域筛选 */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 10 }}>
        {[
          { key: 'all', label: '全部' },
          { key: 'east', label: '🏯 东方' },
          { key: 'west', label: '🏛️ 西方' },
        ].map(opt => (
          <button key={opt.key}
            className={`btn ${region === opt.key ? 'btn-primary' : 'btn-secondary'}`}
            style={{ padding: '6px 14px', fontSize: 13 }}
            onClick={() => setRegion(opt.key)}>
            {opt.label}
          </button>
        ))}
      </div>

      {/* 流派筛选 */}
      {allSchools.size > 0 && (
        <div style={{ display: 'flex', gap: 6, marginBottom: 14, flexWrap: 'wrap' }}>
          {[...allSchools].sort().map(school => (
            <button key={school}
              style={{
                background: schoolFilter === school ? 'var(--accent)' : 'var(--secondary)',
                color: schoolFilter === school ? 'var(--primary)' : 'var(--text-dim)',
                border: 'none', borderRadius: 12, padding: '3px 10px',
                fontSize: 11, cursor: 'pointer', fontWeight: schoolFilter === school ? 600 : 400,
              }}
              onClick={() => setSchoolFilter(schoolFilter === school ? null : school)}>
              {school}
            </button>
          ))}
        </div>
      )}

      {/* 人物关系图（简化版） */}
      {filtered.length > 0 && (
        <div className="relationship-graph" style={{ height: 200, position: 'relative', overflow: 'hidden' }}>
          <div style={{ position: 'absolute', top: 8, left: 12, fontSize: 11, color: 'var(--text-dim)' }}>
            人物关系图 ({filtered.length}位)
          </div>
          {filtered.slice(0, 30).map((author, i) => {
            const cols = Math.min(5, Math.ceil(Math.sqrt(filtered.length)));
            const row = Math.floor(i / cols);
            const col = i % cols;
            const cellW = 100 / cols;
            const cellH = 160 / Math.ceil(filtered.length / cols);
            const x = cellW * col + cellW / 2;
            const y = 30 + cellH * row;
            return (
              <div key={author.name}
                style={{
                  position: 'absolute',
                  left: `${x}%`, top: `${y}px`,
                  transform: 'translate(-50%, -50%)',
                  padding: '4px 8px', borderRadius: 8,
                  fontSize: 10, fontWeight: 500, cursor: 'pointer',
                  whiteSpace: 'nowrap',
                  background: author.region === '东方' ? '#2d1b2e' : '#1b2d2e',
                  color: author.region === '东方' ? '#e8a0bf' : '#a0d8e8',
                  border: `1px solid ${author.region === '东方' ? '#e8a0bf' : '#a0d8e8'}`,
                  zIndex: 2,
                }}
                onClick={() => navigate(`/author/${encodeURIComponent(author.name)}`)}>
                {author.name}
              </div>
            );
          })}
        </div>
      )}

      {/* 作者列表 */}
      {filtered.map(author => (
        <div key={author.name} className="card"
          onClick={() => navigate(`/author/${encodeURIComponent(author.name)}`)}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div style={{ flex: 1 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                <span className="card-title">{author.name}</span>
                <span className={`badge ${author.region === '东方' ? 'badge-east' : 'badge-west'}`}
                  style={{ fontSize: 10 }}>
                  {author.region}
                </span>
              </div>
              {/* 人物信息碎片 */}
              <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 4 }}>
                {author.era && (
                  <span style={{ fontSize: 11, color: 'var(--text-dim)' }}>🕐 {author.era}</span>
                )}
                {author.country && (
                  <span style={{ fontSize: 11, color: 'var(--text-dim)' }}>🌍 {author.country}</span>
                )}
                {author.school && (
                  <span className="tag" style={{ fontSize: 10 }}>{author.school}</span>
                )}
              </div>
              <div className="card-subtitle">
                {author.book_count} 部作品
                {author.books?.slice(0, 3).map((b, i) => (
                  <span key={i} style={{ marginLeft: i === 0 ? 8 : 0 }}>
                    {i > 0 && '、'}{b}
                  </span>
                ))}
              </div>
            </div>
            <span style={{ color: 'var(--text-dim)', fontSize: 18, marginTop: 8 }}>→</span>
          </div>
        </div>
      ))}

      {filtered.length === 0 && (
        <div className="empty-state">
          <p style={{ fontSize: 40, marginBottom: 12 }}>🔗</p>
          <p>未找到匹配的作者</p>
        </div>
      )}
    </div>
  );
}

export default GenealogyPage;
