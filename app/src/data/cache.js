/**
 * API Response Cache — sessionStorage-based with TTL
 * Avoids redundant network requests within a browsing session.
 */
const CACHE_PREFIX = 'dp_cache_';
const DEFAULT_TTL = 5 * 60 * 1000; // 5 minutes

export function getCached(key) {
  try {
    const raw = sessionStorage.getItem(CACHE_PREFIX + key);
    if (!raw) return null;
    const { data, timestamp, ttl } = JSON.parse(raw);
    if (Date.now() - timestamp < (ttl || DEFAULT_TTL)) {
      return data;
    }
    // Expired — remove
    sessionStorage.removeItem(CACHE_PREFIX + key);
  } catch {}
  return null;
}

export function setCache(key, data, ttl = DEFAULT_TTL) {
  try {
    sessionStorage.setItem(CACHE_PREFIX + key, JSON.stringify({
      data,
      timestamp: Date.now(),
      ttl,
    }));
  } catch {}
}

export function clearCache() {
  const keys = [];
  for (let i = 0; i < sessionStorage.length; i++) {
    const k = sessionStorage.key(i);
    if (k?.startsWith(CACHE_PREFIX)) keys.push(k);
  }
  keys.forEach(k => sessionStorage.removeItem(k));
}

/**
 * Fetch with cache — returns cached data if fresh, otherwise fetches.
 */
export async function fetchWithCache(url, options = {}, ttl = DEFAULT_TTL) {
  const cacheKey = url + (options.body || '');
  const cached = getCached(cacheKey);
  if (cached) return cached;

  const resp = await fetch(url, options);
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
  const data = await resp.json();
  setCache(cacheKey, data, ttl);
  return data;
}
