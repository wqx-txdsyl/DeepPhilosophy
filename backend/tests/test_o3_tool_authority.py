# -*- coding: utf-8 -*-
"""O3 — Tool Authority / Main-Agent-Owned Research Control（行为回归测试）

架构契约（见 docs/PHIAGENT_O3_TOOL_AUTHORITY.md）:
  Main Agent: "我要调用这个工具。"
  Runtime:    "schema / 精确重复 / 硬资源上限 机械上是否允许？"
              YES → execute   （绝不追加"但你其实已经查够了"）

runtime 唯一保留的拒绝/停止理由（全部机械可判定）:
  RESOURCE_CEILING_REACHED / EXACT_DUPLICATE_REUSED / 未知工具 / 执行错误（机械回包）
语义类控制（义务配额 / 查询族相似 / obligations_satisfied 总闸 / no_gain force /
sufficiency force / soft 预算提示 / 强制专用工具路由 / 重入拦截）全部 CONTROL_EFFECT = 0。

T1–T14 走 production path（真实 tools_node / 真实图 / 脚本化假 LLM + 工具桩）。
"""
import asyncio
import json
import os
import sys
from types import SimpleNamespace

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import langchain_core
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.tools import StructuredTool
import pytest

import agent_runtime as AR
import engine_langgraph as EG
import reasoning_plan as RP
import tool_contracts as TC
import routes.agent as AG
import agents as AGENTS


# ═══════════════════════════════════════════════════════
# tools_node 直驱 harness（带完整治理状态: ledger/budget/guard/rstate/reentry/raw_log）
# ═══════════════════════════════════════════════════════
_STUB_CALLS = {}


def _tool(name, fn):
    return SimpleNamespace(name=name, func=fn)


def _stub_tools():
    _STUB_CALLS.clear()
    def _wrapped(n, f):
        return _tool(n, lambda **a: (_STUB_CALLS.setdefault(n, []).append(a) or f(**a)))
    return [
        _wrapped("search_books", lambda query, **k:
                 ({"results": []} if "库中不存在" in query else
                  {"results": [{"book_title": "论语", "chapter_title": "先进篇",
                                "book_id": "d9272a80942a", "chapter_idx": 13,
                                "snippet": f"命中（query={query}）"}]})),
        _wrapped("get_chapter", lambda book_id, chapter_idx, **k:
                 {"book_id": book_id, "chapter_idx": chapter_idx,
                  "title": "先进篇", "text": "鲁人为长府。夫人不言，言必有中。"}),
        _wrapped("get_book_detail", lambda book_id, **k: {"book_id": book_id, "title": "论语"}),
        _wrapped("websearch", lambda query, **k: {"results": [{"title": "web", "snippet": "web hit"}]}),
        _wrapped("query_graph", lambda philosopher, **k: {"philosopher": philosopher, "relations": []}),
        _wrapped("compare_views", lambda topic_a, topic_b, **k: {
            "topic": [topic_a, topic_b],
            "citations": [{"book": "论语", "chapter": "先进篇", "book_id": "d9272a80942a",
                           "chapter_idx": 13, "snippet": "内部检索片段"}]}),
        _tool("strict_tool", lambda query: {"ok": query}),   # 位置参数 → 缺参即 TypeError（T9）
    ]


def _mk_state(calls, *, plan=None, budget=None, ledger=None, no_gain_streak=0,
              tool_count=0, forced=False):
    question = "「言必有中」的出处是什么？"
    if plan is None:
        plan = RP.build_plan(question, "general", "zh")
    retrievals = set(EG.RETRIEVAL_TOOLS) | set(AGENTS.PHILO_EXTRA_TOOLS)
    st = {"messages": [AIMessage(content="", tool_calls=calls)],
          "guard": AR.DuplicateGuard(), "budget": budget or AR.ToolBudget(retrieval_tools=retrievals),
          "trace": AR.ToolLoopTrace("c-o3", "m-o3", "general"),
          "retrieval_state": AR.RetrievalState(),
          "obligation_ledger": ledger if ledger is not None else AR.ObligationLedger(plan),
          "verif_box": {"state": None, "term": "", "computed": False},
          "raw_tool_log": [], "agent": "general", "language": "zh",
          "tool_count": tool_count, "no_gain_streak": no_gain_streak,
          "retrieval_count": 0, "plan": plan, "user_message": question,
          "reentry": TC.SkillReentryTracker(), "forced": forced}
    return st


