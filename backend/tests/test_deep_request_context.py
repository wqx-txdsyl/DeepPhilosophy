"""The real FastAPI dependency/SSE task boundary must preserve memory ownership."""
import asyncio
import json
from pathlib import Path
import sys

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import auth
import guard
import engine_langgraph as engine
from deep_context import current_memory_key, general_memory_key
from routes import agent_core as core
from routes import agent_sse as sse


@pytest.fixture
def client(monkeypatch):
    app = FastAPI()
    app.include_router(sse.router)
    monkeypatch.setattr(guard, "resolve_user", lambda header: {
        "id": int(header.split("-")[-1])} if header and header.startswith("Bearer test-") else None)
    monkeypatch.setattr(guard, "_buckets", {})
    monkeypatch.setattr(guard, "_quota", {})
    monkeypatch.setattr(auth, "get_user_by_token", lambda token: None)
    monkeypatch.setattr(sse, "API_KEY", "offline")
    monkeypatch.setattr(core, "_mem_all", {})

    async def observe(message, *args, **kwargs):
        def memory_tool():
            slot = core._mem_slot()
            previous = slot.get("test_value")
            slot["test_value"] = message
            return {"type": "observed", "previous": previous,
                    "identity": guard.current_user.get(), "key": guard.user_memory_key(),
                    "scope": current_memory_key.get()}
        yield await asyncio.to_thread(memory_tool)
    monkeypatch.setattr(engine, "stream_agent", observe)
    with TestClient(app) as result:
        yield result


def post(client, user=11, conversation="conversation-a", message="first", **extra):
    body = {"message": message, "agent": "general", **extra}
    if conversation is not None:
        body["conversation_id"] = conversation
    response = client.post("/api/agent/stream_lg", json=body,
                           headers={"authorization": f"Bearer test-{user}"} if user else {})
    assert response.status_code == 200, response.text
    return json.loads(next(line[6:] for line in response.text.splitlines() if line.startswith("data: ")))


def test_real_dependency_identity_reaches_sse_and_worker_tools(client):
    first = post(client)
    again = post(client, message="second")
    assert first["identity"]["id"] == 11
    assert first["key"] == again["key"] == first["scope"]
    assert again["previous"] == "first"
    assert first["key"].startswith("u:general:")


def test_users_sharing_conversation_id_and_one_users_different_conversations_are_isolated(client):
    first = post(client)
    other_user = post(client, user=12)
    other_conversation = post(client, conversation="conversation-b")
    assert len({item["key"] for item in (first, other_user, other_conversation)}) == 3
    assert other_user["previous"] is None and other_conversation["previous"] is None
    assert post(client)["previous"] == "first"


def test_omitting_conversation_never_reuses_default_or_another_requests_memory(client):
    first = post(client, conversation=None)
    second = post(client, conversation=None)
    assert first["key"] != second["key"]
    assert second["previous"] is None


def test_body_user_identity_cannot_override_authenticated_owner(client):
    actual = post(client, user=11)
    forged = post(client, user=12, user_id=11)
    assert forged["identity"]["id"] == 12
    assert forged["key"] != actual["key"] and forged["previous"] is None


def test_anonymous_ownership_is_namespaced_and_does_not_reuse_logged_in_scope(client):
    anonymous = post(client, user=None)
    authenticated = post(client)
    assert anonymous["identity"]["id"] is None
    assert anonymous["key"].startswith("ip:general:")
    assert anonymous["key"] != authenticated["key"]
    assert general_memory_key(None, "203.0.113.1", "same") != general_memory_key(None, "203.0.113.2", "same")


def test_persona_route_and_unscoped_memory_behavior_remain_legacy(client):
    persona = post(client, agent="nietzsche")
    assert persona["scope"] is None and persona["identity"] is None
    assert persona["key"] == "default"
    assert post(client)["previous"] is None
    token = guard.current_user.set({"id": 91, "ip": "203.0.113.1"})
    try:
        assert guard.user_memory_key() == "u91"
    finally:
        guard.current_user.reset(token)


def test_cancellation_closes_provider_and_restores_context_in_consuming_task(monkeypatch):
    monkeypatch.setattr(sse, "API_KEY", "offline")
    closed = []

    async def provider(*args, **kwargs):
        try:
            yield {"type": "status", "content": "开始"}
            await asyncio.Event().wait()
        finally:
            closed.append(True)
    monkeypatch.setattr(engine, "stream_agent", provider)

    async def run():
        identity = {"id": 999, "ip": "parent"}
        identity_token = guard.current_user.set(identity)
        scope_token = current_memory_key.set("outer-scope")
        after = []
        request = Request({"type": "http", "headers": [], "client": ("203.0.113.9", 1234)})
        response = await sse.agent_stream_lg(sse.AgentChatRequest(message="test", conversation_id="inner"),
                                            request, authorization=None, _g={"id": 11})
        arrived = asyncio.Event()
        async def consume():
            try:
                async for _frame in response.body_iterator:
                    assert guard.current_user.get()["id"] == 11
                    assert current_memory_key.get() != "outer-scope"
                    arrived.set()
            finally:
                after.append((guard.current_user.get(), current_memory_key.get()))
        try:
            task = asyncio.create_task(consume())
            await asyncio.wait_for(arrived.wait(), 1)
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task
            assert after == [(identity, "outer-scope")]
            assert closed == [True]
        finally:
            current_memory_key.reset(scope_token)
            guard.current_user.reset(identity_token)
    asyncio.run(run())
