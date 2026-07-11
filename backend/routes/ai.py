"""AI proxy and RAG QA routes"""
import json
from fastapi import APIRouter, Request, Header
from fastapi.responses import JSONResponse, StreamingResponse
from typing import Optional
from models import QARequest
import config
from auth import get_user_by_token, save_chat_message

router = APIRouter()

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
