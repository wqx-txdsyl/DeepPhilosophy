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
const smooth = (a, b, v) => { const t = Math.min(1, Math.max(0, (v - a) / (b - a))); return t * t * (3 - 2 * t); };

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
    g.addColorStop(0.38, `rgba(${r},${gc},${b},0.95)`);
    g.addColorStop(0.7, `rgba(${r},${gc},${b},0.28)`);
  }
  g.addColorStop(1, `rgba(${r},${gc},${b},0)`);
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, size, size);
  return c;
}

const TYPE_LABEL = { philosopher: '哲人', school: '流派', sub: '子流派', book: '著作', question: '思想之问', quote: '金句', cihai: '辞海' };

export default function HomeCosmos({ philosophers, books, active = false }) {
  const navigate = useNavigate();
  const wrapRef = useRef(null);
  const canvasRef = useRef(null);
  const tipRef = useRef(null);
  const activeRef = useRef(active);
  const activateAtRef = useRef(0);
  useEffect(() => {
    if (active && !activeRef.current) activateAtRef.current = performance.now();
    activeRef.current = active;
  }, [active]);

  useEffect(() => {
    const wrap = wrapRef.current, canvas = canvasRef.current;
    if (!wrap || !canvas || !philosophers?.length || !books?.length) return;
    const ctx = canvas.getContext('2d');
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
    for (let i = 0; i < 650; i++) dust.push({ fx: rand(), fy: rand(), r: 0.6 + rand() * 1.1, phase: rand() * 6.28 });
    for (let i = 0; i < 14; i++) dust.push({ fx: rand(), fy: rand(), r: 1.7 + rand() * 0.8, phase: rand() * 6.28 });

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

    function draw(t) {
      ctx.clearRect(0, 0, W, H);
      if (!activeRef.current) { if (!reduced) raf = requestAnimationFrame(draw); return; }
      const raw = Math.min(1, Math.max(0, (t - activateAtRef.current) / 2000));
      const dim = 0.35 + 0.65 * (raw * raw * (3 - 2 * raw));
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

      // 全层级从概貌起可见（微星为暗星底纹），缩放使其变亮变大——密密麻麻铺满
      const layerAlpha = {
        quote: 0.30 + 0.70 * smooth(1, 3, z),
        cihai: 0.32 + 0.68 * smooth(1, 3, z),
        book: 0.38 + 0.62 * smooth(1, 2.5, z),
        sub: 0.45 + 0.55 * smooth(1, 2, z),
      };

      const idle = t - lastActiveRef.current > 1200; // 闲置时降到 ~15fps，微飘仍动
      frames++;
      for (const n of nodes) {
        if (idle && n.low && frames % 3 !== 0) continue;         // 闲置抽稀
        if (z < 1.9 && n.low && !isLit(n)) continue;             // 概貌抽稀（放大浮现）
        const [sx, sy] = toScreen(n.fx, n.fy);
        const margin = 60 * z;
        if (sx < -margin || sx > W + margin || sy < -margin || sy > H + margin) continue;
        const isHover = n === hovered, isSel = n === selected;
        let alpha = (n.dim ? 0.55 : n.t === 'sub' ? 0.62 : n.soft ? 0.9 : 0.78) * (layerAlpha[n.t] ?? 1);
        alpha += reduced ? 0 : Math.sin(t * 0.0011 * n.tw + n.phase) * 0.08;
        if (isHover || isSel) alpha = 1;
        // 选中态（参照谱系页「按关联」）：选中的与关系链上的高亮放大，其余退为暗星
        if (selected) {
          const related = litMap.has(n);
          const k = Math.min(1, Math.max(0, ((t - litAt) / 1000) / 0.4));
          if (related) alpha = 1;
          else alpha *= 1 - 0.75 * k; // 淡至 25%，仍可见
        }

        const litBoost = selected && (isSel || litMap.has(n)) ? 1.3 : 1;
        const size = n.fr * (isHover || isSel ? 5 : n.soft ? 4 : 3.6) * (0.55 + 0.45 * Math.min(3.2, z)) * (0.6 + 0.4 * dim) * 1.15 * litBoost;

        const fa = Math.max(0.03, Math.min(1, alpha)) * dim;
        if (fa >= 0.045) { // 透明度过低的星跳过绘制（高分屏性能）
          ctx.globalAlpha = fa;
          ctx.drawImage(sprite(n.rgb, n.fr, n.soft), sx - size / 2, sy - size / 2, size, size);
          ctx.globalAlpha = 1;
        }
      }
      // 固定提示卡跟随选中星
      if (selected && tipRef.current) {
        const [sx, sy] = toScreen(selected.fx, selected.fy);
        tipRef.current.style.left = Math.min(Math.max(sx + 14, 8), W - 248) + 'px';
        tipRef.current.style.top = Math.max(8, sy - 14) + 'px';
      }
      if (!reduced) raf = requestAnimationFrame(draw);
    }
    let raf = requestAnimationFrame(draw);

    // ---- 指针交互：拖拽平移 / 滚轮缩放 / 悬停 / 点击 ----
    let dragging = false, moved = 0, lastP = null;
    function onDown(e) {
      dragging = true; moved = 0; lastP = { x: e.clientX, y: e.clientY };
    }
    function onMove(e) {
      if (!activeRef.current) return;
      lastActiveRef.current = performance.now();
      if (selected) { canvas.style.cursor = 'pointer'; return; } // 提示卡已钉在选中星上
      if (dragging && lastP) {
        const dx = e.clientX - lastP.x, dy = e.clientY - lastP.y;
        moved += Math.abs(dx) + Math.abs(dy);
        lastP = { x: e.clientX, y: e.clientY };
        cam.cx -= dx / (W * cam.zoom); cam.cy -= dy / (H * cam.zoom);
        clampCam();
        if (moved > 5) { hovered = null; if (tipRef.current) tipRef.current.style.opacity = '0'; canvas.style.cursor = 'grabbing'; }
        return;
      }
      const r = canvas.getBoundingClientRect();
      const mx = e.clientX - r.left, my = e.clientY - r.top;
      const hit = findHover(mx, my);
      if (hit !== hovered) {
        hovered = hit;
        canvas.style.cursor = hit ? 'pointer' : 'default';
        if (hit) setTip(hit); else if (tipRef.current) tipRef.current.style.opacity = '0';
      }
      if (tipRef.current && hovered && !selected) {
        tipRef.current.style.left = Math.min(mx + 16, W - 248) + 'px';
        tipRef.current.style.top = Math.max(10, my - 14) + 'px';
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
      tipRef.current.innerHTML = `<em>${TYPE_LABEL[hit.t]}</em><strong>${title}</strong>${meta ? `<span>${meta}</span>` : ''}<i>${hit.t === 'quote' ? '点击查看出处' : hit.t === 'cihai' ? '点击查看辞条' : '点击点亮'}</i>`;
      tipRef.current.style.opacity = '1';
    }
    function onUp() { dragging = false; canvas.style.cursor = hovered ? 'pointer' : 'default'; }
    function onLeave() {
      dragging = false; hovered = null;
      canvas.style.cursor = 'default';
      if (!selected && tipRef.current) tipRef.current.style.opacity = '0';
    }
    function onWheel(e) {
      if (!activeRef.current) return;
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
      if (!activeRef.current) return;
      lastActiveRef.current = performance.now();
      if (moved > 5) return; // 拖拽不算点击
      const r = canvas.getBoundingClientRect();
      const hit = findHover(e.clientX - r.left, e.clientY - r.top);
      if (!hit) { // 点中选中星系之外的任何地方 → 取消选中，恢复全亮（拖动除外）
        selected = null; litPairs = []; litMap = new Map();
        if (tipRef.current) tipRef.current.style.opacity = '0';
        return;
      }
      if (hit === selected) { // 二次点击同一颗 → 跳转
        if (hit.t === 'philosopher') navigate(`/author/${encodeURIComponent(hit.name)}`);
        else if (hit.t === 'school') navigate(`/school/${encodeURIComponent(hit.name)}`);
        else if (hit.t === 'sub') navigate(`/school/${encodeURIComponent(hit.parent)}`);
        else if (hit.t === 'book') navigate(`/book/${hit.id}`);
        else if (hit.t === 'quote') navigate(`/school/${encodeURIComponent(hit.parent)}#school-quotes`);
        else if (hit.t === 'cihai') navigate(`/school/${encodeURIComponent(hit.parent)}#school-concepts`);
        else if (hit.t === 'question') navigate(`/genealogy?view=question&question=${hit.id}`);
        selected = null;
        return;
      }
      // 首次点击：点亮关系链，提示卡固定在这颗星上
      selected = hit;
      const { pairs, lit } = adjacency(hit);
      litPairs = pairs; litMap = lit; litAt = performance.now();
      setTip(hit);
    }
    canvas.addEventListener('pointerdown', onDown);
    canvas.addEventListener('pointermove', onMove);
    canvas.addEventListener('pointerup', onUp);
    canvas.addEventListener('pointerleave', onLeave);
    canvas.addEventListener('wheel', onWheel, { passive: false });
    canvas.addEventListener('click', onClick);

    return () => {
      cancelAnimationFrame(raf);
      ro.disconnect();
      canvas.removeEventListener('pointerdown', onDown);
      canvas.removeEventListener('pointermove', onMove);
      canvas.removeEventListener('pointerup', onUp);
      canvas.removeEventListener('pointerleave', onLeave);
      canvas.removeEventListener('wheel', onWheel);
      canvas.removeEventListener('click', onClick);
    };
  }, [philosophers, books, navigate]);

  return (
    <div className="home-cosmos" ref={wrapRef} aria-label="哲学宇宙星图：滚轮缩放，拖拽平移，点击星星点亮关系链">
      <canvas ref={canvasRef} />
      <div className="home-cosmos-tip" ref={tipRef} role="status" />
    </div>
  );
}
