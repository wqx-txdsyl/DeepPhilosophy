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

from fastapi import FastAPI, HTTPException, Query, UploadFile, File, Header, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn

import config
from auth import (
    init_db,
    register, login, get_user_by_token,
    save_reading_progress, get_reading_history,
    save_chat_message, get_chat_history, clear_chat_history,
    save_book_note, get_book_note, get_all_book_notes,
    save_book_chat, get_book_chat, clear_book_chat,
)
from philosophers_db import get_philosopher_info

# ============================================================
# Cloudflare R2 客户端（懒加载）
# ============================================================
_r2_client = None

def _get_r2_client():
    """懒加载 R2 S3 兼容客户端"""
    global _r2_client
    if _r2_client is None and config.USE_R2:
        import boto3
        from botocore.config import Config as BotoConfig
        _r2_client = boto3.client(
            's3',
            aws_access_key_id=config.R2_ACCESS_KEY,
            aws_secret_access_key=config.R2_SECRET_KEY,
            endpoint_url=config.R2_ENDPOINT,
            config=BotoConfig(
                region_name='auto',
                signature_version='s3v4',
            ),
        )
    return _r2_client

# ============================================================
# FastAPI 应用
# ============================================================
app = FastAPI(
    title="DeepPhilosophy API",
    description="哲学爱好者知识库云端服务",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化用户数据库（从OSS云端恢复）
init_db()

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
# 书籍目录 API (带缓存，关键词预计算一次)
# ============================================================

_BOOKS_CACHE = None
_BOOKS_CACHE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "books_cache.json")
_SUMMARIES_CACHE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "book_summaries.json")

def _get_cached_keywords(book_title: str, book_author: str) -> list:
    """从预计算缓存中获取关键词"""
    if not os.path.exists(_BOOKS_CACHE_PATH):
        return []
    try:
        with open(_BOOKS_CACHE_PATH, "r", encoding="utf-8") as f:
            cache = json.load(f)
        return cache.get(book_title + "||" + book_author, [])
    except Exception:
        return []

def _build_and_cache_keywords():
    """一次性预计算所有书籍的关键词（后台线程调一次）"""
    import threading
    def _build():
        try:
            from modules.text_processor import TextProcessor
            from modules.document_loader import DocumentLoader
            tp = TextProcessor()
            loader = DocumentLoader()
            cache = {}
            total = len([1 for r, d, fs in os.walk(config.KNOWLEDGE_DIR) for f in fs if os.path.splitext(f)[1].lower() in ('.epub', '.pdf')])
            idx = 0
            for root, dirs, files in os.walk(config.KNOWLEDGE_DIR):
                for f in files:
                    ext = os.path.splitext(f)[1].lower()
                    if ext not in ('.epub', '.pdf'): continue
                    idx += 1
                    fp = os.path.join(root, f)
                    try:
                        pages = loader.load_file(fp)
                        if pages:
                            text = loader.merge_pages_to_text(pages)[:5000]
                            kws = tp.extract_keywords(text, top_k=6)
                            title = os.path.splitext(f)[0]
                            author = os.path.basename(os.path.dirname(fp))
                            cache[title + "||" + author] = [kw for kw, w in kws]
                    except: pass
                    if idx % 10 == 0:
                        print(f"  Keywords: {idx}/{total}")
            os.makedirs(os.path.dirname(_BOOKS_CACHE_PATH), exist_ok=True)
            with open(_BOOKS_CACHE_PATH, "w", encoding="utf-8") as f:
                json.dump(cache, f, ensure_ascii=False)
            print(f"  Keywords cached: {idx} books")
        except Exception as e:
            print(f"  Keywords cache error: {e}")
    threading.Thread(target=_build, daemon=True).start()

def scan_books() -> list[dict]:
    """扫描书籍目录 —— 自动切换本地 / OSS / R2 / GitHub"""
    if config.USE_OSS:
        return _scan_books_oss()
    if config.USE_GITHUB:
        return _scan_books_github()
    if config.USE_R2:
        return _scan_books_r2()
    return _scan_books_local()


