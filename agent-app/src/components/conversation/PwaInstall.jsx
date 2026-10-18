import { useEffect, useRef, useState } from 'react';
import { Download } from 'lucide-react';
import { useLang } from '../../utils/i18n';
import { standaloneApp, installPrompt, clearInstallPrompt } from '../../utils/pwa';
import { OverlayModal } from './Modal';

export default function PwaInstall({ className = 'cw-side-row', role, onActivate }) {
  const {lang} = useLang();
  const [installed,setInstalled] = useState(standaloneApp);
  const [prompt,setPrompt] = useState(installPrompt);
  const [help,setHelp] = useState(false);
  const [busy,setBusy] = useState(false);
  const returnFocus = useRef(null);
  const zh = lang !== 'en';
  useEffect(() => {
    const offer = () => setPrompt(installPrompt());
    const done = () => {setInstalled(true);setPrompt(null);setHelp(false);};
    const query = window.matchMedia('(display-mode: standalone)');
    const mode = () => setInstalled(standaloneApp());
    window.addEventListener('phiagent-install-ready',offer);
    window.addEventListener('appinstalled',done);
    query.addEventListener('change',mode);
    return () => {
      window.removeEventListener('phiagent-install-ready',offer);
      window.removeEventListener('appinstalled',done);
      query.removeEventListener('change',mode);
    };
  }, []);
  useEffect(() => {
    if (!help) return;
    const previous = returnFocus.current;
    const escape = event => { if (event.key === 'Escape') setHelp(false); };
    window.addEventListener('keydown',escape);
    return () => { window.removeEventListener('keydown',escape); if (previous?.isConnected && previous.getClientRects().length) previous.focus(); };
  }, [help]);
  if (installed) return null;
  const install = async () => {
    onActivate?.();
    returnFocus.current = document.activeElement;
    if (!prompt) {setHelp(true);return;}
    setBusy(true);
    try { await prompt.prompt(); if ((await prompt.userChoice).outcome === 'accepted') setInstalled(true); }
    catch { setHelp(true); }
    finally {clearInstallPrompt();setPrompt(null);setBusy(false);}
  };
  return <>
    <button className={className} role={role} onClick={install} disabled={busy}><Download size={16} aria-hidden="true" /><span>{zh?'安装 PhiAgent':'Install PhiAgent'}</span></button>
    {help && <OverlayModal onClose={()=>setHelp(false)} width={420}><section role="dialog" aria-modal="true" aria-labelledby="pwa-install-title">
      <h2 id="pwa-install-title">{zh?'安装 PhiAgent':'Install PhiAgent'}</h2>
      <p>{zh?'在 Chrome 或 Edge 的地址栏、浏览器菜单中选择“安装应用”。':'Choose Install app in the Chrome or Edge address bar or browser menu.'}</p>
      <p>{zh?'iPhone / iPad：在 Safari 中点“分享”，再选择“添加到主屏幕”。':'iPhone / iPad: in Safari, tap Share, then Add to Home Screen.'}</p>
      <p>{zh?'Mac Safari：菜单“文件”→“添加到程序坞”。':'Mac Safari: File → Add to Dock.'}</p>
      <p>{zh?'安装后可从桌面独立打开。生成回复仍需联网。':'Open it in its own window from your home screen or desktop. Replies still require a connection.'}</p>
      <button className="cw-btn cw-btn-ghost" onClick={()=>setHelp(false)} autoFocus>{zh?'知道了':'Done'}</button>
    </section></OverlayModal>}
  </>;
}
