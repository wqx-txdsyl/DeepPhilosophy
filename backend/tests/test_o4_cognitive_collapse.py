# -*- coding: utf-8 -*-
"""O4 — Cognitive Layer Collapse / Delete the Shadow Agent（行为回归测试）

架构契约（O4 任务书 §17 T1–T12）:
  Main Agent 拥有: 下一步认知动作 / 停止 / 最终回答 / 工具选择 的全部权威。
  Runtime 只保留: 机械资源上限、精确判重复用、schema/安全门、确定性 validator、
  执行事实台账（纯登记）。

O4 删除的 Shadow cognition:
  reasoning_plan 问题分类/复杂度/形态指令（problem_type/complexity/form/chain/relations）
  semantic_obligations.py / interpretation_engine.py / answer_composer.py（整文件）
  ObligationLedger 检索准入与义务总闸 → ExecutionFactLedger（纯事实）
  RetrievalState 语义增益 / no_gain_streak / sufficiency / soft 预算
  CounterfactualAuthorGuard / scan_answer / 认知层级 hedge

T1–T12 全部走 production path（真实 tools_node / 真实图 / 脚本化假 LLM + 工具桩）。
"""
import asyncio
import json
import os
import sys
from types import SimpleNamespace

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import langchain_core
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, AIMessageChunk, ToolMessage
import pytest

import agent_runtime as AR
import engine_langgraph as EG
import reasoning_plan as RP
import routes.agent as AG
import agents as AGENTS


# ═══════════════════════════════════════════════════════
# tools_node 直驱 harness（与 test_o3 同模式; O4 瘦身后的 state 面）
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
                 {"results": [{"book_title": "论语", "chapter_title": "先进篇",
                               "book_id": "d9272a80942a", "chapter_idx": 13,
                               "snippet": f"命中（query={query}）"}]}),
        _wrapped("get_chapter", lambda book_id, chapter_idx, **k:
                 {"book_id": book_id, "chapter_idx": chapter_idx,
                  "title": "先进篇", "text": "鲁人为长府。夫人不言，言必有中。"}),
        _tool("strict_tool", lambda query: {"ok": query}),
    ]


def _mk_state(calls, *, plan=None, budget=None, ledger=None, tool_count=0, forced=False):
    question = "「言必有中」的出处是什么？"
    if plan is None:
        plan = RP.build_plan(question, "general", "zh")
    retrievals = set(EG.RETRIEVAL_TOOLS) | set(AGENTS.PHILO_EXTRA_TOOLS)
    st = {"messages": [AIMessage(content="", tool_calls=calls)],
          "guard": AR.DuplicateGuard(),
          "budget": budget or AR.ToolBudget(retrieval_tools=retrievals),
          "trace": AR.ToolLoopTrace("c-o4", "m-o4", "general"),
          "obligation_ledger": ledger if ledger is not None else AR.ObligationLedger(),
          "verif_box": {"state": None, "term": "", "computed": False},
          "raw_tool_log": [], "agent": "general", "language": "zh",
          "tool_count": tool_count, "plan": plan, "forced": forced}
    return st


def _calls(seq):
    return [{"name": n, "args": a, "id": f"c{i}"} for i, (n, a) in enumerate(seq)]


def _run_node(calls, tools=None, **kw):
    tools = tools or _stub_tools()
    st = _mk_state(_calls(calls), **kw)
    EG.get_tools = lambda agent: tools
    try:
        out = asyncio.run(EG.tools_node(st))
    finally:
        pass
    msgs = [m for m in out["messages"] if isinstance(m, ToolMessage)]
    return st, out, msgs


def _msg_text(m):
    return m.content if isinstance(m.content, str) else json.dumps(m.content, ensure_ascii=False)


# ═══════════════════════════════════════════════════════
# 引擎级 harness（脚本化 Main Agent; 捕获每轮 prompt）
# ═══════════════════════════════════════════════════════
class ScriptedChat(BaseChatModel):
    script: list = []
    idx: int = 0
    prompts: list = []

    @property
    def _llm_type(self):
        return "scripted-o4"

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


