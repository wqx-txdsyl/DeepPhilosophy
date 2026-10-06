"""Actual tool request construction, with deterministic local HTTP responses."""
import asyncio
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from deep_context import current_tool_agent
from routes import agent_llm as llm
from routes import agent_tools_eval as evaluate


@pytest.fixture
def requests(monkeypatch):
    seen = []
    class Response:
        def __enter__(self):
            return self
        def __exit__(self, *_args):
            pass
        def read(self):
            return json.dumps({"choices": [{"finish_reason": "stop", "message": {
                "content": '{"conclusion":"A premise is missing","thesis":{"statement":"The claim"}}'
            }}]}).encode()
    def urlopen(request, **kwargs):
        seen.append(json.loads(request.data))
        return Response()
    monkeypatch.setattr(llm.urllib.request, "urlopen", urlopen)
    monkeypatch.setattr(llm, "MODEL", "deepseek-flash")
    monkeypatch.setattr(llm, "_IS_ZHIPU", False)
    token = current_tool_agent.set(None)
    try:
        yield seen
    finally:
        current_tool_agent.reset(token)


@pytest.mark.parametrize("agent", [None, "nietzsche"])
def test_unscoped_and_persona_plain_calls_keep_the_legacy_request(agent, requests):
    token = current_tool_agent.set(agent)
    try:
        llm.llm_chat([{"role": "user", "content": "fixture"}], max_tokens=900)
    finally:
        current_tool_agent.reset(token)
    assert requests == [{"model": "deepseek-flash", "messages": [{"role": "user", "content": "fixture"}],
                         "max_tokens": 900, "temperature": 0.7}]


def test_general_plain_tool_explicitly_disables_provider_default_thinking(requests):
    token = current_tool_agent.set("general")
    try:
        llm.llm_chat([{"role": "user", "content": "fixture"}], max_tokens=900, temperature=0.6)
    finally:
        current_tool_agent.reset(token)
    assert requests[0]["thinking"] == {"type": "disabled"}
    assert requests[0]["model"] == "deepseek-flash"
    assert requests[0]["max_tokens"] == 900 and requests[0]["temperature"] == 0.6
    assert "reasoning_effort" not in requests[0]
    assert current_tool_agent.get() is None


def test_explicit_tool_thinking_is_not_disabled_by_general_scope(requests):
    token = current_tool_agent.set("general")
    try:
        llm.llm_chat([{"role": "user", "content": "fixture"}], thinking=True)
    finally:
        current_tool_agent.reset(token)
    assert requests[0]["thinking"] == {"type": "enabled"}
    assert requests[0]["reasoning_effort"] == "medium"
    assert "temperature" not in requests[0]


def test_existing_explicit_disable_option_remains_supported(requests):
    llm.llm_chat([{"role": "user", "content": "fixture"}], disable_thinking=True)
    assert requests[0]["thinking"] == {"type": "disabled"}


@pytest.mark.parametrize("agent,expected_attempts", [("general", 1), ("nietzsche", 3)])
def test_failed_tool_transport_retries_remain_owned_by_the_engine_for_general_only(agent, expected_attempts, monkeypatch):
    calls, sleeps = [], []
    def fail(*args, **kwargs):
        calls.append(1)
        raise TimeoutError("local fixture timeout")
    monkeypatch.setattr(llm.urllib.request, "urlopen", fail)
    monkeypatch.setattr(llm.time, "sleep", sleeps.append)
    token = current_tool_agent.set(agent)
    try:
        with pytest.raises(TimeoutError):
            llm.llm_chat([{"role": "user", "content": "fixture"}])
    finally:
        current_tool_agent.reset(token)
    assert len(calls) == expected_attempts
    assert len(sleeps) == expected_attempts - 1


def test_explicit_auxiliary_reasoning_budget_reaches_provider_unchanged(requests):
    token = current_tool_agent.set("general")
    try:
        llm.llm_chat([{"role": "user", "content": "fixture"}], thinking=True,
                     reasoning_effort="low", max_tokens=8192)
    finally:
        current_tool_agent.reset(token)
    assert requests[0]["reasoning_effort"] == "low"
    assert requests[0]["max_tokens"] == 8192
    assert requests[0]["thinking"] == {"type": "enabled"}


def test_provider_specific_field_does_not_leak_to_legacy_zhipu_path(requests, monkeypatch):
    monkeypatch.setattr(llm, "_IS_ZHIPU", True)
    token = current_tool_agent.set("general")
    try:
        llm.llm_chat([{"role": "user", "content": "fixture"}])
    finally:
        current_tool_agent.reset(token)
    assert "thinking" not in requests[0]


@pytest.mark.parametrize("tool,budget,payload", [
    (evaluate._exec_analyze_argument, 900, "argument"),
    (evaluate._exec_paper_review, 1000, "review"),
])
def test_actual_general_structured_tool_defaults_reach_http_with_thinking_disabled(tool, budget, payload, requests):
    async def run():
        token = current_tool_agent.set("general")
        try:
            return await asyncio.to_thread(tool, {"text": "多数人相信这个结论，所以这个结论必然正确。"})
        finally:
            current_tool_agent.reset(token)
    result = asyncio.run(run())
    assert result[payload]
    assert len(requests) == 1
    assert requests[0]["max_tokens"] == budget
    assert requests[0]["thinking"] == {"type": "disabled"}
    assert requests[0]["model"] == "deepseek-flash"


def test_parallel_persona_and_general_workers_do_not_share_tool_scope(requests):
    async def call(agent):
        token = current_tool_agent.set(agent)
        try:
            await asyncio.to_thread(llm.llm_chat, [{"role": "user", "content": agent}])
        finally:
            current_tool_agent.reset(token)
    async def run():
        await asyncio.gather(call("general"), call("nietzsche"))
    asyncio.run(run())
    by_agent = {body["messages"][0]["content"]: body for body in requests}
    assert by_agent["general"]["thinking"] == {"type": "disabled"}
    assert "thinking" not in by_agent["nietzsche"]
    assert current_tool_agent.get() is None


