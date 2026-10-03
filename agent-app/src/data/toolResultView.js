// Presentation only: preserve the received return for inspection; never rewrite
// tool evidence, execution status, or the model's context.
const text = value => typeof value === 'string' ? value : '';
const list = value => Array.isArray(value) ? value : [];
const excerpt = (value, limit = 280) => {
  const s = text(value).trim();
  return s.length > limit ? `${s.slice(0, limit)}…` : s;
};
export function safeResultUrl(value) {
  try { const u = new URL(value); return ['http:', 'https:'].includes(u.protocol) && !u.username && !u.password ? u.href : null; }
  catch { return null; }
}

export function toolResultView(name, raw, zh = true) {
  const say = (cn, en) => zh ? cn : en;
  let data = raw;
  let parsed = typeof raw !== 'string';
  if (typeof raw === 'string') {
    try { data = JSON.parse(raw); parsed = true; } catch { /* Legacy or truncated return. */ }
  }
  const rawText = parsed ? JSON.stringify(data, null, 2) ?? '' : text(raw);
  const view = { headline: '', meta: [], note: '', items: [], rawText, structured: parsed, warnings: [] };
  if (!parsed || data === null || typeof data !== 'object') {
    const looksStructured = !parsed && /^[\s]*[\[{]/.test(rawText);
    view.headline = looksStructured ? say('这条历史返回未能完整解析', 'This stored return could not be parsed') : excerpt(parsed ? String(data ?? '') : rawText, 320);
    view.note = looksStructured ? say('可展开查看保留下来的原始内容。', 'Expand the retained raw content below.') : '';
    return view;
  }
  const count = n => Number(n).toLocaleString(zh ? 'zh-CN' : 'en-US');
  const number = n => Number.isInteger(n) && n >= 0;
  const item = r => {
    if (!r || typeof r !== 'object') return { title: excerpt(String(r ?? '')) };
    const url = safeResultUrl(r.url || r.source_url || r.reader_url);
    const author = text(r.author) || list(r.authors).map(a => typeof a === 'string' ? a : text(a?.name)).filter(Boolean).join(', ');
    const meta = [author, text(r.chapter || r.chapter_title), url ? new URL(url).hostname.replace(/^www\./, '') : ''].filter(Boolean);
    return { title: text(r.book_title || r.book || r.title || r.name) || say('相关资料', 'Related source'),
      meta: [...new Set(meta)].join(' · '), url,
      excerpt: excerpt(r.snippet || r.excerpt || r.text || r.matched_text || r.abstract?.text),
      catalogue: r.evidence_scope === 'catalogue' || r.match_type === 'book_metadata' };
  };
  const errors = { RATE_LIMITED: ['来源暂时限流', 'Source rate-limited'], PROVIDER_RATE_LIMIT: ['来源暂时限流', 'Source rate-limited'],
    AUTHENTICATION_REQUIRED: ['来源需要授权', 'Source authentication required'], ACCESS_DENIED: ['来源拒绝访问', 'Source denied access'],
    UNSUPPORTED_WEB_FORMAT: ['当前阅读器不支持该格式', 'Unsupported document format'],
    NO_READABLE_WEB_TEXT: ['页面没有返回可读正文', 'No readable page text returned'],
    WEB_HTTP_ERROR: ['网页访问失败', 'Webpage request failed'], AMBIGUOUS_BOOK: ['书目尚未明确', 'Book identity is ambiguous'] };
  const errorText = code => errors[code]?.[zh ? 0 : 1] || say('来源请求未成功', 'Source request did not succeed');
  if (data.status === 'blocked' || data.blocked) {
    view.headline = say('本次未执行', 'Not executed');
    view.note = text(data.message || data.reason || data.note);
  } else if (data.error || data.status === 'error' || data.accepted === false) {
    view.headline = errors[data.error]?.[zh ? 0 : 1] || say('工具执行未成功', 'Tool execution did not succeed');
    view.items = list(data.results).map(item);
    view.note = text(data.message) || (view.items.length
      ? say('仍有部分记录返回；完整情况可展开核查。', 'Some records were returned; expand the raw return to inspect the full outcome.')
      : say('尚未取得可用结果；这不代表相关资料不存在。', 'No usable result was obtained; this does not establish that the material is absent.'));
  }
  for (const failure of list(data.provider_errors)) {
    const label = [text(failure.provider), errorText(failure.error)].filter(Boolean).join(' · ');
    if (!view.warnings.includes(label)) view.warnings.push(label);
  }
  if (data.cached) view.meta.push(say('使用已有缓存', 'Cached result'));
  if (data.offline_mode) view.meta.push(say('外部来源不可用，返回本地记录', 'External sources unavailable; local records returned'));
  if (view.headline) return view;

  if (name === 'verify_quote') {
    view.headline = data.found === true ? say('找到原句匹配', 'Quotation match found')
      : data.found === false ? say('本次未找到原句匹配', 'No quotation match in this check') : say('核验状态尚不明确', 'Verification status is unclear');
    if (data.book_title) view.meta.push(data.book_title);
    if (number(data.coverage?.searched_chapters)) view.meta.push(say(`核验 ${count(data.coverage.searched_chapters)} 个本库文本单元`, `${count(data.coverage.searched_chapters)} local text units checked`));
    view.items = list(data.matches).map(item);
    view.note = data.found === false ? say('结论只限本次版本与检索范围，不能推及所有版本。', 'This result applies only to the checked edition and search scope.') : '';
    if (data.coverage?.directory_consistent === false) view.warnings.push(say('本库目录范围不完整', 'Local coverage is incomplete'));
  } else if (name === 'search_primary_texts') {
    view.items = [...list(data.results), ...list(data.sources)].map(item);
    view.headline = say(`找到 ${view.items.length} 条原典线索`, `${view.items.length} primary-text leads found`);
    view.meta.push(say(`${list(data.books).length} 本本地书目`, `${list(data.books).length} local catalogue entries`));
    view.note = text(data.note);
  } else if (name === 'read_primary_text') {
    view.items = [{ title: text(data.book_title || data.title), url: safeResultUrl(data.url),
      meta: text(data.chapter_title), excerpt: excerpt(data.text, 1000) }];
    view.headline = say('已读取原典候选片段', 'Source passage read');
    view.note = text(data.note) || say('已读取片段；不代表读过整本书。', 'A passage was read, not the complete book.');
  } else if (name === 'search_books') {
    const hits = list(data.results);
    const catalogue = list(data.catalogue_matches);
    view.items = (hits.length ? hits : catalogue).map(item);
    const metadataOnly = hits.length ? view.items.every(r => r.catalogue) : catalogue.length > 0;
    view.headline = metadataOnly ? say(`返回 ${count(view.items.length)} 条书目线索`, `${count(view.items.length)} catalogue leads returned`)
      : hits.length ? say(`返回 ${count(hits.length)} 条检索线索`, `${count(hits.length)} search leads returned`)
        : say('本次未检索到足够相关的原文片段', 'No sufficiently relevant passage was found');
    const coverage = data.search_coverage || {};
    if (number(coverage.indexed_books)) view.meta.push(say(`索引覆盖 ${count(coverage.indexed_books)} 本书`, `Index covers ${count(coverage.indexed_books)} books`));
    if (number(coverage.indexed_chapter_entries)) view.meta.push(say(`${count(coverage.indexed_chapter_entries)} 个章节条目`, `${count(coverage.indexed_chapter_entries)} chapter entries`));
    view.note = metadataOnly ? say('已找到书目，尚未取得对应的原文片段。', 'Catalogue entries found; corresponding passages have not been obtained.')
      : !hits.length ? say('这不代表本库一定没有相关内容；可换用原句、作者或书名继续检索。', 'This does not establish absence from the library. Try an exact phrase, author or title.') : say('下列为检索片段，不代表已阅读全文。', 'These are search excerpts, not a full-text read.');
  } else if (name === 'search_scholarship') {
    view.items = list(data.results).map(item);
    view.headline = view.items.length ? say(`返回 ${count(view.items.length)} 条文献记录`, `${count(view.items.length)} scholarly records returned`) : say('本次未取得可用文献记录', 'No usable scholarly records returned');
    if (number(data.READABLE_RESULT_COUNT)) view.meta.push(say(`${count(data.READABLE_RESULT_COUNT)} 条标记为可读`, `${count(data.READABLE_RESULT_COUNT)} marked readable`));
    view.note = say('书目命中不等于已读论文；需继续读取摘要或正文。', 'A bibliographic hit is not a paper read; retrieve the abstract or text next.');
  } else if (name === 'get_chapter' || (name === 'websearch' && data.mode === 'read') || name === 'get_scholarly_source') {
    const abstract = data.abstract?.text;
    const passages = list(data.evidence_passages);
    const body = text(data.text) || text(abstract) || passages.map(r => text(r.text)).join('\n\n');
    view.headline = abstract ? say('已取得摘要片段', 'Abstract excerpt obtained')
      : body ? say('已取得正文片段', 'Text passage obtained') : say('本次未取得可展示的正文', 'No readable text returned');
    if (data.title || data.book_title || data.bibliographic_record?.title) view.meta.push(data.title || data.book_title || data.bibliographic_record.title);
    if (body) view.items = [{ title: '', excerpt: excerpt(body, 650) }];
    if (data.has_more) view.note = say('后面还有内容；本次返回并非全文。', 'More content follows; this return is not the complete text.');
    if (data.historical_evidence_level) view.warnings.push(say('这是此前取得的内容，本次未重新读取网页。', 'Previously obtained content; the page was not fetched again.'));
  } else if (name === 'websearch') {
    view.items = list(data.results).map(item);
    view.headline = view.items.length ? say(`返回 ${count(view.items.length)} 条网页来源`, `${count(view.items.length)} web sources returned`) : say('本次未取得可用网页结果', 'No usable web results returned');
    if (data.source) view.meta.push(data.source === 'deepseek' ? 'DeepSeek' : String(data.source));
    view.note = say('下列为来源链接与检索摘录，尚不等于已读取网页正文。', 'Source links and search excerpts do not constitute a page-text read.');
    if (data.scope === 'encyclopedia_only') view.warnings.push(say('当前仅返回百科来源', 'Encyclopedia fallback only'));
  } else {
    view.headline = text(data.summary || data.message) || say('工具已返回结果', 'Tool result returned');
    view.items = (Array.isArray(data) ? data : list(data.results || data.books || data.items)).map(item);
    view.note = text(data.note);
  }
  return view;
}
