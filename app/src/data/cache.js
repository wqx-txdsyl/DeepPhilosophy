const PREFIX = 'dp_';
const TTL = 10 * 60 * 1000; // 10 minutes

export function cacheGet(key) {
  try {
    const raw = sessionStorage.getItem(PREFIX + key);
    if (!raw) return null;
    const { data, ts } = JSON.parse(raw);
    if (Date.now() - ts < TTL) return data;
    sessionStorage.removeItem(PREFIX + key);
  } catch {}
  return null;
}

export function cacheSet(key, data) {
  try {
    sessionStorage.setItem(PREFIX + key, JSON.stringify({ data, ts: Date.now() }));
  } catch {}
}