def _calls(seq):
    return [{"name": n, "args": a, "id": f"c{i}"} for i, (n, a) in enumerate(seq)]


async def _run_tools(state, tools):
    EG.get_tools = lambda agent: tools
    try:
        return await EG.tools_node(state)
    finally:
        pass


def _run_node(calls, tools=None, **kw):
    tools = tools or _stub_tools()
    st = _mk_state(_calls(calls), **kw)
    out = asyncio.run(_run_tools(st, tools))
    msgs = [m for m in out["messages"] if isinstance(m, ToolMessage)]
    return st, msgs


def _msg_text(m):
    return m.content if isinstance(m.content, str) else json.dumps(m.content, ensure_ascii=False)


# ═══════════════════════════════════════════════════════
# 引擎级 harness（与 test_o2 同口径, 另捕获每轮 prompt 供注入断言）
# ═══════════════════════════════════════════════════════
class ScriptedChat(BaseChatModel):
    script: list = []
    idx: int = 0
    prompts: list = []

    @property
    def _llm_type(self):
        return "scripted-o3"

    def bind_tools(self, tools, **kwargs):
        return self

    def _next_msg(self):
        if self.idx >= len(self.script):
            raise AssertionError("脚本耗尽: 引擎发起了脚本之外的 LLM invocation")
        m = self.script[self.idx]
        self.idx += 1
        return m

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        self.prompts.append(list(messages))
        msg = self._next_msg()
        return langchain_core.outputs.ChatResult(
            generations=[langchain_core.outputs.ChatGeneration(message=msg)])

    def _stream(self, messages, stop=None, run_manager=None, **kwargs):
        from langchain_core.messages import AIMessageChunk
        self.prompts.append(list(messages))
        msg = self._next_msg()
        text = msg.content or ""
        for i in range(0, len(text), 12):
            yield langchain_core.outputs.ChatGenerationChunk(
                message=AIMessageChunk(content=text[i:i + 12]))
        for tc in (msg.tool_calls or []):
            yield langchain_core.outputs.ChatGenerationChunk(
                message=AIMessageChunk(content="", tool_call_chunks=[
                    {"name": tc["name"], "args": json.dumps(tc.get("args") or {}, ensure_ascii=False),
                     "id": tc.get("id"), "index": 0, "type": "tool_call_chunk"}]))


def _msg(note, tool_calls=None):
    return AIMessage(content=note or "", tool_calls=tool_calls or [])


def _run_stream(question, script):
    real = (EG.get_llm, EG.get_tools, AG.llm_chat)
    chat = ScriptedChat(script=list(script), prompts=[])
    tools = _stub_tools()   # 每用例清一次计数; 图每轮 get_tools 复用同一列表（不清空）
    EG.get_llm = lambda: chat
    EG.get_tools = lambda agent: tools
    AG.llm_chat = lambda *a, **k: (_ for _ in ()).throw(AssertionError("禁止隐藏第二 writer"))

    async def _collect():
        evs = []
        async for ev in EG.stream_agent(question, [], agent="general", language="zh"):
            evs.append(ev)
        return evs, chat

    try:
        return asyncio.run(_collect())
    finally:
        EG.get_llm, EG.get_tools, AG.llm_chat = real


def _answer_text(evs):
    return "".join(str(e.get("content") or "") for e in evs if e.get("type") == "token")


def _done(evs):
    ds = [e for e in evs if e.get("type") == "done"]
    assert len(ds) == 1
    return ds[0]


# ═══════════════════════════════════════════════════════
# T1 — 第三次（及第 N 次）语义检索照常执行——无按意图配额拒绝
# ═══════════════════════════════════════════════════════
def test_t1_third_distinct_search_executes():
    seq = [("search_books", {"query": "言必有中"}),
           ("search_books", {"query": "言必有中 出处 先进篇"}),
           ("search_books", {"query": "闵子骞 鲁人为长府"})]
    st, msgs = _run_node(seq)
    assert len(msgs) == 3
    for m in msgs:
        assert "检索准入未通过" not in _msg_text(m)
        assert "RESOURCE_CEILING" not in _msg_text(m)
    assert len(_STUB_CALLS["search_books"]) == 3   # 三次全部真实执行


