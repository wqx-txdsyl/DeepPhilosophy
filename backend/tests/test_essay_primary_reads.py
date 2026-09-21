"""A search hit must be read before it becomes an essay's source material."""
import json
from deep_context import current_tool_agent
import deep_agent_tools as deep
from routes import agent_tools_memory as memory


def test_general_essay_reads_sources_and_lists_only_cited_material(monkeypatch):
    slot = {'essays': {}}
    monkeypatch.setattr(memory, '_mem_slot', lambda: slot)
    hits = [{'book_id': 'a', 'chapter_idx': 2, 'snippet': '摘要不能代替正文'},
            {'book_id': 'b', 'chapter_idx': 3, 'snippet': '空章'}]
    monkeypatch.setitem(memory.TOOLS, 'search_books', {'execute': lambda args: {'results': hits}})
    monkeypatch.setitem(memory.TOOLS, 'websearch', {'execute': lambda args: {}})
    reads = []
    def read(args):
        reads.append(args)
        if args['book_id'] == 'b':
            return {'error': 'EMPTY_CHAPTER_TEXT'}
        return {'book_id': 'a', 'book_title': '甲书', 'chapter_idx': 2, 'title': '第二章',
                'citation_label': '【《甲书》·第二章】', 'text': '真实上下文'}
    monkeypatch.setattr(deep, 'get_chapter', read)
    def chat(messages, **kwargs):
        content = messages[0]['content']
        assert '真实上下文' in content and '摘要不能代替正文' not in content
        return {'choices': [{'message': {'content': '论证【《甲书》·第二章】'}}]}
    monkeypatch.setattr(memory, 'llm_chat', chat)
    token = current_tool_agent.set('general')
    try:
        reply, citations, steps = memory._essay_pipeline('题目')
    finally:
        current_tool_agent.reset(token)
    assert len(reads) == 2
    assert len(citations) == 1 and citations[0]['book_id'] == 'a'
    assert len([s for s in steps if s['name'] == 'get_chapter']) == 2


def test_general_essay_does_not_claim_unused_search_hits(monkeypatch):
    monkeypatch.setattr(memory, '_mem_slot', lambda: {'essays': {}})
    monkeypatch.setitem(memory.TOOLS, 'search_books', {'execute': lambda args: {'results': [{'book_id': 'a', 'chapter_idx': 1}]}})
    monkeypatch.setitem(memory.TOOLS, 'websearch', {'execute': lambda args: {}})
    monkeypatch.setattr(deep, 'get_chapter', lambda args: {'error': 'INVALID_CHAPTER_DATA'})
    monkeypatch.setattr(memory, 'llm_chat', lambda *a, **kw: {'choices': [{'message': {'content': '直接论证'}}]})
    token = current_tool_agent.set('general')
    try:
        assert memory._essay_pipeline('题目')[1] == []
    finally:
        current_tool_agent.reset(token)
