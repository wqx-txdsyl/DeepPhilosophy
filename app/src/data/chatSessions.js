/**
 * 对话会话管理 —— 多轮对话持久化、自动标题、历史列表
 * 存储: localStorage (本地) / 云端同步 (通过 userData)
 */
const STORAGE_KEY = 'dp_chat_sessions';
const CURRENT_KEY = 'dp_current_session';

// 生成唯一 ID
function genId() {
  return 'sess_' + Date.now().toString(36) + '_' + Math.random().toString(36).slice(2, 8);
}

// 从首条用户消息生成标题（截取前30字）
function genTitle(messages) {
  const firstUser = messages.find(m => m.role === 'user');
  if (!firstUser) return '新对话';
  const text = typeof firstUser.content === 'string' ? firstUser.content : '';
  return text.replace(/\n/g, ' ').slice(0, 30) + (text.length > 30 ? '...' : '');
}

// 读取所有会话
export function getSessions() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY)) || [];
  } catch { return []; }
}

// 保存所有会话
function saveSessions(sessions) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions));
}

// 获取当前活跃会话
export function getCurrentSession() {
  try {
    const id = localStorage.getItem(CURRENT_KEY);
    if (!id) return null;
    const sessions = getSessions();
    return sessions.find(s => s.id === id) || null;
  } catch { return null; }
}

// 设置当前活跃会话
export function setCurrentSession(sessionId) {
  localStorage.setItem(CURRENT_KEY, sessionId);
}

// 创建新会话
export function createSession() {
  const session = {
    id: genId(),
    title: '新对话',
    messages: [],
    createdAt: Date.now(),
    updatedAt: Date.now(),
  };
  const sessions = getSessions();
  sessions.unshift(session);
  saveSessions(sessions);
  setCurrentSession(session.id);
  return session;
}

// 更新会话消息
export function updateSession(sessionId, messages) {
  const sessions = getSessions();
  const idx = sessions.findIndex(s => s.id === sessionId);
  if (idx === -1) return;
  sessions[idx].messages = messages;
  sessions[idx].title = genTitle(messages);
  sessions[idx].updatedAt = Date.now();
  saveSessions(sessions);
}

// 删除会话
export function deleteSession(sessionId) {
  const sessions = getSessions().filter(s => s.id !== sessionId);
  saveSessions(sessions);
  if (localStorage.getItem(CURRENT_KEY) === sessionId) {
    localStorage.removeItem(CURRENT_KEY);
  }
}

// 确保有活跃会话（没有则创建）
export function ensureSession() {
  let session = getCurrentSession();
  if (!session) {
    session = createSession();
  } else {
    setCurrentSession(session.id); // 刷新活跃标记
  }
  return session;
}

// 清空当前会话的消息（开新对话）
export function newConversation() {
  const session = createSession();
  return session;
}