# ═══════════════════════════════════════════════════════
# T2 — sufficiency telemetry 为"满足"后, Main Agent 仍可读取
# ═══════════════════════════════════════════════════════
def test_t2_read_after_sufficiency_telemetry():
    plan = RP.build_plan("「言必有中」的出处是什么？", "general", "zh")
    ledger = AR.ObligationLedger(plan)
    ledger.obligations_satisfied = True          # telemetry: 义务已满足
    st, msgs = _run_node([("get_chapter", {"book_id": "d9272a80942a", "chapter_idx": 13})],
                         ledger=ledger)
    assert len(_STUB_CALLS["get_chapter"]) == 1   # 照常执行
    assert "obligation_satisfied" not in _msg_text(msgs[0])


# ═══════════════════════════════════════════════════════
# T3 — no_gain streak 之后换工具仍执行
# ═══════════════════════════════════════════════════════
def test_t3_continue_after_no_gain():
    st, msgs = _run_node([("query_graph", {"philosopher": "孔子"})], no_gain_streak=5)
    assert len(_STUB_CALLS["query_graph"]) == 1
    assert "无增益" not in _msg_text(msgs[0]) and "no_gain" not in _msg_text(msgs[0])


# ═══════════════════════════════════════════════════════
# T4 — telemetry 不足时 Main Agent 直接出 final：runtime 不强制工具
# ═══════════════════════════════════════════════════════
def test_t4_stop_despite_insufficiency():
    final = "苏格拉底的诘问法是一种通过提问揭示对话者信念中矛盾的方法。"
    evs, chat = _run_stream("苏格拉底的诘问法是什么？", [_msg(final)])
    # 零工具宣告 → 零工具事件; 无强制补研究; final 经 O2 validator 发布
    assert not [e for e in evs if e.get("type") in ("tool", "tool_start")]
    assert _answer_text(evs) == final
    assert _done(evs)["validation"]["result"]["ok"] is True
    # 所有 prompt 注入不含"必须检索/立即补跑"式强制
    for prompts in chat.prompts:
        for m in prompts:
            if m.__class__.__name__ == "SystemMessage":
                assert "必须调用" not in (m.content or "")
                assert "最后核验机会" not in (m.content or "")


# ═══════════════════════════════════════════════════════
# T5 — 本地空命中: 无自动 websearch; Main Agent 宣告则执行
# ═══════════════════════════════════════════════════════
def test_t5_no_auto_websearch_but_declared_executes():
    # ① 本地检索空命中, 模型不宣告 websearch 直接作答 → runtime 零 websearch
    evs, _ = _run_stream("库中不存在词项xyz的出处", [
        _msg("我先检索。", [{"name": "search_books", "args": {"query": "库中不存在词项xyz"}, "id": "c1"}]),
        _msg("本地库无命中（不等于该书不存在）。基于通识回答：这是一段生造词。")])
    assert _STUB_CALLS.get("websearch") is None
    done = _done(evs)
    assert done["causal"]["engine_cognitive_auto_tools"] == 0
    # ② 模型自主宣告 websearch → 执行
    evs2, _ = _run_stream("查一个需要上网的概念", [
        _msg("检索一下。", [{"name": "search_books", "args": {"query": "某些概念"}, "id": "c1"}]),
        _msg("本地不足，上网补充。", [{"name": "websearch", "args": {"query": "某些概念"}, "id": "c2"}]),
        _msg("综合本地与网络材料作答。")])
    assert len(_STUB_CALLS["websearch"]) == 1


# ═══════════════════════════════════════════════════════
# T6 — 精确重复: 复用旧结果且结果仍回传 Main Agent（机械措辞）
# ═══════════════════════════════════════════════════════
def test_t6_exact_duplicate_reuse_returns_result():
    st1, msgs1 = _run_node([("search_books", {"query": "言必有中"})])
    st2, msgs2 = _run_node([("search_books", {"query": "言必有中"})])
    st = _mk_state(_calls([("search_books", {"query": "言必有中"})]))
    st["guard"].record("search_books", {"query": "言必有中"}, True,
                       {"results": [{"book_title": "论语"}]})
    tools = _stub_tools()
    out = asyncio.run(_run_tools(st, tools))
    m = [x for x in out["messages"] if isinstance(x, ToolMessage)][0]
    assert "论语" in _msg_text(m)                       # 结果仍回传模型
    assert len(_STUB_CALLS.get("search_books") or []) == 0   # 未重复执行
    kw = m.additional_kwargs or {}
    assert kw.get("_reused") is True and kw.get("_budget_class") == "duplicate"