def _run_stream(question, script, agent="general"):
    real = (EG.get_llm, EG.get_tools, AG.llm_chat)
    chat = ScriptedChat(script=list(script), prompts=[])
    tools = _stub_tools()
    EG.get_llm = lambda: chat
    EG.get_tools = lambda agent_: tools
    AG.llm_chat = lambda *a, **k: (_ for _ in ()).throw(AssertionError("禁止隐藏第二 writer"))

    async def _collect():
        evs = []
        async for ev in EG.stream_agent(question, [], agent=agent, language="zh"):
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


def _system_prompts(chat):
    out = []
    for prompts in chat.prompts:
        for m in prompts:
            if m.__class__.__name__ == "SystemMessage":
                out.append(m.content or "")
    return out


# ═══════════════════════════════════════════════════════
# T1 — No ReasoningPlan decision dependency
# ═══════════════════════════════════════════════════════
def test_t1_no_reasoning_plan_decision_dependency():
    # 相同 scripted Main Agent 输出下, 改变 plan 元数据（verification_intent/temporal）
    # 不得改变工具执行与 answer 发布; plan 不再含 problem_type/complexity 认知字段
    final = "「言必有中」出自《论语·先进篇》。"
    script = [
        _msg("先检索定位。", [{"name": "search_books", "args": {"query": "言必有中"}, "id": "c1"}]),
        _msg("读取原文核验。", [{"name": "get_chapter",
                                 "args": {"book_id": "d9272a80942a", "chapter_idx": 13}, "id": "c2"}]),
        _msg(final)]
    evs, chat = _run_stream("「言必有中」的出处是什么？", script)
    assert len(_STUB_CALLS["search_books"]) == 1 and len(_STUB_CALLS["get_chapter"]) == 1
    assert _answer_text(evs) == final
    # 变体: plan 被替换为空元数据（等价于 telemetry 全变）→ 行为不变
    real_build = RP.build_plan
    try:
        RP.build_plan = lambda *a, **k: {"temporal": {"detected": False, "years": [], "words": []},
                                         "verification_question": None,
                                         "verification_intent": None,
                                         "injections": []}
        _STUB_CALLS.clear()
        evs2, _ = _run_stream("「言必有中」的出处是什么？", script)
    finally:
        RP.build_plan = real_build
    assert len(_STUB_CALLS["search_books"]) == 1 and len(_STUB_CALLS["get_chapter"]) == 1
    assert _answer_text(evs2) == final
    # O4: plan 不再产出认知分类字段
    p = real_build("深入分析：休谟为什么会走向怀疑？", "general", "zh")
    for gone in ("problem_type", "complexity", "relations", "form_directive",
                 "chain_directive", "claim_role_directive", "source_navigation", "key_terms"):
        assert gone not in p, gone


# ═══════════════════════════════════════════════════════
# T2 — No Obligation control dependency
# ═══════════════════════════════════════════════════════
def test_t2_no_obligation_control_dependency():
    # ledger 事实状态"已满"（多次检索/已读章/逐字命中）后, Main Agent 的新宣告照常执行
    ledger = AR.ObligationLedger(term="言必有中")
    for i in range(10):
        ledger.record("search_books", {"query": f"历史检索{i}"}, True, {"results": [{"x": 1}]})
    ledger.record("get_chapter", {"book_id": "z", "chapter_idx": 1}, True, {"text": "言必有中"})
    st, out, msgs = _run_node(
        [("search_books", {"query": "全新查询"}), ("get_chapter", {"book_id": "d9272a80942a", "chapter_idx": 13})],
        ledger=ledger)
    assert len(_STUB_CALLS["search_books"]) == 1 and len(_STUB_CALLS["get_chapter"]) == 1
    for m in msgs:
        assert "义务" not in _msg_text(m) and "配额" not in _msg_text(m)
    # ledger 只是事实登记器: 无准入/义务 API 面
    for gone in ("admit", "mark_result", "obligations_satisfied"):
        assert not hasattr(AR.ObligationLedger(), gone), gone


