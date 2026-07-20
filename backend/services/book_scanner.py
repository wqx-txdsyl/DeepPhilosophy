"""
Book scanner service — unified interface for local/OSS/GitHub/R2 storage backends.
Extracted from main.py on 2026-07-11.
"""
import os, json, hashlib, time, urllib.request
from pathlib import Path
from datetime import datetime
from loguru import logger
import config
from db import get_philosopher_info
from services.summaries import load_summaries_cache, classify_book, book_sort_key

_r2_client = None
_BOOKS_CACHE_LIST = None
_BOOKS_CACHE_TIME = 0
_BOOKS_CACHE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "books_cache.json")
TITLE_FIXES = {"SZ": "S/Z"}
SKIP_AUTHORS = {"合集&概述", "合集", "概述", "其他"}
NON_PERSON_ENTRIES = {"净土宗","禅宗","天台宗","华严宗","唯识宗","密宗","律宗","三论宗","耆那教","琐罗亚斯德教","摩尼教","古文经学","今文经学","犬儒学派","斯多葛学派","伊壁鸠鲁学派","怀疑论","新柏拉图主义","米利都学派","埃利亚学派","智者学派"}

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

            region = parts[0] if len(parts) > 0 else "西方"
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


def _normalize_books(raw_books):
    """Shared post-processing: tag merging + summary appending + sorting"""
    kw_cache = {}
    if os.path.exists(_BOOKS_CACHE_PATH):
        try:
            with open(_BOOKS_CACHE_PATH, "r", encoding="utf-8") as f:
                kw_cache = json.load(f)
        except Exception:
            pass
    summary_cache = load_summaries_cache()
    for b in raw_books:
        key = b["title"] + "||" + b["author"]
        b["keywords"] = kw_cache.get(key, [])
        if key in summary_cache and summary_cache[key].get("tags"):
            for t in summary_cache[key]["tags"]:
                if t not in b.get("tags", []):
                    b.setdefault("tags", []).append(t)
    return sorted(raw_books, key=lambda b: (book_sort_key(b), b["region"], b["author"], b["title"]))

def is_valid_author(name: str) -> bool:
    """过滤非人物条目"""
    if name in NON_PERSON_ENTRIES:
        return False
    for skip in SKIP_AUTHORS:
        if skip in name:
            return False
    # 书名号通常表示这是一本书而非作者
    if name.startswith("《") and name.endswith("》"):
        return False
    return True

def scan_books(force=False) -> list[dict]:
    """扫描书籍目录 —— 自动切换本地 / OSS / R2 / GitHub（带缓存）"""
    global _BOOKS_CACHE_LIST, _BOOKS_CACHE_TIME
    now = time.time()
    if not force and _BOOKS_CACHE_LIST is not None and (now - _BOOKS_CACHE_TIME) < 300:
        return _BOOKS_CACHE_LIST
    if config.USE_OSS:
        _BOOKS_CACHE_LIST = _scan_books_oss()
    elif config.USE_GITHUB:
        _BOOKS_CACHE_LIST = _scan_books_github()
    elif config.USE_R2:
        _BOOKS_CACHE_LIST = _scan_books_r2()
    else:
        _BOOKS_CACHE_LIST = _scan_books_local()
    _BOOKS_CACHE_TIME = now
    return _BOOKS_CACHE_LIST

