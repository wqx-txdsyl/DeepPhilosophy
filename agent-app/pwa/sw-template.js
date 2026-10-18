/* Public assets only. API, authentication, streams and private files stay on the network. */
const CACHE = 'phiagent-pwa-__PWA_VERSION__';
const OFFLINE = '/offline.html';
const SHELL = [OFFLINE, '/pwa/icon-192.png', '/pwa/icon-512.png'];

self.addEventListener('install', event => {
  event.waitUntil(caches.open(CACHE).then(cache => cache.addAll(SHELL)));
  // Keep the default waiting lifecycle: never replace an active streaming page.
});
self.addEventListener('activate', event => {
  event.waitUntil((async () => {
    for (const name of await caches.keys()) {
      if (name.startsWith('phiagent-pwa-') && name !== CACHE) await caches.delete(name);
    }
    await self.clients.claim();
  })());
});
function staticResponse(response) {
  return response.ok && !response.headers.get('cache-control')?.includes('no-store')
    && !response.headers.get('content-type')?.includes('text/html');
}
self.addEventListener('fetch', event => {
  const request = event.request;
  const url = new URL(request.url);
  if (request.method !== 'GET' || url.origin !== self.location.origin
      || request.headers.has('authorization') || url.pathname.startsWith('/api/')) return;
  const appPage = url.pathname === '/' || /^\/(agent|projects)(\/|$)/.test(url.pathname);
  if (request.mode === 'navigate' && appPage) {
    event.respondWith(fetch(request,{cache:'no-store'})
      .then(response => response.status >= 500 ? caches.match(OFFLINE) : response)
      .catch(() => caches.match(OFFLINE)));
    return;
  }
  if (url.search || !['/assets/', '/pwa/'].some(prefix => url.pathname.startsWith(prefix))) return;
  event.respondWith((async () => {
    const cache = await caches.open(CACHE);
    const cached = await cache.match(request);
    if (cached) return cached;
    const response = await fetch(request);
    if (staticResponse(response)) await cache.put(request,response.clone());
    return response;
  })());
});
