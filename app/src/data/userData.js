/**
 * UserData —— 本地用户数据管理
 * 自动保存阅读进度到 localStorage
 * 每10分钟刷新一次时间戳
 */
const STORAGE_KEY = 'dp_userdata';
const SAVE_INTERVAL = 10 * 60 * 1000; // 10 minutes

let saveTimer = null;

function now() {
  return new Date().toISOString();
}

/** Get relative time string for display */
export function relativeTime(dateStr) {
  if (!dateStr) return '';
  const now = new Date();
  const then = new Date(dateStr);
  const diffMs = now - then;
  const diffSec = Math.floor(diffMs / 1000);
  const diffMin = Math.floor(diffSec / 60);
  const diffHr = Math.floor(diffMin / 60);
  const diffDay = Math.floor(diffHr / 24);

  if (diffSec < 60) return '刚刚';
  if (diffMin < 60) return `${diffMin}分钟前`;
  if (diffHr < 24) return `${diffHr}小时前`;
  if (diffDay < 7) return `${diffDay}天前`;
  // Fallback to local date string
  return then.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' });
}

export function loadUserData() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      const data = JSON.parse(raw);
      let fixed = false;
      if (!Array.isArray(data.readingHistory)) {
        data.readingHistory = [];
        fixed = true;
      }
      // 持久化修复，永久治愈旧数据
      if (fixed) {
        data.updated = now();
        try { localStorage.setItem(STORAGE_KEY, JSON.stringify(data)); } catch {}
      }
      return data;
    }
  } catch {}
  return {
    version: 1,
    created: now(),
    updated: now(),
    readingHistory: [],
  };
}

function saveUserData(data) {
  data.updated = now();
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
  } catch {}
}

// ============================================================
// Reading History
// ============================================================
export function saveReadingProgress(bookId, bookTitle, bookAuthor, page, percent, fileType = '') {
  const data = loadUserData();
  const idx = data.readingHistory.findIndex(r => r.bookId === bookId);
  if (idx >= 0) {
    const [entry] = data.readingHistory.splice(idx, 1);
    entry.page = page;
    entry.percent = percent;
    entry.lastReadAt = now();
    if (fileType) entry.fileType = fileType;
    data.readingHistory.unshift(entry);
  } else {
    data.readingHistory.unshift({
      bookId, bookTitle, bookAuthor, page, percent,
      lastReadAt: now(),
      fileType: fileType || '',
    });
  }
  if (data.readingHistory.length > 100) data.readingHistory = data.readingHistory.slice(0, 100);
  saveUserData(data);

  // Cloud sync (fire-and-forget)
  const token = localStorage.getItem('dp_token');
  if (token) {
    fetch(`${getApiBase()}/api/history/reading`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
      body: JSON.stringify({ book_id: bookId, book_title: bookTitle, book_author: bookAuthor, page, percent }),
      signal: AbortSignal.timeout(5000),
    }).catch(() => {});
  }
}

import { getApiBase } from '../utils/api.js';

export function getReadingHistory() {
  return loadUserData().readingHistory;
}

// ============================================================
// Export / Import
// ============================================================
export function exportToFile() {
  const data = loadUserData();
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'userdata.phi';
  a.click();
  URL.revokeObjectURL(url);
}

export function importFromFile(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const data = JSON.parse(e.target.result);
        if (data.version && Array.isArray(data.readingHistory)) {
          saveUserData(data);
          resolve(data);
        } else {
          reject(new Error('Invalid userdata file'));
        }
      } catch {
        reject(new Error('Cannot parse file'));
      }
    };
    reader.onerror = () => reject(new Error('Read error'));
    reader.readAsText(file);
  });
}

export function getAllUserData() {
  return loadUserData();
}

// ============================================================
// Auto-save timer
// ============================================================
export function startAutoSave() {
  if (saveTimer) return;
  saveTimer = setInterval(() => {
    saveUserData(loadUserData());
  }, SAVE_INTERVAL);
}

export function stopAutoSave() {
  if (saveTimer) {
    clearInterval(saveTimer);
    saveTimer = null;
  }
}