# ═══════════════════════════════════════════════════════
# T7 — 相似但实质不同的查询不是重复: 全部执行
# ═══════════════════════════════════════════════════════
def test_t7_similar_distinct_queries_all_execute():
    seq = [("search_books", {"query": "言必有中"}),
           ("search_books", {"query": "夫人不言 言必有中"}),
           ("search_books", {"query": "鲁人为长府 闵子骞"})]
    _run_node(seq)
    assert len(_STUB_CALLS["search_books"]) == 3


# ═══════════════════════════════════════════════════════
# T8 — 硬资源上限: RESOURCE_CEILING_REACHED（无"证据已充分"暗示）
# ═══════════════════════════════════════════════════════
def test_t8_hard_ceiling_mechanical_rejection():
    retrievals = set(EG.RETRIEVAL_TOOLS) | set(AGENTS.PHILO_EXTRA_TOOLS)
    budget = AR.ToolBudget(retrieval_tools=retrievals)
    for _ in range(20):
        budget.count("search_books", "unique", True, "new")
    st, msgs = _run_node([("search_books", {"query": "全新查询"})],
                         budget=budget, forced=True)
    assert "RESOURCE_CEILING_REACHED" in _msg_text(msgs[0])
    assert "证据" not in _msg_text(msgs[0]).split("机械资源约束")[0]
    assert not _STUB_CALLS.get("search_books")   # 未执行


# ═══════════════════════════════════════════════════════
# T9 — 非法 schema（缺参）: 机械拒绝, 结果仍回传
# ═══════════════════════════════════════════════════════
def test_t9_invalid_schema_mechanical_rejection():
    st, msgs = _run_node([("strict_tool", {})])
    assert len(msgs) == 1
    assert "error" in _msg_text(msgs[0])   # TypeError → 机械错误回包（结果完整回到模型）


# ═══════════════════════════════════════════════════════
# T10 — repair 轮工具权威: 此前有检索历史, 新 get_chapter 照常执行
# ═══════════════════════════════════════════════════════
def test_t10_repair_research_executes():
    # 轮 1: 常规检索（建立 family/no_gain 历史）
    _run_node([("search_books", {"query": "言必有中"})])
    # 轮 2（repair 语境: 高 no_gain + 义务已满足 telemetry）: 宣告新 get_chapter
    plan = RP.build_plan("「言必有中」的出处是什么？", "general", "zh")
    ledger = AR.ObligationLedger(plan)
    ledger.obligations_satisfied = True
    st, msgs = _run_node([("get_chapter", {"book_id": "d9272a80942a", "chapter_idx": 13})],
                         ledger=ledger, no_gain_streak=3)
    assert len(_STUB_CALLS["get_chapter"]) == 1
    assert "obligation_satisfied" not in _msg_text(msgs[0])


# ═══════════════════════════════════════════════════════
# T11 — 专用工具内部检索溯源: initiated_by=tool_internal + parent_tool_call_id
# ═══════════════════════════════════════════════════════
def test_t11_specialized_internal_provenance():
    st, msgs = _run_node([("compare_views", {"topic_a": "柏拉图灵魂", "topic_b": "亚里士多德灵魂"})])
    pseudo = [e for e in st["raw_tool_log"] if e.get("pseudo")]
    assert pseudo, "内部检索证据应入池（契约核验用）"
    for e in pseudo:
        assert e.get("initiated_by") == "tool_internal"
        assert e.get("parent_tool_call_id") == "c0"
        assert e.get("parent_tool") == "compare_views"
    # 非 pseudo 的 top-level 条目不得带 tool_internal 标记
    for e in st["raw_tool_log"]:
        if not e.get("pseudo"):
            assert e.get("initiated_by") != "tool_internal"


