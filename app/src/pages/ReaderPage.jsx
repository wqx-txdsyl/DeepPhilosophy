/**
 * 阅读器 — PDF (react-pdf) + EPUB (epubjs)
 */
import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Document, Page, pdfjs } from 'react-pdf';
import ePub from 'epubjs';
import { Capacitor } from '@capacitor/core';
import { getApiBase } from '../App';
import { getBookById } from '../data';
import 'react-pdf/dist/Page/AnnotationLayer.css';
import 'react-pdf/dist/Page/TextLayer.css';

// Setup PDF.js worker (local bundled file)
import pdfjsWorker from 'pdfjs-dist/build/pdf.worker.min.mjs?url';
pdfjs.GlobalWorkerOptions.workerSrc = pdfjsWorker;

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

  // EPUB state
  const epubViewerRef = useRef(null);
  const epubRenditionRef = useRef(null);
  const epubTocRef = useRef([]);
  const [epubReady, setEpubReady] = useState(false);
  const [showToc, setShowToc] = useState(false);

  useEffect(() => { loadBook(); }, [bookId]);

  const loadBook = async () => {
    setLoading(true);
    setError(null);
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
    if (!url) {
      url = `${getApiBase()}/api/books/${bookId}/file`;
    }
    setFileUrl(url);

    if (b.file_type === 'epub') {
      // Delay EPUB init to let DOM render
      setTimeout(() => initEpub(url), 100);
    }
    setLoading(false);
  };

  // ---- PDF ----
  const onPdfLoadSuccess = ({ numPages: n }) => {
    setNumPages(n);
    setPageNumber(1);
  };
  const onPdfLoadError = (err) => {
    console.error('PDF load error:', err);
    setError('PDF 加载失败：' + (err.message || '未知错误'));
  };

  // ---- EPUB ----
  const initEpub = (url) => {
    try {
      if (!epubViewerRef.current) return;
      const book = ePub(url, { openAs: 'epub' });
      const rendition = book.renderTo(epubViewerRef.current, {
        width: '100%', height: '100%',
        flow: 'paginated', spread: 'none',
      });
      epubRenditionRef.current = rendition;

      book.loaded.navigation.then(nav => {
        epubTocRef.current = nav.toc || [];
      }).catch(() => {});

      rendition.display();
      setEpubReady(true);
    } catch (e) {
      console.error('EPUB error:', e);
      setError('EPUB 加载失败：' + e.message);
    }
  };

  // Cleanup
  useEffect(() => {
    return () => {
      epubRenditionRef.current?.destroy();
    };
  }, []);

  if (loading) return <div className="loading">加载中...</div>;
  if (error) return (
    <div className="page-container">
      <button className="btn btn-secondary" onClick={() => navigate(-1)}
        style={{ marginBottom: 16 }}>← 返回</button>
      <div className="card" style={{ cursor: 'default' }}>
        <p style={{ fontSize: 40, textAlign: 'center' }}>😞</p>
        <p style={{ textAlign: 'center' }}>{error}</p>
      </div>
    </div>
  );
  if (!book) return <div className="loading">加载中...</div>;
  if (!fileUrl) return <div className="loading">正在获取文件...</div>;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
      {/* Top bar */}
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '8px 12px', background: 'var(--primary)',
        borderBottom: '1px solid var(--border)',
      }}>
        <button className="btn btn-secondary" onClick={() => navigate(-1)}
          style={{ padding: '4px 10px', fontSize: 13 }}>← 返回</button>
        <span style={{ fontSize: 13, color: 'var(--text)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', flex: 1, textAlign: 'center' }}>
          {book.title}
        </span>
      </div>

      {/* Reader area */}
      <div style={{ flex: 1, overflow: 'auto', background: '#1a1a1a' }}>
        {fileType === 'epub' ? (
          <div style={{ position: 'relative', height: '100%' }}>
            <div ref={epubViewerRef} style={{ width: '100%', height: '100%' }} />
            {/* EPUB controls */}
            <div style={{
              position: 'fixed', bottom: 0, left: 0, right: 0,
              display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              padding: '8px 16px', background: 'var(--primary)',
              borderTop: '1px solid var(--border)', zIndex: 200,
              maxWidth: 480, margin: '0 auto',
            }}>
              <button className="btn btn-secondary" style={{ padding: '6px 14px', fontSize: 13 }}
                onClick={() => epubRenditionRef.current?.prev()}>◀</button>
              <button className="btn btn-secondary" style={{ padding: '6px 14px', fontSize: 12 }}
                onClick={() => setShowToc(!showToc)}>
                {showToc ? '关闭' : '目录'}
              </button>
              <button className="btn btn-secondary" style={{ padding: '6px 14px', fontSize: 13 }}
                onClick={() => epubRenditionRef.current?.next()}>▶</button>
            </div>
            {/* TOC */}
            {showToc && (
              <div style={{
                position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
                background: 'rgba(0,0,0,0.85)', zIndex: 300,
                display: 'flex', flexDirection: 'column',
              }} onClick={() => setShowToc(false)}>
                <div style={{
                  maxWidth: 480, margin: '50px auto 0', width: '90%',
                  background: 'var(--primary)', borderRadius: 12,
                  maxHeight: '70vh', overflow: 'auto', padding: 16,
                }} onClick={e => e.stopPropagation()}>
                  <h3 style={{ color: 'var(--accent)', marginBottom: 12 }}>目录</h3>
                  {epubTocRef.current.map((item, i) => (
                    <div key={i} style={{
                      padding: '8px 12px', cursor: 'pointer', borderRadius: 8,
                      borderBottom: '1px solid var(--border)',
                    }} onClick={() => { epubRenditionRef.current?.display(item.href); setShowToc(false); }}>
                      {item.label}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          /* PDF */
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '8px 0 80px' }}>
            <Document
              file={fileUrl}
              onLoadSuccess={onPdfLoadSuccess}
              onLoadError={onPdfLoadError}
              loading={<div className="loading">加载PDF中...</div>}
              error={<div className="loading">PDF加载失败</div>}
            >
              <Page
                pageNumber={pageNumber}
                scale={pdfScale}
                renderTextLayer={false}
                renderAnnotationLayer={false}
                width={window.innerWidth > 480 ? 440 : window.innerWidth - 32}
              />
            </Document>
            {/* PDF controls */}
            <div style={{
              position: 'fixed', bottom: 0, left: 0, right: 0,
              background: 'var(--primary)', borderTop: '1px solid var(--border)',
              padding: '8px 16px', zIndex: 200, maxWidth: 480, margin: '0 auto',
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                <button className="btn btn-secondary" style={{ padding: '4px 10px', fontSize: 11 }}
                  onClick={() => setPdfScale(s => Math.max(0.4, s - 0.2))}>🔍−</button>
                <span style={{ fontSize: 12, color: 'var(--text-dim)' }}>
                  {pageNumber} / {numPages}
                </span>
                <button className="btn btn-secondary" style={{ padding: '4px 10px', fontSize: 11 }}
                  onClick={() => setPdfScale(s => Math.min(3, s + 0.2))}>🔍+</button>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <button className="btn btn-primary" style={{ padding: '6px 16px', fontSize: 13 }}
                  onClick={() => setPageNumber(p => Math.max(1, p - 1))} disabled={pageNumber <= 1}>◀ 上一页</button>
                <button className="btn btn-primary" style={{ padding: '6px 16px', fontSize: 13 }}
                  onClick={() => setPageNumber(p => Math.min(numPages, p + 1))} disabled={pageNumber >= numPages}>下一页 ▶</button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default ReaderPage;
