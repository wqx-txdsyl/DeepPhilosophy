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

test('a certified heading remains a boundary between OCR page fragments', () => {
  const html = render({ content: [{ type: 'text', value: '上一节正文的结尾' }, { type: 'text', role: 'section-title', level: 2, value: 'V.6 论超越是的东西不思' }, { type: 'text', value: '1.一物思考另一物与某物思考自身。' }] });
  assert.match(html, /<h3[^>]*>V\.6 论超越是的东西不思<\/h3>/);
  assert.ok(!html.includes('上一节正文的结尾V.6'));
  assert.ok(!html.includes('不思1.一物'));
});

test('a section mentioned in prose has one anchor at its recorded heading', () => {
  const html = render({ paragraphMode:'source', content:[{type:'text',value:'下文第一节将讨论这个问题。'},{type:'text',role:'section-title',level:2,value:'第一节'},{type:'text',value:'回顾第一节的论证。'}] }, {toc:[{type:'section',title:'第一节',index:0,sec:1,level:2}]});
  assert.equal((html.match(/id="sec-0"/g)||[]).length,1);
  assert.match(html,/<h3[^>]*><span[^>]*id="sec-0"[^>]*><\/span>第一节<\/h3>/);
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
