/**
 * 阅读器 — PDF (react-pdf) + EPUB (epubjs)
 * 支持：页数跳转、批注笔记、阅读进度自动保存
 */
import { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Document, Page, pdfjs } from 'react-pdf';
import ePub from 'epubjs';
import { Capacitor } from '@capacitor/core';
import { getApiBase } from '../App';
import { getBookById } from '../data';
import { saveReadingProgress } from '../data/userData';
import 'react-pdf/dist/Page/AnnotationLayer.css';
import 'react-pdf/dist/Page/TextLayer.css';

pdfjs.GlobalWorkerOptions.workerSrc = `https://unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;

function ReaderPage() {
  const { bookId } = useParams();
  const navigate = useNavigate();

  const [book, setBook] = useState(null);
  const [fileUrl, setFileUrl] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [fileType, setFileType] = useState(null);

  // PDF state
  const [numPages, setNumPages] = useState(0);
  const [pageNumber, setPageNumber] = useState(1);
  const [pdfScale, setPdfScale] = useState(1.0);
  const [jumpPage, setJumpPage] = useState('');
  const [showJumpInput, setShowJumpInput] = useState(false);

  // EPUB state
  const epubViewerRef = useRef(null);
  const epubRenditionRef = useRef(null);
  const epubTocRef = useRef([]);
  const [epubReady, setEpubReady] = useState(false);
  const [showToc, setShowToc] = useState(false);

  // Notes state
  const [showNotes, setShowNotes] = useState(false);
  const [noteText, setNoteText] = useState('');
  const notesKey = `dp_notes_${bookId}`;

  useEffect(() => { loadBook(); }, [bookId]);

  // Load saved notes on book change
  useEffect(() => {
    try {
      const saved = localStorage.getItem(notesKey);
      if (saved) setNoteText(saved);
      else setNoteText('');
    } catch { setNoteText(''); }
  }, [bookId]);

  // Load saved page from reading history
  useEffect(() => {
    if (!book || numPages === 0) return;
    try {
      const data = JSON.parse(localStorage.getItem('dp_userdata') || '{}');
      const entry = (data.readingHistory || []).find(r => r.bookId === bookId);
      if (entry && entry.page > 0 && entry.page <= numPages) {
        setPageNumber(entry.page);
      }
    } catch {}
  }, [book, numPages]);

  // Auto-save reading progress every 30 seconds
  useEffect(() => {
    if (!book || numPages === 0) return;
    const interval = setInterval(() => {
      saveReadingProgress(bookId, book.title, book.author, pageNumber, (pageNumber / numPages));
    }, 30000);
    return () => clearInterval(interval);
  }, [book, numPages, pageNumber]);

  // Save progress on page change
  const goToPage = useCallback((n) => {
    const p = Math.max(1, Math.min(numPages, n));
    setPageNumber(p);
    if (book) {
      saveReadingProgress(bookId, book.title, book.author, p, (p / numPages));
    }
  }, [book, bookId, numPages]);

  const handleJump = () => {
    const p = parseInt(jumpPage, 10);
    if (p >= 1 && p <= numPages) {
      goToPage(p);
      setJumpPage('');
      setShowJumpInput(false);
    }
  };

  // Save notes
  const saveNotes = () => {
    try {
      localStorage.setItem(notesKey, noteText);
    } catch {}
  };

  const loadBook = async () => {
    setLoading(true); setError(null);
    const b = await getBookById(bookId);
    if (!b) { setError('书籍未找到'); setLoading(false); return; }
    setBook(b);
    setFileType(b.file_type);

    let url;
    if (Capacitor.isNativePlatform()) {
      const config = JSON.parse(localStorage.getItem('dp_api_config') || '{}');
      const basePath = config.booksPath || '';
      if (basePath && b.path) {
        url = Capacitor.convertFileSrc(basePath.replace(/\/$/, '') + '/' + b.path);
      }
    }
    if (!url) url = `${getApiBase()}/api/books/${bookId}/file`;
    setFileUrl(url);

    if (b.file_type === 'epub') {
      setTimeout(() => initEpub(url), 100);
    }
    setLoading(false);
  };

  // PDF callbacks
  const onPdfLoadSuccess = ({ numPages: n }) => {
    setNumPages(n);
    goToPage(1);
  };

  // EPUB init
  const initEpub = (url) => {
    try {
      if (!epubViewerRef.current) return;
      const bk = ePub(url, { openAs: 'epub' });
      const rendition = bk.renderTo(epubViewerRef.current, {
        width: '100%', height: '100%', flow: 'paginated', spread: 'none',
      });
      epubRenditionRef.current = rendition;
      bk.loaded.navigation.then(nav => { epubTocRef.current = nav.toc || []; }).catch(() => {});
      rendition.display();
      setEpubReady(true);
    } catch (e) { setError('EPUB 加载失败：' + e.message); }
  };

  useEffect(() => { return () => { epubRenditionRef.current?.destroy(); }; }, []);

  if (loading) return <div className="loading">加载中...</div>;
  if (error) return (
    <div className="page-container">
      <button className="btn btn-secondary" onClick={() => navigate(-1)} style={{ marginBottom: 16 }}>← 返回</button>
      <div className="card"><p style={{ textAlign: 'center', fontSize: 40 }}>😞</p><p style={{ textAlign: 'center' }}>{error}</p></div>
    </div>
  );
  if (!book || !fileUrl) return <div className="loading">正在获取文件...</div>;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
      {/* Top bar */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 8,
        padding: '6px 10px', background: 'var(--primary)', borderBottom: '1px solid var(--border)',
      }}>
        <button className="btn btn-secondary" style={{ padding: '4px 8px', fontSize: 12 }}
          onClick={() => navigate(-1)}>←</button>
        <span style={{ fontSize: 12, color: 'var(--text)', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          {book.title}
        </span>
        <button className="btn btn-secondary" style={{ padding: '4px 8px', fontSize: 11 }}
          onClick={() => { setShowNotes(!showNotes); if (showNotes) saveNotes(); }}>
          {showNotes ? '关闭批注' : '📝 批注'}
        </button>
      </div>

      {/* Main area: reader + optional notes panel */}
      <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        {/* Reader */}
        <div style={{ flex: showNotes ? '0 0 60%' : 1, overflow: 'auto', background: '#1a1a1a' }}>
          {fileType === 'epub' ? (
            <div style={{ position: 'relative', height: '100%' }}>
              <div ref={epubViewerRef} style={{ width: '100%', height: '100%' }} />
              <div style={{
                position: 'fixed', bottom: 0, left: 0, right: 0,
                display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                padding: '8px 16px', background: 'var(--primary)',
                borderTop: '1px solid var(--border)', zIndex: 200, maxWidth: 480, margin: '0 auto',
              }}>
                <button className="btn btn-secondary" style={{ padding: '6px 14px', fontSize: 13 }}
                  onClick={() => epubRenditionRef.current?.prev()}>◀</button>
                <button className="btn btn-secondary" style={{ padding: '6px 14px', fontSize: 12 }}
                  onClick={() => setShowToc(!showToc)}>{showToc ? '关闭' : '目录'}</button>
                <button className="btn btn-secondary" style={{ padding: '6px 14px', fontSize: 13 }}
                  onClick={() => epubRenditionRef.current?.next()}>▶</button>
              </div>
              {showToc && (
                <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.85)', zIndex: 300 }}
                  onClick={() => setShowToc(false)}>
                  <div style={{ maxWidth: 480, margin: '50px auto 0', width: '90%', background: 'var(--primary)', borderRadius: 12, maxHeight: '70vh', overflow: 'auto', padding: 16 }}
                    onClick={e => e.stopPropagation()}>
                    <h3 style={{ color: 'var(--accent)', marginBottom: 12 }}>目录</h3>
                    {epubTocRef.current.map((item, i) => (
                      <div key={i} style={{ padding: '8px 12px', cursor: 'pointer', borderRadius: 8, borderBottom: '1px solid var(--border)' }}
                        onClick={() => { epubRenditionRef.current?.display(item.href); setShowToc(false); }}>
                        {item.label}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '8px 0 120px' }}>
              <Document file={fileUrl} onLoadSuccess={onPdfLoadSuccess}
                loading={<div className="loading">加载PDF中...</div>}
                error={<div className="loading">PDF加载失败</div>}>
                <Page pageNumber={pageNumber} scale={pdfScale}
                  renderTextLayer={false} renderAnnotationLayer={false}
                  width={Math.min(440, window.innerWidth - (showNotes ? 180 : 32))} />
              </Document>
              {/* PDF controls */}
              <div style={{
                position: 'fixed', bottom: 0, left: 0, right: 0,
                background: 'var(--primary)', borderTop: '1px solid var(--border)',
                padding: '8px 12px', zIndex: 200, maxWidth: 480, margin: '0 auto',
              }}>
                {/* Zoom + Page display */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                  <button className="btn btn-secondary" style={{ padding: '4px 8px', fontSize: 11 }}
                    onClick={() => setPdfScale(s => Math.max(0.4, s - 0.2))}>🔍−</button>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    {showJumpInput ? (
                      <form onSubmit={e => { e.preventDefault(); handleJump(); }}
                        style={{ display: 'flex', gap: 4, alignItems: 'center' }}>
                        <input type="number" min={1} max={numPages} value={jumpPage}
                          onChange={e => setJumpPage(e.target.value)}
                          style={{ width: 50, padding: '2px 6px', borderRadius: 6, border: '1px solid var(--accent)',
                            background: 'var(--secondary)', color: 'var(--text)', fontSize: 13, textAlign: 'center' }}
                          autoFocus />
                        <button type="submit" className="btn btn-primary" style={{ padding: '2px 8px', fontSize: 11 }}>跳转</button>
                        <button type="button" className="btn btn-secondary" style={{ padding: '2px 8px', fontSize: 11 }}
                          onClick={() => { setShowJumpInput(false); setJumpPage(''); }}>✕</button>
                      </form>
                    ) : (
                      <span style={{ fontSize: 13, color: 'var(--text-dim)', cursor: 'pointer' }}
                        onClick={() => setShowJumpInput(true)}>
                        {pageNumber} / {numPages}
                      </span>
                    )}
                  </div>
                  <button className="btn btn-secondary" style={{ padding: '4px 8px', fontSize: 11 }}
                    onClick={() => setPdfScale(s => Math.min(3, s + 0.2))}>🔍+</button>
                </div>
                {/* Prev/Next */}
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <button className="btn btn-primary" style={{ padding: '6px 16px', fontSize: 13 }}
                    onClick={() => goToPage(pageNumber - 1)} disabled={pageNumber <= 1}>◀ 上一页</button>
                  <button className="btn btn-primary" style={{ padding: '6px 16px', fontSize: 13 }}
                    onClick={() => goToPage(pageNumber + 1)} disabled={pageNumber >= numPages}>下一页 ▶</button>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Notes sidebar */}
        {showNotes && (
          <div style={{
            flex: '0 0 40%', borderLeft: '1px solid var(--border)',
            background: 'var(--primary)', padding: 12,
            display: 'flex', flexDirection: 'column', overflow: 'auto',
          }}>
            <div style={{ fontSize: 11, color: 'var(--text-dim)', marginBottom: 6 }}>
              📝 阅读批注 · 第{pageNumber}页
            </div>
            <textarea
              value={noteText}
              onChange={e => setNoteText(e.target.value)}
              onBlur={saveNotes}
              placeholder="在这里写下你的思考和笔记..."
              style={{
                flex: 1, width: '100%', minHeight: 200,
                background: 'var(--secondary)', color: 'var(--text)',
                border: '1px solid var(--border)', borderRadius: 8,
                padding: 10, fontSize: 13, lineHeight: 1.6,
                resize: 'none', outline: 'none',
              }}
            />
            <button className="btn btn-primary btn-block" style={{ marginTop: 8, padding: '6px', fontSize: 12 }}
              onClick={saveNotes}>💾 保存批注</button>
            <button className="btn btn-secondary btn-block" style={{ marginTop: 4, padding: '6px', fontSize: 12 }}
              onClick={() => { navigator.clipboard?.writeText(noteText); }}>
              📋 复制全部
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export default ReaderPage;
