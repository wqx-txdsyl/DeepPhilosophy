import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {mergeBook,normalizeBookToc,groupBookToc,bookReaderPath,resumedChapter,bookAuthors,relatedBooks,officialReadingLinks} from '../src/data/bookDetail.js';
import {BOOK_EDITORIAL} from '../src/data/bookEditorial.js';
const catalog=JSON.parse(fs.readFileSync(new URL('../public/books.json',import.meta.url)));
const flatten=nodes=>nodes.flatMap(n=>[n,...flatten(n.children)]);
test('new edition links require an exact trusted HTTPS host without embedded credentials',()=>{
 const urls=['https://ebook.dswxyjy.org.cn/detail/67','https://www.theorychina.org.cn/ztjj/','https://www.sanmin.com.tw/product/index/012901236','http://www.sanmin.com.tw/product/1','https://www.sanmin.com.tw.evil.example/','https://user:pass@ebook.dswxyjy.org.cn/detail/67','javascript:alert(1)'];
 const links=officialReadingLinks({readingLinks:urls.map(url=>({label:'版本入口',url}))});
 assert.deepEqual(links.map(x=>x.url),urls.slice(0,3));
});
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
test('Hu Shi chapter headings contain their own sections without changing reading-file addresses',()=>{
 const book=JSON.parse(fs.readFileSync(new URL('../public/book_detail/ef077e01b6ee.json',import.meta.url)));
 const tree=groupBookToc(normalizeBookToc(book));
 assert.equal(book.chapterCount,15);
 const ending=tree.find(n=>n.title==='第十二篇 古代哲学的终局');
 assert.deepEqual(ending.children.map(n=>n.title),['第一章 西历前三世纪之思潮','第二章 所谓法家','第三章 古代哲学之中绝']);
 const legal=ending.children[1];
 assert.deepEqual(legal.children.map(n=>n.title),['一、论“法家”之名','二、所谓“法家”的人物及其书','三、法','四、“法”的哲学','五、韩非']);
 assert.equal(legal.index,14);assert.equal(bookReaderPath(book.id,legal,book.chapterCount),`/reader/${book.id}?ch=14&toc=${legal.tocIndex}`);
 for(const node of flatten(tree).filter(n=>n.type==='section')){
  const ch=JSON.parse(fs.readFileSync(new URL(`../../backend/data/book_chapters/${book.id}/${node.index}.json`,import.meta.url)));
  assert.equal(ch.content[node.sec]?.value?.replace(/^§/,'').trim(),node.title,node.title);
 }
 for(const title of ['第二章 孟子','第二章 天与性','第三章 心理学与名学'])assert.equal(flatten(tree).filter(n=>n.title===title).length,1,title);
});
test('Kumarajiva Vimalakirti keeps its fourteen chapters under three original volumes',()=>{
 const book=JSON.parse(fs.readFileSync(new URL('../public/book_detail/27d12f8ac6bd.json',import.meta.url)));
 const roots=groupBookToc(normalizeBookToc(book));
 assert.equal(book.chapterCount,15);assert.equal(roots[0].title,'版本与来源说明');
 assert.deepEqual(roots.slice(1).map(n=>[n.title,n.children.length]),[['卷上',4],['卷中',5],['卷下',5]]);
 assert.deepEqual(roots.slice(1).flatMap(n=>n.children.map(c=>c.index)),Array.from({length:14},(_,i)=>i+1));
 assert.equal(roots[3].children.at(-1).title,'囑累品第十四');
});