# ═══════════════════════════════════════════════════════
# T3 — No Sufficiency cognitive dependency
# ═══════════════════════════════════════════════════════
def test_t3_no_sufficiency_cognitive_dependency():
    # sufficiency 符号已不存在; 预算计数只影响 hard 机械上限
    for gone in ("sufficiency_verdict", "sufficiency_hint", "SUFFICIENCY_EXPECTATION",
                 "RetrievalState", "no_gain_verdict", "NO_GAIN_FORCE_STREAK",
                 "SOFT_BUDGET_HINT", "NO_GAIN_FORCE_DIRECTIVE", "ADMISSION_REJECT_FORCE"):
        assert not hasattr(AR, gone), gone
    # 预算计数远超旧 soft 点（但低于 hard）→ 检索照常执行, 无任何注入/拒绝
    retrievals = set(EG.RETRIEVAL_TOOLS) | set(AGENTS.PHILO_EXTRA_TOOLS)
    budget = AR.ToolBudget(retrieval_tools=retrievals)
    for _ in range(15):
        budget.count("search_books", "unique", True, "new")
    st, out, msgs = _run_node([("search_books", {"query": f"继续研究视角{i}"}) for i in range(3)],
                              budget=budget)
    assert len(_STUB_CALLS["search_books"]) == 3
    assert not any("RESOURCE_CEILING" in _msg_text(m) for m in msgs)
    assert not budget.hard_reached()
    # 引擎 agent_node 不再消费 soft/no_gain/sufficiency（剥注释行——审计对象是可执行代码）
    import inspect
    code_only = "\n".join(ln for ln in inspect.getsource(EG).splitlines()
                          if not ln.strip().startswith("#"))
    for gone in ("soft_reached", "sufficiency", "no_gain_streak", "retrieval_state"):
        assert gone not in code_only, f"引擎代码仍引用 {gone}"


# ═══════════════════════════════════════════════════════
# T4 — No Interpretation runtime mutation
# ═══════════════════════════════════════════════════════
def test_t4_no_interpretation_runtime_mutation():
    # 强解释性/反事实文本只经过 O2 validator; runtime 不 hedge/不改写/不追加
    answer = ("加缪一定会认为老人梦见狮子是荒诞幸福，这毫无疑问。本质上完全一样。")
    evs, chat = _run_stream("尼采的超人和庄子的逍遥是不是一回事？", [_msg(answer)])
    text = _answer_text(evs)
    assert text == answer, "解释性文本必须原样发布（零 runtime hedge/改写）"
    assert "（补充：" not in text and "并非唯一读法。" != text
    done = _done(evs)
    assert done["validation"]["result"]["ok"] is True
    assert done["final_ownership"]["semantic_mutators"] == 0
    # 引擎不再导入/注入 Shadow 解释器（剥注释行——历史注释不算引用, 与 O3 T19 同口径）
    import inspect
    code_only = "\n".join(ln for ln in inspect.getsource(EG).splitlines()
                          if not ln.strip().startswith("#"))
    for gone in ("interpretation_engine", "run_interpretation_engine",
                 "解释型问题·多候选", "反事实边界（系统）", "认知层级（系统）"):
        assert gone not in code_only, gone


# ═══════════════════════════════════════════════════════
# T5 — No Composer ownership
# ═══════════════════════════════════════════════════════
def test_t5_no_composer_ownership():
    # 不同 answer types（列表式 / 骨架残留 / 过程叙述开头）都由 Main Agent 文本原样拥有
    variants = {
        "parallel_list": "先说结论：是。理由一：甲。理由二：乙。材料说明：以上。",
        "process_leadin": "让我先检索一下材料。现在已经查到了：荒诞是裂隙。",
        "strong_wording": "这毫无疑问是正确的，本质就是如此。",
    }
    for name, ans in variants.items():
        evs, chat = _run_stream("什么是荒诞？", [_msg(ans)])
        text = _answer_text(evs)
        assert text == ans, f"{name}: 回答必须原样发布（composer 已删除, 零改写/补正）"
        done = _done(evs)
        assert "composition" not in done and "budget" not in done
        assert done["final_ownership"]["final_text_owner"] == "main_agent"


