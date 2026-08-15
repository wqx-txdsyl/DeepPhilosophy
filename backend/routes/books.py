"""书籍 API 路由 — 列表/标签/详情/render/图片/下载
从 main.py 拆分（2026-08-15），复用 services.book_scanner / services.summaries 权威实现
"""
import os, json, hashlib, urllib.request
from pathlib import Path
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import FileResponse, Response
from starlette.responses import JSONResponse as StarletteJSON
from starlette.responses import RedirectResponse as StarletteRedirect

import config
from services.book_scanner import scan_books
from services.summaries import load_summaries_cache, generate_summary

router = APIRouter()


def _normalize_book_summary(b: dict) -> dict:
    """附加摘要字段（纯缓存，瞬间返回）"""
    b = dict(b)
    b["summary"] = generate_summary(b)
    return b


@router.get("/api/books")
async def list_books(
    region: str | None = Query(None),
    author: str | None = Query(None),
    tag: str | None = Query(None),
    status: str | None = Query(None),
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
    summaries_cache = load_summaries_cache()
    for b in books:
        key = f"{b['title']}||{b.get('author', '')}"
        cached = summaries_cache.get(key, {})
        if cached.get("tags"):
            b["tags"] = cached["tags"]

    all_tags = sorted(set(t for b in books for t in b.get("tags", [])))

    # 允许浏览器缓存 5 分钟（减少重复加载）
    return StarletteJSON(
        {"books": books, "total": len(books), "tags": all_tags},
        headers={"Cache-Control": "public, max-age=300"},
    )


@router.get("/api/books/tags")
async def list_tags():
    """获取所有分类标签"""
    books = scan_books()
    tags_count = {}
    for b in books:
        for t in b.get("tags", []):
            tags_count[t] = tags_count.get(t, 0) + 1
    return {"tags": sorted(tags_count.items(), key=lambda x: -x[1])}


@router.get("/api/books/{book_id}")
async def get_book(book_id: str):
    """获取单本书籍详情（含摘要和关键词）"""
    books = scan_books()
    for b in books:
        if b["id"] == book_id:
            b["summary"] = generate_summary(b)
            b["keywords"] = b.get("keywords", [])
            return b
    raise HTTPException(status_code=404, detail="书籍未找到")


@router.get("/api/books/{book_id}/render")
async def render_epub_chapter(book_id: str, chapter: int = Query(0)):
    """将 EPUB 章节渲染为分页 HTML"""
    import ebooklib
    from ebooklib import epub
    from bs4 import BeautifulSoup

    books = scan_books()
    book = next((b for b in books if b["id"] == book_id), None)
    if not book or book["file_type"] != "epub":
        raise HTTPException(status_code=404, detail="仅支持 EPUB")

    # Resolve file location
    if config.USE_OSS and "_download_url" in book:
        req = urllib.request.Request(book["_download_url"], headers={"User-Agent": "DeepPhilosophy/1.0"})
        with urllib.request.urlopen(req, timeout=30) as src:
            raw = src.read()
        import tempfile
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".epub")
        tmp.write(raw); tmp.close()
        eb = epub.read_epub(tmp.name)
        os.unlink(tmp.name)
    elif config.USE_GITHUB and "_download_url" in book:
        req = urllib.request.Request(book["_download_url"], headers={"User-Agent": "DeepPhilosophy/1.0"})
        with urllib.request.urlopen(req, timeout=30) as src:
            raw = src.read()
        import tempfile
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".epub")
        tmp.write(raw); tmp.close()
        eb = epub.read_epub(tmp.name)
        os.unlink(tmp.name)
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
    page_html = ""
    if body:
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


@router.get("/api/books/{book_id}/file")
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
        return StarletteRedirect(url=book["_download_url"], status_code=302)

    # GitHub 模式：代理下载（支持 Range 按需取块）
    if config.USE_GITHUB and "_download_url" in book:
        gh_url = book["_download_url"]
        ext = Path(gh_url).suffix.lower()
        mime_map = {".pdf": "application/pdf", ".epub": "application/epub+zip", ".txt": "text/plain", ".md": "text/markdown"}
        mime = mime_map.get(ext, "application/octet-stream")
        range_header = request.headers.get("range", "")

        try:
            if range_header:
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
        from services.book_scanner import _get_r2_client
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
