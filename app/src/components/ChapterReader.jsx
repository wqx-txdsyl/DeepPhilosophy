/**
 * ChapterReader — 章节滚动式阅读器
 * 每章一页，上下滑动，底部切换章节
 * 阅读体验: 背景色 4 档 / 字号 A-/A+ / 行距 3 档 / 自动阅读(速度可调, 交互即暂停, localStorage 持久化)
 */
import { Fragment, useRef, useEffect, useState, useCallback, useMemo } from 'react';

// 阅读背景主题
const BG_THEMES = {
  default: { bg: 'var(--card-bg)', color: 'var(--ink)', name: '默认' },
  paper:   { bg: '#f6f1e3',  color: '#3d3a33', name: '米黄纸' },
  green:   { bg: '#e6efe3',  color: '#2f3a2e', name: '护眼绿' },
  night:   { bg: '#202124',  color: '#d8d8dc', name: '夜间' },
};
const AUTO_SPEEDS = { slow: 45, medium: 80, fast: 130 };   // px/s
const SPEED_LABEL = { slow: '慢', medium: '中', fast: '快' };

// 章内图片直连 OSS（跳过 worker 302 两跳：worker 响应 ~1.8s + 重定向，直连单跳 ~0.2s）
// 章节 JSON 里的 src 为 /api/books/{bid}/image/{name}.webp → https://deepphilosophy.oss-cn-shanghai.aliyuncs.com/book_images/{name}
const OSS_IMAGE_BASE = 'https://deepphilosophy.oss-cn-shanghai.aliyuncs.com/book_images';
// 章内图转 OSS 直链; resize 传宽度时走 OSS 图片处理按需缩放(显示 1.1em 的行内图
// 不必下载原图: 300KB → ~24KB)。不匹配 /api/ 路径的历史坏数据返回 null → 不渲染。
const toOssImage = (src, resize) => {
  if (!src) return null;
  const m = src.match(/\/api\/books\/[^/]+\/image\/([^/]+)$/);
  if (!m) return null;
  let u = `${OSS_IMAGE_BASE}/${m[1]}`;
  if (resize) u += `?x-oss-process=image/resize,w_${resize}`;
  return u;
};
// EPUB 打不出的字符（ä/ö/ü/ß/λ/ς/' 等）在转换时被映射为私用区占位符（U+E000–F8FF）。
// 浏览器把私用区字符当独立断行单元，会在它和后一字之间断行 → 占位符孤悬行尾、后字换行。
// 在占位符后补 word-joiner（U+2060，零宽不可见）：禁止其两侧断行，与后字绑定同行。
const gluePua = (t) => t.replace(/[-]/g, (c) => c + '⁠');

const loadSettings = () => {
  try {
    const s = JSON.parse(localStorage.getItem('dp_reader_settings') || '{}');
    return { bg: s.bg || 'default', fontSize: s.fontSize || 18, lineHeight: s.lineHeight || 2.0,
             autoSpeed: s.autoSpeed || 'medium' };
  } catch { return { bg: 'default', fontSize: 18, lineHeight: 2.0, autoSpeed: 'medium' }; }
};

// 标题级锚点定位：toc section 的 sec 常缺或指向页块首（标题嵌在块内）→ 改为
// 按标题文本在正文中定位，插入精确锚点 <span id="sec-{tocIdx}">，跳转不依赖 sec 数字。
const norm = (s) => (s || '').replace(/\s+/g, '');
// 候选短块与 section 标题的实质相似度：最长公共子串 + 头部一致取最大。
// 兜底分配只认"长得像标题"的短块 —— 脚注/注释/书目块(①、[12]、英文括注)
// 与标题相似度 0-1 分, 不分配, 避免锚点打在脚注上(上帝之城类正文无标题行)。
const titleSim = (blockText, title) => {
  const a = norm(blockText), b = norm(title);
  if (!a || !b) return 0;
  let best = 0;
  for (let i = 0; i < a.length; i++) {
    let k = 0;
    for (let j = 0; j < b.length; j++) {
      if (a[i + k] === b[j]) { k++; if (k > best) best = k; }
      else k = 0;
    }
  }
  let head = 0;
  const L = Math.min(a.length, b.length);
  while (head < L && a[head] === b[head]) head++;
  return Math.max(best, head);
};
// 在 text 中找 title 的原文起始下标；容 OCR 错字/截断（全文匹配失败退前 8 字前缀）
const findTitleOffset = (text, title) => {
  const nT = norm(text), nTi = norm(title);
  if (!nTi) return -1;
  let hit = nT.indexOf(nTi);
  if (hit < 0 && nTi.length > 8) hit = nT.indexOf(nTi.slice(0, 8));
  if (hit < 0) return -1;
  let cnt = 0;
  for (let i = 0; i < text.length; i++) {
    if (/\s/.test(text[i])) continue;
    if (cnt === hit) return i;
    cnt++;
  }
  return -1;
};

