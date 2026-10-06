"""Stateful tools retain real thread ownership and discard late memory writes."""
import asyncio
import json
from pathlib import Path
import sys
import threading

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from deep_context import current_memory_key, current_memory_overlay
import deep_stateful as stateful
from routes import agent_core as core


@pytest.fixture(autouse=True)
def memory(monkeypatch, tmp_path):
    monkeypatch.setattr(core, "_mem_all", {})
    monkeypatch.setattr(core, "MEM_FILE", tmp_path / "memory.json")


async def call(key, func, timeout=2):
    token = current_memory_key.set(key)
    try:
        return await stateful.execute_stateful(func, {}, timeout)
    finally:
        current_memory_key.reset(token)


async def until(predicate):
    async def poll():
        while not predicate():
            await asyncio.sleep(0.001)
    await asyncio.wait_for(poll(), 2)


def test_success_commits_once_and_detaches_returned_memory():
    def mutate():
        slot = core._mem_slot()
        assert current_memory_overlay.get() is slot
        slot["essays"]["topic"] = {"text": "first"}
        core._save_agent_memory()
        assert not core.MEM_FILE.exists()
        return slot["essays"]["topic"]
    result = asyncio.run(call("u:general:one", mutate))
    result["text"] = "later caller mutation"
    assert core._mem_all["u:general:one"]["essays"]["topic"]["text"] == "first"
    assert json.loads(core.MEM_FILE.read_text())["u:general:one"]["essays"]["topic"]["text"] == "first"
    assert not stateful._locks and current_memory_overlay.get() is None


@pytest.mark.parametrize("failure", [{"error": "failed"}, {"accepted": False}, RuntimeError("failed")])
def test_failed_or_rejected_tools_cannot_commit_partial_mutations(failure):
    def mutate():
        core._mem_slot()["essays"]["unwanted"] = {"text": "partial"}
        core._save_agent_memory()
        if isinstance(failure, Exception):
            raise failure
        return failure
    if isinstance(failure, Exception):
        with pytest.raises(RuntimeError):
            asyncio.run(call("u:general:one", mutate))
    else:
        assert asyncio.run(call("u:general:one", mutate)) == failure
    assert core._mem_all["u:general:one"]["essays"] == {}
    assert not core.MEM_FILE.exists() and not stateful._locks


@pytest.mark.parametrize("cancel", [False, True])
def test_timed_out_or_cancelled_worker_cannot_save_late_memory(cancel):
    entered, release = threading.Event(), threading.Event()
    def mutate():
        slot = core._mem_slot()
        slot["essays"]["unwanted"] = {"text": "partial"}
        entered.set()
        assert release.wait(2)
        slot["debate"] = {"topic": "late mutation"}
        core._save_agent_memory()
        return {"ok": True}
    async def run():
        task = asyncio.create_task(call("u:general:one", mutate, 2 if cancel else 0.03))
        await until(entered.is_set)
        if cancel:
            task.cancel()
        try:
            with pytest.raises(asyncio.CancelledError if cancel else asyncio.TimeoutError):
                await task
            assert core._mem_all["u:general:one"]["essays"] == {}
        finally:
            release.set()
        await until(lambda: not stateful._locks)
    asyncio.run(run())
    assert core._mem_all["u:general:one"]["essays"] == {}
    assert core._mem_all["u:general:one"]["debate"] is None
    assert not core.MEM_FILE.exists()


def test_new_same_scope_request_waits_for_timed_out_thread_then_reads_committed_state_only():
    entered, release, finished = threading.Event(), threading.Event(), threading.Event()
    def first():
        core._mem_slot()["debate"] = {"topic": "cancelled topic"}
        entered.set()
        assert release.wait(2)
        finished.set()
        return {"ok": True}
    def second():
        assert finished.is_set(), "The real worker still owned this conversation"
        assert core._mem_slot()["debate"] is None
        core._mem_slot()["debate"] = {"topic": "new topic"}
        return {"ok": True}
    async def run():
        task = asyncio.create_task(call("u:general:one", first, 0.03))
        await until(entered.is_set)
        with pytest.raises(asyncio.TimeoutError):
            await task
        following = asyncio.create_task(call("u:general:one", second))
        try:
            await until(lambda: stateful._locks.get("u:general:one", {}).get("users") == 2)
            assert not following.done()
        finally:
            release.set()
        assert await following == {"ok": True}
    asyncio.run(run())
    assert core._mem_all["u:general:one"]["debate"] == {"topic": "new topic"}
    assert not stateful._locks


def test_cancelled_lock_waiter_never_invokes_the_tool():
    entered, release = threading.Event(), threading.Event()
    invoked = []
    def first():
        entered.set()
        assert release.wait(2)
        return {"ok": True}
    def cancelled():
        invoked.append(True)
        return {"ok": True}
    async def run():
        one = asyncio.create_task(call("u:general:one", first))
        await until(entered.is_set)
        two = asyncio.create_task(call("u:general:one", cancelled))
        try:
            await until(lambda: stateful._locks.get("u:general:one", {}).get("users") == 2)
            two.cancel()
            with pytest.raises(asyncio.CancelledError):
                await two
        finally:
            release.set()
        await one
        await until(lambda: not stateful._locks)
    asyncio.run(run())
    assert invoked == []


def test_different_conversation_scopes_execute_independently():
    barrier = threading.Barrier(2)
    def tool(value):
        def mutate():
            barrier.wait(1)
            core._mem_slot()["debate"] = {"topic": value}
            return {"ok": True}
        return mutate
    async def run():
        await asyncio.gather(call("u:general:one", tool("first")), call("u:general:two", tool("second")))
    asyncio.run(run())
    assert core._mem_all["u:general:one"]["debate"]["topic"] == "first"
    assert core._mem_all["u:general:two"]["debate"]["topic"] == "second"
    persisted = json.loads(core.MEM_FILE.read_text())
    assert persisted == core._mem_all
    assert not stateful._locks
