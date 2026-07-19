/**
 * ChapterReader — 章节滚动式阅读器
 * 每章一页，上下滑动，底部切换章节
 */
import { useRef, useEffect, useState, useCallback } from 'react';
import { getApiBase } from '../utils/api';

// 解析图片 URL：相对路径 → dev 直接走，生产加 Render API 前缀
function resolveImgSrc(src) {
  if (!src) return '';
  if (src.startsWith('http://') || src.startsWith('https://') || src.startsWith('data:')) return src;
  if (import.meta.env.DEV) return src; // Vite proxy 处理 /api/
  const base = getApiBase();
  return base ? base + src : src;
}

export default function ChapterReader({
  chapters = [],
  currentChapter,
  onChapterChange,
  cover,
  title,
  showToc = false,
  onToggleToc,
}) {
  const scrollRef = useRef(null);
  const ch = chapters[currentChapter] || {};
  const total = chapters.length;


  // 切章时滚到顶部
  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = 0;
  }, [currentChapter]);

  // 键盘：左右切章
  useEffect(() => {
    const handler = (e) => {
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
      if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
        // 滚到底部才切章
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
  const handleTouchStart = (e) => { touchStartY.current = e.touches[0].clientY; };
  const handleTouchEnd = (e) => {
    const diff = touchStartY.current - e.changedTouches[0].clientY;
    const el = scrollRef.current;
    if (!el) return;
    // 在页面顶部下滑 → 上一章
    if (diff < -80 && el.scrollTop <= 10 && currentChapter > 0) onChapterChange(currentChapter - 1);
    // 在页面底部上滑 → 下一章
    if (diff > 80 && el.scrollHeight - el.scrollTop - el.clientHeight < 100 && currentChapter < total - 1) onChapterChange(currentChapter + 1);
  };

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      {/* 章节内容 — 滚动区 */}
      <div ref={scrollRef} onTouchStart={handleTouchStart} onTouchEnd={handleTouchEnd}
        style={{
          flex: 1, overflow: 'auto', padding: '24px max(24px, 12vw) 32px',
          fontFamily: 'var(--font-serif, "Playfair Display", serif)',
          fontSize: 18, lineHeight: 2.0, color: 'var(--ink)',
          wordBreak: 'break-word', scrollBehavior: 'smooth',
          WebkitOverflowScrolling: 'touch',
        }}>
        {/* 章标题 */}
        {ch.type === 'section' ? (
          <h2 style={{
            textAlign: 'center', fontSize: 20, fontWeight: 300, margin: '40px 0 48px',
            fontFamily: 'var(--font-sans)', letterSpacing: '0.12em',
            color: 'var(--ochre)', textTransform: 'uppercase',
            borderBottom: '1px solid var(--border)', paddingBottom: 16,
          }}>
            {ch.title}
          </h2>
        ) : (
          <h2 style={{
            textAlign: 'center', fontSize: 22, fontWeight: 500, margin: '0 0 32px',
            fontFamily: 'var(--font-serif)', letterSpacing: '0.04em',
          }}>
            {ch.title || `第${currentChapter + 1}章`}
          </h2>
        )}

        {/* 内容 — HTML 保留原排版 */}
        {ch.type === 'section' ? null : !ch.content && !ch._loaded ? (
          <p style={{ textAlign: 'center', color: 'var(--text-dim)', padding: '40px 0' }}>加载中...</p>
        ) : ch.content ? (
          ch.content.map((block, i) => {
            if (block.type === 'image') {
              return (
                <div key={i} style={{ textAlign: 'center', margin: '16px 0' }}>
                  <img src={resolveImgSrc(block.src)} alt={block.alt || ''}
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
            return <p key={i} style={{ margin: '0 0 0.5em', textIndent: '2em' }}>{block.value}</p>;
          })
        ) : (
          <p>{ch.text || ''}</p>
        )}
      </div>

      {/* 底部栏 — 仅章节切换 */}
      <div style={{
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        padding: '8px 16px', borderTop: '1px solid var(--border)',
        background: 'var(--card-bg)', flexShrink: 0,
      }}>
        <button className="btn btn-secondary" style={{ padding: '4px 12px', fontSize: 12 }}
          onClick={() => currentChapter > 0 && onChapterChange(currentChapter - 1)}
          disabled={currentChapter <= 0}>
          ◀ 上一章
        </button>
        <button className="btn btn-secondary" style={{ padding: '4px 12px', fontSize: 12 }}
          onClick={() => currentChapter < total - 1 && onChapterChange(currentChapter + 1)}
          disabled={currentChapter >= total - 1}>
          下一章 ▶
        </button>
      </div>

      {/* TOC 浮层 */}
      {showToc && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)', zIndex: 400 }}
          onClick={() => onToggleToc && onToggleToc()}>
          <div style={{ maxWidth: 450, margin: '60px auto 0', width: '90%', background: 'var(--bg)', borderRadius: 10, maxHeight: '70vh', overflow: 'auto', padding: 20 }}
            onClick={e => e.stopPropagation()}>
            <h3 style={{ fontFamily: 'var(--font-serif)', marginTop: 0 }}>目录</h3>
            {chapters.map((c, i) => (
              <div key={i} style={{
                padding: c.type === 'section' ? '10px 0 6px' : '8px 0',
                cursor: c.type === 'section' ? 'default' : 'pointer',
                borderBottom: c.type === 'section' ? 'none' : '1px solid var(--border)',
                fontSize: c.type === 'section' ? 11 : 13,
                fontWeight: c.type === 'section' ? 300 : (i === currentChapter ? 600 : 400),
                color: c.type === 'section' ? 'var(--ochre)' : (i === currentChapter ? 'var(--ochre)' : 'var(--text)'),
                letterSpacing: c.type === 'section' ? '0.1em' : '0',
                textTransform: c.type === 'section' ? 'uppercase' : 'none',
              }} onClick={() => {
                if (c.type === 'section') return;
                onToggleToc && onToggleToc();
                onChapterChange(i);
              }}>
                {c.title}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
