import test from 'node:test';
import assert from 'node:assert/strict';
import { loadUserData, saveReadingProgress, getReadingHistory, importFromFile } from '../src/data/userData.js';

test('reading progress works without chat storage and does not overwrite existing notes or legacy fields', () => {
  const previous = globalThis.localStorage;
  const data = new Map([['dp_userdata',JSON.stringify({version:1,readingHistory:[],legacyField:'untouched'})],['dp_notes_book','已有笔记']]);
  globalThis.localStorage = {getItem:key=>data.get(key) ?? null,setItem:(key,value)=>data.set(key,value)};
  try {
    saveReadingProgress('book','书名','作者',2,.4,'text');
    assert.equal(getReadingHistory()[0].page, 2);
    assert.equal(getReadingHistory()[0].percent, .4);
    assert.equal(loadUserData().legacyField, 'untouched');
    assert.equal(data.get('dp_notes_book'), '已有笔记');
    assert.equal(data.has('dp_chat_sessions'), false);
    data.clear();
    assert.deepEqual(loadUserData().readingHistory, []);
    assert.equal(Object.hasOwn(loadUserData(), 'chatHistory'), false);
  } finally { globalThis.localStorage = previous; }
});

test('reading-only exports can be imported without the retired chatHistory field', async () => {
  const oldStorage=globalThis.localStorage, oldReader=globalThis.FileReader;
  let saved;
  globalThis.localStorage={setItem:(_key,value)=>{saved=JSON.parse(value);}};
  globalThis.FileReader=class { readAsText(text) { this.onload({target:{result:text}}); } };
  try {
    await importFromFile(JSON.stringify({version:1,readingHistory:[{bookId:'book',page:3}]}));
    assert.equal(saved.readingHistory[0].page,3);
    await assert.rejects(importFromFile(JSON.stringify({version:1,readingHistory:'invalid'})));
  } finally { globalThis.localStorage=oldStorage;globalThis.FileReader=oldReader; }
});
