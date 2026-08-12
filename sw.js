/* DeepPhilosophy Service Worker — 壳预缓存 + 网络优先（数据实时性优先于离线）
 * 版本号变更 → 安装新版并清理旧缓存
 * 不拦截: 跨域（OSS/jsDelivr 章节、Google 字体）、/api/*
 * 离线兜底: 已缓存资源直接返回; SPA 导航失败 → index.html
 */
const VERSION = 'dp-sw-v3';
const SHELL = ['/', '/index.html', '/manifest.json', '/favicon.png', '/icons/pwa-192.png', '/icons/pwa-512.png', '/icons/pwa-512-maskable.png'];

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(VERSION).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== VERSION).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (e) => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.origin !== location.origin) return;
  if (url.pathname.startsWith('/api/')) return;
  // UI 图标是静态装饰（icon-edit.png 等），cache-first 秒显——首访后不再等网络
  if (url.pathname.startsWith('/icons/') && !url.pathname.startsWith('/icons/pwa-')) {
    e.respondWith(
      caches.match(req).then((m) =>
        m || fetch(req).then((res) => {
          if (res.ok) { const copy = res.clone(); caches.open(VERSION).then((c) => c.put(req, copy)).catch(() => {}); }
          return res;
        })
      )
    );
    return;
  }
  e.respondWith(
    fetch(req)
      .then((res) => {
        const copy = res.clone();
        caches.open(VERSION).then((c) => c.put(req, copy)).catch(() => {});
        return res;
      })
      .catch(() =>
        caches.match(req).then((m) => m || (req.mode === 'navigate' ? caches.match('/index.html') : undefined))
      )
  );
});
