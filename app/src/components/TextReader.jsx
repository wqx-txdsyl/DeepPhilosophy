/**
 * TextReader — 番茄小说式固定页码阅读器
 * Props: pages, currentPage, onPageChange, fontSize, lineHeight
 */
import { useRef, useEffect, useCallback } from 'react';
import Icon from './Icon';

// 默认阅读设置
const DEFAULT_STYLE = {
  fontFamily: 'var(--font-serif, "Playfair Display", "PingFang SC", serif)',
  fontSize: 18,
  lineHeight: 1.9,
  padding: '20px 24px',
  color: 'var(--ink)',
};

export default function TextReader({
  pages = [],
  currentPage,
  onPageChange,
  fontSize = 18,
  lineHeight = 1.9,
  showChapterTitle = null,
  style = {},
}) {
  const containerRef = useRef(null);
  const page = pages[currentPage] || pages[0];
  const totalPages = pages.length;

  // 键盘翻页
  useEffect(() => {
    const handler = (e) => {
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
      if (e.key === 'ArrowRight' || e.key === 'ArrowDown' || e.key === ' ') {
        e.preventDefault();
        if (currentPage < totalPages - 1) onPageChange(currentPage + 1);
      } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
        e.preventDefault();
        if (currentPage > 0) onPageChange(currentPage - 1);
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [currentPage, totalPages, onPageChange]);

  // 点击翻页（左半页=上一页，右半页=下一页）
  const handleClick = useCallback((e) => {
    const rect = containerRef.current?.getBoundingClientRect();
    if (!rect) return;
    const x = e.clientX - rect.left;
    if (x < rect.width * 0.3) {
      if (currentPage > 0) onPageChange(currentPage - 1);
    } else if (x > rect.width * 0.7) {
      if (currentPage < totalPages - 1) onPageChange(currentPage + 1);
    }
  }, [currentPage, totalPages, onPageChange]);

  // 触摸滑动
  const touchStartX = useRef(0);
  const handleTouchStart = (e) => { touchStartX.current = e.touches[0].clientX; };
  const handleTouchEnd = (e) => {
    const diff = touchStartX.current - e.changedTouches[0].clientX;
    if (Math.abs(diff) > 60) {
      if (diff > 0 && currentPage < totalPages - 1) onPageChange(currentPage + 1);
      else if (diff < 0 && currentPage > 0) onPageChange(currentPage - 1);
    }
  };

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      {/* 章节标题 */}
      {showChapterTitle && (
        <div style={{
          padding: '12px 24px 8px', textAlign: 'center',
          fontFamily: DEFAULT_STYLE.fontFamily, fontSize: 16, fontWeight: 500,
          color: 'var(--ink)', opacity: 0.7, borderBottom: '1px solid var(--border)',
        }}>
          {showChapterTitle}
        </div>
      )}

      {/* 阅读内容 */}
      <div
        ref={containerRef}
        onClick={handleClick}
        onTouchStart={handleTouchStart}
        onTouchEnd={handleTouchEnd}
        style={{
          flex: 1, overflow: 'hidden',
          fontFamily: DEFAULT_STYLE.fontFamily,
          fontSize: fontSize + 'px',
          lineHeight: lineHeight,
          padding: DEFAULT_STYLE.padding,
          color: DEFAULT_STYLE.color,
          whiteSpace: 'pre-wrap',
          wordBreak: 'break-word',
          textAlign: 'justify',
          userSelect: 'none',
          WebkitUserSelect: 'none',
          cursor: 'default',
          ...style,
        }}>
        {page ? page.text : ''}
      </div>

      {/* 底部翻页栏 */}
      <div style={{
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        padding: '8px 16px', borderTop: '1px solid var(--border)',
        background: 'var(--card-bg)', flexShrink: 0,
      }}>
        <button className="btn btn-secondary" style={{ padding: '4px 10px', fontSize: 12 }}
          onClick={() => currentPage > 0 && onPageChange(currentPage - 1)}
          disabled={currentPage <= 0}>
          ◀ 上一页
        </button>
        <span style={{ fontSize: 13, color: 'var(--text-dim)', fontFamily: 'var(--font-sans)' }}>
          {currentPage + 1} / {totalPages || '?'}
        </span>
        <button className="btn btn-secondary" style={{ padding: '4px 10px', fontSize: 12 }}
          onClick={() => currentPage < totalPages - 1 && onPageChange(currentPage + 1)}
          disabled={currentPage >= totalPages - 1}>
          下一页 <span style={{ display: 'inline-block', transform: 'scaleX(-1)', fontSize: 12 }}>◀</span>
        </button>
      </div>
    </div>
  );
}
