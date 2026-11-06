import Icon from '../components/Icon';
/**
 * ChapterReader — 章节滚动式阅读器
 * 每章一页，上下滑动，底部切换章节
 * 阅读体验: 背景色 4 档 / 字号 A-/A+ / 行距 3 档 / 自动阅读(速度可调, 交互即暂停, localStorage 持久化)
 */
import { Fragment, useRef, useEffect, useState, useCallback, useMemo } from 'react';
import DOMPurify from 'dompurify';
import { locateChapterSections } from '../data/chapterSections';
import { validSourceInlineStyles, sourceInlineSegments } from '../data/sourceInlineStyles';
import './readerGlyphs.css';

// S9（audit 2026-08-17）：章节 HTML 渲染前用 DOMPurify 净化（防存储型 XSS）。
// 章节内容为策展 HTML，仍按"不可信输入"处理。
const SANITIZE_CONFIG = {
  ALLOWED_TAGS: ['p','br','b','strong','i','em','u','s','sub','sup','h1','h2','h3','h4',
    'ul','ol','li','blockquote','pre','code','hr','table','thead','tbody','tr','td','th',
    'a','span','div','img','figure','figcaption'],
  ALLOWED_ATTR: ['href','title','alt','src','width','height','align','colspan','rowspan','class','id','style'],
  ALLOW_DATA_ATTR: false,
};

export function sanitizeChapterHtml(html) {
  return DOMPurify.sanitize(html || '', SANITIZE_CONFIG);
}

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

const renderSourceInline = (text, styles, offset = 0) => {
  if (!styles?.length) return text;
  return sourceInlineSegments(text, styles, offset).map((part, i) => {
    if (!part.kind) return <Fragment key={i}>{part.text}</Fragment>;
    const Tag = part.kind;
    return <Tag key={i} style={{ fontSize: '0.75em', lineHeight: 1, position: 'static', verticalAlign: part.kind === 'sub' ? 'sub' : 'super' }}>{part.text}</Tag>;
  });
};

const loadSettings = () => {
  try {
    const s = JSON.parse(localStorage.getItem('dp_reader_settings') || '{}');
    return { bg: s.bg || 'default', fontSize: s.fontSize || 18, lineHeight: s.lineHeight || 2.0,
             autoSpeed: s.autoSpeed || 'medium' };
  } catch { return { bg: 'default', fontSize: 18, lineHeight: 2.0, autoSpeed: 'medium' }; }
};

