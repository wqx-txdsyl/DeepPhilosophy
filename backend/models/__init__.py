"""
DeepPhilosophy — 共享 Pydantic 请求/响应模型
"""
from typing import Optional
from pydantic import BaseModel


class RegisterRequest(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class ReadingProgressRequest(BaseModel):
    book_id: str
    book_title: str
    book_author: str = ""
    page: int = 1
    percent: float = 0


class ChatMessageRequest(BaseModel):
    role: str
    content: str
    sources: Optional[str] = None


class ChatHistoryClearRequest(BaseModel):
    pass


class QARequest(BaseModel):
    question: str
    api_key: Optional[str] = None
    model: Optional[str] = "deepseek-chat"


class SyncDeleteRequest(BaseModel):
    path: str


class NoteRequest(BaseModel):
    book_id: str
    note_text: str = ""


class BookChatRequest(BaseModel):
    book_id: str
    role: str
    content: str


class UpdateProfileRequest(BaseModel):
    username: str


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


class AvatarRequest(BaseModel):
    avatar: str  # base64 data URL
