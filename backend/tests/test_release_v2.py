"""Release provenance and evidence scope regressions; no live provider calls."""
import asyncio
import json
import sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import agent_release as release
import scholarly_sources as SS
from reading_coverage import ReadingCoverage


def test_registered_prompt_profiles_have_distinct_fingerprints_and_no_secret_values(monkeypatch):
    monkeypatch.setenv('LLM_API_KEY','must-not-appear')
    monkeypatch.delenv('PHIAGENT_PROMPT_VERSION',raising=False)
    current=release.release_descriptor(profile='0.1.2')
    historical=release.release_descriptor(profile='0.1.1')
    assert current['prompt_matches_manifest'] and historical['prompt_matches_manifest']
    assert current['effective_prompt_sha256']!=historical['effective_prompt_sha256']
    assert current['configuration_fingerprint']!=historical['configuration_fingerprint']
    assert current['tool_budget'] is None and not current['historical_prompt_override']
    assert historical['historical_prompt_override']
    assert release.prompt_spec()['version']=='0.1.2'
    for old,new in [('1.0.0','0.1.0'),('1.1.0','0.1.1'),('2.0.0-rc.2','0.1.2'),('0.2.0','0.1.2')]:
        assert release.prompt_spec(profile=old)['text']==release.prompt_spec(profile=new)['text']
    assert 'must-not-appear' not in json.dumps(current)
    assert len(release.prompt_spec(profile='0.1.2')['text'])<1000
    with pytest.raises(ValueError):release.prompt_spec(profile='unknown')
    pkg=json.loads((release.BASE.parent/'agent-app/package.json').read_text())
    assert pkg['version']==release.VERSION


@pytest.mark.parametrize('bad',[None,[],False,{'searches':None,'records':{'kept':{'title':'保留记录'}}}])
def test_null_and_wrong_shape_cache_recovers_preserves_bad_file_and_writes_atomically(tmp_path,monkeypatch,bad):
    cache=tmp_path/'cache.json';cache.write_text(json.dumps(bad))
    monkeypatch.setattr(SS,'CACHE_PATH',str(cache));monkeypatch.setattr(SS,'_cache',None)
    data=SS._load_cache()
    assert isinstance(data['searches'],dict) and isinstance(data['records'],dict)
    if isinstance(bad,dict):assert data['records']==bad['records']
    assert list(tmp_path.glob('cache.json.invalid-*'))
    data['searches']['fixture']={'results':[]}
    SS._save_cache()
    assert json.loads(cache.read_text())['searches']['fixture']=={'results':[]}
    assert not list(tmp_path.glob('tmp*'))


def test_partial_read_coverage_never_merges_editions_or_changed_text():
    ledger=ReadingCoverage()
    def result(a,b,book='one',sha='hash'):
        return {'book_id':book,'chapter_idx':2,'chapter_content_sha256':sha,'text':'文'*(b-a),
                'excerpt_start':a,'excerpt_end':b,'chapter_text_length':30}
    first=ledger.observe(result(0,10))['reading_progress']
    assert not first['whole_chapter_read']
    gap=ledger.observe(result(20,30))['reading_progress']
    assert gap['gaps_between_returned_ranges']==1
    assert ledger.observe(result(10,20,'other'))['reading_progress']['covered_characters']==10
    assert ledger.observe(result(10,20,sha='changed'))['reading_progress']['covered_characters']==10
    complete=ledger.observe(result(10,20))['reading_progress']
    assert complete['whole_chapter_read'] and complete['returned_ranges']==[[0,30]]
    assert ledger.observe(result(0,10))['reading_progress']['covered_characters']==30
    # Target section may already be complete even when the chapter isn't.
    assert '不能仅凭has_more' in first['note']


def test_abstract_is_resumable_and_never_mislabelled_as_paper_full_text(monkeypatch):
    from routes import agent_tools_scholarly as tool
    import research_bridge
    text='摘要开头。'*700+'决定性结论在末尾。'
    monkeypatch.setattr(research_bridge,'evidence_result',lambda *a:{'source_record_id':'fixture','abstract':{'text':text,'hash':'source-hash'},'access_level_after':'ABSTRACT_AVAILABLE'})
    first=tool._exec_get_scholarly_source({'source_record_id':'fixture','max_chars':1800})
    second=tool._exec_get_scholarly_source({'source_record_id':'fixture','offset':first['abstract']['next_offset'],'max_chars':10000})
    assert first['abstract']['text']+second['abstract']['text']==text
    assert first['read_scope']=='abstract_excerpt' and not first['whole_document_returned']
    assert second['abstract']['next_offset'] is None
    whole=tool._exec_get_scholarly_source({'source_record_id':'fixture','max_chars':len(text)})
    assert whole['read_scope']=='available_abstract' and not whole['whole_document_returned']
    assert whole['abstract']['window_covers_available_text']
    assert whole['abstract']['source_abstract_completeness']=='unverified'
    missing=tool._exec_get_scholarly_source({'source_record_id':'fixture','offset':len(text)+1})
    assert missing['error']=='ABSTRACT_OFFSET_OUT_OF_RANGE' and missing['read_scope']=='empty_window'
    for value in [-1,False,0]:
        assert tool._exec_get_scholarly_source({'source_record_id':'fixture','max_chars':value})['error']=='INVALID_EVIDENCE_WINDOW'


def test_main_usage_is_recorded_without_claiming_auxiliary_model_cost(monkeypatch):
    monkeypatch.delenv('PHIAGENT_PROMPT_VERSION',raising=False)
    import deep_bare_agent as bare
    from langchain_core.messages import AIMessageChunk
    class Model:
        def bind_tools(self,tools):return self
        async def astream(self,messages):
            assert sum(m.type=='system' for m in messages)==1
            assert messages[0].content == release.prompt_spec(profile='0.1.2')['text']
            yield AIMessageChunk(content='测试回答',response_metadata={'finish_reason':'stop','model_name':'fixture'},
                usage_metadata={'input_tokens':10,'output_tokens':5,'total_tokens':15})
    async def tools():return []
    async def questions(*args):return {'suggestions':[],'status':'unavailable'}
    monkeypatch.setattr(bare,'load_tools',tools);monkeypatch.setattr(bare,'load_model',Model)
    monkeypatch.setattr(bare,'source_metadata',lambda *a:([],None));monkeypatch.setattr(bare,'exploration_questions',questions)
    async def run():return [e async for e in bare.stream_bare_agent('测试',[])]
    events=asyncio.run(run());done=next(e for e in events if e['type']=='done')
    assert done['main_model_usage']['usage']['total_tokens']==15
    assert not done['main_model_usage']['includes_auxiliary_tool_models']
    assert done['release']['prompt_version']=='0.1.2' and done['release']['tool_budget'] is None
    assert done['release']['toolset_sha256'] and any(e['type']=='runtime_metadata' for e in events)