export default function ChapterReader({
  chapters = [],
  toc = null,
  currentChapter,
  onChapterChange,
  onRetryChapter,   // 章节加载失败后的重试回调（ReaderPage 提供）
  showToc = false,
  onToggleToc,
  initialTocIdx = null,  // URL 直达节: toc 数组下标(标题锚点 sec-{tocIdx}，主路径)
  initialSec = null,     // URL 直达节: 章内块下标(兼容旧 URL，缺 sec 字段时定位不到)
  initialNote = null,    // URL 直达注释: 显示号(章末注释锚点 dp-note-{ch}-{disp}，note-contract v1)
}) {
  const scrollRef = useRef(null);
  const ch = chapters[currentChapter] || {};
  const total = chapters.length;
  const [scrollTick, setScrollTick] = useState(0);

  // ── 章末注释（note-contract v1，docs/note-contract.md）──
  // 数据: 章.notes=[{n,kind,text,imgs?}]，正文引用记号 {{n:x}}（仅此格式，由逐段实读迁移放置）。
  // 显示号 = 按正文首次引用顺序重排（数据 n 只是稳定标识）；无引用的注释排在后面按数据序。
  const NOTE_TOKEN_RE = /\{\{n:(\d+)\}\}/g;
  const NOTE_KIND_LABEL = { author: '作者注', translator: '译注', editor: '编注', original: '原注', recorder: '记录者' };
  const noteIndex = useMemo(() => {
    const notes = Array.isArray(ch.notes) ? ch.notes : null;
    if (!notes || !notes.length || !Array.isArray(ch.content)) return null;
    const byN = new Map(notes.map(nt => [Number(nt.n), nt]));
    if (!byN.size) return null;
    const order = [];
    const seen = new Set();
    for (const b of ch.content) {
      if (!b || b.type !== 'text' || !b.value || !b.value.includes('{{n:')) continue;
      NOTE_TOKEN_RE.lastIndex = 0;
      let m;
      while ((m = NOTE_TOKEN_RE.exec(b.value))) {
        const n = parseInt(m[1], 10);
        if (byN.has(n) && !seen.has(n)) { seen.add(n); order.push(n); }
      }
    }
    for (const nt of notes) if (!seen.has(Number(nt.n))) order.push(Number(nt.n));
    const disp = new Map();
    order.forEach((n, i) => disp.set(n, i + 1));
    return { byN, order, disp };
  }, [ch.notes, ch.content, currentChapter]);
  // 每条注释"最近入口"引用实例 id：点正文上标时记录，点注释号/返回时回到该实例（重复引用不回错）
  const lastRefRef = useRef({});
  useEffect(() => { lastRefRef.current = {}; }, [currentChapter]);
  const [hlId, setHlId] = useState(null);
  const hlTimer = useRef(null);
  const flashAndScroll = useCallback((id) => {
    const el = document.getElementById(id);
    if (!el) return;
    // 即时滚动：容器 CSS scroll-behavior:smooth 会让 behavior:'auto' 仍走动画（后台/节流标签页会卡死），
    // 必须 instant 强制瞬时；高亮闪烁承担视觉引导
    el.scrollIntoView({ behavior: 'instant', block: 'center' });
    setHlId(id);
    if (hlTimer.current) clearTimeout(hlTimer.current);
    hlTimer.current = setTimeout(() => setHlId(null), 1800);
  }, []);
  const goNote = useCallback((n, disp, entryEl) => {
    if (entryEl && entryEl.id) lastRefRef.current[n] = entryEl.id;
    flashAndScroll(`dp-note-${currentChapter}-${disp}`);
  }, [currentChapter, flashAndScroll]);
  const goBackRef = useCallback((n) => {
    const id = lastRefRef.current[n];
    if (id) flashAndScroll(id);
  }, [flashAndScroll]);
  // URL 直达注释（?ch=&note=显示号）：内容渲染后滚到该注释（无入口 → 不显示返回）
  const pendingNoteRef = useRef(initialNote);
  useEffect(() => { pendingNoteRef.current = initialNote; }, [initialNote]);

  // 当前章的 section 目录条目（含 toc 全局下标 → 标题锚点 id 用）
  const secList = useMemo(() => {
    if (!Array.isArray(toc)) return [];
    return toc
      .map((item, i) => ({ item, tocIdx: i }))
      .filter(x => x.item && typeof x.item === 'object' && x.item.type === 'section' && x.item.index === currentChapter);
  }, [toc, currentChapter]);

  // 切章先回顶部，再执行下方的目录/块定位，避免覆盖已找到的目标。
  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = 0;
  }, [currentChapter]);

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
    // URL 直达注释: 等该章 notes/正文渲染出锚点后滚动（与节定位互不阻塞）
    if (pendingNoteRef.current != null && noteIndex) {
      const disp = pendingNoteRef.current;
      const el = document.getElementById(`dp-note-${currentChapter}-${disp}`);
      if (el) {
        el.scrollIntoView({ behavior: 'instant', block: 'center' });
        setHlId(el.id);
        if (hlTimer.current) clearTimeout(hlTimer.current);
        hlTimer.current = setTimeout(() => setHlId(null), 1800);
        pendingNoteRef.current = null;
      }
    }
    const p = pendingSecRef.current;
    if (p == null) return;
    // URL 直达(sec 数字) → 映射到当前章的 toc 条目下标，命中则用标题锚点。
    // sec 是章内块下标，全书多章重复，必须限定 index === currentChapter。
    if (p.tocIdx == null && p.sec != null && Array.isArray(toc)) {
      const ti = toc.findIndex(t => t && typeof t === 'object' && t.type === 'section'
        && t.index === currentChapter && t.sec === p.sec);
      if (ti >= 0) p.tocIdx = ti;
    }
    // Book-detail links carry toc, while sidebar clicks also carry sec. Resolve
    // the same validated block fallback for both paths.
    if (p.tocIdx != null && p.sec == null && Array.isArray(toc)) {
      const target = toc[p.tocIdx];
      if (target?.type === 'section' && target.index === currentChapter
        && Number.isInteger(target.sec) && target.sec >= 0 && target.sec < (ch.content?.length || 0)) p.sec = target.sec;
    }
    let el = null;
    if (p.tocIdx != null) el = document.getElementById(`sec-${p.tocIdx}`);
    if (!el && p.sec != null) el = document.getElementById(`b-${p.sec}`);
    if (el) {
      // An empty inline anchor sits on the text baseline. Scroll the complete
      // heading so its first line stays visible, including titles with notes.
      const target = el.closest('h2, h3, h4, h5, h6') || el;
      target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      pendingSecRef.current = null;
    }
    // 未找到(章节异步加载中) → 等 ch.content / currentChapter 变化再试
  }, [currentChapter, ch?.content, ch?.notes, scrollTick, toc, noteIndex]);

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

