/**
 * TextReader — 固定页码阅读器（目录 + 双页 + 键盘/触摸翻页）
 */
import { useRef, useEffect, useState, useCallback } from 'react';

export default function TextReader({
  pages = [], currentPage, onPageChange,
  fontSize = 18, lineHeight = 1.9,
  toc = [],
  onTocNavigate,
}) {
  const containerRef = useRef(null);
  const page = pages[currentPage] || pages[0];
  const totalPages = pages.length;
  const [twoPage, setTwoPage] = useState(false);
  const [showToc, setShowToc] = useState(false);

  // 实际显示页码（双页模式跳过偶数页的左半）
  const displayPage = twoPage ? Math.floor(currentPage / 2) * 2 : currentPage;
  const nextPage = displayPage + (twoPage ? 2 : 1);
  const nextPageValid = nextPage < totalPages;

  // 键盘
  useEffect(() => {
    const handler = (e) => {
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
      if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
        e.preventDefault(); if (nextPageValid) onPageChange(nextPage);
      } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
        e.preventDefault(); if (currentPage > 0) onPageChange(Math.max(0, currentPage - (twoPage ? 2 : 1)));
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [currentPage, totalPages, twoPage, nextPageValid, onPageChange, nextPage]);

  // 点击翻页
  const handleClick = useCallback((e) => {
    const rect = containerRef.current?.getBoundingClientRect();
    if (!rect) return;
    const x = e.clientX - rect.left;
    if (x < rect.width * 0.25 && currentPage > 0) onPageChange(Math.max(0, currentPage - (twoPage ? 2 : 1)));
    else if (x > rect.width * 0.75 && nextPageValid) onPageChange(nextPage);
  }, [currentPage, totalPages, twoPage, onPageChange, nextPage, nextPageValid]);

  // 触摸
  const touchStartX = useRef(0);
  const handleTouchStart = (e) => { touchStartX.current = e.touches[0].clientX; };
  const handleTouchEnd = (e) => {
    const diff = touchStartX.current - e.changedTouches[0].clientX;
    if (Math.abs(diff) > 60) {
      if (diff > 0 && nextPageValid) onPageChange(nextPage);
      else if (diff < 0 && currentPage > 0) onPageChange(Math.max(0, currentPage - (twoPage ? 2 : 1)));
    }
  };

  const renderBlock = (block, i) => {
    if (block.type === 'image') {
      return (
        <div key={i} style={{ textAlign: 'center', margin: '8px 0' }}>
          <img src={block.src} alt={block.alt || ''} style={{ maxWidth: '100%', maxHeight: '35vh', objectFit: 'contain', borderRadius: 4 }} />
          {block.alt && <div style={{ fontSize: 10, color: 'var(--text-dim)', marginTop: 3 }}>{block.alt}</div>}
        </div>
      );
    }
    return <span key={i}>{block.value}{'\n\n'}</span>;
  };

  const readerStyle = {
    fontFamily: 'var(--font-serif, "Playfair Display", serif)',
    fontSize: fontSize + 'px', lineHeight,
    color: 'var(--ink)', whiteSpace: 'pre-wrap', wordBreak: 'break-word',
    userSelect: 'none', WebkitUserSelect: 'none',
  };

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      {/* 页面内容 */}
      <div ref={containerRef} onClick={handleClick} onTouchStart={handleTouchStart} onTouchEnd={handleTouchEnd}
        style={{ flex: 1, overflow: 'hidden', display: 'flex' }}>
        {/* 左页 */}
        <div style={{ flex: 1, padding: '20px 8px 20px 24px', overflow: 'hidden', ...readerStyle,
          borderRight: twoPage ? '1px solid var(--border)' : 'none' }}>
          {page ? (page.blocks ? page.blocks.map(renderBlock) : (page.text || '')) : ''}
        </div>
        {/* 右页（双页模式） */}
        {twoPage && pages[displayPage + 1] && (
          <div style={{ flex: 1, padding: '20px 24px 20px 8px', overflow: 'hidden', ...readerStyle }}>
            {pages[displayPage + 1].blocks ? pages[displayPage + 1].blocks.map(renderBlock) : (pages[displayPage + 1].text || '')}
          </div>
        )}
      </div>

      {/* TOC 目录浮层 */}
      {showToc && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)', zIndex: 400, display: 'flex', justifyContent: 'center', alignItems: 'flex-start', paddingTop: 60 }}
          onClick={() => setShowToc(false)}>
          <div style={{ maxWidth: 500, width: '90%', background: 'var(--bg)', borderRadius: 10, maxHeight: '70vh', overflow: 'auto', padding: 20 }}
            onClick={e => e.stopPropagation()}>
            <h3 style={{ fontFamily: 'var(--font-serif)', marginTop: 0 }}>目录</h3>
            {toc.length > 0 ? toc.map((item, i) => (
              <div key={i} style={{ padding: '8px 0', cursor: 'pointer', borderBottom: '1px solid var(--border)', fontSize: 13 }}
                onClick={() => { setShowToc(false); if (onTocNavigate) onTocNavigate(item); }}>
                {item.title || item.label}
              </div>
            )) : (
              <p style={{ color: 'var(--text-dim)', fontSize: 12 }}>暂无目录</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
