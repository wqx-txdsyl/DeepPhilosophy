import { useState } from 'react';
import { Check, Copy, RotateCcw, Square, TriangleAlert } from 'lucide-react';
import { streamNotice } from '../../data/streamNotice';
import { copyAnswerText } from '../../utils/clipboard';

export function StreamNotice({ message, question, onSend, busy, zh = true }) {
  const [copied, setCopied] = useState(false);
  const [manualCopy, setManualCopy] = useState(false);
  const hasContent = !!String(message.content || '').trim();
  const view = streamNotice({ state: message.stream_state, error: message.error, hasContent, hasQuestion: !!question?.trim(), zh });
  const stopped = view.kind === 'stopped';
  const diagnosticText = ['PhiAgent', view.title, view.diagnostics].join('\n');
  const copy = async () => {
    const ok = await copyAnswerText(diagnosticText);
    setCopied(ok); setManualCopy(!ok);
  };
  return <section className="general-stream-notice" data-kind={view.kind} aria-label={view.title}>
    <div className="general-notice-symbol" aria-hidden="true">{stopped ? <Square size={16} /> : <TriangleAlert size={18} />}</div>
    <div className="general-notice-content">
      <div role={stopped ? 'status' : 'alert'}>
        <p className="general-notice-title">{view.title}</p>
        <p className="general-notice-description">{view.description}{view.retained && <> {view.retained}</>}</p>
      </div>
      <div className="general-notice-actions">
        {view.action && typeof onSend === 'function' && <button type="button" className="general-notice-retry" disabled={busy} onClick={() => onSend(view.action === 'continue'
          ? (zh ? '请继续完成刚才未完成的回答；如果存在错误，请先修正。' : 'Please complete this interrupted answer, correcting any errors first.') : question, message)}>
          <RotateCcw size={13} aria-hidden="true" />{view.actionLabel}
        </button>}
        {!stopped && <details className="general-notice-details">
          <summary>{zh ? '错误详情' : 'Error details'}</summary>
          <div className="general-notice-diagnostics">
            <pre>{view.diagnostics}</pre>
            <button type="button" onClick={copy}>{copied ? <Check size={13} /> : <Copy size={13} />}{copied ? (zh ? '已复制' : 'Copied') : (zh ? '复制错误信息' : 'Copy error information')}</button>
            {copied && <span className="general-notice-copy-status" role="status">{zh ? '错误信息已复制' : 'Error information copied'}</span>}
            {manualCopy && <label className="general-notice-manual-copy">{zh ? '可长按或选择下方文字复制' : 'Select the text below to copy'}
              <textarea readOnly value={diagnosticText} aria-label={zh ? '可复制的错误信息' : 'Error information to copy'} />
            </label>}
          </div>
        </details>}
      </div>
    </div>
  </section>;
}
