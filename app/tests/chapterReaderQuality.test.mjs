import test, { after } from 'node:test';
import assert from 'node:assert/strict';
import { fileURLToPath } from 'node:url';
import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { createServer } from 'vite';

const server = await createServer({ root: fileURLToPath(new URL('../', import.meta.url)), server: { middlewareMode: true, watch: null }, optimizeDeps: { noDiscovery: true }, appType: 'custom', logLevel: 'error' });
after(() => server.close());
const { default: ChapterReader } = await server.ssrLoadModule('/src/components/ChapterReader.jsx');
function render(chapter, props = {}) {
  return renderToStaticMarkup(React.createElement(ChapterReader, { chapters: [{ index: 0, title: '测试章节', ...chapter }], currentChapter: 0, onChapterChange() {}, ...props }));
}
const plain = html => html.replace(/<[^>]*>/g, '');

test('a full-page figure links to its original pixels without reducing the image or sharing its opener', () => {
  const html = render({ content: [{ type: 'image', src: '/api/books/demo/image/source-table.png', alt: '原版统计表', w: 3330, h: 4483 }] });
  assert.match(html, /<a href="https:\/\/deepphilosophy\.oss-cn-shanghai\.aliyuncs\.com\/book_images\/source-table\.png" target="_blank" rel="noopener noreferrer" aria-label="查看原图：原版统计表"/);
  assert.ok(!html.includes('x-oss-process'));
  assert.equal((html.match(/<img\b/g) || []).length, 1);
});

test('an unavailable block image does not create an empty or unsafe original-image link', () => {
  const html = render({ content: [{ type: 'image', src: 'javascript:untrusted-image', alt: '不可用图' }, { type: 'text', value: '原文完整保留。' }] });
  assert.ok(!html.includes('查看原图'));
  assert.ok(!html.includes('javascript:'));
  assert.ok(plain(html).includes('原文完整保留。'));
});

test('a verified same-source note reference keeps its original words when note numbers change', () => {
  const html = render({ paragraphMode: 'source', content: [{ type: 'text', value: '先引这一条{{n:29}}，再引上一来源{{n:11}}。' }], notes: [
    { n: 11, text: '原书上注。' },
    { n: 29, text: '同上。', crossRefs: [{ n: 11, start: 0, end: 2 }] },
  ] });
  assert.match(html, /id="dp-note-cross-0-29-1"[^>]*aria-label="转到注释2"[^>]*>同上<\/button>。/);
  assert.ok(!/aria-label="转到注释2"[^>]*>\[2\]/.test(html));
});

test('same-source words after an astral character use the actual UTF-16 location', () => {
  const html = render({ content: [{ type: 'text', value: '原文{{n:1}}{{n:2}}。' }], notes: [
    { n: 1, text: '原版书名。' },
    { n: 2, text: '𝛂同上。', crossRefs: [{ n: 1, start: 2, end: 5 }] },
  ] });
  assert.match(html, /𝛂<button[^>]*aria-label="转到注释1"[^>]*>同上。<\/button>/);
});

test('unverified text, incomplete same-source words and a false superscript stay unchanged', () => {
  for (const [text, ref] of [
    ['不是注号。', { n: 1, start: 0, end: 4 }],
    ['同上。', { n: 1, start: 0, end: 1 }],
    ['同上。', { n: 1, start: 0, end: 2, superscript: true }],
  ]) {
    const html = render({ content: [{ type: 'text', value: '原文{{n:1}}{{n:2}}。' }], notes: [
      { n: 1, text: '原书来源。' }, { n: 2, text, crossRefs: [ref] },
    ] });
    assert.ok(plain(html).includes(text));
    assert.ok(!html.includes('dp-note-cross-0-2-1'));
  }
});

