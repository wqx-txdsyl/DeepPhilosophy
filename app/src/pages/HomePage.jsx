/**
 * 首页 —— 哲学宇宙（全屏星图，一屏即全部）
 * 纯黑星空 + 品牌字；点击「立即探索」：文字与按钮离子化——
 * 碎成光点飞散，落进星图成为星星，导航同步隐去，只剩纯粹可玩的宇宙
 */
import { useState, useEffect, useRef } from 'react';
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

  // 离子化：把 Hero 文字/按钮栅格化采样成光点，飞散落入星图
  function ionize() {
    const hero = heroRef.current, canvas = burstRef.current;
    if (!hero || !canvas) return;
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    const rect = hero.getBoundingClientRect();
    const W = rect.width, H = rect.height;

    // 1) 离屏画布重绘同样的文字/按钮
    const off = document.createElement('canvas');
    off.width = W; off.height = H;
    const o = off.getContext('2d');
    o.textAlign = 'center';
    const content = hero.querySelector('.home-hero-content');
    if (!content) return;
    content.querySelectorAll('.home-hero-eyebrow,.home-hero-title,.home-hero-divider,.home-hero-cta').forEach(el => {
      const r = el.getBoundingClientRect();
      const x = r.left - rect.left, y = r.top - rect.top;
      if (el.classList.contains('home-hero-divider')) {
        o.fillStyle = '#B8956A';
        o.fillRect(x, y + r.height / 2 - 1, r.width, 2);
        return;
      }
      if (el.classList.contains('home-hero-cta')) {
        o.fillStyle = '#B8956A';
        o.beginPath();
        o.roundRect(x, y, r.width, r.height, 6);
        o.fill();
        o.fillStyle = '#16120B';
        o.font = '500 14px -apple-system, "PingFang SC", sans-serif';
        o.textBaseline = 'middle';
        o.fillText('立即探索', x + r.width / 2, y + r.height / 2 + 1);
        return;
      }
      const cs = getComputedStyle(el);
      o.fillStyle = cs.color;
      o.font = `${cs.fontStyle} ${cs.fontWeight} ${cs.fontSize} ${cs.fontFamily}`;
      if ('letterSpacing' in o) o.letterSpacing = cs.letterSpacing;
      const fs = parseFloat(cs.fontSize);
      const lh = cs.lineHeight === 'normal' ? fs * 1.2 : parseFloat(cs.lineHeight);
      const lines = el.innerText.split('\n');
      o.textBaseline = 'top';
      lines.forEach((line, i) => {
        o.fillText(line, x + r.width / 2, y + i * lh + (lh - fs) / 2);
      });
    });

    // 2) 像素采样 → 光点
    const img = o.getImageData(0, 0, W, H).data;
    let parts = [];
    for (let y = 0; y < H; y += 3) {
      for (let x = 0; x < W; x += 3) {
        const i = (y * W + x) * 4;
        if (img[i + 3] > 110) {
          parts.push({
            x, y,
            c: `${img[i]},${img[i + 1]},${img[i + 2]}`,
            dx: 0, dy: 0, tx: 0, ty: 0, delay: 0, dur: 0, t: 0,
            s: 1.7 + Math.random() * 1.3,
            wob: Math.random() * Math.PI * 2,
          });
        }
      }
    }
    // 数量上限：随机抽稀
    const CAP = 2800;
    if (parts.length > CAP) {
      parts = parts.filter(() => Math.random() < CAP / parts.length);
    }
    const BANDS = [0.30, 0.58, 0.80];
    const g = () => (Math.random() + Math.random() + Math.random()) / 1.5 - 1;
    for (const p of parts) {
      const centerD = Math.hypot(p.x - W / 2, p.y - H * 0.45);
      p.delay = 0.04 + (centerD / Math.hypot(W / 2, H / 2)) * 0.42 + Math.random() * 0.16; // 由中心向外离子化
      p.dur = 1.15 + Math.random() * 1.05;
      if (Math.random() < 0.78) {           // 落入星带，成为星星
        p.tx = Math.random() * W;
        p.ty = (BANDS[(Math.random() * 3) | 0] + g() * 0.11) * H;
      } else {                               // 一部分向上飘散离场
        p.tx = Math.random() * W;
        p.ty = -30 - Math.random() * H * 0.35;
        p.gone = true;
      }
    }

    // 3) 飞行动画：短暂颤动 → 弧线飞向星位 → 缩小没入星图（dpr 上限 1.5 保帧率）
    const dpr = Math.min(1.5, window.devicePixelRatio || 1);
    canvas.width = W * dpr; canvas.height = H * dpr;
    // 显式指定 CSS 尺寸：高 DPI 屏若 inset 拉伸失效，画布会按位图原始尺寸
    // 显示 → 粒子文字放大 2 倍偏移到右下角（线上实测 bug）
    canvas.style.width = W + 'px';
    canvas.style.height = H + 'px';
    const ctx = canvas.getContext('2d');
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    const t0 = performance.now();
    let raf;
    const tick = (now) => {
      const t = (now - t0) / 1000;
      ctx.clearRect(0, 0, W, H);
      let alive = 0;
      for (const p of parts) {
        if (t < p.delay) { // 离子化前：原位颤动
          alive++;
          ctx.fillStyle = `rgba(${p.c},0.92)`;
          ctx.fillRect(p.x + Math.sin(now * 0.02 + p.wob) * 1.1, p.y + Math.cos(now * 0.017 + p.wob) * 1.1, p.s, p.s);
          continue;
        }
        const k = Math.min(1, (t - p.delay) / p.dur);
        if (k >= 1) continue;
        alive++;
        const ease = 1 - Math.pow(1 - k, 3);
        const px = p.x + (p.tx - p.x) * ease + Math.sin(now * 0.004 + p.wob) * 3 * (1 - k);
        const py = p.y + (p.ty - p.y) * ease;
        const alpha = p.gone ? 1 - k * 0.9 : (k > 0.75 ? (1 - k) / 0.25 : 1);
        const s = p.s * (1 - ease * 0.55);
        ctx.fillStyle = `rgba(${p.c},${alpha.toFixed(3)})`;
        ctx.fillRect(px, py, s, s);
      }
      if (alive > 0) raf = requestAnimationFrame(tick);
      else ctx.clearRect(0, 0, W, H);
    };
    raf = requestAnimationFrame(tick);
  }

  function handleExplore() {
    if (veiledRef.current) return;
    veiledRef.current = true;
    setVeiled(true);
    requestAnimationFrame(() => ionize());
  }

  return (
    <div className="page-container home-page" style={{ paddingBottom: 0, margin: 0 }}>
      <NavBar variant="floating" loggedIn={loggedIn} username={username} userAvatar={userAvatar} />

      <section className={`home-hero${veiled ? ' veiled' : ''}`} ref={heroRef}>
        <HomeCosmos philosophers={thinkers} books={books} active={veiled} />
        <div className="home-hero-overlay" />
        <canvas className="home-hero-burst" ref={burstRef} aria-hidden="true" />
        <div className="home-hero-content">
          <p className="home-hero-eyebrow">The Philosophy Universe</p>
          <h1 className="home-hero-title">DeepPhilosophy</h1>
          <div className="home-hero-divider" />
          <button className="home-hero-cta" onClick={handleExplore}>立即探索</button>
        </div>
      </section>
    </div>
  );
}

export default HomePage;
