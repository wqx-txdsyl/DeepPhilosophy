/**
 * 哲人页面 —— 东西方哲学家按时间排序，显示年代/国家/流派/简介/作品
 * 离线可用（内置数据库兜底）
 */
import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import Icon from '../components/Icon';
import { getApiBase } from '../App';
import { cacheGet, cacheSet } from '../data/cache';

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
    "米利都学派":"古希腊哲学","埃利亚学派":"古希腊哲学","前苏格拉底":"古希腊哲学",
    "古代哲学":"古希腊哲学","犬儒学派":"古希腊哲学","自然哲学":"古希腊哲学",
    "新柏拉图主义":"古希腊哲学","斯多葛派":"古希腊哲学","斯多葛":"古希腊哲学","斯多葛学派":"古希腊哲学",
    "斯多葛主义":"古希腊哲学","怀疑论":"古希腊哲学","智者派":"古希腊哲学",
    "批判哲学":"德国古典哲学","德国唯心论":"德国古典哲学","唯意志论":"德国古典哲学",
    "德国观念论":"德国古典哲学","德国唯心主义":"德国古典哲学","悲观主义哲学":"德国古典哲学",
    "绝对唯心主义":"德国古典哲学","生命哲学":"德国古典哲学","哲学人类学":"德国古典哲学",
    "启蒙哲学":"启蒙运动","启蒙思想":"启蒙运动","苏格兰启蒙":"启蒙运动","人文主义":"启蒙运动",
    "理性主义":"启蒙运动","经验主义":"启蒙运动","实在论":"启蒙运动",
    "精神分析":"精神分析学","分析心理学":"精神分析学","心理治疗":"精神分析学",
    "逻辑实证":"分析哲学","逻辑原子主义":"分析哲学","日常语言":"分析哲学","语言哲学":"分析哲学",
    "形式社会学":"社会学","社会心理学":"社会学","群体心理学":"社会学",
    "社会达尔文":"社会学","宗教社会学":"社会学","理解社会学":"社会学","社会理论":"社会学",
    "自由主义":"政治哲学","社群主义":"政治哲学","功利主义":"政治哲学",
    "政治经济学":"政治哲学","激进平等":"政治哲学","责任伦理":"政治哲学","社会契约论":"政治哲学",
    "德性伦理":"伦理学","道德哲学":"伦理学",
    "批判理性主义":"科学哲学","实证":"科学哲学","实证主义":"科学哲学",
    "解释学":"存在主义","身体哲学":"存在主义","意向性":"存在主义",
    "荒诞文学":"存在主义","荒诞派戏剧":"存在主义","荒诞哲学":"存在主义",
    "浪漫主义":"存在主义","浪漫主义先驱":"存在主义",
    "结构语言学":"后结构主义","结构主义":"后结构主义",
    "进步教育":"科学哲学","新实用主义":"科学哲学",
    "后现代哲学":"后现代主义","解构主义":"后现代主义","后结构":"后结构主义","解构":"后结构主义",
    "儒家创始人":"儒家","先秦儒家":"儒家","理学":"儒家","心学":"儒家","经学":"儒家",
    "两汉经学":"儒家","宋明理学":"儒家","明清实学":"儒家","乾嘉朴学":"儒家","现代新儒家":"儒家",
    "道家创始人":"道家","先秦道家":"道家","魏晋玄学":"道家",
    "墨家创始人":"墨家","先秦墨家":"墨家","后期墨家":"墨家",
    "法家创始人":"法家","先秦法家":"法家",
    "兵家创始人":"兵家","名家创始人":"名家","阴阳家创始人":"阴阳家",
    "隋唐佛学":"佛学","禅宗":"佛学","净土":"佛学",
    "毛泽东思想":"中国马克思主义","中国马克思主义哲学":"中国马克思主义",
    "苏联马克思主义":"中国马克思主义",
    "天演论":"中国近代","维新派":"中国近代","三民主义":"中国近代",
    "教父哲学":"基督教哲学","经院哲学":"基督教哲学","唯名论":"基督教哲学",
    "希腊教父":"基督教哲学","拉丁教父":"基督教哲学",
    "历史唯物主义":"马克思主义","结构马克思主义":"马克思主义","西方马克思主义":"马克思主义",
    "文化霸权理论":"马克思主义","法兰克福学派":"马克思主义","交往理论":"马克思主义",
    "后女性主义":"女性主义","激进女性主义":"女性主义",
    "苏格兰":"英国","英格兰":"英国","俄国":"俄罗斯","普鲁士":"德国","罗马帝国":"古罗马",
    "儒":"儒家","道":"道家","墨":"墨家","法":"法家","兵":"兵家","名":"名家","佛":"佛学",
    "阴阳":"阴阳家","纵横":"纵横家",
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
    // 组合流派 → 筛选父标签时也能匹配到（如筛选"女性主义"→"存在主义女性主义"也会出现）
    "存在主义女性主义":["存在主义","女性主义"],
    "马克思主义女性主义":["马克思主义","女性主义"],
    "精神分析学女性主义":["精神分析学","女性主义"],
    "自由主义女性主义":["自由主义","女性主义"],
    "后结构主义女性主义":["后结构主义","女性主义"],
    "分析哲学女性主义":["分析哲学","女性主义"],
    "实用主义女性主义":["实用主义","女性主义"],
    "批判理论女性主义":["批判理论","女性主义"],
    "后现代主义女性主义":["后现代主义","女性主义"],
    "现象学存在主义":["现象学","存在主义"],
    "现象学诠释学":["现象学","哲学诠释学"],
    "分析哲学马克思主义":["分析哲学","马克思主义"],
    "存在主义现象学":["存在主义","现象学"],
    "马克思主义存在主义":["马克思主义","存在主义"],
    "结构主义马克思主义":["结构主义","马克思主义"],
    "现象学女性主义":["现象学","女性主义"],
    "后殖民女性主义":["后殖民哲学","女性主义"],
    "生态女性主义":["环境哲学","女性主义"],
  };
  const cntMap = {"苏格兰":"英国","英格兰":"英国","罗马帝国":"古罗马","北非":"古罗马","奥匈帝国（捷克）":"捷克","俄国":"俄罗斯"};
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

  const loadAllAuthors = async () => {
    setLoading(true);
    // Check cache first (10 min TTL)
    const cached = cacheGet('all_authors');
    if (cached?.length) {
      setAllAuthors(cached);
      setLoading(false);
      return;
    }
    try {
      const resp = await fetch(`${getApiBase()}/api/authors`, { signal: AbortSignal.timeout(8000) });
      if (resp.ok) {
        const data = await resp.json();
        const authors = data.authors || [];
        cacheSet('all_authors', authors);
        setAllAuthors(authors);
      }
    } catch (e) { console.error('Failed to load authors:', e); }
    setLoading(false);
  };

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
  else if (filter === 'world') filtered = filtered.filter(a => a.region === '世界');
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

  // Parse era string to centuries, e.g. "421-611年" -> ["5世纪","6世纪","7世纪"]
  const eraToCenturies = (era) => {
    if (!era) return [];
    const m = era.match(/(\d+)\s*[-–—]\s*(\d+)/);
    if (!m) return [era]; // can't parse, return as-is
    let start = parseInt(m[1]), end = parseInt(m[2]);
    // BC years
    const isBC = era.includes('前') || era.includes('BC');
    if (isBC) { start = -start; end = -end; }
    const centuries = new Set();
    for (let y = start; y <= end; y++) {
      const c = Math.ceil(Math.abs(y) / 100);
      centuries.add((isBC ? '前' : '') + c + '世纪');
    }
    return [...centuries];
  };

  // Compute filters client-side from allAuthors (instant, no extra API call)
  useEffect(() => {
    if (allAuthors.length === 0) return;
    const schools = new Set();
    const centuries = new Set();
    const countries = new Set();
    for (const a of allAuthors) {
      if (a.school) for (const s of String(a.school).split(/[/,、，;；]/)) {
        const t = s.trim();
        if (t) schools.add(t.replace(/[（(].*[)）]/g, ''));
      }
      if (a.era) {
        const cs = eraToCenturies(a.era);
        cs.forEach(c => centuries.add(c));
      }
      if (a.country) for (const c of String(a.country).split(/[/,、，;；]/)) {
        const t = c.trim();
        if (t) countries.add(countryDisplayMap[t] || cntMap[t] || t);
      }
    }
    setFilters({
      schools: [...schools].sort(),
      eras: [...centuries].sort((a,b) => {
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

      {/* Author list — CSS content-visibility for fast rendering */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
        {filtered.map((author) => (
          <div key={author.name} style={{ contentVisibility: 'auto', containIntrinsicSize: 'auto 80px' }}>
          <div
            className="card"
            onClick={() => navigate(`/author/${encodeURIComponent(author.name)}`)}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                  <span className={`badge ${author.region === '东方' ? 'badge-east' : author.region === '世界' ? 'badge-world' : 'badge-west'}`}
                    style={{ fontSize: 10, padding: '2px 8px' }}>
                    {author.region}
                  </span>
                  <span style={{ fontSize: 15, fontWeight: 600, color: 'var(--text)' }}>
                    {author.name}
                  </span>
                </div>
                <div style={{ fontSize: 12, color: 'var(--text-dim)', display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                  {author.era && <span>{author.era}</span>}
                  {author.country && <span>{author.country}</span>}
                  {author.school && <span>{author.school}</span>}
                </div>
              </div>
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
