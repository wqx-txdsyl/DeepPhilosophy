/** Account-owned outbox + per-conversation revision synchronization.
 * Token/owner are captured per session. Late responses never touch a new account.
 */
import { normalizeConversation } from './conversationLogic.js';

export function mergeConversation(remote, local) {
  if (!remote) return normalizeConversation(local);
  if (!local) return normalizeConversation(remote);
  const messages = new Map((remote.messages || []).map(m => [m.message_id, m]));
  for (const m of local.messages || []) {
    const old = messages.get(m.message_id);
    if (!old) { messages.set(m.message_id, m); continue; }
    // A stale partial stream must never shorten a completed reply.
    const preferOld = (old.content || '').length > (m.content || '').length;
    messages.set(m.message_id, { ...old, ...m, ...(preferOld ? {
      content: old.content, tool_events: old.tool_events, stream_state: old.stream_state,
      citations: old.citations, evidence: old.evidence,
    } : {}) });
  }
  return normalizeConversation({ ...remote, ...local,
    messages: [...messages.values()].sort((a, b) => Date.parse(a.created_at) - Date.parse(b.created_at)) });
}

export class ConversationSync {
  constructor(store, { owner, token, fetcher = (...args) => fetch(...args), onStatus = () => {}, onChange = () => {} }) {
    this.store = store; this.owner = owner; this.token = token;
    this.fetcher = fetcher; this.onStatus = onStatus; this.onChange = onChange;
    this.closed = false; this.hydrated = false; this.timer = null; this.running = null;
    this.revisions = {}; this.queue = new Map(); this.generation = 0;
    this.metaKey = `phiagent_sync_v2:${owner}`;
    try {
      const meta = JSON.parse(store.storage?.getItem(this.metaKey) || '{}');
      this.revisions = meta.revisions || {};
      for (const id of meta.dirty || []) {
        const c = store._loadAll().find(c => c.conversation_id === id);
        this.queue.set(id, { data: c || null, version: ++this.generation });
      }
    } catch { /* malformed metadata never replaces history */ }
    this.unsubscribe = store.subscribe((list, previous, scope) => {
      if (scope !== this.owner || this.closed) return;
      const old = new Map(previous.map(c => [c.conversation_id, c]));
      for (const c of list) {
        if (JSON.stringify(c) !== JSON.stringify(old.get(c.conversation_id))) this.enqueue(c.conversation_id, c);
        old.delete(c.conversation_id);
      }
      for (const id of old.keys()) this.enqueue(id, null);
    });
  }
  active() { return !this.closed && this.store.owner === this.owner; }
  saveMeta() {
    try { this.store.storage?.setItem(this.metaKey, JSON.stringify({ revisions: this.revisions, dirty: [...this.queue.keys()] })); }
    catch { this.onStatus('cache-error'); }
  }
  enqueue(id, data) {
    this.queue.set(id, { data: structuredClone(data), version: ++this.generation });
    this.saveMeta(); this.onStatus('saving'); this.schedule();
  }
  schedule(delay = 700) {
    clearTimeout(this.timer);
    if (this.closed || !this.hydrated) return;
    this.timer = setTimeout(() => this.flush().catch(() => {}), delay);
  }
  async request(path, options = {}) {
    const response = await this.fetcher(`/api/agent/conversations${path}`, { ...options,
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${this.token}` }, keepalive: false });
    const body = await response.json();
    if (!response.ok && response.status !== 409) throw new Error(`history:${response.status}`);
    return { response, body };
  }
  apply(list) {
    if (!this.active()) return;
    this.store.replaceAll(list); this.onChange();
  }
  async hydrate() {
    this.onStatus('loading');
    try {
      const { body } = await this.request('');
      if (!this.active()) return;
      if (!Array.isArray(body.records)) throw new Error('invalid history response');
      const local = new Map(this.store._loadAll().map(c => [c.conversation_id, c]));
      const combined = [];
      for (const record of body.records) {
        const id = record.conversation_id;
        this.revisions[id] = record.revision;
        const cached = local.get(id); local.delete(id);
        if (record.deleted) { this.queue.delete(id); continue; }
        const pending = this.queue.get(id);
        if (pending?.data === null) continue;
        const c = pending ? mergeConversation(record.data, pending.data) : record.data;
        if (pending) this.queue.set(id, { data: c, version: ++this.generation });
        combined.push(c);
        // Old browser caches predate sync metadata; union them once safely.
        if (cached && !pending && !this.revisions.__migrated) {
          const merged = mergeConversation(record.data, cached);
          combined[combined.length - 1] = merged;
          this.queue.set(id, { data: merged, version: ++this.generation });
        }
      }
      for (const [id, c] of local) {
        combined.push(c);
        if (!this.queue.has(id)) this.queue.set(id, { data: c, version: ++this.generation });
      }
      this.revisions.__migrated = 1;
      this.apply(combined); this.saveMeta();
      this.hydrated = true;
      this.onStatus(this.queue.size ? 'saving' : 'saved');
      if (this.queue.size) await this.flush();
    } catch (error) {
      console.warn('[HistorySync] restore', error.message);
      if (this.active()) { this.hydrated = true; this.onStatus('offline'); this.schedule(10000); }
    }
  }
  async flush() {
    clearTimeout(this.timer);
    if (this.running) return this.running;
    this.running = this._flush();
    try { await this.running; } finally { this.running = null; }
  }
  async _flush() {
    try {
      for (const [id, pending] of [...this.queue]) {
        const { response, body } = await this.request(`/${encodeURIComponent(id)}`, pending.data === null
          ? { method: 'DELETE' }
          : { method: 'PUT', body: JSON.stringify({ data: pending.data, expected_revision: this.revisions[id] || 0 }) });
        const record = response.status === 409 ? body.detail?.record : body.record;
        if (!record) throw new Error('invalid record');
        this.revisions[id] = record.revision;
        const current = this.queue.get(id);
        if (record.deleted) {
          this.queue.delete(id);
          if (this.active()) this.apply(this.store._loadAll().filter(c => c.conversation_id !== id));
        } else if (response.status === 409) {
          if (current?.data) {
            const merged = mergeConversation(record.data, current.data);
            this.queue.set(id, { data: merged, version: ++this.generation });
            if (this.active()) this.apply(this.store._loadAll().map(c => c.conversation_id === id ? merged : c));
          }
        } else if (current?.version === pending.version) this.queue.delete(id);
        this.saveMeta();
      }
      if (this.active()) {
        this.onStatus(this.queue.size ? 'saving' : 'saved');
        if (this.queue.size) this.schedule();
      }
    } catch (error) {
      console.warn('[HistorySync] save', error.message);
      if (this.active()) { this.onStatus('offline'); this.schedule(10000); }
      throw new Error('history sync unavailable');
    }
  }
  close() {
    this.unsubscribe(); clearTimeout(this.timer);
    // Flush captured data with the captured token, never the next user's token.
    this.flush().catch(() => {}); this.closed = true;
  }
}