# ═══════════════════════════════════════════════════════
# T12 — 比较题不被强制 compare_views: 模型用常规检索也能完成
# ═══════════════════════════════════════════════════════
def test_t12_no_forced_specialized_routing():
    final = "柏拉图视灵魂为不朽的、与身体分离的实体；亚里士多德则认为灵魂是身体的形式（entelechy）。"
    script = [
        _msg("比较两家的灵魂观需要材料，先分别检索。",
             [{"name": "search_books", "args": {"query": "柏拉图 灵魂 不朽"}, "id": "c1"},
              {"name": "search_books", "args": {"query": "亚里士多德 灵魂 形式"}, "id": "c2"}]),
        _msg(final)]
    evs, chat = _run_stream("比较柏拉图与亚里士多德的灵魂观", script)
    assert _STUB_CALLS.get("compare_views") is None      # runtime 未强制专用工具
    assert len(_STUB_CALLS["search_books"]) == 2         # 常规检索全部执行
    assert final in _answer_text(evs)
    # prompt 注入不含 compare_views 强制路由指令（能力描述允许, 命令式路由禁止）
    for prompts in chat.prompts:
        for m in prompts:
            if m.__class__.__name__ == "SystemMessage":
                c = m.content or ""
                assert "首选直接调用" not in c and "不要先自行" not in c
                assert "（比较类问题路由）" not in c


# ═══════════════════════════════════════════════════════
# T13 — 无强制收口: 越过旧 soft/sufficiency 点后调用照常执行
# ═══════════════════════════════════════════════════════
def test_t13_no_forced_closeout_past_old_soft_point():
    seq = [(("search_books", {"query": f"言必有中 研究视角{i}"})) for i in range(9)]
    retrievals = set(EG.RETRIEVAL_TOOLS) | set(AGENTS.PHILO_EXTRA_TOOLS)
    budget = AR.ToolBudget(retrieval_tools=retrievals)   # soft_retrieval=8: 旧口径第 9 次前已提示收口
    st, msgs = _run_node(seq, budget=budget)
    assert len(_STUB_CALLS["search_books"]) == 9         # 全部执行（hard=20 未到）
    assert not any("RESOURCE_CEILING" in _msg_text(m) for m in msgs)


# ═══════════════════════════════════════════════════════
# T14 — 工具结果完整性: 每个宣告的 tool_call_id 都有终态回传
# ═══════════════════════════════════════════════════════
def test_t14_tool_outcome_completeness():
    seq = [("search_books", {"query": "言必有中"}),           # 执行
           ("search_books", {"query": "言必有中"}),           # 精确重复复用
           ("unknown_tool", {"x": 1}),                        # 未知工具
           ("strict_tool", {})]                               # schema 错误
    tools = _stub_tools()
    st = _mk_state(_calls(seq))
    out = asyncio.run(_run_tools(st, tools))
    msgs = [m for m in out["messages"] if isinstance(m, ToolMessage)]
    assert len(msgs) == len(seq)
    ids_sent = {c["id"] for c in _calls(seq)}
    ids_back = {m.tool_call_id for m in msgs}
    assert ids_sent == ids_back
    for m in msgs:
        assert _msg_text(m) != ""              # 每个终态都有内容回传

# ═══════════════════════════════════════════════════════
# §19 — 静态权威审计: 生产引擎源码不得再引用语义控制路径
# （与行为测试互补的结构性审计——防止控制路径以引用形式悄悄回归）
# ═══════════════════════════════════════════════════════
def test_t19_static_authority_audit():
    import inspect
    src = inspect.getsource(EG)
    # 剥除注释行——审计对象是可执行代码/文案, 历史注释不算引用
    code_only = "\n".join(ln for ln in src.splitlines() if not ln.strip().startswith("#"))
    # 语义拒绝回包文案（原 ledger/reentry 准入拒绝路径）不得存在
    for banned in ("检索准入未通过", "技能重入被拦截", "已达核验配额", "最后核验机会",
                   "收口轮禁止新检索", "（检索收敛）"):
        assert banned not in code_only, f"语义控制文案残留: {banned}"
    # 语义强制源（directive/verdict/hint）不得再被引擎消费
    for banned_ref in ("NO_GAIN_FORCE_DIRECTIVE", "NO_GAIN_WARN_HINT", "SOFT_BUDGET_HINT",
                       "SUFFICIENCY_FORCE", "sufficiency_hint", "sufficiency_verdict",
                       "ADMISSION_REJECT_FORCE", "no_gain_verdict", "_read_hint_sent"):
        assert banned_ref not in src, f"语义强制源被引擎引用: {banned_ref}"
    # admit 调用只允许 telemetry 形态（不消费 ok 判定）
    assert "ok, reason" not in src
    assert '"_admitted": False' not in src
    # 机械门保留
    for kept in ("RESOURCE_CEILING_REACHED", "hard_reached"):
        assert kept in src
