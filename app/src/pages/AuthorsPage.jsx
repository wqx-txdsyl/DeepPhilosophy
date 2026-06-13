/**
 * 作家页面 —— 东西方哲学家按时间排序，显示年代/国家/流派/简介/作品
 * 离线可用（内置数据库兜底）
 */
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getApiBase } from '../App';

function AuthorsPage() {
  const navigate = useNavigate();
  const [authors, setAuthors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');
  const [activeTags, setActiveTags] = useState([]);
  const [filters, setFilters] = useState({ eras: [], countries: [], schools: [] });
  const [showAllTags, setShowAllTags] = useState(false);
  const [search, setSearch] = useState('');

  // Tag normalization map (mirrors backend _normalize_tag)
  const normMap = {
    "存在主义先驱":"存在主义","存在哲学":"存在主义","文学哲学":"存在主义",
    "柏拉图主义":"古希腊哲学","逍遥学派":"古希腊哲学","伊壁鸠鲁主义":"古希腊哲学",
    "米利都学派":"古希腊哲学","埃利亚派":"古希腊哲学","前苏格拉底":"古希腊哲学",
    "古代哲学":"古希腊哲学","犬儒学派":"古希腊哲学","自然哲学":"古希腊哲学",
    "新柏拉图主义":"古希腊哲学","折衷主义":"古希腊哲学","元素论":"古希腊哲学",
    "斯多葛派":"斯多葛学派","斯多葛主义":"斯多葛学派","晚期斯多亚":"斯多葛学派",
    "批判哲学":"德国古典哲学","德国唯心论":"德国古典哲学","唯意志论":"德国古典哲学",
    "交往理论":"法兰克福学派","文化批评":"法兰克福学派","法兰克福学派（批判理论）":"法兰克福学派",
    "结构马克思主义":"马克思主义","政治经济学":"政治哲学","宗教社会学":"社会学",
    "现实主义政治哲学":"政治哲学","文艺复兴人文主义":"启蒙运动","逻辑实证主义":"实证主义",
    "启蒙哲学":"启蒙运动","启蒙思想":"启蒙运动","苏格兰启蒙":"启蒙运动","人文主义":"启蒙运动",
    "精神分析":"精神分析学","分析心理学":"精神分析学","心理治疗":"精神分析学",
    "逻辑原子主义":"分析哲学","逻辑实用主义":"分析哲学","逻辑实证":"分析哲学",
    "日常语言":"分析哲学","语言哲学":"分析哲学",
    "形式社会学":"社会学","社会心理学":"社会学","群体心理学":"社会学","社会达尔文":"社会学",
    "激进平等":"政治哲学","责任伦理":"政治哲学","社会契约论":"政治哲学","古典经济学":"政治哲学",
    "德性伦理":"伦理学","批判理性主义":"科学哲学",
    "解释学":"现象学","身体哲学":"现象学","意向性":"现象学",
    "常识实在论":"实在论","人本唯物论":"实在论","机械唯物主义":"实在论",
    "结构语言学":"结构主义","进步教育":"实用主义","新实用主义":"实用主义",
    "荒诞文学":"荒诞哲学","浪漫主义先驱":"浪漫主义",
    "近代哲学之父":"近代哲学","有机体哲学":"过程哲学",
    "后现代哲学":"后现代主义","解构主义":"后现代主义",
    "宗教社会学":"社会学","政治经济学":"政治哲学","现实主义政治哲学":"政治哲学",
    "文艺复兴人文主义":"启蒙运动","逻辑实证主义":"实证主义",
    "绝对唯心主义":"唯心主义","历史唯物主义":"马克思主义","结构马克思主义":"马克思主义",
  };
  const expandMap = {
    "结构马克思主义":["马克思主义","结构主义"],
    "政治经济学":["政治哲学","社会学"],
    "宗教社会学":["社会学","宗教哲学"],
    "逻辑实证主义":["实证主义","分析哲学"],
    "绝对唯心主义":["唯心主义"],
    "历史唯物主义":["马克思主义"],
    "后现代哲学":["后现代主义"],
    "解构主义":["后现代主义"],
    "现实主义政治哲学":["政治哲学"],
    "文艺复兴人文主义":["启蒙运动"],
  };
  const cntMap = {"苏格兰":"英国","英格兰":"英国","罗马帝国":"古罗马","北非":"古罗马","奥匈帝国（捷克）":"捷克","俄国":"俄罗斯"};

  const toggleTag = (tag) => {
    setActiveTags(prev =>
      prev.includes(tag) ? prev.filter(t => t !== tag) : [...prev, tag]
    );
  };

  // Load all authors once on mount
  const [allAuthors, setAllAuthors] = useState([]);
  useEffect(() => {
    loadAllAuthors();
    loadFilters();
  }, []);

  const loadAllAuthors = async () => {
    setLoading(true);
    try {
      const resp = await fetch(`${getApiBase()}/api/authors`, { signal: AbortSignal.timeout(5000) });
      if (resp.ok) {
        const data = await resp.json();
        setAllAuthors(data.authors || []);
      }
    } catch (e) {}
    setLoading(false);
  };

  useEffect(() => {
    loadFilters();
  }, []);

  // Client-side filtering (instant, no reload)
  let filtered = allAuthors;
  if (search) {
    const q = search.toLowerCase();
    filtered = filtered.filter(a =>
      a.name.toLowerCase().includes(q) || (a.country||'').toLowerCase().includes(q) || (a.school||'').toLowerCase().includes(q)
    );
  }
  if (filter === 'east') filtered = filtered.filter(a => a.region === '东方');
  else if (filter === 'west') filtered = filtered.filter(a => a.region === '西方');
  // Multi-tag filter (client-side, mirrored normalization)
  for (const tag of activeTags) {
    filtered = filtered.filter(a => {
      const rawSchool = a.school || '';
      const schools = rawSchool.split(/[/,、，;；]/).map(s => s.trim());
      const matchTags = schools.reduce((arr, s) => {
        const all = [s];
        // Add display parent
        const parent = normMap[s];
        if (parent && parent !== s && !all.includes(parent)) all.push(parent);
        // Add multi-tag expansions
        const expanded = expandMap[s];
        if (expanded) expanded.forEach(t => { if (!all.includes(t)) all.push(t); });
        return arr.concat(...all);
      }, []);
      const rawCountry = a.country || '';
      const countries = rawCountry.split(/[/,、，;；]/).map(c => c.trim());
      const normCountries = countries.map(c => cntMap[c] || c);
      return matchTags.includes(tag) ||
             countries.includes(tag) || normCountries.includes(tag) ||
             (a.century || '') === tag || (a.era || '') === tag;
    });
  }

  const loadFilters = async () => {
    try {
      const resp = await fetch(`${getApiBase()}/api/authors/filters`, {
        signal: AbortSignal.timeout(5000),
      });
      if (resp.ok) {
        const data = await resp.json();
        setFilters(data);
      }
    } catch (e) {}
  };


  if (loading) return <div className="loading">加载中...</div>;

  return (
    <div className="page-container">
      {/* 统计 */}
      <div style={{ fontSize: 13, color: 'var(--text-dim)', marginBottom: 10 }}>
        ✒️ 共 {allAuthors.length} 位作家，{allAuthors.reduce((s, a) => s + (a.book_count || 0), 0)} 部作品
      </div>

      {/* Search + Region filter */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 12, alignItems: 'center' }}>
        <input
          value={search}
          onChange={e => setSearch(e.target.value)}
          placeholder="搜索作家/国家/流派..."
          style={{
            flex: 1, padding: '8px 14px', borderRadius: 8,
            border: '1px solid var(--border)', background: 'var(--secondary)',
            color: 'var(--text)', fontSize: 13, outline: 'none',
          }}
        />
        {['all', 'east', 'west'].map(f => (
          <button key={f}
            className={`btn ${filter === f ? 'btn-primary' : 'btn-secondary'}`}
            style={{ padding: '6px 12px', fontSize: 13, flexShrink: 0 }}
            onClick={() => setFilter(f)}>
            {f === 'all' ? '全部' : f === 'east' ? '☯' : '🏛'}
          </button>
        ))}
      </div>

      {/* Tag/chip filters — show all schools */}
      {(filters.schools.length > 0 || filters.eras.length > 0) && (
        <div style={{ marginBottom: 12 }}>
          {/* Section: schools/流派 */}
          <div style={{ fontSize: 11, color: 'var(--text-dim)', marginBottom: 6 }}>
            流派标签 ({filters.schools.length})
            {filters.schools.length > 20 && (
              <span onClick={() => setShowAllTags(!showAllTags)} style={{ cursor: 'pointer', color: 'var(--accent)', marginLeft: 8 }}>
                {showAllTags ? '收起' : '展开全部'}
              </span>
            )}
          </div>
          <div style={{ display: 'flex', gap: 5, flexWrap: 'wrap', marginBottom: 10 }}>
            {(showAllTags ? filters.schools : filters.schools.slice(0, 20)).map(s => (
              <span key={s} onClick={() => toggleTag(s)}
                style={{
                  fontSize: 11, padding: '3px 10px', borderRadius: 12, cursor: 'pointer',
                  background: activeTags.includes(s) ? 'var(--accent)' : 'var(--secondary)',
                  color: activeTags.includes(s) ? 'var(--primary)' : 'var(--text-dim)',
                  border: '1px solid var(--border)',
                }}>
                {s}
              </span>
            ))}
          </div>
          {/* Section: eras/时代 */}
          {filters.eras.length > 0 && (
            <>
              <div style={{ fontSize: 11, color: 'var(--text-dim)', marginBottom: 6 }}>
                时代 ({filters.eras.length})
              </div>
              <div style={{ display: 'flex', gap: 5, flexWrap: 'wrap' }}>
                {filters.eras.map(e => (
                  <span key={e} onClick={() => toggleTag(e)}
                    style={{
                      fontSize: 11, padding: '3px 10px', borderRadius: 12, cursor: 'pointer',
                      background: activeTags.includes(e) ? 'var(--accent)' : 'var(--secondary)',
                      color: activeTags.includes(e) ? 'var(--primary)' : 'var(--text-dim)',
                      border: '1px solid var(--border)',
                    }}>
                    {e}
                  </span>
                ))}
              </div>
            </>
          )}
          {/* Section: countries/国家 */}
          {filters.countries.length > 0 && (
            <>
              <div style={{ fontSize: 11, color: 'var(--text-dim)', marginBottom: 6 }}>
                国家/地区 ({filters.countries.length})
              </div>
              <div style={{ display: 'flex', gap: 5, flexWrap: 'wrap', marginBottom: 10 }}>
                {filters.countries.map(c => (
                  <span key={c} onClick={() => toggleTag(c)}
                    style={{
                      fontSize: 11, padding: '3px 10px', borderRadius: 12, cursor: 'pointer',
                      background: activeTags.includes(c) ? 'var(--accent)' : 'var(--secondary)',
                      color: activeTags.includes(c) ? 'var(--primary)' : 'var(--text-dim)',
                      border: '1px solid var(--border)',
                    }}>
                    {c}
                  </span>
                ))}
              </div>
            </>
          )}
        </div>
      )}

      {/* Active tag chips */}
      {activeTags.length > 0 && (
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 10, alignItems: 'center' }}>
          <span style={{ fontSize: 11, color: 'var(--text-dim)' }}>筛选:</span>
          {activeTags.map(t => (
            <span key={t} onClick={() => toggleTag(t)}
              style={{
                fontSize: 11, padding: '3px 10px', borderRadius: 12, cursor: 'pointer',
                background: 'var(--accent)', color: 'var(--primary)',
                border: '1px solid var(--accent)',
              }}>
              {t} ✕
            </span>
          ))}
          <span onClick={() => setActiveTags([])}
            style={{ fontSize: 11, color: 'var(--text-dim)', cursor: 'pointer', marginLeft: 4 }}>
            清除全部
          </span>
        </div>
      )}

      {/* Author list */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
        {filtered.map((author) => (
          <div key={author.name}
            className="card"
            onClick={() => navigate(`/author/${encodeURIComponent(author.name)}`)}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                  <span className={`badge ${author.region === '东方' ? 'badge-east' : 'badge-west'}`}
                    style={{ fontSize: 10, padding: '2px 8px' }}>
                    {author.region}
                  </span>
                  <span style={{ fontSize: 15, fontWeight: 600, color: 'var(--text)' }}>
                    {author.name}
                  </span>
                </div>
                <div style={{ fontSize: 12, color: 'var(--text-dim)', display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                  {author.era && <span>📅 {author.era}</span>}
                  {author.country && <span>📍 {author.country}</span>}
                  {author.school && <span>📚 {author.school}</span>}
                </div>
                <div style={{ fontSize: 12, color: 'var(--text-dim)', marginTop: 4, lineHeight: 1.5 }}>
                  📖 收录 {author.book_count} 部作品:
                  {(author.books || []).slice(0, 5).map((b, i) => (
                    <span key={i} style={{ color: 'var(--accent)' }}>
                      《{b}》{i < Math.min(author.books.length, 5) - 1 ? '、' : ''}
                    </span>
                  ))}
                  {(author.books || []).length > 5 && <span> 等</span>}
                </div>
              </div>
              <span style={{ fontSize: 24, flexShrink: 0, marginLeft: 8 }}>
                {author.region === '东方' ? '☯' : '🏛'}
              </span>
            </div>
          </div>
        ))}
      </div>

      {filtered.length === 0 && !loading && (
        <div className="empty-state">
          <p>暂无匹配的作家</p>
        </div>
      )}
    </div>
  );
}

export default AuthorsPage;
