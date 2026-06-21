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

// PDF.js — import worker as blob for WebView compat
import pdfjsWorker from 'pdfjs-dist/build/pdf.worker.min.mjs?url';
(async () => {
  try {
    const resp = await fetch(pdfjsWorker);
    const blob = await resp.blob();
    const url = URL.createObjectURL(blob);
    pdfjs.GlobalWorkerOptions.workerSrc = url;
  } catch {
    pdfjs.GlobalWorkerOptions.workerSrc = pdfjsWorker; // fallback
  }
})();

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
  const [showToc, setShowToc] = useState(false);
  const [epubReady, setEpubReady] = useState(false);
  const [epubChapter, setEpubChapter] = useState(0);
  const [epubPage, setEpubPage] = useState(0);
  const [epubTotalPages, setEpubTotalPages] = useState(0);
  // PDF state

  // Notes state
  const [showNotes, setShowNotes] = useState(false);
  const [noteText, setNoteText] = useState('');
  const notesKey = `dp_notes_${bookId}`;

  // Two-page view toggle (default single for mobile)
  const [twoPage, setTwoPage] = useState(true);

  // AI Chat state
  const [showAiChat, setShowAiChat] = useState(false);
  const [aiQuestion, setAiQuestion] = useState('');
  const [aiAnswer, setAiAnswer] = useState('');
  const [aiLoading, setAiLoading] = useState(false);
  const [aiHistory, setAiHistory] = useState([]);
  const aiChatRef = useRef(null);
  const aiBottomRef = useRef(null);

  // AI 聊天自动滚动
  useEffect(() => {
    if (aiBottomRef.current) {
      aiBottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [aiHistory]);

  useEffect(() => { loadBook(); }, [bookId]);

  // Load saved notes on book change
  useEffect(() => {
    try {
      const saved = localStorage.getItem(notesKey);
      if (saved) setNoteText(saved);
      else setNoteText('');
    } catch { setNoteText(''); }
  }, [bookId]);

  // Auto-save reading progress every 30 seconds (PDF) — uses ref to avoid timer reset
  const pdfSaveRef = useRef({ bookId: '', title: '', author: '', page: 0, total: 0 });
  useEffect(() => { if (book && numPages > 0) { pdfSaveRef.current = { bookId, title: book.title, author: book.author, page: pageNumber, total: numPages }; } }, [bookId, book?.title, pageNumber, numPages]);
  useEffect(() => {
    if (fileType !== 'pdf') return;
    const interval = setInterval(() => {
      const s = pdfSaveRef.current;
      if (s.total > 0) saveReadingProgress(s.bookId, s.title, s.author, s.page, s.page / s.total, 'pdf');
    }, 15000);
    return () => clearInterval(interval);
  }, [fileType]);

  // EPUB: save chapter index as progress
  useEffect(() => {
    if (fileType !== 'epub' || !book || epubChapter < 0) return;
    saveReadingProgress(bookId, book.title, book.author, epubChapter, epubChapter / 1, 'epub');
  }, [epubChapter, fileType]);

  // Save progress on page change
  const goToPage = useCallback((n) => {
    const step = (twoPage && numPages > 1) ? 2 : 1;
    const p = Math.max(1, Math.min(numPages, n));
    // snap to odd page in two-page mode
    const finalP = twoPage ? (p % 2 === 0 ? p - 1 : p) : p;
    setPageNumber(finalP);
    if (book) {
      saveReadingProgress(bookId, book.title, book.author, finalP, (finalP / numPages));
    }
  }, [book, bookId, numPages, twoPage]);

  const handleJump = () => {
    const p = parseInt(jumpPage, 10);
    if (p >= 1 && p <= numPages) {
      goToPage(p);
      setJumpPage('');
      setShowJumpInput(false);
    }
  };

  // Save notes — local + cloud
  const saveNotes = () => {
    try {
      localStorage.setItem(notesKey, noteText);
      // Cloud sync
      const token = localStorage.getItem('dp_token');
      if (token) {
        fetch(`${getApiBase()}/api/notes/save`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
          body: JSON.stringify({ book_id: bookId, note_text: noteText }),
          signal: AbortSignal.timeout(5000),
        }).catch(() => {});
      }
    } catch {}
  };

  // 获取当前页文字
  const getCurrentPageText = async () => {
    if (fileType === 'epub') {
      try {
        const contents = epubRenditionRef.current?.getContents?.();
        if (contents?.[0]?.document?.body) {
          return contents[0].document.body.innerText?.trim()?.substring(0, 3000) || '';
        }
      } catch {}
      return '';
    }
    if (fileType === 'pdf') {
      // 从 TextLayer DOM 提取
      const layers = document.querySelectorAll('.react-pdf__Page__textContent');
      return Array.from(layers).map(l => l.textContent).join(' ').substring(0, 3000);
    }
    return '';
  };

  // AI 问答：基于当前阅读内容（流式输出）
  const askAI = async () => {
    if (!aiQuestion.trim() || aiLoading) return;
    const q = aiQuestion.trim();
    const pageText = await getCurrentPageText();
    setAiQuestion('');
    setAiHistory(prev => [...prev, { role: 'user', content: q }, { role: 'assistant', content: '', _streaming: true }]);
    setAiLoading(true);

    const config = JSON.parse(localStorage.getItem('dp_api_config') || '{}');
    // Decrypt if needed
    let apiKey = config.apiKey;
    if (config._encrypted && apiKey && apiKey.includes(':')) {
      const { decryptApiKey } = await import('../data/crypto');
      apiKey = await decryptApiKey(apiKey);
    }
    const apiConfig = { ...config, apiKey };
    const locInfo = fileType === 'epub' ? `章节 ${epubChapter + 1}/${epubTotalChapters || '?'}` : `第${pageNumber}页${numPages ? `（共${numPages}页）` : ''}`;
    const textContext = pageText ? `\n当前页面文字内容：\n"""\n${pageText}\n"""\n` : '';
    const systemPrompt = `你是一位博学的哲学导师。读者正在阅读哲学著作，需要你的帮助理解文本。

当前阅读上下文：
- 书名：《${book?.title}》
- 作者：${book?.author}
- ${locInfo}
${book?.region ? `- 所属传统：${book.region}哲学` : ''}
${textContext}
请根据读者的问题，结合你看到的页面内容以及对这本书和该作者哲学思想的了解，给出深入浅出的解答。`;

    let answer = '';
    try {
      if (apiConfig.apiKey) {
        const baseUrl = (apiConfig.apiUrl || 'https://api.deepseek.com').replace(/\/+$/, '');
        const resp = await fetch(`${baseUrl}/v1/chat/completions`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${apiConfig.apiKey}` },
          body: JSON.stringify({
            model: 'deepseek-chat',
            messages: [
              { role: 'system', content: systemPrompt },
              ...aiHistory.filter(m => !m._streaming).map(m => ({ role: m.role, content: m.content })),
              { role: 'user', content: q },
            ],
            temperature: 0.7, max_tokens: 1024, stream: true,
          }),
          signal: AbortSignal.timeout(60000),
        });

        if (resp.ok) {
          const reader = resp.body.getReader();
          const decoder = new TextDecoder();
          let buffer = '';
          while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop() || '';
            for (const line of lines) {
              if (line.startsWith('data: ')) {
                const data = line.slice(6).trim();
                if (data === '[DONE]') continue;
                try {
                  const delta = JSON.parse(data).choices?.[0]?.delta?.content || '';
                  if (delta) {
                    answer += delta;
                    setAiHistory(prev => {
                      const u = [...prev];
                      const l = { ...u[u.length - 1] };
                      l.content = answer;
                      u[u.length - 1] = l;
                      return u;
                    });
                  }
                } catch {}
              }
            }
          }
        }
      }
    } catch (e) {}

    if (!answer) answer = '无法获取回答。请检查网络连接或在设置中配置 API Key。';
    setAiLoading(false);
    setAiHistory(prev => {
      const u = [...prev];
      const l = { ...u[u.length - 1] };
      l.content = answer;
      delete l._streaming;
      u[u.length - 1] = l;
      return u;
    });

    // Cloud sync: save both user question + AI answer
    const token = localStorage.getItem('dp_token');
    if (token) {
      fetch(`${getApiBase()}/api/book-chat/save`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({ book_id: bookId, role: 'user', content: q }),
        signal: AbortSignal.timeout(5000),
      }).catch(() => {});
      if (answer && answer !== '无法获取回答。请检查网络连接或在设置中配置 API Key。') {
        fetch(`${getApiBase()}/api/book-chat/save`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
          body: JSON.stringify({ book_id: bookId, role: 'assistant', content: answer }),
          signal: AbortSignal.timeout(5000),
        }).catch(() => {});
      }
    }
  };

  // Load AI chat + notes from cloud on book open (if logged in)
  useEffect(() => {
    if (!bookId) return;
    const token = localStorage.getItem('dp_token');
    if (!token) return;
    // Load notes
    fetch(`${getApiBase()}/api/notes/${bookId}`, {
      headers: { 'Authorization': `Bearer ${token}` },
      signal: AbortSignal.timeout(5000),
    }).then(r => r.ok && r.json()).then(d => {
      if (d?.note_text) setNoteText(d.note_text);
    }).catch(() => {});
    // Load AI chat
    fetch(`${getApiBase()}/api/book-chat/${bookId}`, {
      headers: { 'Authorization': `Bearer ${token}` },
      signal: AbortSignal.timeout(5000),
    }).then(r => r.ok && r.json()).then(d => {
      if (d?.messages?.length) setAiHistory(d.messages.map(m => ({ role: m.role, content: m.content })));
    }).catch(() => {});
  }, [bookId]);

  const loadBook = async () => {
    setLoading(true); setError(null);
    const b = await getBookById(bookId);
    if (!b) { setError('书籍未找到'); setLoading(false); return; }
    setBook(b);
    setFileType(b.file_type);

    const url = `${getApiBase()}/api/books/${bookId}/file`;
    setFileUrl(url);
    setLoading(false);
  };

  // Init EPUB — restore saved chapter
  useEffect(() => {
    if (!loading && fileType === 'epub') {
      try {
        const data = JSON.parse(localStorage.getItem('dp_userdata') || '{}');
        const entry = (data.readingHistory || []).find(r => r.bookId === bookId);
        if (entry?.page > 0) setEpubChapter(entry.page);
      } catch {}
    }
  }, [loading, fileType]);

  // PDF callbacks
  const onPdfLoadSuccess = ({ numPages: n }) => {
    setNumPages(n);
    // Restore saved position directly (more reliable than useEffect timing)
    try {
      const data = JSON.parse(localStorage.getItem('dp_userdata') || '{}');
      const entry = (data.readingHistory || []).find(r => r.bookId === bookId);
      if (entry && entry.page > 0 && entry.page <= n) {
        setPageNumber(entry.page);
        saveReadingProgress(bookId, book.title, book.author, entry.page, entry.page / n, 'pdf');
        return;
      }
    } catch {}
    setPageNumber(1);
  };
  const onPdfLoadError = (err) => {
    console.error('PDF load error:', err);
    setError('PDF 加载失败：' + (err?.message || err?.toString?.() || '未知错误'));
  };

  // EPUB init
  const initEpub = (url) => {
    if (!epubViewerRef.current) return;
    const bk = ePub(url, { openAs: 'epub' });
    const vh = epubViewerRef.current.clientHeight || window.innerHeight - 180;
    const rendition = bk.renderTo(epubViewerRef.current, {
      width: '100%', height: vh, flow: 'paginated', spread: 'none',
    });
    epubRenditionRef.current = rendition;
    bk.loaded.navigation.then(nav => { epubTocRef.current = nav.toc || []; }).catch(() => {});
    rendition.on('relocated', (loc) => {
      if (loc?.start?.displayed) {
        setEpubPage(loc.start.displayed.page);
        setEpubTotalPages(loc.start.displayed.total);
      }
    });
    rendition.display();
    setEpubReady(true);
  };

  const goEpubChapter = (ch) => {
    const idx = Math.max(0, ch);
    setEpubChapter(idx);
    const bk = epubRenditionRef.current?.book;
    if (bk?.spine && bk.spine.length > 0) {
      const section = bk.spine.get(Math.min(bk.spine.length - 1, idx));
      if (section?.href) epubRenditionRef.current.display(section.href);
    }
  };

  useEffect(() => {
    if (!loading && fileType === 'epub' && fileUrl && epubViewerRef.current) {
      initEpub(fileUrl);
    }
  }, [loading, fileType, fileUrl]);

  // Two-page toggle for EPUB
  useEffect(() => {
    const r = epubRenditionRef.current;
    if (r && fileType === 'epub') r.spread(twoPage ? 'auto' : 'none');
  }, [twoPage, fileType]);

  // Save on unmount (only when actually leaving the page)
  const saveRef = useRef({ pdfPage: 0, pdfTotal: 0, bookId: '', title: '', author: '' });
  useEffect(() => {
    saveRef.current = { pdfPage: pageNumber, pdfTotal: numPages, bookId, title: book?.title || '', author: book?.author || '' };
  });
  useEffect(() => {
    return () => {
      const s = saveRef.current;
      if (s.pdfTotal > 0) saveReadingProgress(s.bookId, s.title, s.author, s.pdfPage, s.pdfPage / s.pdfTotal, 'pdf');
    };
  }, []);

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
          onClick={() => { setShowNotes(!showNotes); if (!showNotes) setShowAiChat(false); if (showNotes) saveNotes(); }}>
          {showNotes ? '关闭批注' : '📝 批注'}
        </button>
        <button className="btn btn-secondary" style={{ padding: '4px 8px', fontSize: 11 }}
          onClick={() => setTwoPage(!twoPage)}>
          {twoPage ? '📖 单页' : '📖 双页'}
        </button>
        <button className="btn btn-primary" style={{ padding: '4px 8px', fontSize: 11 }}
          onClick={() => { setShowAiChat(!showAiChat); if (!showAiChat) setShowNotes(false); }}>
          {showAiChat ? '关闭问答' : '💬 问AI'}
        </button>
      </div>

      {/* Main area: reader + optional notes panel */}
      <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        {/* Reader */}
        <div style={{ flex: (showNotes || showAiChat) ? '0 0 60%' : 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', background: 'var(--card-bg)', position: 'relative', WebkitOverflowScrolling: 'touch' }}>
          {fileType === 'epub' ? (
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
              <div ref={epubViewerRef} style={{ flex: 1, minHeight: 0 }} />
              <div style={{ flexShrink: 0, background: 'var(--primary)', borderTop: '1px solid var(--border)', padding: '6px 12px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                  <button className="btn btn-secondary" style={{ padding: '4px 8px', fontSize: 11 }}
                    onClick={() => setShowToc(true)}>📑 目录</button>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    {showJumpInput ? (
                      <form onSubmit={e => { e.preventDefault(); const p = parseInt(jumpPage, 10); if (p >= 1 && p <= epubTotalPages) { epubRenditionRef.current?.display(p - 1); setShowJumpInput(false); setJumpPage(''); } }}
                        style={{ display: 'flex', gap: 4, alignItems: 'center' }}>
                        <input type="number" min={1} max={epubTotalPages} value={jumpPage}
                          onChange={e => setJumpPage(e.target.value)}
                          style={{ width: 50, padding: '2px 6px', borderRadius: 6, border: '1px solid var(--accent)', background: 'var(--secondary)', color: 'var(--text)', fontSize: 13, textAlign: 'center' }}
                          autoFocus />
                        <button type="submit" className="btn btn-primary" style={{ padding: '2px 8px', fontSize: 11 }}>跳转</button>
                        <button type="button" className="btn btn-secondary" style={{ padding: '2px 8px', fontSize: 11 }}
                          onClick={() => { setShowJumpInput(false); setJumpPage(''); }}>✕</button>
                      </form>
                    ) : (
                      <span style={{ fontSize: 13, color: 'var(--text-dim)', cursor: 'pointer' }}
                        onClick={() => setShowJumpInput(true)}>
                        {epubPage + 1} / {epubTotalPages || '?'}
                      </span>
                    )}
                  </div>
                  <span style={{ width: 50 }} />
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <button className="btn btn-primary" style={{ padding: '6px 16px', fontSize: 13 }}
                    onClick={() => epubRenditionRef.current?.prev()}>◀ 上一页</button>
                  <button className="btn btn-primary" style={{ padding: '6px 16px', fontSize: 13 }}
                    onClick={() => epubRenditionRef.current?.next()}>下一页 ▶</button>
                </div>
              </div>
              {/* TOC overlay */}
              {showToc && (
                <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.85)', zIndex: 400 }}
                  onClick={() => setShowToc(false)}>
                  <div style={{ maxWidth: 600, margin: '50px auto 0', width: '90%', background: 'var(--primary)', borderRadius: 12, maxHeight: '70vh', overflow: 'auto', padding: 20 }}
                    onClick={e => e.stopPropagation()}>
                    <h3 style={{ color: 'var(--accent)', marginBottom: 12 }}>📑 目录</h3>
                    {epubTocRef.current.map((item, i) => (
                      <div key={i} style={{ padding: '10px 12px', cursor: 'pointer', borderRadius: 8, borderBottom: '1px solid var(--border)', fontSize: 14 }}
                        onClick={() => { epubRenditionRef.current?.display(item.href); setShowToc(false); }}>
                        {item.label}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
              <div style={{ flex: 1, overflow: 'auto', display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '8px 0 8px' }}>
                <Document file={fileUrl} onLoadSuccess={onPdfLoadSuccess} onLoadError={onPdfLoadError}
                  loading={<div className="loading">加载PDF中...</div>}
                  error={<div className="loading">PDF加载失败</div>}>
                  {twoPage ? (
                    <div style={{
                      display: 'flex', justifyContent: 'center', alignItems: 'flex-start',
                      gap: 0, background: 'var(--card-bg)',
                      boxShadow: '0 4px 24px rgba(0,0,0,0.5)',
                      borderRadius: 2,
                    }}>
                      <div style={{
                        borderRight: '1px solid rgba(0,0,0,0.15)',
                        boxShadow: '2px 0 8px rgba(0,0,0,0.1)',
                      }}>
                        <Page pageNumber={pageNumber} scale={pdfScale}
                          renderTextLayer={true} renderAnnotationLayer={false}
                          width={Math.min((window.innerWidth - ((showNotes || showAiChat) ? 260 : 40)) / 2 - 8, 500)} />
                      </div>
                      <div style={{
                        boxShadow: '-2px 0 8px rgba(0,0,0,0.1)',
                      }}>
                        <Page pageNumber={pageNumber + 1} scale={pdfScale}
                          renderTextLayer={true} renderAnnotationLayer={false}
                          width={Math.min((window.innerWidth - ((showNotes || showAiChat) ? 260 : 40)) / 2 - 8, 500)} />
                      </div>
                    </div>
                  ) : (
                    <Page pageNumber={pageNumber} scale={pdfScale}
                      renderTextLayer={true} renderAnnotationLayer={false}
                      width={Math.min(window.innerWidth - ((showNotes || showAiChat) ? 260 : 32), 800)} />
                  )}
                </Document>
              </div>
              {/* PDF controls — flex item, always matches reader width */}
              <div style={{
                flexShrink: 0,
                background: 'var(--primary)', borderTop: '1px solid var(--border)',
                padding: '6px 12px',
              }}>
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
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <button className="btn btn-primary" style={{ padding: '6px 16px', fontSize: 13 }}
                    onClick={() => goToPage(pageNumber - (twoPage ? 2 : 1))} disabled={pageNumber <= 1}>◀ 上一页</button>
                  <button className="btn btn-primary" style={{ padding: '6px 16px', fontSize: 13 }}
                    onClick={() => goToPage(pageNumber + (twoPage ? 2 : 1))} disabled={pageNumber >= numPages}>下一页 ▶</button>
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

      {/* AI Chat sidebar — same style as notes panel */}
      {showAiChat && (
        <div style={{
          flex: '0 0 40%', borderLeft: '1px solid var(--border)',
          background: 'var(--primary)', display: 'flex', flexDirection: 'column',
          overflow: 'hidden',
        }}>
          {/* Header */}
          <div style={{
            padding: '10px 12px', borderBottom: '1px solid var(--border)',
            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
            flexShrink: 0,
          }}>
            <span style={{ fontSize: 12, color: 'var(--accent)', fontWeight: 600 }}>
              💬 AI 伴读 · 第{pageNumber}页
            </span>
            <button onClick={() => setShowAiChat(false)}
              style={{ background: 'none', border: 'none', color: 'var(--text-dim)', fontSize: 16, cursor: 'pointer' }}>
              ✕
            </button>
          </div>
          <div style={{ fontSize: 10, color: 'var(--text-dim)', padding: '4px 12px', lineHeight: 1.4, flexShrink: 0 }}>
            🤖 正在阅读《{book?.title}》（{book?.author}）
          </div>

          {/* Chat history */}
          <div ref={aiChatRef} style={{
            flex: 1, overflow: 'auto', padding: '8px 10px',
            display: 'flex', flexDirection: 'column', gap: 6,
          }}>
            {aiHistory.length === 0 && (
              <div style={{ fontSize: 12, color: 'var(--text-dim)', textAlign: 'center', padding: 20 }}>
                💡 试试问：<br/>
                <span style={{ color: 'var(--accent)' }}>"这段的核心思想是什么？"</span><br/>
                <span style={{ color: 'var(--accent)' }}>"作者想表达什么？"</span>
              </div>
            )}
            {aiHistory.map((msg, i) => (
              <div key={i} style={{
                alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
                maxWidth: '90%',
                background: msg.role === 'user' ? 'var(--accent)' : 'var(--secondary)',
                color: msg.role === 'user' ? 'var(--primary)' : 'var(--text)',
                padding: '6px 10px', borderRadius: 10,
                fontSize: 12, lineHeight: 1.5, whiteSpace: 'pre-wrap', wordBreak: 'break-word',
              }}>
                {msg.content}
              </div>
            ))}
            {aiLoading && (
              <div style={{ alignSelf: 'flex-start', display: 'flex', gap: 4, padding: '6px 10px' }}>
                {[0,1,2].map(i => (
                  <span key={i} style={{
                    width: 6, height: 6, borderRadius: '50%', background: 'var(--accent)',
                    animation: `pulse 0.6s ease-in-out ${i * 0.15}s infinite`,
                  }}/>
                ))}
              </div>
            )}
            <div ref={aiBottomRef} />
          </div>

          {/* Input */}
          <div style={{
            display: 'flex', gap: 6, padding: '8px 10px',
            borderTop: '1px solid var(--border)', flexShrink: 0,
          }}>
            <input
              value={aiQuestion}
              onChange={e => setAiQuestion(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); askAI(); }}}
              placeholder="问AI..."
              disabled={aiLoading}
              autoFocus
              style={{
                flex: 1, padding: '8px 12px', borderRadius: 18,
                border: '1px solid var(--accent)', background: 'var(--secondary)',
                color: 'var(--text)', fontSize: 13, outline: 'none',
              }}
            />
            <button onClick={askAI} disabled={aiLoading}
              style={{
                width: 34, height: 34, borderRadius: '50%', flexShrink: 0,
                border: 'none', background: 'var(--accent)', color: 'var(--primary)',
                fontSize: 16, cursor: 'pointer', fontWeight: 700,
              }}>↑</button>
          </div>
        </div>
      )}
    </div>
  );
}

export default ReaderPage;
