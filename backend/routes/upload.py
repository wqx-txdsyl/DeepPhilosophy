"""附件上传 API 路由 — md 直读 / markitdown 转 md / Agnes 识图（智谱 glm-4v-flash 兜底）
从 main.py 拆分（2026-08-15）; 2026-08-30 增加智谱免费视觉兜底（Agnes 需代理, 失败时直连智谱）
"""
import os, json, time, urllib.request
import logging
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Depends
from fastapi.responses import JSONResponse

import guard

logger = logging.getLogger("routes.upload")  # S25: 错误详情只写服务端日志，不原样回传

router = APIRouter()

_VISION_PROMPT = "请详细描述这张图片的内容（哲学/文字/图表场景: 提取其中的文字与要点）"


def _zhipu_vision(image_bytes: bytes, prompt: str = _VISION_PROMPT) -> Optional[str]:
    """智谱 glm-4v-flash 视觉识图（免费, 国内直连无需代理）——图片经 base64 传入"""
    import base64 as _b64
    api_key = os.environ.get("ZHIPU_API_KEY", "")
    if not api_key:
        return None
    body = {"model": "glm-4v-flash", "messages": [{"role": "user", "content": [
        {"type": "text", "text": prompt},
        {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + _b64.b64encode(image_bytes).decode()}},
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


def _agnes_vision(image_bytes: bytes, prompt: str = _VISION_PROMPT) -> Optional[str]:
    """Agnes 视觉识图（agnes-2.5-flash, 免费, 需网络代理）——智谱不可用时的兜底"""
    import base64 as _b64
    api_key = os.environ.get("AGNES_API_KEY", "")
    if not api_key:
        return None
    body = {"model": "agnes-2.5-flash", "messages": [{"role": "user", "content": [
        {"type": "text", "text": prompt},
        {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + _b64.b64encode(image_bytes).decode()}},
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