test('source subscripts and powers retain UTF-16 offsets past a note and an inline picture', () => {
  const value='𝛂klP{{n:1}}[IMG]Q2';
  const inlineStyles=[
    {start:value.indexOf('P'),end:value.indexOf('P')+1,kind:'sub'},
    {start:value.indexOf('Q'),end:value.indexOf('Q')+1,kind:'sub'},
    {start:value.indexOf('2'),end:value.indexOf('2')+1,kind:'sup'},
  ];
  const html=render({paragraphMode:'source',content:[{type:'text',value,inlineStyles,imgs:[{src:'/api/books/demo/image/formula.png',background:'white'}]}],notes:[{n:1,text:'原注。'}]});
  assert.match(html,/<sub[^>]*>P<\/sub>/);
  assert.match(html,/<sub[^>]*>Q<\/sub>/);
  assert.match(html,/<sup[^>]*>2<\/sup>/);
  assert.ok(plain(html).includes('𝛂klP[1]Q2'));
  assert.match(html,/background-color:#fff/);
  assert.equal((html.match(/id="dp-ref-0-1-1"/g)||[]).length,1);
});

for (const [kind, tag] of [['strong', 'strong'], ['em', 'em'], ['underline', 'u']]) test(`source ${kind} stays full-sized and preserves a note between ranges`, () => {
  const value = '𝛂引文{{n:1}}续引，评论。';
  const continuation = value.indexOf('续引');
  const html = render({
    paragraphMode: 'source',
    content: [{ type: 'text', value, inlineStyles: [
      { start: 2, end: 4, kind },
      { start: continuation, end: continuation + 2, kind },
    ] }],
    notes: [{ n: 1, text: '原注。' }],
  });
  assert.ok(html.includes(`𝛂<${tag}>引文</${tag}>`));
  assert.match(html, /id="dp-ref-0-1-1"/);
  assert.ok(html.includes(`<${tag}>续引</${tag}>，评论。`));
});

test('section anchors and the hidden leading section sign do not shift a source subscript', () => {
  const html=render({paragraphMode:'source',content:[{type:'text',role:'section-title',level:2,value:'§kP',inlineStyles:[{start:2,end:3,kind:'sub'}]}]}, {toc:[{type:'section',title:'kP',index:0,sec:0}]});
  assert.match(html,/<h3[^>]*>.*id="sec-0".*k<sub[^>]*>P<\/sub><\/h3>/);
  assert.ok(!plain(html).includes('§'));
});

test('source note mathematics survives a nested reference, paragraph break and picture', () => {
  const text='klP[9]\n[IMG]Q2';
  const html=render({paragraphMode:'source',content:[{type:'text',value:'原文{{n:1}}。'}],notes:[
    {n:1,text,inlineStyles:[{start:2,end:3,kind:'sub'},{start:text.indexOf('Q'),end:text.indexOf('Q')+1,kind:'sub'},{start:text.indexOf('2'),end:text.indexOf('2')+1,kind:'sup'}],crossRefs:[{n:2,start:3,end:6}],imgs:[{src:'/api/books/demo/image/formula.png',background:'white'}]},
    {n:2,text:'原版第二层注。'},
  ]});
  assert.match(html,/<sub[^>]*>P<\/sub><button[^>]*aria-label="转到注释2"/);
  assert.match(html,/<sub[^>]*>Q<\/sub><sup[^>]*>2<\/sup>/);
  assert.match(html,/background-color:#fff/);
});

test('consecutive native pictures separated only by whitespace are all retained in their paragraph', () => {
  const html=render({paragraphMode:'source',content:[{type:'text',value:'[IMG] [IMG]末',imgs:[{src:'/api/books/demo/image/a.png'},{src:'/api/books/demo/image/b.png'}]}]});
  assert.equal((html.match(/<img\b/g)||[]).length,2);
  assert.ok(html.indexOf('/a.png')<html.indexOf('/b.png'));
  assert.equal((plain(html).match(/末/g)||[]).length,1);
});

test('unrecognized source style metadata remains plain text', () => {
  const html=render({paragraphMode:'source',content:[{type:'text',value:'kP',inlineStyles:[{start:1,end:2,kind:'script'}]}]});
  assert.ok(plain(html).includes('kP'));
  assert.ok(!/<(?:sub|sup|script)\b/.test(html));
});

test('repeated references in separate source paragraphs have unique, sequential return targets', () => {
  const html = render({ paragraphMode: 'source', content: [{ type: 'text', value: '第一处引用{{n:1}}。' }, { type: 'text', value: '另一段再次引用{{n:1}}。' }], notes: [{ n: 1, text: '同一条章末注释。' }] });
  const ids = [...html.matchAll(/id="(dp-ref-[^"]+)"/g)].map(match => match[1]);
  assert.deepEqual(ids, ['dp-ref-0-1-1', 'dp-ref-0-1-2']);
  assert.equal(new Set(ids).size, ids.length);
});

test('an unavailable inline image never removes the following character', () => {
  for (const following of ['甲乙', '𝛂乙']) {
    const html = render({ paragraphMode: 'source', content: [{ type: 'text', value: `前文[IMG]${following}后文。`, imgs: [{ src: 'unavailable-original-image' }] }] });
    assert.ok(plain(html).includes(following + '后文。'), following);
  }
});

test('OCR line joining does not cut a sentence merely because it exceeds 300 characters', () => {
  const lines = ['甲'.repeat(120), '乙'.repeat(120), '丙'.repeat(120), '丁'.repeat(40) + '。'];
  const html = render({ content: [{ type: 'text', value: lines.join('\n') }] });
  assert.equal((html.match(/<p\b/g) || []).length, 1);
  assert.ok(plain(html).includes(lines.join('')));
});

test('a source chapter title with its own note is rendered once with a working reference target', () => {
  const html = render({ title: '善的程度', paragraphMode: 'source', content: [{ type: 'text', role: 'chapter-title', value: '善{{n:1}}的程度' }, { type: 'text', value: '正文。' }], notes: [{ n: 1, text: '标题中的善对应原文 goodness。' }] });
  assert.equal((html.match(/<h2\b/g) || []).length, 1);
  assert.match(html, /<h2[^>]*>善<sup[^>]*id="dp-ref-0-1-1"/);
});

test('source section hierarchy and quotations retain their distinct reading structure', () => {
  const html = render({ paragraphMode: 'source', content: [{ type: 'text', role: 'section-title', level: 2, value: '§第一节' }, { type: 'text', role: 'section-title', level: 3, value: '节内小标题' }, { type: 'text', quote: true, value: '原书引文{{n:1}}。' }], notes: [{ n: 1, text: '引文注。' }] });
  assert.match(html, /<h3[^>]*>第一节<\/h3>/);
  assert.match(html, /<h4[^>]*>节内小标题<\/h4>/);
  assert.match(html, /class="reader-quotation"/);
  assert.match(html, /id="dp-ref-0-1-1"/);
});

test('nested value-form headings retain levels below the lettered subsection', () => {
  const content = [
    {type:'text',role:'section-title',level:2,value:'3.价值形式或交换价值'},
    {type:'text',role:'section-title',level:3,value:'A.简单的、个别的或偶然的价值形式'},
    {type:'text',role:'section-title',level:4,value:'（1）价值表现的两极'},
    {type:'text',role:'section-title',level:5,value:'更深一级标题'},
  ];
  const html=render({paragraphMode:'source',content});
  assert.match(html,/<h3[^>]*>3\.价值形式或交换价值<\/h3>/);
  assert.match(html,/<h4[^>]*>A\.简单的、个别的或偶然的价值形式<\/h4>/);
  assert.match(html,/<h5[^>]*>（1）价值表现的两极<\/h5>/);
  assert.match(html,/<h6[^>]*>更深一级标题<\/h6>/);
});

test('a certified heading remains a boundary between OCR page fragments', () => {
  const html = render({ content: [{ type: 'text', value: '上一节正文的结尾' }, { type: 'text', role: 'section-title', level: 2, value: 'V.6 论超越是的东西不思' }, { type: 'text', value: '1.一物思考另一物与某物思考自身。' }] });
  assert.match(html, /<h3[^>]*>V\.6 论超越是的东西不思<\/h3>/);
  assert.ok(!html.includes('上一节正文的结尾V.6'));
  assert.ok(!html.includes('不思1.一物'));
});

test('a translator credit before the native title does not duplicate that title or remove its note', () => {
  const html = render({ title: '第一章 地下室', paragraphMode: 'source', content: [
    { type: 'text', value: '曾思艺译' },
    { type: 'text', role: 'chapter-title', value: '第一章 地下室{{n:1}}' },
    { type: 'text', value: '我是个病人……' },
  ], notes: [{ n: 1, kind: 'original', text: '原书的章题说明。' }] });
  assert.equal((html.match(/<h2\b/g) || []).length, 1);
  assert.equal((plain(html).match(/第一章 地下室/g) || []).length, 1);
  assert.ok(plain(html).indexOf('曾思艺译') < plain(html).indexOf('第一章 地下室'));
  assert.match(html, /id="dp-ref-0-1-1"/);
  assert.match(html, /id="dp-note-0-1"/);
  assert.ok(plain(html).includes('我是个病人……'));
});

test('a section mentioned in prose has one anchor at its recorded heading', () => {
  const html = render({ paragraphMode:'source', content:[{type:'text',value:'下文第一节将讨论这个问题。'},{type:'text',role:'section-title',level:2,value:'第一节'},{type:'text',value:'回顾第一节的论证。'}] }, {toc:[{type:'section',title:'第一节',index:0,sec:1,level:2}]});
  assert.equal((html.match(/id="sec-0"/g)||[]).length,1);
  assert.match(html,/<h3[^>]*><span[^>]*id="sec-0"[^>]*><\/span>第一节<\/h3>/);
});

test('a note inside a section title keeps the literal title anchor and its own reference', () => {
  for (const sec of [undefined, 1]) {
    const html=render({paragraphMode:'source',content:[{type:'text',value:'下文讨论作为意志和表象的世界。'},{type:'text',role:'section-title',level:3,value:'作为意志和表象{{n:1}}的世界'},{type:'text',value:'原节正文。'}],notes:[{n:1,text:'原书用词为Vorstellung。'}]},{toc:[{type:'section',title:'作为意志和表象的世界',index:0,sec,level:3}]});
    assert.equal((html.match(/id="sec-0"/g)||[]).length,1);
    assert.match(html,/<h4[^>]*><span[^>]*id="sec-0"[^>]*><\/span>作为意志和表象<sup[^>]*id="dp-ref-0-1-1"/);
    assert.ok(plain(html).includes('的世界'));
  }
});

test('a one-character heading never anchors an ordinary word in prose', () => {
  const html=render({paragraphMode:'source',content:[{type:'text',value:'这是一个普通句子。'},{type:'text',value:'作者另有一种看法。'}]},{toc:[{type:'section',title:'一',index:0,level:2}]});
  assert.ok(!html.includes('id="sec-0"'));
});

test('an unlocated title with an invalid block is never assigned a guessed ratio anchor', () => {
  const html=render({paragraphMode:'source',content:[{type:'text',value:'第一段内容。'},{type:'text',value:'第二段内容。'}]},{toc:[{type:'section',title:'尚未定位的真实标题',index:0,sec:90,level:2}]});
  assert.ok(!html.includes('id="sec-0"'));
});

test('an explicit note cross-reference follows its stable target after displayed numbers change', () => {
  const html=render({paragraphMode:'source',content:[{type:'text',value:'先引这条{{n:29}}，再引另一条{{n:11}}。'}],notes:[{n:11,text:'被转引的原注。'},{n:29,text:'参见[99]。',crossRefs:[{n:11,start:2,end:6}]}]});
  assert.match(html,/aria-label="转到注释2"[^>]*>\[2\]<\/button>/);
  assert.ok(!plain(html).includes('[99]'));
});

test('inline note images continue in source order across paragraph breaks', () => {
  const html=render({paragraphMode:'source',content:[{type:'text',value:'正文{{n:1}}。'}],notes:[{n:1,text:'字形[IMG]甲\n次段[IMG]乙',imgs:[{src:'/api/books/test/image/first.png'},{src:'/api/books/test/image/second.png'}]}]});
  const images=[...html.matchAll(/<img[^>]*src="([^"]+)"/g)].map(m=>m[1].split('?')[0]);
  assert.deepEqual(images,['https://deepphilosophy.oss-cn-shanghai.aliyuncs.com/book_images/first.png','https://deepphilosophy.oss-cn-shanghai.aliyuncs.com/book_images/second.png']);
});

test('source formula note images remain legible and expose their faithful transcription', () => {
  const html=render({paragraphMode:'source',content:[{type:'text',value:'正文{{n:1}}。'}],notes:[{n:1,text:'关于克卜勒[IMG]到[IMG]。',imgs:[{src:'/api/books/test/image/fraction.webp',role:'formula',alt:'s³/t²'},{src:'/api/books/test/image/glyph.webp'}]}]});
  assert.match(html,/<img[^>]*alt="s³\/t²"[^>]*height:2\.4em/);
  assert.match(html,/<img[^>]*alt=""[^>]*height:1\.1em/);
});

test('a recorder attribution and editorial collation are distinguished from original note wording', () => {
  const html=render({paragraphMode:'source',content:[{type:'text',value:'原段{{n:1}}。'}],notes:[{n:1,kind:'recorder',text:'㽦',editorialAddendum:'此署名据文渊阁本补。'}]});
  const noteStart=html.indexOf('id="dp-note-0-1"');
  assert.ok(!html.slice(0,noteStart).includes('此署名据文渊阁本补'));
  assert.ok(plain(html.slice(noteStart)).includes('记录者：㽦校：此署名据文渊阁本补。'));
  assert.equal((html.match(/class="dp-note-editorial-addendum"/g)||[]).length,1);
});

test('a source star note inside another note is superscript and keeps a unique return origin', () => {
  const html=render({paragraphMode:'source',content:[{type:'text',value:'正文{{n:17}}。'}],notes:[
    {n:17,text:'讲座[219]，续文。',crossRefs:[{n:219,start:2,end:7,superscript:true}]},
    {n:219,text:'原注内的科学院版编者注。'},
  ]});
  assert.match(html,/id="dp-note-cross-0-17-1"[^>]*vertical-align:super[^>]*aria-label="转到注释2"[^>]*>\[2\]<\/button>/);
  assert.match(html,/vertical-align:super;font-size:0.75em;line-height:1/);
  assert.match(html,/id="dp-note-0-2"/);
  assert.equal((html.match(/id="dp-note-cross-0-17-1"/g)||[]).length,1);
  assert.ok(plain(html).includes('讲座[2]，续文。'));
  assert.ok(!html.includes('dp-ref-0-2-'));
});

test('verified body fractions retain legible source height and their faithful accessible transcription',()=>{
 const html=render({paragraphMode:'source',content:[{type:'text',value:'微分之比[IMG]，再取根式[IMG]。',imgs:[
  {src:'/api/books/source/image/fraction.jpeg',role:'formula',alt:'dy/dx'},
  {src:'/api/books/source/image/root.jpeg',alt:'√(−1)'},
 ]}]});
 assert.match(html,/<img[^>]*alt="dy\/dx"[^>]*height:2\.4em/);
 assert.match(html,/<img[^>]*alt="√\(−1\)"[^>]*height:1\.1em/);
 assert.ok(plain(html).includes('，再取根式'));
 assert.ok(plain(html).includes('。'));
});

test('a directly opened note can return to a real body reference before any click', () => {
  const html = render({
    paragraphMode: 'source',
    content: [{ type: 'text', value: '正文{{n:9}}，重复引用{{n:9}}。' }],
    notes: [{ n: 5, text: '印本中待定位的注释。' }, { n: 9, text: '可回到正文的注释。' }],
  }, { initialNote: 1 });
  assert.match(html, /id="dp-ref-0-1-1"/);
  assert.match(html, /id="dp-ref-0-1-2"/);
  assert.match(html, /aria-label="返回引用位置1"/);
  assert.doesNotMatch(html, /aria-label="返回引用位置2"/);
  assert.equal((html.match(/class="dp-note-back"/g) || []).length, 1);
});
