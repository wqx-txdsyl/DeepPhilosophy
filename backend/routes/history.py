"""Reading history, chat history, notes, and book-chat routes"""
import json
from fastapi import APIRouter, Depends, Header
from models import ReadingProgressRequest, ChatMessageRequest, ChatHistoryClearRequest, NoteRequest, BookChatRequest
from auth import (
    get_user_by_token,
    save_reading_progress, get_reading_history,
    save_chat_message, get_chat_history, clear_chat_history,
    save_book_note, get_book_note, get_all_book_notes,
    save_book_chat, get_book_chat, clear_book_chat,
)

router = APIRouter()

def auth_required(authorization: str = Header(None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="请先登录")
    token = authorization[7:]
    user = get_user_by_token(token)
    if not user:
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="登录已过期，请重新登录")
    return user

@router.post("/api/history/reading")
async def save_reading(req: ReadingProgressRequest,
                       user: dict = Depends(auth_required)):
    save_reading_progress(user["id"], req.book_id, req.book_title,
                          req.book_author, req.page, req.percent)
    return {"success": True}

@router.get("/api/history/reading")
async def get_reading(user: dict = Depends(auth_required)):
    return {"history": get_reading_history(user["id"])}

@router.post("/api/history/chat")
async def save_chat(req: ChatMessageRequest,
                    user: dict = Depends(auth_required)):
    save_chat_message(user["id"], req.role, req.content, req.sources)
    return {"success": True}

@router.get("/api/history/chat")
async def get_chat(user: dict = Depends(auth_required)):
    return {"messages": get_chat_history(user["id"])}

@router.delete("/api/history/chat")
async def clear_chat(user: dict = Depends(auth_required)):
    clear_chat_history(user["id"])
    return {"success": True}

@router.post("/api/notes/save")
async def api_save_note(req: NoteRequest,
                       user: dict = Depends(auth_required)):
    save_book_note(user["id"], req.book_id, req.note_text)
    return {"success": True}

@router.get("/api/notes/{book_id}")
async def api_get_note(book_id: str,
                      user: dict = Depends(auth_required)):
    return {"note_text": get_book_note(user["id"], book_id)}

@router.get("/api/notes")
async def api_get_all_notes(user: dict = Depends(auth_required)):
    return {"notes": get_all_book_notes(user["id"])}

@router.post("/api/book-chat/save")
async def api_save_book_chat(req: BookChatRequest,
                            user: dict = Depends(auth_required)):
    save_book_chat(user["id"], req.book_id, req.role, req.content)
    return {"success": True}

@router.get("/api/book-chat/{book_id}")
async def api_get_book_chat(book_id: str,
                           user: dict = Depends(auth_required)):
    return {"messages": get_book_chat(user["id"], book_id)}

@router.delete("/api/book-chat/{book_id}")
async def api_clear_book_chat(book_id: str,
                             user: dict = Depends(auth_required)):
    clear_book_chat(user["id"], book_id)
    return {"success": True}
