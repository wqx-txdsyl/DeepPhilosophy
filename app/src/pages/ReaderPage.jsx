/**
 * 阅读器 — 章节文本阅读（所有书统一方式，PDF/EPUB 原始渲染已移除）
 * 支持：章跳转、目录、批注笔记、AI 问答、阅读进度自动保存
 * URL 参数：ch（章）、sec（详情页目录节跳转）
 */
import { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import Icon from '../components/Icon';
import { getApiBase } from '../App';
import { saveReadingProgress } from '../data/userData';
import ChapterReader from '../components/ChapterReader';

// 章节 CDN 双轨（2026-08-11 提速）:
//   OSS 优先 — 上海直连 ~80ms（backend/data/book_chapters 由 dp_sync_oss_chapters.py 增量同步到 bucket）
//   jsDelivr 兜底 — GitHub 自动刷新（OSS 超时/缺文件时切换, 国内 ~0.9s 但可用）
// 本地开发（localhost）→ 本地静态目录（vite dev 服务 public/backend/data/book_chapters junction, 空串拼接同源相对路径）
// 章节 CDN 引脚: 部署 commit hash 由 index.html 的 <meta name="dp-commit"> 运行时提供
// （2026-08-14 解耦: 不再内联 __COMMIT_HASH__ 进 JS 包——否则每次 push 都换资产 hash,
//   OSS 未同步即白屏; 现 meta 由 postbuild.mjs 每次构建注入, JS 包内容跨 commit 稳定）
const DP_COMMIT =
  (typeof document !== 'undefined' && document.querySelector('meta[name="dp-commit"]')?.content) || 'master';
const CDN_BASES = (typeof location !== 'undefined' && ['localhost', '127.0.0.1'].includes(location.hostname))
  ? ['']
  : [
      'https://deepphilosophy.oss-cn-shanghai.aliyuncs.com',
      `https://cdn.jsdelivr.net/gh/wqx-txdsyl/DeepPhilosophy@${DP_COMMIT}`,
    ];

// 依次尝试各 CDN; 全部失败抛最后错误
// 超时: OSS 2s 快超时（直连上海 ~80ms, 抖动瞬时, 失败立刻重试 1 次）;
//       jsDelivr 10s（兜底路径, 首次回源实测 6.5s, 2s 必然超时 → 曾致"永久加载中"）
const CDN_TIMEOUTS = [2000, 2000, 10000];
async function fetchChapter(path) {
  let lastErr;
  const rel = path.startsWith('/') ? path.slice(1) : path;   // {bid}/{idx}.json
  // 基地址与路径成对：OSS bucket 前缀 book_chapters/（dp_sync_oss_chapters 上传，无 backend/data）；
  // jsDelivr 镜像 git 仓库 → 保留 backend/data/book_chapters/ 前缀；本地 dev 走 vite public junction
  const tries = CDN_BASES.length > 1
    ? [
        `${CDN_BASES[0]}/book_chapters/${rel}`,            // OSS
        `${CDN_BASES[0]}/book_chapters/${rel}`,            // OSS 重试
        `${CDN_BASES[1]}/backend/data/book_chapters/${rel}`,  // jsDelivr 兜底
      ]
    : [`${CDN_BASES[0]}/backend/data/book_chapters${path}`];   // 本地 dev 单 base
  for (let i = 0; i < tries.length; i++) {
    try {
      const resp = await fetch(tries[i], { signal: AbortSignal.timeout(CDN_TIMEOUTS[i] || 2000) });
      if (resp.ok) return resp;
      lastErr = new Error('HTTP ' + resp.status);
    } catch (e) { lastErr = e; }
  }
  throw lastErr;
}

function ReaderPage() {
  const { bookId } = useParams();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const [book, setBook] = useState(null);
  const [error, setError] = useState(null);
  // 章节阅读
  const [textChapters, setTextChapters] = useState([]);
  const [textChapter, setTextChapter] = useState(0);
  const [textToc, setTextToc] = useState([]);
  const [textLoading, setTextLoading] = useState(false);
  const [textReady, setTextReady] = useState(false);
  const [showReaderToc, setShowReaderToc] = useState(false);
  // URL 直达节(第X节): 详情页目录 section 跳转
  // 主路径: &toc={toc数组下标} → 标题锚点 sec-{tocIdx}，不依赖 sec 字段（缺 sec 的书也准）
  // 兼容旧 URL: &sec={章内块下标}（防御: 缺 sec 字段的书旧 URL 带 "sec=undefined" → NaN → 置 null）
  const tocParam = searchParams.get('toc');
  const tocNum = tocParam ? parseInt(tocParam, 10) : NaN;
  const initialTocIdx = !isNaN(tocNum) ? tocNum : null;
  const secParam = searchParams.get('sec');
  const secNum = secParam ? parseInt(secParam, 10) : NaN;
  const initialSec = !isNaN(secNum) ? secNum : null;

  // Notes state
  const [showNotes, setShowNotes] = useState(false);
  const [noteText, setNoteText] = useState('');
  const notesKey = `dp_notes_${bookId}`;

  // AI Chat state
  const [showAiChat, setShowAiChat] = useState(false);
  const [aiQuestion, setAiQuestion] = useState('');
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

  // Save progress on unmount（章节阅读统一 'text' 类型）
  const chapterPosRef = useRef({ bookId: '', title: '', author: '', ch: 0, total: 0 });
  useEffect(() => {
    if (textReady && book) {
      chapterPosRef.current = { bookId, title: book.title, author: book.author, ch: textChapter, total: textChapters.length };
    }
  }, [bookId, textChapter, textReady, book, textChapters.length]);
  useEffect(() => {
    return () => {
      const s = chapterPosRef.current;
      if (s.total > 0) saveReadingProgress(s.bookId, s.title, s.author, s.ch + 1, (s.ch + 1) / s.total, 'text');
    };
  }, []);

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

  // 获取当前页文字（从已加载章节内容提取）
  const getCurrentPageText = async () => {
    const ch = textChapters[textChapter];
    if (ch?.content) {
      return String(ch.content).replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim().substring(0, 3000);
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
    const locInfo = textReady ? `第${textChapter + 1}章（共${textChapters.length}章）` : '';
    const textContext = pageText ? `\n当前章节文字内容（节选）：\n"""\n${pageText}\n"""\n` : '';
    const systemPrompt = `你是一位博学的哲学导师。读者正在阅读哲学著作，需要你的帮助理解文本。

当前阅读上下文：
- 书名：《${book?.title}》
- 作者：${book?.author}
- ${locInfo}
${book?.region ? `- 所属传统：${book.region}哲学` : ''}
${textContext}
请根据读者的问题，结合你看到的章节内容以及对这本书和该作者哲学思想的了解，给出深入浅出的解答。`;

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
    } catch {
      // 静默：回答失败时走兜底文案
    }

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

  // 秒开：meta → 立即显示 → 按需加载章节（所有书统一章节阅读，不再有 PDF/EPUB 原始渲染）
  const loadTextBook = async () => {
    setTextLoading(true);
    setError(null);
    try {
      // 1. 从 meta.json 获取正确的章节元数据（排除 TOC 纯标题条目）
      const metaResp = await fetchChapter(`/${bookId}/meta.json`);
      if (!metaResp.ok) throw new Error('Meta ' + metaResp.status);
      const meta = await metaResp.json();
      const total = meta.chapterCount || 0;
      if (total === 0) throw new Error('No chapters');

      setBook({ title: meta.title || bookId, author: meta.author || '', region: meta.region, file_type: 'text' });
      setTextToc(meta.toc || []);
      const chapters = Array.from({ length: total }, (_, i) => ({
        title: meta.chapterTitles?.[i] || `第${i + 1}章`,
        content: null,
        _loaded: false,
      }));
      setTextChapters(chapters);
      setError(null); setTextReady(true);

      // URL 跳转：优先 ch 参数，其次历史记录，最后默认 ch=0
      const urlCh = parseInt(searchParams.get('ch'));
      let startCh;
      if (!isNaN(urlCh) && urlCh >= 0 && urlCh < total) {
        startCh = urlCh;
      } else {
        let histCh = -1;
        try {
          const ud = JSON.parse(localStorage.getItem('dp_userdata') || '{}');
          const entry = (ud.readingHistory || []).find(r => r.bookId === bookId);
          if (entry?.page > 0 && entry.page <= total) histCh = entry.page - 1;
        } catch {}
        startCh = histCh >= 0 ? histCh : 0;
      }
      setTextChapter(startCh);

      // 2. 立即加载当前章节（通过章节 index 查找对应文件）
      await loadChapter(startCh, chapters);
      // 3. 预加载下一章
      if (startCh + 1 < total) loadChapter(startCh + 1, chapters);
    } catch (e) {
      console.error('Load error:', e);
      if (!textReady) setError('无法阅读：该书籍暂无章节数据。');
    } finally {
      setTextLoading(false);
    }
  };

  useEffect(() => {
    loadTextBook();
  }, [bookId]);

  const loadingRef = useRef({});
  const markChapterError = (idx) => {
    setTextChapters(prev => {
      const next = [...prev];
      if (next[idx]) next[idx] = { ...next[idx], _error: true };
      return next;
    });
  };
  const loadChapter = async (idx, chaptersArr) => {
    const chs = chaptersArr || textChapters;
    if (!chs[idx] || chs[idx]._loaded || chs[idx].content) return;
    if (loadingRef.current[idx]) return;
    loadingRef.current[idx] = true;
    try {
      const resp = await fetchChapter(`/${bookId}/${idx}.json`);
      if (resp.ok) {
        const ch = await resp.json();
        setTextChapters(prev => {
          const next = [...prev];
          if (next[idx]) next[idx] = { ...ch, _loaded: true, _error: false };
          return next;
        });
      } else {
        markChapterError(idx);
      }
    } catch { markChapterError(idx); } finally {
      loadingRef.current[idx] = false;
    }
  };
  // 失败后重试: 清错误标记重新加载（失败态不再永久卡"加载中"）
  const retryChapter = (idx) => {
    setTextChapters(prev => {
      const next = [...prev];
      if (next[idx]) next[idx] = { ...next[idx], _error: false };
      return next;
    });
    loadChapter(idx);
  };

  const handleChapterChange = useCallback((ch) => {
    if (ch === textChapter) return;
    // 跳过 section 章节
    let target = ch;
    if (textChapters[target]?.type === 'section') {
      target = ch > textChapter ? target + 1 : target - 1;
      if (target < 0 || target >= textChapters.length) return;
    }
    setTextChapter(target);
    loadChapter(target);
    if (target + 1 < textChapters.length) loadChapter(target + 1);
    if (book) saveReadingProgress(bookId, book.title, book.author, target + 1, (target + 1) / textChapters.length, 'text');
    // URL 只保留 ch/sec，不再写 type
    const params = new URLSearchParams(searchParams);
    params.delete('type');
    params.set('ch', target);
    navigate(`/reader/${bookId}?${params.toString()}`, { replace: true });
  }, [textChapter, textChapters, book, bookId, searchParams, navigate]);

  // Keyboard navigation: left/right arrow to switch chapters
  useEffect(() => {
    const handler = (e) => {
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
      if (!textReady) return;
      if (e.key === 'ArrowLeft') {
        if (textChapter > 0) handleChapterChange(textChapter - 1);
      } else if (e.key === 'ArrowRight') {
        if (textChapter < textChapters.length - 1) handleChapterChange(textChapter + 1);
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [textReady, textChapter, textChapters.length, handleChapterChange]);

  if (textLoading && !textReady) return <div className="loading">加载中...</div>;
  if (error) return (
    <div className="page-container">
      <button className="btn btn-secondary" onClick={() => navigate(-1)} style={{ marginBottom: 16 }}>← 返回</button>
      <div className="card"><p style={{ textAlign: 'center', fontSize: 40 }}><Icon name="icon-error" size={16} /></p><p style={{ textAlign: 'center' }}>{error}</p></div>
    </div>
  );

  return (
    <div className="reader-page-wrapper" style={{ display: 'flex', flexDirection: 'column', height: '100dvh', maxHeight: '100dvh', overflow: 'hidden', paddingBottom: 'env(safe-area-inset-bottom, 0px)' }}>
      {/* Top bar — compact */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 4, flexShrink: 0,
        padding: '2px 8px', background: 'var(--primary)', borderBottom: '1px solid var(--border)',
      }}>
        <button className="btn btn-secondary" style={{ padding: '2px 6px', fontSize: 11 }}
          onClick={() => navigate(-1)}>←</button>
        <span style={{ fontSize: 11, color: 'var(--text)', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          {book?.title}
          {textReady && (
            <span style={{ color: 'var(--text-dim)', marginLeft: 8 }}>第{textChapter + 1}章 / 共{textChapters.length}章</span>
          )}
        </span>
        {textReady && (
          <button className="btn btn-secondary" style={{ padding: '2px 8px', fontSize: 10 }}
            onClick={() => setShowReaderToc(!showReaderToc)}>
            ☰ 目录
          </button>
        )}
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
      <div style={{ flex: 1, display: 'flex', overflow: 'hidden', minHeight: 0 }}>
        {/* Reader — 唯一滚动容器是内部 .reader-content；本列 overflow:hidden 防止
            某层高度链未就绪时接管滚动（会导致底部工具栏被内容顶出视口） */}
        <div style={{ flex: (showNotes || showAiChat) ? '0 0 60%' : 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', minHeight: 0, background: 'var(--card-bg)', position: 'relative', WebkitOverflowScrolling: 'touch' }}>
          <div className="reader-text-container" style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0, overflow: 'hidden' }}>
            {textLoading ? (
              <div className="loading">加载中...</div>
            ) : textReady ? (
              <ChapterReader
                chapters={textChapters}
                toc={textToc}
                currentChapter={textChapter}
                onChapterChange={handleChapterChange}
                title={book?.title}
                showToc={showReaderToc}
                onToggleToc={() => setShowReaderToc(!showReaderToc)}
                initialTocIdx={initialTocIdx}
                initialSec={initialSec}
                onRetryChapter={retryChapter}
              />
            ) : error ? (
              <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-dim)' }}>
                <p style={{ fontSize: 36, margin: '0 0 12px' }}><Icon name="icon-error" size={16} /></p>
                <p>{error}</p>
              </div>
            ) : (
              <div className="loading">加载中...</div>
            )}
          </div>
        </div>

        {/* Notes sidebar */}
        {showNotes && (
          <div style={{
            flex: '0 0 40%', borderLeft: '1px solid var(--border)',
            background: 'var(--primary)', padding: 12,
            display: 'flex', flexDirection: 'column', overflow: 'auto',
          }}>
            <div style={{ fontSize: 11, color: 'var(--text-dim)', marginBottom: 6 }}>
              <Icon name="icon-edit" size={16} /> 阅读批注 · 第{textChapter + 1}章
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
