import { useState, useRef, useEffect, useCallback } from 'react';
import { Plus, ArrowUp, Square } from 'lucide-react';
import { getApiBase } from '../../utils/api';
import { useLang } from '../../utils/i18n';
import AgentSelector from './AgentSelector';
import AttachmentCard from './AttachmentCard';
import { useAuth } from '../../auth';

/**
 * Composer — 输入区（spec §11, 最高优先级组件）
 * anatomy: [AttachmentCard…] / textarea(auto-grow, max 200px 内滚) /
 *          [+] [回答者：尼采 ▾] … [Send|Stop]
 *
 * 行为: Shift+Enter 换行; Enter 发送但中文 IME composition 中不误发（§32）;
 *       切 Agent 不清 draft; Settings 开关不丢 draft; Conversation 切换清 draft（隔离）。
 * 附件: 多文件、类型/大小校验、uploading/error/retry、drag&drop 轻量目标（§12）。
 */
const MAX_SIZE = 25 * 1024 * 1024;   // 25MB 客户端预检（后端另有校验）
const ALLOW_ALL = true;

let uid = 0;
const nextId = () => `att_${Date.now().toString(36)}_${(uid++).toString(36)}`;

function guessKind(filename, mime = '') {
  if (mime.startsWith('image/') || /\.(png|jpe?g|gif|webp|bmp|svg)$/i.test(filename)) return 'image';
  if (/\.(md|markdown)$/i.test(filename) || mime === 'text/markdown') return 'markdown';
  if (/\.(txt|text)$/i.test(filename) || mime === 'text/plain') return 'text';
  return 'document';
}

