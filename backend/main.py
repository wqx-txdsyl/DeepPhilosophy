"""
DeepPhilosophy 云端 API 服务器
功能：书籍目录 | 文件下载 | RAG问答 | 作者信息(爬虫+内置库) | 用户系统 | 历史同步
"""
import os
import sys
import json
import hashlib
import urllib.request
import urllib.error
import re
from pathlib import Path
from typing import Optional
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException, Query, UploadFile, File, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
import uvicorn

import config
from auth import (
    register, login, get_user_by_token,
    save_reading_progress, get_reading_history,
    save_chat_message, get_chat_history, clear_chat_history,
)
from philosophers_db import get_philosopher_info

# ============================================================
# FastAPI 应用
# ============================================================
app = FastAPI(
    title="DeepPhilosophy API",
    description="哲学爱好者知识库云端服务",
    version="1.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# 工具函数
# ============================================================
SKIP_AUTHORS = {"合集&概述", "合集", "概述", "其他"}

def is_valid_author(name: str) -> bool:
    """过滤非人物条目"""
    for skip in SKIP_AUTHORS:
        if skip in name:
            return False
    # 书名号通常表示这是一本书而非作者
    if name.startswith("《") and name.endswith("》"):
        return False
    return True


# ============================================================
# 数据模型
# ============================================================
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


# ============================================================
# 认证依赖
# ============================================================
def auth_required(authorization: str = Header(None)) -> dict:
    """验证 Bearer Token，返回用户信息"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="请先登录")
    token = authorization[7:]
    user = get_user_by_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="登录已过期，请重新登录")
    return user


# ============================================================
# 书籍目录 API
# ============================================================

def scan_books() -> list[dict]:
    """扫描哲学目录，返回所有书籍信息"""
    books = []
    knowledge_dir = config.KNOWLEDGE_DIR
    if not os.path.exists(knowledge_dir):
        return books

    for root, dirs, files in os.walk(knowledge_dir):
        for f in files:
            ext = Path(f).suffix.lower()
            if ext not in (".pdf", ".epub", ".txt", ".md"):
                continue

            full_path = os.path.join(root, f)
            rel_path = os.path.relpath(full_path, knowledge_dir)
            parts = rel_path.replace("\\", "/").split("/")

            region = parts[0] if len(parts) > 0 else "未知"
            author = parts[1] if len(parts) > 1 else "未知"
            author_clean = author.replace("###合集&概述###", "合集&概述")
            title = Path(f).stem

            file_id = hashlib.md5(rel_path.encode()).hexdigest()[:12]

            # 书籍分类标签
            tags = _classify_book(title, author_clean, region)

            books.append({
                "id": file_id,
                "title": title,
                "author": author_clean,
                "region": region,
                "file_type": ext.replace(".", ""),
                "file_size": os.path.getsize(full_path),
                "status": "pending" if ext == ".txt" else "available",
                "path": rel_path.replace("\\", "/"),
                "tags": tags,
                "updated_at": datetime.fromtimestamp(
                    os.path.getmtime(full_path)
                ).isoformat(),
            })

    return sorted(books, key=lambda b: (b["region"], b["author"], b["title"]))


def _classify_book(title: str, author: str, region: str) -> list[str]:
    """根据书名和作者自动生成分类标签"""
    tags = []
    title_lower = title.lower()

    # 哲学流派
    school_keywords = {
        "存在主义": ["存在", "existential"],
        "现象学": ["现象", "phenomenolog"],
        "形而上学": ["形而上学", "metaphysic"],
        "伦理学": ["伦理", "道德", "ethic", "moral"],
        "政治哲学": ["政治", "politic", "政府", "国家", "社会契约"],
        "美学": ["美学", "aesthetic", "艺术"],
        "认识论": ["认识", "知识", "理解", "epistemolog"],
        "逻辑学": ["逻辑", "logic", "推理"],
        "心灵哲学": ["心灵", "意识", "mind", "consciousness"],
        "语言哲学": ["语言", "language", "linguistic"],
        "科学哲学": ["科学", "science", "scientif"],
        "宗教哲学": ["宗教", "信仰", "神", "religion", "god"],
        "历史哲学": ["历史", "history"],
    }
    for school, kws in school_keywords.items():
        for kw in kws:
            if kw in title_lower:
                tags.append(school)
                break

    # 著作类型
    if any(kw in title for kw in ["全集", "文集", "选集", "著作", "作品"]):
        tags.append("全集/选集")
    elif any(kw in title for kw in ["批判", "论", "原理", "导论", "概论"]):
        tags.append("专著")
    elif any(kw in title for kw in ["对话", "篇", "录"]):
        tags.append("对话/语录")

    # 区域标记
    if region == "东方":
        if "儒家" in author or any(kw in title for kw in ["论语", "孟子", "大学", "中庸"]):
            tags.append("儒家")
        elif "道家" in author or any(kw in title for kw in ["道", "庄子", "老子"]):
            tags.append("道家")
        elif any(kw in title for kw in ["佛", "禅", "心经"]):
            tags.append("佛学")
    else:
        if any(kw in author for kw in ["柏拉图", "亚里士多德", "苏格拉底"]):
            tags.append("古希腊哲学")
        elif any(kw in author for kw in ["康德", "黑格尔", "尼采", "叔本华", "海德格尔"]):
            tags.append("德国哲学")
        elif any(kw in author for kw in ["笛卡尔", "萨特", "福柯", "德里达", "卢梭"]):
            tags.append("法国哲学")
        elif any(kw in author for kw in ["休谟", "洛克", "罗素", "维特根斯坦"]):
            tags.append("英国哲学")

    return tags[:4]  # 最多4个标签


@app.get("/api/books")
async def list_books(
    region: Optional[str] = Query(None),
    author: Optional[str] = Query(None),
    tag: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
):
    """获取书籍列表，支持多维度筛选"""
    books = scan_books()
    if region:
        books = [b for b in books if b["region"] == region]
    if author:
        books = [b for b in books if b["author"] == author]
    if tag:
        books = [b for b in books if tag in b.get("tags", [])]
    if status:
        books = [b for b in books if b["status"] == status]

    # 收集所有标签
    all_tags = sorted(set(t for b in books for t in b.get("tags", [])))

    return {"books": books, "total": len(books), "tags": all_tags}


@app.get("/api/books/tags")
async def list_tags():
    """获取所有分类标签"""
    books = scan_books()
    tags_count = {}
    for b in books:
        for t in b.get("tags", []):
            tags_count[t] = tags_count.get(t, 0) + 1
    return {"tags": sorted(tags_count.items(), key=lambda x: -x[1])}


@app.get("/api/books/{book_id}")
async def get_book(book_id: str):
    """获取单本书籍详情（含摘要）"""
    books = scan_books()
    for b in books:
        if b["id"] == book_id:
            b["summary"] = _generate_summary(b)
            return b
    raise HTTPException(status_code=404, detail="书籍未找到")


def _generate_summary(book: dict) -> str:
    """生成书籍摘要"""
    author = book["author"]
    title = book["title"]
    region = book["region"]
    tags = book.get("tags", [])

    parts = []
    if tags:
        parts.append(f"本书属于{'、'.join(tags)}领域的{t('专著', '著作')}。")
    if region == "东方":
        parts.append(f"{author}是东方哲学的重要思想家。")
    else:
        parts.append(f"{author}是西方哲学史上的重要思想家。")
    if book["file_type"] == "txt":
        parts.append(f"《{title}》目前尚未收录全文，敬请期待。")
    else:
        parts.append(f"《{title}》以{book['file_type'].upper()}格式提供阅读。")

    return "".join(parts)


def t(a, b):
    # 简单去重辅助
    return a


@app.get("/api/books/{book_id}/file")
async def download_book(book_id: str):
    """下载/流式传输书籍文件"""
    books = scan_books()
    for b in books:
        if b["id"] == book_id:
            file_path = os.path.join(config.KNOWLEDGE_DIR, b["path"])
            if os.path.exists(file_path):
                return FileResponse(
                    file_path,
                    media_type="application/octet-stream",
                    filename=Path(file_path).name,
                )
    raise HTTPException(status_code=404, detail="文件未找到")


# ============================================================
# 作者信息 API（哲学家数据库 + 百度百科爬虫）
# ============================================================

def scrape_baidu_baike(author_name: str) -> Optional[dict]:
    """从百度百科爬取作者信息"""
    try:
        import urllib.request
        import urllib.error
        import re

        url = f"https://baike.baidu.com/item/{urllib.parse.quote(author_name)}"
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        with urllib.request.urlopen(req, timeout=8) as resp:
            html = resp.read().decode('utf-8', errors='ignore')

        # 提取摘要（meta description）
        desc_match = re.search(
            r'<meta[^>]*name="description"[^>]*content="([^"]+)"',
            html, re.IGNORECASE
        )
        bio = ""
        if desc_match:
            bio = desc_match.group(1).strip()
            # 清理 HTML 实体
            bio = bio.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
            bio = bio.replace("&quot;", '"').replace("&#039;", "'")

        if bio and len(bio) > 30:
            return {"bio": bio, "source": "baidu_baike", "wiki_url": url}
        return None
    except Exception:
        return None


@app.get("/api/authors/{author_name}")
async def get_author_info(author_name: str):
    """获取作者详细信息（内置库 + 百度百科爬虫）"""
    books = scan_books()
    author_books = [
        b for b in books
        if b["author"] == author_name or author_name in b["author"]
    ]

    region = author_books[0]["region"] if author_books else "未知"
    book_titles = [b["title"] for b in author_books]

    # 1. 先从内置数据库获取
    info = get_philosopher_info(author_name)

    if info:
        return {
            "name": author_name,
            "region": region,
            "era": info.get("era", ""),
            "country": info.get("country", ""),
            "school": info.get("school", ""),
            "bio": info.get("bio", ""),
            "wiki_url": info.get("wiki_url", f"https://baike.baidu.com/item/{author_name}"),
            "books": book_titles,
            "book_count": len(book_titles),
            "source": "builtin_database",
        }

    # 2. 尝试从百度百科爬取
    scraped = scrape_baidu_baike(author_name)
    if scraped:
        return {
            "name": author_name,
            "region": region,
            "era": "",
            "country": "",
            "school": "",
            "bio": scraped["bio"],
            "wiki_url": scraped.get("wiki_url", f"https://baike.baidu.com/item/{author_name}"),
            "books": book_titles,
            "book_count": len(book_titles),
            "source": "baidu_baike",
        }

    # 3. 兜底
    return {
        "name": author_name,
        "region": region,
        "era": "",
        "country": "",
        "school": "",
        "bio": f"{author_name}是{region}哲学史上的重要思想家。著有{'、'.join(book_titles[:5])}等作品。",
        "wiki_url": f"https://baike.baidu.com/item/{author_name}",
        "books": book_titles,
        "book_count": len(book_titles),
        "source": "fallback",
    }


@app.get("/api/authors")
async def list_all_authors(tag: Optional[str] = Query(None)):
    """获取所有作者（过滤合集等非人物条目）"""
    books = scan_books()
    authors_map = {}

    for b in books:
        author = b["author"]
        if not is_valid_author(author):
            continue
        if author not in authors_map:
            # 获取哲学家信息
            info = get_philosopher_info(author)
            authors_map[author] = {
                "name": author,
                "region": b["region"],
                "books": [],
                "era": info.get("era", "") if info else "",
                "country": info.get("country", "") if info else "",
                "school": info.get("school", "") if info else "",
            }
        if b["title"] not in authors_map[author]["books"]:
            authors_map[author]["books"].append(b["title"])

    result = []
    for name, info in authors_map.items():
        entry = {
            "name": name,
            "region": info["region"],
            "book_count": len(info["books"]),
            "books": info["books"][:10],
            "era": info["era"],
            "country": info["country"],
            "school": info["school"],
        }
        # 标签筛选
        if tag and tag not in info.get("school", "") and tag not in info.get("country", ""):
            continue
        result.append(entry)

    return {"authors": sorted(result, key=lambda a: (a["region"], a["name"]))}


@app.get("/api/authors/filters")
async def get_author_filters():
    """获取作者多维度筛选选项"""
    books = scan_books()
    eras = set()
    countries = set()
    schools = set()

    for b in books:
        author = b["author"]
        if not is_valid_author(author):
            continue
        info = get_philosopher_info(author)
        if info:
            if info.get("era"):
                eras.add(info["era"])
            if info.get("country"):
                countries.add(info["country"])
            if info.get("school"):
                schools.add(info["school"])

    return {
        "eras": sorted(eras),
        "countries": sorted(countries),
        "schools": sorted(schools),
    }


# ============================================================
# 用户认证 API
# ============================================================

@app.post("/api/auth/register")
async def api_register(req: RegisterRequest):
    """用户注册"""
    result = register(req.username, req.password)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.post("/api/auth/login")
async def api_login(req: LoginRequest):
    """用户登录"""
    result = login(req.username, req.password)
    if not result["success"]:
        raise HTTPException(status_code=401, detail=result["error"])
    return result


@app.get("/api/auth/profile")
async def api_profile(user: dict = __import__('fastapi').Depends(auth_required)):
    """获取用户信息"""
    return {"username": user["username"], "id": user["id"]}


# ============================================================
# 阅读历史 API
# ============================================================

@app.post("/api/history/reading")
async def save_reading(req: ReadingProgressRequest,
                       user: dict = __import__('fastapi').Depends(auth_required)):
    """保存阅读进度"""
    save_reading_progress(
        user["id"], req.book_id, req.book_title,
        req.book_author, req.page, req.percent,
    )
    return {"success": True}


@app.get("/api/history/reading")
async def get_reading(user: dict = __import__('fastapi').Depends(auth_required)):
    """获取阅读历史"""
    return {"history": get_reading_history(user["id"])}


# ============================================================
# 聊天历史 API
# ============================================================

@app.post("/api/history/chat")
async def save_chat(req: ChatMessageRequest,
                    user: dict = __import__('fastapi').Depends(auth_required)):
    """保存聊天消息"""
    save_chat_message(user["id"], req.role, req.content, req.sources)
    return {"success": True}


@app.get("/api/history/chat")
async def get_chat(user: dict = __import__('fastapi').Depends(auth_required)):
    """获取聊天历史"""
    return {"messages": get_chat_history(user["id"])}


@app.delete("/api/history/chat")
async def clear_chat(user: dict = __import__('fastapi').Depends(auth_required)):
    """清空聊天历史"""
    clear_chat_history(user["id"])
    return {"success": True}


# ============================================================
# RAG 问答 API
# ============================================================

@app.post("/api/qa")
async def ask_question(req: QARequest,
                       authorization: Optional[str] = Header(None)):
    """基于哲学知识库的 RAG 问答，自动保存聊天历史"""
    try:
        from modules.embedding import EmbeddingManager
        from modules.vector_store import VectorStoreManager
        from modules.rag_chain import RAGChain

        mgr = EmbeddingManager()
        store = VectorStoreManager(embedding_function=mgr.get_embedding_function())

        if store.get_collection_stats()["chunk_count"] == 0:
            return {
                "answer": "知识库尚未初始化，请联系管理员或前往设置页面初始化知识库。",
                "sources": [],
                "question": req.question,
            }

        # LLM 客户端
        if req.api_key:
            from openai import OpenAI
            class UserLLMClient:
                def __init__(self, api_key, base_url, model):
                    self._client = OpenAI(api_key=api_key, base_url=base_url)
                    self._model = model
                def chat(self, messages, temperature=0.7, max_tokens=1024, max_retries=3):
                    import time
                    for attempt in range(max_retries):
                        try:
                            resp = self._client.chat.completions.create(
                                model=self._model, messages=messages,
                                temperature=temperature, max_tokens=max_tokens,
                            )
                            return resp.choices[0].message.content
                        except Exception as e:
                            if attempt < max_retries - 1:
                                time.sleep(2 ** attempt)
                            else:
                                raise RuntimeError(str(e))
            llm = UserLLMClient(req.api_key, "https://api.deepseek.com", req.model or "deepseek-chat")
        else:
            from modules.llm_client import DeepSeekClient
            llm = DeepSeekClient()

        rag = RAGChain(vector_store=store, llm_client=llm)
        result = rag.query(req.question)

        # 如果用户已登录，自动保存聊天历史
        if authorization and authorization.startswith("Bearer "):
            try:
                user = get_user_by_token(authorization[7:])
                if user:
                    save_chat_message(user["id"], "user", req.question)
                    save_chat_message(
                        user["id"], "assistant", result["answer"],
                        json.dumps(result.get("sources", []), ensure_ascii=False),
                    )
            except Exception:
                pass

        return result

    except Exception as e:
        return {
            "answer": f"问答服务暂时不可用: {str(e)}",
            "sources": [],
            "question": req.question,
        }


# ============================================================
# 知识库管理 API
# ============================================================

@app.post("/api/knowledge/init")
async def init_knowledge_base():
    """初始化/重建知识库（后台异步）"""
    import threading

    def _build():
        from modules.document_loader import DocumentLoader
        from modules.text_processor import TextProcessor
        from modules.embedding import EmbeddingManager
        from modules.vector_store import VectorStoreManager
        import chromadb
        import pdfplumber

        try:
            old_client = chromadb.PersistentClient(path=config.CHROMA_PERSIST_DIR)
            old_client.delete_collection(config.CHROMA_COLLECTION_NAME)
        except Exception:
            pass

        mgr = EmbeddingManager()
        store = VectorStoreManager(embedding_function=mgr.get_embedding_function())
        tp = TextProcessor()
        loader = DocumentLoader()

        count = skipped = 0
        for root, dirs, files in os.walk(config.KNOWLEDGE_DIR):
            for f in files:
                ext = Path(f).suffix.lower()
                if ext not in ('.epub', '.pdf'):
                    continue
                file_path = os.path.join(root, f)
                if ext == '.pdf':
                    try:
                        with pdfplumber.open(file_path) as pdf:
                            chars = sum(len((p.extract_text() or '')) for p in pdf.pages[:3])
                        if chars < 200:
                            skipped += 1
                            continue
                    except Exception:
                        skipped += 1
                        continue
                try:
                    pages = loader.load_file(file_path)
                    if pages:
                        full_text = loader.merge_pages_to_text(pages)
                        cleaned = tp.clean_text(full_text)
                        chunks = tp.split_text(cleaned)
                        rel_path = os.path.relpath(file_path, config.KNOWLEDGE_DIR)
                        category = loader.extract_category(rel_path)
                        store.add_documents(
                            chunks,
                            [{'source': f, 'category': category} for _ in chunks],
                            doc_id_prefix=f.replace('.', '_')[:50],
                        )
                        count += 1
                except Exception:
                    pass

    threading.Thread(target=_build, daemon=True).start()
    return {"status": "started", "message": "Building in background. Check /api/knowledge/stats for progress."}


@app.get("/api/knowledge/stats")
async def knowledge_stats():
    try:
        from modules.vector_store import VectorStoreManager
        from modules.embedding import EmbeddingManager
        mgr = EmbeddingManager()
        store = VectorStoreManager(embedding_function=mgr.get_embedding_function())
        return store.get_collection_stats()
    except Exception:
        return {"document_count": 0, "chunk_count": 0}


# ============================================================
# 数据同步 API
# ============================================================

@app.post("/api/sync/upload")
async def sync_upload(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="文件名不能为空")
    safe_name = file.filename.replace("\\", "/")
    if safe_name.startswith("/") or ".." in safe_name:
        raise HTTPException(status_code=400, detail="非法文件路径")

    target_path = os.path.join(config.KNOWLEDGE_DIR, safe_name)
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    content = await file.read()
    with open(target_path, "wb") as f:
        f.write(content)
    return {"status": "ok", "path": safe_name, "size": len(content)}


@app.post("/api/sync/delete")
async def sync_delete(req: SyncDeleteRequest):
    safe_path = req.path.replace("\\", "/")
    if safe_path.startswith("/") or ".." in safe_path:
        raise HTTPException(status_code=400, detail="非法文件路径")
    target_path = os.path.join(config.KNOWLEDGE_DIR, safe_path)
    if os.path.exists(target_path):
        os.remove(target_path)
        try:
            parent = os.path.dirname(target_path)
            if not os.listdir(parent):
                os.rmdir(parent)
        except Exception:
            pass
        return {"status": "ok", "deleted": safe_path}
    return {"status": "not_found", "path": safe_path}


# ============================================================
# 健康检查
# ============================================================

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "version": "1.1.0", "timestamp": datetime.now().isoformat()}


@app.get("/")
async def root():
    return {"name": "DeepPhilosophy API", "version": "1.1.0", "docs": "/docs"}


# ============================================================
# 启动
# ============================================================
if __name__ == "__main__":
    print("=" * 50)
    print("  DeepPhilosophy API Server v1.1.0")
    print("=" * 50)
    books = scan_books()
    print(f"  书籍总数: {len(books)}")
    print(f"  数据目录: {config.KNOWLEDGE_DIR}")
    print(f"  API: http://0.0.0.0:{config.SERVER_PORT}")
    print(f"  文档: http://0.0.0.0:{config.SERVER_PORT}/docs")
    print("=" * 50)
    uvicorn.run(app, host=config.SERVER_HOST, port=config.SERVER_PORT)
