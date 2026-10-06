import asyncio
from contextlib import asynccontextmanager
import json
import logging
import os
from pathlib import Path
import uuid
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field, field_validator
from phiagent_lab.engine import build_graph, initial_state
from phiagent_lab.library import read_passage
from phiagent_lab.model import build_model
from phiagent_lab.store import Store

ROOT = Path(__file__).resolve().parents[1]
log = logging.getLogger(__name__)

class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    conversation_id: uuid.UUID
    message: str = Field(min_length=1, max_length=2000)

    @field_validator("message")
    @classmethod
    def nonblank(cls, value):
        if not value.strip():
            raise ValueError("请输入问题")
        return value.strip()

def sse(event):
    return "data: " + json.dumps(event, ensure_ascii=False) + "\n\n"

def create_app(model=None, db_path=None):
    @asynccontextmanager
    async def lifespan(app):
        app.state.store = Store(db_path or os.environ.get("PHI_DB", ROOT / "runtime" / "chat.sqlite3"))
        app.state.graph = build_graph(model or build_model())
        app.state.active = set()  # Single-process teaching app, not a distributed lock.
        yield

    app = FastAPI(title="PhiAgent Lab — local teaching app", lifespan=lifespan)

    @app.get("/api/health")
    async def health():
        return {"ok": True, "mode": os.environ.get("PHI_MODE", "mock")}

    @app.get("/api/conversations/{conversation_id}")
    async def history(conversation_id: uuid.UUID):
        return await asyncio.to_thread(app.state.store.history, str(conversation_id), 200)

    @app.get("/api/passages/{passage_id}")
    async def passage(passage_id: str):
        try:
            return read_passage(passage_id)
        except ValueError:
            raise HTTPException(404, "材料不存在")

    @app.post("/api/chat")
    async def chat(body: ChatRequest):
        cid, request_id = str(body.conversation_id), uuid.uuid4().hex
        if cid in app.state.active:
            raise HTTPException(409, "该会话正在生成，请稍后重试")
        app.state.active.add(cid)

        async def events():
            saved_answer = None
            yield sse({"type": "start", "request_id": request_id})
            try:
                async with asyncio.timeout(120):
                    history = await asyncio.to_thread(app.state.store.history, cid)
                    async for part in app.state.graph.astream(
                        initial_state(body.message, history), stream_mode="custom", version="v2",
                        config={"recursion_limit": 16},
                    ):
                        event = part["data"]
                        if event["type"] == "answer":
                            saved_answer = event
                        else:
                            yield sse(event)
                    if saved_answer is None:
                        raise RuntimeError("缺少已校验回答")
                    await asyncio.to_thread(app.state.store.save_turn, cid, body.message, saved_answer["text"])
                    yield sse({**saved_answer, "type": "done"})
            except asyncio.CancelledError:
                raise  # Disconnect must cancel model work, not become a successful answer.
            except Exception as exc:
                log.warning("request=%s error_type=%s", request_id, type(exc).__name__)
                yield sse({"type": "error", "message": "本次回答未完成，请检查服务端配置或重试。",
                           "request_id": request_id})
            finally:
                app.state.active.discard(cid)

        return StreamingResponse(events(), media_type="text/event-stream", headers={
            "Cache-Control": "no-cache", "X-Accel-Buffering": "no",
        })

    # API routes must be registered before the '/' static mount.
    app.mount("/", StaticFiles(directory=ROOT / "web", html=True), name="web")
    return app

app = create_app()
