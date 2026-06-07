/**
 * UserData —— 本地用户数据管理
 * 自动保存阅读进度 + 聊天历史到 localStorage
 * 每10分钟刷新一次时间戳
 */
const STORAGE_KEY = 'dp_userdata';
const SAVE_INTERVAL = 10 * 60 * 1000; // 10 minutes

let saveTimer = null;

function now() {
  return new Date().toISOString();
}

export function loadUserData() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) return JSON.parse(raw);
  } catch {}
  return {
    version: 1,
    created: now(),
    updated: now(),
    readingHistory: [],
    chatHistory: [],
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
export function saveReadingProgress(bookId, bookTitle, bookAuthor, page, percent) {
  const data = loadUserData();
  const existing = data.readingHistory.find(r => r.bookId === bookId);
  if (existing) {
    existing.page = page;
    existing.percent = percent;
    existing.lastReadAt = now();
  } else {
    data.readingHistory.unshift({
      bookId, bookTitle, bookAuthor, page, percent,
      lastReadAt: now(),
    });
  }
  // Keep last 100
  if (data.readingHistory.length > 100) data.readingHistory = data.readingHistory.slice(0, 100);
  saveUserData(data);
}

export function getReadingHistory() {
  return loadUserData().readingHistory;
}

// ============================================================
// Chat History
// ============================================================
export function saveChatMessage(role, content, sources) {
  const data = loadUserData();
  data.chatHistory.push({ role, content, sources: sources || [], createdAt: now() });
  if (data.chatHistory.length > 500) data.chatHistory = data.chatHistory.slice(-500);
  saveUserData(data);
}

export function getChatHistory() {
  return loadUserData().chatHistory;
}

export function clearChatHistory() {
  const data = loadUserData();
  data.chatHistory = [];
  saveUserData(data);
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
        if (data.version && data.readingHistory && data.chatHistory) {
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
