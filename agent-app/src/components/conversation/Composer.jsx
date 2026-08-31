import { useState, useRef, useEffect, useCallback } from 'react';
import { Plus, ArrowUp, Square } from 'lucide-react';
import { getApiBase } from '../../utils/api';
import { useLang } from '../../utils/i18n';
import AgentSelector from './AgentSelector';
import AttachmentCard from './AttachmentCard';

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
  const [input, setInput] = useState('');
  const [attachments, setAttachments] = useState([]);   // draft: [{id, filename, kind, size, status, content?, error?}]
  const [dragOver, setDragOver] = useState(false);
  const [uploadingCount, setUploadingCount] = useState(0);
  const fileInputRef = useRef(null);
  const inputRef = useRef(null);
  const composingRef = useRef(false);     // 中文 IME composition 保护（§32）
  const dragDepthRef = useRef(0);

  // 切换会话/草稿 → 清空输入与附件（draft 隔离: A 附件不串 B, §30）
  useEffect(() => {
    setInput('');
    setAttachments([]);
    if (autoFocus) requestAnimationFrame(() => inputRef.current?.focus());
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [resetKey]);

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
    try {
      const fd = new FormData();
      fd.append('file', file);
      const resp = await fetch(`${getApiBase()}/api/upload`, { method: 'POST', body: fd });
      const d = await resp.json();
      setAttachments(prev => prev.map(a => a.id === id
        ? (d.error
            ? { ...a, status: 'error', error: d.error }
            : { ...a, status: 'ready', kind: d.kind || a.kind, content: d.content })
        : a));
    } catch (err) {
      setAttachments(prev => prev.map(a => a.id === id ? { ...a, status: 'error', error: err.message } : a));
    }
    setUploadingCount(c => c - 1);
  }, []);

  const handleFiles = useCallback((fileList) => {
    const files = Array.from(fileList || []);
    for (const f of files) {
      if (f.size > MAX_SIZE) {
        setAttachments(prev => [...prev, {
          id: nextId(), filename: f.name, kind: guessKind(f.name, f.type),
          size: f.size, status: 'error', error: `${t('uploadFail')} (>25MB)`,
        }]);
        continue;
      }
      uploadFile(f);
    }
  }, [uploadFile, t]);

  const removeAttachment = (id) => setAttachments(prev => prev.filter(a => a.id !== id));
  const retryAttachment = (att) => {
    if (!att.file) { removeAttachment(att.id); return; }   // 无原始 File（异常态）→ 移除
    uploadFile(att.file, att.id);                          // 复用原卡重传（§12 error → retry 非假控件）
  };

  const canSend = (input.trim().length > 0 || attachments.some(a => a.status === 'ready')) && !streaming && !unavailable;
  const isUploading = attachments.some(a => a.status === 'uploading') || uploadingCount > 0;

  const submit = () => {
    const text = input.trim();
    const ready = attachments.filter(a => a.status === 'ready');
    if ((!text && !ready.length) || streaming || unavailable || isUploading) return;
    // P0-3: message（模型上下文）保留附件内联描述; display（可见 user message）
    // = 纯用户文本, 系统生成的附件 serialization 绝不进入 persisted visible content。
    const attachText = ready.length
      ? ready.map(a => `【附件《${a.filename}》】\n${a.content || ''}`).join('\n\n') + '\n\n'
      : '';
    const display = text;   // 附件一律由 structured attachments 渲染
    // 发送瞬间 snapshot draft → immutable metadata; draft 清空（§12/§14）
    const snapshot = ready.map(a => ({ filename: a.filename, kind: a.kind, size: a.size }));
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
                <AttachmentCard key={a.id} att={a} onRemove={removeAttachment} onRetry={retryAttachment} />
              ))}
            </div>
          )}
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={onKeyDown}
            onCompositionStart={() => { composingRef.current = true; }}
            onCompositionEnd={() => { composingRef.current = false; }}
            placeholder={t('placeholder')}
            rows={1}
            className="cw-composer-input"
            aria-label={t('placeholder')}
            enterKeyHint="send"
          />
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
