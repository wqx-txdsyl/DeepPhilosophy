import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {mergeBook,normalizeBookToc,groupBookToc,bookReaderPath,bookTocReadingNode,resumedChapter,bookAuthors,relatedBooks,officialReadingLinks} from '../src/data/bookDetail.js';
import {BOOK_EDITORIAL} from '../src/data/bookEditorial.js';
const catalog=JSON.parse(fs.readFileSync(new URL('../public/books.json',import.meta.url)));
const flatten=nodes=>nodes.flatMap(n=>[n,...flatten(n.children)]);
test('a one-chapter part with the same title keeps one disclosure and all real section destinations',()=>{
 const book=JSON.parse(fs.readFileSync(new URL('../public/book_detail/9dd09c22b4c0.json',import.meta.url)));
 const tree=groupBookToc(normalizeBookToc(book));
 const part=tree.find(n=>n.title==='第二部分 今日之神话（长文）');
 const reading=bookTocReadingNode(part);
 assert.equal(reading.type,'chapter');assert.equal(reading.index,45);
 assert.equal(bookReaderPath(book.bookId,reading,book.chapterCount),'/reader/9dd09c22b4c0?ch=45');
 assert.equal(reading.children.length,11);
 for(const section of reading.children)assert.ok(bookReaderPath(book.bookId,section,book.chapterCount).endsWith(`&toc=${section.tocIndex}`));
 const first=tree.find(n=>n.title==='第一部分 神话学（情景条目41篇）');
 assert.equal(bookTocReadingNode(first),first);
 const different={type:'part',title:'卷',index:0,children:[{type:'chapter',title:'引论',index:0,children:[]}]};
 assert.equal(bookTocReadingNode(different),different);
 assert.deepEqual(flatten(tree).map(n=>n.tocIndex),normalizeBookToc(book).map(n=>n.tocIndex));
});
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
test('Kant volumes own their real chapters and restored related-essay prose stays out of endnotes',()=>{
 const book=JSON.parse(fs.readFileSync(new URL('../public/book_detail/390398aff8d0.json',import.meta.url)));
 const roots=groupBookToc(normalizeBookToc(book));
 assert.equal(roots.length,10);
 assert.ok(roots.every(n=>n.type==='part'&&n.children.some(c=>c.type==='chapter'&&c.title.replace(/\s/g,'')==='前言')));
 const chapters=flatten(roots).filter(n=>n.type==='chapter');
 assert.equal(new Set(chapters.map(n=>n.index)).size,book.chapterCount);
 assert.equal(chapters.length,book.chapterCount);
 for(const node of chapters){
  const ch=JSON.parse(fs.readFileSync(new URL(`../../backend/data/book_chapters/${book.bookId}/${node.index}.json`,import.meta.url)));
  assert.equal(node.title,ch.title,`${node.index}: wrong chapter destination`);
  assert.equal(ch.paragraphMode,'source',`${node.index}: native EPUB paragraphs must not be joined as OCR pages`);
 }
 const politics=roots.find(n=>n.title.includes('政治哲学'));
 const politicalTitles=flatten(politics.children).filter(n=>n.type==='chapter').map(n=>n.title);
 const enlightenment='回答这个问题：什么是启蒙？';
 assert.ok(politicalTitles.includes(enlightenment));
 assert.ok(politicalTitles.indexOf(enlightenment)<politicalTitles.indexOf('论书籍翻印的不合法性'));
 const moral=roots.find(n=>n.title.includes('道德哲学'));
 assert.ok(moral.children.some(n=>n.type==='chapter'&&n.title==='纯然理性界限内的宗教'));
 const related=moral.children.find(n=>n.type==='chapter'&&n.title==='相关论述');
 const ch=JSON.parse(fs.readFileSync(new URL(`../../backend/data/book_chapters/${book.bookId}/${related.index}.json`,import.meta.url)));
 assert.ok(ch.content.some(b=>(b.value||'').startsWith('人们要求有一部人的历史')));
 assert.ok(!ch.notes.some(n=>n.text.startsWith('人们要求有一部人的历史')));
 const essay=related.children.find(n=>n.title==='重新提出的问题：人类是否在不断地向着更善进步？');
 assert.equal(essay.children.length,11);
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

test('Western9 summaries open before their prose, not at a repeated closing title',()=>{
 const book=JSON.parse(fs.readFileSync(new URL('../public/book_detail/4a4a200536bd.json',import.meta.url)));
 const normalized=s=>String(s||'').replace(/\s/g,'');
 const summaries=book.toc.filter(x=>x.type==='section'&&normalized(x.title)==='总结');
 assert.equal(summaries.length,20);
 for(const item of summaries){
  const chapter=JSON.parse(fs.readFileSync(new URL(`../../backend/data/book_chapters/4a4a200536bd/${item.index}.json`,import.meta.url)));
  assert.equal(chapter.content.filter(b=>normalized(b.value)==='总结').length,1,chapter.title);
  assert.equal(chapter.content[item.sec].role,'section-title');
  assert.ok(chapter.content[item.sec+1]?.value?.length>50,chapter.title);
  assert.notEqual(chapter.content[item.sec+1]?.role,'section-title');
  const questions=book.toc.find(x=>x.index===item.index&&x.title==='研究问题');
  assert.ok(questions.sec>item.sec+1,chapter.title);
  assert.equal(questions.level,item.level);
 }
});
