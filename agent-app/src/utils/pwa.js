export const standaloneApp = () => typeof window !== 'undefined' && typeof navigator !== 'undefined'
  && !!(window.matchMedia('(display-mode: standalone)').matches || navigator.standalone);
let pendingInstall = null;
export const installPrompt = () => pendingInstall;
export const clearInstallPrompt = () => { pendingInstall = null; };
// Capture before React/account hydration: browsers may offer installation early.
if (typeof window !== 'undefined') {
  window.addEventListener('beforeinstallprompt', event => {
    event.preventDefault(); pendingInstall = event;
    window.dispatchEvent(new Event('phiagent-install-ready'));
  });
  window.addEventListener('appinstalled', clearInstallPrompt);
}

export async function registerPwa() {
  if (!('serviceWorker' in navigator)) return null;
  try {
    const registration = await navigator.serviceWorker.register('/api/pwa/worker', {scope:'/', updateViaCache:'none'});
    window.addEventListener('focus', () => registration.update().catch(() => {}));
    return registration;
  } catch { return null; }
}
