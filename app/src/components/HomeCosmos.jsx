/**
 * 哲学宇宙 v3 —— 可缩放的星图地图
 *
 * 交互逻辑（导航式）：
 *   默认概貌：只有流派星系核 + 哲人恒星 + 尘埃（"国界"层）
 *   滚轮缩放 / 拖拽平移：逐级精细化——子流派、著作浮现（"城市"），
 *   再放大金句、辞海微星显现（"街道与店铺"）
 *   点击星星：选中亮起，关系链逐跳点亮相邻星星；再次点击同一颗才跳转
 *
 * 节点：流派175 子流派355 哲人652 著作410 金句2684 辞海3831 思想之问12
 * 布局：均匀有机团簇（无疏密斑驳、无条带）；无鼠标视差；常显文字已移除
 */
import { useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { QUESTIONS } from '../data/genealogyTopics';
import { layoutHomeSkyLabels } from './homeSkyLabels';

const REGION_COLOR = { '西方': [217, 179, 108], '东方': [127, 163, 204], '世界': [143, 185, 143] };
const BONE = 'rgba(232, 227, 217,';
const SUB_RGB = [206, 196, 176];
const QUOTE_RGB = [226, 220, 208];
const CIHAI_RGB = [196, 162, 112];
const ZOOM_MIN = 1, ZOOM_MAX = 36; // 自由缩放：1 倍全银河概貌 ↔ 36 倍精细；默认停在 2.6 倍

function hashStr(s) { let h = 2166136261; for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); } return h >>> 0; }
function mulberry32(seed) { let a = seed; return function () { a |= 0; a = (a + 0x6D2B79F5) | 0; let t = Math.imul(a ^ (a >>> 15), 1 | a); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }
function gauss(rand) { return (rand() + rand() + rand()) / 1.5 - 1; }
const clamp01 = (v, lo = 0.02, hi = 0.98) => Math.min(hi, Math.max(lo, v));

// 均匀有机团簇中心（无疏密斑驳）
function clusterCenters(count, rand) {
  const pts = [];
  let guard = 0;
  while (pts.length < count && guard < 40000) {
    guard++;
    const x = 0.04 + rand() * 0.92, y = 0.05 + rand() * 0.90;
    if (pts.every(p => Math.hypot(p[0] - x, p[1] - y) >= 0.062)) pts.push([x, y]);
  }
  return pts;
}

function makeSprite(rgb, size, soft) {
  const c = document.createElement('canvas');
  c.width = c.height = size;
  const ctx = c.getContext('2d');
  const half = size / 2;
  const g = ctx.createRadialGradient(half, half, 0, half, half, half);
  const [r, gc, b] = rgb;
  if (soft) {
    g.addColorStop(0, `rgba(${r},${gc},${b},1)`);
    g.addColorStop(0.22, `rgba(${r},${gc},${b},0.6)`);
    g.addColorStop(0.55, `rgba(${r},${gc},${b},0.18)`);
  } else {
    g.addColorStop(0, 'rgba(255,252,245,1)');
    g.addColorStop(0.12, `rgba(${r},${gc},${b},0.35)`);
    g.addColorStop(0.4, `rgba(${r},${gc},${b},0.055)`);
  }
  g.addColorStop(1, `rgba(${r},${gc},${b},0)`);
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, size, size);
  return c;
}

