const NOTE = 'dp_notes_', PENDING = 'dp_note_pending_', SNAPSHOT = 'dp_room_v1_';
const parse = (storage,key,fallback) => { try { return JSON.parse(storage.getItem(key) || 'null') ?? fallback; } catch { return fallback; } };
const keys = storage => Array.from({length:storage.length},(_,i)=>storage.key(i)).filter(Boolean);
export function localNotes(storage=localStorage){return Object.fromEntries(keys(storage).filter(k=>k.startsWith(NOTE)).map(k=>[k.slice(NOTE.length),storage.getItem(k)||'']));}
export function switchReadingOwner(name,storage=localStorage){
  const next=name ? `account:${name}` : 'guest';
  const storedOwner=storage.getItem('dp_room_owner');
  const previous=storedOwner ? (storedOwner.startsWith('account:') || storedOwner==='guest' ? storedOwner : `account:${storedOwner}`) : storage.getItem('dp_username') ? `account:${storage.getItem('dp_username')}` : 'guest';
  if(previous!==next){
    const data=parse(storage,'dp_userdata',{});
    const current={history:data.readingHistory||[],notes:localNotes(storage),pending:Object.fromEntries(keys(storage).filter(k=>k.startsWith(PENDING)).map(k=>[k,storage.getItem(k)])),avatar:storage.getItem('dp_avatar')||''};
    storage.setItem(SNAPSHOT+encodeURIComponent(previous),JSON.stringify(current));
    const legacy=name && name!=='guest' ? parse(storage,SNAPSHOT+encodeURIComponent(name),null) : null;
    const target=parse(storage,SNAPSHOT+encodeURIComponent(next),legacy||{history:[],notes:{},pending:{},avatar:''});
    storage.setItem('dp_userdata',JSON.stringify({...data,readingHistory:target.history||[]}));
    keys(storage).filter(k=>k.startsWith(NOTE)||k.startsWith(PENDING)).forEach(k=>storage.removeItem(k));
    Object.entries(target.notes||{}).forEach(([id,text])=>storage.setItem(NOTE+id,text));
    Object.entries(target.pending||{}).forEach(([key,value])=>storage.setItem(key,value));
    if(target.avatar)storage.setItem('dp_avatar',target.avatar);else storage.removeItem('dp_avatar');
  }
  storage.setItem('dp_room_owner',next);
}
export function renameReadingOwner(name,storage=localStorage){storage.setItem('dp_room_owner',`account:${name}`);}
export function writeLocalNote(id,text,storage=localStorage){storage.setItem(PENDING+id,'1');storage.setItem(NOTE+id,text);}
export function notePending(id,storage=localStorage){return storage.getItem(PENDING+id)==='1';}
export function markNoteSynced(id,text,storage=localStorage){if(storage.getItem(NOTE+id)===text)storage.removeItem(PENDING+id);}
export function mergeCloudNotes(notes,storage=localStorage){
  for(const [id,text] of Object.entries(notes||{}))if(!notePending(id,storage)&&typeof text==='string')storage.setItem(NOTE+id,text);
  return localNotes(storage);
}
const stamp=value=>{const s=String(value||'');return Date.parse(/^\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}$/.test(s)?s.replace(' ','T')+'Z':s)||0;};
export function mergeReadingHistory(local=[],cloud=[]){
  const normalized=cloud.map(h=>({bookId:h.book_id||h.bookId,bookTitle:h.book_title||h.bookTitle||'',bookAuthor:h.book_author||h.bookAuthor||'',page:h.progress_page??h.page??0,percent:h.progress_percent??h.percent??0,fileType:h.file_type||h.fileType||'',lastReadAt:h.last_read_at||h.lastReadAt||''}));
  const map=new Map();
  for(const h of [...normalized,...local])if(h.bookId&&(!map.has(h.bookId)||stamp(h.lastReadAt)>=stamp(map.get(h.bookId).lastReadAt)))map.set(h.bookId,h);
  return [...map.values()].sort((a,b)=>stamp(b.lastReadAt)-stamp(a.lastReadAt)).slice(0,100);
}
export function readingView(entry,book){
  const total=Number(book?.chapterCount)||0;const page=Math.max(1,Math.floor(Number(entry?.page)||1));
  const chapter=total?Math.min(total,page)-1:page-1;
  const raw=Number(entry?.percent)||0;const percent=Math.round(Math.min(1,Math.max(0,raw))*100);
  return {chapter,total,percent,href:`/reader/${encodeURIComponent(entry.bookId)}?ch=${chapter}`};
}
