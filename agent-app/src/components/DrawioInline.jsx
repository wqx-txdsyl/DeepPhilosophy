import { useEffect, useRef, useState } from 'react';
import { DrawIoEmbed } from 'react-drawio';
import { useLang } from '../utils/i18n';

/**
 * DrawioInline — 对话内的 draw.io 内嵌编辑器（编辑后的图回填到此, 可继续编辑）
 */
export default function DrawioInline({ xml, onEdit, height = 320 }) {
  const { t } = useLang();
  const ref = useRef(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (ready && xml) {
      try { ref.current?.load({ xml }); } catch (e) { /* iframe 未就绪 */ }
    }
  }, [ready, xml]);

  return (
    <div style={{ position: 'relative', margin: '10px 0', border: '1px solid var(--border)',
                  borderRadius: 10, overflow: 'hidden', background: 'var(--card-bg)' }}>
      <div style={{ height }}>
        <DrawIoEmbed ref={ref} urlParameters={{ ui: 'min' }}
          onLoad={() => setReady(true)} onInit={() => setReady(true)} />
      </div>
      {onEdit && (
        <button onClick={onEdit} title={t('drawioReEdit')}
          style={{ position: 'absolute', top: 6, right: 6, fontSize: 11, cursor: 'pointer',
                   padding: '3px 8px', borderRadius: 6, border: '1px solid var(--border)',
                   background: 'var(--card-bg)', color: 'var(--text-dim)', zIndex: 5 }}>
          {t('drawioReEdit')}
        </button>
      )}
    </div>
  );
}
