import { X, RotateCcw, Loader2, Image as ImageIcon, FileText, FileType, File as FileIcon } from 'lucide-react';
import { useLang } from '../../utils/i18n';

/**
 * AttachmentCard — Composer draft 附件卡（spec §12）
 * 显示: 类型图标 / 文件名 / 类型·大小 / 上传状态 / error → retry / ✕ 移除。
 * 发送前属于 draft; 发送瞬间 snapshot 为空 → immutable metadata; 跨会话隔离由
 * resetKey 层保证（B 不会出现 A 的附件）。
 */
function KindIcon({ kind }) {
  if (kind === 'image') return <ImageIcon size={15} />;
  if (kind === 'markdown') return <FileText size={15} />;
  if (kind === 'text') return <FileType size={15} />;
  return <FileIcon size={15} />;
}

function fmtSize(bytes) {
  if (!Number.isFinite(bytes) || bytes <= 0) return '';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

export default function AttachmentCard({ att, onRemove, onRetry }) {
  const { t } = useLang();
  const kindLabel = t(`kind${att.kind[0].toUpperCase()}${att.kind.slice(1)}`) || att.kind;
  return (
    <div className={`cw-attach-card${att.status === 'error' ? ' cw-attach-error' : ''}`}>
      <span className="cw-attach-icon"><KindIcon kind={att.kind} /></span>
      <span className="cw-attach-meta">
        <span className="cw-attach-name" title={att.filename}>{att.filename}</span>
        <span className="cw-attach-sub">
          {kindLabel}
          {fmtSize(att.size) && ` · ${fmtSize(att.size)}`}
          {att.status === 'uploading' && (<> · {t('uploading')}…</>)}
          {att.status === 'error' && ` · ${att.error || t('uploadFail')}`}
        </span>
      </span>
      {att.status === 'uploading' && <Loader2 size={13} className="cw-spinner" aria-label={t('uploading')} />}
      {att.status === 'error' && onRetry && (
        <button className="cw-attach-retry" onClick={onRetry}>{t('uploadRetry')}</button>
      )}
      <button className="cw-attach-x" onClick={() => onRemove(att.id)} aria-label={`${t('removeFile')}: ${att.filename}`} title={t('removeFile')}>
        <X size={13} />
      </button>
    </div>
  );
}
