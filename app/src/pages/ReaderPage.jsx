/**
 * 阅读器 — 章节文本阅读（所有书统一方式，PDF/EPUB 原始渲染已移除）
 * 支持：章跳转、目录、批注笔记、阅读进度自动保存
 * URL 参数：ch（章）、sec（详情页目录节跳转）
 */
import { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import Icon from '../components/Icon';
import { getApiBase } from '../App';
import { writeLocalNote, notePending, markNoteSynced } from '../data/readingRoom';
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
  const noteDirty = useRef(false);
  useEffect(() => {
    let active = true;
    noteDirty.current = false;
    const token = localStorage.getItem('dp_token');
    const loadNotes = async () => {
      try { setNoteText(localStorage.getItem(notesKey) || ''); } catch { setNoteText(''); }
      if (!token || notePending(bookId)) return;
      try {
        const r = await fetch(`${getApiBase()}/api/notes/load?book_id=${encodeURIComponent(bookId)}`, {
          headers: { Authorization: `Bearer ${token}` }, signal: AbortSignal.timeout(5000),
        });
        if (!r.ok) return;
        const d = await r.json();
        if (active && localStorage.getItem('dp_token') === token && !noteDirty.current && !notePending(bookId) && typeof d.note_text === 'string') {
          setNoteText(d.note_text); localStorage.setItem(notesKey, d.note_text);
        }
      } catch { /* Keep the local draft when offline. */ }
    };
    loadNotes();
    return () => { active = false; };
  }, [bookId, notesKey]);

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

  // Share pending-note tracking with the reading room; late cloud reads must not overwrite drafts.
  const saveNotes = () => {
    if (!noteDirty.current && !notePending(bookId)) return;
    try {
      writeLocalNote(bookId, noteText);
      const token = localStorage.getItem('dp_token');
      if (token) fetch(`${getApiBase()}/api/notes/save`, {
        method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ book_id: bookId, note_text: noteText }), signal: AbortSignal.timeout(5000),
      }).then(r => { if (r.ok && localStorage.getItem('dp_token') === token) markNoteSynced(bookId, noteText); }).catch(() => {});
      noteDirty.current = false;
    } catch {}
  };

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
          onClick={() => setShowNotes(!showNotes)}>
          <Icon name="icon-edit" size={16} />批注
        </button>
      </div>

      {/* Main area: reader + optional notes panel */}
      <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        {/* Reader */}
        <div style={{ flex: showNotes ? '0 0 60%' : 1, display: 'flex', flexDirection: 'column', overflow: 'auto', background: 'var(--card-bg)', position: 'relative', WebkitOverflowScrolling: 'touch' }}>
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
              onChange={e => { noteDirty.current = true; setNoteText(e.target.value); try { writeLocalNote(bookId, e.target.value); } catch {} }}
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

      </div>
    </div>
  );
}

export default ReaderPage;
