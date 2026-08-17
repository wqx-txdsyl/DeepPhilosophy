"""文本提取 API — 借鉴番茄小说：提取纯文本 + 章节索引 + 字符偏移"""
import os, json, re, zipfile
from pathlib import Path
from html.parser import HTMLParser
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse, FileResponse, Response
from loguru import logger
import config

router = APIRouter()
IMG_EXTS = {'.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.gif': 'image/gif', '.webp': 'image/webp', '.svg': 'image/svg+xml', '.bmp': 'image/bmp'}

# 路径参数白名单（审计 S2 加固: 防路径穿越任意文件读取, 与 workers/api 图片名规则一致）
# 仅允许 [A-Za-z0-9_.-]（不含路径分隔符）; "." / ".." 显式拒绝
_NAME_RE = re.compile(r"^[A-Za-z0-9_.-]+$")


def _safe_name(name: str) -> bool:
    """路径参数白名单: 仅字母数字 _ . -; 不含 / \\ 与空串; 拒绝 . .."""
    return bool(name) and name not in (".", "..") and bool(_NAME_RE.match(name))


def _safe_join(base_dir: str, *parts: str):
    """白名单拼接 + abspath/startswith 双保险: 解析后必须位于 base_dir 内, 否则返回 None"""
    if any(not _safe_name(p) for p in parts):
        return None
    base = os.path.abspath(base_dir)
    joined = os.path.abspath(os.path.join(base, *parts))
    if joined != base and not joined.startswith(base + os.sep):
        return None
    return joined

@router.get("/api/books/{book_id}/detail")
async def get_book_detail(book_id: str):
    """获取书籍详情 — 静态数据可缓存 1 小时"""
    import urllib.request
    # 本地优先
    dd = os.path.join(os.path.dirname(__file__), "..", "data", "book_detail")
    lp = _safe_join(dd, f"{book_id}.json")
    if lp is None:
        raise HTTPException(status_code=400, detail="非法的 book_id")
    headers = {"Cache-Control": "public, max-age=3600"}
    if os.path.exists(lp):
        with open(lp, 'r', encoding='utf-8') as f:
            return JSONResponse(content=json.load(f), headers=headers)
    # OSS
    if config.USE_OSS:
        url = f"https://{config.OSS_BUCKET_HOST}/book_detail/{book_id}.json"
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=8) as resp:
                if resp.status == 200:
                    return JSONResponse(content=json.loads(resp.read().decode('utf-8')), headers=headers)
        except Exception as e:
            logger.debug(f"OSS detail 兜底失败 {book_id}: {e}")
    raise HTTPException(status_code=404, detail="详情未找到")


@router.get("/api/books/{book_id}/chapter/{ch}")
async def get_book_chapter(book_id: str, ch: int):
    """获取单章内容（<200KB，按需秒加载）"""
    import urllib.request
    # 本地优先
    cd_root = os.path.join(os.path.dirname(__file__), "..", "data", "book_chapters")
    lp = _safe_join(cd_root, book_id, f"{ch}.json")
    if lp is None:
        raise HTTPException(status_code=400, detail="非法的 book_id")
    if os.path.exists(lp):
        with open(lp, 'r', encoding='utf-8') as f: return json.load(f)
    # OSS
    if config.USE_OSS:
        url = f"https://{config.OSS_BUCKET_HOST}/book_chapters/{book_id}/{ch}.json"
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=8) as resp:
                if resp.status == 200: return json.loads(resp.read().decode('utf-8'))
        except Exception as e:
            logger.debug(f"OSS chapter 兜底失败 {book_id}/{ch}: {e}")
    raise HTTPException(status_code=404, detail="章节未找到")


@router.get("/api/books/{book_id}/text")
async def get_book_text(book_id: str, meta: str = "", chapter: str = ""):
    """获取预构建的书籍JSON。?meta=1 仅返回元数据(快速), ?chapter=N 仅返回第N章"""
    import urllib.request

    # 加载完整 JSON（本地优先，OSS兜底）
    data = None
    json_dir = os.path.join(os.path.dirname(__file__), "..", "data", "book_json")
    json_path = _safe_join(json_dir, f"{book_id}.json")
    if json_path is None:
        raise HTTPException(status_code=400, detail="非法的 book_id")
    if os.path.exists(json_path) and os.path.getsize(json_path) > 100:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    if not data and config.USE_OSS:
        oss_url = f"https://{config.OSS_BUCKET_HOST}/book_json/{book_id}.json"
        try:
            req = urllib.request.Request(oss_url)
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode('utf-8'))
        except Exception as e:
            logger.debug(f"OSS book_json 兜底失败 {book_id}: {e}")
    if not data:
        raise HTTPException(status_code=404, detail="书籍数据未找到")

    # ?meta=1 → 仅返回元数据（快速加载，<5KB）
    if meta == "1":
        return {
            "bookId": data.get("bookId", book_id),
            "title": data.get("title", ""),
            "author": data.get("author", ""),
            "cover": data.get("cover"),
            "toc": data.get("toc", []),
            "totalChars": data.get("totalChars", 0),
            "estimatedPages": data.get("estimatedPages", 0),
            "chapterCount": len(data.get("chapters", [])),
            "chapterTitles": [c.get("title", "") for c in data.get("chapters", [])],
        }

    # ?chapter=N → 仅返回第 N 章
    if chapter:
        try:
            idx = int(chapter)
            chs = data.get("chapters", [])
            if 0 <= idx < len(chs):
                return {"chapter": chs[idx], "index": idx, "totalChapters": len(chs)}
            raise HTTPException(status_code=404, detail="章节不存在")
        except ValueError:
            pass

    return data


@router.get("/api/books/{book_id}/image/{img_name}")
async def get_book_image(book_id: str, img_name: str):
    """提供从 EPUB 提取的图片（本地优先，OSS 兜底）—— 带强缓存"""
    import urllib.request
    if not _safe_name(book_id):
        raise HTTPException(status_code=400, detail="非法的 book_id")
    img_dir = os.path.join(os.path.dirname(__file__), "..", "data", "book_images")
    local_path = _safe_join(img_dir, img_name)
    if local_path is None:
        raise HTTPException(status_code=400, detail="非法的 img_name")
    headers = {"Cache-Control": "public, max-age=604800, immutable"}  # 7天强缓存
    if os.path.exists(local_path):
        ext = Path(img_name).suffix.lower()
        mime = IMG_EXTS.get(ext, 'image/png')
        with open(local_path, 'rb') as f:
            return Response(content=f.read(), media_type=mime, headers=headers)
    # OSS 兜底
    if config.USE_OSS:
        oss_url = f"https://{config.OSS_BUCKET_HOST}/book_images/{img_name}"
        try:
            req = urllib.request.Request(oss_url)
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.status == 200:
                    return Response(content=resp.read(), media_type='image/webp', headers=headers)
        except Exception as e:
            logger.debug(f"OSS 图片兜底失败 {img_name}: {e}")
    raise HTTPException(status_code=404, detail="图片未找到")
