"""附件上传 API 路由 — md 直读 / markitdown 转 md / Agnes 识图（智谱 glm-4v-flash 兜底）
从 main.py 拆分（2026-08-15）; 2026-08-30 增加智谱免费视觉兜底（Agnes 需代理, 失败时直连智谱）
"""
import os, json, time, urllib.request, asyncio, tempfile
import logging
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Depends
from fastapi.responses import JSONResponse

import guard

logger = logging.getLogger("routes.upload")  # S25: 错误详情只写服务端日志，不原样回传

router = APIRouter()

_VISION_PROMPT = "请详细描述这张图片的内容（哲学/文字/图表场景: 提取其中的文字与要点）"
_GENERAL_VISION_PROMPT = (
    "只提取图片中实际可见的文字与信息，保留数字、人物标记和图表关系。"
    "先准确转录文字，再简短描述有助于理解这些文字的可见布局。"
    "无法辨认的内容明确标记，不猜测。不要引申哲学意义、文化典故、作者意图或相关联想；"
    "这些不是图片本身提供的材料。不要使用emoji。")


def _zhipu_vision(image_bytes: bytes, prompt: str = _VISION_PROMPT, mime_type="image/jpeg") -> Optional[str]:
    """智谱 glm-4v-flash 视觉识图（免费, 国内直连无需代理）——图片经 base64 传入"""
    import base64 as _b64
    api_key = os.environ.get("ZHIPU_API_KEY", "")
    if not api_key:
        return None
    body = {"model": "glm-4v-flash", "messages": [{"role": "user", "content": [
        {"type": "text", "text": prompt},
        {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64," + _b64.b64encode(image_bytes).decode()}},
    ]}], "max_tokens": 1500}
    req = urllib.request.Request("https://open.bigmodel.cn/api/paas/v4/chat/completions",
                                 data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json",
                                          "Authorization": f"Bearer {api_key}"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            resp = json.loads(r.read().decode())
        return (resp.get("choices") or [{}])[0].get("message", {}).get("content") or None
    except Exception as e:
        logger.warning("智谱识图失败: %s", e)
        return None


def _agnes_vision(image_bytes: bytes, prompt: str = _VISION_PROMPT, mime_type="image/jpeg") -> Optional[str]:
    """Agnes 视觉识图（agnes-2.5-flash, 免费, 需网络代理）——智谱不可用时的兜底"""
    import base64 as _b64
    api_key = os.environ.get("AGNES_API_KEY", "")
    if not api_key:
        return None
    body = {"model": "agnes-2.5-flash", "messages": [{"role": "user", "content": [
        {"type": "text", "text": prompt},
        {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64," + _b64.b64encode(image_bytes).decode()}},
    ]}], "max_tokens": 1500}
    req = urllib.request.Request("https://apihub.agnes-ai.com/v1/chat/completions",
                                 data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json",
                                          "Authorization": f"Bearer {api_key}"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:   # 走系统代理（Agnes 需代理）
            resp = json.loads(r.read().decode())
        return (resp.get("choices") or [{}])[0].get("message", {}).get("content") or None
    except Exception:
        return None


@router.post("/api/upload")
async def api_upload(file: UploadFile = File(...), _g: dict = Depends(guard.upload_guard)):
    """上传附件 → 文本内容（供对话上下文使用）
    .md/.txt → 直接读; 其他文档 → markitdown 转 md; 图片 → Agnes 识图（智谱兜底）
    加固: 限流（guard.upload_guard）+ 文件名消毒（防路径穿越写临时目录）"""
    try:
        fname = Path(file.filename or "attachment").name   # 消毒: 仅取文件名, 剥路径分隔符
        ext = Path(fname).suffix.lower()
        raw = await file.read()
        max_bytes = 20 * 1024 * 1024
        if len(raw) > max_bytes:
            return JSONResponse({"error": "文件超过 20MB 限制"}, status_code=413)
        # 1) md/txt 直读
        if ext in (".md", ".txt", ".markdown"):
            text = raw.decode("utf-8", errors="replace")
            return {"filename": fname, "kind": "md", "content": text[:20000],
                    "truncated": len(text) > 20000}
        # 2) 图片 → Agnes 视觉识图（智谱 glm-4v-flash 兜底）
        if ext in (".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"):
            desc = _agnes_vision(raw) or _zhipu_vision(raw)
            if desc is None:
                return JSONResponse({"error": "识图失败，请稍后重试"}, status_code=502)
            return {"filename": fname, "kind": "image", "content": desc, "truncated": False}
        # 3) 其他文档 → markitdown 转 md
        try:
            from markitdown import MarkItDown
            tmp = Path(os.environ.get("TEMP", ".")) / f"dp_upload_{int(time.time())}_{fname}"
            tmp.write_bytes(raw)
            try:
                result = MarkItDown().convert(str(tmp))
                text = result.text_content or ""
            finally:
                tmp.unlink(missing_ok=True)
            if not text.strip():
                return JSONResponse({"error": "文档转换后无内容（格式不支持）"}, status_code=400)
            return {"filename": fname, "kind": "md", "content": text[:20000],
                    "truncated": len(text) > 20000}
        except Exception as e:
            logger.warning("文档转换失败: %s", e)
            return JSONResponse({"error": "文档转换失败，请检查文件格式"}, status_code=400)
    except Exception as e:
        logger.warning("上传处理失败: %s", e)
        return JSONResponse({"error": "上传处理失败，请稍后重试"}, status_code=400)


def _convert_general_attachment(raw, filename, ext):
    """Conversion runs outside the event loop, with an isolated temporary file."""
    if ext in {".txt", ".md", ".markdown", ".csv"}:
        text = raw.decode("utf-8-sig", errors="replace")
        kind = "md"
    elif ext in {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"}:
        import io
        from PIL import Image, UnidentifiedImageError
        try:
            with Image.open(io.BytesIO(raw)) as picture:
                mime = Image.MIME.get(picture.format)
                if picture.format not in {"PNG", "JPEG", "WEBP", "GIF", "BMP"}:
                    raise ValueError("不支持此图片格式")
                picture.verify()
        except (UnidentifiedImageError, OSError):
            raise ValueError("图片内容损坏或与图片格式不符") from None
        text = (_agnes_vision(raw, prompt=_GENERAL_VISION_PROMPT, mime_type=mime)
                or _zhipu_vision(raw, prompt=_GENERAL_VISION_PROMPT, mime_type=mime))
        if not text:
            raise ValueError("识图失败，请稍后重试")
        kind = "image"
    else:
        from markitdown import MarkItDown
        with tempfile.TemporaryDirectory(prefix="deep_attachment_") as tmp:
            path = Path(tmp) / ("attachment" + ext)
            path.write_bytes(raw)
            text = MarkItDown().convert(str(path)).text_content or ""
        kind = "md"
    if not text.strip():
        raise ValueError("附件中没有可读取的文字")
    return {"filename": filename, "kind": kind, "content": text[:20000],
            "truncated": len(text) > 20000, "extracted_chars": len(text)}


@router.post("/api/agent/upload")
async def general_agent_upload(file: UploadFile = File(...), _g: dict = Depends(guard.upload_guard)):
    """General-agent attachment ingestion; leave the persona upload path unchanged."""
    filename = Path((file.filename or "attachment").replace("\\", "/")).name
    ext = Path(filename).suffix.lower()
    if ext not in {".txt", ".md", ".markdown", ".csv", ".pdf", ".docx", ".pptx", ".xlsx",
                   ".html", ".htm", ".epub", ".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"}:
        await file.close()
        return JSONResponse({"error": "不支持此附件格式，请使用文本、文档或图片"}, status_code=415)
    try:
        raw = await file.read(20 * 1024 * 1024 + 1)
        if len(raw) > 20 * 1024 * 1024:
            return JSONResponse({"error": "文件超过 20MB 限制"}, status_code=413)
        if not raw:
            return JSONResponse({"error": "附件为空"}, status_code=400)
        return await asyncio.to_thread(_convert_general_attachment, raw, filename, ext)
    except ValueError as exc:
        return JSONResponse({"error": str(exc)}, status_code=422)
    except Exception:
        logger.exception("General agent attachment conversion failed")
        return JSONResponse({"error": "附件读取失败，请检查文件格式或稍后重试"}, status_code=422)
    finally:
        await file.close()