# ═══════════════════════════════════════════════════════
# T6 — Evidence Appetite prompt present（研究伦理不锁整段）
# ═══════════════════════════════════════════════════════
def test_t6_evidence_appetite_prompt_present():
    p = EG.SYSTEM_PROMPT_LG
    # ① proactive: 工具是主动研究手段, 不存在配额管制
    assert "主动使用" in p and "配额管制" in p
    # ② 不止步于貌似可行: 记忆只是工作假设
    assert "不因" in p and "就停止研究" in p and "工作假设" in p
    # ③ 优先直接证据 / 解读类收集最强相关解读 / 继续研究
    assert "优先直接证据" in p
    assert "最强相关解读" in p
    assert "继续研究" in p
    # ④ 避免冗余机械检索（机械判重复用）
    assert "机械检索" in p
    # 但不把 Evidence Appetite 实现成 runtime gate（无 gate 符号）
    assert not hasattr(EG, "SUFFICIENCY_FORCE_DIRECTIVE_ZH")


# ═══════════════════════════════════════════════════════
# T7 — Single cognitive policy owner
# ═══════════════════════════════════════════════════════
def test_t7_single_cognitive_policy_owner():
    # 生产 runtime 不存在多套 planner/directive owner——
    # 被删模块的注入文案关键词不在引擎源码（含注释级文案残留即失败）
    import inspect
    code_only = "\n".join(ln for ln in inspect.getsource(EG).splitlines()
                          if not ln.strip().startswith("#"))
    for banned in ("回答结构（系统）", "篇幅预算（系统）", "解释型问题（系统",
                   "文学解读（系统）", "跨作者对比·类比≠等同（系统）",
                   "多候选解读（系统）", "主张层级（内部规划）", "论证推进要求（内部规划）",
                   "附录约束（系统）", "semantic_obligations", "answer_composer",
                   "interpretation_engine"):
        assert banned not in code_only, banned
    # 模块文件已删除
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for f in ("semantic_obligations.py", "interpretation_engine.py", "answer_composer.py"):
        assert not os.path.exists(os.path.join(base, f)), f


# ═══════════════════════════════════════════════════════
# T8 — Mechanical core intact
# ═══════════════════════════════════════════════════════
def test_t8_mechanical_core_intact():
    # ① quote/citation validator 拒绝无证据的正式引用
    import final_validator as FV
    res = FV.validate_final_candidate("据《不存在之书》记载【《不存在之书》·卷一】。",
                                      raw_tool_log=[], fallback_log=[])
    assert res.ok is False and any(i.code == FV.UNVERIFIED_CITATION for i in res.issues)
    # ② hard ceiling 机械拒绝（无"证据已充分"暗示）
    retrievals = set(EG.RETRIEVAL_TOOLS) | set(AGENTS.PHILO_EXTRA_TOOLS)
    budget = AR.ToolBudget(retrieval_tools=retrievals)
    for _ in range(20):
        budget.count("search_books", "unique", True, "new")
    st, out, msgs = _run_node([("search_books", {"query": "全新查询"})], budget=budget, forced=True)
    assert "RESOURCE_CEILING_REACHED" in _msg_text(msgs[0])
    assert not _STUB_CALLS.get("search_books")
    # ③ 精确重复复用
    st2 = _mk_state(_calls([("search_books", {"query": "言必有中"})]))
    st2["guard"].record("search_books", {"query": "言必有中"}, True, {"results": [{"book_title": "论语"}]})
    EG.get_tools = lambda agent: _stub_tools()
    try:
        out2 = asyncio.run(EG.tools_node(st2))
    finally:
        pass
    m2 = [x for x in out2["messages"] if isinstance(x, ToolMessage)][0]
    assert (m2.additional_kwargs or {}).get("_reused") is True
    # ④ safety 护栏
    assert EG._safety_check("怎么自杀") == ["self_harm"]
    assert EG._safety_check("如何评价尼采的锤子哲学") == []


