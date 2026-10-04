import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {mergeBook,normalizeBookToc,groupBookToc,bookReaderPath,resumedChapter,bookAuthors,relatedBooks} from '../src/data/bookDetail.js';
import {BOOK_EDITORIAL} from '../src/data/bookEditorial.js';
const catalog=JSON.parse(fs.readFileSync(new URL('../public/books.json',import.meta.url)));
const flatten=nodes=>nodes.flatMap(n=>[n,...flatten(n.children)]);
test('all book TOCs retain every source entry and its original reader anchor after nesting',()=>{
 for(const b of catalog){const d=JSON.parse(fs.readFileSync(new URL(`../public/book_detail/${b.id}.json`,import.meta.url)));const flat=normalizeBookToc(d);const tree=flatten(groupBookToc(flat));assert.deepEqual(tree.map(n=>n.tocIndex),flat.map(n=>n.tocIndex),b.title);for(const n of tree){const path=bookReaderPath(b.id,n,d.chapterCount);if(n.type==='part')assert.equal(path,null);if(path&&n.type==='section')assert.ok(path.endsWith(`&toc=${n.tocIndex}`));}}
});
test('section positions without sec and nested volumes keep precise navigation; invalid chapters never link',()=>{
 const toc=normalizeBookToc({toc:[{type:'part',title:'卷',level:0},{type:'part',title:'篇',level:1},{type:'chapter',title:'章',index:0},{type:'section',title:'节',index:0}]});const roots=groupBookToc(toc);assert.equal(roots[0].children[0].children[0].children[0].tocIndex,3);assert.equal(bookReaderPath('a',toc[3],1),'/reader/a?ch=0&toc=3');assert.equal(bookReaderPath('a',{type:'chapter',index:2},1),null);
});
test('metadata fallbacks and saved reading chapter are conservative',()=>{
 assert.equal(mergeBook('x',{title:'书',summary:'简介',tags:['伦理学'],cover:'/covers/x.webp'},{title:'书',summary:'',tags:[]}).summary,'简介');assert.equal(mergeBook('x',null,null),null);
 assert.equal(resumedChapter([{bookId:'x',page:20}],'x',3),2);assert.equal(resumedChapter([{bookId:'x',page:-2}],'x',3),null);assert.equal(resumedChapter([], 'x',3),null);
 const authors=bookAuthors('旧名/佚名',{aliases:{旧名:'新名'},people:{新名:{}}});assert.equal(authors[0].path,'/author/%E6%96%B0%E5%90%8D');assert.equal(authors[1].path,null);
});
test('editorial concepts resolve to real section anchors and recommendations never include current or missing books',()=>{
 const book=catalog.find(b=>b.id==='c5013f33fe01');const d=JSON.parse(fs.readFileSync(new URL('../public/book_detail/c5013f33fe01.json',import.meta.url)));const toc=normalizeBookToc(d);
 for(const c of BOOK_EDITORIAL[book.id].concepts)assert.ok(toc.some(t=>t.type==='section'&&t.index===c.ch&&t.sec===c.sec),c.name);
 const related=relatedBooks(book,catalog,BOOK_EDITORIAL[book.id]);assert.equal(related.length,3);assert.ok(related.every(b=>b.id!==book.id&&catalog.some(x=>x.id===b.id)));assert.equal(new Set(related.map(x=>x.id)).size,related.length);
});
