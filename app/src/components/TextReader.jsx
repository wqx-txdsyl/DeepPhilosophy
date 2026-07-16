/**
 * TextReader — 番茄小说式固定页码阅读器（图文混排）
 */
import { useRef, useEffect, useCallback } from 'react';

export default function TextReader({
  pages = [],
  currentPage,
  onPageChange,
  fontSize = 18,
  lineHeight = 1.9,
}) {
  const containerRef = useRef(null);
  const page = pages[currentPage] || pages[0];
  const totalPages = pages.length;

  useEffect(() => {
    const handler = (e) => {
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
      if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
        e.preventDefault(); if (currentPage < totalPages - 1) onPageChange(currentPage + 1);
      } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
        e.preventDefault(); if (currentPage > 0) onPageChange(currentPage - 1);
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [currentPage, totalPages, onPageChange]);

  const handleClick = useCallback((e) => {
    const rect = containerRef.current?.getBoundingClientRect();
    if (!rect) return;
    const x = e.clientX - rect.left;
    if (x < rect.width * 0.3 && currentPage > 0) onPageChange(currentPage - 1);
    else if (x > rect.width * 0.7 && currentPage < totalPages - 1) onPageChange(currentPage + 1);
  }, [currentPage, totalPages, onPageChange]);

  const touchStartX = useRef(0);
  const handleTouchStart = (e) => { touchStartX.current = e.touches[0].clientX; };
  const handleTouchEnd = (e) => {
    const diff = touchStartX.current - e.changedTouches[0].clientX;
    if (Math.abs(diff) > 60) {
      if (diff > 0 && currentPage < totalPages - 1) onPageChange(currentPage + 1);
      else if (diff < 0 && currentPage > 0) onPageChange(currentPage - 1);
    }
  };

  const renderBlock = (block, i) => {
    if (block.type === 'image') {
      return (
        <div key={i} style={{ textAlign: 'center', margin: '12px 0' }}>
          <img src={block.src} alt={block.alt || ''}
            style={{ maxWidth: '100%', maxHeight: '40vh', objectFit: 'contain', borderRadius: 4 }}
          />
          {block.alt && <div style={{ fontSize: 11, color: 'var(--text-dim)', marginTop: 4 }}>{block.alt}</div>}
        </div>
      );
    }
    return <span key={i}>{block.value}</span>;
  };

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      <div ref={containerRef} onClick={handleClick} onTouchStart={handleTouchStart} onTouchEnd={handleTouchEnd}
        style={{
          flex: 1, overflow: 'auto', padding: '20px 24px',
          fontFamily: 'var(--font-serif, "Playfair Display", "PingFang SC", serif)',
          fontSize: fontSize + 'px', lineHeight, color: 'var(--ink)',
          whiteSpace: 'pre-wrap', wordBreak: 'break-word',
          userSelect: 'none', WebkitUserSelect: 'none', cursor: 'default',
        }}>
        {page ? page.blocks ? page.blocks.map(renderBlock) : (page.text || '') : ''}
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        padding: '8px 16px', borderTop: '1px solid var(--border)', background: 'var(--card-bg)', flexShrink: 0 }}>
        <button className="btn btn-secondary" style={{ padding: '4px 10px', fontSize: 12 }}
          onClick={() => currentPage > 0 && onPageChange(currentPage - 1)} disabled={currentPage <= 0}>◀ 上一页</button>
        <span style={{ fontSize: 13, color: 'var(--text-dim)', fontFamily: 'var(--font-sans)' }}>
          {currentPage + 1} / {totalPages || '?'}
        </span>
        <button className="btn btn-secondary" style={{ padding: '4px 10px', fontSize: 12 }}
          onClick={() => currentPage < totalPages - 1 && onPageChange(currentPage + 1)} disabled={currentPage >= totalPages - 1}>
          下一页 <span style={{ display: 'inline-block', transform: 'scaleX(-1)', fontSize: 12 }}>◀</span>
        </button>
      </div>
    </div>
  );
}
