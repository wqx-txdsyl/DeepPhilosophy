# -*- coding: utf-8 -*-
"""Phase A（2026-08-30）—— Agent Runtime Reliability / Tool Loop Audit 回归集

A1 Tool Loop Observability: 单轮 invocation 轨迹（conversation/message/agent/invocation id、
    归一化参数+hash、call index、时长、成败、结果摘要/hash、evidence 数、info gain、
    model retry、总时长）→ JSONL; 禁止记录原始 chain-of-thought
A2 Duplicate Tool Call Guard: 同 turn same tool + effectively same args → 复用/拦截;
    参数实质变化/范围变化/失败重试/生成类工具一律放行
A3 Tool Budget: hard（graceful answer completion）配置化,
    区分 useful/retry/duplicate/no-gain 计数（O4: 纯遥测, 无 soft 提示分支）
A4 Model/Tool Error Recovery: 可恢复错误有限重试 → 耗尽后用已取得 evidence graceful
    completion; 不暴露 stack trace; 不丢 evidence
A5 Termination: 显式结束条件 + 防御性流帧处理
O4 Cognitive Layer Collapse: soft 预算提示 / no_gain 守卫 / RetrievalState 语义增益 /
    no_gain_streak 状态链已删除——停止权威只在 Main Agent 宣告 + hard 机械上限。
根因回归: "约 13 次工具调用后模型侧 error"（DeepSeek 流式连接中断）→ graceful recovery

确定性单测: LLM 一律 mock（不依赖网络）; 真实 retrieval UAT 见 tools/dp_uat_phase_a.py。
"""
import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from langchain_core.messages import AIMessage, AIMessageChunk, HumanMessage, SystemMessage, ToolMessage

import agent_runtime as AR
import routes.agent as AG
import engine_langgraph as elg


# ── 公共设施 ─────────────────────────────────────────
@pytest.fixture(autouse=True)
def _clean_state(tmp_path, monkeypatch):
    """trace 写入临时文件（不污染 backend/data/agent_loop_trace.jsonl）; 关闭打字机等待"""
    monkeypatch.setattr(AR, "TRACE_FILE", tmp_path / "trace.jsonl")
    monkeypatch.setattr(AR, "MODEL_RETRY", {"attempts": 2, "backoff_seconds": [0, 0]})
    yield
    elg._llm = None   # 复位 LLM 缓存（防测试 fake 泄漏到其他用例）


def _trace_lines():
    if not AR.TRACE_FILE.exists():
        return []
    return [json.loads(ln) for ln in AR.TRACE_FILE.read_text(encoding="utf-8").splitlines() if ln.strip()]


async def _collect_stream(question, agent="general", language="zh", **kw):
    return [ev async for ev in elg.stream_agent(question, [], agent, None, language, **kw)]


def _run_tools_node(calls, guard=None, budget=None, trace=None, tools=None, tool_count=0):
    """直接驱动 tools_node（mock 工具集, 不触网）"""
    if tools is None:
        tools = []
    orig_get_tools = elg.get_tools
    elg.get_tools = lambda agent: tools
    try:
        from langchain_core.messages import AIMessage as _AIM
        state = {"messages": [_AIM(content="", tool_calls=calls)],
                 "guard": guard or AR.DuplicateGuard(),
                 "budget": budget or AR.ToolBudget(retrieval_tools=set(elg.RETRIEVAL_TOOLS) | {"philosopher_memory"}),
                 "trace": trace or AR.ToolLoopTrace("conv-t", "msg-t", "general"),
                 "agent": "general", "tool_count": tool_count}
        return asyncio.run(elg.tools_node(state))
    finally:
        elg.get_tools = orig_get_tools


def _fake_tool(name, fn):
    from types import SimpleNamespace
    return SimpleNamespace(name=name, func=fn)


