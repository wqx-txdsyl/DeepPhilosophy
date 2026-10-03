"""Author-bound primary-text discovery and reading, with no persona databases."""
import hashlib
import re
from urllib.parse import urlsplit
from langchain_core.tools import StructuredTool
from soul_agents import catalog, local_books


class PrimaryTexts:
    def __init__(self, key):
        self.spec = catalog()[key]
        self.books = {b['id']: b for b in local_books(key)}
        self.sources = {}
        self.reads = []

    def search(self, query: str, online: bool = False) -> dict:
        """检索本人的原典。返回本地书目/片段；online=true 时发现外部原典候选，候选须读取核对作者与作品。"""
        from routes.agent_core import _book_chapter_texts
        terms = [t.casefold() for t in re.split(r'[\s，。；、,;]+', query) if len(t) >= 2]
        hits = []
        for book in self.books.values():
            for index, title, text in _book_chapter_texts(book['id']):
                score = sum(text.casefold().count(t) + title.casefold().count(t) * 3 for t in terms)
                if not score:
                    continue
                positions = [text.casefold().find(t) for t in terms if t in text.casefold()]
                start = max(0, min(positions, default=0) - 120)
                hits.append({'book_id': book['id'], 'book_title': book['title'],
                             'chapter_idx': index, 'chapter_title': title,
                             'snippet': text[start:start + 700], 'offset': start, 'score': score,
                             'source_type': self.spec['source_type'], 'access_level': 'EXCERPT_DISCOVERED'})
        hits.sort(key=lambda h: -h['score'])
        out = {'agent': self.spec['name'], 'canonical_works': self.spec['works'],
               'books': [{'book_id': b['id'], 'title': b['title'], 'author': b.get('author'),
                          'chapter_count': b.get('chapterCount', 0)} for b in self.books.values()],
               'results': hits[:6], 'sources': [],
               'note': '书目或搜索摘要不等于已读取原典；使用 read_primary_text 读取上下文。'}
        if online or not hits:
            from routes.agent_tools_retrieval import _exec_websearch
            work = next((w for w in self.spec['works'] if w in query), self.spec['works'][0])
            search_query = f'{self.spec["name"]} {self.spec["name_en"]} "{work}" {query} 原文 original text full text'
            response = _exec_websearch({'query': search_query})
            for row in response.get('results', [])[:10]:
                url = row.get('url') or row.get('link') or ''
                host = (urlsplit(url).hostname or '').lower()
                # Encyclopedias and commentary are not promoted to primary texts.
                if not host or any(h in host for h in ('wikipedia.org', 'plato.stanford.edu', 'iep.utm.edu')):
                    continue
                ref = 'web:' + hashlib.sha256(url.encode()).hexdigest()[:16]
                self.sources[ref] = url
                out['sources'].append({'source_ref': ref, 'url': url, 'title': row.get('title', ''),
                                       'snippet': row.get('snippet') or row.get('description', ''),
                                       'source_status': 'UNVERIFIED_PRIMARY_CANDIDATE'})
            if response.get('error') or response.get('provider_errors'):
                out['provider_errors'] = response.get('provider_errors') or response.get('error')
            if not out['sources'] and not hits:
                out['note'] = '未取得可读原典。不得将模型记忆或 soul.md 的概述作为已查证引文。'
        return out

    def read(self, book_id: str = '', chapter_idx: int = 0, source_ref: str = '',
             offset: int = 0, focus: str = '') -> dict:
        """读取检索发现的原典。传本地 book_id/chapter_idx 或外部 source_ref；offset 可继续读取，focus 可定位。"""
        if offset < 0 or (bool(book_id) == bool(source_ref)):
            return {'error': 'INVALID_PRIMARY_READ', 'message': '选择一个本地书籍或外部来源，offset 不得为负。'}
        if source_ref:
            if source_ref not in self.sources:
                return {'error': 'UNKNOWN_PRIMARY_SOURCE', 'message': '请先搜索并使用实际返回的 source_ref。'}
            from deep_web import read_page
            args = {'url': self.sources[source_ref], 'focus': focus}
            if offset or not focus:
                args['offset'] = offset
            result = read_page(args)
            if result.get('error') == 'UNSUPPORTED_WEB_FORMAT' or urlsplit(args['url']).path.lower().endswith('.pdf'):
                result = read_pdf_source(args['url'], offset, focus)
            result.update(source_ref=source_ref, source_status='UNVERIFIED_PRIMARY_CANDIDATE',
                          note='实际读取的网页片段。核对它是否为目标作者的原典；导言、评论与目录不能充作原典。')
        else:
            if book_id not in self.books:
                return {'error': 'OUTSIDE_AUTHOR_CORPUS', 'message': '只能读取当前哲学家的原典或登记的历史见证。'}
            from routes.agent_core import read_chapter
            chapter = read_chapter(book_id, chapter_idx)
            if not chapter or not chapter.get('text'):
                return {'error': 'PRIMARY_TEXT_UNAVAILABLE', 'message': '书目存在，但该章节正文不可读。'}
            text = chapter['text']
            if focus and offset == 0:
                location = text.casefold().find(focus.casefold())
                if location >= 0:
                    offset = max(0, location - 150)
            if offset >= len(text):
                return {'error': 'OFFSET_OUT_OF_RANGE', 'text_chars': len(text)}
            end = min(offset + 4000, len(text))
            result = {'book_id': book_id, 'book_title': self.books[book_id]['title'],
                      'chapter_idx': chapter_idx, 'chapter_title': chapter['title'],
                      'text': text[offset:end], 'offset': offset, 'end_offset': end,
                      'next_offset': end if end < len(text) else None, 'has_more': end < len(text),
                      'access_level': 'PRIMARY_PASSAGE_READ', 'source_type': self.spec['source_type'],
                      'citation_label': f'【《{self.books[book_id]["title"]}》·{chapter["title"]}】'}
        if result.get('text') and not result.get('error'):
            self.reads.append(result)
        return result

    def tools(self):
        return [StructuredTool.from_function(self.search, name='search_primary_texts'),
                StructuredTool.from_function(self.read, name='read_primary_text')]


def read_pdf_source(url, offset=0, focus=''):
    """Reuse the existing public transport and bounded PDF text parser."""
    try:
        from research_transport import fetch_bytes
        from research_access import parse_pdf, MAX_PDF_PAGES
        response = fetch_bytes(url, accept='application/pdf')
        pages = parse_pdf(response['body'])
        text = '\n\n'.join(pages)
        if focus and not offset:
            found = text.casefold().find(focus.casefold())
            if found >= 0:
                offset = max(0, found - 150)
        if offset >= len(text):
            return {'error': 'OFFSET_OUT_OF_RANGE', 'text_chars': len(text)}
        end = min(offset + 4000, len(text))
        return {'url': response['url'], 'text': text[offset:end], 'offset': offset, 'end_offset': end,
                'has_more': end < len(text), 'next_offset': end if end < len(text) else None,
                'access_level': 'PDF_PASSAGE_READ', 'parsed_pages': len(pages),
                'parsed_page_limit': MAX_PDF_PAGES, 'document_truncated': True,
                'pdf_page': text[:offset].count('\n\n') + 1}
    except Exception as exc:
        return {'error': 'PDF_READ_UNAVAILABLE', 'message': str(exc)[:200]}