export default function Composer({
  agents, agent, onAgentChange, onSend, streaming, onStop,
  onExplore, unavailable, resetKey, autoFocus, dockLeft,
}) {
  const { t } = useLang();
  const { token } = useAuth();
  const general = agent === 'general';
  const [input, setInput] = useState('');
  const [attachments, setAttachments] = useState([]);   // draft: [{id, filename, kind, size, status, content?, error?}]
  const [dragOver, setDragOver] = useState(false);
  const [uploadingCount, setUploadingCount] = useState(0);
  const fileInputRef = useRef(null);
  const inputRef = useRef(null);
  const composingRef = useRef(false);     // 中文 IME composition 保护（§32）
  const dragDepthRef = useRef(0);
  const uploadsRef = useRef(new Map());

  // 切换会话/草稿 → 清空输入与附件（draft 隔离: A 附件不串 B, §30）
  useEffect(() => {
    setInput('');
    setAttachments([]);
    if (general) {
      for (const controller of uploadsRef.current.values()) controller.abort();
      uploadsRef.current.clear();
      setUploadingCount(0);
      dragDepthRef.current = 0;
      setDragOver(false);
    }
    if (autoFocus) requestAnimationFrame(() => inputRef.current?.focus());
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [resetKey]);
  useEffect(() => () => { for (const controller of uploadsRef.current.values()) controller.abort(); }, []);

  // textarea auto-grow: 高度随内容, 超 maxHeight 内滚（§11）
  useEffect(() => {
    const el = inputRef.current;
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = `${Math.min(el.scrollHeight, 200)}px`;
  }, [input]);

  const uploadFile = useCallback(async (file, existingId = null) => {
    // existingId 支持 error retry 复用原卡（不重复添加）
    const id = existingId || nextId();
    const base = { id, filename: file.name, kind: guessKind(file.name, file.type), size: file.size, status: 'uploading', file };
    if (existingId) {
      setAttachments(prev => prev.map(a => a.id === id ? base : a));
    } else {
      setAttachments(prev => [...prev, base]);
    }
    setUploadingCount(c => c + 1);
    const controller = new AbortController();
    if (general) uploadsRef.current.set(id, controller);
    try {
      const fd = new FormData();
      fd.append('file', file);
      const resp = await fetch(`${getApiBase()}${general ? '/api/agent/upload' : '/api/upload'}`, { method: 'POST', body: fd,
        ...(general ? { signal: controller.signal, headers: token ? { Authorization: `Bearer ${token}` } : {} } : {}) });
      const d = await resp.json();
      if (general && (!resp.ok || d.error || typeof d.content !== 'string' || !d.content.trim())) throw new Error(d.error || d.detail || t('uploadFail'));
      setAttachments(prev => prev.map(a => a.id === id
        ? (d.error
            ? { ...a, status: 'error', error: d.error }
            : { ...a, status: 'ready', kind: general ? a.kind : d.kind || a.kind, content: d.content, truncated: !!d.truncated })
        : a));
    } catch (err) {
      if (err.name !== 'AbortError') setAttachments(prev => prev.map(a => a.id === id ? { ...a, status: 'error', error: err.message } : a));
    }
    if (general) uploadsRef.current.delete(id);
    setUploadingCount(c => Math.max(0, c - 1));
  }, [general, token, t]);

  const handleFiles = useCallback((fileList) => {
    const files = Array.from(fileList || []);
    for (const f of files) {
      if (f.size > (general ? 20 * 1024 * 1024 : MAX_SIZE)) {
        setAttachments(prev => [...prev, {
          id: nextId(), filename: f.name, kind: guessKind(f.name, f.type),
          size: f.size, status: 'error', error: `${t('uploadFail')} (>${general ? 20 : 25}MB)`,
        }]);
        continue;
      }
      uploadFile(f);
    }
  }, [uploadFile, t, general]);

  const removeAttachment = (id) => {
    if (general) { uploadsRef.current.get(id)?.abort(); uploadsRef.current.delete(id); }
    setAttachments(prev => prev.filter(a => a.id !== id));
  };
  const retryAttachment = (att) => {
    if (!att.file) { removeAttachment(att.id); return; }   // 无原始 File（异常态）→ 移除
    uploadFile(att.file, att.id);                          // 复用原卡重传（§12 error → retry 非假控件）
  };

  const isUploading = attachments.some(a => a.status === 'uploading') || (!general && uploadingCount > 0);
  const hasFailed = general && attachments.some(a => a.status === 'error');
  const canSend = (input.trim().length > 0 || attachments.some(a => a.status === 'ready')) && !streaming && !unavailable && (!general || (!isUploading && !hasFailed));

  const submit = () => {
    const text = input.trim();
    const ready = attachments.filter(a => a.status === 'ready');
    if ((!text && !ready.length) || streaming || unavailable || isUploading || hasFailed) return;
    // P0-3: message（模型上下文）保留附件内联描述; display（可见 user message）
    // = 纯用户文本, 系统生成的附件 serialization 绝不进入 persisted visible content。
    const attachText = ready.length
      ? ready.map(a => `【附件《${a.filename}》${general && a.truncated ? '（仅包含文件前 20000 字符）' : ''}】\n${a.content || ''}`).join('\n\n') + '\n\n'
      : '';
    const display = text;   // 附件一律由 structured attachments 渲染
    // 发送瞬间 snapshot draft → immutable metadata; draft 清空（§12/§14）
    const snapshot = ready.map(a => ({ filename: a.filename, kind: a.kind, size: a.size, ...(general ? { truncated: !!a.truncated } : {}) }));
    setAttachments([]);
    setInput('');
    onSend({ message: attachText + text, display, attachments: snapshot });
  };

  const onKeyDown = (e) => {
    if (e.key !== 'Enter') return;
    if (e.shiftKey) return;                       // Shift+Enter 换行
    if (composingRef.current) return;             // IME composition → 不误发送（§32）
    e.preventDefault();
    submit();
  };

  const onDrop = (e) => {
    e.preventDefault();
    dragDepthRef.current = 0;
    setDragOver(false);
    if (streaming || unavailable) return;
    handleFiles(e.dataTransfer?.files);
  };

  const onDragEnter = (e) => {
    e.preventDefault();
    if (streaming || unavailable) return;
    dragDepthRef.current += 1;
    setDragOver(true);
  };
  const onDragLeave = () => {
    dragDepthRef.current = Math.max(0, dragDepthRef.current - 1);
    if (dragDepthRef.current === 0) setDragOver(false);
  };
  const onDragOver = (e) => e.preventDefault();

  return (
    <div className="composer-dock" style={dockLeft !== undefined ? { left: dockLeft } : undefined}>
      <div className="cw-composer-wrap">
        <div className={`cw-composer${dragOver ? ' cw-composer-drag' : ''}`}
          onDragEnter={onDragEnter} onDragLeave={onDragLeave} onDragOver={onDragOver} onDrop={onDrop}>
          {dragOver && <div className="cw-composer-dragover-hint">{t('dropHint')}</div>}
          {attachments.length > 0 && (
            <div className="cw-attach-tray">
              {attachments.map((a) => (
                <AttachmentCard key={a.id} att={a} onRemove={removeAttachment} onRetry={general ? () => retryAttachment(a) : retryAttachment} general={general} />
              ))}
            </div>
          )}
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={onKeyDown}
            onPaste={general ? e => { if (!streaming && !unavailable && e.clipboardData?.files?.length) handleFiles(e.clipboardData.files); } : undefined}
            onCompositionStart={() => { composingRef.current = true; }}
            onCompositionEnd={() => { composingRef.current = false; }}
            placeholder={t('placeholder')}
            rows={1}
            className="cw-composer-input"
            aria-label={t('placeholder')}
            enterKeyHint="send"
          />
          {general && (isUploading || hasFailed) && <div className="general-attachment-hint" role="status">{hasFailed ? '请重试或移除失败的附件，再发送。' : '正在读取附件，完成后即可发送。'}</div>}
          <div className="cw-composer-controls">
            <input ref={fileInputRef} type="file" multiple onChange={(e) => { handleFiles(e.target.files); e.target.value = ''; }} style={{ display: 'none' }}
              aria-hidden tabIndex={-1} />
            <button className="cw-control-icon" onClick={() => fileInputRef.current?.click()}
              title={`${t('attach')} · ${t('filterKinds')}`} aria-label={t('attach')}
              disabled={streaming || unavailable}>
              <Plus size={17} />
            </button>
            <AgentSelector agents={agents} value={agent} onChange={onAgentChange}
              onExplore={onExplore} unavailable={unavailable} />
            <div style={{ flex: 1 }} />
            {streaming ? (
              <button className="cw-control-icon" onClick={onStop} title={t('stopGenerating')} aria-label={t('stopGenerating')}
                style={{ border: '1px solid var(--border)', background: 'var(--card-bg)', color: 'var(--accent)' }}>
                <Square size={12} fill="currentColor" />
              </button>
            ) : (
              <button className="cw-send-btn" onClick={submit} disabled={!canSend}
                title={unavailable ? t('agentUnavailable') : t('send')} aria-label={t('send')}>
                <ArrowUp size={16} />
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
