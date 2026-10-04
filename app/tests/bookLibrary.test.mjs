import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {classifyBook,prepareLibrary,filterLibrary,sortLibrary,BOOK_TOPICS,BOOK_FORMS} from '../src/data/bookLibrary.js';
const books=JSON.parse(fs.readFileSync(new URL('../public/books.json',import.meta.url)));
const catalog=prepareLibrary(books);
test('all catalog works remain reachable with valid facets and source metadata intact',()=>{
 assert.equal(filterLibrary(catalog).length,books.length);
 for(const b of catalog){assert.ok(b.facets.topics.length,b.title);assert.ok(b.facets.forms.length,b.title);assert.ok(b.facets.topics.every(t=>BOOK_TOPICS.some(f=>f.id===t)));assert.ok(b.facets.forms.every(t=>BOOK_FORMS.some(f=>f.id===t)));assert.deepEqual(b.tags,books.find(x=>x.id===b.id).tags);}
 assert.deepEqual(new Set(sortLibrary(catalog,'author').map(x=>x.id)),new Set(books.map(x=>x.id)));
});
test('geography and disciplines never imply a school; source school distinctions survive',()=>{
 const f=tags=>classifyBook({tags});
 assert.deepEqual(f(['欧陆哲学','语言哲学','德国哲学']).traditions,[]);
 assert.ok(!f(['荒诞哲学']).traditions.includes('existential'));
 assert.ok(!f(['马克思主义']).traditions.includes('western-marxist'));
 assert.ok(f(['经验论']).traditions.includes('empiricist'));
 assert.ok(!classifyBook({file_type:'txt',chapterCount:10}).readable);
 assert.ok(!classifyBook({file_type:'epub',chapterCount:0}).readable);
});
test('combined filters intersect and keyword searches retain original tags',()=>{
 const found=filterLibrary(catalog,{q:'存在',topic:'life',tradition:'phenomenology',region:'west',readable:true});
 assert.ok(found.some(x=>x.id==='c5013f33fe01'));
 assert.ok(found.every(b=>b.facets.topics.includes('life')&&b.facets.traditions.includes('phenomenology')&&b.facets.readable));
 assert.equal(filterLibrary(catalog,{q:'没有这本书987654'}).length,0);
 assert.ok(filterLibrary(catalog,{q:'无为而治'}).some(x=>x.title==='道德经'));
 assert.ok(!classifyBook({title:'哲学研究',tags:[]}).forms.includes('commentary'));
});
