/**
 * 哲人页面 —— 东西方哲学家按时间排序，显示年代/国家/流派/简介/作品
 * 离线可用（内置数据库兜底）
 */
import { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import Icon from '../components/Icon';
import { getApiBase } from '../App';
import { cacheGet, cacheSet } from '../data/cache';
import RANKING from '../data/schoolRanking';
import { normalizeTag, expandTag, normalizeCountry } from '../data/tagMaps';

// AuthorPortrait — 纯同步渲染，懒加载哲学家肖像
function AuthorPortrait({ name }) {
  const [visible, setVisible] = useState(false);
  const [failed, setFailed] = useState(false);
  const ref = useRef(null);
  useEffect(() => {
    const el = ref.current; if (!el) return;
    const obs = new IntersectionObserver(([e]) => { if (e.isIntersecting) { setVisible(true); obs.disconnect(); } }, { rootMargin: '200px' });
    obs.observe(el);
    return () => obs.disconnect();
  }, []);

  if (!visible) return <div ref={ref} style={{ width: '100%', height: '100%', background: 'var(--bg)' }} />;
  const safe = encodeURIComponent(name);
  if (failed) {
    return <div ref={ref} style={{ width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--card-bg)' }}><Icon name="nav-authors" size={18} /></div>;
  }
  return (
    <img ref={ref} src={`/philosopher/${safe}.webp`} alt={name}
      loading="lazy" decoding="async"
      style={{ width: '100%', height: '100%', objectFit: 'cover' }}
      onError={(e) => {
        if (e.target.src.endsWith('.webp')) {
          e.target.src = `/philosopher/${safe}.jpg`;
        } else {
          setFailed(true);
        }
      }} />
  );
}

function AuthorsPage() {
  const navigate = useNavigate();
  const [authors, setAuthors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [filter, setFilter] = useState('all');
  const [activeTags, setActiveTags] = useState([]);
  const [filters, setFilters] = useState({ eras: [], countries: [], schools: [] });
  const [showAllTags, setShowAllTags] = useState(false);
  const [search, setSearch] = useState('');

  // Tag normalization — imported from shared data/tagMaps.js (single source of truth)
  // 国家标签显示合并（筛选列表简化显示，详情页保持原名）
  const countryDisplayMap = {
    "巴比伦第一王朝":"巴比伦", "以色列王国":"以色列", "犹大王国":"犹太",
    "罗马共和国":"古罗马", "罗马帝国":"古罗马",
    "古埃及":"埃及", "古希腊":"希腊", "古印度":"印度",
    "玛雅文明":"玛雅", "玛雅城邦帕伦克":"玛雅",
    "阿兹特克帝国":"阿兹特克",
    "朝鲜王朝":"朝鲜", "蒙古帝国":"蒙古", "后突厥汗国":"突厥",
    "俄国":"俄罗斯", "中国等":"中国",
    "印加帝国":"印加", "拜占庭帝国":"拜占庭",
    "阿拉伯帝国":"阿拉伯", "奥匈帝国":"奥地利",
    "苏美尔":"美索不达米亚",
  };
  // 反向展开：简化名 → 所有原始名（用于筛选匹配）
  const countryExpandMap = {};
  for (const [orig, display] of Object.entries(countryDisplayMap)) {
    if (!countryExpandMap[display]) countryExpandMap[display] = [display];
    if (!countryExpandMap[display].includes(orig)) countryExpandMap[display].push(orig);
  }

  const toggleTag = (tag) => {
    setActiveTags(prev =>
      prev.includes(tag) ? prev.filter(t => t !== tag) : [...prev, tag]
    );
  };

  // Load all authors once on mount
  const [allAuthors, setAllAuthors] = useState([]);
  useEffect(() => {
    loadAllAuthors();
  }, []);

  // Parse era string to centuries. Handles: "20世纪", "421-611年", "约公元前6世纪", "1929-", etc.
  // Memoized — same era string parsed only once
  const _eraCache = useRef(new Map()).current;
  const eraToCenturies = useCallback((era) => {
    if (!era) return [];
    const cached = _eraCache.get(era);
    if (cached) return cached;

    let s = era.replace(/约|大約|左右|年/g, '').replace(/至今|迄今|现在|-$/g, '2025').replace(/-$/, '-2025').trim();
    const results = [];

    // Fix implicit BC prefix: "公元前6-5世纪" -> both should be BC
    // Extract the leading BC marker and apply to all century numbers
    const bcPrefix = s.match(/^(公元前|前)/);
    s = s.replace(/^(公元前|前)/, ''); // strip leading BC marker for parsing
    const isBC = !!bcPrefix;

    const centuryRe = /(前)?\s*(\d+)\s*世纪/g;
    let cm;
    while ((cm = centuryRe.exec(s)) !== null) {
      const c = parseInt(cm[2]);
      const prefix = cm[1] || (isBC ? '前' : ''); // inherit BC from context
      if (prefix ? c <= 100 : c <= 21)
        results.push(prefix + c + '世纪');
    }
    if (results.length > 0) {
      const out = [...new Set(results)];
      _eraCache.set(era, out);
      return out;
    }

    // Re-add BC prefix for year range parsing
    s = (isBC ? '前' : '') + s;

    const rangeRe = /(前)?\s*(\d+)\s*[-–—]\s*(前)?\s*(\d+)/;
    const rm = s.match(rangeRe);
    if (rm) {
      const bc1 = !!(rm[1] || isBC);
      const bc2 = !!(rm[3] || isBC);
      let y1 = parseInt(rm[2]) * (bc1 ? -1 : 1);
      let y2 = parseInt(rm[4]) * (bc2 ? -1 : 1);
      if (y1 > y2) [y1, y2] = [y2, y1];
      const set = new Set();
      for (let y = y1; y <= y2; y++) {
        if (y === 0) continue;
        const ay = Math.abs(y);
        const c = Math.floor((ay - 1) / 100) + 1;
        if ((y < 0 && c > 100) || (y > 0 && c > 21)) continue; // BC up to 10000BC, AD up to 2100
        set.add((y < 0 ? '前' : '') + c + '世纪');
      }
      const out = [...set];
      _eraCache.set(era, out);
      return out;
    }

    const singleRe = /(前)?\s*(\d{3,4})/;
    const sm = s.match(singleRe);
    if (sm) {
      const y = parseInt(sm[2]) * ((sm[1] || isBC) ? -1 : 1);
      const c = Math.floor((Math.abs(y) - 1) / 100) + 1;
      const out = [(y < 0 ? '前' : '') + c + '世纪'];
      _eraCache.set(era, out);
      return out;
    }
    _eraCache.set(era, []);
    return [];
  }, []);

  const loadAllAuthors = async () => {
    setLoading(true);
    // 1. 优先本地 JSON（毫秒级），和 BooksPage 一样的策略
    try {
      const resp = await fetch('/philosophers.json?v=2');
      if (resp.ok) {
        const philo = await resp.json();
        const authors = Object.values(philo).map(p => ({
          name: p.name, region: p.region || '西方', era: p.era || '',
          country: p.country || '', school: p.school || '',
          book_count: (p.books || []).length, books: p.books || [],
          rank: p.rank || 0,
        }));
        // 按 AI 综合评分降序（无评分的放末尾）
        authors.sort((a, b) => (b.rank || 0) - (a.rank || 0));
        cacheSet('all_authors_v2', authors);
        setAllAuthors(authors);
        setLoading(false);
        return;
      }
    } catch (e) { console.error('Local authors load failed:', e); }
    // 3. 回退 API
    try {
      const resp = await fetch(`${getApiBase()}/api/authors`, { signal: AbortSignal.timeout(8000) });
      if (resp.ok) {
        const data = await resp.json();
        const authors = (data.authors || []).map(a => ({...a, book_count: a.book_count || (a.books||[]).length, rank: a.rank || 0}));
        try { authors.sort((a, b) => (b.rank || 0) - (a.rank || 0)); } catch {}
        cacheSet('all_authors_v2', authors);
        setAllAuthors(authors);
      }
    } catch (e2) { console.error('API fallback also failed:', e2); }
    setLoading(false);
  };

  // Client-side filtering — useMemo so heavy eraToCenturies doesn't re-run on every render
  const filtered = useMemo(() => {
    let result = allAuthors;
    if (search) {
      const q = search.toLowerCase();
      result = result.filter(a =>
        a.name.toLowerCase().includes(q) || (a.country||'').toLowerCase().includes(q) || (a.school||'').toLowerCase().includes(q)
      );
    }
    if (filter === 'east') result = result.filter(a => a.region === '东方');
    else if (filter === 'west') result = result.filter(a => a.region === '西方');
    else if (filter === 'world') result = result.filter(a => a.region === '世界');
    // Multi-tag filter (client-side, mirrored normalization)
    for (const tag of activeTags) {
      result = result.filter(a => {
        const rawSchool = a.school || '';
        const schools = rawSchool.split(/[/,、，;；]/).map(s => s.trim());
        const matchTags = schools.reduce((arr, s) => {
          return arr.concat(...expandTag(s));
        }, []);
        const rawCountry = a.country || '';
        const countries = rawCountry.split(/[/,、，;；]/).map(c => c.trim());
        const normCountries = countries.map(c => normalizeCountry(c));
        // Expand simplified country tags to match all variants
        const expandedCountries = countryExpandMap[tag] || [tag];
        // Century matching: philosopher spans that century
        const authorCenturies = eraToCenturies(a.era);
        return matchTags.includes(tag) ||
               countries.some(c => expandedCountries.includes(c)) ||
               normCountries.some(c => expandedCountries.includes(c)) ||
               authorCenturies.includes(tag);
      });
    }
    return result;
  }, [allAuthors, search, filter, activeTags, eraToCenturies]);

  // Compute filters client-side from allAuthors (instant, no extra API call)
  useEffect(() => {
    if (allAuthors.length === 0) return;
    const schoolCount = new Map(); // count philosophers per normalized school
    const centuries = new Set();
    const countries = new Set();
    for (const a of allAuthors) {
      if (a.school) for (const s of String(a.school).split(/[/,、，;；]/)) {
        const t = s.trim().replace(/[（(].*[)）]/g, '');
        if (!t) continue;
        const norm = normalizeTag(t);
        schoolCount.set(norm, (schoolCount.get(norm) || 0) + 1);
      }
      if (a.era) {
        const cs = eraToCenturies(a.era);
        cs.forEach(c => centuries.add(c));
      }
      if (a.country) for (const c of String(a.country).split(/[/,、，;；]/)) {
        const t = c.trim();
        if (t) countries.add(countryDisplayMap[t] || normalizeCountry(t));
      }
    }
    // Final sanity filter: reject impossible centuries
    const validEras = [...centuries].filter(c => {
      const n = parseInt(c.replace('前',''));
      if (isNaN(n)) return false;
      return c.includes('前') ? n <= 100 : n <= 21;
    });
    // Sort schools by AI influence ranking
    const rankIndex = Object.fromEntries(RANKING.map((name, i) => [name, i]));
    const sortedSchools = [...schoolCount.entries()]
      .sort((a, b) => {
        const ra = rankIndex[a[0]] ?? 9999;
        const rb = rankIndex[b[0]] ?? 9999;
        return ra - rb;
      })
      .map(([name]) => name);

    setFilters({
      schools: sortedSchools,
      eras: validEras.sort((a,b) => {
        const na = a.includes('前') ? -parseInt(a) : parseInt(a);
        const nb = b.includes('前') ? -parseInt(b) : parseInt(b);
        return na - nb;
      }),
      countries: [...countries].sort(),
    });
  }, [allAuthors]);


  if (loading) return <div className="loading">加载中...</div>;

  return (
    <div className="page-container">
      {/* 统计 */}
      <div style={{ fontSize: 13, color: 'var(--text-dim)', marginBottom: 10 }}>
        <Icon name="nav-authors" size={16} /> 共 {allAuthors.length} 位哲人，{allAuthors.reduce((s, a) => s + (a.book_count || 0), 0)} 部作品
      </div>

      {/* Search + Region filter */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 12, alignItems: 'center' }}>
        <input
          value={search}
          onChange={e => setSearch(e.target.value)}
          placeholder="搜索哲人/国家/流派..."
          style={{
            flex: 1, padding: '8px 14px', borderRadius: 8,
            border: '1px solid var(--border)', background: 'var(--secondary)',
            color: 'var(--text)', fontSize: 13, outline: 'none',
          }}
        />
        {['all', 'east', 'west', 'world'].map(f => (
          <button key={f}
            className={`btn ${filter === f ? 'btn-primary' : 'btn-secondary'}`}
            style={{ padding: '6px 12px', fontSize: 13, flexShrink: 0 }}
            onClick={() => setFilter(f)}>
            {f === 'all' ? '全部' : f === 'east' ? <><Icon name='region-east' size={14} /> 东方</> : f === 'west' ? <><Icon name='region-west' size={14} /> 西方</> : <><Icon name='region-world' size={14} /> 世界</>}
          </button>
        ))}
      </div>

      {/* Tag/chip filters */}
      <div>
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
                {Array.from(new Set(filters.countries.map(c => countryDisplayMap[c] || c))).sort().map(c => (
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
      </div>

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
              {t} <Icon name="icon-close" size={16} />
            </span>
          ))}
          <span onClick={() => setActiveTags([])}
            style={{ fontSize: 11, color: 'var(--text-dim)', cursor: 'pointer', marginLeft: 4 }}>
            清除全部
          </span>
        </div>
      )}

      {/* Author grid — 带肖像的卡片网格 */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
        gap: 10,
      }}>
        {filtered.map((author) => (
          <div key={author.name}
            className="card"
            onClick={() => navigate(`/author/${encodeURIComponent(author.name)}`)}
            style={{
              padding: '12px 16px', cursor: 'pointer', contentVisibility: 'auto', containIntrinsicSize: 'auto 80px',
              display: 'flex', gap: 12, alignItems: 'flex-start',
            }}>
            {/* 肖像缩略图 */}
            <div style={{
              width: 48, height: 64, flexShrink: 0,
              borderRadius: 4, overflow: 'hidden',
              background: 'var(--bg)', border: '1px solid var(--border)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              <AuthorPortrait name={author.name} />
            </div>
            {/* 信息 */}
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{
                fontSize: 14, fontWeight: 500, color: 'var(--ink)',
                fontFamily: 'var(--font-serif)', marginBottom: 2,
                overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                display: 'flex', alignItems: 'center', gap: 6,
              }}>
                <span className={`badge ${author.region === '东方' ? 'badge-east' : author.region === '世界' ? 'badge-world' : 'badge-west'}`}
                  style={{ fontSize: 9, padding: '1px 6px', flexShrink: 0 }}>
                  {author.region}
                </span>
                {author.name}
              </div>
              <div style={{ fontSize: 11, color: 'var(--text-dim)', marginBottom: 4 }}>
                {[author.era, author.country].filter(Boolean).join(' · ')}
              </div>
              <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap', alignItems: 'center' }}>
                {author.book_count > 0 && (
                  <span style={{ fontSize: 10, color: 'var(--text-dim)', display: 'flex', alignItems: 'center', gap: 3 }}>
                    <Icon name="nav-books" size={12} />{author.book_count}部
                  </span>
                )}
                {author.school && author.school.split(/[/,，、;；]/).slice(0, 2).map((s, i) => {
                  const t = s.trim().replace(/[（(].*[)）]/g, '');
                  return t ? <span key={i} className="tag" style={{ fontSize: 9, padding: '1px 6px' }}>{t}</span> : null;
                })}
              </div>
            </div>
          </div>
        ))}
      </div>

      {filtered.length === 0 && !loading && (
        <div className="empty-state">
          <p>暂无匹配的哲人</p>
        </div>
      )}
    </div>
  );
}

export default AuthorsPage;