# ═══════════════════════════════════════════════════════
# A2 参数归一化 + DuplicateGuard
# ═══════════════════════════════════════════════════════
def test_a2_normalize_args_collapses_whitespace_and_drops_empty():
    assert AR.normalize_args({"query": "  权力   意志 ", "limit": None, "x": ""}) == {"query": "权力 意志"}
    assert AR.normalize_args({"k": 5.0}) == {"k": 5}


def test_a2_same_tool_same_args_reuses_result_without_execution():
    g = AR.DuplicateGuard()
    prev = {"results": [{"snippet": "我是光"}]}
    g.record("search_books", {"query": "权力意志"}, True, prev)
    d = g.decide("search_books", {"query": " 权力意志 "})   # 空白差异不构成"实质修改"
    assert d["action"] == "reuse" and d["cls"] == "duplicate" and d["prev"] is prev


def test_a2_substantively_changed_args_execute():
    g = AR.DuplicateGuard()
    g.record("search_books", {"query": "权力意志"}, True, {"results": [1]})
    assert g.decide("search_books", {"query": "永恒轮回"})["cls"] == "unique"
    # metadata/filter/period 变化 → 归一化参数不同 → 放行
    assert g.decide("search_books", {"query": "权力意志", "author": "尼采"})["cls"] == "unique"
    g.record("philosopher_period", {"period": "early"}, True, {})
    assert g.decide("philosopher_period", {"period": "late"})["cls"] == "unique"


def test_a2_scope_variant_allowed_but_marked():
    g = AR.DuplicateGuard()
    g.record("search_books", {"query": "权力意志", "limit": 5}, True, {"results": [1]})
    d = g.decide("search_books", {"query": "权力意志", "limit": 20})
    assert d["action"] == "execute" and d["cls"] == "scope_variant"


def test_a2_failed_call_allows_reasonable_retry():
    g = AR.DuplicateGuard()
    g.record("search_books", {"query": "权力意志"}, False, {"error": "超时"})
    d = g.decide("search_books", {"query": "权力意志"})
    assert d["action"] == "execute" and d["cls"] == "retry_after_fail"


def test_a2_generative_and_interactive_tools_exempt():
    for tool in ("write_essay", "generate_image", "philosopher_debate", "thought_experiment",
                 "agent_council", "school_arena", "conceptual_map", "role_play"):
        g = AR.DuplicateGuard()
        g.record(tool, {"topic": "x"}, True, {"ok": 1})
        assert g.decide(tool, {"topic": "x"})["cls"] == "unique", f"{tool} 必须豁免（同参重调是合法交互）"


# ═══════════════════════════════════════════════════════
# A3 ToolBudget
# ═══════════════════════════════════════════════════════
def test_a3_budget_classification_useful_retry_duplicate_no_gain():
    b = AR.ToolBudget(retrieval_tools={"search_books"})
    b.count("search_books", "unique", True, "new")          # useful
    b.count("search_books", "unique", True, "empty")        # no gain（空命中）
    b.count("search_books", "unique", True, "repeat")       # no gain（同结果）
    b.count("search_books", "duplicate", False)             # 复用（不占执行预算）
    b.count("search_books", "retry_after_fail", True)       # retry
    assert (b.useful, b.no_gain, b.duplicate_reused, b.retry, b.total_executed) == (1, 2, 1, 1, 4)


def test_a3_hard_thresholds_from_config():
    # O4: 只剩硬资源上限（soft 提示机制已删）
    b = AR.ToolBudget(retrieval_tools={"search_books"},
                      cfg={"hard_retrieval": 20, "hard_total": 24})
    for _ in range(19):
        b.count("search_books", "unique", True, "new")
    assert not b.hard_reached()
    b.count("search_books", "unique", True, "new")            # 检索第 20 次
    assert b.hard_reached()


