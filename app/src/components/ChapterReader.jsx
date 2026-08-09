/**
 * ChapterReader — 章节滚动式阅读器
 * 每章一页，上下滑动，底部切换章节
 * 阅读体验: 背景色 4 档 / 字号 A-/A+ / 行距 3 档 / 自动阅读(速度可调, 交互即暂停, localStorage 持久化)
 */
import { Fragment, useRef, useEffect, useState, useCallback } from 'react';

// 阅读背景主题
const BG_THEMES = {
  default: { bg: 'var(--card-bg)', color: 'var(--ink)', name: '默认' },
  paper:   { bg: '#f6f1e3',  color: '#3d3a33', name: '米黄纸' },
  green:   { bg: '#e6efe3',  color: '#2f3a2e', name: '护眼绿' },
  night:   { bg: '#202124',  color: '#d8d8dc', name: '夜间' },
};
const AUTO_SPEEDS = { slow: 45, medium: 80, fast: 130 };   // px/s
const SPEED_LABEL = { slow: '慢', medium: '中', fast: '快' };

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
  cover,
  title,
  showToc = false,
  onToggleToc,
  initialSec = null,   // URL 直达节(第X节)滚动锚点
}) {
  const scrollRef = useRef(null);
  const ch = chapters[currentChapter] || {};
  const total = chapters.length;
  const [scrollTick, setScrollTick] = useState(0);

  // 节(section)滚动定位: 目标块 id = b-{text块序号}
  const pendingSecRef = useRef(initialSec != null ? initialSec : null);
  useEffect(() => {
    const target = pendingSecRef.current;
    if (target == null) return;
    const el = document.getElementById(`b-${target}`);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'start' });
      pendingSecRef.current = null;
    }
    // 未找到(章节异步加载中) → 等 ch.content / currentChapter 变化再试
  }, [currentChapter, ch?.content, scrollTick]);

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
          <p style={{ textAlign: 'center', color: 'var(--text-dim)', padding: '40px 0' }}>加载中...</p>
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
            // 段长 300 字上限强切兜底(OCR 标点缺失时防超长段)。
            const END_SENT = /[。！？…"”』」）〉\.!?]$/;
            const splitPageParas = (text) => {
              const paras = [];
              let cur = '';
              let curLen = 0;
              for (const ln of (text || '').split('\n')) {
                const s = ln.trim();
                if (!s) continue;
                cur += s; curLen += s.length;
                if (END_SENT.test(s)) { paras.push(cur); cur = ''; curLen = 0; }
                else if (curLen >= 300) {
                  // 超长无句末标点 → 在行内最后一个句末标点处强切(太近则整段切)
                  const m = cur.match(/.*[。！？…"”』」）〉\.!?]/);
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
              parts.forEach((p, j) => {
                const segs = splitPageParas(p);
                segs.forEach((seg, k) => {
                  if (!seg.trim()) return;   // 空段跳过
                  const segImgs = (j < parts.length - 1 && k === segs.length - 1 && imgs[j]) ? [imgs[j]] : [];
                  const isBlockFirst = (j === 0 && k === 0);
                  if (isBlockFirst && tail && !END_SENT.test(tail.text.trim().slice(-1))) {
                    // 页边界断句 → 拼接到前块尾段; 锚点给当前块(跳转落在本块内容开头)
                    tail.text += seg;
                    tail.imgs = tail.imgs.concat(segImgs);
                    tail.id = `b-${blk._i}`;
                  } else {
                    if (tail) paras.push(tail);
                    tail = { text: seg, id: isBlockFirst ? `b-${blk._i}` : undefined, imgs: segImgs };
                  }
                });
              });
            }
            if (tail) paras.push(tail);
            return paras.map((block, i) => {
            if (block.type === 'image') {
              return (
                <div key={i} style={{ textAlign: 'center', margin: '8px 0' }}>
                  <img src={block.src} alt={block.alt || ''}
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
            return (
              <p key={i} id={block.id} style={{ margin: '0 0 0.5em', textIndent: '2em' }}>
                {block.text}
                {block.imgs && block.imgs.map((img, j) => (
                  <img key={j} src={img.src} alt=""
                    style={{ height: '1.1em', verticalAlign: 'middle', margin: '0 1px', display: 'inline' }} />
                ))}
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
                      // 节跳转: 同章直接滚, 异章切章后由 useEffect 定位
                      pendingSecRef.current = item.sec;
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