def _tool_state(name, *, agent="general", question="用户真正的问题"):
    from langchain_core.messages import AIMessage
    import agent_runtime as runtime
    return {"agent": agent, "request_message": question,
            "guard": runtime.DuplicateGuard(), "discipline": None,
            "budget": runtime.ToolBudget(set()), "tool_count": 0, "raw_tool_log": [],
            "messages": [AIMessage(content="", tool_calls=[{"name": name, "id": "scope-check", "args": {}}])]}


def test_engine_stateful_worker_inherits_tool_scope_original_question_and_memory_overlay(requests, monkeypatch, tmp_path):
    import engine_langgraph as engine
    from deep_context import current_memory_key, current_memory_overlay, current_request_question
    from routes import agent_core as core
    monkeypatch.setattr(core, "_mem_all", {})
    monkeypatch.setattr(core, "MEM_FILE", tmp_path / "memory.json")
    observations = []
    def write_essay():
        observations.append((current_tool_agent.get(), current_request_question.get(),
                             current_memory_overlay.get() is not None))
        llm.llm_chat([{"role": "user", "content": "stateful fixture"}])
        core._mem_slot()["essays"]["fixture"] = {"text": "committed"}
        return {"essay": "committed"}
    monkeypatch.setattr(engine, "get_tools", lambda _agent: [SimpleNamespace(name="write_essay", func=write_essay)])
    async def run():
        scope = current_memory_key.set("u:general:tool-scope-test")
        question = current_request_question.set("outside request")
        try:
            result = await engine.tools_node(_tool_state("write_essay"))
            assert current_tool_agent.get() is None
            assert current_request_question.get() == "outside request"
            return result
        finally:
            current_request_question.reset(question)
            current_memory_key.reset(scope)
    result = asyncio.run(run())
    assert result["messages"][0].additional_kwargs["_result_full"] == {"essay": "committed"}
    assert observations == [("general", "用户真正的问题", True)]
    assert requests[0]["thinking"] == {"type": "disabled"}
    assert core._mem_all["u:general:tool-scope-test"]["essays"]["fixture"]["text"] == "committed"


def test_engine_nietzsche_tool_does_not_install_general_context_or_change_request(requests, monkeypatch):
    import engine_langgraph as engine
    from deep_context import current_request_question
    observations = []
    def probe():
        observations.append((current_tool_agent.get(), current_request_question.get()))
        llm.llm_chat([{"role": "user", "content": "persona fixture"}], temperature=0.6, max_tokens=900)
        return {"ok": True}
    monkeypatch.setattr(engine, "get_tools", lambda _agent: [SimpleNamespace(name="probe", func=probe)])
    asyncio.run(engine.tools_node(_tool_state("probe", agent="nietzsche")))
    assert observations == [(None, None)]
    assert requests == [{"model": "deepseek-flash", "messages": [{"role": "user", "content": "persona fixture"}],
                         "max_tokens": 900, "temperature": 0.6}]


def test_cancelled_engine_tool_resets_both_context_variables_in_its_own_task(monkeypatch):
    import deep_context
    import engine_langgraph as engine
    class ObservedContext:
        def __init__(self, variable):
            self.variable, self.resets = variable, []
        def get(self):
            return self.variable.get()
        def set(self, value):
            return self.variable.set(value)
        def reset(self, token):
            before = self.get()
            self.variable.reset(token)
            self.resets.append((before, self.get()))
    agent_scope = ObservedContext(deep_context.current_tool_agent)
    question_scope = ObservedContext(deep_context.current_request_question)
    monkeypatch.setattr(deep_context, "current_tool_agent", agent_scope)
    monkeypatch.setattr(deep_context, "current_request_question", question_scope)
    async def run():
        entered = asyncio.Event()
        async def probe():
            assert agent_scope.get() == "general"
            assert question_scope.get() == "用户真正的问题"
            entered.set()
            await asyncio.Event().wait()
        monkeypatch.setattr(engine, "get_tools", lambda _agent: [SimpleNamespace(name="probe", func=probe)])
        outer_agent = agent_scope.set("outer")
        outer_question = question_scope.set("outer question")
        try:
            task = asyncio.create_task(engine.tools_node(_tool_state("probe")))
            await asyncio.wait_for(entered.wait(), 1)
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task
            assert agent_scope.resets == [("general", "outer")]
            assert question_scope.resets == [("用户真正的问题", "outer question")]
            assert agent_scope.get() == "outer" and question_scope.get() == "outer question"
        finally:
            agent_scope.reset(outer_agent)
            question_scope.reset(outer_question)
    asyncio.run(run())


@pytest.mark.parametrize("agent", [None, "general", "nietzsche"])
def test_council_threads_inherit_context_only_for_general_caller(agent, requests, monkeypatch):
    from deep_context import current_request_question
    monkeypatch.setitem(evaluate.TOOLS, "search_books", {"execute": lambda args: {"results": []}})
    token = current_tool_agent.set(agent)
    question = current_request_question.set("original question")
    try:
        result = evaluate._exec_agent_council({"topic": "选择与责任"})
    finally:
        current_request_question.reset(question)
        current_tool_agent.reset(token)
    assert len(requests) == 3
    assert all(body["model"] == "deepseek-flash" for body in requests)
    if agent == "general":
        assert all(body["thinking"] == {"type": "disabled"} for body in requests)
    else:
        assert all("thinking" not in body for body in requests)
    assert all(result["council"][key] for key in ("deep", "nietzsche", "synthesis"))
