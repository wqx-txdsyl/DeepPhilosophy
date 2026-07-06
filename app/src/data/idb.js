/**
 * IndexedDB wrapper for large user data (chat history, reading progress, notes).
 * Fallback to localStorage if IndexedDB is unavailable.
 */
const DB_NAME = 'dp_userdb';
const DB_VERSION = 1;
const STORE_NAME = 'userdata';

let dbPromise = null;

function openDB() {
  if (dbPromise) return dbPromise;
  dbPromise = new Promise((resolve, reject) => {
    if (!window.indexedDB) {
      reject(new Error('IndexedDB not available'));
      return;
    }
    const req = indexedDB.open(DB_NAME, DB_VERSION);
    req.onupgradeneeded = (e) => {
      const db = e.target.result;
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        db.createObjectStore(STORE_NAME);
      }
    };
    req.onsuccess = (e) => resolve(e.target.result);
    req.onerror = () => reject(req.error);
  });
  return dbPromise;
}

export async function idbGet(key) {
  try {
    const db = await openDB();
    return new Promise((resolve) => {
      const tx = db.transaction(STORE_NAME, 'readonly');
      const store = tx.objectStore(STORE_NAME);
      const req = store.get(key);
      req.onsuccess = () => resolve(req.result);
      req.onerror = () => resolve(null);
    });
  } catch {
    // Fallback to localStorage
    try {
      const raw = localStorage.getItem(`dp_idb_${key}`);
      return raw ? JSON.parse(raw) : undefined;
    } catch { return undefined; }
  }
}

export async function idbSet(key, value) {
  try {
    const db = await openDB();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE_NAME, 'readwrite');
      const store = tx.objectStore(STORE_NAME);
      const req = store.put(value, key);
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error);
    });
  } catch {
    // Fallback to localStorage
    try {
      localStorage.setItem(`dp_idb_${key}`, JSON.stringify(value));
    } catch {}
  }
}

export async function idbDelete(key) {
  try {
    const db = await openDB();
    return new Promise((resolve) => {
      const tx = db.transaction(STORE_NAME, 'readwrite');
      tx.objectStore(STORE_NAME).delete(key);
      tx.oncomplete = () => resolve();
    });
  } catch {
    localStorage.removeItem(`dp_idb_${key}`);
  }
}
