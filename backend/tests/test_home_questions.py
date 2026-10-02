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
