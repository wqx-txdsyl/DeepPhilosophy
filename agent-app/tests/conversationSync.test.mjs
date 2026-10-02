import assert from 'node:assert/strict';
import { LocalConversationStore } from '../src/data/conversationStore.js';
import { ConversationSync } from '../src/data/conversationSync.js';
function storage() {
  const map = new Map();
  return { getItem:k=>map.get(k)||null, setItem:(k,v)=>map.set(k,v), removeItem:k=>map.delete(k), key:i=>[...map.keys()][i], get length(){return map.size;} };
}
function server() {
  const owners = new Map(); let online = true;
  const fetcher = async (path, options={}) => {
    if (!online) throw new Error('offline');
    const owner = options.headers.Authorization;
    if (!owners.has(owner)) owners.set(owner, new Map());
    const rows = owners.get(owner), id = decodeURIComponent(path.split('/conversations/')[1] || '');
    const old = rows.get(id), body = options.body ? JSON.parse(options.body) : null;
    let status = 200, payload;
    if (!id) payload = { records:[...rows.values()] };
    else if (options.method === 'DELETE') {
      const row = {conversation_id:id, revision:(old?.revision||0)+1, deleted:true, data:null};
      rows.set(id,row); payload={record:row};
    } else if (old?.deleted || (old?.revision||0) !== body.expected_revision) {
      status=409; payload={detail:{record:old}};
    } else {
      const row={conversation_id:id,revision:(old?.revision||0)+1,deleted:false,data:structuredClone(body.data)};
      rows.set(id,row); payload={record:row};
    }
    return {ok:status===200,status,json:async()=>structuredClone(payload)};
  };
  return { fetcher, owners, offline:()=>online=false, online:()=>online=true };
}
function session(store, remote, owner='a') {
  store.setScope(owner);
  return new ConversationSync(store,{owner,token:owner,fetcher:remote.fetcher});
}
async function flushAll(s) { await s.flush(); if (s.queue.size) await s.flush(); clearTimeout(s.timer); }
const remote=server(); const cacheA=storage(); const storeA=new LocalConversationStore(cacheA);
let a=session(storeA,remote); await a.hydrate();
storeA.createConversation({conversation_id:'original',title:'原有问题'});
storeA.appendMessage('original',{message_id:'one',role:'user',content:'因果的必然性从何而来？'});
await flushAll(a); assert.equal(remote.owners.get('Bearer a').get('original').data.messages.length,1);
a.close();
a=session(storeA,remote); await a.hydrate();
const storeB=new LocalConversationStore(storage()); const b=session(storeB,remote); await b.hydrate();
assert.equal(storeB.getConversation('original').messages[0].content,'因果的必然性从何而来？');
storeA.appendMessage('original',{message_id:'two',role:'user',content:'康德的回应？'});
storeB.appendMessage('original',{message_id:'three',role:'user',content:'休谟的回应？'});
await flushAll(a); await flushAll(b);
assert.deepEqual(new Set(remote.owners.get('Bearer a').get('original').data.messages.map(m=>m.message_id)),new Set(['one','two','three']));
storeB.deleteConversation('original'); await flushAll(b);
storeA.appendMessage('original',{message_id:'late',role:'user',content:'旧缓存'}); await flushAll(a);
assert.equal(storeA.listConversations().length,0);
assert.equal(remote.owners.get('Bearer a').get('original').deleted,true);
storeB.createConversation({conversation_id:'survives'}); await flushAll(b);
const empty=new LocalConversationStore(storage()); const c=session(empty,remote); await c.hydrate();
assert.equal(empty.listConversations().length,1);
const different=new LocalConversationStore(storage()); const d=session(different,remote,'other'); await d.hydrate();
assert.deepEqual(different.listConversations(),[]);
remote.offline(); storeB.createConversation({conversation_id:'offline'});
await b.flush().catch(()=>{}); b.close();
remote.online(); const restored=session(storeB,remote); await restored.hydrate(); await flushAll(restored);
assert.ok(remote.owners.get('Bearer a').get('offline'));
const before=storeB.listConversations().length;
storeB.setScope('guest'); assert.equal(storeB.listConversations().length,0);
storeB.setScope('a'); assert.equal(storeB.listConversations().length,before);
let release;
const delayed=new LocalConversationStore(storage()); delayed.setScope('a');
const stale=new ConversationSync(delayed,{owner:'a',token:'a',fetcher:async()=>new Promise(r=>release=r)});
const pull=stale.hydrate(); stale.close(); delayed.setScope('other');
release({ok:true,status:200,json:async()=>({records:[{conversation_id:'private',revision:1,data:{conversation_id:'private',messages:[]}}]})});
await pull; assert.deepEqual(delayed.listConversations(),[]);
const bad=storage(); const quotaStore=new LocalConversationStore(bad); const q=session(quotaStore,remote,'quota'); await q.hydrate();
bad.setItem=()=>{throw new Error('quota')};
quotaStore.createConversation({conversation_id:'quota-kept'}); await flushAll(q);
assert.ok(remote.owners.get('Bearer quota').get('quota-kept'));
assert.equal(quotaStore.listConversations().length,1);
for(const s of [a,b,c,d,restored,q]) s.close();
console.log('Account sync: relogin, second browser, conflicts, deletions, isolation, offline recovery, quota and stale responses passed');
// Browser native fetch cannot be called as a ConversationSync instance method.
const nativeFetch = globalThis.fetch;
let defaultSession;
try {
  globalThis.fetch = async function(...args) {
    assert.notEqual(this, defaultSession, 'native fetch has an illegal receiver');
    return {ok:true,status:200,json:async()=>({records:[]})};
  };
  const nativeStore = new LocalConversationStore(storage()); nativeStore.setScope('native');
  defaultSession = new ConversationSync(nativeStore,{owner:'native',token:'native'});
  await defaultSession.hydrate(); assert.equal(defaultSession.hydrated,true);
} finally { defaultSession?.close(); globalThis.fetch = nativeFetch; }
console.log('Browser native fetch receiver regression passed');
