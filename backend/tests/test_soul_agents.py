"""Preview roster, corpus isolation, provenance and streaming behavior."""
import asyncio
import json
import sys
from pathlib import Path
import pytest
from langchain_core.messages import AIMessageChunk

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from soul_agents import ROOT, catalog, soul_prompt, is_soul_agent
from soul_agent_tools import PrimaryTexts
from soul_agent_runtime import stream_soul_agent, used_citations


def test_complete_roster_with_independent_souls_and_no_nietzsche():
    assert len(catalog()) == 119
    assert not is_soul_agent('nietzsche') and not is_soul_agent('general')
    contents = []
    cognitive_paths, voices = [], []
    for key, spec in catalog().items():
        prompt = soul_prompt(key)
        assert spec['name'] in prompt and spec['name_en'] in prompt
        assert spec['works'] and all(w in prompt for w in spec['works'])
        assert '## 思想立场' in prompt and '## 原典驱动' in prompt
        assert f'我是{spec["name"]}（{spec["name_en"]}）' in prompt
        cognition = prompt.split('## 我的认知路径\n', 1)[1].split('\n', 1)[0]
        voice = prompt.split('## 我的语气与交往\n', 1)[1].split('\n', 1)[0]
        cognitive_paths.append(cognition)
        voices.append(voice)
        assert '未取得' not in spec['works']
        contents.append(prompt)
    assert len(set(contents)) == 119
    assert len(set(cognitive_paths)) == 119 and len(set(voices)) == 119


def test_only_primary_tools_for_every_agent():
    for key in catalog():
        assert {tool.name for tool in PrimaryTexts(key).tools()} == {'search_primary_texts', 'read_primary_text'}


def test_author_scope_and_real_offsets(monkeypatch):
    import routes.agent_core as core
    monkeypatch.setattr(core, 'get_books', lambda: [
        {'id': 'ours', 'title': '道德形而上学奠基', 'author': '伊曼努尔·康德'},
        {'id': 'other', 'title': '伦理学', 'author': '斯宾诺莎'},
        {'id': 'commentary', 'title': '康德导论', 'author': '现代研究者'}])
    texts = PrimaryTexts('kant')
    assert set(texts.books) == {'ours'}
    assert texts.read(book_id='other')['error'] == 'OUTSIDE_AUTHOR_CORPUS'
    monkeypatch.setattr(core, 'read_chapter', lambda *_: {'title': '第一章', 'text': 'a' * 6000})
    first = texts.read(book_id='ours')
    second = texts.read(book_id='ours', offset=first['next_offset'])
    assert len(first['text']) == 4000 and second['offset'] == 4000 and len(second['text']) == 2000
    assert texts.read(book_id='ours', offset=7000)['error'] == 'OFFSET_OUT_OF_RANGE'
    assert texts.read(source_ref='web:invented')['error'] == 'UNKNOWN_PRIMARY_SOURCE'


def test_search_does_not_promote_commentary_and_web_read_keeps_candidate_status(monkeypatch):
    import routes.agent_core as core
    import routes.agent_tools_retrieval as retrieval
    import deep_web
    monkeypatch.setattr(core, 'get_books', lambda: [])
    monkeypatch.setattr(retrieval, '_exec_websearch', lambda _: {'results': [
        {'url': 'https://en.wikipedia.org/wiki/Kant', 'title': 'Biography'},
        {'url': 'https://plato.stanford.edu/entries/kant/', 'title': 'Commentary'},
        {'url': 'https://www.gutenberg.org/ebooks/5682', 'title': 'Critique of Pure Reason'}]})
    texts = PrimaryTexts('kant')
    result = texts.search('纯粹理性批判', online=True)
    assert len(result['sources']) == 1
    assert result['sources'][0]['source_status'] == 'UNVERIFIED_PRIMARY_CANDIDATE'
    monkeypatch.setattr(deep_web, 'read_page', lambda _: {'text': 'preface', 'url': result['sources'][0]['url']})
    read = texts.read(source_ref=result['sources'][0]['source_ref'])
    assert read['source_status'] == 'UNVERIFIED_PRIMARY_CANDIDATE'
    assert len(texts.reads) == 1


def test_sources_are_neither_fabricated_nor_unread_candidates():
    read = {'book_id': 'abc', 'book_title': '论语', 'chapter_title': '学而', 'chapter_idx': 0,
            'citation_label': '【《论语》·学而】', 'source_type': 'primary_text', 'text': '学而时习之'}
    assert used_citations([read], '未引用资料') == []
    assert used_citations([read], '【《论语》·学而】')[0]['verified'] is False


