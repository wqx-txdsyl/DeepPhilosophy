"""Project isolation and lifecycle against disposable databases, never live users."""
import asyncio
import json
import sqlite3
import sys
from pathlib import Path
from types import SimpleNamespace
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import auth
import project_store as store
import project_research as research
from routes.projects import router
from auth_deps import auth_required


@pytest.fixture
def fixture(tmp_path,monkeypatch):
    monkeypatch.setattr(auth,'DB_PATH',str(tmp_path/'accounts.db'))
    app=FastAPI();app.include_router(router)
    app.dependency_overrides[auth_required]=lambda:{'id':1}
    return app,TestClient(app)


def content():
    return dict(title='儒家思想的当代价值',question='如何正视尊孔与批孔？',brief='区分学术批评与政治运动。',
                sources=[dict(id='S1',title='论语',url='https://ctext.org/analects/yan-yuan',locator='颜渊',text='己所不欲，勿施於人。')],
                objects=[dict(id='draft',kind='document',title='文稿',content='',versions=[]),dict(id='debate',kind='debate',title='争点',content='',versions=[])])


def create(client):
    r=client.post('/api/projects',json=content());assert r.status_code==201,r.text
    assert r.headers['cache-control']=='private, no-store'
    return r.json()['project']


def test_create_reload_user_project_chat_isolation_and_delete(fixture):
    app,c=fixture;p=create(c);pid=p['id']
    assert c.get('/api/projects').json()['projects'][0]['id']==pid
    assert c.get('/api/projects/'+pid).json()['project']==p
    # No Chat tables are even initialized by Project.
    with sqlite3.connect(auth.DB_PATH) as db:
        assert not db.execute("SELECT name FROM sqlite_master WHERE name LIKE 'agent_%'").fetchall()
    other=create(c);assert other['id']!=pid
    app.dependency_overrides[auth_required]=lambda:{'id':2}
    assert c.get('/api/projects').json()=={'projects':[]}
    for suffix in ('','/runs'):
        assert c.get('/api/projects/'+pid+suffix).status_code==404
    assert c.delete('/api/projects/'+pid).status_code==404
    app.dependency_overrides[auth_required]=lambda:{'id':1}
    assert c.delete('/api/projects/'+pid).status_code==200
    assert c.get('/api/projects/'+pid).status_code==404
    assert c.put('/api/projects/'+pid,json=dict(data=p['data'],expected_revision=1)).status_code==404
    assert c.get('/api/projects/'+other['id']).status_code==200


def test_auth_validation_owner_and_unique_object_ids(fixture):
    app,c=fixture
    assert c.post('/api/projects',json={**content(),'user_id':2}).status_code==422
    d=content();d['objects'].append(d['objects'][0]);assert c.post('/api/projects',json=d).status_code==422
    d=content();d['sources'][0]['url']='javascript:alert(1)';assert c.post('/api/projects',json=d).status_code==422
    app.dependency_overrides.clear()
    assert c.get('/api/projects').status_code==401


def test_conflict_manual_versions_and_import_export(fixture):
    _,c=fixture;p=create(c);pid=p['id'];d=p['data'];d['objects'][0]['content']='第一稿'
    r=c.put('/api/projects/'+pid,json=dict(data=d,expected_revision=1));assert r.status_code==200
    assert r.json()['project']['data']['objects'][0]['versions'][0]['content']==''
    d['objects'][0]['content']='过期修改'
    assert c.put('/api/projects/'+pid,json=dict(data=d,expected_revision=1)).status_code==409
    saved=c.get('/api/projects/'+pid).json()['project']
    assert saved['data']['objects'][0]['content']=='第一稿'
    imported=c.post('/api/projects',json=json.loads(json.dumps(saved['data']))).json()['project']
    assert imported['id']!=pid and imported['data']==saved['data']


def test_real_lifecycle_proposal_adopt_target_and_idempotence(fixture,monkeypatch):
    _,c=fixture;p=create(c);pid=p['id']
    async def fake(project,run):
        assert [s['id'] for s in project['data']['sources']]==['S1']
        assert run['object_id']=='debate'
        return '最强异议：能否在保留礼的同时消除身份等级？ [S1]'
    monkeypatch.setattr(research,'generate',fake)
    r=c.post(f'/api/projects/{pid}/runs',json=dict(object_id='debate',instruction='提出反驳',expected_revision=1));assert r.status_code==202
    run=c.get(f'/api/projects/{pid}/runs').json()['runs'][0]
    assert run['status']=='completed' and 'session' not in run
    assert c.get(f'/api/projects/{pid}').json()['project']['data']['objects'][1]['content']==''
    adopt=f'/api/projects/{pid}/runs/{run["id"]}/adopt'
    r=c.post(adopt,json=dict(expected_revision=1));assert r.status_code==200
    p=r.json()['project'];assert p['data']['objects'][0]['content']==''
    assert p['data']['objects'][1]['content'].startswith('最强异议')
    assert c.post(adopt,json=dict(expected_revision=1)).json()['project']['revision']==p['revision']
    assert c.get(f'/api/projects/{pid}/runs').json()['runs'][0]['status']=='adopted'


