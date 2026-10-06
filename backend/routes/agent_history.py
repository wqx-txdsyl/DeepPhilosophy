"""Authenticated, revisioned PhiAgent history and explicit account memory."""
from fastapi import APIRouter, Depends, HTTPException, Response, Request, BackgroundTasks
import gzip
import json
from pydantic import BaseModel, Field, ConfigDict
from auth_deps import auth_required
import account_data

def private_response(response: Response):
    response.headers["Cache-Control"] = "private, no-store"


router = APIRouter(prefix="/api/agent", dependencies=[Depends(private_response)])


def history_response(request, payload):
    headers = {'Cache-Control':'private, no-store', 'Vary':'Accept-Encoding'}
    raw = json.dumps(payload, ensure_ascii=False).encode('utf-8')
    if len(raw) > 2000 and 'gzip' in request.headers.get('accept-encoding','').lower():
        raw = gzip.compress(raw, compresslevel=5)
        headers['Content-Encoding'] = 'gzip'
    return Response(raw, media_type='application/json', headers=headers)


class ConversationWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")
    data: dict
    expected_revision: int = Field(ge=0)


class MemoryWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str = Field(min_length=1)


class MemoryProfileWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str
    enabled: bool
    expected_revision: int = Field(ge=0)


class MemoryCorrection(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request: str = Field(min_length=1)
    expected_revision: int = Field(ge=0)


@router.get("/conversations")
def get_conversations(request: Request, index: bool = False, user: dict = Depends(auth_required)):
    return history_response(request, {"records": account_data.list_conversations(user["id"], index_only=index)})


@router.get('/conversations/{conversation_id}')
def get_conversation(conversation_id: str, request: Request, user: dict = Depends(auth_required)):
    # Revision must be read together with the payload, never from another call.
    with account_data.connection() as conn:
        row = conn.execute('SELECT * FROM agent_conversation_records WHERE user_id=? AND conversation_id=? AND deleted=0',
                           (user['id'], conversation_id)).fetchone()
        if not row: raise HTTPException(404, '会话不存在或已删除')
        return history_response(request, {'record':account_data.record(row)})


@router.put("/conversations/{conversation_id}")
def put_conversation(conversation_id: str, req: ConversationWrite, background_tasks: BackgroundTasks, user: dict = Depends(auth_required)):
    if req.data.get("conversation_id") != conversation_id or not isinstance(req.data.get("messages"), list):
        raise HTTPException(422, "会话ID或消息格式不正确")
    if not all(isinstance(m, dict) and m.get('role') in {'user','assistant'}
               and isinstance(m.get('content'), str) and isinstance(m.get('message_id'), str)
               for m in req.data['messages']):
        raise HTTPException(422, "消息格式不正确")
    saved, item = account_data.save_conversation(user["id"], conversation_id, req.data, req.expected_revision)
    if not saved:
        raise HTTPException(409, {"record": item, "error": "CONVERSATION_CONFLICT"})
    last = req.data['messages'][-1] if req.data['messages'] else {}
    if last.get('role') == 'assistant' and last.get('content') and not last.get('streaming') and last.get('stream_state') not in {'error','interrupted'}:
        from account_memory_profile import refresh
        background_tasks.add_task(refresh, user['id'])
    return {"record": item}


@router.delete("/conversations/{conversation_id}")
def remove_conversation(conversation_id: str, user: dict = Depends(auth_required)):
    return {"record": account_data.delete_conversation(user["id"], conversation_id)}


@router.get("/memory")
def get_memory(user: dict = Depends(auth_required)):
    return {"memories": account_data.list_memories(user["id"])}


@router.get('/memory/profile')
def get_memory_profile(background_tasks: BackgroundTasks, user: dict = Depends(auth_required)):
    from account_memory_profile import get_profile, history_sources, refresh, is_updating
    profile = get_profile(user['id'])
    if profile['status'] == 'updating' and not is_updating(user['id']):
        # A process restart can interrupt a background task. Resume next read.
        with account_data.connection() as conn:
            conn.execute("UPDATE agent_memory_profile SET status='idle',source_hash='' WHERE user_id=?", (user['id'],))
            conn.commit()
        profile['status'] = 'idle'
        profile['source_hash'] = ''
    if profile['enabled'] and profile['status'] != 'updating' and not (profile['manual'] and not profile['text'].strip()):
        _, digest = history_sources(user['id'])
        if digest != profile['source_hash']:
            background_tasks.add_task(refresh, user['id'])
            profile['status'] = 'updating'
    return {'profile': profile, 'memories': account_data.list_memories(user['id'])}


@router.put('/memory/profile')
def put_memory_profile(req: MemoryProfileWrite, user: dict = Depends(auth_required)):
    from account_memory_profile import save_profile
    saved, profile = save_profile(user['id'], req.text, req.enabled, req.expected_revision)
    if not saved:
        raise HTTPException(409, '记忆已在其他设备或后台更新；草稿已保留，请重新查看')
    return {'profile': profile}


@router.post('/memory/profile/refresh')
def refresh_memory_profile(background_tasks: BackgroundTasks, user: dict = Depends(auth_required)):
    from account_memory_profile import get_profile, refresh
    profile = get_profile(user['id'])
    if profile['enabled']:
        background_tasks.add_task(refresh, user['id'], True)
        profile['status'] = 'updating'
    return {'profile': profile}


@router.post('/memory/profile/correct')
async def correct_memory_profile(req: MemoryCorrection, user: dict = Depends(auth_required)):
    if not req.request.strip():
        raise HTTPException(422, '更正内容不能为空')
    from account_memory_profile import correct_profile
    try:
        saved, profile = await correct_profile(user['id'], req.request.strip(), req.expected_revision)
    except Exception:
        raise HTTPException(503, '本次更正未完成，旧摘要未改变，请重试')
    if not saved:
        raise HTTPException(409, '摘要刚刚更新，更正内容已保留，请读取最新版本再提交')
    return {'profile': profile}


@router.post("/memory")
def add_memory(req: MemoryWrite, user: dict = Depends(auth_required)):
    if not req.text.strip():
        raise HTTPException(422, "记忆不能为空")
    return {"memory": account_data.remember(user["id"], req.text.strip())}


@router.delete("/memory/{memory_id}")
def delete_memory(memory_id: str, user: dict = Depends(auth_required)):
    return {"deleted": account_data.forget(user["id"], memory_id)}