export default function ChapterReader({
  chapters = [],
  toc = null,
  currentChapter,
  onChapterChange,
  onRetryChapter,   // 章节加载失败后的重试回调（ReaderPage 提供）
  cover,
  title,
  showToc = false,
  onToggleToc,
  initialTocIdx = null,  // URL 直达节: toc 数组下标(标题锚点 sec-{tocIdx}，主路径)
  initialSec = null,     // URL 直达节: 章内块下标(兼容旧 URL，缺 sec 字段时定位不到)
}) {
  const scrollRef = useRef(null);
  const ch = chapters[currentChapter] || {};
  const total = chapters.length;
  const [scrollTick, setScrollTick] = useState(0);

  // 当前章的 section 目录条目（含 toc 全局下标 → 标题锚点 id 用）
  const secList = useMemo(() => {
    if (!Array.isArray(toc)) return [];
    return toc
      .map((item, i) => ({ item, tocIdx: i }))
      .filter(x => x.item && typeof x.item === 'object' && x.item.type === 'section' && x.item.index === currentChapter);
  }, [toc, currentChapter]);

  // 节(section)滚动定位: 优先标题级锚点 sec-{tocIdx}，回退块锚点 b-{text块序号}
  // tocIdx(URL &toc= 主路径 / TOC 浮层) 优先于 sec 数字(旧 URL 兼容)
  const pendingSecRef = useRef(
    initialTocIdx != null ? { tocIdx: initialTocIdx }
      : initialSec != null ? { sec: initialSec } : null);
  // URL 参数变化（同路由不同 query 不重挂载）→ 同步 pendingSecRef
  useEffect(() => {
    if (initialTocIdx != null) pendingSecRef.current = { tocIdx: initialTocIdx };
    else if (initialSec != null) pendingSecRef.current = { sec: initialSec };
  }, [initialTocIdx, initialSec]);
  useEffect(() => {
    const p = pendingSecRef.current;
    if (p == null) return;
    // URL 直达(sec 数字) → 映射到当前章的 toc 条目下标，命中则用标题锚点。
    // sec 是章内块下标，全书多章重复，必须限定 index === currentChapter。
    if (p.tocIdx == null && p.sec != null && Array.isArray(toc)) {
      const ti = toc.findIndex(t => t && typeof t === 'object' && t.type === 'section'
        && t.index === currentChapter && t.sec === p.sec);
      if (ti >= 0) p.tocIdx = ti;
    }
    let el = null;
    if (p.tocIdx != null) el = document.getElementById(`sec-${p.tocIdx}`);
    if (!el && p.sec != null) el = document.getElementById(`b-${p.sec}`);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'start' });
      pendingSecRef.current = null;
    }
    // 未找到(章节异步加载中) → 等 ch.content / currentChapter 变化再试
  }, [currentChapter, ch?.content, scrollTick, toc]);

  // 阅读设置（持久化）
  const [settings, setSettings] = useState(loadSettings);
  const [showSettings, setShowSettings] = useState(false);
  const [autoPlaying, setAutoPlaying] = useState(false);
  const saveSettings = useCallback((patch) => {
    setSettings(prev => {
      const next = { ...prev, ...patch };
      try { localStorage.setItem('dp_reader_settings', JSON.stringify(next)); } catch {}
      return next;
    });
  }, []);
  const theme = BG_THEMES[settings.bg] || BG_THEMES.default;

  // 切章时滚到顶部
  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = 0;
  }, [currentChapter]);

  // 键盘：左右切章
  useEffect(() => {
    const handler = (e) => {
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
      if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
        const el = scrollRef.current;
        if (el && el.scrollHeight - el.scrollTop - el.clientHeight < 100 && currentChapter < total - 1) {
          onChapterChange(currentChapter + 1);
        }
      } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
        if (scrollRef.current?.scrollTop <= 10 && currentChapter > 0) {
          onChapterChange(currentChapter - 1);
        }
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [currentChapter, total, onChapterChange]);

  // 触摸滑动：底部上滑切章
  const touchStartY = useRef(0);
  const handleTouchStart = (e) => { touchStartY.current = e.touches[0].clientY; setAutoPlaying(false); };
  const handleTouchEnd = (e) => {
    const diff = touchStartY.current - e.changedTouches[0].clientY;
    const el = scrollRef.current;
    if (!el) return;
    if (diff < -80 && el.scrollTop <= 10 && currentChapter > 0) onChapterChange(currentChapter - 1);
    if (diff > 80 && el.scrollHeight - el.scrollTop - el.clientHeight < 100 && currentChapter < total - 1) onChapterChange(currentChapter + 1);
  };

  // 自动阅读: 每 200ms 滚动 speed*0.2 px; 到底自动切章; 滚轮/触摸/键盘即暂停
  useEffect(() => {
    if (!autoPlaying) return;
    const el = scrollRef.current;
    const speed = AUTO_SPEEDS[settings.autoSpeed] || AUTO_SPEEDS.medium;
    const iv = setInterval(() => {
      if (!el) return;
      if (el.scrollHeight - el.scrollTop - el.clientHeight < 10) {
        if (currentChapter < total - 1) {
          onChapterChange(currentChapter + 1);
        } else {
          setAutoPlaying(false);
        }
        return;
      }
      el.scrollTop += speed * 0.2;
    }, 200);
    return () => clearInterval(iv);
  }, [autoPlaying, settings.autoSpeed, currentChapter, total, onChapterChange]);

  // 滚轮交互暂停自动阅读
  const pauseAuto = () => { if (autoPlaying) setAutoPlaying(false); };

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      {/* 章节内容 — 滚动区 */}
      <div ref={scrollRef} onTouchStart={handleTouchStart} onTouchEnd={handleTouchEnd}
        onWheel={pauseAuto}
        className="reader-content"
        style={{
          flex: 1, overflow: 'auto', padding: '24px max(24px, 12vw) 32px',
          fontFamily: 'var(--font-serif, "Playfair Display", serif)',
          fontSize: settings.fontSize, lineHeight: settings.lineHeight,
          color: theme.color, background: theme.bg,
          wordBreak: 'break-word', scrollBehavior: 'smooth',
          WebkitOverflowScrolling: 'touch',
          transition: 'background 0.3s, color 0.3s',
        }}>
        {/* 章标题 */}
        {ch.type === 'section' ? (
          <h2 style={{
            textAlign: 'center', fontSize: Math.max(18, settings.fontSize - 2), fontWeight: 300, margin: '40px 0 48px',
            fontFamily: 'var(--font-sans)', letterSpacing: '0.12em',
            color: 'var(--ochre)', textTransform: 'uppercase',
            borderBottom: '1px solid var(--border)', paddingBottom: 16,
          }}>
            {ch.title}
          </h2>
        ) : (
          <h2 style={{
            textAlign: 'center', fontSize: Math.max(18, settings.fontSize + 2), fontWeight: 500, margin: '0 0 32px',
            fontFamily: 'var(--font-serif)', letterSpacing: '0.04em',
          }}>
            {ch.title || `第${currentChapter + 1}章`}
          </h2>
        )}

        {/* 内容 — HTML 保留原排版 */}
        {ch.type === 'section' ? null : !ch.content && !ch._loaded ? (
          ch._error ? (
            <div style={{ textAlign: 'center', padding: '40px 0', color: 'var(--text-dim)' }}>
              <p style={{ margin: '0 0 12px' }}>章节加载失败（网络或 CDN 异常）</p>
              <button className="btn btn-primary" style={{ padding: '4px 20px' }}
                onClick={() => onRetryChapter && onRetryChapter(currentChapter)}>
                点击重试
              </button>
            </div>
          ) : (
            <p style={{ textAlign: 'center', color: 'var(--text-dim)', padding: '40px 0' }}>加载中...</p>
          )
        ) : ch.content ? (
          (() => {
            const isSmall = b => b.w && b.h
              && Math.max(b.w, b.h) < 300
              && (b.w / b.h) > 0.3 && (b.w / b.h) < 3;
            const merged = [];
            let prevWasSmallImg = false;
            for (let si = 0; si < ch.content.length; si++) {
              const src = ch.content[si];
              const blk = { ...src, _i: si };   // 原始块序号(节滚动锚点 id 用)
              if (blk.type === 'image' && isSmall(blk)) {
                if (merged.length && merged[merged.length - 1].type === 'text') {
                  const last = merged[merged.length - 1];
                  merged[merged.length - 1] = { ...last, value: last.value + '[IMG]', imgs: [...(last.imgs || []), blk] };
                } else {
                  merged.push({ type: 'text', value: '[IMG]', imgs: [blk] });
                }
                prevWasSmallImg = true;
              } else if (blk.type === 'text') {
                if (prevWasSmallImg && merged.length && merged[merged.length - 1].type === 'text') {
                  const last = merged[merged.length - 1];
                  merged[merged.length - 1] = { ...last, value: last.value + blk.value };
                } else {
                  merged.push(blk);
                }
                prevWasSmallImg = false;
              } else {
                merged.push(blk);
                prevWasSmallImg = false;
              }
            }
            // ── 段落重建 ──
            // OCR 每页一个 text block 且段间无空行(段落结构已丢), 靠"行尾句末标点=段边界"重建:
            // 原书折行行尾几乎从不落在句中, 段尾行恰以句号结束 → 可靠边界(页内行内句号不切)。
            // 句末判定 = 行尾先剥掉成对闭合符(”』」）〉“), 再看剩尾是否句子终结符(。！？….!?):
            // 「…在一起”，」行尾是逗号 → 续行; 「…不干净的"。」行尾是句号 → 切段;
            // 「…。」"」引号收尾 → 剥引号后句号 → 切段。否则「…放置在一起"，」长段会在
            // 引号处被切段, 下一段以逗号开头。
            // 段长 300 字上限强切兜底(OCR 标点缺失时防超长段)。
            const END_SENT_RE = /[。！？….!?]$/;
            const END_CLOSE = '”』」）〉"';
            const isEndSent = (s) => {
              let t = String(s).trim();
              while (t && END_CLOSE.includes(t[t.length - 1])) t = t.slice(0, -1);
              return END_SENT_RE.test(t);
            };
            const splitPageParas = (text) => {
              const paras = [];
              let cur = '';
              let curLen = 0;
              for (const ln of (text || '').split('\n')) {
                const s = ln.trim();
                if (!s) continue;
                cur += s; curLen += s.length;
                if (isEndSent(s)) { paras.push(cur); cur = ''; curLen = 0; }
                else if (curLen >= 300) {
                  // 超长无句末标点 → 在行内最后一个句末标点处强切(太近则整段切)
                  // 句末标点后可选跟闭合符(。「」"等), 一并带走避免下段以引号开头
                  const m = cur.match(/.*[。！？….!?][”』」）〉"]?/);
                  if (m && m[0].length > 50) {
                    paras.push(m[0]); cur = cur.slice(m[0].length); curLen = cur.length;
                  } else { paras.push(cur); cur = ''; curLen = 0; }
                }
              }
              if (cur) paras.push(cur);
              return paras;
            };
            // ── 跨块连续段落: 页边界若断句(前块尾段未以句末标点结尾) → 拼接为连续段落 ──
            const paras = [];
            let tail = null;   // 尾段(可能被下一页首段拼接)
            for (const blk of merged) {
              if (blk.type !== 'text') {
                if (tail) { paras.push(tail); tail = null; }
                paras.push(blk);
                continue;
              }
              const parts = (blk.value || '').split('[IMG]');
              const imgs = blk.imgs || [];
              // [IMG] 拼接点 = 图中位置（text1[IMG]text2 → 图渲染在句中）。
              // text1 尾段建段时在段尾留 [IMG] 标记 + 挂图；text2 首段拼回同段 →
              // 图与前字同段、与后字同行（渲染时图+后字 nowrap 绑定, 不孤悬行尾）。
              // 块首 [IMG]（value 以 [IMG] 开头, 图前无文本）→ 图插在首段段首。
              let leadImg = (blk.value || '').startsWith('[IMG]') ? imgs[0] : null;
              let leadUsed = false;
              parts.forEach((p, j) => {
                const segs = splitPageParas(p);
                segs.forEach((seg, k) => {
                  if (!seg.trim()) return;   // 空段跳过
                  const hasImg = (j < parts.length - 1 && k === segs.length - 1 && imgs[j]);
                  const isBlockFirst = (j === 0 && k === 0);
                  let segText = seg, segImgs = [];
                  if (leadImg && !leadUsed) { segText = '[IMG]' + seg; segImgs = [leadImg]; leadUsed = true; }
                  if (hasImg) { segText += '[IMG]'; segImgs = segImgs.concat(imgs[j]); }
                  if (tail && tail.text.endsWith('[IMG]')) {
                    // text2 首段: 拼回图段（图在句中）
                    tail.text += segText;
                    tail.imgs = tail.imgs.concat(segImgs);
                  } else if (hasImg || segImgs.length) {
                    // 段尾留 [IMG] 标记 + 挂图, 等 text2 首段拼入
                    if (isBlockFirst && tail && !isEndSent(tail.text.trim().slice(-2))) {
                      // 页边界断句拼接优先（跨块拼接段）
                      tail.text += segText;
                      tail.imgs = tail.imgs.concat(segImgs);
                    } else {
                      if (tail) paras.push(tail);
                      tail = { text: segText, id: isBlockFirst ? `b-${blk._i}` : undefined,
                               imgs: segImgs, _block: blk._i, _blockFirst: isBlockFirst };
                    }
                  } else if (isBlockFirst && tail && !isEndSent(tail.text.trim().slice(-2))) {
                    // 页边界断句 → 拼接到前块尾段。段首内容仍是原块(常是标题块),
                    // 必须保留 tail 的 id/_block —— b-{sec} 回退与 blockAnchors
                    // 按 _block 匹配都依赖它; 被拼入的本块内容位于段中, 由标题级
                    // sec-{tocIdx} 锚点按文本位置精确定位。
                    tail.text += segText;
                  } else {
                    if (tail) paras.push(tail);
                    tail = { text: segText, id: isBlockFirst ? `b-${blk._i}` : undefined, imgs: segImgs,
                             _block: blk._i, _blockFirst: isBlockFirst };
                  }
                });
              });
            }
            if (tail) paras.push(tail);
            // 每块在段层中的第一个段下标 —— 兜底锚点(块级/比例级)定位用。
            // 块首段可能因页边界断句拼入前块尾段(该段 _blockFirst=false),
            // 但块内容仍从该拼接段中部开始 —— 锚点插在该段开头, 误差仅首段几字。
            const blockFirstSeg = new Map();
            paras.forEach((p, pi) => {
              if (p._block != null && !blockFirstSeg.has(p._block)) blockFirstSeg.set(p._block, pi);
            });

            // 兜底锚点: 文本匹配不到的 section 按两级分配
            // ① 块级: toc 顺序 ↔ 章内"短标题块"顺序, 且候选块与标题实质相似(≥6)
            //    （南怀瑾类: 正文短标题块=节标题, 一一对应; 上帝之城/释义类: 短块
            //      是脚注/注释/书目(相似度 0-1), 不分配 → 落第②级, 避免锚点打在脚注上）
            // ② 比例级: 已匹配 section 的锚点块间按 toc 序比例插值(无已匹配 → 章内均匀),
            //    保证正文无标题行的书(上帝之城等)也能落到节内容所在区域
            const blockAnchors = new Map();
            const ratioAnchors = new Map();
            if (secList.length) {
              const candidates = [];
              (ch.content || []).forEach((b, bi) => {
                const v = (b && (b.value || '')) || '';
                if (v && v.length <= 60 && !/[。！？….!?]$/.test(v.trim())) candidates.push(bi);
              });
              const M = (ch.content || []).length;
              const orderOf = new Map(secList.map((s, o) => [s.tocIdx, o]));  // tocIdx → 章内序
              const matchedBlock = new Map();   // tocIdx → 文本匹配命中块(插值锚)
              let j = 0;
              for (const s of secList) {
                let mBlock = -1;
                (ch.content || []).some((b, bi) => {
                  if (findTitleOffset((b && (b.value || '')) || '', s.item.title) >= 0) { mBlock = bi; return true; }
                  return false;
                });
                if (mBlock >= 0) { matchedBlock.set(s.tocIdx, mBlock); }
                else {
                  const cv = norm(((ch.content || [])[candidates[j]] || {}).value || '');
                  if (j < candidates.length
                    && blockFirstSeg.has(candidates[j])   // 空白块无段, 分配了也跳不了
                    && titleSim(cv, s.item.title) >= 6) {
                    blockAnchors.set(s.tocIdx, candidates[j]);
                  } else {
                    // 无候选或候选与标题不相似 → 比例级
                    const myOrder = orderOf.get(s.tocIdx);
                    // 插值锚按章内序排列(与 tocIdx 无关, 章内序才反映内容先后)
                    const anchors = [...matchedBlock.entries()]
                      .sort((a, b) => orderOf.get(a[0]) - orderOf.get(b[0]))
                      .map(([ti, bi]) => [orderOf.get(ti), bi]);
                    let target;
                    if (!anchors.length) {
                      target = Math.floor((myOrder + 1) * M / (secList.length + 1));
                    } else {
                      let prev = null, next = null;
                      for (const [o, bi] of anchors) {
                        if (o < myOrder) prev = [o, bi]; else { next = [o, bi]; break; }
                      }
                      if (prev && next) {
                        target = Math.round(prev[1] + (next[1] - prev[1]) * (myOrder - prev[0]) / (next[0] - prev[0]));
                      } else if (prev) {
                        target = Math.round(prev[1] + (M - 1 - prev[1]) * (myOrder - prev[0]) / (secList.length - 1 - prev[0]));
                      } else {
                        target = Math.round(next[1] * myOrder / next[0]);
                      }
                    }
                    // 锚点必须落在文本块且段层有该块(image/html 或单段块首段拼入前块 → 无段)
                    const content = ch.content || [];
                    while (target >= 0 && target < M && !(content[target] && content[target].value)) target++;
                    while (target >= 0 && target < M && !blockFirstSeg.has(target)) target++;
                    if (target >= M) {   // 章尾块均无段 → 向前找最近可用块
                      target = M - 1;
                      while (target >= 0 && !blockFirstSeg.has(target)) target--;
                    }
                    ratioAnchors.set(s.tocIdx, target < 0 ? 0 : target);
                  }
                  j++;
                }
              }
            }
            return paras.map((block, i) => {
            if (block.type === 'image') {
              const src = toOssImage(block.src);   // 块级图原图直链(库内最大 ~330KB, 70vh 显示够用)
              if (!src) return null;   // 历史坏数据(本地/OSS 均无) → 不渲染破图
              return (
                <div key={i} style={{ textAlign: 'center', margin: '8px 0' }}>
                  <img src={src} alt={block.alt || ''}
                    loading="lazy" decoding="async"
                    style={{ maxWidth: '100%', maxHeight: '70vh', objectFit: 'contain', borderRadius: 4 }} />
                  {block.alt && <div style={{ fontSize: 11, color: 'var(--text-dim)', marginTop: 4 }}>{block.alt}</div>}
                </div>
              );
            }
            if (block.type === 'html' || (block.value && block.value.startsWith('<') && block.value.includes('>'))) {
              const html = block.value || block.html || '';
              return <div key={i} className="chapter-html" dangerouslySetInnerHTML={{ __html: html }} />;
            }
            const parts = [];
            let cursor = 0;
            // [IMG] 是原子单元: 锚点切点若落在标记内/中间, 推到标记后(防切碎标记)
            const safeOff = (t, off) => {
              while (off < t.length) {
                if (t.slice(off, off + 5) === '[IMG]') { off += 5; continue; }
                if (off >= 2 && t.slice(off - 2, off + 3) === '[IMG]') { off += 3; continue; }
                break;
              }
              return off;
            };
            if ((secList.length || blockAnchors.size || ratioAnchors.size) && block.text) {
              // 锚点: ① 文本匹配 → 标题起始处(精确到标题行);
              //       ② 块级兜底/比例级兜底 → 目标块块首
              const hits = [];
              if (secList.length) {
                for (const s of secList) {
                  const off = findTitleOffset(block.text, s.item.title);
                  if (off >= 0) hits.push({ tocIdx: s.tocIdx, off });
                }
              }
              if (blockAnchors.size || ratioAnchors.size) {
                for (const [tocIdx, bIdx] of blockAnchors) {
                  if (blockFirstSeg.get(bIdx) === i) hits.push({ tocIdx, off: 0 });
                }
                for (const [tocIdx, bIdx] of ratioAnchors) {
                  if (blockFirstSeg.get(bIdx) === i) hits.push({ tocIdx, off: 0 });
                }
              }
              hits.sort((a, b) => a.off - b.off);
              for (const h of hits) {
                if (h.off < cursor) continue;
                parts.push(gluePua(block.text.slice(cursor, safeOff(block.text, h.off))));
                parts.push(<span key={`a${h.tocIdx}`} id={`sec-${h.tocIdx}`} />);
                cursor = safeOff(block.text, h.off);
              }
            }
            parts.push(gluePua(block.text.slice(cursor)));
            // [IMG] 拼接点渲染: 图插在标记处, 图+后字首字 nowrap 绑定
            // （图是行内原子, 行尾放不下时图+首字整体换行, 不再孤悬行尾后字下移）
            let imgCursor = 0;
            const renderText = (s) => {
              // parts 中可能混有锚点 <span> React 元素, 只处理字符串
              if (typeof s !== 'string' || !s.includes('[IMG]')) return s;
              const segs = s.split('[IMG]');
              return segs.map((seg, j) => {
                if (j === 0) return seg;
                const img = block.imgs && block.imgs[imgCursor++];
                const first = Array.from(seg)[0] || '';
                const isrc = img && toOssImage(img.src, 200);   // 行内图 1.1em, 200 宽足够
                return (
                  <Fragment key={`i${j}`}>
                    {isrc ? (
                      <span style={{ whiteSpace: 'nowrap' }}>
                        <img src={isrc} alt="" loading="lazy" decoding="async"
                          style={{ height: '1.1em', verticalAlign: 'middle', margin: '0 1px', display: 'inline' }} />
                        {first}
                      </span>
                    ) : null}
                    {seg.slice(first.length)}
                  </Fragment>
                );
              });
            };
            return (
              <p key={i} id={block.id} style={{ margin: '0 0 0.5em', textIndent: '2em' }}>
                {parts.map((p, pi) => <Fragment key={`p${pi}`}>{renderText(p)}</Fragment>)}
                {(block.imgs || []).slice(imgCursor).map((img, j) => {
                  const isrc = toOssImage(img.src, 200);
                  return isrc ? <img key={j} src={isrc} alt="" loading="lazy" decoding="async"
                    style={{ height: '1.1em', verticalAlign: 'middle', margin: '0 1px', display: 'inline' }} /> : null;
                })}
              </p>
            );
          });
          })()
        ) : (
          <p>{ch.text || ''}</p>
        )}

        {/* 自动阅读中提示 */}
        {autoPlaying && (
          <div style={{
            position: 'sticky', bottom: 16, textAlign: 'center', marginTop: 8, pointerEvents: 'none',
          }}>
            <span style={{
              background: 'rgba(0,0,0,0.45)', color: '#fff', padding: '4px 14px', borderRadius: 12,
              fontSize: 11, letterSpacing: '0.08em',
            }}>自动阅读中 · {SPEED_LABEL[settings.autoSpeed]}速</span>
          </div>
        )}
      </div>

      {/* 底部栏 — 章节切换 + 阅读设置 + 自动阅读 */}
      <div style={{
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        padding: '6px 12px', borderTop: '1px solid var(--border)',
        background: 'var(--card-bg)', flexShrink: 0, gap: 8,
      }}>
        <button className="btn btn-secondary" style={{ padding: '4px 10px', fontSize: 12 }}
          onClick={() => currentChapter > 0 && onChapterChange(currentChapter - 1)}
          disabled={currentChapter <= 0}>
          ◀ 上一章
        </button>
        <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
          <button className="btn btn-secondary" style={{ padding: '4px 10px', fontSize: 12 }}
            onClick={() => setShowSettings(!showSettings)} title="阅读设置">
            ⚙ 设置
          </button>
          <button className="btn btn-secondary" style={{
            padding: '4px 10px', fontSize: 12,
            background: autoPlaying ? 'var(--accent)' : 'transparent',
            color: autoPlaying ? '#fff' : 'inherit',
          }}
            onClick={() => setAutoPlaying(!autoPlaying)} title="自动阅读">
            {autoPlaying ? '⏸ 暂停' : `▶ 自动阅读(${SPEED_LABEL[settings.autoSpeed]})`}
          </button>
        </div>
        <button className="btn btn-secondary" style={{ padding: '4px 10px', fontSize: 12 }}
          onClick={() => currentChapter < total - 1 && onChapterChange(currentChapter + 1)}
          disabled={currentChapter >= total - 1}>
          下一章 ▶
        </button>
      </div>

      {/* 阅读设置面板 */}
      {showSettings && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.45)', zIndex: 420 }}
          onClick={() => setShowSettings(false)}>
          <div style={{
            position: 'absolute', bottom: 52, left: '50%', transform: 'translateX(-50%)',
            width: 'min(92vw, 480px)', background: 'var(--bg)', borderRadius: 12,
            padding: '18px 20px', boxShadow: '0 12px 40px rgba(0,0,0,0.25)',
          }} onClick={e => e.stopPropagation()}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
              <b style={{ fontSize: 14 }}>阅读设置</b>
              <span style={{ cursor: 'pointer', color: 'var(--text-dim)' }} onClick={() => setShowSettings(false)}>✕</span>
            </div>

            {/* 背景色 */}
            <div style={{ marginBottom: 14 }}>
              <div style={{ fontSize: 12, color: 'var(--text-dim)', marginBottom: 6 }}>背景色</div>
              <div style={{ display: 'flex', gap: 8 }}>
                {Object.entries(BG_THEMES).map(([key, t]) => (
                  <button key={key} onClick={() => saveSettings({ bg: key })}
                    style={{
                      flex: 1, padding: '8px 0', borderRadius: 8, cursor: 'pointer', fontSize: 12,
                      border: settings.bg === key ? '2px solid var(--accent)' : '1px solid var(--border)',
                      background: t.bg, color: t.color,
                      opacity: settings.bg === key ? 1 : 0.75,
                    }}>
                    {t.name}
                  </button>
                ))}
              </div>
            </div>

            {/* 字号 */}
            <div style={{ marginBottom: 14, display: 'flex', alignItems: 'center', gap: 10 }}>
              <span style={{ fontSize: 12, color: 'var(--text-dim)', flexShrink: 0 }}>字号</span>
              <button className="btn btn-secondary" style={{ padding: '2px 12px', fontSize: 13 }}
                onClick={() => saveSettings({ fontSize: Math.max(12, settings.fontSize - 2) })}>A−</button>
              <span style={{ fontSize: 13, minWidth: 40, textAlign: 'center' }}>{settings.fontSize}px</span>
              <button className="btn btn-secondary" style={{ padding: '2px 12px', fontSize: 13 }}
                onClick={() => saveSettings({ fontSize: Math.min(26, settings.fontSize + 2) })}>A+</button>
              <span style={{ flex: 1 }} />
              <span style={{ fontSize: 12, color: 'var(--text-dim)', flexShrink: 0 }}>行距</span>
              {[1.6, 2.0, 2.4].map(v => (
                <button key={v} onClick={() => saveSettings({ lineHeight: v })}
                  style={{
                    padding: '3px 10px', borderRadius: 6, cursor: 'pointer', fontSize: 12,
                    border: settings.lineHeight === v ? '1px solid var(--accent)' : '1px solid var(--border)',
                    background: settings.lineHeight === v ? 'var(--soft)' : 'transparent',
                  }}>
                  {v}
                </button>
              ))}
            </div>

            {/* 自动阅读速度 */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <span style={{ fontSize: 12, color: 'var(--text-dim)', flexShrink: 0 }}>自动阅读速度</span>
              {Object.entries(AUTO_SPEEDS).map(([key, px]) => (
                <button key={key} onClick={() => saveSettings({ autoSpeed: key })}
                  style={{
                    padding: '3px 12px', borderRadius: 6, cursor: 'pointer', fontSize: 12,
                    border: settings.autoSpeed === key ? '1px solid var(--accent)' : '1px solid var(--border)',
                    background: settings.autoSpeed === key ? 'var(--soft)' : 'transparent',
                  }}>
                  {SPEED_LABEL[key]}{settings.autoSpeed === key ? ` ·${px}px/s` : ''}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* TOC 浮层 */}
      {showToc && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)', zIndex: 400 }}
          onClick={() => onToggleToc && onToggleToc()}>
          <div style={{ maxWidth: 450, margin: '60px auto 0', width: '90%', background: 'var(--bg)', borderRadius: 10, maxHeight: '70vh', overflow: 'auto', padding: 20 }}
            onClick={e => e.stopPropagation()}>
            <h3 style={{ fontFamily: 'var(--font-serif)', marginTop: 0 }}>目录</h3>
            {(() => {
              const list = (toc && toc.length)
                ? toc.map((item, i) => typeof item === 'string' ? { type: 'chapter', title: item, index: i } : item)
                : chapters.map((c, i) => ({ type: 'chapter', title: c.title, index: i }));
              return list.map((item, i) => {
                const isPart = item.type === 'part';
                const isSubPart = isPart && item.level === 1;   // 书内分组(与神合一内部的部分级)
                const isSection = item.type === 'section';
                const isCur = !isPart && !isSection && item.index === currentChapter;
                return (
                  <div key={i} style={{
                    padding: isPart ? (isSubPart ? '8px 0 4px' : '12px 0 6px') : (isSection ? '5px 0' : '8px 0'),
                    cursor: isPart ? 'default' : 'pointer',
                    borderBottom: isPart ? '1px solid var(--border)' : '1px solid rgba(0,0,0,0.04)',
                    fontSize: isPart ? (isSubPart ? 11 : 11.5) : (isSection ? 11 : 13),
                    fontWeight: isPart ? 700 : (isCur ? 600 : 400),
                    color: isPart ? 'var(--ochre)' : (isCur ? 'var(--ochre)' : (isSection ? 'var(--text-dim)' : 'var(--text)')),
                    letterSpacing: isPart ? '0.15em' : '0',
                    paddingLeft: isPart ? (isSubPart ? 28 : 0) : (isSection ? 42 : 14),
                    opacity: isPart ? 0.85 : 1,
                  }} onClick={() => {
                    if (isPart) return;
                    onToggleToc && onToggleToc();
                    if (isSection) {
                      // 节跳转: 优先标题锚点 sec-{tocIdx}，回退块锚点 b-{sec}；
                      // 同章直接滚, 异章切章后由 useEffect 定位
                      pendingSecRef.current = { tocIdx: i, sec: item.sec };
                      if (item.index !== currentChapter) {
                        onChapterChange(item.index);
                      } else {
                        setScrollTick(t => t + 1);
                      }
                    } else {
                      onChapterChange(item.index);
                    }
                  }}>
                    {isPart ? `— ${item.title} —` : item.title}
                  </div>
                );
              });
            })()}
          </div>
        </div>
      )}
    </div>
  );
}