def test_edit_or_delete_sources_cannot_reappear_via_late_result(fixture,monkeypatch):
    _,c=fixture;p=create(c);pid=p['id']
    _,(r,snapshot)=store.new_run(1,pid,'r',1,'draft','研究')
    async def changed(project,run):
        new=content();new['sources']=[]
        store.save(1,pid,new,1)
        return '已删除的材料'
    monkeypatch.setattr(research,'generate',changed)
    asyncio.run(research.execute(1,pid,'r',snapshot))
    r=store.runs(1,pid)[0];assert r['status']=='stale' and r['result']==''
    assert store.adopt(1,pid,'r',2)[0]=='invalid'


def test_stop_and_delete_during_generation_drop_output(fixture,monkeypatch):
    _,c=fixture;p=create(c);pid=p['id']
    _,(r,snapshot)=store.new_run(1,pid,'r',1,'draft','研究')
    async def stopped(project,run):
        store.update_run(1,pid,'r',lambda r:{**r,'status':'canceled'})
        return '不应写入的结果'
    monkeypatch.setattr(research,'generate',stopped)
    asyncio.run(research.execute(1,pid,'r',snapshot))
    assert store.runs(1,pid)[0]['status']=='canceled' and store.runs(1,pid)[0]['result']==''
    _,(r,snapshot)=store.new_run(1,pid,'r2',1,'draft','研究')
    async def deleted(project,run):
        store.delete(1,pid);return '不能复活'
    monkeypatch.setattr(research,'generate',deleted)
    asyncio.run(research.execute(1,pid,'r2',snapshot))
    assert store.get(1,pid) is None and store.runs(1,pid)==[]


def test_model_failure_and_restart_are_not_success(fixture,monkeypatch):
    _,c=fixture;p=create(c);pid=p['id']
    _,(r,snapshot)=store.new_run(1,pid,'r',1,'draft','研究')
    async def fail(*args):raise RuntimeError('secret upstream detail')
    monkeypatch.setattr(research,'generate',fail)
    asyncio.run(research.execute(1,pid,'r',snapshot))
    r=store.runs(1,pid)[0];assert r['status']=='failed' and 'secret' not in r['error']
    store.new_run(1,pid,'r2',1,'draft','研究')
    monkeypatch.setattr(store,'SESSION','new-process')
    assert store.runs(1,pid)[0]['status']=='interrupted'


def test_run_revision_and_owner_check_adopt_conflict(fixture,monkeypatch):
    app,c=fixture;p=create(c);pid=p['id']
    assert c.post(f'/api/projects/{pid}/runs',json=dict(object_id='draft',instruction='研究',expected_revision=2)).status_code==409
    assert c.post(f'/api/projects/{pid}/runs',json=dict(object_id='unknown',instruction='研究',expected_revision=1)).status_code==404
    store.new_run(1,pid,'r',1,'draft','研究')
    store.update_run(1,pid,'r',lambda r:{**r,'status':'completed','result':'结果'})
    store.save(1,pid,content(),1)
    assert store.adopt(1,pid,'r',2)[0]=='conflict'
    app.dependency_overrides[auth_required]=lambda:{'id':2}
    assert c.post(f'/api/projects/{pid}/runs/r/adopt',json=dict(expected_revision=2)).status_code==404
    assert c.post(f'/api/projects/{pid}/runs/r/stop').status_code==404


def test_removing_source_revokes_stored_suggestions_and_account_delete(fixture):
    _,c=fixture;p=create(c);pid=p['id']
    store.new_run(1,pid,'r',1,'draft','研究')
    store.update_run(1,pid,'r',lambda r:{**r,'status':'completed','result':'私有原文'})
    d=content();d['sources']=[]
    assert c.put('/api/projects/'+pid,json=dict(data=d,expected_revision=1)).status_code==200
    r=store.runs(1,pid)[0];assert r['status']=='stale' and not r['result']
    store.delete_account(1);assert store.listing(1)==[] and store.runs(1,pid)==[]


def test_project_prompt_has_no_account_context_or_raw_history(fixture,monkeypatch):
    _,c=fixture;p=create(c)
    text='\n'.join(m.content for m in research.messages(p,dict(object_id='draft',instruction='研究')))
    assert '孔' in text and 'S1' in text
    assert 'conversation_id' not in text and 'explicit_memories' not in text
    import deep_bare_agent
    class Model:
        async def ainvoke(self,messages):
            assert len(messages)==2
            return SimpleNamespace(content='',response_metadata={})
    monkeypatch.setattr(deep_bare_agent,'load_model',lambda:Model())
    with pytest.raises(ValueError):asyncio.run(research.generate(p,dict(object_id='draft',instruction='研究')))
