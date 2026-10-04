import test from 'node:test';
import assert from 'node:assert/strict';
import {switchReadingOwner,localNotes,writeLocalNote,notePending,mergeCloudNotes,markNoteSynced,mergeReadingHistory,readingView,renameReadingOwner} from '../src/data/readingRoom.js';
function storage(values={}){const map=new Map(Object.entries(values));return{get length(){return map.size;},key:i=>[...map.keys()][i],getItem:k=>map.get(k)??null,setItem:(k,v)=>map.set(k,String(v)),removeItem:k=>map.delete(k)};}
test('switching accounts separates notes/history and restores guest and account caches',()=>{
 const s=storage({dp_username:'alice',dp_userdata:JSON.stringify({version:1,readingHistory:[{bookId:'a'}]}),dp_notes_a:'Alice note',dp_avatar:'avatar'});
 switchReadingOwner('alice',s);writeLocalNote('a','Alice draft',s);switchReadingOwner('bob',s);assert.deepEqual(localNotes(s),{});assert.deepEqual(JSON.parse(s.getItem('dp_userdata')).readingHistory,[]);assert.equal(s.getItem('dp_avatar'),null);
 writeLocalNote('b','Bob draft',s);switchReadingOwner('alice',s);assert.equal(localNotes(s).a,'Alice draft');assert.ok(notePending('a',s));assert.equal(localNotes(s).b,undefined);assert.equal(s.getItem('dp_avatar'),'avatar');
 switchReadingOwner('guest',s);assert.deepEqual(localNotes(s),{});writeLocalNote('g','guest note',s);switchReadingOwner('bob',s);assert.equal(localNotes(s).b,'Bob draft');switchReadingOwner('guest',s);assert.equal(localNotes(s).g,'guest note');
});
test('cloud sync and an old save response cannot overwrite or acknowledge a newer draft',()=>{
 const s=storage();writeLocalNote('a','new draft',s);mergeCloudNotes({a:'old cloud text',b:'other note'},s);assert.equal(localNotes(s).a,'new draft');assert.equal(localNotes(s).b,'other note');markNoteSynced('a','old draft',s);assert.ok(notePending('a',s));markNoteSynced('a','new draft',s);assert.ok(!notePending('a',s));mergeCloudNotes({a:''},s);assert.equal(localNotes(s).a,'');
 writeLocalNote('b','',s);mergeCloudNotes({b:'deleted cloud note'},s);assert.equal(localNotes(s).b,'');
});
test('reading merge uses latest timestamps and resume clamps to actual chapter count',()=>{
 const merged=mergeReadingHistory([{bookId:'a',page:3,lastReadAt:'2026-10-04T08:00:00Z'}],[{book_id:'a',progress_page:1,last_read_at:'2026-10-03 08:00:00'},{book_id:'b',progress_page:2,last_read_at:'2026-10-04T09:00:00Z'}]);assert.equal(merged[0].bookId,'b');assert.equal(merged[1].page,3);
 assert.equal(readingView({bookId:'a',page:99,percent:1.3},{chapterCount:13}).href,'/reader/a?ch=12');assert.equal(readingView({bookId:'a',page:-2,percent:-1},{chapterCount:13}).percent,0);
});
test('renaming an account preserves the active cache under its new identity',()=>{const s=storage({dp_username:'alice',dp_room_owner:'alice',dp_notes_a:'draft'});renameReadingOwner('alicia',s);switchReadingOwner('alicia',s);assert.equal(localNotes(s).a,'draft');});
