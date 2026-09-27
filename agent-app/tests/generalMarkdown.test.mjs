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
  const primaryCitation = { book: '论语', book_id: 'lunyu', chapter: '学而', chapter_idx: 0, excerpt: '学而时习之，不亦说乎。', access_level: 'PASSAGE_READ', used: true };
  const linked = render('“学而时习之，不亦说乎。”【《论语》·学而】', { citations: [primaryCitation] });
  assert.equal((linked.match(/href="https:\/\/deepphilosophy.top\/reader\/lunyu\?ch=0"/g) || []).length, 2, 'quote and its citation both open the actual chapter');
  const legacy = render('[【《论语》·学而】](http://127.0.0.1:8011/cite/论语/学而)', { citations: [primaryCitation] });
  assert.ok(legacy.includes('href="https://deepphilosophy.top/reader/lunyu?ch=0"'));
  assert.ok(!legacy.includes('127.0.0.1'));
  const nestedTitle = render('正文观点。【《康德《实践理性批判》句读》·序言】', { citations: [{ book: '康德《实践理性批判》句读', chapter: '序言', book_id: 'kant-commentary', chapter_idx: 0 }] });
  assert.ok(nestedTitle.includes('href="https://deepphilosophy.top/reader/kant-commentary?ch=0"'), 'nested work names still produce inline reader links');
  const unresolvedLegacy = render('[【《未知》·未知章】](http://localhost:8011/cite/未知/未知章)');
  assert.ok(!unresolvedLegacy.includes('href='), 'unresolved saved reference never links to the user’s own computer');
  assert.ok(unresolvedLegacy.includes('【《未知》·未知章】'));
  assert.ok(!render('“一段没有读到的伪造原文。”', { citations: [primaryCitation] }).includes('general-inline-quote'));
  assert.ok(!render('“学而时习之，不亦说乎。”', { citations: [{ ...primaryCitation, access_level: 'SEARCH_EXCERPT' }] }).includes('general-inline-quote'));
  assert.ok(render('“不患人之不己知，患不知人也”', { citations: [{ ...primaryCitation, quoted_passages: ['不患人之不己知，患不知人也'] }] }).includes('general-inline-quote'), 'verified quotations outside the preview excerpt remain linked');
  const { sourceHref } = await server.ssrLoadModule('/src/utils/evidence.js');
  assert.equal(sourceHref({ book: '未知', book_id: 'missing', chapter_idx: -1 }), null, 'unknown chapter must not silently open chapter zero');
  assert.equal(sourceHref({ book: '原典', book_id: 'known', chapter_idx: 10, reader_available: false }), null, 'local readability does not prove an accessible website coordinate');
  assert.equal(sourceHref({ source_type: 'web', url: 'javascript:alert(1)' }), null);
  assert.equal(sourceHref({ book: '论语', reader_url: 'http://127.0.0.1:8011/cite/论语/学而' }), null);
  assert.equal(sourceHref({ book: '论语', reader_url: 'https://deepphilosophy.top/book/lunyu' }), 'https://deepphilosophy.top/book/lunyu');
  const { AnswerResearch, AnswerExploration } = await server.ssrLoadModule('/src/components/conversation/AnswerResearch.jsx');
  const { ReasoningTimeline } = await server.ssrLoadModule('/src/components/conversation/GeneralAnswer.jsx');
  const timeline = renderToStaticMarkup(createElement(ReasoningTimeline, { lang: 'zh', toolLabel: () => '检索原典', message: { streaming: true, events: [
    { t: 'provider_reasoning', source: 'deepseek', id: 'r1', content: '先定位原文。' },
    { t: 'thinking_summary', id: 'note1', content: '不再展示的研究旁白' },
    { t: 'tool_note', text: '不再展示的工具旁白' },
    { t: 'tool', call_id: 'a', status: 'success', tc: { name: 'search_books', args: { query: '责任' }, result_summary: '找到相关章节' } },
    { t: 'provider_reasoning', source: 'deepseek', id: 'r1', content: '再结合上下文分析。<script>' },
    { t: 'tool_start', call_id: 'b', name: 'get_chapter', status: 'running' },
  ] } }));
  assert.ok(timeline.indexOf('先定位原文。') < timeline.indexOf('general-tool-success'));
  assert.ok(timeline.indexOf('general-tool-success') < timeline.indexOf('再结合上下文分析。'));
  assert.ok(timeline.indexOf('再结合上下文分析。') < timeline.indexOf('general-tool-running'));
  assert.equal((timeline.match(/class="general-think-toggle"/g) || []).length, 2, 'each reasoning block has its own disclosure');
  assert.equal((timeline.match(/aria-expanded="false"/g) || []).length, 2, 'tool calls settle and collapse preceding reasoning');
  assert.ok(timeline.includes('进行中') && !timeline.includes('<script>'));
  assert.ok(!timeline.includes('研究旁白') && !timeline.includes('工具旁白') && !timeline.includes('研究说明'));
  const interimTimeline = renderToStaticMarkup(createElement(ReasoningTimeline, { message: {
    runtime_profile:'bare', streaming:true, events:[
      {t:'provider_reasoning',source:'deepseek',id:'one',content:'第一段思考'},
      {t:'assistant_commentary',id:'speech',content:'先给一个**初步判断**。'},
      {t:'tool',call_id:'read',status:'success',tc:{name:'get_chapter',result_summary:'原文结果'}},
      {t:'thinking_summary',id:'legacy',content:'旧裸模式保存的中间回答'},
      {t:'provider_reasoning',source:'deepseek',id:'two',content:'第二段思考'},
    ],
  } }));
  assert.ok(interimTimeline.includes('<strong>初步判断</strong>'));
  assert.ok(interimTimeline.indexOf('初步判断') < interimTimeline.indexOf('general-tool-success'));
  assert.ok(interimTimeline.indexOf('general-tool-success') < interimTimeline.indexOf('旧裸模式保存的中间回答'));
  assert.ok(interimTimeline.indexOf('旧裸模式保存的中间回答') < interimTimeline.indexOf('第二段思考'));
  assert.equal((interimTimeline.match(/general-interim-answer/g)||[]).length,2);
  assert.equal((interimTimeline.match(/aria-expanded="true"/g)||[]).length,1);
  const researchPanel = message => renderToStaticMarkup(createElement(AnswerResearch, { message, lang: 'zh', onSend() {}, onSource() {} }));
  const emptyResearch = researchPanel({});
  assert.ok(emptyResearch.includes('原典检索') && emptyResearch.includes('本轮未检索原典') && emptyResearch.includes('检索相关原典'));
  const research = researchPanel({ citations: [primaryCitation], evidence: { primary_research: { status: 'complete', total: 2, sources: [primaryCitation, { ...primaryCitation, book: '相关著作', book_id: 'other', used: false, access_level: 'SEARCH_EXCERPT' }] } } });
  assert.ok(research.includes('本回答引用') && research.includes('另有 1 处检索材料') && research.includes('阅读原典'));
  assert.ok(researchPanel({ evidence: { primary_research: { sources: [{ ...primaryCitation, used: false }] } } }).includes('相关材料 · 未引用'));
  const absentQuote = researchPanel({ evidence: { primary_research: { sources: [], status: 'no_quote_match', quote_checks: [{ book_title:'论语',quote:'算法比人更懂幸福',found:false,coverage:{searched_chapters:24,directory_consistent:true} }] } } });
  assert.ok(absentQuote.includes('未找到原句匹配') && absentQuote.includes('24 个文本单元'));
  assert.ok(!absentQuote.includes('换一个概念'));
  const exploration = renderToStaticMarkup(createElement(AnswerExploration, { message: { suggestions: [] }, lang: 'zh', onSend() {} }));
  assert.ok(exploration.includes('继续探索') && exploration.includes('检验反例') && exploration.includes('比较不同立场'));
  const unusedDrawer = source({ ...primaryCitation, used: false });
  assert.ok(unusedDrawer.includes('未被本回答引用') && !unusedDrawer.includes('本回答使用的来源'));
  console.log('8 general markdown/source delivery checks passed');
  console.log('Answer structure, primary-text links and exploration checks passed');
} finally { await server.close(); }
