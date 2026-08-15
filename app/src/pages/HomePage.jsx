/**
 * 谱系 —— 垂直时间轴，每行一个大流派卡片
 */
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import DAILY_QUOTES from '../data/dailyQuotes';
import { normalizeTag } from '../data/tagMaps';
import WorldMap from '../components/WorldMap';
import NavBar from '../components/NavBar';
import Icon from '../components/Icon';
import CountUp from '../components/CountUp';
import SectionReveal from '../components/SectionReveal';
import Footer from '../components/Footer';
import './HomePage.css';







function HomePage() {
  const navigate = useNavigate();
  const [authorCount, setAuthorCount] = useState(743);
  const [bookCount, setBookCount] = useState(293);
  const [schoolCount] = useState(111);
  const [, setSchoolData] = useState({});
  const loggedIn = !!localStorage.getItem('dp_token');
  const username = localStorage.getItem('dp_username') || '';
  const userAvatar = localStorage.getItem('dp_avatar') || '';
  const [dailyQuote, setDailyQuote] = useState(() => DAILY_QUOTES[Math.floor(Math.random() * DAILY_QUOTES.length)]);

  // 从本地静态 JSON 加载准确数据（与 BooksPage/AuthorsPage 一致）
  // OSS 上海双轨: 先试 OSS（~80ms）, 2.5s 超时回退同源（同源兜底边缘缓存, 二次命中秒开）
  useEffect(() => {
    const tryFetch = async (url, timeout) => {
      try {
        const resp = await fetch(url, timeout ? { signal: AbortSignal.timeout(timeout) } : undefined);
        return resp.ok ? resp.json() : null;
      } catch { return null; }
    };
    Promise.all([
      tryFetch('https://deepphilosophy.oss-cn-shanghai.aliyuncs.com/books.json', 2500)
        .then(r => r || fetch('/books.json').then(x => x.ok ? x.json() : []).catch(() => [])),
      tryFetch('https://deepphilosophy.oss-cn-shanghai.aliyuncs.com/philosophers.json', 2500)
        .then(r => r || fetch('/philosophers.json').then(x => x.ok ? x.json() : {}).catch(() => ({})),
      ),
    ]).then(([books, philosophers]) => {
      setBookCount(Array.isArray(books) ? books.length : 0);
      const authors = Object.values(philosophers);
      setAuthorCount(authors.length);
      // 聚合流派数据
      const map = {};
      authors.forEach(a => {
        const raw = a.school || '';
        if (!raw) return;
        raw.replace(/[、，,]/g, '/').split('/').forEach(s => {
          s = s.trim();
          if (!s || s.length < 2) return;
          const big = normalizeTag(s);
          if (!map[big]) map[big] = { authors: [], keywords: new Set(), books: [] };
          if (!map[big].authors.includes(a.name)) {
            map[big].authors.push(a.name);
            map[big].books.push(...(a.books || []));
          }
          if (a.era) map[big].keywords.add(a.era.split('-')[0].replace(/[^0-9]/g,'') + '年代');
          if (a.country) map[big].keywords.add(a.country.split('/')[0]);
        });
      });
      setSchoolData(map);
    }).catch(() => {});
  }, []);

  const scrollToDaily = () => {
    document.getElementById('daily-quote')?.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <div className="page-container" style={{ paddingBottom: 0, margin: 0 }}>
      <NavBar variant="floating" loggedIn={loggedIn} username={username} userAvatar={userAvatar} />

      <section className="home-hero">
        <div className="home-hero-bg" />
        <div className="home-hero-overlay" />
        <div className="home-hero-content">
          <p className="home-hero-eyebrow">Philosophical Genealogy</p>
          <h1 className="home-hero-title">DeepPhilosophy</h1>
          <div className="home-hero-divider" />
          <p className="home-hero-subtitle">从公元前三十世纪至二十一世纪<br />一部横跨五千年的思想史长卷</p>
          <button className="home-hero-cta" onClick={scrollToDaily}>开始探索</button>
        </div>
        <div className="home-hero-scroll-hint">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--text-dim)" strokeWidth="1.5" strokeLinecap="round"><line x1="12" y1="5" x2="12" y2="19"/><polyline points="5 12 12 19 19 12"/></svg>
        </div>
      </section>

      <SectionReveal>
      <section className="home-stats">
        <div className="home-stats-grid">
          {[{ end: bookCount, label: '哲学著作' }, { end: authorCount, label: '哲学家' }, { end: schoolCount, label: '哲学流派' }].map(s => (
            <div key={s.label}>
              <p className="home-stat-number"><CountUp end={s.end} /></p>
              <p className="home-stat-label">{s.label}</p>
            </div>
          ))}
        </div>
      </section>
      </SectionReveal>

      <SectionReveal>
      <section id="daily-quote" className="home-quote"
        onClick={() => { const q = DAILY_QUOTES[Math.floor(Math.random() * DAILY_QUOTES.length)]; setDailyQuote(q); }}>
        <div style={{ maxWidth: 680, margin: '0 auto', position: 'relative' }}>
          <p className="home-quote-eyebrow">Daily Quote — 点击切换</p>
          <p className="home-quote-text">&ldquo;{dailyQuote.text}&rdquo;</p>
          <p className="home-quote-author">&mdash; {dailyQuote.author}</p>
        </div>
      </section>
      </SectionReveal>

      <SectionReveal>
      <section className="home-showcase">
        <div className="home-showcase-grid">
          <div className="home-showcase-card" onClick={() => navigate('/books')}>
            <span className="home-showcase-eyebrow" style={{ color: 'var(--ochre)' }}>Library</span>
            <h2 className="home-showcase-title">{bookCount} 部哲学著作</h2>
            <p className="home-showcase-desc">PDF · EPUB · TXT 三格式，涵盖古希腊至当代的中西方哲学经典。支持在线阅读、AI批注与笔记。</p>
          </div>
          <div className="home-showcase-card card-philosophers" onClick={() => navigate('/authors')}>
            <span className="home-showcase-eyebrow" style={{ color: 'var(--prussian)' }}>Philosophers</span>
            <h2 className="home-showcase-title">{authorCount} 位哲学家</h2>
            <p className="home-showcase-desc">从柏拉图到尼采，从孔子到牟宗三。每位哲学家配备千字思想剖析与Wikipedia链接。</p>
          </div>
        </div>
      </section>
      </SectionReveal>

      <SectionReveal>
      <section className="home-world-section">
        <h2 className="home-world-title">探索世界哲学</h2>
        <p className="home-world-subtitle">悬停查看简介 · 点击进入详情</p>
        <WorldMap />
        <div style={{ display: 'flex', justifyContent: 'center', gap: 24, marginTop: 24, flexWrap: 'wrap' }}>
          {[
            { l: <><Icon name="region-west" size={14} /> 西方 42 流派</>, p: '/western-philosophies', c: 'var(--ochre)' },
            { l: <><Icon name="region-east" size={14} /> 东方 25 流派</>, p: '/eastern-philosophies', c: 'var(--prussian)' },
            { l: <><Icon name="region-world" size={14} /> 世界 38 流派</>, p: '/world-philosophies', c: '#5A8A5A' },
          ].map(b => (
            <span key={b.p} onClick={() => navigate(b.p)} style={{ fontSize: 12, color: b.c, cursor: 'pointer', borderBottom: '1px solid transparent', transition: 'all 0.2s' }}
              onMouseEnter={e => e.currentTarget.style.borderBottomColor = b.c}
              onMouseLeave={e => e.currentTarget.style.borderBottomColor = 'transparent'}>{b.l}</span>
          ))}
        </div>
      </section>
      </SectionReveal>

      <Footer />
    </div>
  );
}

export default HomePage;