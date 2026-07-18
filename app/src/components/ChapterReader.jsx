/**
 * ChapterReader — 章节滚动式阅读器
 * 每章一页，上下滑动，底部切换章节
 */
import { useRef, useEffect, useState, useCallback } from 'react';

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
        <h2 style={{
          textAlign: 'center', fontSize: 22, fontWeight: 500, margin: '0 0 32px',
          fontFamily: 'var(--font-serif)', letterSpacing: '0.04em',
        }}>
          {ch.title || `第${currentChapter + 1}章`}
        </h2>

        {/* 内容 — HTML 保留原排版 */}
        {!ch.content && !ch._loaded ? (
          <p style={{ textAlign: 'center', color: 'var(--text-dim)', padding: '40px 0' }}>加载中...</p>
        ) : ch.content ? (() => {
          // 预处理：将夹在两个文本块之间的图片合并为行内图
          const merged = [];
          for (let i = 0; i < ch.content.length; i++) {
            const block = ch.content[i];
            if (block.type === 'image' && i > 0 && i + 1 < ch.content.length
                && ch.content[i-1].type === 'text' && ch.content[i+1].type === 'text') {
              // 行内小图 → 合并到前一个文本块
              const prev = merged[merged.length - 1];
              prev._inlineImg = prev._inlineImg || [];
              prev._inlineImg.push(block);
            } else {
              merged.push({...block});
            }
          }
          return merged.map((block, i) => {
            if (block.type === 'image') {
              return (
                <div key={i} style={{ textAlign: 'center', margin: '16px 0' }}>
                  <img src={block.src} alt={block.alt || ''}
                    loading="lazy" decoding="async"
                    style={{ maxWidth: '100%', maxHeight: '50vh', objectFit: 'contain', borderRadius: 4 }} />
                </div>
              );
            }
            // HTML 内容
            if (block.type === 'html' || (block.value && block.value.startsWith('<') && block.value.includes('>'))) {
              const html = block.value || block.html || '';
              return <div key={i} className="chapter-html" dangerouslySetInnerHTML={{ __html: html }} />;
            }
            if (block._inlineImg) {
              // 文本中间插入行内图
              const parts = [];
              const val = block.value || '';
              // 把图插在文本末尾（引号之后通常是图）
              parts.push(<span key="t">{val}</span>);
              block._inlineImg.forEach((img, j) => {
                parts.push(<img key={`img${j}`} src={img.src} alt={img.alt || ''}
                  loading="lazy" decoding="async"
                  style={{ height: '1.2em', verticalAlign: 'middle', display: 'inline' }} />);
              });
              return <p key={i} style={{ margin: '0 0 0.5em', textIndent: '2em' }}>{parts}</p>;
            }
            return <p key={i} style={{ margin: '0 0 0.5em', textIndent: '2em' }}>{block.value}</p>;
          });
        })()
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
                padding: '8px 0', cursor: 'pointer', borderBottom: '1px solid var(--border)',
                fontSize: 13, fontWeight: i === currentChapter ? 600 : 400,
                color: i === currentChapter ? 'var(--ochre)' : 'var(--text)',
              }} onClick={() => { onToggleToc && onToggleToc(); onChapterChange(i); }}>
                {c.title}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
