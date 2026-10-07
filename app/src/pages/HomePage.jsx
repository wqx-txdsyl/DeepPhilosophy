/**
 * 首页 —— 哲学宇宙（全屏星图，一屏即全部）
 * 纯黑星空 + 品牌字；点击「立即探索」：文字与按钮离子化——
 * 碎成光点飞散，落进星图成为星星，导航保持可用，完整内容节点与生成的星光共同构成夜空
 */
import { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { getReadingHistory } from '../data/userData';
import { readingView } from '../data/readingRoom';
import { startHomeSkyTransition } from '../components/homeSkyParticles';
import NavBar from '../components/NavBar';
import HomeCosmos from '../components/HomeCosmos';
import './HomePage.css';

function HomePage() {
  const [thinkers, setThinkers] = useState(null);
  const [books, setBooks] = useState(null);
  const [veiled, setVeiled] = useState(false);
  const heroRef = useRef(null);
  const burstRef = useRef(null);
  const veiledRef = useRef(false);
  const sceneRef = useRef(null);
  const birthStarsRef = useRef([]);
  const transitionRef = useRef(null);
  const [transitioning, setTransitioning] = useState(false);
  const [history] = useState(getReadingHistory);
  const recent = history.find(entry => entry.bookId && (!books || books.some(book => book.id === entry.bookId && Number(book.chapterCount) > 0)));
  const recentBook = books?.find(book => book.id === recent?.bookId);
  const resume = recent ? readingView(recent, recentBook) : null;
  useEffect(() => () => transitionRef.current?.(), []);
  const loggedIn = !!localStorage.getItem('dp_token');
  const username = localStorage.getItem('dp_username') || '';
  const userAvatar = localStorage.getItem('dp_avatar') || '';

  // 从本地静态 JSON 加载星图数据（与 BooksPage/AuthorsPage 一致）
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
        .then(r => r || fetch('/philosophers.json').then(x => x.ok ? x.json() : {}).catch(() => ({}))),
    ]).then(([bookList, philosophers]) => {
      setBooks(Array.isArray(bookList) ? bookList : []);
      setThinkers(Object.values(philosophers).filter(person => !person.listingKind || person.listingKind === 'thinker'));
    }).catch(() => {});
  }, []);

  // 导航栏全程悬浮在星空上，用骨白配色；点击探索后依然保留
  useEffect(() => {
    const nav = document.querySelector('.navbar-floating');
    if (!nav) return;
    nav.classList.add('nav-on-dark');
    return () => nav.classList.remove('nav-on-dark');
  }, []);

  function handleExplore() {
    if (veiledRef.current) return;
    veiledRef.current = true;
    setTransitioning(true);
    try {
      transitionRef.current = startHomeSkyTransition({
        hero: heroRef.current, canvas: burstRef.current, sceneRef, birthStarsRef,
        onFinish: () => setTransitioning(false),
      });
    } catch {
      heroRef.current?.classList.remove('is-ionizing');
      setTransitioning(false);
    }
    setVeiled(true);
  }

  return (
    <div className="page-container home-page" style={{ paddingBottom: 0, margin: 0 }}>
      <NavBar variant="floating" loggedIn={loggedIn} username={username} userAvatar={userAvatar} />

      <section className={`home-hero${veiled ? ' veiled' : ''}`} ref={heroRef}>
        <HomeCosmos philosophers={thinkers} books={books} active={veiled} interactive={!transitioning} sceneRef={sceneRef} birthStarsRef={birthStarsRef} />
        <div className="home-hero-overlay" />
        <canvas className="home-hero-burst" ref={burstRef} aria-hidden="true" />
        <div className="home-hero-content" aria-hidden={veiled} inert={veiled}>
          <p className="home-hero-eyebrow">The Philosophy Universe</p>
          <h1 className="home-hero-title">DeepPhilosophy</h1>
          <p className="home-hero-invitation">循着问题，走近思想。</p>
          <button className="home-hero-cta" onClick={handleExplore}>立即探索 ↗</button>
          <Link className="home-hero-continue" to={resume?.href || '/books'}>
            {resume ? <>继续阅读 <span>{recentBook?.title || recent.bookTitle || '上次的书'} →</span></> : <>从一本书开始 <span>去书库 →</span></>}
          </Link>
        </div>
      </section>
    </div>
  );
}

export default HomePage;