const escapeHTML = value => String(value || '').replace(/[&<>"']/g, c => ({ '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;' }[c]));
// This quiet sky is rendered with the opening itself, before any CDN data arrives.
const openingRand=mulberry32(20261008);
const OPENING_STARS=Array.from({length:480},(_,i)=>({
  x:openingRand()*1440,y:openingRand()*900,
  r:i%47===0?1.05+openingRand()*.55:.28+openingRand()*.50,
  alpha:i%47===0?.58+openingRand()*.22:.20+openingRand()*.30,
  color:i%13===0?'#d7c6ab':'#dce3ea',
}));

const TYPE_LABEL = { philosopher: '哲人', school: '流派', sub: '子流派', book: '著作', question: '思想之问', quote: '金句', cihai: '辞海' };

export default function HomeCosmos({ philosophers, books, active = false, interactive = true, sceneRef, birthStarsRef }) {
  const navigate = useNavigate();
  const wrapRef = useRef(null);
  const canvasRef = useRef(null);
  const tipRef = useRef(null);
  const activeRef = useRef(active);
  const interactiveRef = useRef(interactive);
  const labelsRef = useRef(null);
  useEffect(() => { interactiveRef.current = interactive; }, [interactive]);
  const activateAtRef = useRef(0);
  useEffect(() => {
    if (active && !activeRef.current) activateAtRef.current = performance.now();
    activeRef.current = active;
    sceneRef?.current?.renderFrame();
  }, [active, sceneRef]);

  useEffect(() => {
    const wrap = wrapRef.current, canvas = canvasRef.current;
    if (!wrap || !canvas || !philosophers?.length || !books?.length) return;
    const ctx = canvas.getContext('2d');
    const tipElement=tipRef.current,labelsElement=labelsRef.current;
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const rand = mulberry32(20261006);

    let cosmos = null;
    fetch('/cosmos/cosmos-data.json').then(r => r.ok ? r.json() : null).then(d => { cosmos = d; rebuild(); }).catch(() => {});

    // ---- 相机 ----
    const cam = { cx: 0.5, cy: 0.5, zoom: 2.6 }; // 默认停在理想星点大小，可自由缩放到 1~36 倍
    const clampCam = () => {
      cam.zoom = Math.min(ZOOM_MAX, Math.max(ZOOM_MIN, cam.zoom));
      const half = 0.5 / cam.zoom;
      cam.cx = cam.zoom > 1 ? Math.min(1 - half, Math.max(half, cam.cx)) : 0.5;
      cam.cy = cam.zoom > 1 ? Math.min(1 - half, Math.max(half, cam.cy)) : 0.5;
    };
    const toScreen = (fx, fy) => [(fx - cam.cx) * W * cam.zoom + W / 2, (fy - cam.cy) * H * cam.zoom + H / 2];
    const toWorld = (mx, my) => [cam.cx + (mx - W / 2) / (W * cam.zoom), cam.cy + (my - H / 2) / (H * cam.zoom)];

    // ---- 节点 ----
    let nodes = [];
    let grid = new Map();
    let philNodeByName = new Map();
    let quotesByPhil = new Map(), cihaiByPhil = new Map(), quotesBySchool = new Map(), cihaiBySchool = new Map();
    let booksByPhil = new Map(), booksBySchool = new Map(), subsByParent = new Map(), philBySub = new Map(), subByName = new Map();
    let centerOf = new Map();
    const CELL = 0.045;
    const cellKey = (fx, fy) => `${Math.floor(fx / CELL)}:${Math.floor(fy / CELL)}`;

    function rebuild() {
      nodes = [];
      const centers = clusterCenters(175, rand);
      centerOf = new Map();

      cosmos?.schools?.forEach((s, i) => {
        const [cx, cy] = centers[i] || [rand() * 0.9 + 0.05, rand() * 0.88 + 0.06];
        centerOf.set(s.n, [cx, cy]);
        nodes.push({
          t: 'school', name: s.n, fx: cx, fy: cy,
          fr: Math.min(5.2, 3.0 + (s.q.length + s.c.length) / 280),
          rgb: [232, 227, 217], phase: rand() * 6.28, tw: 0.3, pri: 3, soft: true,
          nq: s.q.length, nc: s.c.length,
        });
      });
      const posNear = (name, sigma) => {
        const c = centerOf.get(name);
        if (!c) return null;
        return [clamp01(c[0] + gauss(rand) * sigma), clamp01(c[1] + gauss(rand) * sigma * 0.8)];
      };

      if (cosmos?.tags) {
        for (const [tag, parent] of Object.entries(cosmos.tags)) {
          if (tag === parent) continue;
          const p = posNear(parent, 0.022) || [rand(), rand()];
          nodes.push({
            t: 'sub', name: tag, parent, fx: p[0], fy: p[1],
            fr: 1.6 + rand() * 0.5, rgb: SUB_RGB, phase: rand() * 6.28, tw: 0.45, pri: 2.2, soft: true,
          });
        }
      }

      const philCluster = new Map(); //哲人 -> 父流派名
      for (const p0 of philosophers) {
        const tags = (p0.school || '').split(/[、，,;/·]+/).map(s => s.trim()).filter(s => s.length >= 2);
        let parent = null;
        for (const tg of tags) { if (cosmos?.tags?.[tg]) { parent = cosmos.tags[tg]; break; } }
        if (parent) philCluster.set(p0.name, parent);
        const base = parent ? posNear(parent, 0.030) : null;
        const rank = p0.rank || 30;
        const n = {
          t: 'philosopher', name: p0.name, region: p0.region, school: p0.school, parent,
          fx: base ? base[0] : clamp01(rand()), fy: base ? base[1] : clamp01(rand()),
          fr: Math.min(3.0, Math.max(1.2, 1.2 + (rank - 30) / 20)),
          rgb: REGION_COLOR[p0.region] || [217, 179, 108],
          phase: rand() * 6.28, tw: 0.5 + rand() * 0.6, pri: 1.6,
        };
        nodes.push(n);
      }
      philNodeByName = new Map(nodes.filter(n => n.t === 'philosopher').map(n => [n.name, n]));

      for (const b of books) {
        const host = philNodeByName.get((b.author || '').split('/')[0].trim()) || philNodeByName.get((b.author || '').trim());
        let fx, fy;
        if (host) {
          const ang = rand() * 6.28, orb = 0.008 + rand() * 0.010;
          fx = host.fx + Math.cos(ang) * orb; fy = host.fy + Math.sin(ang) * orb * 1.5;
        } else {
          const pc = cosmos?.bp?.[b.id] ? centerOf.get(cosmos.bp[b.id]) : null;
          if (pc) { fx = pc[0] + gauss(rand) * 0.05; fy = pc[1] + gauss(rand) * 0.04; }
          else { fx = rand(); fy = rand(); }
        }
        nodes.push({
          t: 'book', name: b.title, id: b.id, fx: clamp01(fx), fy: clamp01(fy),
          fr: 0.9 + rand() * 0.5, rgb: QUOTE_RGB, phase: rand() * 6.28, tw: 0.25, pri: 1, dim: true,
          author: host?.name || null, parent: cosmos?.bp?.[b.id] || null,
        });
      }

      if (cosmos?.schools) {
        for (const s of cosmos.schools) {
          const c = centerOf.get(s.n); if (!c) continue;
          for (const q of s.q) {
            const field = rand() < 0.3; // 30% 全域散布，密密麻麻铺满
            const fx = field ? rand() : clamp01(c[0] + gauss(rand) * 0.040);
            const fy = field ? rand() : clamp01(c[1] + gauss(rand) * 0.032);
            nodes.push({
              t: 'quote', name: q[0], author: q[1], phil: q[2], book: q[3], parent: s.n,
              fx, fy, low: rand() < 0.4,
              fr: 0.85 + rand() * 0.45, rgb: QUOTE_RGB, phase: rand() * 6.28, tw: 0.4, pri: 0.6, dim: true,
            });
          }
          for (const w of s.c) {
            const field = rand() < 0.3;
            const fx = field ? rand() : clamp01(c[0] + gauss(rand) * 0.044);
            const fy = field ? rand() : clamp01(c[1] + gauss(rand) * 0.036);
            nodes.push({
              t: 'cihai', name: w[0], sub: w[1], phil: w[2], book: w[3], parent: s.n,
              fx, fy, low: rand() < 0.4,
              fr: 1.25 + rand() * 0.4, rgb: CIHAI_RGB, phase: rand() * 6.28, tw: 0.55, pri: 0.7,
            });
          }
        }
      }

      QUESTIONS.slice(0, 12).forEach(q => {
        nodes.push({
          t: 'question', name: q.title, sub: q.category, id: q.id,
          fx: 0.06 + rand() * 0.88, fy: 0.06 + rand() * 0.88,
          fr: 2.2, rgb: [240, 230, 210], phase: rand() * 6.28, tw: 1.0, pri: 4,
        });
      });

      for (const n of nodes) {
        const visual=mulberry32(hashStr(n.t+':'+n.name));const p=visual();
        const fine=n.t==='quote'||n.t==='cihai'||n.t==='book';
        n.core=fine?.40+p*p*.48:n.t==='sub'?.35+p*.38:n.t==='school'?.83+p*.52:.38+p*p*p*1.08;
        n.light=fine?.43+Math.pow(visual(),1.5)*.47:.58+visual()*.37;
        if(n.t==='philosopher'&&n.fr>2.45){n.core=1.30+visual()*.7;n.light=1.12;}
        n.skyRGB=visual()<.075?[211,222,236]:visual()<.08?[227,211,182]:[224,225,226];
        n.skyTwinkle=visual()<.035;
      }

      grid = new Map();
      for (const n of nodes) {
        const k = cellKey(n.fx, n.fy);
        if (!grid.has(k)) grid.set(k, []);
        grid.get(k).push(n);
      }
      philNodeByName = new Map(nodes.filter(n => n.t === 'philosopher').map(n => [n.name, n]));
      indexRelations();
    }
    rebuild();

    // ---- 关系邻接（11 类连线，点亮用） ----
    function indexRelations() {
      quotesByPhil = new Map(); cihaiByPhil = new Map(); quotesBySchool = new Map(); cihaiBySchool = new Map();
      booksByPhil = new Map(); booksBySchool = new Map(); subsByParent = new Map(); philBySub = new Map(); subByName = new Map();
      const push = (m, k, v) => { if (!k) return; if (!m.has(k)) m.set(k, []); m.get(k).push(v); };
      for (const n of nodes) {
        if (n.t === 'quote') { push(quotesByPhil, n.phil, n); push(quotesBySchool, n.parent, n); }
        else if (n.t === 'cihai') { push(cihaiByPhil, n.phil, n); push(cihaiBySchool, n.parent, n); }
        else if (n.t === 'book') { push(booksByPhil, n.author, n); push(booksBySchool, n.parent, n); }
        else if (n.t === 'sub') { push(subsByParent, n.parent, n); subByName.set(n.name, n); }
        else if (n.t === 'philosopher') {
          for (const tg of (n.school || '').split(/[、，,;/·]+/).map(s => s.trim())) {
            if (tg && cosmos?.tags?.[tg] && cosmos.tags[tg] !== tg) push(philBySub, tg, n);
          }
        }
      }
    }
    function parentOf(schoolStr) {
      for (const tg of (schoolStr || '').split(/[、，,;/·]+/).map(s => s.trim())) {
        if (tg && cosmos?.tags?.[tg]) return cosmos.tags[tg];
      }
      return null;
    }
    function schoolNode(name) {
      const c = centerOf.get(name);
      return c ? nodes.find(n => n.t === 'school' && n.name === name) : null;
    }

    function neighbors(node) {
      const out = [];
      if (node.t === 'philosopher') {
        for (const c of network?.[node.name]?.connections?.slice(0, 6) || []) out.push(philNodeByName.get(c.name));
        const hub = parentOf(node.school);
        if (hub) out.push(schoolNode(hub));
        for (const tg of (node.school || '').split(/[、，,;/·]+/).map(s => s.trim()).slice(0, 3)) out.push(subByName.get(tg));
        for (const w of (cihaiByPhil.get(node.name) || []).slice(0, 3)) out.push(w);
        for (const q of (quotesByPhil.get(node.name) || []).slice(0, 3)) out.push(q);
        for (const b of (booksByPhil.get(node.name) || []).slice(0, 3)) out.push(b);
      } else if (node.t === 'school') {
        for (const m of nodes.filter(n => n.t === 'philosopher' && (n.school || '').split(/[、，,;/·]+/).map(s => s.trim()).includes(node.name)).sort((a, b) => b.fr - a.fr).slice(0, 8)) out.push(m);
        for (const s of (subsByParent.get(node.name) || []).slice(0, 4)) out.push(s);
        for (const q of (quotesBySchool.get(node.name) || []).slice(0, 4)) out.push(q);
        for (const w of (cihaiBySchool.get(node.name) || []).slice(0, 4)) out.push(w);
        for (const b of (booksBySchool.get(node.name) || []).slice(0, 4)) out.push(b);
      } else if (node.t === 'sub') {
        out.push(schoolNode(node.parent));
        for (const p of (philBySub.get(node.name) || []).slice(0, 8)) out.push(p);
      } else if (node.t === 'book') {
        if (node.author) out.push(philNodeByName.get(node.author));
        out.push(schoolNode(node.parent));
        for (const q of nodes.filter(n => n.t === 'quote' && n.book === node.id).slice(0, 3)) out.push(q);
        for (const w of nodes.filter(n => n.t === 'cihai' && n.book === node.id).slice(0, 3)) out.push(w);
      } else if (node.t === 'quote' || node.t === 'cihai') {
        out.push(schoolNode(node.parent));
        if (node.phil) out.push(philNodeByName.get(node.phil));
        if (node.book) out.push(nodes.find(n => n.t === 'book' && n.id === node.book));
      }
      return out.filter(Boolean);
    }

    // 关系点亮：只点亮与选中星直接相关的星（一跳），依次亮起
    function adjacency(node) {
      const lit = new Map([[node, 0]]);
      const pairs = [];
      let budget = 30;
      let delay = 0.1;
      for (const nb of neighbors(node)) {
        if (!nb || lit.has(nb) || budget <= 0) continue;
        budget--;
        delay += 0.07;
        lit.set(nb, delay);
        pairs.push([node, nb, delay]);
      }
      return { pairs, lit };
    }

    // ---- 尘埃 ----
    const dust = [];
    for (let i = 0; i < 1800; i++) dust.push({ fx: rand(), fy: rand(), r: 0.28 + rand() * 0.55, phase: rand() * 6.28 });
    for (let i = 0; i < 14; i++) dust.push({ fx: rand(), fy: rand(), r: 0.8 + rand() * 0.5, phase: rand() * 6.28 });

    // ---- 精灵 ----
    const spriteCache = new Map();
    const sprite = (rgb, fr, soft) => {
      const key = `${rgb.join(',')}-${Math.round(fr)}-${soft ? 1 : 0}`;
      if (!spriteCache.has(key)) spriteCache.set(key, makeSprite(rgb, soft ? 96 : 40, soft));
      return spriteCache.get(key);
    };

    // ---- 画布 ----
    let W = 0, H = 0, dpr = 1;
    const resize = () => {
      // 高分屏（4K/dpr2）下 8100 星点全帧重绘会掉帧：dpr 上限 1.5，光晕精灵几乎无损
      dpr = Math.min(1.5, window.devicePixelRatio || 1);
      W = wrap.clientWidth; H = wrap.clientHeight;
      canvas.width = W * dpr; canvas.height = H * dpr;
      canvas.style.width = W + 'px'; canvas.style.height = H + 'px';
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    };
    resize();
    const ro = new ResizeObserver(resize);
    ro.observe(wrap);

    // ---- 交互状态 ----
    let hovered = null, selected = null;
    let labelNodes=[],labelKey='';
    const hideTip=()=>{if(tipRef.current)tipRef.current.hidden=true;};
    let lastActiveRef = { current: 0 };
    let frames = 0;
    const isLit = n => litMap.has(n);
    let litPairs = [], litMap = new Map(), litAt = 0;
    let network = null;
    fetch('/philosopher_network.json').then(r => r.ok ? r.json() : null).then(d => { network = d; }).catch(() => {});

    function findHover(mx, my) {
      const [wx, wy] = toWorld(mx, my);
      let best = null, bestScore = 1e9;
      const cx = Math.floor(wx / CELL), cy = Math.floor(wy / CELL);
      const span = Math.ceil(14 / (W * cam.zoom) / CELL) + 1;
      for (let gx = cx - span; gx <= cx + span; gx++) {
        for (let gy = cy - span; gy <= cy + span; gy++) {
          const cell = grid.get(`${gx}:${gy}`);
          if (!cell) continue;
          for (const n of cell) {
            // 选中期间：只有选中星与关系链上的星可悬停/点击，其余暂时失效
            if (selected && n !== selected && !litMap.has(n)) continue;
            const [sx, sy] = toScreen(n.fx, n.fy);
            const d = Math.hypot(sx - mx, sy - my);
            // 点亮的星命中半径加大（+9px），确保点得中
            const r = (n.soft ? 18 : n.t === 'question' ? 16 : n.t === 'quote' || n.t === 'cihai' ? Math.max(9, 4 * cam.zoom) : 11)
              + n.fr * cam.zoom * 0.4
              + (selected && litMap.has(n) ? 9 : 0);
            if (d < r) {
              const score = d - n.pri * 10 - (litMap.has(n) ? 4 : 0); // 点亮的星优先命中
              if (score < bestScore) { bestScore = score; best = n; }
            }
          }
        }
      }
      return best;
    }

    function draw(t, schedule = true) {
      // 闲置降频：整帧跳过（含清屏），画面保持上一帧内容——节流且无频闪
      const idle = interactiveRef.current && t - lastActiveRef.current > 1200;
      frames++;
      if (schedule && idle && !reduced && frames % 3 !== 0) { raf = requestAnimationFrame(draw); return; }
      ctx.clearRect(0, 0, W, H);
      const raw = Math.min(1, Math.max(0, (t - activateAtRef.current) / 2000));
      const dim = activeRef.current ? 0.20 + 0.80 * (raw * raw * (3 - 2 * raw)) : 0.20;
      const z = cam.zoom;

      const visible = [[0, 0], [1, 1]];
      const [wx0, wy0] = toWorld(0, 0), [wx1, wy1] = toWorld(W, H);
      visible[0] = [wx0, wy0]; visible[1] = [wx1, wy1];

      // 尘埃（缩放时按视野裁剪）
      for (const d of dust) {
        if (d.fx < visible[0][0] - 0.02 || d.fx > visible[1][0] + 0.02 || d.fy < visible[0][1] - 0.02 || d.fy > visible[1][1] + 0.02) continue;
        const a = (0.20 + 0.10 * Math.sin(t * 0.0009 + d.phase)) * dim;
        ctx.fillStyle = `${BONE}${a})`;
        const [sx, sy] = toScreen(d.fx, d.fy);
        ctx.fillRect(sx, sy, d.r * Math.min(2, z * 0.8), d.r * Math.min(2, z * 0.8));
      }

      // 选中：关系线延伸动画（无圆圈；非相关星星整体变淡——参照谱系页「按关联」）
      if (selected) {
        const since = (t - litAt) / 1000;
        for (const [a, b, delay] of litPairs) {
          const k = Math.min(1, Math.max(0, (since - delay) / 0.6));
          if (k <= 0) continue;
          const [ax, ay] = toScreen(a.fx, a.fy), [bx, by] = toScreen(b.fx, b.fy);
          ctx.strokeStyle = `rgba(217,179,108,${0.55 * k * dim})`;
          ctx.lineWidth = 1;
          ctx.beginPath(); ctx.moveTo(ax, ay); ctx.lineTo(ax + (bx - ax) * k, ay + (by - ay) * k); ctx.stroke();
        }
      }

      for(const star of birthStarsRef?.current||[]){
        const [x,y]=toScreen(star.fx,star.fy);if(x<0||x>W||y<0||y>H)continue;
        ctx.fillStyle=`rgba(${star.rgb.join(',')},${star.a*dim})`;
        ctx.beginPath();ctx.arc(x,y,star.r*(.8+.2*Math.sqrt(z/star.zoom)),0,Math.PI*2);ctx.fill();
      }
      for(const n of nodes){
        const [x,y]=toScreen(n.fx,n.fy);if(x<-20||x>W+20||y<-20||y>H+20)continue;
        const lit=isLit(n),hot=n===hovered||n===selected;
        const density=.54+.24*Math.min(1.8,Math.exp(-((n.fx-.25)**2/.025+(n.fy-.30)**2/.045))+Math.exp(-((n.fx-.72)**2/.07+(n.fy-.66)**2/.015))+Math.exp(-((n.fx-.58)**2/.05+(n.fy-.22)**2/.027)))+.075*Math.sin(18*n.fx+5*n.fy)*Math.sin(13*n.fy-3*n.fx);
        let alpha=n.light*density*1.8*dim;
        if(selected&&!lit)alpha*=.72;
        if(n.skyTwinkle&&!reduced)alpha*=.88+.12*Math.sin(t*.0007+n.phase);
        let radius=n.core*(.85+.23*Math.sqrt(z));
        if(lit){alpha=.98*dim;radius=Math.max(1.4,radius*1.3);}
        if(hot)radius*=1.22;
        if(radius>.9){const size=(radius*9+3)*.85;ctx.globalAlpha=Math.min(1,alpha)*(lit?.7:.4);ctx.drawImage(sprite(n.skyRGB,n.fr,false),x-size/2,y-size/2,size,size);ctx.globalAlpha=1;}
        ctx.fillStyle=`rgba(${lit?'232,210,165':n.skyRGB.join(',')},${Math.min(.96,alpha)})`;
        ctx.beginPath();ctx.arc(x,y,radius,0,Math.PI*2);ctx.fill();
      }
      if(selected&&labelsRef.current&&tipRef.current){
        const key=[cam.cx,cam.cy,cam.zoom,W,H,tipRef.current.offsetHeight].join('/');
        if(key!==labelKey){labelKey=key;layoutHomeSkyLabels(labelsRef.current,tipRef.current,labelNodes,W,H,toScreen);}
      }
      if (schedule && !reduced) raf = requestAnimationFrame(draw);
    }
    const bridge={
      getStars:()=>nodes.map(n=>{const [x,y]=toScreen(n.fx,n.fy);return{x,y,r:Math.max(.5,Math.min(1.25,n.core*(.85+.23*Math.sqrt(cam.zoom)))),a:Math.max(.45,Math.min(.88,n.light)),rgb:n.skyRGB};}).filter(p=>p.x>20&&p.x<W-20&&p.y>102&&p.y<H-75),
      toWorld,zoom:()=>cam.zoom,renderFrame:()=>draw(performance.now(),false),
    };
    if(sceneRef)sceneRef.current=bridge;
    let raf = requestAnimationFrame(draw);

    // ---- 指针交互：拖拽平移 / 滚轮缩放 / 悬停 / 点击 ----
    let dragging = false, moved = 0, lastP = null;
    function onDown(e) {
      if(!activeRef.current||!interactiveRef.current)return;
      dragging = true; moved = 0; lastP = { x: e.clientX, y: e.clientY };
    }
    function onMove(e) {
      if (!activeRef.current || !interactiveRef.current) return;
      lastActiveRef.current = performance.now();
      if (dragging && lastP) {
        const dx = e.clientX - lastP.x, dy = e.clientY - lastP.y;
        moved += Math.abs(dx) + Math.abs(dy);
        lastP = { x: e.clientX, y: e.clientY };
        cam.cx -= dx / (W * cam.zoom); cam.cy -= dy / (H * cam.zoom);
        clampCam();
        if (moved > 5) {
          hovered = null;
          if (!selected && tipRef.current) hideTip(); // 选中期间固定卡保持
          canvas.style.cursor = 'grabbing';
        }
        return;
      }
      if (selected) { canvas.style.cursor = 'default'; return; } // 选中期间提示卡固定，无悬停
      const r = canvas.getBoundingClientRect();
      const mx = e.clientX - r.left, my = e.clientY - r.top;
      const hit = findHover(mx, my);
      if (hit !== hovered) {
        hovered = hit;
        canvas.style.cursor = hit ? 'pointer' : 'default';
        if (hit) setTip(hit); else if (tipRef.current) hideTip();
      }

    }

    function setTip(hit) {
      if (!tipRef.current) return;
      const meta = hit.t === 'philosopher' ? [hit.region, (hit.school || '').split(/[、，,;/]+/)[0]].filter(Boolean).join(' · ')
        : hit.t === 'school' ? `${hit.nq} 金句 · ${hit.nc} 辞海`
        : hit.t === 'sub' ? `属于「${hit.parent}」`
        : hit.t === 'quote' ? (hit.author ? `—— ${hit.author}` : '')
        : hit.sub || '';
      const title = hit.t === 'quote' && hit.name.length > 42 ? hit.name.slice(0, 42) + '……' : hit.name;
      tipRef.current.hidden=false;
      tipRef.current.style.pointerEvents=selected?'auto':'none';
      tipRef.current.innerHTML=`<em>${TYPE_LABEL[hit.t]}</em><strong>${escapeHTML(title)}</strong>${meta?`<span>${escapeHTML(meta)}</span>`:''}${selected?'<button class="home-cosmos-open" type="button" data-open>查看'+(hit.t==='quote'?'出处':hit.t==='cihai'?'辞条':TYPE_LABEL[hit.t])+' ↗</button>':'<i>点击点亮关系</i>'}`;
    }
    function selectStar(hit){
      selected=hit;const {pairs,lit}=adjacency(hit);litPairs=pairs;litMap=lit;litAt=performance.now();setTip(hit);
      labelNodes=[...lit.keys()].filter(n=>n!==hit);labelKey='';
      labelsRef.current.innerHTML=labelNodes.map((n,i)=>`<button type="button" data-node="${i}" aria-label="点亮${escapeHTML(n.name)}">${escapeHTML(n.name)}</button>`).join('');
      draw(performance.now(),false);
    }
    function destination(hit){
      if(hit.t==='philosopher')return `/author/${encodeURIComponent(hit.name)}`;
      if(hit.t==='school')return `/school/${encodeURIComponent(hit.name)}`;
      if(hit.t==='book')return `/book/${hit.id}`;
      if(hit.t==='question')return `/genealogy?view=question&question=${hit.id}`;
      return `/school/${encodeURIComponent(hit.parent)}`+(hit.t==='quote'?'#school-quotes':hit.t==='cihai'?'#school-concepts':'');
    }
    const onTipClick=e=>{if(e.target.closest('[data-open]')&&selected)navigate(destination(selected));};
    const onLabelClick=e=>{const button=e.target.closest('[data-node]');if(button)selectStar(labelNodes[Number(button.dataset.node)]);};
    const onEscape=e=>{if(e.key==='Escape'){selected=null;litPairs=[];litMap=new Map();hideTip();labelsRef.current.innerHTML='';draw(performance.now(),false);}};
    tipRef.current.addEventListener('click',onTipClick);
    labelsRef.current.addEventListener('click',onLabelClick);
    wrap.addEventListener('keydown',onEscape);
    function onUp() { dragging = false; canvas.style.cursor = hovered ? 'pointer' : 'default'; }
    function onLeave() {
      dragging = false; hovered = null;
      canvas.style.cursor = 'default';
      if (!selected && tipRef.current) hideTip();
    }
    function onWheel(e) {
      if (!activeRef.current || !interactiveRef.current) return;
      lastActiveRef.current = performance.now();
      e.preventDefault();
      const r = canvas.getBoundingClientRect();
      const mx = e.clientX - r.left, my = e.clientY - r.top;
      const [wx, wy] = toWorld(mx, my);
      cam.zoom = Math.min(ZOOM_MAX, Math.max(ZOOM_MIN, cam.zoom * Math.exp(-e.deltaY * 0.0013)));
      cam.cx = wx - (mx - W / 2) / (W * cam.zoom);
      cam.cy = wy - (my - H / 2) / (H * cam.zoom);
      clampCam();
    }
    function onClick(e) {
      if (!activeRef.current || !interactiveRef.current) return;
      lastActiveRef.current = performance.now();
      if (moved > 5) return; // 拖拽不算点击
      const r = canvas.getBoundingClientRect();
      const hit = findHover(e.clientX - r.left, e.clientY - r.top);
      if (!hit) { // 点中选中星系之外的任何地方 → 取消选中，恢复全亮（拖动除外）
        selected = null; litPairs = []; litMap = new Map(); labelsRef.current.innerHTML='';
        if (tipRef.current) hideTip();
        return;
      }
      if(hit===selected){navigate(destination(hit));return;}
      selectStar(hit);

    }
    canvas.addEventListener('pointerdown', onDown);
    canvas.addEventListener('pointermove', onMove);
    canvas.addEventListener('pointerup', onUp);
    canvas.addEventListener('pointerleave', onLeave);
    canvas.addEventListener('wheel', onWheel, { passive: false });
    canvas.addEventListener('click', onClick);

    return () => {
      cancelAnimationFrame(raf);
      if(sceneRef?.current===bridge)sceneRef.current=null;
      tipElement?.removeEventListener('click',onTipClick);
      labelsElement?.removeEventListener('click',onLabelClick);
      wrap.removeEventListener('keydown',onEscape);
      ro.disconnect();
      canvas.removeEventListener('pointerdown', onDown);
      canvas.removeEventListener('pointermove', onMove);
      canvas.removeEventListener('pointerup', onUp);
      canvas.removeEventListener('pointerleave', onLeave);
      canvas.removeEventListener('wheel', onWheel);
      canvas.removeEventListener('click', onClick);
    };
  }, [philosophers, books, navigate, sceneRef, birthStarsRef]);

  return (
    <div className={`home-cosmos${active && philosophers?.length && books?.length ? ' is-active' : ''}`} ref={wrapRef} aria-label="哲学宇宙星图：滚轮缩放，拖拽平移，点击星星点亮关系链">
      <svg className="home-opening-sky" viewBox="0 0 1440 900" preserveAspectRatio="xMidYMid slice" aria-hidden="true" focusable="false">
        {OPENING_STARS.map((star,i)=><circle key={i} cx={star.x} cy={star.y} r={star.r} fill={star.color} opacity={star.alpha}/>)}
      </svg>
      <canvas ref={canvasRef} />
      <div className="home-cosmos-labels" ref={labelsRef} />
      <div className="home-cosmos-tip" ref={tipRef} role="status" hidden />
    </div>
  );
}