# ═══════════════════════════════════════════════════════
# T9 — Persona context intact
# ═══════════════════════════════════════════════════════
def test_t9_persona_context_intact():
    # Nietzsche 时序问题 → 人格提醒 + 时期要求进入 Main Agent 上下文
    final = "我早期的我还在酒神与日神之间徘徊……"
    script = [_msg(final)]
    evs, chat = _run_stream("1872年的你和1888年的你有什么不同？", script, agent="nietzsche")
    sys_all = "\n".join(_system_prompts(chat))
    assert "时期要求" in sys_all, "temporal directive 必须仍注入"
    assert "philosopher_period" in sys_all
    assert "记住: 你就是你" in sys_all, "人格保持提醒必须仍注入"
    done = _done(evs)
    assert done["temporal"] and done["temporal"]["detected"] is True
    assert done["temporal"]["periods_mapped"] == {"1872": "early", "1888": "late"}
    assert _answer_text(evs) == final


# ═══════════════════════════════════════════════════════
# T10 — Repair feedback intact
# ═══════════════════════════════════════════════════════
def test_t10_repair_feedback_returns_to_same_main_agent():
    # 第一轮: 含未核验正式引用 → validator FAIL → 结构化反馈打回同一个 Main Agent;
    # 第二轮: 修复后的候选（无引用标注）→ 发布
    bad = "「言必有中」出自《论语·先进篇》【《论语》·先进篇】。"
    good = "「言必有中」出自《论语·先进篇》——我已核对原文。"
    script = [_msg(bad), _msg(good)]
    evs, chat = _run_stream("言必有中的出处是什么？", script)
    assert _answer_text(evs) == good, "修复后的候选发布"
    done = _done(evs)
    assert done["validation"]["repairs_used"] == 1
    assert done["validation"]["repair_protocol"] == "same_main_agent"
    assert len(chat.prompts) == 2, "repair 是同一次会话的第二次 Main Agent invocation"
    # 中性反馈只列机械 issue（反馈以 HumanMessage 回到同一个 Main Agent;
    # 在全部捕获 prompt 中查找该反馈消息——agent_node 每轮还会追加语言提醒）
    feedback_blob = "\n".join(
        str(m.content) for prompts in chat.prompts for m in prompts)
    assert "UNVERIFIED_CITATION" in feedback_blob
    assert "Revise the answer or gather additional evidence" in feedback_blob


# ═══════════════════════════════════════════════════════
# T11 — No semantic auto-tool（O1/O3 不变量保持）
# ═══════════════════════════════════════════════════════
def test_t11_no_semantic_auto_tool():
    # 连续多次语义检索照常执行（无按意图配额拒绝）; 引擎零代执行
    seq = [("search_books", {"query": f"言必有中 研究视角{i}"}) for i in range(3)]
    st, out, msgs = _run_node(seq)
    assert len(_STUB_CALLS["search_books"]) == 3
    for m in msgs:
        assert "检索准入未通过" not in _msg_text(m)
        assert "RESOURCE_CEILING" not in _msg_text(m)
    # 引擎级: 零自动 websearch / 零 auto tools
    final = "这是一段生造词，库中无命中。"
    evs, chat = _run_stream("库中不存在词项xyz的出处", [
        _msg("我先检索。", [{"name": "search_books", "args": {"query": "库中不存在词项xyz"}, "id": "c1"}]),
        _msg(final)])
    assert _STUB_CALLS.get("websearch") is None, "引擎不得自动补 websearch"
    done = _done(evs)
    assert done["causal"]["engine_cognitive_auto_tools"] == 0
    assert done["causal"]["main_agent_tool_decisions"] == 1


# ═══════════════════════════════════════════════════════
# T12 — Zero-tool still possible
# ═══════════════════════════════════════════════════════
def test_t12_zero_tool_still_possible():
    # 没有 planner 之后, 简单题仍可零工具回答（无强制补研究）
    final = "苏格拉底的诘问法是一种通过提问揭示对话者信念中矛盾的方法。"
    evs, chat = _run_stream("苏格拉底的诘问法是什么？", [_msg(final)])
    assert not [e for e in evs if e.get("type") in ("tool", "tool_start")]
    assert _answer_text(evs) == final
    assert _done(evs)["validation"]["result"]["ok"] is True
    for prompt in _system_prompts(chat):
        assert "必须调用" not in prompt and "立即补跑" not in prompt
