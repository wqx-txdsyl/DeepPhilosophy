import assert from 'node:assert/strict';
import { createServer } from 'vite';
import { renderToStaticMarkup } from 'react-dom/server';
import { createElement } from 'react';

// Exercise the actual JSX renderer through Vite, rather than asserting source-code strings.
const server = await createServer({ server: { middlewareMode: true }, appType: 'custom' });
try {
  const { renderMarkdown } = await server.ssrLoadModule('/src/components/conversation/markdown.jsx');
  const options = { general: true, streaming: true, citations: [{ book: '论语', chapter: '学而' }], onCitation() {} };
  const render = (text, extra = {}) => renderToStaticMarkup(renderMarkdown(text, null, null, null, { ...options, ...extra }));
  const references = render('【《论语》·学而】 [1] 【普通强调】 [99] 【《虚构书》·不存在】');
  assert.equal((references.match(/class="general-inline-cite"/g) || []).length, 2);
  assert.ok(references.includes('【普通强调】')); assert.ok(!references.includes('cw-cite-inline'));
  const pending = render('```mermaid\ngraph TD\nA-->');
  assert.ok(pending.includes('<pre')); assert.ok(!pending.includes('class="mermaid"'));
  const complete = render('```mermaid\ngraph TD\nA-->B\n```');
  assert.ok(complete.includes('class="mermaid"'));
  const list = render('1. 第一步\n2. 第二步\n- [x] 已完成');
  assert.ok(list.includes('1. 第一步')); assert.ok(list.includes('2. 第二步')); assert.ok(list.includes('<svg'));
  assert.ok(!list.includes('☑'));
  const unsafe = render('[危险链接](javascript:alert)\n<script>alert(1)</script>');
  assert.ok(!unsafe.includes('href="javascript:')); assert.ok(!unsafe.includes('<script>'));
  const table = '| 观点 | 来源 |\n| --- | --- |\n| 仁 | [1] |';
  const first = renderMarkdown(table, null, null, null, options);
  const second = renderMarkdown(table + '\n| 礼 | [1] |', null, null, null, options);
  assert.equal(first[0].key, second[0].key, 'streaming table keeps its DOM identity');
  assert.ok(renderToStaticMarkup(second).includes('general-inline-cite'));
  const { SourceDrawer } = await server.ssrLoadModule('/src/components/conversation/O9.jsx');
  const source = (citation, general = true) => renderToStaticMarkup(createElement(SourceDrawer, { open: true, citation, lang: 'zh', onClose() {}, general }));
  const passage = '原文片段'.repeat(130) + '片段结尾';
  const primary = source({ book: '论语', chapter: '学而', book_id: 'book-test', excerpt: passage, access_level: 'PASSAGE_READ' });
  assert.ok(primary.includes('已读取原文片段')); assert.ok(primary.includes('来源片段')); assert.ok(primary.includes('片段结尾'), 'excerpt is not silently cut off');
  assert.ok(source({ book: '论语', excerpt: '命中片段', access_level: 'SEARCH_EXCERPT' }).includes('仅检索片段'));
  assert.ok(!source({ book: '论语', excerpt: passage, access_level: 'PASSAGE_READ' }, false).includes('读取范围'), 'legacy agent drawer is unchanged');
  const scholarship = source({ source_type: 'scholarly', book: '论文题名', title: '论文题名', doi: '10.1234/example', excerpt: '这是摘要所陈述的观点。', access_level: 'ABSTRACT_AVAILABLE' });
  assert.ok(scholarship.includes('学术')); assert.ok(scholarship.includes('摘要片段')); assert.ok(scholarship.includes('https://doi.org/10.1234/example'));
  assert.ok(!scholarship.includes('已核验：')); assert.ok(!scholarship.includes('已读全文'));
  assert.ok(source({ source_type: 'scholarly', title: '论文', excerpt: '正文节选', access_level: 'FULL_TEXT_READ' }).includes('已读取正文片段'));
  assert.ok(source({ source_type: 'web', title: '网页', url: 'https://example.org', access_level: 'WEB_DISCOVERY_ONLY' }).includes('仅定位网页，未读取正文'));
  const webRead = source({ source_type: 'web', title: '网页', url: 'https://example.org', excerpt: '实际读到的正文', access_level: 'WEB_PASSAGE_READ' });
  assert.ok(webRead.includes('已读取网页正文片段') && webRead.includes('实际读到的正文'));
  assert.ok(!webRead.includes('已读全文'));
  console.log('8 general markdown/source delivery checks passed');
} finally { await server.close(); }
