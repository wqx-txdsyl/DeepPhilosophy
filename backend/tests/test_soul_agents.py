"""Preview roster, corpus isolation, provenance and streaming behavior."""
import asyncio
import json
import sys
from pathlib import Path
import pytest
from langchain_core.messages import AIMessageChunk

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from soul_agents import ROOT, catalog, active_catalog, soul_prompt, is_soul_agent
from soul_agent_tools import PrimaryTexts
from soul_agent_runtime import stream_soul_agent, used_citations, persona_history, PublicPerspective, split_perspective


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
    assert done['release']['prompt_version'] == 'soul-persona-4'


async def _collect(key):
    return [e async for e in stream_soul_agent('请讨论自由', [], key)]


@pytest.mark.parametrize('key', list(active_catalog()))
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
    assert not any(e['type']=='provider_reasoning_delta' for e in events)
    done=next(e for e in events if e['type']=='done')
    assert done['suggestions_status']=='disabled' and done['runtime_profile']=='bare'
    assert done['content']=='第一句。第二句。'
    assert not any(e['type']=='suggestions' for e in events)


def test_other_responders_are_not_personal_memories():
    original = [
        {'role':'user','content':'聊聊你自己'},
        {'role':'assistant','agent_id':'general','content':'我是深哲，没有眼睛。'},
        {'role':'assistant','agent_id':'sartre','content':'谈谈我的作品。'},
        {'role':'assistant','content':'旧版本没有身份字段的回答'},
    ]
    converted = persona_history(original,'sartre')
    assert converted[0] == original[0]
    assert converted[1]['role']=='user'
    assert '仅作引用资料' in converted[1]['content'] and '深哲' in converted[1]['content']
    assert converted[2] == original[2] and converted[3] == original[3]
    assert original[1]['role']=='assistant'  # No mutation of saved history.


def test_body_questions_and_platform_identity_are_distinct_in_souls():
    for key in catalog():
        prompt = soul_prompt(key)
        assert '你的眼睛' in prompt
        assert '已知的生平可以用第一人称叙述' in prompt
        assert '只有明确询问屏幕后' in prompt
    sartre = soul_prompt('sartre')
    assert '1975年' in sartre and '三岁' in sartre


@pytest.mark.parametrize('step', [1, 2, 5, 13, 1000])
@pytest.mark.parametrize('opening,closing', [('<perspective>','</perspective>'), ('<Perspective>','</PERSPECTIVE>')])
def test_public_perspective_protocol_at_arbitrary_chunk_boundaries(step, opening, closing):
    raw = '\n'+opening+'赞许不能使一个准则成为正当。'+closing+'\n先问这个准则能否普遍成立。'
    output = PublicPerspective()
    events = []
    for start in range(0, len(raw), step):
        events += output.events({'type':'answer_preview', 'id':'one', 'content':raw[start:start+step]})
    for kind in ('token', 'done'):
        events += output.events({'type':kind, 'id':'one', 'content':raw})
    assert ''.join(e['content'] for e in events if e['type']=='answer_preview') == '先问这个准则能否普遍成立。'
    assert [e['content'] for e in events if e['type']=='persona_perspective'] == ['赞许不能使一个准则成为正当。']
    assert next(e for e in events if e['type']=='done')['content'] == '先问这个准则能否普遍成立。'
    assert not any('<perspective>' in e.get('content','') for e in events)


def test_plain_exact_output_and_broken_protocol_do_not_lose_text():
    for raw in (' {"message":"<perspective>示例</perspective>"}', '<other>正文</other>',
                '<perspective>没有结束', '<perspective>'+'x'*2100+'</perspective>正文'):
        output = PublicPerspective()
        for char in raw:
            output.events({'type':'answer_preview','id':'a','content':char})
        done = output.events({'type':'done','id':'a','content':raw})[-1]
        assert done['content'] == raw
    assert split_perspective('正文内 <perspective>引述</perspective>', final=True)[1].startswith('正文内 ')


def test_perspective_tools_and_answer_are_from_same_actor_without_duplicate_notes(monkeypatch):
    import deep_bare_agent
    class Model:
        turn = 0
        def bind_tools(self, tools): return self
        async def astream(self, messages):
            self.turn += 1
            yield AIMessageChunk(content='', additional_kwargs={'reasoning_content':'用户要求我扮演康德。'})
            if self.turn == 1:
                yield AIMessageChunk(content='<perspective>这句话的出处关系到我的判断。</perspective>\n先核对原文。')
                yield AIMessageChunk(content='', tool_call_chunks=[{'name':'read_primary_text',
                    'args':'{"book_id":"outside"}', 'id':'p1', 'index':0}])
            else:
                yield AIMessageChunk(content='<perspective>赞许不能作为正当性的根据。</perspective>\n')
                yield AIMessageChunk(content='这个理由不够。', response_metadata={'finish_reason':'stop'})
    model=Model()
    monkeypatch.setattr(deep_bare_agent, 'load_model', lambda:model)
    events=asyncio.run(_collect('kant'))
    assert model.turn == 2  # One tool turn and one answer; no note-writing model.
    assert [e['content'] for e in events if e['type']=='persona_perspective'] == [
        '这句话的出处关系到我的判断。','赞许不能作为正当性的根据。']
    assert any(e['type']=='tool' and e['status']=='error' for e in events)
    assert any(e['type']=='assistant_commentary' and e['content']=='先核对原文。' for e in events)
    assert next(e for e in events if e['type']=='done')['content']=='这个理由不够。'
    assert not any(e['type']=='provider_reasoning_delta' for e in events)
    assert all('<perspective>' not in e.get('content','') for e in events)


def test_perspective_is_not_a_cited_answer_and_cancelled_prefix_is_not_published(monkeypatch):
    import deep_bare_agent
    from soul_agent_tools import PrimaryTexts
    def read_tools(self):
        self.reads.append({'book_id':'abc','book_title':'论语','chapter_title':'学而','chapter_idx':0,
                          'citation_label':'【《论语》·学而】','source_type':'primary_text','text':'学而时习之'})
        return []
    class Model:
        def bind_tools(self, tools): return self
        async def astream(self, messages):
            yield AIMessageChunk(content='<perspective>《论语》值得核对。</perspective>\n你好。', response_metadata={'finish_reason':'stop'})
    monkeypatch.setattr(deep_bare_agent, 'load_model', Model)
    monkeypatch.setattr(PrimaryTexts, 'tools', read_tools)
    done=next(e for e in asyncio.run(_collect('confucius')) if e['type']=='done')
    assert done['citations']==[] and done['content']=='你好。'
    output=PublicPerspective()
    assert output.events({'type':'answer_preview','id':'a','content':'<perspective>尚未写完'})==[]
    assert output.events({'type':'error','content':'已停止'})==[{'type':'error','content':'已停止'}]


@pytest.mark.parametrize('content', ['', '<perspective>尚无充分根据。</perspective>'])
def test_provider_stop_without_public_answer_is_not_reported_as_success(monkeypatch, content):
    import deep_bare_agent
    class Model:
        def bind_tools(self, tools): return self
        async def astream(self, messages):
            yield AIMessageChunk(content=content, additional_kwargs={'reasoning_content':'工作规划'},
                                 response_metadata={'finish_reason':'stop'})
    monkeypatch.setattr(deep_bare_agent, 'load_model', Model)
    events=asyncio.run(_collect('epicurus'))
    done=next(e for e in events if e['type']=='done')
    assert not done['complete'] and done['finish_reason']=='empty_public_answer'
    assert any(e['type']=='error' for e in events)
