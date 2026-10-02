/**
 * ConversationStore — 会话持久化统一抽象（§12）
 *
 * 组件禁止直接操作 localStorage；未来可把 LocalConversationStore 平滑替换为
 * 登录后由 conversationSync 按会话同步服务器；本地仅作账号隔离缓存和离线队列。
 *
 * 存储键: phiagent_conversations_v1（全部会话单键 JSON）
 * legacy 迁移: dp_agent_msgs_v2_{agent} → 每智能体一个会话（迁移后删除旧键）
 */
import {
  normalizeConversation,
  toPersistedMessage,
  legacyMessagesToConversations,
  GENERAL_AGENT,
  clonePersisted,
} from './conversationLogic.js';

const STORAGE_KEY = 'phiagent_conversations_v1';
const LEGACY_MSG_PREFIX = 'dp_agent_msgs_v2_';

export class ConversationNotFoundError extends Error {
  constructor(id) { super(`conversation not found: ${id}`); this.name = 'ConversationNotFoundError'; this.id = id; }
}

export class LocalConversationStore {
  constructor(storage = (typeof window !== 'undefined' ? window.localStorage : null)) {
    this.storage = storage;
    this._migrated = false;
    this.key = STORAGE_KEY;
    this.owner = 'legacy';
    this.listeners = new Set();
    this.memory = null;
    this.volatile = false;
  }

  setScope(owner, claimLegacy = false) {
    this.owner = owner;
    this.key = `phiagent_conversations_v2:${owner}`;
    this.memory = null;
    this.volatile = false;
    this._migrated = false;
    if (claimLegacy && this.storage && !this.storage.getItem(this.key)) {
      const old = this.storage.getItem(STORAGE_KEY);
      if (old) {
        // Only the authenticated identity already present in this browser may
        // claim old unscoped history. A different login cannot claim it.
        this.storage.setItem(this.key, old);
        this.storage.removeItem(STORAGE_KEY);
      }
    }
  }

  subscribe(fn) { this.listeners.add(fn); return () => this.listeners.delete(fn); }
  replaceAll(list) { this._saveAll(list, false); }

  // ── 内部 ──
  _loadAll() {
    if (this.volatile && this.memory) return clonePersisted(this.memory);
    if (!this.storage) return [];
    try {
      const raw = this.storage.getItem(this.key);
      if (!raw) return [];
      const parsed = JSON.parse(raw);
      if (!Array.isArray(parsed)) return [];
      return parsed.map(normalizeConversation).filter(Boolean);
    } catch (e) {
      console.warn('[ConversationStore] 读取失败', e);
      throw e;   // 让上层能呈现"加载失败 + 重试"（§13）
    }
  }

  _saveAll(list, notify = true) {
    const previous = this._loadAll();
    this.memory = clonePersisted(list);
    try {
      this.storage?.setItem(this.key, JSON.stringify(list));
      this.volatile = !this.storage;
    } catch (e) {
      this.volatile = true;
      // Keep the live copy and continue server saving. Surface the failure
      // instead of silently pretending local persistence succeeded.
      if (typeof window !== 'undefined') window.dispatchEvent(new Event('phiagent-cache-error'));
    }
    if (notify) for (const fn of this.listeners) fn(list, previous, this.owner);
  }

  _mutate(id, fn) {
    const list = this._loadAll();
    const idx = list.findIndex((c) => c.conversation_id === id);
    if (idx < 0) return null;   // 防复活: 不存在的会话不因 late write 重新出现
    const next = fn(list[idx], list);
    if (next === null) {        // fn 返回 null → 删除
      list.splice(idx, 1);
    } else {
      list[idx] = next;
    }
    this._saveAll(list);
    return next;
  }

