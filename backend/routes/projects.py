"""Independent authenticated Project API. Does not create Chat conversations."""
import json
import uuid
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Response, BackgroundTasks
from pydantic import BaseModel, ConfigDict, Field, model_validator
from auth_deps import auth_required
import project_store as store
import project_research


def private(response: Response):
    response.headers['Cache-Control'] = 'private, no-store'


router = APIRouter(prefix='/api/projects', tags=['projects'], dependencies=[Depends(private)])


class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid')


class Source(Strict):
    id: str = Field(min_length=1,max_length=100)
    title: str = Field(min_length=1,max_length=500)
    url: str = Field(default='',max_length=2000)
    locator: str = Field(default='',max_length=1000)
    text: str = Field(default='',max_length=25000)

    @model_validator(mode='after')
    def safe_url(self):
        if self.url and not self.url.startswith(('https://','http://')): raise ValueError('来源链接须为 http 或 https')
        return self


class Version(Strict):
    content: str = Field(max_length=80000)
    at: str = Field(max_length=100)


class Artifact(Strict):
    id: str = Field(min_length=1,max_length=100)
    kind: Literal['document','debate','action']
    title: str = Field(min_length=1,max_length=200)
    content: str = Field(default='',max_length=80000)
    versions: list[Version] = Field(default_factory=list,max_length=10)


class Project(Strict):
    title: str = Field(min_length=1,max_length=200)
    question: str = Field(min_length=1,max_length=3000)
    brief: str = Field(default='',max_length=10000)
    sources: list[Source] = Field(default_factory=list,max_length=50)
    objects: list[Artifact] = Field(min_length=1,max_length=20)

    @model_validator(mode='after')
    def unique(self):
        for values in (self.sources,self.objects):
            if len({v.id for v in values}) != len(values): raise ValueError('对象ID不得重复')
        if len(json.dumps(self.model_dump(),ensure_ascii=False).encode()) > 2_000_000: raise ValueError('项目超过 2MB，请拆分资料或导出归档')
        if not self.title.strip() or not self.question.strip(): raise ValueError('标题和问题不能为空')
        return self


class Write(Strict):
    data: Project
    expected_revision: int = Field(ge=1)


class Run(Strict):
    object_id: str = Field(min_length=1,max_length=100)
    instruction: str = Field(min_length=1,max_length=3000)
    expected_revision: int = Field(ge=1)


class Revision(Strict):
    expected_revision: int = Field(ge=1)


def require(uid,pid):
    p = store.get(uid,pid)
    if not p: raise HTTPException(404,'项目不存在')
    return p


@router.get('')
def listing(user: dict = Depends(auth_required)):
    return {'projects':store.listing(user['id'])}


@router.post('',status_code=201)
def create(data: Project,user: dict = Depends(auth_required)):
    pid = 'prj_'+uuid.uuid4().hex
    _, p = store.save(user['id'],pid,data.model_dump(),0,create=True)
    return {'project':p}


@router.get('/{pid}')
def get(pid: str,user: dict = Depends(auth_required)):
    return {'project':require(user['id'],pid)}


@router.put('/{pid}')
def put(pid: str,req: Write,user: dict = Depends(auth_required)):
    require(user['id'],pid)
    # Preserve a bounded previous draft when users edit, not on unchanged saves.
    previous = require(user['id'],pid)
    data = req.data.model_dump()
    old = {o['id']:o for o in previous['data']['objects']}
    for obj in data['objects']:
        if obj['id'] in old and old[obj['id']]['content'] != obj['content']:
            obj['versions'] = (old[obj['id']].get('versions',[])+[{'content':old[obj['id']]['content'],'at':store.now()}])[-10:]
    ok,p = store.save(user['id'],pid,data,req.expected_revision)
    if not ok: raise HTTPException(409,'项目已有新版本；请先导出当前修改，再重新加载。')
    # A source removed or changed invalidates old source-dependent suggestions.
    if previous['data']['sources'] != data['sources']:
        for r in store.runs(user['id'],pid):
            store.update_run(user['id'],pid,r['id'],lambda r:{**r,'result':'','status':'stale','error':'资料已变动，旧研究结果已撤回。'})
    return {'project':p}


@router.delete('/{pid}')
def delete(pid: str,user: dict = Depends(auth_required)):
    require(user['id'],pid)
    store.delete(user['id'],pid)
    return {'deleted':True}


@router.get('/{pid}/runs')
def runs(pid: str,user: dict = Depends(auth_required)):
    require(user['id'],pid)
    return {'runs':[{k:v for k,v in r.items() if k!='session'} for r in store.runs(user['id'],pid)]}


@router.post('/{pid}/runs',status_code=202)
def start(pid: str,req: Run,background: BackgroundTasks,user: dict = Depends(auth_required)):
    status,payload = store.new_run(user['id'],pid,'run_'+uuid.uuid4().hex,req.expected_revision,req.object_id,req.instruction)
    if status != 'ok': raise HTTPException({'missing':404,'object':404,'busy':409,'conflict':409}[status], {'missing':'项目不存在','object':'工作对象不存在','busy':'请先停止或等待当前项目任务','conflict':'项目已有新版本，请重新加载'}[status])
    run,snapshot = payload
    background.add_task(project_research.execute,user['id'],pid,run['id'],snapshot)
    return {'run':{k:v for k,v in run.items() if k!='session'}}


@router.post('/{pid}/runs/{rid}/stop')
def stop(pid: str,rid: str,user: dict = Depends(auth_required)):
    require(user['id'],pid)
    r = store.update_run(user['id'],pid,rid,lambda r:{**r,'status':'canceled'} if r['status'] in ('queued','running') else r)
    if not r: raise HTTPException(404,'任务不存在')
    return {'stopped':True}


@router.post('/{pid}/runs/{rid}/adopt')
def adopt(pid: str,rid: str,req: Revision,user: dict = Depends(auth_required)):
    status,p = store.adopt(user['id'],pid,rid,req.expected_revision)
    if status != 'ok': raise HTTPException(404 if status=='missing' else 409,'无法采纳；请确认任务完成且项目未修改。')
    return {'project':p}