def test_pdf_reader_uses_actual_page_boundaries(monkeypatch):
    import research_transport, research_access
    from soul_agent_tools import read_pdf_source
    monkeypatch.setattr(research_transport, 'fetch_bytes', lambda *a, **kw: {'body': b'%PDF', 'url': a[0]})
    monkeypatch.setattr(research_access, 'parse_pdf', lambda _: ['first\n\nparagraph', 'second page'])
    result = read_pdf_source('https://example.org/text.pdf', offset=18)
    assert result['pdf_page'] == 2 and result['access_level'] == 'PDF_PASSAGE_READ'
    assert result['text'] == 'second page'


def test_stream_uses_soul_not_general_or_nietzsche_and_returns_tool_errors(monkeypatch):
    import deep_bare_agent
    seen = []
    class Model:
        turn = 0
        def bind_tools(self, tools):
            assert len(tools) == 2
            return self
        async def astream(self, messages):
            seen.append(list(messages))
            self.turn += 1
            if self.turn == 1:
                yield AIMessageChunk(content='', tool_call_chunks=[{'name': 'read_primary_text',
                    'args': '{"book_id":"outside"}', 'id': 'test-call', 'index': 0}])
            else:
                yield AIMessageChunk(content='我是康德。未取得原典，不作引文。', response_metadata={'finish_reason': 'stop'})
    monkeypatch.setattr(deep_bare_agent, 'load_model', Model)
    events = asyncio.run(_collect('kant'))
    systems = [m for m in seen[0] if m.type == 'system']
    assert len(systems) == 1 and systems[0].content == soul_prompt('kant')
    tool = next(e for e in events if e['type'] == 'tool')
    assert tool['tool_call_id'] == 'test-call' and tool['status'] == 'error'
    assert json.loads(tool['result'])['error'] == 'OUTSIDE_AUTHOR_CORPUS'
    done = next(e for e in events if e['type'] == 'done')
    assert done['agent_id'] == 'kant' and done['primary_passages_read'] == 0 and done['complete']
    assert done['release']['prompt_version'] == 'soul-persona-2'


async def _collect(key):
    return [e async for e in stream_soul_agent('请讨论自由', [], key)]


@pytest.mark.parametrize('key', list(catalog()))
def test_each_registered_agent_can_complete_a_turn(monkeypatch, key):
    import deep_bare_agent
    class Model:
        def bind_tools(self, tools): return self
        async def astream(self, messages):
            assert messages[0].content == soul_prompt(key)
            yield AIMessageChunk(content=catalog()[key]['name'], response_metadata={'finish_reason': 'stop'})
    monkeypatch.setattr(deep_bare_agent, 'load_model', Model)
    events = asyncio.run(_collect(key))
    assert next(e for e in events if e['type'] == 'done')['content'] == catalog()[key]['name']


def test_shared_stream_preserves_deltas_and_interim_without_exploration(monkeypatch):
    import deep_bare_agent
    class Model:
        turn=0
        def bind_tools(self,tools):return self
        async def astream(self,messages):
            self.turn+=1
            yield AIMessageChunk(content='',additional_kwargs={'reasoning_content':'分段思考'})
            if self.turn==1:
                yield AIMessageChunk(content='先回答一部分。')
                yield AIMessageChunk(content='',tool_call_chunks=[{'name':'read_primary_text','args':'{"book_id":"outside"}','id':'p1','index':0}])
            else:
                yield AIMessageChunk(content='第一句。')
                yield AIMessageChunk(content='第二句。',response_metadata={'finish_reason':'stop'})
    async def forbidden(*args):raise AssertionError('No philosopher exploration request')
    monkeypatch.setattr(deep_bare_agent,'load_model',Model)
    monkeypatch.setattr(deep_bare_agent,'exploration_questions',forbidden)
    events=asyncio.run(_collect('kant'))
    assert [e['content'] for e in events if e['type']=='answer_preview']==['先回答一部分。','第一句。','第二句。']
    assert any(e['type']=='assistant_commentary' and e['content']=='先回答一部分。' for e in events)
    assert len({e['id'] for e in events if e['type']=='provider_reasoning_delta'})==2
    done=next(e for e in events if e['type']=='done')
    assert done['suggestions_status']=='disabled' and done['runtime_profile']=='bare'
    assert done['content']=='第一句。第二句。'
    assert not any(e['type']=='suggestions' for e in events)