def test_a3_engine_reads_budget_from_config_not_magic_numbers():
    # O4: 引擎不再持有 RETRIEVAL_LIMIT/RETRIEVAL_HARD 别名——预算单一真源在 TOOL_BUDGET
    assert not hasattr(elg, "RETRIEVAL_LIMIT") and not hasattr(elg, "RETRIEVAL_HARD")
    assert AR.TOOL_BUDGET["hard_retrieval"] == AR._env_int("AGENT_HARD_RETRIEVAL", 20)
    assert AR.TOOL_BUDGET["hard_total"] == AR._env_int("AGENT_HARD_TOTAL", 24)
    assert AR.RECURSION_LIMIT >= AR.TOOL_BUDGET["hard_total"] // 2 + 4   # 递归兜底必须高于 hard 预算轮数
    assert AR.TOOL_TIMEOUT == AR._env_int("AGENT_TOOL_TIMEOUT", 90)


def test_a3_env_override(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_HARD_TOTAL", "30")
    monkeypatch.setattr(AR, "TRACE_FILE", tmp_path / "t.jsonl")
    import importlib
    ar2 = importlib.reload(AR)
    try:
        assert ar2.TOOL_BUDGET["hard_total"] == 30
    finally:
        monkeypatch.delenv("AGENT_HARD_TOTAL", raising=False)
        importlib.reload(AR)   # 复位默认配置（env 已清, reload 恢复默认值）


# ═══════════════════════════════════════════════════════
# A4 错误分类 + 有限重试
# ═══════════════════════════════════════════════════════
def test_a4_error_classification():
    for msg in ("Connection error: peer closed connection without sending complete message body",
                "Request timed out", "Error code: 429 - rate limit", "Error code: 503"):
        assert AR.classify_model_error(Exception(msg)) == "retryable", msg
    for msg in ("Error code: 401 - invalid api key", "Insufficient Balance",
                "Error code: 400 - This model's maximum context length is 65536 tokens"):
        assert AR.classify_model_error(Exception(msg)) == "fatal", msg


def test_a4_retry_recovers_on_transient_failure():
    calls = {"n": 0}
    def flaky(msgs):
        calls["n"] += 1
        if calls["n"] < 3:
            raise Exception("peer closed connection without sending complete message body")
        return "OK"
    resp, retries = AR.invoke_llm_with_retry(flaky, [])
    assert resp == "OK" and retries == 2 and calls["n"] == 3


def test_a4_fatal_error_not_retried():
    calls = {"n": 0}
    def fatal(msgs):
        calls["n"] += 1
        raise Exception("Error code: 401 - invalid api key")
    with pytest.raises(AR.ModelCallError):
        AR.invoke_llm_with_retry(fatal, [])
    assert calls["n"] == 1


def test_a4_retry_budget_exhausted_raises_model_call_error():
    calls = {"n": 0}
    def always(msgs):
        calls["n"] += 1
        raise Exception("connection reset by peer")
    with pytest.raises(AR.ModelCallError):
        AR.invoke_llm_with_retry(always, [])
    assert calls["n"] == AR.MODEL_RETRY["attempts"] + 1   # 首次 + 有限重试, 绝不无限


# ═══════════════════════════════════════════════════════
# A5 终止条件
# ═══════════════════════════════════════════════════════
def test_a5_should_continue_forced_rounds():
    state = {"messages": [AIMessage(content="", tool_calls=[{"name": "search_books", "args": {}, "id": "c"}])],
             "forced": True, "forced_tools_done": False}
    assert elg.should_continue(state) == "tools"       # 补跑一轮已宣告调用
    state["forced_tools_done"] = True
    assert elg.should_continue(state) == "end"         # 截断防死循环
    assert elg.should_continue({"messages": [AIMessage(content="回答")], "forced": False}) == "end"


# ═══════════════════════════════════════════════════════
# A1 Observability
# ═══════════════════════════════════════════════════════
def test_a1_trace_call_record_shape():
    t = AR.ToolLoopTrace("conv-1", "msg-1", "nietzsche", question_chars=11)
    t.record_call(0, "search_books", {"query": "权力 意志", "limit": 5}, 123.4, True, None,
                  '{"results": []}', "abc123", "unique", "new", 3,
                  executed=True, thought="执行 search_books")
    (rec,) = [r for r in _trace_lines() if r["type"] == "call"]
    for field in ("conversation_id", "message_id", "agent_id", "invocation_id", "call_index",
                  "tool", "args_normalized", "args_hash", "duration_ms", "success", "error",
                  "result_hash", "result_summary", "budget_class", "info_gain",
                  "evidence_items", "model_retry_count" if False else "rationale"):
        assert field in rec, field
    assert rec["args_normalized"] == {"query": "权力 意志", "limit": 5}
    assert rec["success"] is True and rec["executed"] is True and rec["evidence_items"] == 3


def test_a1_trace_finalize_turn_summary():
    t = AR.ToolLoopTrace("conv-2", "msg-2", "general")
    t.record_call(0, "search_books", {"query": "x"}, 5.0, True, None, "r", "h", "unique", "new", 1)
    t.model_retries = 2
    rec = t.finalize(88.8, error=None, answer_chars=1200, evidence_ids=["ev_0", "ev_1"],
                     budget_snapshot={"useful": 1})
    assert rec["type"] == "turn" and rec["total_tool_calls"] == 1
    assert rec["model_retry_count"] == 2 and rec["total_turn_duration_s"] == 88.8
    assert rec["evidence_ids"] == ["ev_0", "ev_1"] and rec["answer_chars"] == 1200


def test_a1_no_chain_of_thought_recorded():
    t = AR.ToolLoopTrace("conv-3", "msg-3", "general")
    t.record_call(0, "search_books", {"query": "x"}, 1.0, True, None, "r", "h", "unique", "new", 0,
                  executed=True, thought="rationale 标签" * 20)   # 超长标签被截断
    raw = AR.TRACE_FILE.read_text(encoding="utf-8")
    rec = json.loads(raw.splitlines()[0])
    assert len(rec["rationale"]) <= 40
    assert "reasoning_content" not in rec and "reasoning" not in json.dumps(rec, ensure_ascii=False)
    assert "thought_stream" not in rec


# ═══════════════════════════════════════════════════════
# 引擎接线: tools_node（A2 复用 / A3 计数 / A5 无增益轮）
# ═══════════════════════════════════════════════════════
def test_engine_tools_node_reuses_duplicate_without_execution():
    exec_counter = {"n": 0}
    def _search(**kw):
        exec_counter["n"] += 1
        return {"results": [{"snippet": "原文"}]}
    tools = [_fake_tool("search_books", _search)]
    guard = AR.DuplicateGuard()
    guard.record("search_books", {"query": "权力意志"}, True, {"results": [{"snippet": "原文"}]})
    out = _run_tools_node([{"name": "search_books", "args": {"query": "权力意志"}, "id": "c1"}],
                          guard=guard, tools=tools)
    msg = out["messages"][0]
    assert exec_counter["n"] == 0, "同参重复调用必须复用结果, 不再执行"
    assert msg.additional_kwargs["_reused"] is True and msg.additional_kwargs["_budget_class"] == "duplicate"
    assert msg.tool_call_id == "c1"
    assert out["tool_count"] == 0


def test_engine_tools_node_executes_unique_and_counts():
    exec_counter = {"n": 0}
    def _search(**kw):
        exec_counter["n"] += 1
        return {"results": [{"snippet": f"原文{exec_counter['n']}"}]}
    out = _run_tools_node(
        [{"name": "search_books", "args": {"query": "永恒轮回"}, "id": "c1"},
         {"name": "get_chapter", "args": {"book_id": "b", "idx": 1}, "id": "c2"}],
        tools=[_fake_tool("search_books", _search), _fake_tool("get_chapter", lambda **kw: {"text": "段落"})])
    assert exec_counter["n"] == 1
    assert out["tool_count"] == 2
    assert out["messages"][0].additional_kwargs["_info_gain"] == "new"


def test_engine_tools_node_marks_empty_results_as_no_gain_telemetry():
    # O4: 空命中只计入遥测（info_gain/budget.no_gain）——不再产生 streak/守卫控制
    out = _run_tools_node([{"name": "search_books", "args": {"query": "生僻词xyz"}, "id": "c1"}],
                          tools=[_fake_tool("search_books", lambda **kw: {"results": []})])
    assert out["messages"][0].additional_kwargs["_info_gain"] == "empty"
    assert "no_gain_streak" not in out


def test_engine_tools_node_failed_tool_retry_then_fallback_hint():
    calls = {"n": 0}
    def _failing(**kw):
        calls["n"] += 1
        return {"error": "索引未就绪"}
    budget = AR.ToolBudget(retrieval_tools={"search_books"})
    out = _run_tools_node([{"name": "search_books", "args": {"query": "x"}, "id": "c1"}],
                          tools=[_fake_tool("search_books", _failing)], budget=budget)
    assert calls["n"] == AR.TOOL_RETRY["attempts"] + 1     # 有限重试
    assert out["messages"][0].additional_kwargs["_result_full"].get("fallback_hint")
    assert budget.inner_retries == AR.TOOL_RETRY["attempts"]   # 轮内重试计入观测
    assert budget.snapshot()["inner_retries"] == AR.TOOL_RETRY["attempts"]


def test_engine_tools_node_inner_retry_then_success_counts_and_succeeds():
    calls = {"n": 0}
    def _flaky(**kw):
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("瞬时故障")
        return {"results": [{"snippet": "原文"}]}
    budget = AR.ToolBudget(retrieval_tools={"search_books"})
    out = _run_tools_node([{"name": "search_books", "args": {"query": "x"}, "id": "c1"}],
                          tools=[_fake_tool("search_books", _flaky)], budget=budget)
    assert calls["n"] == 2 and not out["messages"][0].additional_kwargs["_result_full"].get("error")
    assert budget.inner_retries == 1 and budget.useful == 1   # 自愈成功 → useful, 重试入观测


# ═══════════════════════════════════════════════════════
# 引擎接线: agent_node（A3 预算注入 / A4 模型重试）
# ═══════════════════════════════════════════════════════
class _FakeLLM:
    def __init__(self, script):
        self.script = list(script)   # 每次调用弹出一个: Exception 或 AIMessage
        self.prompts = []

    def bind_tools(self, tools):
        return self

    def invoke(self, msgs):
        self.prompts.append(msgs)
        item = self.script.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def _patch_llm(monkeypatch, fake, tools=None):
    monkeypatch.setattr(elg, "get_llm", lambda: fake)
    monkeypatch.setattr(elg, "get_tools", lambda agent: tools or [])


def test_engine_agent_node_soft_budget_no_control_effect(monkeypatch):
    # O3 §5/§8 + O4: soft 机制已整体删除——工具计数不影响 prompt/forced
    fake = _FakeLLM([AIMessage(content="回答")])
    _patch_llm(monkeypatch, fake)
    budget = AR.ToolBudget(retrieval_tools={"search_books"},
                           cfg={"hard_retrieval": 20, "hard_total": 24})
    for _ in range(8):
        budget.count("search_books", "unique", True, "new")
    state = {"messages": [HumanMessage(content="问")], "agent": "general", "language": "zh",
             "budget": budget}
    out = asyncio.run(elg.agent_node(state))
    assert out["forced"] is False
    assert not any("预算提示" in m.content or "材料是否足以回答" in m.content
                   for m in fake.prompts[0] if isinstance(m, SystemMessage))


def test_engine_agent_node_hard_budget_forces_answer(monkeypatch):
    fake = _FakeLLM([AIMessage(content="最终回答")])
    _patch_llm(monkeypatch, fake)
    budget = AR.ToolBudget(retrieval_tools={"search_books"},
                           cfg={"hard_retrieval": 20, "hard_total": 24})
    for _ in range(24):
        budget.count("search_books", "unique", True, "new")
    state = {"messages": [HumanMessage(content="问")], "agent": "general", "language": "zh",
             "budget": budget}
    out = asyncio.run(elg.agent_node(state))
    assert out["forced"] is True
    assert any("禁止调用任何工具" in m.content for m in fake.prompts[0] if isinstance(m, SystemMessage))


def test_engine_agent_node_no_gain_streak_no_control_effect(monkeypatch):
    # O3 §4/§8 + O4: no_gain 状态字段已删除——即便按旧字面 streak 语义（连续 3 轮无增益）
    # 也不再有 force 收口/注入任何指令; 行为只取决于 Main Agent 宣告。
    fake = _FakeLLM([AIMessage(content="最终回答")])
    _patch_llm(monkeypatch, fake)
    state = {"messages": [HumanMessage(content="问")], "agent": "general", "language": "zh",
             "budget": AR.ToolBudget()}
    out = asyncio.run(elg.agent_node(state))
    assert out["forced"] is False
    assert not any("无增益" in m.content or "不再检索" in m.content
                   for m in fake.prompts[0] if isinstance(m, SystemMessage))


def test_engine_agent_node_model_retry_then_success(monkeypatch):
    fake = _FakeLLM([Exception("peer closed connection without sending complete message body"),
                     AIMessage(content="回答")])
    _patch_llm(monkeypatch, fake)
    trace = AR.ToolLoopTrace("c", "m", "general")
    state = {"messages": [HumanMessage(content="问")], "agent": "general", "language": "zh",
             "budget": AR.ToolBudget(), "trace": trace}
    out = asyncio.run(elg.agent_node(state))
    # O5 字段级适配: model_retries state 字段已删（write-only）——计数真源 = trace.model_retries
    assert "model_retries" not in out
    assert trace.model_retries == 1 and out["messages"][0].content == "回答"


def test_engine_agent_node_model_retry_exhausted_raises(monkeypatch):
    fake = _FakeLLM([Exception("peer closed connection")] * (AR.MODEL_RETRY["attempts"] + 1))
    _patch_llm(monkeypatch, fake)
    state = {"messages": [HumanMessage(content="问")], "agent": "general", "language": "zh",
             "budget": AR.ToolBudget()}
    with pytest.raises(AR.ModelCallError):
        asyncio.run(elg.agent_node(state))


# ═══════════════════════════════════════════════════════
# 根因回归: 图流中断 → graceful recovery（13 calls → error 的防护）
# ═══════════════════════════════════════════════════════
class _FakeAppMidTurnCrash:
    """模拟: 工具调用后模型侧流式连接中断（peer closed connection）。

    O2/Phase A 改写: graceful recovery = 同一个图原样重跑一次（不再调 AG.llm_chat
    独立生成）。recovery_answer 给定时, 第二次 invocation（重跑）返回恢复轮正文;
    给 None 时重跑继续崩溃（恢复失败 → 友好 error 路径）。"""

    def __init__(self, tool_result, recovery_answer=None):
        self.tool_result = tool_result
        self.recovery_answer = recovery_answer
        self.invocations = 0

    async def astream(self, inputs, config, stream_mode="messages"):
        self.invocations += 1
        if self.recovery_answer and self.invocations >= 2:
            # 恢复轮: 同一个 Main Agent 图重跑, 直接产出最终回答（evidence 已在上轮取得）
            yield (AIMessageChunk(content=self.recovery_answer), {"langgraph_node": "agent"})
            return
        yield (AIMessageChunk(content="", tool_call_chunks=[
            {"name": "search_books", "args": "{\"query\": \"尼采 永恒轮回\"}", "id": "c1", "index": 0}]),
               {"langgraph_node": "agent"})
        yield (ToolMessage(content='{"results": []}', name="search_books", tool_call_id="c1",
                           additional_kwargs={"_args": {"query": "尼采 永恒轮回"},
                                              "_result_full": self.tool_result,
                                              "_budget_class": "unique", "_info_gain": "new"}),
               {"langgraph_node": "tools"})
        raise Exception("peer closed connection without sending complete message body (incomplete chunked read)")


def _stub_auto_websearch(monkeypatch):
    """根因回归用: 引擎自动 websearch 补充替换为静态结果（单测不触网）"""
    monkeypatch.setitem(AG.TOOLS, "websearch",
                        {"execute": lambda args: {"source": "wikipedia", "title": "永恒轮回", "snippet": "eternal recurrence"},
                         "description": "stub", "parameters": {"type": "object", "properties": {}}})


def test_root_cause_13_calls_mid_turn_crash_recovers_with_evidence(monkeypatch, tmp_path):
    stats_rec = []
    monkeypatch.setattr(elg, "_log_stats", lambda *a, **k: stats_rec.append(a))
    _stub_auto_websearch(monkeypatch)
    _recovery = "永恒轮回是权力意志的试金石：一切价值重估的极端形式。"
    fake_app = _FakeAppMidTurnCrash(
        tool_result={"results": [{"book_title": "查拉图斯特拉如是说", "chapter_title": "夜歌",
                                   "snippet": "我是光", "author": "弗里德里希·尼采"}]},
        recovery_answer=_recovery)
    monkeypatch.setattr(elg, "APP", fake_app)
    llm_calls = []

    def _forbidden_llm_chat(*a, **k):
        llm_calls.append(a)
        return {"choices": [{"message": {"content": ""}}]}
    monkeypatch.setattr(AG, "llm_chat", _forbidden_llm_chat)
    evs = asyncio.run(_collect_stream("永恒轮回是什么意思？"))
    types = [ev["type"] for ev in evs]
    assert "error" not in types, "图流中断必须 graceful recovery, 不得以 error 终止"
    assert fake_app.invocations == 2, "恢复 = 同一个图原样重跑一次"
    done = next(ev for ev in evs if ev["type"] == "done")
    assert done["tool_loop"]["recovered_after_error"] is True
    text = "".join(ev.get("content", "") for ev in evs if ev["type"] == "token")
    assert text == _recovery, "恢复后正文来自主图重跑 invocation, 非第二 writer 代写"
    assert llm_calls == [], "O2/Phase A: 恢复不得再调 AG.llm_chat 独立生成答案"
    assert done["tool_calls"], "已完成的工具调用证据必须保留在 done 中"
    # 观测: turn 汇总落盘且 error 有记录（不再把工具数记 0——stats 记录真实工具名）
    turns = [r for r in _trace_lines() if r["type"] == "turn"]
    assert turns and turns[-1]["error"]
    assert stats_rec and stats_rec[-1][3] == ["search_books"], "stats error/恢复路径必须记录真实工具名"


def test_root_cause_no_evidence_and_recovery_fails_friendly_error(monkeypatch):
    stats_rec = []
    monkeypatch.setattr(elg, "_log_stats", lambda *a, **k: stats_rec.append(a))
    _stub_auto_websearch(monkeypatch)
    monkeypatch.setattr(elg, "APP", _FakeAppMidTurnCrash(tool_result={"results": []}))
    def _fail_llm(*a, **k):
        raise Exception("recovery model down")
    monkeypatch.setattr(AG, "llm_chat", _fail_llm)
    evs = asyncio.run(_collect_stream("永恒轮回是什么意思？"))
    err = next(ev for ev in evs if ev["type"] == "error")
    assert "智能体暂时出错" in err["content"] or "暂时" in err["content"]
    assert "peer closed" not in err["content"] and "Exception" not in err["content"], "不暴露内部细节/stack trace"
    turns = [r for r in _trace_lines() if r["type"] == "turn"]
    assert turns and turns[-1]["error"]                # 观测: 失败轮的轨迹落盘
    assert stats_rec and stats_rec[-1][3] and "search_books" in stats_rec[-1][3], \
        "stats error 路径工具数不再硬编码 0（含引擎自动补充的 websearch）"


def test_stream_agent_partial_answer_before_crash_kept(monkeypatch):
    class _CrashAfterAnswer:
        async def astream(self, inputs, config, stream_mode="messages"):
            yield (AIMessageChunk(content="回答已经开始流式输出：权力意志是自我克服的冲动。"), {"langgraph_node": "agent"})
            raise Exception("peer closed connection without sending complete message body")
    monkeypatch.setattr(elg, "APP", _CrashAfterAnswer())
    evs = asyncio.run(_collect_stream("权力意志"))
    types = [ev["type"] for ev in evs]
    assert "error" not in types
    done = next(ev for ev in evs if ev["type"] == "done")
    text = "".join(ev.get("content", "") for ev in evs if ev["type"] == "token")
    assert "权力意志" in text and done["tool_loop"]["recovered_after_error"] is True


# ═══════════════════════════════════════════════════════
# A5 防御性流帧（'AIMessage' object has no attribute 'tool_call_chunks' 修复）
# ═══════════════════════════════════════════════════════
def test_stream_agent_tolerates_full_aimessage_chunk(monkeypatch):
    class _FullMessageApp:
        async def astream(self, inputs, config, stream_mode="messages"):
            # 完整 AIMessage（无 tool_call_chunks 属性）——2026-08-30 三连错误的触发形态
            yield AIMessage(content="完整的回答消息对象。"), {"langgraph_node": "agent"}
    monkeypatch.setattr(elg, "APP", _FullMessageApp())
    evs = asyncio.run(_collect_stream("测试问题"))
    types = [ev["type"] for ev in evs]
    assert "error" not in types
    text = "".join(ev.get("content", "") for ev in evs if ev["type"] == "token")
    assert "完整的回答消息对象" in text


# ═══════════════════════════════════════════════════════
# 协议兼容回归
# ═══════════════════════════════════════════════════════
def test_stream_agent_signature_backward_compatible():
    import inspect
    sig = inspect.signature(elg.stream_agent)
    params = list(sig.parameters)
    assert params[:5] == ["req_message", "history", "agent", "custom_instructions", "language"]
    assert all(sig.parameters[p].kind == inspect.Parameter.POSITIONAL_OR_KEYWORD for p in params[:5])
    assert sig.parameters["conversation_id"].default is None
    assert sig.parameters["message_id"].default is None


def test_done_event_carries_tool_loop_state(monkeypatch):
    monkeypatch.setattr(elg, "APP", _FakeAppMidTurnCrash(
        tool_result={"results": [{"book_title": "查", "chapter_title": "夜歌", "snippet": "我是光"}]},
        recovery_answer="回答正文：权力意志是自我克服的冲动。"))
    monkeypatch.setattr(AG, "llm_chat", lambda *a, **k:
                        {"choices": [{"message": {"content": ""}}]})
    evs = asyncio.run(_collect_stream("测试", conversation_id="conv-x", message_id="msg-y"))
    done = next(ev for ev in evs if ev["type"] == "done")
    tl = done["tool_loop"]
    assert tl["invocation_id"] and tl["budget"]["cfg"]["hard_total"] == AR.TOOL_BUDGET["hard_total"]
    assert tl["budget"]["total_executed"] >= 0
    assert tl["recovered_after_error"] == True  # stream_error 已发生 → 如实审计
    turns = [r for r in _trace_lines() if r["type"] == "turn"]
    assert turns[-1]["conversation_id"] == "conv-x" and turns[-1]["message_id"] == "msg-y"