def _scan_books_oss() -> list[dict]:
    """从阿里云 OSS manifest 重建书籍列表"""
    TITLE_FIXES = {"SZ": "S/Z"}
    if not os.path.exists(config.OSS_MANIFEST_PATH):
        return []
    with open(config.OSS_MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    books = []
    for rel_path, entry in manifest.items():
        parts = rel_path.split("/")
        if len(parts) < 3: continue
        region = parts[0]
        author = parts[1].replace("###合集&概述###", "合集&概述")
        title = Path(parts[-1]).stem
        title = TITLE_FIXES.get(title, title)
        ext = os.path.splitext(parts[-1])[1].lower().replace(".", "")
        file_id = hashlib.md5(rel_path.encode()).hexdigest()[:12]
        tags = _classify_book(title, author, region)
        url = entry["url"] if isinstance(entry, dict) else entry
        size = entry.get("size", 0) if isinstance(entry, dict) else 0
        books.append({
            "id": file_id, "title": title, "author": author, "region": region,
            "file_type": ext, "file_size": size,
            "status": "available",
            "path": rel_path, "tags": tags,
            "updated_at": datetime.now().isoformat(),
            "_download_url": url,
        })
    # 附加缓存标签 + TXT 占位
    summary_cache = _load_summaries_cache()
    for b in books:
        key = b["title"] + "||" + b["author"]
        if key in summary_cache and summary_cache[key].get("tags"):
            for t in summary_cache[key]["tags"]:
                if t not in b["tags"]: b["tags"].append(t)
    seen = {(b["title"], b["author"]) for b in books}
    for cache_key, entry in summary_cache.items():
        if "||" not in cache_key: continue
        title, author = cache_key.split("||", 1)
        if (title, author) in seen: continue
        if "待收录" in title and "：" in title: continue
        seen.add((title, author))
        pfx = hashlib.md5((title + author).encode()).hexdigest()[:12]
        books.append({
            "id": pfx, "title": title, "author": author, "region": "西方",
            "file_type": "txt", "file_size": 0, "status": "pending",
            "path": f"西方/{author}/{title}.txt",
            "tags": entry.get("tags", []),
            "updated_at": datetime.now().isoformat(),
        })
    return sorted(books, key=lambda b: (_book_sort_key(b), b["region"], b["author"], b["title"]))


def _scan_books_github() -> list[dict]:
    """从 GitHub Release manifest 重建书籍列表"""
    TITLE_FIXES = {"SZ": "S/Z"}
    if not os.path.exists(config.GITHUB_MANIFEST_PATH):
        return []

    with open(config.GITHUB_MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    books = []
    seen_authors = set()

    for rel_path, entry in manifest.items():
        # rel_path: 东方/孔子/论语.epub
        parts = rel_path.split("/")
        if len(parts) < 3:
            continue
        region = parts[0]
        author_raw = parts[1]
        author = author_raw.replace("###合集&概述###", "合集&概述")
        ext = os.path.splitext(parts[-1])[1].lower().replace(".", "")
        title = Path(parts[-1]).stem
        title = TITLE_FIXES.get(title, title)

        file_id = hashlib.md5(rel_path.encode()).hexdigest()[:12]
        seen_authors.add(author)

        # Manifest entry may be {url, size} dict or plain string
        if isinstance(entry, dict):
            download_url = entry.get("url", "")
            file_size = entry.get("size", 0)
        else:
            download_url = entry
            file_size = 0

        tags = _classify_book(title, author, region)
        books.append({
            "id": file_id,
            "title": title,
            "author": author,
            "region": region,
            "file_type": ext,
            "file_size": file_size,
            "status": "pending" if ext == "txt" else "available",
            "path": rel_path,
            "tags": tags,
            "updated_at": datetime.now().isoformat(),
            "_download_url": download_url,
        })

    # 附加缓存标签
    summary_cache = _load_summaries_cache()
    for b in books:
        key = b["title"] + "||" + b["author"]
        if key in summary_cache and summary_cache[key].get("tags"):
            for t in summary_cache[key]["tags"]:
                if t not in b["tags"]:
                    b["tags"].append(t)

    # 补充 TXT 占位书（在缓存中但没有 PDF/EPUB 的书）
    seen = {(b["title"], b["author"]) for b in books}
    for cache_key, entry in summary_cache.items():
        if "||" not in cache_key:
            continue
        title, author = cache_key.split("||", 1)
        if (title, author) in seen:
            continue
        if "待收录" in title and "：" in title:
            continue  # 跳过空目录占位（如"待收录：XXX"）
        seen.add((title, author))
        cached_tags = entry.get("tags", [])
        region = "西方"
        pfx = hashlib.md5((title + author).encode()).hexdigest()[:12]
        books.append({
            "id": pfx,
            "title": title,
            "author": author,
            "region": region,
            "file_type": "txt",
            "file_size": 0,
            "status": "pending",
            "path": f"{region}/{author}/{title}.txt",
            "tags": cached_tags,
            "updated_at": datetime.now().isoformat(),
        })

    return sorted(books, key=lambda b: (_book_sort_key(b), b["region"], b["author"], b["title"]))


def _scan_books_r2() -> list[dict]:
    """从 Cloudflare R2 列出所有书籍"""
    TITLE_FIXES = {"SZ": "S/Z"}
    client = _get_r2_client()
    if client is None:
        return []

    books = []
    seen_authors = set()

    paginator = client.get_paginator('list_objects_v2')
    for page in paginator.paginate(Bucket=config.R2_BUCKET, Prefix='books/'):
        for obj in page.get('Contents', []):
            key = obj['Key']
            filename = key.rsplit('/', 1)[-1]
            ext = Path(filename).suffix.lower()
            if ext not in ('.pdf', '.epub', '.txt', '.md'):
                continue

            parts = key.replace('books/', '', 1).split('/')
            if len(parts) < 3:
                continue
            region = parts[0]
            author_raw = parts[1]
            author = author_raw.replace('###合集&概述###', '合集&概述')
            title = Path(parts[-1]).stem
            title = TITLE_FIXES.get(title, title)

            file_id = hashlib.md5(key.encode()).hexdigest()[:12]
            seen_authors.add(author)

            tags = _classify_book(title, author, region)
            books.append({
                "id": file_id,
                "title": title,
                "author": author,
                "region": region,
                "file_type": ext.replace('.', ''),
                "file_size": obj['Size'],
                "status": "pending" if ext == '.txt' else "available",
                "path": key.replace('books/', '', 1),
                "tags": tags,
                "updated_at": obj['LastModified'].strftime('%Y-%m-%dT%H:%M:%S'),
            })

    # 补充空目录占位
    prefix_len = len('books/')
    paginator2 = client.get_paginator('list_objects_v2')
    for page in paginator2.paginate(Bucket=config.R2_BUCKET, Prefix='books/', Delimiter='/'):
        for prefix in page.get('CommonPrefixes', []):
            p = prefix['Prefix'][prefix_len:]
            sub_paginator = client.get_paginator('list_objects_v2')
            for sub_page in sub_paginator.paginate(
                Bucket=config.R2_BUCKET,
                Prefix=prefix['Prefix'],
                Delimiter='/',
                MaxKeys=1,
            ):
                for cp in sub_page.get('CommonPrefixes', []):
                    pp = cp['Prefix'][len(prefix['Prefix']):].rstrip('/')
                    if not pp or pp.startswith('###合集&概述###'):
                        continue
                    author_clean = pp.replace('###合集&概述###', '合集&概述')
                    if author_clean not in seen_authors:
                        seen_authors.add(author_clean)
                        # figure out region
                        reg = '西方' if '西方' in prefix['Prefix'] else '东方'
                        pfx = hashlib.md5((reg + author_clean).encode()).hexdigest()[:12]
                        books.append({
                            "id": pfx,
                            "title": f"（待收录：{author_clean}）",
                            "author": author_clean,
                            "region": reg,
                            "file_type": "txt",
                            "file_size": 0,
                            "status": "pending",
                            "path": f"{reg}/{author_clean}/",
                            "tags": ["待收录"],
                            "updated_at": datetime.now().isoformat(),
                        })
                break  # only one page needed for delimiter query

    # 附加缓存
    kw_cache = {}
    if os.path.exists(_BOOKS_CACHE_PATH):
        try:
            with open(_BOOKS_CACHE_PATH, 'r', encoding='utf-8') as f:
                kw_cache = json.load(f)
        except Exception:
            pass
    summary_cache = _load_summaries_cache()
    for b in books:
        key = b["title"] + "||" + b["author"]
        b["keywords"] = kw_cache.get(key, [])
        if key in summary_cache and summary_cache[key].get("tags"):
            for t in summary_cache[key]["tags"]:
                if t not in b["tags"]:
                    b["tags"].append(t)

    return sorted(books, key=lambda b: (_book_sort_key(b), b["region"], b["author"], b["title"]))


def _scan_books_local() -> list[dict]:
    """扫描本地哲学目录，返回所有书籍信息"""
    # 文件名→显示标题修正（因文件系统不允许 / 等字符）
    TITLE_FIXES = {
        "SZ": "S/Z",
    }

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
            title = TITLE_FIXES.get(title, title)  # 修正文件名限制导致的显示问题

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

    # Also include empty author directories (no books yet, but author exists)
    seen_authors = {b["author"] for b in books}
    for region_name in ["东方", "西方"]:
        region_path = os.path.join(knowledge_dir, region_name)
        if not os.path.isdir(region_path): continue
        for author_dir in os.listdir(region_path):
            author_full = os.path.join(region_path, author_dir)
            if not os.path.isdir(author_full): continue
            author_clean = author_dir.replace("###合集&概述###", "合集&概述")
            if author_clean in seen_authors: continue
            # Count actual book files
            has_files = any(
                os.path.splitext(f)[1].lower() in ('.pdf', '.epub', '.txt', '.md')
                for f in os.listdir(author_full)
            )
            if has_files: continue  # alreay counted in main loop
            seen_authors.add(author_clean)
            pfx = hashlib.md5(author_dir.encode()).hexdigest()[:12]
            books.append({
                "id": pfx,
                "title": f"（待收录：{author_clean}）",
                "author": author_clean,
                "region": region_name,
                "file_type": "txt",
                "file_size": 0,
                "status": "pending",
                "path": f"{region_name}/{author_dir}/",
                "tags": ["待收录"],
                "updated_at": datetime.now().isoformat(),
            })

    # Attach cached keywords and tags (fast, no file loading)
    kw_cache = {}
    if os.path.exists(_BOOKS_CACHE_PATH):
        try:
            with open(_BOOKS_CACHE_PATH, "r", encoding="utf-8") as f:
                kw_cache = json.load(f)
        except Exception:
            pass
    summary_cache = _load_summaries_cache()
    for b in books:
        key = b["title"] + "||" + b["author"]
        b["keywords"] = kw_cache.get(key, [])
        # 从摘要缓存追加标签
        if b["title"] in summary_cache and summary_cache[b["title"]].get("tags"):
            cached_tags = summary_cache[b["title"]]["tags"]
            # 去重合并
            for t in cached_tags:
                if t not in b["tags"]:
                    b["tags"].append(t)
    return sorted(books, key=lambda b: (_book_sort_key(b), b["region"], b["author"], b["title"]))


def _book_sort_key(book: dict) -> int:
    """计算排序权重：合集最先，然后按哲学家出生年份升序"""
    author = book["author"]
    # 合集/概述排最前
    if "合集" in author or "概述" in author:
        return -99999
    # 从内置数据库获取年代
    info = get_philosopher_info(author)
    if info and info.get("era"):
        era = info["era"]
        # 提取出生年份
        import re
        m = re.search(r'(\d+)', era)
        if m:
            year = int(m.group(1))
            # 公元前年份转为负数（公元前数值越大=越早，所以直接取反）
            if "公元前" in era or "前" in era:
                year = -year
            return year
    # 未知年代的放最后
    return 9999


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

    # 附加AI标签（不附加摘要，减小列表体积加速加载）
    summaries_cache = _load_summaries_cache()
    for b in books:
        key = f"{b['title']}||{b.get('author', '')}"
        cached = summaries_cache.get(key, {})
        if cached.get("tags"):
            b["tags"] = cached["tags"]

    # 收集所有标签
    all_tags = sorted(set(t for b in books for t in b.get("tags", [])))

    # 允许浏览器缓存 5 分钟（减少重复加载）
    from starlette.responses import JSONResponse as StarletteJSON
    return StarletteJSON(
        {"books": books, "total": len(books), "tags": all_tags},
        headers={"Cache-Control": "public, max-age=300"},
    )


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
    """获取单本书籍详情（含摘要和关键词）"""
    books = scan_books()
    for b in books:
        if b["id"] == book_id:
            b["summary"] = _generate_summary(b)
            b["keywords"] = b.get("keywords", [])
            return b
    raise HTTPException(status_code=404, detail="书籍未找到")


def _load_summaries_cache() -> dict:
    """加载书籍摘要缓存"""
    if not os.path.exists(_SUMMARIES_CACHE_PATH):
        return {}
    try:
        with open(_SUMMARIES_CACHE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _generate_summary(book: dict) -> str:
    """生成书籍摘要（纯缓存，瞬间返回）"""
    cache = _load_summaries_cache()
    title = book["title"]
    author = book.get("author", "")
    # 优先用 title||author 作为 key（同名不同作者不冲突）
    key = f"{title}||{author}"
    if key in cache and cache[key].get("summary"):
        return cache[key]["summary"]
    # 兼容旧格式（仅 title 作为 key）
    if title in cache and cache[title].get("summary"):
        return cache[title]["summary"]

    # 极少数未缓存的情况：走极简兜底
    return f"《{title}》是{book['author']}的著作，{book['file_type'].upper()}格式，约{(book['file_size']/1024/1024):.1f}MB。"


def _read_book_sample(book: dict) -> str:
    """读取书籍开头内容样本（最多5000字符）"""
    try:
        file_path = os.path.join(config.KNOWLEDGE_DIR, book["path"])
        if not os.path.exists(file_path):
            return ""
        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".txt":
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read(5000)
        elif ext == ".epub":
            import ebooklib
            from ebooklib import epub
            from bs4 import BeautifulSoup
            import html2text
            bk = epub.read_epub(file_path)
            h2t = html2text.HTML2Text()
            h2t.ignore_links = True
            h2t.ignore_images = True
            h2t.body_width = 0
            texts = []
            for item in bk.get_items_of_type(ebooklib.ITEM_DOCUMENT):
                try:
                    soup = BeautifulSoup(item.get_content(), "html.parser")
                    for tag in soup(["script", "style", "nav"]):
                        tag.decompose()
                    t = h2t.handle(str(soup)).strip()
                    if len(t) > 50:
                        texts.append(t)
                except Exception:
                    pass
                if sum(len(t) for t in texts) > 5000:
                    break
            return "\n".join(texts)[:5000]
        elif ext == ".pdf":
            try:
                import pdfplumber
                with pdfplumber.open(file_path) as pdf:
                    texts = []
                    for page in pdf.pages[:3]:
                        t = page.extract_text()
                        if t:
                            texts.append(t)
                    return "\n".join(texts)[:5000]
            except Exception:
                return ""
    except Exception:
        return ""
    return ""


def _extract_summary_from_content(content: str, book: dict) -> str:
    """从内容中提取摘要信息（使用jieba关键词 + 启发式规则）"""
    import jieba.analyse
    try:
        # 提取关键词
        keywords = jieba.analyse.textrank(content[:3000], topK=8, withWeight=True,
            allowPOS=("n", "nr", "ns", "nt", "nz", "v", "vn", "a", "an"))
        key_terms = [kw for kw, w in keywords if len(kw) >= 2 and w > 0.01][:6]

        parts = []
        parts.append(f"《{book['title']}》是{book['author']}的{'哲学' if book['region'] == '西方' else ''}著作。")
        if key_terms:
            parts.append(f"主要涉及{'、'.join(key_terms[:4])}等主题。")
        parts.append(f"本书约{(book['file_size'] / 1024 / 1024):.1f}MB，以{book['file_type'].upper()}格式收录。")
        return "".join(parts)
    except Exception:
        return f"《{book['title']}》是{book['author']}的著作，约{(book['file_size'] / 1024 / 1024):.1f}MB。"


def t(a, b):
    # 简单去重辅助
    return a


@app.get("/api/books/{book_id}/render")
async def render_epub_chapter(book_id: str, chapter: int = Query(0)):
    """将 EPUB 章节渲染为分页 HTML"""
    import ebooklib
    from ebooklib import epub
    from bs4 import BeautifulSoup, NavigableString

    books = scan_books()
    book = next((b for b in books if b["id"] == book_id), None)
    if not book or book["file_type"] != "epub":
        raise HTTPException(status_code=404, detail="仅支持 EPUB")

    # Resolve file location
    if config.USE_OSS and "_download_url" in book:
        req = urllib.request.Request(book["_download_url"], headers={"User-Agent": "DeepPhilosophy/1.0"})
        with urllib.request.urlopen(req, timeout=30) as src:
            raw = src.read()
        import tempfile, os as _os
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".epub")
        tmp.write(raw); tmp.close()
        eb = epub.read_epub(tmp.name)
        _os.unlink(tmp.name)
    elif config.USE_GITHUB and "_download_url" in book:
        req = urllib.request.Request(book["_download_url"], headers={"User-Agent": "DeepPhilosophy/1.0"})
        with urllib.request.urlopen(req, timeout=30) as src:
            raw = src.read()
        import tempfile, os as _os2
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".epub")
        tmp.write(raw); tmp.close()
        eb = epub.read_epub(tmp.name)
        _os2.unlink(tmp.name)
    else:
        eb = epub.read_epub(os.path.join(config.KNOWLEDGE_DIR, book["path"]))

    items = [it for it in eb.get_items_of_type(ebooklib.ITEM_DOCUMENT)]
    if not items:
        raise HTTPException(status_code=404, detail="无内容")

    chapter_idx = max(0, min(chapter, len(items) - 1))
    item = items[chapter_idx]
    content = item.get_content().decode('utf-8', errors='replace')
    soup = BeautifulSoup(content, 'html.parser')

    # Clean out unwanted tags
    for tag in soup(["script", "style", "nav", "head", "meta", "link"]):
        tag.decompose()

    # Extract text from body
    body = soup.find('body')
    if body:
        # Get all text with paragraph breaks
        paras = []
        for el in body.descendants:
            if el.name in ('p','h1','h2','h3','h4','h5','h6','div','blockquote','li') and el.get_text(strip=True):
                tag = el.name
                txt = el.get_text(strip=False)
                if tag.startswith('h'):
                    paras.append(f'<{tag}>{txt}</{tag}>')
                elif tag == 'blockquote':
                    paras.append(f'<blockquote>{txt}</blockquote>')
                else:
                    paras.append(f'<p>{txt}</p>')
        page_html = '\n'.join(paras) if paras else body.get_text()

    total_chapters = len(items)

    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<style>
  body {{ font-family: SimSun, serif; font-size: 18px; line-height: 1.9; color: #ccc; background: #1a1a1a; padding: 16px 20px 60px; max-width: 800px; margin: 0 auto; }}
  h1,h2,h3,h4,h5,h6 {{ color: #d4a574; text-align: center; margin: 1em 0 0.6em; }}
  p {{ margin: 0 0 0.8em; text-indent: 2em; }}
  blockquote {{ border-left: 3px solid #555; margin: 0.6em 1em; padding: 0.3em 1em; color: #aaa; }}
  li {{ margin: 0 0 0.4em; }}
</style></head><body>
{page_html}
</body></html>"""

    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=html)


@app.get("/api/books/{book_id}/file")
async def download_book(book_id: str, request: Request):
    """下载/流式传输书籍文件 —— R2 模式返回预签名 URL，本地模式返回文件流"""
    books = scan_books()
    book = None
    for b in books:
        if b["id"] == book_id:
            book = b
            break
    if not book:
        raise HTTPException(status_code=404, detail="书籍未找到")

    # OSS 模式：重定向到 OSS 直链（国内高速）
    if config.USE_OSS and "_download_url" in book:
        from starlette.responses import RedirectResponse as StarletteRedirect
        return StarletteRedirect(url=book["_download_url"], status_code=302)

    # GitHub 模式：Render 代理下载（支持 Range 按需取块）
    if config.USE_GITHUB and "_download_url" in book:
        gh_url = book["_download_url"]
        ext = Path(gh_url).suffix.lower()
        mime_map = {".pdf": "application/pdf", ".epub": "application/epub+zip", ".txt": "text/plain", ".md": "text/markdown"}
        mime = mime_map.get(ext, "application/octet-stream")
        range_header = request.headers.get("range", "")

        try:
            if range_header:
                # Range 请求：只取需要的字节块（PDF 逐页加载靠这个）
                import re as _re
                m = _re.match(r'bytes=(\d+)-(\d*)', range_header)
                if m:
                    start = int(m.group(1))
                    end_str = m.group(2)
                    end = int(end_str) if end_str else start + 2097151  # 默认 2MB 块
                    gh_req = urllib.request.Request(gh_url, headers={
                        "User-Agent": "DeepPhilosophy/1.0",
                        "Range": f"bytes={start}-{end}",
                    })
                    with urllib.request.urlopen(gh_req, timeout=30) as src:
                        data = src.read()
                        cr = src.headers.get("Content-Range", "")
                        total = int(cr.split("/")[-1]) if "/" in cr else len(data)
                    return Response(
                        content=data, status_code=206, media_type=mime,
                        headers={
                            "Content-Range": f"bytes {start}-{start+len(data)-1}/{total}",
                            "Accept-Ranges": "bytes",
                            "Content-Length": str(len(data)),
                        },
                    )

            # 全量下载
            gh_req = urllib.request.Request(gh_url, headers={"User-Agent": "DeepPhilosophy/1.0"})
            with urllib.request.urlopen(gh_req, timeout=120) as src:
                data = src.read()
            return Response(
                content=data, media_type=mime,
                headers={"Accept-Ranges": "bytes", "Content-Length": str(len(data))},
            )
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"下载失败: {str(e)[:100]}")

    # R2 模式：生成 1 小时有效的预签名下载 URL
    if config.USE_R2:
        client = _get_r2_client()
        r2_key = 'books/' + book["path"]
        url = client.generate_presigned_url(
            'get_object',
            Params={'Bucket': config.R2_BUCKET, 'Key': r2_key},
            ExpiresIn=3600,
        )
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=url)

    # 本地模式：流式返回文件
    file_path = os.path.join(config.KNOWLEDGE_DIR, book["path"])
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="文件不存在")
    ext = Path(file_path).suffix.lower()
    mime_map = {
        ".pdf": "application/pdf",
        ".epub": "application/epub+zip",
        ".mobi": "application/x-mobipocket-ebook",
        ".txt": "text/plain",
        ".md": "text/markdown",
    }
    return FileResponse(
        file_path,
        media_type=mime_map.get(ext, "application/octet-stream"),
        headers={"Content-Disposition": "inline"},
    )


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


# ⚠️ 标签分隔符统一：[/,、，;；] — 新增分隔符时，下面3个地方必须同步修改：
#   1. get_author_filters() — 第626/631行 (split+countries/schools)
#   2. list_all_authors() — 第768/772行 (filter matching)
#   3. AuthorsPage.jsx 前端 — 第88/91行 (client-side filter)
def _normalize_tag(tag):
    """Merge similar tags into broader categories for filter DISPLAY only.
    Returns a single canonical tag."""
    tag = tag.strip()
    merge_map = {
        "存在主义先驱": "存在主义", "存在哲学": "存在主义", "文学哲学": "存在主义",
        "柏拉图主义": "古希腊哲学", "逍遥学派": "古希腊哲学", "伊壁鸠鲁主义": "古希腊哲学",
        "米利都学派": "古希腊哲学", "埃利亚派": "古希腊哲学", "前苏格拉底": "古希腊哲学",
        "古代哲学": "古希腊哲学", "犬儒学派": "古希腊哲学", "自然哲学": "古希腊哲学",
        "新柏拉图主义": "古希腊哲学", "折衷主义": "古希腊哲学", "元素论": "古希腊哲学",
        "斯多葛派": "斯多葛学派", "斯多葛主义": "斯多葛学派", "晚期斯多亚": "斯多葛学派",
        "批判哲学": "德国古典哲学", "德国唯心论": "德国古典哲学", "唯意志论": "德国古典哲学",
        "交往理论": "法兰克福学派", "文化批评": "法兰克福学派",
        "法兰克福学派（批判理论）": "法兰克福学派",
        "启蒙哲学": "启蒙运动", "启蒙思想": "启蒙运动", "苏格兰启蒙": "启蒙运动", "人文主义": "启蒙运动",
        "精神分析": "精神分析学", "分析心理学": "精神分析学", "心理治疗": "精神分析学",
        "逻辑原子主义": "分析哲学", "逻辑实用主义": "分析哲学",
        "逻辑实证": "分析哲学", "日常语言": "分析哲学", "语言哲学": "分析哲学",
        "形式社会学": "社会学", "社会心理学": "社会学", "群体心理学": "社会学", "社会达尔文": "社会学",
        "激进平等": "政治哲学", "责任伦理": "政治哲学", "社会契约论": "政治哲学", "古典经济学": "政治哲学",
        "德性伦理": "伦理学", "批判理性主义": "科学哲学",
        "解释学": "现象学", "身体哲学": "现象学", "意向性": "现象学",
        "常识实在论": "实在论", "人本唯物论": "实在论", "机械唯物主义": "实在论",
        "结构语言学": "结构主义", "进步教育": "实用主义", "新实用主义": "实用主义",
        "荒诞文学": "荒诞哲学", "浪漫主义先驱": "浪漫主义",
        "近代哲学之父": "近代哲学", "有机体哲学": "过程哲学",
        "后现代哲学": "后现代主义", "解构主义": "后现代主义",
        # 新增合并
        "宗教社会学": "社会学", "政治经济学": "政治哲学",
        "现实主义政治哲学": "政治哲学", "文艺复兴人文主义": "启蒙运动",
        "逻辑实证主义": "实证主义", "绝对唯心主义": "唯心主义",
        "历史唯物主义": "马克思主义", "结构马克思主义": "马克思主义",
        "悲观主义哲学": "德国古典哲学", "文化霸权理论": "西方马克思主义",
    }
    return merge_map.get(tag, tag)

def _expand_tags(tag):
    """Expand a tag for FILTER MATCHING. Each tag maps to itself + all its
    merged/expanded parents (used by both merge_map and multi_map logic)."""
    tag = tag.strip()
    # Start with the tag itself
    result = [tag]
    # Add the display-merged parent (from merge_map)
    display_parent = _normalize_tag(tag)
    if display_parent != tag and display_parent not in result:
        result.append(display_parent)
    # Add any multi-tag expansions
    multi_map = {
        "结构马克思主义": ["马克思主义", "结构主义"],
        "政治经济学": ["政治哲学", "社会学"],
        "宗教社会学": ["社会学", "宗教哲学"],
        "逻辑实证主义": ["实证主义", "分析哲学"],
        "现实主义政治哲学": ["政治哲学"],
        "文艺复兴人文主义": ["启蒙运动"],
        "绝对唯心主义": ["唯心主义"],
        "历史唯物主义": ["马克思主义"],
        "后现代哲学": ["后现代主义"],
        "解构主义": ["后现代主义"],
    }
    extras = multi_map.get(tag, [])
    for t in extras:
        if t not in result:
            result.append(t)
    return result

def _era_to_century(era_str):
    """Convert era string to century: '约前624-前546' -> '公元前7世纪'"""
    import re
    if not era_str or era_str in ("-", "未知", ""):
        return None
    # BCE: 公元前xxx / 约前xxx / 约公元前xxx / 前xxx
    m = re.search(r'(?:公元前|约公元前|约前|前)\s*(\d+)', era_str)
    if m:
        year = int(m.group(1))
        return f'公元前{(year + 99) // 100}世纪'
    # CE: find the first 3-4 digit number as birth year
    m = re.search(r'(?<!\d)(\d{3,4})', era_str)
    if m:
        year = int(m.group(1))
        century = (year + 99) // 100 if year < 1000 else (year - 1) // 100 + 1
        return f'{century}世纪'
    return None

@app.get("/api/authors/filters")
async def get_author_filters():
    """获取作者多维度筛选选项（按世纪分组）"""
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
                century = _era_to_century(info["era"])
                if century:
                    eras.add(century)
            if info.get("country"):
                cnt_map = {"苏格兰":"英国","英格兰":"英国","罗马帝国":"古罗马","北非":"古罗马","奥匈帝国（捷克）":"捷克","俄国":"俄罗斯"}
                for c in re.split(r'[/,、，;；]', info["country"]):
                    c = c.strip()
                    c = cnt_map.get(c, c)
                    if c: countries.add(c)
            if info.get("school"):
                for tag in re.split(r'[/,、，;；]', info["school"]):
                    tag = tag.strip()
                    if tag:
                        schools.add(_normalize_tag(tag))

    def _century_sort_key(c):
        """Sort centuries: 公元前 first (descending), then CE (ascending)"""
        import re
        m_bce = re.match(r'公元前(\d+)世纪', c)
        if m_bce:
            return (-int(m_bce.group(1)), 0)  # negative so -5 before -4
        m_ce = re.match(r'(\d+)世纪', c)
        if m_ce:
            return (0, int(m_ce.group(1)))  # positive after BCE
        return (1, 0)

    # Sort schools by historical influence (rough ranking)
    _school_rank = {
        "古希腊哲学": 1, "启蒙运动": 2, "德国古典哲学": 3, "经验主义": 4,
        "理性主义": 5, "马克思主义": 6, "存在主义": 7, "现象学": 8,
        "分析哲学": 9, "实用主义": 10, "自由主义": 11, "政治哲学": 12,
        "伦理学": 13, "科学哲学": 14, "斯多葛学派": 15, "怀疑论": 16,
        "经院哲学": 17, "浪漫主义": 18, "宗教哲学": 19, "荒诞哲学": 20,
        "结构主义": 21, "后现代主义": 22, "精神分析学": 23, "法兰克福学派": 24,
        "生命哲学": 25, "功利主义": 26, "实证主义": 27, "实在论": 28,
        "唯心主义": 29, "历史唯物主义": 30, "后结构主义": 31, "过程哲学": 32,
        "哲学诠释学": 33, "技术哲学": 34, "社会学": 35, "女性主义": 36,
        "超验主义": 37, "教父哲学": 38, "托马斯主义": 39, "绝对唯心主义": 40,
        "唯名论": 41, "近代哲学": 42, "社群主义": 43, "基督教哲学": 44,
        "悲观主义哲学": 45,
    }
    def _school_sort_key(s):
        return _school_rank.get(s, 100)

    from starlette.responses import JSONResponse as StarletteJSON3
    return StarletteJSON3({
        "eras": sorted(eras, key=_century_sort_key),
        "countries": sorted(countries),
        "schools": sorted(schools, key=_school_sort_key),
    }, headers={"Cache-Control": "public, max-age=300"})

@app.get("/api/authors/{author_name}")
async def get_author_info(author_name: str):
    """获取作者详细信息（内置库 + 百度百科爬虫）"""
    books = scan_books()
    author_books = [
        b for b in books
        if b["author"] == author_name or author_name in b["author"]
    ]

    region = author_books[0]["region"] if author_books else "未知"
    book_list = [{"id": b["id"], "title": b["title"], "file_type": b["file_type"]} for b in author_books]
    book_count = len(book_list)

    # 1. 先从内置数据库获取
    info = get_philosopher_info(author_name)

    def build_response(source, era="", country="", school="", bio="", wiki_url=None):
        return {
            "name": author_name,
            "region": region,
            "era": era,
            "country": country,
            "school": school,
            "bio": bio,
            "wiki_url": wiki_url or f"https://en.wikipedia.org/wiki/{author_name}",
            "books": book_list,
            "book_count": book_count,
            "source": source,
        }

    if info:
        return build_response(
            "builtin_database",
            era=info.get("era", ""),
            country=info.get("country", ""),
            school=info.get("school", ""),
            bio=info.get("bio", ""),
            wiki_url=info.get("wiki_url"),
        )

    # 2. 尝试从百度百科爬取
    scraped = scrape_baidu_baike(author_name)
    if scraped:
        return build_response(
            "baidu_baike",
            bio=scraped["bio"],
            wiki_url=scraped.get("wiki_url"),
        )

    # 3. 兜底
    book_titles = [b["title"] for b in author_books]
    return build_response(
        "fallback",
        bio=f"{author_name}是{region}哲学史上的重要思想家。著有{'、'.join(book_titles[:5])}等作品。",
    )


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
        if b["title"] not in authors_map[author]["books"] and "待收录" not in b["title"]:
            authors_map[author]["books"].append(b["title"])

    # 补入只有空目录没有著作的哲学家
    knowledge_dir = config.KNOWLEDGE_DIR
    for region_name in ["东方", "西方"]:
        region_path = os.path.join(knowledge_dir, region_name)
        if not os.path.isdir(region_path):
            continue
        for author_dir in os.listdir(region_path):
            author_full = os.path.join(region_path, author_dir)
            if not os.path.isdir(author_full):
                continue
            author_clean = author_dir.replace("###合集&概述###", "合集&概述")
            if not is_valid_author(author_clean):
                continue
            if author_clean in authors_map:
                continue
            info = get_philosopher_info(author_clean)
            authors_map[author_clean] = {
                "name": author_clean,
                "region": region_name,
                "books": [],
                "era": info.get("era", "") if info else "",
                "country": info.get("country", "") if info else "",
                "school": info.get("school", "") if info else "",
            }
    # 云端兜底：GitHub/R2 模式下书香目录为空，用硬编码的16位空目录作者列表
    if config.USE_GITHUB or config.USE_R2:
        from philosophers_db import EMPTY_DIR_AUTHORS
        for author_clean in EMPTY_DIR_AUTHORS:
            if author_clean in authors_map:
                continue
            info = get_philosopher_info(author_clean)
            authors_map[author_clean] = {
                "name": author_clean,
                "region": "西方",
                "books": [],
                "era": info.get("era", "") if info else "",
                "country": info.get("country", "") if info else "",
                "school": info.get("school", "") if info else "",
            }

    # 补入哲学家数据库中所有未在作者列表中出现的人物（星丛补全后共355位）
    from philosophers_db import PHILOSOPHERS
    for ph_name, ph_info in PHILOSOPHERS.items():
        if ph_name in authors_map:
            continue
        # 检查别名是否有匹配
        matched = False
        from philosophers_db import NAME_ALIASES
        for alias, target in NAME_ALIASES.items():
            if alias in authors_map:
                matched = True
                break
            if target == ph_name and alias not in authors_map:
                pass  # alias not in authors either
        if matched:
            continue
        # 添加到作者列表
        authors_map[ph_name] = {
            "name": ph_name,
            "region": "东方" if any(kw in (ph_info.get("school", "") + ph_info.get("country", ""))
                                    for kw in ["中国", "儒家", "道家", "墨家", "法家", "兵家", "宋明", "魏晋", "禅", "佛"]) else "西方",
            "books": [],
            "era": ph_info.get("era", ""),
            "country": ph_info.get("country", ""),
            "school": ph_info.get("school", ""),
        }

    result = []
    for name, info in authors_map.items():
        century = _era_to_century(info.get("era", "")) if info.get("era") else ""
        entry = {
            "name": name,
            "region": info["region"],
            "book_count": len(info["books"]),
            "books": info["books"][:10],
            "era": info["era"],
            "century": century,
            "country": info["country"],
            "school": info["school"],
        }
        # 多标签筛选（逗号分隔，AND逻辑，流派/国家/时代/世纪）
        if tag:
            raw_school = info.get("school") or ""
            expanded_schools = [t for s in re.split(r'[/,、，;；]', raw_school) if s.strip() for t in _expand_tags(s.strip())]
            raw_country = info.get("country") or ""
            cnt_map = {"苏格兰":"英国","英格兰":"英国","罗马帝国":"古罗马","北非":"古罗马","奥匈帝国（捷克）":"捷克","俄国":"俄罗斯"}
            norm_countries = set()
            for c in re.split(r'[/,、，;；]', raw_country):
                c = c.strip()
                c = cnt_map.get(c, c)
                if c: norm_countries.add(c)
            # All tags must match (AND logic)
            all_match = True
            for t in tag.split(","):
                t = t.strip()
                if not t: continue
                if t in raw_school or t in expanded_schools: continue
                if t in raw_country or t in norm_countries: continue
                if t == info.get("era", "") or t == (century or ""): continue
                all_match = False
                break
            if not all_match:
                continue
        result.append(entry)

    from starlette.responses import JSONResponse as StarletteJSON2
    return StarletteJSON2(
        {"authors": sorted(result, key=lambda a: (_author_sort_key(a["name"]), a["region"], a["name"]))},
        headers={"Cache-Control": "public, max-age=300"},
    )


def _author_sort_key(author_name: str) -> int:
    """作者排序权重：合集=最前，按出生年份升序"""
    if "合集" in author_name or "概述" in author_name:
        return -99999
    info = get_philosopher_info(author_name)
    if info and info.get("era"):
        import re
        m = re.search(r'(\d+)', info["era"])
        if m:
            year = int(m.group(1))
            if "公元前" in info["era"] or "前" in info["era"]:
                year = -year
            return year
    return 9999


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
async def api_profile(user: dict = Depends(auth_required)):
    """获取用户信息"""
    return {"username": user["username"], "id": user["id"]}


# ============================================================
# 阅读历史 API
# ============================================================

@app.post("/api/history/reading")
async def save_reading(req: ReadingProgressRequest,
                       user: dict = Depends(auth_required)):
    """保存阅读进度"""
    save_reading_progress(
        user["id"], req.book_id, req.book_title,
        req.book_author, req.page, req.percent,
    )
    return {"success": True}


@app.get("/api/history/reading")
async def get_reading(user: dict = Depends(auth_required)):
    """获取阅读历史"""
    return {"history": get_reading_history(user["id"])}


# ============================================================
# 聊天历史 API
# ============================================================

@app.post("/api/history/chat")
async def save_chat(req: ChatMessageRequest,
                    user: dict = Depends(auth_required)):
    """保存聊天消息"""
    save_chat_message(user["id"], req.role, req.content, req.sources)
    return {"success": True}


@app.get("/api/history/chat")
async def get_chat(user: dict = Depends(auth_required)):
    """获取聊天历史"""
    return {"messages": get_chat_history(user["id"])}


@app.delete("/api/history/chat")
async def clear_chat(user: dict = Depends(auth_required)):
    """清空聊天历史"""
    clear_chat_history(user["id"])
    return {"success": True}


# ============================================================
# 批注笔记 API
# ============================================================

class NoteRequest(BaseModel):
    book_id: str
    note_text: str = ""

@app.post("/api/notes/save")
async def api_save_note(req: NoteRequest,
                       user: dict = Depends(auth_required)):
    save_book_note(user["id"], req.book_id, req.note_text)
    return {"success": True}

@app.get("/api/notes/{book_id}")
async def api_get_note(book_id: str,
                      user: dict = Depends(auth_required)):
    return {"note_text": get_book_note(user["id"], book_id)}

@app.get("/api/notes")
async def api_get_all_notes(user: dict = Depends(auth_required)):
    return {"notes": get_all_book_notes(user["id"])}


# ============================================================
# 书内 AI 对话 API
# ============================================================

class BookChatRequest(BaseModel):
    book_id: str
    role: str
    content: str

@app.post("/api/book-chat/save")
async def api_save_book_chat(req: BookChatRequest,
                            user: dict = Depends(auth_required)):
    save_book_chat(user["id"], req.book_id, req.role, req.content)
    return {"success": True}

@app.get("/api/book-chat/{book_id}")
async def api_get_book_chat(book_id: str,
                           user: dict = Depends(auth_required)):
    return {"messages": get_book_chat(user["id"], book_id)}

@app.delete("/api/book-chat/{book_id}")
async def api_clear_book_chat(book_id: str,
                             user: dict = Depends(auth_required)):
    clear_book_chat(user["id"], book_id)
    return {"success": True}


# ============================================================
# AI 流式代理 — 无用户Key时用服务器Key
# ============================================================

@app.post("/api/ai/stream")
async def ai_stream_proxy(req: Request):
    """流式代理 DeepSeek API，使用服务器默认 Key"""
    from openai import OpenAI
    key = config.DEEPSEEK_API_KEY
    if not key:
        return JSONResponse({"error": "Server API key not configured"}, status_code=500)

    body = await req.json()
    client = OpenAI(api_key=key, base_url=config.DEEPSEEK_BASE_URL)

    def generate():
        try:
            stream = client.chat.completions.create(
                model=body.get("model", config.DEEPSEEK_MODEL),
                messages=body.get("messages", []),
                temperature=body.get("temperature", 0.7),
                max_tokens=body.get("max_tokens", 1024),
                stream=True,
            )
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield f"data: {json.dumps({'choices':[{'delta':{'content': chunk.choices[0].delta.content}}]})}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache"},
    )

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

        kb_ready = store.get_collection_stats()["chunk_count"] > 0

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

        if kb_ready:
            rag = RAGChain(vector_store=store, llm_client=llm)
            result = rag.query(req.question)
        else:
            # No knowledge base - direct LLM Q&A
            try:
                answer = llm.chat(messages=[
                    {"role": "system", "content": "你是一个哲学知识助手。请用中文回答用户的问题，尽可能准确和详细。如果不知道，请如实说明。"},
                    {"role": "user", "content": req.question},
                ])
                result = {"answer": answer, "sources": [], "question": req.question}
            except Exception as e:
                result = {"answer": f"问答服务暂不可用: {e}\n\n请确认已在设置中配置了有效的 API Key。", "sources": [], "question": req.question}

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

    # Check if uploading to vectordb (special path)
    if safe_name.startswith("vectordb/"):
        base = config.CHROMA_PERSIST_DIR
        safe_name = safe_name[len("vectordb/"):]
    else:
        base = config.KNOWLEDGE_DIR

    target_path = os.path.join(base, safe_name)
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


# ============================================================
# 静态前端（同源部署，须在 API 路由之后注册）
# ============================================================
import os as _os2
_STATIC_DIR = _os2.path.join(_os2.path.dirname(__file__), "static")
if _os2.path.isdir(_STATIC_DIR) and _os2.path.isfile(_os2.path.join(_STATIC_DIR, "index.html")):
    # 先挂 assets，再挂根路由
    app.mount("/assets", StaticFiles(directory=_os2.path.join(_STATIC_DIR, "assets")), name="spa_assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """SPA fallback: 非 API 路径返回 index.html"""
        fp = _os2.path.join(_STATIC_DIR, full_path) if full_path else _os2.path.join(_STATIC_DIR, "index.html")
        if _os2.path.isfile(fp):
            return FileResponse(fp)
        return FileResponse(_os2.path.join(_STATIC_DIR, "index.html"))

    @app.get("/")
    async def serve_index():
        return FileResponse(_os2.path.join(_STATIC_DIR, "index.html"))


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
    # Pre-compute keywords in background (will be cached after first run)
    if not os.path.exists(_BOOKS_CACHE_PATH):
        _build_and_cache_keywords()
    print("=" * 50)
    uvicorn.run(app, host=config.SERVER_HOST, port=config.SERVER_PORT)
# force redeploy Sun Jun 14 18:39:51     2026
