/**
 * 阅读器 — PDF (react-pdf) + EPUB (epubjs)
 * 支持：页数跳转、批注笔记、阅读进度自动保存
 */
import { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import Icon from '../components/Icon';
import { Document, Page, pdfjs } from 'react-pdf';
import ePub from 'epubjs';
import { getApiBase } from '../App';
import { getBookById } from '../data';
import { saveReadingProgress } from '../data/userData';
import ChapterReader from '../components/ChapterReader';
import 'react-pdf/dist/Page/AnnotationLayer.css';
import 'react-pdf/dist/Page/TextLayer.css';

pdfjs.GlobalWorkerOptions.workerSrc = `https://unpkg.com/pdfjs-dist@5.4.296/build/pdf.worker.min.mjs`;

function ReaderPage() {
  const { bookId } = useParams();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const [book, setBook] = useState(null);
  const [fileUrl, setFileUrl] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const pageCacheRef = useRef({});
  const [fileType, setFileType] = useState(null);
  const cacheReadyRef = useRef(false);
  // 章节阅读
  const [textChapters, setTextChapters] = useState([]);
  const [textChapter, setTextChapter] = useState(0);
  const [textToc, setTextToc] = useState([]);
  const [textLoading, setTextLoading] = useState(false);
  const [textReady, setTextReady] = useState(false);
  const [useEpubFallback, setUseEpubFallback] = useState(false);

  // 预加载页数缓存（确保 initEpub 之前就绪）
  useEffect(() => {
    fetch('/epub_pages.json')
      .then(r => r.json())
      .then(d => {
        pageCacheRef.current = d.byTitle || {};
        cacheReadyRef.current = true;
      })
      .catch(() => { cacheReadyRef.current = true; });
  }, []);

  // PDF state
  const [numPages, setNumPages] = useState(0);
  const [pageNumber, setPageNumber] = useState(1);
  const [pdfScale, setPdfScale] = useState(0.99); // 略低于1.0避免亚像素渲染伪影
  const [jumpPage, setJumpPage] = useState('');
  const [showJumpInput, setShowJumpInput] = useState(false);

  // EPUB state
  const epubViewerRef = useRef(null);
  const epubRenditionRef = useRef(null);
  const epubTocRef = useRef([]);
  const chapterPagesRef = useRef([]);
  const pageTotalFixed = useRef(false);
  const [showToc, setShowToc] = useState(false);
  const [epubReady, setEpubReady] = useState(false);
  const [epubPage, setEpubPage] = useState(0);
  const [epubTotalChapters, setEpubTotalChapters] = useState(0);
  const [epubBookPage, setEpubBookPage] = useState(1);
  const [epubBookTotal, setEpubBookTotal] = useState(0);
  const [epubPercent, setEpubPercent] = useState(0);
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

  // Load saved notes on book change — cloud first, localStorage fallback
  useEffect(() => {
    const loadNotes = async () => {
      const token = localStorage.getItem('dp_token');
      if (token) {
        try {
          const r = await fetch(`${getApiBase()}/api/notes/load?book_id=${encodeURIComponent(bookId)}`, {
            headers: { 'Authorization': `Bearer ${token}` },
            signal: AbortSignal.timeout(5000),
          });
          if (r.ok) {
            const d = await r.json();
            if (d.note_text) { setNoteText(d.note_text); localStorage.setItem(notesKey, d.note_text); return; }
          }
        } catch { /* network error, fall through to local */ }
      }
      try {
        const saved = localStorage.getItem(notesKey);
        if (saved) setNoteText(saved);
        else setNoteText('');
      } catch { setNoteText(''); }
    };
    loadNotes();
  }, [bookId]);

  // Save on unmount (PDF)
  const pdfSaveRef = useRef({ bookId: '', title: '', author: '', page: 0, total: 0 });
  useEffect(() => { if (book && numPages > 0) { pdfSaveRef.current = { bookId, title: book.title, author: book.author, page: pageNumber, total: numPages }; } }, [bookId, book?.title, pageNumber, numPages]);
  useEffect(() => {
    return () => {
      const s = pdfSaveRef.current;
      if (s.total > 0) saveReadingProgress(s.bookId, s.title, s.author, s.page, s.page / s.total, 'pdf');
    };
  }, []);

  // EPUB: 用百分比保存进度（EPUB 无固定页码）
  useEffect(() => {
    if (fileType !== 'epub' || !book) return;
    const pct = epubPercent / 100;
    if (pct > 0) saveReadingProgress(bookId, book.title, book.author, epubBookPage, pct, 'epub');
  }, [epubBookPage, epubPercent, fileType]);

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
    const locInfo = fileType === 'epub' ? `第${epubCumulativePage || epubPage + 1}页（共${epubCumulativeTotal || epubTotalPages || '?'}页）` : `第${pageNumber}页${numPages ? `（共${numPages}页）` : ''}`;
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

  // 从 URL 参数预填文件类型
  useEffect(() => {
    const type = searchParams.get('type');
    if (type) setFileType(type);
  }, [searchParams]);

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

  // 秒开：meta → 立即显示 → 按需加载章节
  const loadTextBook = async () => {
    setTextLoading(true);
    setLoading(false);
    try {
      // 1. 加载元数据（<5KB，毫秒级）
      const metaResp = await fetch(`${getApiBase()}/api/books/${bookId}/text?meta=1`);
      if (!metaResp.ok) throw new Error('API ' + metaResp.status);
      const meta = await metaResp.json();
      setBook({ title: meta.title || bookId, author: meta.author || '', file_type: 'epub' });
      setFileType('epub');
      setTextToc(meta.toc || []);
      const total = meta.chapterCount || 0;
      const chapters = Array.from({ length: total }, (_, i) => ({
        title: meta.chapterTitles?.[i] || `第${i + 1}章`,
        content: null, // 按需加载
        _loaded: false,
      }));
      setTextChapters(chapters);
      setTextReady(true);

      // URL 跳转
      const urlCh = parseInt(searchParams.get('ch'));
      const startCh = urlCh >= 0 && urlCh < total ? urlCh : 0;
      setTextChapter(startCh);

      // 2. 立即加载当前章节
      await loadChapter(startCh);
      // 3. 预加载下一章
      if (startCh + 1 < total) loadChapter(startCh + 1);
    } catch (e) {
      console.error('Load error:', e);
      if (!textReady) setError('加载失败');
    } finally {
      setTextLoading(false);
    }
  };

  const loadingRef = useRef({});
  const loadChapter = async (idx) => {
    if (!textChapters[idx] || textChapters[idx]._loaded || textChapters[idx].content) return;
    if (loadingRef.current[idx]) return;
    loadingRef.current[idx] = true;
    try {
      const resp = await fetch(`${getApiBase()}/api/books/${bookId}/chapter/${idx}`);
      if (resp.ok) {
        const ch = await resp.json();
        setTextChapters(prev => {
          const next = [...prev];
          if (next[idx]) next[idx] = { ...ch, index: idx, _loaded: true };
          return next;
        });
      }
    } catch {} finally {
      loadingRef.current[idx] = false;
    }
  };

  const handleChapterChange = (ch) => {
    if (ch === textChapter) return;
    setTextChapter(ch);
    loadChapter(ch);
    if (ch + 1 < textChapters.length) loadChapter(ch + 1);
    if (book) saveReadingProgress(bookId, book.title, book.author, ch + 1, (ch + 1) / textChapters.length, fileType);
  };

  useEffect(() => {
    const type = searchParams.get('type') || fileType;
    if (type === 'epub' || type === 'txt' || fileType === 'epub' || fileType === 'txt') {
      setFileType(type || 'epub');
      loadTextBook();
    } else if (!loading && bookId) {
      loadBook();
    }
  }, [bookId]);

  // Init EPUB — locations.generate 在 initEpub 中已完成，此处无需额外处理
  useEffect(() => {
    if (!epubReady) return;
    // 无需操作：initEpub 的 locations.generate 回调中已完成页面恢复
  }, [epubReady]);

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
    bk.loaded.spine.then(spine => { setEpubTotalChapters(spine?.length || 0); }).catch(() => {});
    // —— 全书页码（跟 PDF 完全一样的逻辑）——
    const cacheKey = `${book?.title||''}||${book?.author||''}`;
    const cachedTotal = pageCacheRef.current?.[cacheKey] || 0;
    const totalPages = cachedTotal > 0 ? cachedTotal : 1000;
    setEpubBookTotal(totalPages);

    rendition.on('relocated', (loc) => {
      const pct = loc?.start?.percentage;
      if (pct !== undefined && pct !== null) {
        setEpubPercent(Math.round(pct * 100));
        setEpubBookPage(Math.max(1, Math.round(pct * totalPages)));
      }
    });
    // 直接显示首页（percentage 不依赖 locations.generate）
    bk.ready.then(() => rendition.display(0));
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

  // Keyboard navigation: left/right arrow to turn pages
  useEffect(() => {
    const handler = (e) => {
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
      if (e.key === 'ArrowLeft') {
        if (fileType === 'pdf') goToPage(pageNumber - (twoPage ? 2 : 1));
        else epubRenditionRef.current?.prev();
      } else if (e.key === 'ArrowRight') {
        if (fileType === 'pdf') goToPage(pageNumber + (twoPage ? 2 : 1));
        else epubRenditionRef.current?.next();
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [fileType, pageNumber, numPages, twoPage, goToPage]);

  // Two-page toggle for EPUB
  useEffect(() => {
    const r = epubRenditionRef.current;
    if (r && fileType === 'epub') r.spread(twoPage ? 'auto' : 'none');
  }, [twoPage, fileType]);

  if (loading) return <div className="loading">加载中...</div>;
  if (error) return (
    <div className="page-container">
      <button className="btn btn-secondary" onClick={() => navigate(-1)} style={{ marginBottom: 16 }}>← 返回</button>
      <div className="card"><p style={{ textAlign: 'center', fontSize: 40 }}><Icon name="icon-error" size={16} /></p><p style={{ textAlign: 'center' }}>{error}</p></div>
    </div>
  );
  if (!book) return <div className="loading">正在获取文件...</div>;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100dvh', overflow: 'hidden' }}>
      {/* Top bar — compact */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 4, flexShrink: 0,
        padding: '2px 8px', background: 'var(--primary)', borderBottom: '1px solid var(--border)',
      }}>
        <button className="btn btn-secondary" style={{ padding: '2px 6px', fontSize: 11 }}
          onClick={() => navigate(-1)}>←</button>
        <span style={{ fontSize: 11, color: 'var(--text)', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          {book.title}
          {(fileType === 'epub' || fileType === 'txt') && textReady && (
            <span style={{ color: 'var(--text-dim)', marginLeft: 8 }}>第{textChapter + 1}章 / 共{textChapters.length}章</span>
          )}
        </span>
        <button className="btn btn-secondary" style={{ padding: '2px 8px', fontSize: 10 }}
          onClick={() => { setShowNotes(!showNotes); if (!showNotes) setShowAiChat(false); }}>
          <Icon name="icon-edit" size={16} />批注
        </button>
        <button className="btn btn-primary" style={{ padding: '2px 8px', fontSize: 10 }}
          onClick={() => { setShowAiChat(!showAiChat); if (!showAiChat) setShowNotes(false); }}>
          {showAiChat ? '关闭' : <><Icon name="nav-qa" size={16} /> AI</>}
        </button>
      </div>

      {/* Main area: reader + optional notes panel */}
      <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        {/* Reader */}
        <div style={{ flex: (showNotes || showAiChat) ? '0 0 60%' : 1, display: 'flex', flexDirection: 'column', overflow: 'auto', background: 'var(--card-bg)', position: 'relative', WebkitOverflowScrolling: 'touch' }}>
          {fileType === 'epub' || fileType === 'txt' ? (
            useEpubFallback ? (
              <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
                <div ref={epubViewerRef} style={{ flex: 1, minHeight: 0 }} />
                <div style={{ flexShrink: 0, padding: '4px 8px', borderTop: '1px solid var(--border)', textAlign: 'center', fontSize: 11, color: 'var(--text-dim)' }}>
                  使用旧版阅读器（文本引擎未部署）
                </div>
              </div>
            ) : (
              <div className="reader-text-container" style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0, overflow: 'hidden' }}>
                {textLoading ? (
                  <div className="loading">加载中...</div>
                ) : textReady ? (
                  <ChapterReader
                    chapters={textChapters}
                    currentChapter={textChapter}
                    onChapterChange={handleChapterChange}
                    title={book?.title}
                  />
                ) : (
                  <div className="loading">加载中...</div>
                )}
              </div>
            )
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
                        borderRight: pageNumber < numPages ? '1px solid rgba(0,0,0,0.15)' : 'none',
                        boxShadow: pageNumber < numPages ? '2px 0 8px rgba(0,0,0,0.1)' : 'none',
                      }}>
                        <Page pageNumber={pageNumber} scale={pdfScale}
                          renderTextLayer={true} renderAnnotationLayer={false}
                          width={Math.min((window.innerWidth - ((showNotes || showAiChat) ? 260 : 40)) / (pageNumber < numPages ? 2 : 1) - 8, pageNumber < numPages ? 500 : 800)} />
                      </div>
                      {pageNumber < numPages && (
                      <div style={{
                        boxShadow: '-2px 0 8px rgba(0,0,0,0.1)',
                      }}>
                        <Page pageNumber={pageNumber + 1} scale={pdfScale}
                          renderTextLayer={true} renderAnnotationLayer={false}
                          width={Math.min((window.innerWidth - ((showNotes || showAiChat) ? 260 : 40)) / 2 - 8, 500)} />
                      </div>
                      )}
                    </div>
                  ) : (
                    <Page pageNumber={pageNumber} scale={pdfScale}
                      renderTextLayer={true} renderAnnotationLayer={false}
                      width={Math.min(window.innerWidth - ((showNotes || showAiChat) ? 260 : 32), 800)} />
                  )}
                </Document>
              </div>
              {/* PDF controls — single row */}
              <div style={{
                flexShrink: 0, background: 'var(--primary)', borderTop: '1px solid var(--border)', padding: '2px 8px',
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <button className="btn btn-primary" style={{ padding: '4px 10px', fontSize: 13 }}
                    onClick={() => goToPage(pageNumber - (twoPage ? 2 : 1))} disabled={pageNumber <= 1}>◀</button>
                  {showJumpInput ? (
                    <form onSubmit={e => { e.preventDefault(); handleJump(); }}
                      style={{ display: 'flex', gap: 2, alignItems: 'center' }}>
                      <input type="number" min={1} max={numPages} value={jumpPage}
                        onChange={e => setJumpPage(e.target.value)}
                        style={{ width: 36, padding: '1px 4px', borderRadius: 4, border: '1px solid var(--accent)', background: 'var(--secondary)', color: 'var(--text)', fontSize: 11, textAlign: 'center' }}
                        autoFocus />
                      <button type="submit" className="btn btn-primary" style={{ padding: '1px 6px', fontSize: 10 }}>跳</button>
                      <button type="button" className="btn btn-secondary" style={{ padding: '1px 6px', fontSize: 10 }}
                        onClick={() => { setShowJumpInput(false); setJumpPage(''); }}><Icon name="icon-close" size={16} /></button>
                    </form>
                  ) : (
                    <span style={{ fontSize: 12, color: 'var(--text-dim)', cursor: 'pointer' }}
                      onClick={() => setShowJumpInput(true)}>
                      {pageNumber}/{numPages}
                    </span>
                  )}
                  <button className="btn btn-primary" style={{ padding: '4px 10px', fontSize: 13 }}
                    onClick={() => goToPage(pageNumber + (twoPage ? 2 : 1))} disabled={pageNumber >= numPages}><span style={{ display: 'inline-block', transform: 'scaleX(-1)', fontSize: 14 }}>◀</span></button>
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
              <Icon name="icon-edit" size={16} /> 阅读批注 · 第{pageNumber}页
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
              onClick={saveNotes}><Icon name="icon-save" size={16} /> 保存批注</button>
            <button className="btn btn-secondary btn-block" style={{ marginTop: 4, padding: '6px', fontSize: 12 }}
              onClick={() => { navigator.clipboard?.writeText(noteText); }}>
              <Icon name="icon-clipboard" size={16} /> 复制全部
            </button>
          </div>
        )}

        {/* AI Chat sidebar — inside flex container, side-by-side with reader */}
        {showAiChat && (
          <div style={{
            flex: '0 0 40%', borderLeft: '1px solid var(--border)',
            background: 'var(--primary)', display: 'flex', flexDirection: 'column',
            overflow: 'hidden',
          }}>
            {/* Header — compact */}
            <div style={{
              padding: '4px 10px', borderBottom: '1px solid var(--border)',
              display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              flexShrink: 0,
            }}>
              <span style={{ fontSize: 11, color: 'var(--accent)' }}><Icon name="nav-qa" size={16} /> AI · {book?.title?.slice(0,8)}</span>
              <button onClick={() => setShowAiChat(false)}
                style={{ background: 'none', border: 'none', color: 'var(--text-dim)', fontSize: 14, cursor: 'pointer' }}><Icon name="icon-close" size={16} /></button>
            </div>

            {/* Chat history */}
            <div ref={aiChatRef} style={{
              flex: 1, overflow: 'auto', padding: '4px 8px',
              display: 'flex', flexDirection: 'column', gap: 4,
            }}>
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
              display: 'flex', gap: 4, padding: '4px 8px',
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
    </div>
  );
}

export default ReaderPage;
