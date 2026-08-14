import { useEffect, useRef, useState } from 'react';
import { DrawIoEmbed } from 'react-drawio';
import { useLang } from '../utils/i18n';

/**
 * DrawioModal — 全屏 draw.io 编辑器（autosave 跟踪编辑, 关闭时回传最新 XML）
 * onClose(editedXml) — editedXml 为编辑后的 XML（未编辑则与原 xml 相同）
 */
export default function DrawioModal({ xml, onClose }) {
  const { t } = useLang();
  const ref = useRef(null);
  const latestXml = useRef(xml);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (ready && xml) {
      try { ref.current?.load({ xml }); } catch (e) { /* iframe 未就绪 */ }
    }
  }, [ready, xml]);

  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,.4)', zIndex: 1200,
                 display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }}>
      <div style={{ background: 'var(--card-bg)', borderRadius: 12, width: '100%', maxWidth: 920, height: '82vh',
                    display: 'flex', flexDirection: 'column', overflow: 'hidden',
                    boxShadow: '0 16px 60px rgba(0,0,0,.25)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                      padding: '10px 16px', borderBottom: '1px solid var(--border)' }}>
          <span style={{ fontSize: 14, fontWeight: 600 }}>{t('drawioTitle')}</span>
          <span onClick={() => onClose(latestXml.current)} style={{ cursor: 'pointer', color: 'var(--text-dim)', fontSize: 13 }}>✕ {t('drawioDone')}</span>
        </div>
        <div style={{ flex: 1, minHeight: 0 }}>
          <DrawIoEmbed
            ref={ref}
            urlParameters={{ ui: 'min' }}
            autosave
            onLoad={() => setReady(true)}
            onInit={() => setReady(true)}
            onAutoSave={({ xml }) => { latestXml.current = xml; }}
            onExit={() => onClose(latestXml.current)}
          />
        </div>
      </div>
    </div>
  );
}
