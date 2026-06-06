/**
 * 内嵌阅读器 — 支持 PDF 和 EPUB
 */
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { Document, Page, pdfjs } from 'react-pdf';
import ePub from 'epubjs';
import { getApiBase } from '../App';
import { getBookById } from '../data';
import 'react-pdf/dist/Page/AnnotationLayer.css';
import 'react-pdf/dist/Page/TextLayer.css';

// Setup PDF.js worker
import pdfjsWorker from 'pdfjs-dist/build/pdf.worker.min.mjs?url';
pdfjs.GlobalWorkerOptions.workerSrc = pdfjsWorker;

function ReaderPage() {
  const { bookId } = useParams();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const [book, setBook] = useState(null);
  const [fileUrl, setFileUrl] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // PDF state
  const [numPages, setNumPages] = useState(0);
  const [pageNumber, setPageNumber] = useState(1);
  const [pdfScale, setPdfScale] = useState(1.0);
  const pdfContainerRef = useRef(null);

  // EPUB state
  const epubViewerRef = useRef(null);
  const epubBookRef = useRef(null);
  const epubRenditionRef = useRef(null);
  const epubTocRef = useRef([]);
  const [epubReady, setEpubReady] = useState(false);
  const [currentChapter, setCurrentChapter] = useState('');
  const [showToc, setShowToc] = useState(false);

  const fileType = searchParams.get('type') || book?.file_type;

  useEffect(() => {
    loadBook();
  }, [bookId]);

  const loadBook = async () => {
    const b = await getBookById(bookId);
    if (!b) { setError('书籍未找到'); setLoading(false); return; }
    setBook(b);

    const url = `${getApiBase()}/api/books/${bookId}/file`;
    setFileUrl(url);

    if (b.file_type === 'epub') {
      initEpub(url);
    }
    setLoading(false);
  };

  // ---- PDF logic ----
  const onPdfLoadSuccess = ({ numPages }) => {
    setNumPages(numPages);
    setPageNumber(1);
  };

  const goToPrevPage = () => setPageNumber(p => Math.max(1, p - 1));
  const goToNextPage = () => setPageNumber(p => Math.min(numPages, p + 1));
  const zoomIn = () => setPdfScale(s => Math.min(3, s + 0.2));
  const zoomOut = () => setPdfScale(s => Math.max(0.4, s - 0.2));

  // ---- EPUB logic ----
  const initEpub = (url) => {
    try {
      const book = ePub(url);
      epubBookRef.current = book;
      book.loaded.navigation.then(nav => {
        epubTocRef.current = nav.toc || [];
      });

      if (epubViewerRef.current) {
        const rendition = book.renderTo(epubViewerRef.current, {
          width: '100%',
          height: '100%',
          flow: 'paginated',
          spread: 'none',
        });
        epubRenditionRef.current = rendition;

        rendition.hooks.render.register((section) => {
          setCurrentChapter(section.href || '');
        });

        const startCfi = rendition.location?.start?.cfi;
        rendition.display(startCfi);

        setEpubReady(true);
      }
    } catch (e) {
      console.error('EPUB init error:', e);
      setError('EPUB 加载失败');
    }
  };

  const goToEpubPrev = () => {
    epubRenditionRef.current?.prev();
  };
  const goToEpubNext = () => {
    epubRenditionRef.current?.next();
  };
  const goToChapter = (href) => {
    epubRenditionRef.current?.display(href);
    setShowToc(false);
  };

  // Cleanup EPUB on unmount
  useEffect(() => {
    return () => {
      if (epubRenditionRef.current) {
        epubRenditionRef.current.destroy();
      }
    };
  }, []);

  if (loading) return <div className="loading">加载中...</div>;
  if (error) return (
    <div className="page-container">
      <div className="empty-state">
        <p style={{ fontSize: 40 }}>😞</p>
        <p>{error}</p>
        <button className="btn btn-secondary" onClick={() => navigate(-1)}
          style={{ marginTop: 16 }}>← 返回</button>
      </div>
    </div>
  );

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - var(--header-height))' }}>
      {/* Top bar */}
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '8px 12px', background: 'var(--primary)',
        borderBottom: '1px solid var(--border)', gap: 8,
      }}>
        <button className="btn btn-secondary" onClick={() => navigate(-1)}
          style={{ padding: '4px 10px', fontSize: 13 }}>← 返回</button>
        <span style={{ fontSize: 12, color: 'var(--text)', flex: 1, textAlign: 'center',
          overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          {book?.title}
        </span>
        <span className="badge badge-available" style={{ fontSize: 10 }}>
          {(fileType || book?.file_type)?.toUpperCase()}
        </span>
      </div>

      {/* Reader area */}
      <div style={{ flex: 1, overflow: 'auto', background: '#1a1a1a' }}>
        {fileType === 'epub' ? (
          /* ---- EPUB ---- */
          <div style={{ position: 'relative', height: '100%' }}>
            <div ref={epubViewerRef} style={{ width: '100%', height: '100%', overflow: 'hidden' }} />

            {/* EPUB controls */}
            {epubReady && (
              <div style={{
                position: 'fixed', bottom: 0, left: 0, right: 0,
                display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                padding: '8px 16px', background: 'var(--primary)',
                borderTop: '1px solid var(--border)', zIndex: 200,
                maxWidth: 480, margin: '0 auto',
                paddingBottom: 'calc(8px + env(safe-area-inset-bottom))',
              }}>
                <button className="btn btn-secondary" style={{ padding: '4px 12px', fontSize: 13 }}
                  onClick={goToEpubPrev}>◀ 上一页</button>
                <button className="btn btn-secondary" style={{ padding: '4px 12px', fontSize: 13 }}
                  onClick={() => setShowToc(!showToc)}>
                  {showToc ? '关闭目录' : '📑 目录'}
                </button>
                <button className="btn btn-secondary" style={{ padding: '4px 12px', fontSize: 13 }}
                  onClick={goToEpubNext}>下一页 ▶</button>
              </div>
            )}

            {/* TOC overlay */}
            {showToc && (
              <div style={{
                position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
                background: 'rgba(0,0,0,0.8)', zIndex: 300,
                display: 'flex', flexDirection: 'column',
              }} onClick={() => setShowToc(false)}>
                <div style={{
                  maxWidth: 480, margin: '60px auto 0', width: '90%',
                  background: 'var(--primary)', borderRadius: 12,
                  maxHeight: '70vh', overflow: 'auto', padding: 16,
                }} onClick={e => e.stopPropagation()}>
                  <h3 style={{ color: 'var(--accent)', marginBottom: 12 }}>📑 目录</h3>
                  {epubTocRef.current.map((item, i) => (
                    <div key={i} style={{
                      padding: '8px 12px', cursor: 'pointer', borderRadius: 8,
                      borderBottom: '1px solid var(--border)',
                      color: currentChapter === item.href ? 'var(--accent)' : 'var(--text)',
                    }} onClick={() => goToChapter(item.href)}>
                      {item.label}
                      {item.subitems?.map((sub, j) => (
                        <div key={j} style={{
                          padding: '4px 12px', fontSize: 12, color: 'var(--text-dim)',
                        }} onClick={(e) => { e.stopPropagation(); goToChapter(sub.href); }}>
                          {sub.label}
                        </div>
                      ))}
                    </div>
                  ))}
                  {!epubTocRef.current.length && (
                    <p style={{ color: 'var(--text-dim)', fontSize: 13 }}>无目录</p>
                  )}
                </div>
              </div>
            )}
          </div>
        ) : (
          /* ---- PDF ---- */
          <div ref={pdfContainerRef} style={{
            display: 'flex', flexDirection: 'column', alignItems: 'center',
            padding: '8px 0 80px',
          }}>
            <Document
              file={fileUrl}
              onLoadSuccess={onPdfLoadSuccess}
              loading={<div className="loading">加载PDF中...</div>}
              error={<div className="loading">PDF加载失败，请确认文件存在</div>}
            >
              <Page
                pageNumber={pageNumber}
                scale={pdfScale}
                renderTextLayer={true}
                renderAnnotationLayer={false}
                width={pdfContainerRef.current?.clientWidth ? pdfContainerRef.current.clientWidth - 16 : 350}
              />
            </Document>

            {/* PDF controls */}
            <div style={{
              position: 'fixed', bottom: 0, left: 0, right: 0,
              background: 'var(--primary)', borderTop: '1px solid var(--border)',
              padding: '8px 16px', zIndex: 200, maxWidth: 480, margin: '0 auto',
              paddingBottom: 'calc(8px + env(safe-area-inset-bottom))',
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                <button className="btn btn-secondary" style={{ padding: '4px 10px', fontSize: 11 }}
                  onClick={zoomOut}>🔍−</button>
                <span style={{ fontSize: 12, color: 'var(--text-dim)' }}>
                  {pageNumber} / {numPages}
                </span>
                <button className="btn btn-secondary" style={{ padding: '4px 10px', fontSize: 11 }}
                  onClick={zoomIn}>🔍+</button>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <button className="btn btn-primary" style={{ padding: '6px 16px', fontSize: 13 }}
                  onClick={goToPrevPage} disabled={pageNumber <= 1}>◀ 上一页</button>
                <button className="btn btn-primary" style={{ padding: '6px 16px', fontSize: 13 }}
                  onClick={goToNextPage} disabled={pageNumber >= numPages}>下一页 ▶</button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default ReaderPage;
