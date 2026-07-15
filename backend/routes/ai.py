"""AI proxy, RAG QA, and ASR routes"""
import json
import base64
import requests as req_lib
from fastapi import APIRouter, Request, Header
from fastapi.responses import JSONResponse, StreamingResponse
from typing import Optional
from models import QARequest
import config
from auth import get_user_by_token, save_chat_message

router = APIRouter()

# ── Baidu ASR token cache ──────────────────────────────────
_asr_token = None

def _get_baidu_token():
    global _asr_token
    try:
        resp = req_lib.post(
            "https://aip.baidubce.com/oauth/2.0/token",
            data={
                "grant_type": "client_credentials",
                "client_id": config.BAIDU_ASR_API_KEY,
                "client_secret": config.BAIDU_ASR_SECRET_KEY,
            },
            timeout=10,
        )
        result = resp.json()
        _asr_token = result.get("access_token")
        return _asr_token
    except Exception:
        return None

@router.post("/api/ai/stream")
async def ai_stream_proxy(req: Request):
    """Stream proxy for DeepSeek API using server default key"""
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
                    yield f"data: {json.dumps({'choices':[{'delta':{'content': chunk.choices[0].delta.content}}]})}\\n\\n"
            yield "data: [DONE]\\n\\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\\n\\n"
    return StreamingResponse(generate(), media_type="text/event-stream",
        headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache"})

@router.post("/api/qa")
async def ask_question(req: QARequest, authorization: Optional[str] = Header(None)):
    """RAG-based Q&A with automatic chat history save"""
    try:
        from modules.embedding import EmbeddingManager
        from modules.vector_store import VectorStoreManager
        from modules.rag_chain import RAGChain
        mgr = EmbeddingManager()
        store = VectorStoreManager(embedding_function=mgr.get_embedding_function())
        kb_ready = store.get_collection_stats()["chunk_count"] > 0
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
                                temperature=temperature, max_tokens=max_tokens)
                            return resp.choices[0].message.content
                        except Exception as e:
                            if attempt < max_retries - 1: time.sleep(2 ** attempt)
                            else: raise RuntimeError(str(e))
            llm = UserLLMClient(req.api_key, "https://api.deepseek.com", req.model or "deepseek-chat")
        else:
            from modules.llm_client import DeepSeekClient
            llm = DeepSeekClient()
        if kb_ready:
            rag = RAGChain(vector_store=store, llm_client=llm)
            result = rag.query(req.question)
        else:
            try:
                answer = llm.chat(messages=[
                    {"role": "system", "content": "你是一个哲学知识助手。请用中文回答用户的问题，尽可能准确和详细。如果不知道，请如实说明。"},
                    {"role": "user", "content": req.question}])
                result = {"answer": answer, "sources": [], "question": req.question}
            except Exception as e:
                result = {"answer": f"问答服务暂不可用: {e}\\n\\n请确认已在设置中配置了有效的 API Key。", "sources": [], "question": req.question}
        if authorization and authorization.startswith("Bearer "):
            try:
                user = get_user_by_token(authorization[7:])
                if user:
                    save_chat_message(user["id"], "user", req.question)
                    save_chat_message(user["id"], "assistant", result["answer"],
                        json.dumps(result.get("sources", []), ensure_ascii=False))
            except Exception: pass
        return result
    except Exception as e:
        return {"answer": f"问答服务暂时不可用: {str(e)}", "sources": [], "question": req.question}


@router.post("/api/asr")
async def speech_to_text(req: Request):
    """语音识别：接收 WAV 音频，返回文本。需要配置百度 API Key。"""
    if not config.BAIDU_ASR_API_KEY:
        return JSONResponse({"error": "ASR not configured", "text": ""}, status_code=503)

    # Ensure token
    global _asr_token
    if not _asr_token:
        _asr_token = _get_baidu_token()
    if not _asr_token:
        return JSONResponse({"error": "Baidu token failed", "text": ""}, status_code=502)

    # Read raw audio from request body
    raw_audio = await req.body()
    if not raw_audio or len(raw_audio) < 100:
        return JSONResponse({"error": "Audio too short", "text": ""}, status_code=400)

    # Call Baidu ASR
    try:
        payload = {
            "format": "wav",
            "rate": 16000,
            "channel": 1,
            "cuid": "deepphilosophy_web",
            "token": _asr_token,
            "speech": base64.b64encode(raw_audio).decode(),
            "len": len(raw_audio),
        }
        resp = req_lib.post(
            "https://vop.baidu.com/server_api",
            json=payload,
            timeout=10,
        )
        result = resp.json()
        err_no = result.get("err_no")
        if err_no == 0:
            text = result.get("result", [""])[0]
            return {"text": text}
        elif err_no in (3301, 3302, 3303):
            # Token expired, refresh and tell client to retry
            _asr_token = _get_baidu_token()
            return JSONResponse({"error": "Token expired, retry", "text": ""}, status_code=401)
        else:
            err_msg = result.get("err_msg", "unknown")
            return JSONResponse({"error": err_msg, "text": ""}, status_code=502)
    except Exception as e:
        return JSONResponse({"error": str(e), "text": ""}, status_code=502)