  // ── legacy 迁移（幂等: v1 键已存在则跳过; 迁移后删除旧键）──
  migrateLegacy() {
    if (this._migrated || !this.storage) return { migrated: 0 };
    this._migrated = true;
    try {
      if (this.storage.getItem(this.key)) return { migrated: 0 };
      if (!['legacy', 'guest'].includes(this.owner)) return { migrated: 0 };
      const legacyByAgent = {};
      for (let i = this.storage.length - 1; i >= 0; i--) {
        const k = this.storage.key(i);
        if (k && k.startsWith(LEGACY_MSG_PREFIX)) {
          const agent = k.slice(LEGACY_MSG_PREFIX.length);
          try { legacyByAgent[agent] = JSON.parse(this.storage.getItem(k)); } catch { /* 坏数据跳过 */ }
        }
      }
      const convs = legacyMessagesToConversations(legacyByAgent);
      if (convs.length) this._saveAll(convs);
      if (this.volatile) return { migrated: 0 }; // Never remove the only recoverable copy.
      // 清理旧键（含更早的 v1 残留, 与旧版清理逻辑一致）
      for (let i = this.storage.length - 1; i >= 0; i--) {
        const k = this.storage.key(i);
        if (k && (k.startsWith('dp_agent_msgs_'))) this.storage.removeItem(k);
      }
      return { migrated: convs.length };
    } catch (e) {
      console.warn('[ConversationStore] legacy 迁移失败', e);
      return { migrated: 0 };
    }
  }

  // ── 对外接口（§12 规定的最小集合）──
  listConversations() {
    return this._loadAll().sort((a, b) => Date.parse(b.updated_at) - Date.parse(a.updated_at));
  }

  getConversation(id) {
    const conv = this._loadAll().find((c) => c.conversation_id === id);
    if (!conv) throw new ConversationNotFoundError(id);
    return conv;
  }

  createConversation({ title = '新对话', default_agent_id = GENERAL_AGENT, reading_context = null, conversation_id = null } = {}) {
    const list = this._loadAll();
    // updated_at 单调递增: 同毫秒创建的会话排序仍确定（listConversations 新→旧）
    const maxT = list.reduce((m, c) => Math.max(m, Date.parse(c.updated_at) || 0), 0);
    const now = Date.now();
    const ts = now <= maxT ? maxT + 1 : now;
    const iso = new Date(ts).toISOString();
    const conv = normalizeConversation({
      conversation_id: conversation_id || `conv_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 8)}`,
      title, default_agent_id, last_used_agent_id: default_agent_id,
      created_at: iso, updated_at: iso,
      ...(reading_context ? { reading_context } : {}),
      messages: [],
    });
    list.push(conv);
    this._saveAll(list);
    return conv;
  }

  updateConversation(id, patch) {
    return this._mutate(id, (conv) => normalizeConversation({ ...conv, ...patch, conversation_id: conv.conversation_id }));
  }

  deleteConversation(id) {
    const list = this._loadAll();
    const next = list.filter((c) => c.conversation_id !== id);
    if (next.length !== list.length) this._saveAll(next);
    return list.length - next.length > 0;
  }

  appendMessage(id, message) {
    const persisted = toPersistedMessage(message);
    if (!persisted) return null;
    persisted.conversation_id = id;
    return this._mutate(id, (conv) => {
      const messages = [...conv.messages, { ...persisted, created_at: persisted.created_at || new Date().toISOString() }];
      return normalizeConversation({ ...conv, messages, updated_at: new Date().toISOString() });
    });
  }

  updateMessage(id, messageId, patch) {
    return this._mutate(id, (conv) => {
      let hit = false;
      const messages = conv.messages.map((m) => {
        if (m.message_id !== messageId) return m;
        hit = true;
        return { ...m, ...toPersistedMessage({ ...m, ...patch }), message_id: m.message_id, conversation_id: m.conversation_id };
      });
      if (!hit) return conv;
      return normalizeConversation({ ...conv, messages, updated_at: new Date().toISOString() });
    });
  }

  setConversationTitle(id, title) {
    return this._mutate(id, (conv) => normalizeConversation({ ...conv, title: String(title || '').trim() || conv.title }));
  }

  setDefaultAgent(id, agentId) {
    return this._mutate(id, (conv) => normalizeConversation({ ...conv, default_agent_id: agentId || GENERAL_AGENT }));
  }

  setLastUsedAgent(id, agentId) {
    return this._mutate(id, (conv) => normalizeConversation({ ...conv, last_used_agent_id: agentId || GENERAL_AGENT }));
  }
}

export const conversationStore = new LocalConversationStore();
