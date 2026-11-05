import test, { after } from 'node:test';
import assert from 'node:assert/strict';
import { fileURLToPath } from 'node:url';
import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { createServer } from 'vite';

const server = await createServer({ root: fileURLToPath(new URL('../', import.meta.url)), server: { middlewareMode: true, watch: null }, optimizeDeps: { noDiscovery: true }, appType: 'custom', logLevel: 'error' });
after(() => server.close());
const { default: ChapterReader } = await server.ssrLoadModule('/src/components/ChapterReader.jsx');
function render(chapter) {
  return renderToStaticMarkup(React.createElement(ChapterReader, { chapters: [{ index: 0, title: '测试章节', ...chapter }], currentChapter: 0, onChapterChange() {} }));
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
