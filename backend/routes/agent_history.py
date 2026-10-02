"""Authenticated, revisioned PhiAgent history and explicit account memory."""
from fastapi import APIRouter, Depends, HTTPException, Response, Request
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
def put_conversation(conversation_id: str, req: ConversationWrite, user: dict = Depends(auth_required)):
    if req.data.get("conversation_id") != conversation_id or not isinstance(req.data.get("messages"), list):
        raise HTTPException(422, "会话ID或消息格式不正确")
    if not all(isinstance(m, dict) and m.get('role') in {'user','assistant'}
               and isinstance(m.get('content'), str) and isinstance(m.get('message_id'), str)
               for m in req.data['messages']):
        raise HTTPException(422, "消息格式不正确")
    saved, item = account_data.save_conversation(user["id"], conversation_id, req.data, req.expected_revision)
    if not saved:
        raise HTTPException(409, {"record": item, "error": "CONVERSATION_CONFLICT"})
    return {"record": item}


@router.delete("/conversations/{conversation_id}")
def remove_conversation(conversation_id: str, user: dict = Depends(auth_required)):
    return {"record": account_data.delete_conversation(user["id"], conversation_id)}


@router.get("/memory")
def get_memory(user: dict = Depends(auth_required)):
    return {"memories": account_data.list_memories(user["id"])}


@router.post("/memory")
def add_memory(req: MemoryWrite, user: dict = Depends(auth_required)):
    if not req.text.strip():
        raise HTTPException(422, "记忆不能为空")
    return {"memory": account_data.remember(user["id"], req.text.strip())}


@router.delete("/memory/{memory_id}")
def delete_memory(memory_id: str, user: dict = Depends(auth_required)):
    return {"deleted": account_data.forget(user["id"], memory_id)}
