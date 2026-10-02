/** Account-owned outbox + per-conversation revision synchronization.
 * Token/owner are captured per session. Late responses never touch a new account.
 */
import { normalizeConversation, clonePersisted } from './conversationLogic.js';

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
    this.pulling = null;
    this.reading = new Map();
    this.busy = new Set(); this.lastPushed = new Map();
    this.revisions = {}; this.queue = new Map(); this.generation = 0;
    this.metaKey = `phiagent_sync_v2:${owner}`;
    try {
      const meta = JSON.parse(store.storage?.getItem(this.metaKey) || '{}');
      this.revisions = meta.revisions || {};
      for (const id of meta.dirty || []) {
        const c = store._loadAll().find(c => c.conversation_id === id);
        if (c || (meta.deleted || []).includes(id)) this.queue.set(id, { data: c || null, version: ++this.generation });
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
    try { this.store.storage?.setItem(this.metaKey, JSON.stringify({ revisions: this.revisions, dirty: [...this.queue.keys()],
      deleted:[...this.queue].filter(([,v])=>v.data===null).map(([id])=>id) })); }
    catch { this.onStatus('cache-error'); }
  }
  enqueue(id, data) {
    this.queue.set(id, { data: clonePersisted(data), version: ++this.generation });
    this.saveMeta(); this.onStatus('saving'); this.schedule();
  }
  beginStream(id) { this.busy.add(id); }
  endStream(id) { this.busy.delete(id); if (this.queue.has(id)) this.schedule(0); }
  schedule(delay) {
    clearTimeout(this.timer);
    if (this.closed) return;
    if (delay === undefined) delay = this.queue.size ? Math.min(...[...this.queue.keys()].map(id=>
      this.busy.has(id) ? Math.max(700,20000-(Date.now()-(this.lastPushed.get(id)||0))) : 700)) : 700;
    this.timer = setTimeout(() => (this.hydrated ? this.flush() : this.hydrate()).catch(() => {}), delay);
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
    if (!this.active()) return;
    if (this.pulling) return this.pulling;
    this.pulling = this._hydrate();
    try { await this.pulling; } finally { this.pulling = null; }
  }
  async _hydrate() {
    this.onStatus('loading');
    try {
      const { body } = await this.request('?index=true');
      if (!this.active()) return;
      if (!Array.isArray(body.records)) throw new Error('invalid history response');
      const local = new Map(this.store._loadAll().map(c => [c.conversation_id, c]));
      const combined = [];
      for (let record of body.records) {
        const id = record.conversation_id;
        const knownRevision = this.revisions[id];
        this.revisions[id] = record.revision;
        const cached = local.get(id); local.delete(id);
        if (record.deleted) { this.queue.delete(id); continue; }
        const pending = this.queue.get(id);
        if (pending?.data === null) continue;
        if (record.data.messages_loaded === false && pending?.data) {
          record = (await this.request(`/${encodeURIComponent(id)}`)).body.record;
          if (!this.active()) return;
          this.revisions[id] = record.revision;
          if (record.deleted) { this.queue.delete(id); continue; }
        }
        if (record.data.messages_loaded === false && cached && cached.messages_loaded !== false) {
          record.data = knownRevision === record.revision ? cached : { ...cached, ...record.data, messages:cached.messages };
        }
        const c = pending ? mergeConversation(record.data, pending.data) : record.data;
        if (pending) this.queue.set(id, { data: c, version: ++this.generation });
        combined.push(c);
        // Old browser caches predate sync metadata; union them once safely.
        if (cached && cached.messages_loaded !== false && !pending && !this.revisions.__migrated) {
          if (record.data.messages_loaded === false) {
            record = (await this.request(`/${encodeURIComponent(id)}`)).body.record;
            if (!this.active()) return;
            this.revisions[id] = record.revision;
          }
          const merged = mergeConversation(record.data, cached);
          combined[combined.length - 1] = merged;
          this.queue.set(id, { data: merged, version: ++this.generation });
        }
      }
      for (const [id, c] of local) {
        combined.push(c);
        if (!this.queue.has(id) && c.messages_loaded !== false) this.queue.set(id, { data: c, version: ++this.generation });
      }
      this.revisions.__migrated = 1;
      this.apply(combined); this.saveMeta();
      this.hydrated = true;
      this.onStatus(this.queue.size ? 'saving' : 'saved');
      if (this.queue.size) await this.flush();
    } catch (error) {
      console.warn('[HistorySync] restore', error.message);
      if (this.active()) { this.hydrated = false; this.onStatus('offline'); this.schedule(3000); }
    }
  }
  async flush() {
    clearTimeout(this.timer);
    if (!this.hydrated && !this.closed) return this.hydrate();
    if (this.running) return this.running;
    this.running = this._flush();
    try { await this.running; } finally { this.running = null; }
  }
  async ensureConversation(id) {
    if (!this.active()) return;
    const local = this.store._loadAll().find(c => c.conversation_id === id);
    if (local && local.messages_loaded !== false) return local;
    if (this.reading.has(id)) return this.reading.get(id);
    const task = (async () => {
      const { body } = await this.request(`/${encodeURIComponent(id)}`);
      if (!this.active() || this.queue.get(id)?.data === null) return;
      const record = body.record;
      if (!record || record.deleted) throw new Error('conversation unavailable');
      this.revisions[id] = record.revision;
      const pending = this.queue.get(id);
      const data = pending?.data ? mergeConversation(record.data,pending.data) : normalizeConversation(record.data);
      if (pending) this.queue.set(id,{data,version:++this.generation});
      this.apply(this.store._loadAll().map(c=>c.conversation_id===id ? data : c));
      this.saveMeta();
      return data;
    })();
    this.reading.set(id,task);
    try { return await task; } finally { this.reading.delete(id); }
  }
  async _flush() {
    try {
      for (const [id, pending] of [...this.queue]) {
        if (!this.closed && this.busy.has(id) && Date.now()-(this.lastPushed.get(id)||0)<20000) continue;
        const { response, body } = await this.request(`/${encodeURIComponent(id)}`, pending.data === null
          ? { method: 'DELETE' }
          : { method: 'PUT', body: JSON.stringify({ data: pending.data, expected_revision: this.revisions[id] || 0 }) });
        const record = response.status === 409 ? body.detail?.record : body.record;
        if (!record) throw new Error('invalid record');
        this.revisions[id] = record.revision;
        this.lastPushed.set(id,Date.now());
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
    if (this.closing) return this.closing;
    this.unsubscribe(); clearTimeout(this.timer);
    // Flush captured data with the captured token, never the next user's token.
    this.closed = true;
    this.closing = (async()=>{ while (this.queue.size) await this.flush(); })().catch(()=>{});
    return this.closing;
  }
}