<div style={{ flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      {/* 章节内容 — 滚动区 */}
      <div ref={scrollRef} onTouchStart={handleTouchStart} onTouchEnd={handleTouchEnd}
        onWheel={pauseAuto}
        className="reader-content"
        style={{
          flex: 1, minHeight: 0, overflow: 'auto', padding: '24px max(24px, 12vw) 32px',
          fontFamily: '"DP Classical Han", var(--font-serif, "Playfair Display", serif)',
          fontSize: settings.fontSize, lineHeight: settings.lineHeight,
          color: theme.color, background: theme.bg,
          wordBreak: 'break-word', scrollBehavior: 'smooth',
          WebkitOverflowScrolling: 'touch',
          transition: 'background 0.3s, color 0.3s',
        }}>
        {/* 章标题 */}
        {ch.content?.some(block => block?.role === 'chapter-title') ? null : ch.type === 'section' ? (
          <h2 style={{
            textAlign: 'center', fontSize: Math.max(18, settings.fontSize - 2), fontWeight: 300, margin: '40px 0 48px',
            fontFamily: '"DP Classical Han", var(--font-sans)', letterSpacing: '0.12em',
            color: 'var(--ochre)', textTransform: 'uppercase',
            borderBottom: '1px solid var(--border)', paddingBottom: 16,
          }}>
            {ch.title}
          </h2>
        ) : (
          <h2 style={{
            textAlign: 'center', fontSize: Math.max(18, settings.fontSize + 2), fontWeight: 500, margin: '0 0 32px',
            fontFamily: '"DP Classical Han", var(--font-serif)', letterSpacing: '0.04em',
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
            const hasSourceStyles = ch.paragraphMode === 'source' && ch.content.some(b => b?.inlineStyles?.length);
            const isSmall = b => !hasSourceStyles && b.display !== 'block' && b.w && b.h
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
            // 不按字数强切；没有真实句末/段落边界时保留句子连续性。
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
              for (const ln of (text || '').split('\n')) {
                const s = ln.trim();
                if (!s) {
                  if (cur) { paras.push(cur); cur = ''; }
                  continue;
                }
                cur += s;
                if (isEndSent(s)) { paras.push(cur); cur = ''; }
              }
              if (cur) paras.push(cur);
              return paras;
            };
            // ── 跨块连续段落: 页边界若断句(前块尾段未以句末标点结尾) → 拼接为连续段落 ──
            const paras = [];
            let tail = null;   // 尾段(可能被下一页首段拼接)
            for (const blk of merged) {
              // Direct text imports already have paragraph boundaries. OCR page
              // continuation heuristics must not join their adjacent blocks.
              if (ch.paragraphMode === 'source' && tail) {
                paras.push(tail);
                tail = null;
              }
              if (blk.type !== 'text') {
                if (tail) { paras.push(tail); tail = null; }
                paras.push(blk);
                continue;
              }
              // Certified headings are boundaries even when their surrounding
              // OCR page blocks still need continuation joining.
              if (ch.paragraphMode === 'source' || blk.role === 'section-title' || blk.role === 'chapter-title') {
                if (tail) { paras.push(tail); tail = null; }
                paras.push({ text: blk.value || '', id: `b-${blk._i}`, imgs: blk.imgs || [], _block: blk._i, _blockFirst: true });
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
                const segs = ch.paragraphMode === 'source' ? [p] : splitPageParas(p);
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
                    // 必须保留 tail 的 id/_block —— b-{sec} 回退与节定位
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
            const sectionTargets = locateChapterSections(ch.content || [], paras, secList);
            const noteReferenceSequence = {};
            return paras.map((block, i) => {
            if (block.type === 'image') {
              const src = toOssImage(block.src);   // 块级图原图直链(库内最大 ~330KB, 70vh 显示够用)
              if (!src) return null;   // 历史坏数据(本地/OSS 均无) → 不渲染破图
              return (
                <div key={i} style={{ textAlign: 'center', margin: '8px 0' }}>
                  <img src={src} alt={block.alt || ''}
                    loading="lazy" decoding="async"
                    style={{ maxWidth: '100%', maxHeight: '70vh', objectFit: 'contain', borderRadius: 4, backgroundColor: block.background === 'white' ? '#fff' : undefined }} />
                  {block.alt && <div style={{ fontSize: 11, color: 'var(--text-dim)', marginTop: 4 }}>{block.alt}</div>}
                </div>
              );
            }
            if (block.type === 'html' || (block.value && block.value.startsWith('<') && block.value.includes('>'))) {
              const html = sanitizeChapterHtml(block.value || block.html || '');  // S9: 净化后渲染
              return <div key={i} className="chapter-html" dangerouslySetInnerHTML={{ __html: html }} />;
            }
            const sourceBlock = ch.content?.[block._block];
            const sourceStyles = block.text === sourceBlock?.value ? validSourceInlineStyles(block.text, sourceBlock?.inlineStyles) : [];
            const protectGlyphs = sourceStyles.length ? t => t : gluePua;
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
            const hits = sectionTargets.get(i) || [];
            if (hits.length && block.text) {
              for (const h of hits) {
                if (h.off < cursor) continue;
                parts.push(protectGlyphs(block.text.slice(cursor, safeOff(block.text, h.off))));
                parts.push(<span key={`a${h.tocIdx}`} id={`sec-${h.tocIdx}`} />);
                cursor = safeOff(block.text, h.off);
              }
            }
            parts.push(protectGlyphs(block.text.slice(cursor)));
            // [IMG] 拼接点渲染: 图插在标记处, 图+后字首字 nowrap 绑定
            // （图是行内原子, 行尾放不下时图+首字整体换行, 不再孤悬行尾后字下移）
            let imgCursor = 0;
            const renderText = (s, sourceOffset = 0) => {
              // parts 中可能混有锚点 <span> React 元素, 只处理字符串
              if (typeof s !== 'string') return s;
              if (!s.includes('[IMG]')) return renderSourceInline(s, sourceStyles, sourceOffset);
              const segs = s.split('[IMG]');
              let segmentOffset = sourceOffset;
              return segs.map((seg, j) => {
                if (j === 0) {
                  const words = renderSourceInline(seg, sourceStyles, segmentOffset);
                  segmentOffset += seg.length;
                  return words;
                }
                segmentOffset += 5;
                const img = block.imgs && block.imgs[imgCursor++];
                const first = Array.from(seg)[0] || '';
                const isrc = img && toOssImage(img.src, 200);   // 行内图 1.1em, 200 宽足够
                const firstWord = renderSourceInline(first, sourceStyles, segmentOffset);
                const rest = renderSourceInline(seg.slice(first.length), sourceStyles, segmentOffset + first.length);
                segmentOffset += seg.length;
                return (
                  <Fragment key={`i${j}`}>
                    {isrc ? (
                      <span style={{ whiteSpace: 'nowrap' }}>
                        <img src={isrc} alt={img.alt || ''} loading="lazy" decoding="async"
                          style={{ height: img.role === 'formula' ? '2.4em' : '1.1em', verticalAlign: 'middle', margin: '0 1px', display: 'inline', backgroundColor: img.background === 'white' ? '#fff' : undefined }} />
                        {firstWord}
                      </span>
                    ) : firstWord}
                    {rest}
                  </Fragment>
                );
              });
            };
            // 行内注释引用 {{n:x}} → 可点上标 [显示号]（note-contract v1; token 只由逐段实读迁移放置,
            // 渲染层只认这一种精确格式, 数学方括号/圣经章句/引用年份不受影响）
            const rseq = noteReferenceSequence;   // 全章共享，不能在每个段落中重新计数
            const renderWithNotes = (p, sourceOffset = 0) => {
              if (typeof p !== 'string') return p;
              if (!noteIndex || !p.includes('{{n:')) return renderText(p, sourceOffset);
              const out = [];
              const re = /\{\{n:(\d+)\}\}/g;
              let last = 0, m, k = 0;
              while ((m = re.exec(p))) {
                if (m.index > last) out.push(renderText(p.slice(last, m.index), sourceOffset + last));
                const n = parseInt(m[1], 10);
                const disp = noteIndex.disp.get(n);
                if (disp == null) { out.push(renderText(m[0], sourceOffset + m.index)); }
                else {
                  rseq[n] = (rseq[n] || 0) + 1;
                  const rid = `dp-ref-${currentChapter}-${disp}-${rseq[n]}`;
                  out.push(
                    <sup key={`nt${k++}`} id={rid}
                      className={'dp-note-ref' + (hlId === rid ? ' dp-flash' : '')}
                      role="button" tabIndex={0} aria-label={`注释${disp}`}
                      onClick={(e) => goNote(n, disp, e.currentTarget)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); goNote(n, disp, e.currentTarget); }
                      }}>
                      [{disp}]
                    </sup>
                  );
                }
                last = m.index + m[0].length;
              }
              if (last < p.length) out.push(renderText(p.slice(last), sourceOffset + last));
              return out;
            };
            const isSourceTitle = sourceBlock?.role === 'chapter-title';
            const isSectionTitle = sourceBlock?.role === 'section-title';
            const isQuotation = sourceBlock?.quote === true;
            const alignment = ['center', 'right'].includes(sourceBlock?.align) ? sourceBlock.align : undefined;
            const sectionHeading = Number.isInteger(sourceBlock?.level)
              ? `h${Math.min(6, Math.max(3, sourceBlock.level + 1))}` : 'h4';
            const TextElement = isSourceTitle ? 'h2' : isSectionTitle ? sectionHeading : 'p';
            const paragraphStyle = isSourceTitle
              ? { textAlign: 'center', fontSize: Math.max(18, settings.fontSize + 2), fontWeight: 500, margin: '0 0 32px', fontFamily: '"DP Classical Han", var(--font-serif)', letterSpacing: '0.04em' }
              : isSectionTitle ? { margin: '1.2em 0 .6em', textIndent: 0, fontSize: sourceBlock.level === 2 ? '1.08em' : '1em', fontWeight: 600 }
              : { margin: '0 0 0.5em', textIndent: isQuotation || alignment ? 0 : '2em', textAlign: alignment, marginLeft: isQuotation ? '2em' : undefined, whiteSpace: ch.paragraphMode === 'source' ? 'pre-line' : undefined };
            let partTextOffset = 0;
            return (
              <TextElement key={i} id={block.id} className={isQuotation ? 'reader-quotation' : undefined} style={paragraphStyle}>
                {parts.map((p, pi) => {
                  const start = partTextOffset;
                  if (typeof p === 'string') partTextOffset += p.length;
                  const trimSectionSign = isSectionTitle && start === 0 && typeof p === 'string' && p.startsWith('§');
                  return <Fragment key={`p${pi}`}>{renderWithNotes(trimSectionSign ? p.slice(1) : p, start + (trimSectionSign ? 1 : 0))}</Fragment>;
                })}
                {(block.imgs || []).slice(imgCursor).map((img, j) => {
                  const isrc = toOssImage(img.src, 200);
                  return isrc ? <img key={j} src={isrc} alt={img.alt || ''} loading="lazy" decoding="async"
                    style={{ height: img.role === 'formula' ? '2.4em' : '1.1em', verticalAlign: 'middle', margin: '0 1px', display: 'inline', backgroundColor: img.background === 'white' ? '#fff' : undefined }} /> : null;
                })}
              </TextElement>
            );
          });
          })()
        ) : (
          <p>{ch.text || ''}</p>
        )}

        {/* 章末注释（note-contract v1）: 正文后集中显示；点编号/返回回到最近点击的正文引用实例 */}
        {noteIndex && (
          <div className="dp-notes" style={{
            margin: '36px 0 8px', paddingTop: 18, borderTop: '1px solid var(--border)',
            fontSize: Math.max(12, settings.fontSize - 4), lineHeight: 1.8, color: 'var(--text)',
          }}>
            <div style={{
              textAlign: 'center', fontSize: Math.max(13, settings.fontSize - 4), letterSpacing: '0.3em',
              color: 'var(--text-dim)', marginBottom: 14,
            }}>注　释</div>
            {noteIndex.order.map((n, i) => {
              const disp = i + 1;
              const nt = noteIndex.byN.get(n) || {};
              const noteId = `dp-note-${currentChapter}-${disp}`;
              const hasBack = lastRefRef.current[n] != null;
              const noteBody = String(nt.text || '');
              const noteStyles = validSourceInlineStyles(noteBody, nt.inlineStyles);
              let noteImageCursor = 0;
              let noteTextOffset = 0;
              let crossSequence = 0;
              const renderNoteWords = (segment, start) => {
                if (!Array.isArray(nt.crossRefs)) return renderSourceInline(segment, noteStyles, start);
                const out = [];
                let cursor = 0;
                for (const ref of nt.crossRefs) {
                  const from = ref.start - start, to = ref.end - start;
                  const target = noteIndex.disp.get(ref.n);
                  if (!Number.isInteger(from) || !Number.isInteger(to) || from < cursor || to <= from || to > segment.length || target == null) continue;
                  out.push(renderSourceInline(segment.slice(cursor, from), noteStyles, start + cursor));
                  const id = `dp-note-cross-${currentChapter}-${n}-${++crossSequence}`;
                  out.push(<button key={id} id={id} type="button" className={'dp-note-cross' + (hlId === id ? ' dp-flash' : '')}
                    style={{ border: 0, background: 'none', padding: 0, font: 'inherit', textIndent: 0, color: 'var(--ochre)', cursor: 'pointer', ...(ref.superscript === true ? { verticalAlign: 'super', fontSize: '0.75em', lineHeight: 1 } : {}) }}
                    aria-label={`转到注释${target}`} onClick={e => goNote(ref.n, target, e.currentTarget)}>[{target}]</button>);
                  cursor = to;
                }
                out.push(renderSourceInline(segment.slice(cursor), noteStyles, start + cursor));
                return out;
              };
              return (
                <div key={n} id={noteId}
                  className={'dp-note-item' + (hlId === noteId ? ' dp-flash' : '')}
                  style={{ margin: '0 0 8px', paddingLeft: '2.4em', textIndent: '-2.4em' }}>
                  <span className="dp-note-num" role="button" tabIndex={0}
                    style={{ cursor: hasBack ? 'pointer' : 'default', color: 'var(--ochre)' }}
                    aria-label={hasBack ? `返回引用位置${disp}` : `注释${disp}`}
                    title={hasBack ? '回到引用位置' : undefined}
                    onClick={() => goBackRef(n)}
                    onKeyDown={(e) => {
                      if ((e.key === 'Enter' || e.key === ' ') && hasBack) { e.preventDefault(); goBackRef(n); }
                    }}>
                    [{disp}]
                  </span>
                  {nt.kind && NOTE_KIND_LABEL[nt.kind] && (
                    <span style={{ fontSize: '0.85em', color: 'var(--text-dim)', marginRight: 4 }}>
                      {NOTE_KIND_LABEL[nt.kind]}：
                    </span>
                  )}
                  {noteBody.split('\n').map((para, pj) => {
                    let segmentOffset = noteTextOffset;
                    noteTextOffset += para.length + 1;
                    return <span key={pj} style={{ display: pj > 0 ? 'block' : 'inline', textIndent: pj > 0 ? 0 : undefined }}>
                      {para.split('[IMG]').map((seg, sk) => {
                        if (sk > 0) segmentOffset += 5;
                        const words = renderNoteWords(seg, segmentOffset);
                        segmentOffset += seg.length;
                        if (sk === 0) return words;
                        const img = (nt.imgs || [])[noteImageCursor++];
                        const isrc = img && toOssImage(img.src, 200);
                        return (
                          <Fragment key={sk}>
                            {isrc ? <img src={isrc} alt={img.alt || ''} loading="lazy" decoding="async"
                              style={{ height: img.role === 'formula' ? '2.4em' : '1.1em', verticalAlign: 'middle', margin: '0 1px', display: 'inline', backgroundColor: img.background === 'white' ? '#fff' : undefined }} /> : null}
                            {words}
                          </Fragment>
                        );
                      })}
                    </span>;
                  })}
                  {nt.editorialAddendum && (
                    <span className="dp-note-editorial-addendum" style={{ display: 'block', textIndent: 0, fontSize: '0.9em', color: 'var(--text-dim)' }}>
                      校：{nt.editorialAddendum}
                    </span>
                  )}
                  {hasBack && (
                    <button className="dp-note-back" title="回到引用位置"
                      style={{
                        border: 'none', background: 'transparent', color: 'var(--ochre)', cursor: 'pointer',
                        fontSize: '0.85em', padding: '0 2px', marginLeft: 4,
                      }}
                      onClick={() => goBackRef(n)}>↩</button>
                  )}
                </div>
              );
            })}
          </div>
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
            <Icon name="btn-settings" size={11} style={{ marginRight: 3 }} />设置
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
                    paddingLeft: isPart ? (isSubPart ? 28 : 0) : (isSection ? 42 + (Math.max(2, Number(item.level) || 2) - 2) * 14 : 14),
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
