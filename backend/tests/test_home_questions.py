import json
import sqlite3
import sys
from pathlib import Path
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import auth
import home_questions as home
import account_data

@pytest.fixture
def db(tmp_path, monkeypatch):
    monkeypatch.setattr(auth, 'DB_PATH', str(tmp_path / 'fixture.db'))
    monkeypatch.setattr(auth, '_sync_db_from_cloud', lambda: None)
    monkeypatch.setattr(auth, '_sync_db', lambda: None)
    monkeypatch.setenv('DP_ALLOW_GH_RESTORE','0')
    auth.init_db()
    with auth._get_conn() as conn:
        conn.execute("INSERT INTO users (id,username,password_hash,salt,profile) VALUES(1,'fixture','','','{}')")
        conn.execute("INSERT INTO users (id,username,password_hash,salt,profile) VALUES(2,'other','','','{}')")
    home._cache.clear()


def test_empty_account_does_not_generate_canned_questions(db, monkeypatch):
    monkeypatch.setattr(home, '_model_questions', lambda *args: pytest.fail('empty accounts should not call model'))
    assert home.generate_home_questions(1)['status'] == 'empty'


def test_signals_include_real_conversations_and_memory_but_not_other_account(db, monkeypatch):
    account_data.save_conversation(1,'a',{'messages':[{'message_id':'u','role':'user','content':'康德因果论如何回应休谟？'}, {'role':'assistant','content':'不作为用户立场'}]},0)
    account_data.save_conversation(2,'b',{'messages':[{'role':'user','content':'另一个账号私密问题'}]},0)
    account_data.remember(1,'我在研究康德')
    signals = home.load_signals(1)
    assert any(s['kind'] == 'discussion' and '康德因果' in s['text'] for s in signals)
    assert any(s['kind'] == 'explicit_memory' for s in signals)
    assert '另一个账号' not in json.dumps(signals,ensure_ascii=False)
    assert '不作为用户立场' not in json.dumps(signals,ensure_ascii=False)
    counter = []
    def model(signals, language, previous):
        counter.append(previous)
        return [{'question':'康德的因果范畴回应了休谟的哪个前提？','source_id':signals[0]['source_id']},
                {'question':'如果经验总是有例外，因果必然性还成立吗？','source_id':signals[0]['source_id'],'basis':'编造标签'},
                {'question':'一条编造的问题能通过核验吗？','source_id':'fake'}]
    monkeypatch.setattr(home,'_model_questions',model)
    first = home.generate_home_questions(1)
    assert first['status'] == 'ready' and len(first['suggestions']) == 2
    assert first['suggestions'][1]['basis'] == '最近讨论'
    assert home.generate_home_questions(1)['cached']
    assert len(counter) == 1
    assert home.generate_home_questions(1,refresh=True)['status'] == 'ready'
    assert len(counter[1]) == 2
    assert home.generate_home_questions(2)['status'] == 'ready'
    assert len(counter) == 3


def test_generation_failure_does_not_fallback_to_static_samples(db, monkeypatch):
    account_data.remember(1,'我在读亚里士多德')
    monkeypatch.setattr(home, '_model_questions', lambda *args: [{'question':'编造来源的问题？','source_id':'invented'}])
    assert home.generate_home_questions(1) == {'status':'unavailable','suggestions':[],'cached':False}


def test_deleting_legacy_archive_removes_recent_discussion_even_when_raw_rows_remain(db, monkeypatch):
    with auth._get_conn() as conn:
        conn.execute("INSERT INTO chat_history(user_id,role,content) VALUES(1,'user','语言是存在之家与语言使用如何比较？')")
    signals=home.load_signals(1)
    assert [s['source_id'] for s in signals]==['agent:conv_legacy_account_chat:legacy_chat_1']
    def model(signals,*args):
        return [{'question':'语言使用与存在之家能否解释同一种意义？','source_id':signals[0]['source_id']},
                {'question':'两种语言观对沉默的解释有什么不同？','source_id':signals[0]['source_id']}]
    monkeypatch.setattr(home,'_model_questions',model)
    assert home.generate_home_questions(1)['status']=='ready'
    assert home.generate_home_questions(1)['cached']
    account_data.delete_conversation(1,'conv_legacy_account_chat')
    with auth._get_conn() as conn: assert conn.execute('SELECT count(*) FROM chat_history WHERE user_id=1').fetchone()[0]==1
    assert home.load_signals(1)==[]
    assert home.generate_home_questions(1)['status']=='empty'
    assert home.load_signals(1)==[]  # reload/migration must not resurrect the archive


def test_reading_notes_and_saved_memory_are_separate_from_deleted_discussions(db, monkeypatch):
    auth.save_reading_progress(1,'fixture-book','测试书目','作者',1,5)
    auth.save_book_note(1,'fixture-book','我记录的阅读笔记')
    account_data.remember(1,'请记住我的阅读目标')
    account_data.save_conversation(1,'a',{'messages':[{'role':'user','message_id':'u','content':'需要删除的讨论'}]},0)
    account_data.save_conversation(2,'b',{'messages':[{'role':'user','message_id':'u','content':'他人记录'}]},0)
    account_data.delete_conversation(1,'a')
    signals=home.load_signals(1)
    assert {s['kind'] for s in signals}=={'reading','note','explicit_memory'}
    assert '需要删除的讨论' not in json.dumps(signals,ensure_ascii=False)
    assert len([s for s in home.load_signals(2) if s['kind']=='discussion'])==1


def test_deletion_while_model_generates_drops_mixed_reading_and_discussion_result(db, monkeypatch):
    auth.save_reading_progress(1,'fixture-book','测试书目','作者',1,5)
    account_data.save_conversation(1,'a',{'messages':[{'role':'user','message_id':'u','content':'删除中的讨论'}]},0)
    def model(signals,*args):
        account_data.delete_conversation(1,'a')
        # Even the reading-tagged question may have absorbed deleted context.
        return [{'question':'这本书如何回应刚才已经删除的讨论？','source_id':signals[0]['source_id']},
                {'question':'刚才的讨论与书中概念有什么关联？','source_id':signals[0]['source_id']}]
    monkeypatch.setattr(home,'_model_questions',model)
    assert home.generate_home_questions(1)=={'status':'stale','suggestions':[],'cached':False}
    assert not home._cache


def test_deletion_on_cache_hit_cannot_return_cached_discussion(db, monkeypatch):
    account_data.save_conversation(1,'a',{'messages':[{'role':'user','message_id':'u','content':'缓存中的讨论'}]},0)
    monkeypatch.setattr(home,'_model_questions',lambda signals,*args:[
        {'question':'该讨论中的因果必然性来自什么？','source_id':signals[0]['source_id']},
        {'question':'该讨论中的经验习惯如何受到反驳？','source_id':signals[0]['source_id']}])
    assert home.generate_home_questions(1)['status']=='ready'
    original=home.load_signals;calls=[]
    def race(*args):
        calls.append(1)
        if len(calls)==2:account_data.delete_conversation(1,'a')
        return original(*args)
    monkeypatch.setattr(home,'load_signals',race)
    assert home.generate_home_questions(1)=={'status':'empty','suggestions':[],'cached':False}
