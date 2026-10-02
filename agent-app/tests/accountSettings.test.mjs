import assert from 'node:assert/strict';
import { accountProfile, profilePatch, clearDeviceCache, deleteConversationHistory } from '../src/data/accountSettings.js';
import { LocalConversationStore } from '../src/data/conversationStore.js';
import { ConversationSync } from '../src/data/conversationSync.js';

const normalized=accountProfile({id:5,username:'reader',profile:{id:999,username:'other',nickname:'小读者',language:'en',custom_instructions:'先给结论'}});
assert.equal(normalized.id,5);assert.equal(normalized.username,'reader');
assert.equal(normalized.nickname,'小读者');assert.equal(normalized.language,'en');
assert.deepEqual(profilePatch({id:1,about:'',nickname:'A',is_admin:true}),{about:'',nickname:'A'});
const entries=new Map([['my-cache','history'],['my-sync','dirty'],['other-cache','keep'],['phiagent_theme','dark']]);
const storage={getItem:k=>entries.get(k)||null,setItem:(k,v)=>entries.set(k,v),removeItem:k=>entries.delete(k)};
const guard={active:()=>true,hydrated:true,queue:new Map([['unsaved',{}]]),busy:new Set(),metaKey:'my-sync'};
assert.throws(()=>clearDeviceCache({key:'my-cache'},guard,storage),/SYNC_PENDING/);
assert.equal(entries.get('my-cache'),'history');guard.queue.clear();
clearDeviceCache({key:'my-cache'},guard,storage);
assert.equal(entries.has('my-cache'),false);assert.equal(entries.has('my-sync'),false);
assert.equal(entries.get('other-cache'),'keep');assert.equal(entries.get('phiagent_theme'),'dark');

const cache=new Map();const st={getItem:k=>cache.get(k)||null,setItem:(k,v)=>cache.set(k,v),removeItem:k=>cache.delete(k)};
const store=new LocalConversationStore(st);store.setScope('local-user:5');
const remote=new Map();const requests=[];
const fetcher=async(path,options={})=>{
  requests.push({path,method:options.method||'GET'});
  const id=path.split('/conversations/')[1];let body;
  if(!id)body={records:[...remote.values()]};
  else if(options.method==='DELETE'){const r={conversation_id:id,revision:(remote.get(id)?.revision||0)+1,deleted:true,data:null};remote.set(id,r);body={record:r};}
  else{const d=JSON.parse(options.body);const r={conversation_id:id,revision:d.expected_revision+1,deleted:false,data:d.data};remote.set(id,r);body={record:r};}
  return{ok:true,status:200,json:async()=>structuredClone(body)};
};
const sync=new ConversationSync(store,{owner:store.owner,token:'fixture',fetcher});
await sync.hydrate();store.createConversation({conversation_id:'one'});store.createConversation({conversation_id:'two'});await sync.flush();
await deleteConversationHistory(store,sync);
assert.equal(store.listConversations().length,0);assert.equal(remote.get('one').deleted,true);assert.equal(remote.get('two').deleted,true);
assert.equal(requests.filter(r=>r.method==='DELETE').length,2);
assert.ok(requests.every(r=>r.path.startsWith('/api/agent/conversations')),'Deletes real agent records, not the unrelated legacy chat endpoint');
await sync.hydrate();assert.equal(store.listConversations().length,0,'Deleted conversations do not reappear during hydration');
sync.busy.add('active');await assert.rejects(deleteConversationHistory(store,sync),/HISTORY_BUSY/);sync.busy.clear();
await sync.close();clearTimeout(sync.timer);

const changed={active:()=>true,busy:new Set(),hydrate:async()=>{store.setScope('local-user:other')}};
await assert.rejects(deleteConversationHistory(store,changed),/ACCOUNT_CHANGED/);


const previousStorage=globalThis.localStorage;
globalThis.localStorage={getItem(){return '{}'},setItem(){throw new Error('quota')}};
const {setPref}=await import('../src/data/localPrefs.js');
assert.equal(setPref('showCitations',false),false,'Failed persistence must not report a saved preference');
globalThis.localStorage=previousStorage;

const discardedStore=new LocalConversationStore(st);discardedStore.setScope('deleted-account');
let mutationRequests=0;
const discardedSync=new ConversationSync(discardedStore,{owner:discardedStore.owner,token:'fixture',fetcher:async()=>{mutationRequests++;throw new Error('must not send deleted-account data')}});
discardedSync.hydrated=true;
discardedStore.createConversation({conversation_id:'discard-this'});
const removedMeta=discardedSync.metaKey;
await discardedSync.discard();st.removeItem(removedMeta);
discardedSync.saveMeta();await discardedSync.flush();
assert.equal(mutationRequests,0);
assert.equal(st.getItem(removedMeta),null,'Late cleanup must not restore deleted-account outbox');
console.log('Account settings: profile identity, empty-field clearing, safe cache cleanup and real conversation tombstones passed');
