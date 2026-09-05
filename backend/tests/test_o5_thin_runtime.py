# -*- coding: utf-8 -*-
"""O5 — Thin Runtime / Mechanical Core Consolidation（行为回归测试）

任务书 §17 T1–T12。O5 后 runtime 只剩机械执行层:
  context assembly / tool schema+execution / hard ceilings / exact duplicate reuse /
  timeouts / safety / evidence recording / quote+citation validation / repair / SSE。
旧义务台账整类删除（事实并入 EvidenceState → done.evidence.facts）;
VERIFY_LATER 机制 / live_citation_sanitize / 伪工具记录 / 死 SSE 事件全部消失。

测试走 production path（真实 LangGraph 图 + 真实工具桩 + 脚本化假 LLM）,
harness 与 test_o1/test_o2/test_o3 同口径。
"""
import asyncio
import inspect
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
import evidence_contract as EC
import final_validator as FV
import quote_bound as QB
import routes.agent as AG
import agents as AGENTS
from evidence_contract import EvidenceState


# ═══════════════════════════════════════════════════════
# harness A: production 图流（脚本化假 LLM + 工具桩; 与 test_o1/test_o2 同口径）
# ═══════════════════════════════════════════════════════
class ScriptedChat(BaseChatModel):
    script: list = []
    idx: int = 0

    @property
    def _llm_type(self):
        return "scripted-o5"

    def bind_tools(self, tools, **kwargs):
        return self

    def _next_msg(self):
        if self.idx >= len(self.script):
            raise AssertionError("脚本耗尽: 引擎发起了脚本之外的 LLM invocation")
        msg = self.script[self.idx]
        self.idx += 1
        return msg

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        msg = self._next_msg()
        return langchain_core.outputs.ChatResult(
            generations=[langchain_core.outputs.ChatGeneration(message=msg)])

    def _stream(self, messages, stop=None, run_manager=None, **kwargs):
        from langchain_core.messages import AIMessageChunk
        msg = self._next_msg()
        text = msg.content or ""
        for i in range(0, len(text), 12):
            yield langchain_core.outputs.ChatGenerationChunk(
                message=AIMessageChunk(content=text[i:i + 12]))
        for tc in (msg.tool_calls or []):
            yield langchain_core.outputs.ChatGenerationChunk(
                message=AIMessageChunk(
                    content="",
                    tool_call_chunks=[{"name": tc["name"],
                                       "args": json.dumps(tc.get("args") or {}, ensure_ascii=False),
                                       "id": tc.get("id"), "index": 0,
                                       "type": "tool_call_chunk"}]))


def _msg(note, tool_calls=None):
    return AIMessage(content=note or "", tool_calls=tool_calls or [])


_LUNYU_PASSAGE = ("鲁人为长府，闵子骞曰：“仍旧贯如之何？何必改作？”"
                  "子曰：“夫人不言，言必有中。”")
_BID = "d9272a80942a"   # 真实书目 id: 论语

_STUB_CALLS = {"search_books": [], "get_chapter": [], "compare_views": []}


def _stub_results():
    return {
        "search_books": lambda **a: (
            {"results": [{"book_title": "论语", "chapter_title": "先进篇", "book_id": _BID,
                          "chapter_idx": 13, "snippet": _LUNYU_PASSAGE, "score": 0.9}]}
            if "不存在词项" not in (a.get("query") or "") else {"results": []}),
        "get_chapter": lambda **a: (_STUB_CALLS["get_chapter"].append(a) or
                                    {"book_id": a.get("book_id"), "chapter_idx": a.get("chapter_idx"),
                                     "title": "先进篇", "text": "先进篇正文……" + _LUNYU_PASSAGE}),
        "get_book_detail": lambda **a: {"book_id": a.get("book_id"), "title": "论语",
                                        "chapters": [{"index": 13, "title": "先进篇"}]},
        "websearch": lambda **a: {"results": [{"title": "web", "snippet": "web hit"}]},
        "query_graph": lambda **a: {"philosopher": "孔子", "relations": []},
        "get_philosopher": lambda **a: {"name": a.get("name"), "region": "先秦"},
        "list_books": lambda **a: {"books": []},
        "query_database": lambda **a: {"records": []},
        "concept_trace": lambda **a: {"trace": []},
        "compare_views": lambda **a: (_STUB_CALLS["compare_views"].append(a) or
                                      {"topic": [a.get("topic_a"), a.get("topic_b")],
                                       "citations": [{"book": "论语", "chapter": "先进篇",
                                                      "book_id": _BID, "chapter_idx": 13,
                                                      "snippet": "专用工具内部检索片段"}]}),
    }


def _fake_tools():
    res = _stub_results()
    return [StructuredTool.from_function(func=fn, name=name, description=f"{name} stub")
            for name, fn in res.items()]


def _run_stream(question, script):
    for k in _STUB_CALLS:
        _STUB_CALLS[k] = []
    real_get_llm, real_get_tools, real_llm_chat = EG.get_llm, EG.get_tools, AG.llm_chat
    _chat = ScriptedChat(script=list(script))
    EG.get_llm = lambda: _chat
    EG.get_tools = lambda agent: _fake_tools()
    AG.llm_chat = lambda *a, **k: (_ for _ in ()).throw(AssertionError("收口路径不得调用隐藏 LLM"))

    async def _collect():
        evs = []
        async for ev in EG.stream_agent(question, [], agent="general", language="zh"):
            evs.append(ev)
        return evs

    try:
        return asyncio.run(_collect())
    finally:
        EG.get_llm, EG.get_tools, AG.llm_chat = real_get_llm, real_get_tools, real_llm_chat


def _of(evs, *types):
    return [e for e in evs if e.get("type") in types]


def _answer_text(evs):
    return "".join(e.get("content", "") for e in evs if e["type"] == "token")


def _done(evs):
    return [e for e in evs if e.get("type") == "done"][-1]


_R_SCRIPT = [
    _msg("我记得这句话可能与闵子骞有关，先定位原典。",
         [{"name": "search_books", "args": {"query": "言必有中 出处"}, "id": "c1"}]),
    _msg("检索已命中《论语·先进篇》，读取该章原文核对措辞。",
         [{"name": "get_chapter", "args": {"book_id": _BID, "chapter_idx": 13}, "id": "c2"}]),
    _msg("经原文核验确认，本句出自《论语·先进篇》。先前的记忆假设与原文一致。\n\n"
         "> " + _LUNYU_PASSAGE + "\n\n以上为最终核验回答。"),
]


# ═══════════════════════════════════════════════════════
# T1 Evidence facts replace obligation ledger
# ═══════════════════════════════════════════════════════
class TestT1EvidenceFacts:
    def test_search_read_quote_facts_recorded(self):
        evs = _run_stream("言必有中出处", _R_SCRIPT)
        done = _done(evs)
        facts = done["evidence"]["facts"]
        assert facts["primary_text_read"] is True            # 模型自己的 get_chapter 置位
        assert f"{_BID}#13" in facts["read_chapters"]
        assert facts["read_execs"] == 1
        assert facts["search_execs"] >= 1
        assert facts["source_candidate_found"] is True
        # quote 核验（同一轮 raw_tool_log 上）: blockquote 判 VERIFIED_EXACT
        assert done["quote_bound"]["summary"]["verified_exact"] >= 1

    def test_obligation_ledger_gone_from_done_and_runtime(self):
        evs = _run_stream("言必有中出处", _R_SCRIPT)
        done = _done(evs)
        assert "obligation_ledger" not in done
        # 旧义务台账类在 runtime 不复存在（dir 级负断言, 覆盖任何同名变体）
        assert not any("Obligation" in n for n in dir(AR))
        # 事实只随 Evidence Store 输出——done.evidence 仍是契约 dict 且带 facts 子键
        assert done["evidence"] is not None and "facts" in done["evidence"]
        assert "retrieved_count" in done["evidence"]         # 前端消费字段不受影响


# ═══════════════════════════════════════════════════════
# T2 Dead term removed
# ═══════════════════════════════════════════════════════
class TestT2DeadTermRemoved:
    def test_no_term_state_without_producer(self):
        ev = EvidenceState()
        # term 失去生产喂入口（O4-RP1 删 verif_box）→ O5 连字段一并删除
        for gone in ("term", "exact_quote_verified", "record", "verification_states"):
            assert not hasattr(ev, gone), gone
        snap = ev.snapshot()
        assert set(snap) == {"read_chapters", "search_execs", "read_execs",
                             "source_candidate_found", "primary_text_read"}
        # 归一真源唯一 = quote_bound.norm_q（agent_runtime 的重复实现已删）
        assert not hasattr(AR, "_QUOTE_NORM")
        assert QB.norm_q("言，必有中。") == "言必有中"

    def test_agent_state_fields_thinned(self):
        # AgentState: model_retries（write-only）/ obligation_ledger 字段已删
        ann = set(EG.AgentState.__annotations__)
        assert "model_retries" not in ann
        assert "obligation_ledger" not in ann
        assert "evidence_state" in ann


# ═══════════════════════════════════════════════════════
# T3 No dead verification policy
# ═══════════════════════════════════════════════════════
class TestT3NoDeadVerificationPolicy:
    def test_no_verify_now_later_or_source_constraint_symbols(self):
        # VERIFY_LATER 机械已删（quote_bound）; VERIFY_NOW / check_consistency 从未存在
        assert not hasattr(QB, "VERIFY_LATER_RE")
        assert not hasattr(QB, "VERIFY_LATER_OPEN_RE")
        assert not hasattr(FV, "check_consistency")
        assert not hasattr(FV, "VERIFY_LATER_MISSTATEMENT")
        assert not hasattr(EG, "verification_constraint_directive")
        # validator / 契约签名无 source_constraint / 意图分类参数（O4-RP1 收窄保持）
        for fn in (FV.validate_final_candidate, EC.build_evidence_contract):
            params = inspect.signature(fn).parameters
            for gone in ("source_constraint", "subject_authors", "verification_intent"):
                assert gone not in params, (fn.__name__, gone)
        # 生产模块源码无 VERIFY_NOW 控制符号
        import agent_runtime
        for mod in (EG, agent_runtime, FV, QB, EC):
            assert "VERIFY_NOW" not in inspect.getsource(mod), mod.__name__


# ═══════════════════════════════════════════════════════
# T4 Final validator intact
# ═══════════════════════════════════════════════════════
class TestT4FinalValidatorIntact:
    def test_pseudo_quote_still_rejected(self):
        raw_log = [{"name": "get_chapter", "args": {}, "result_summary": "",
                    "result_full": {"book_id": _BID, "book_title": "论语", "title": "先进篇",
                                    "text": _LUNYU_PASSAGE}}]
        fake = "原文如下：\n\n> 「这是一段凭记忆写出的引文文本足够长以触发逐字核验判定」\n"
        res = FV.validate_final_candidate(fake, raw_tool_log=raw_log, fallback_log=[])
        assert res.ok is False
        assert any(i.code == FV.UNSUPPORTED_EXACT_QUOTE for i in res.issues)
        # 真引文仍通过
        good = "核验如下：\n\n> " + _LUNYU_PASSAGE + "\n\n以上。"
        res2 = FV.validate_final_candidate(good, raw_tool_log=raw_log, fallback_log=[])
        assert res2.ok is True
        # 未核验 formal citation 仍拒绝
        res3 = FV.validate_final_candidate("见【《韩非子·五蠹》】所述。", raw_tool_log=[], fallback_log=[])
        assert res3.ok is False
        assert any(i.code == FV.UNVERIFIED_CITATION for i in res3.issues)


# ═══════════════════════════════════════════════════════
# T5 Tool authority intact（机械门, 无语义拒绝）
# ═══════════════════════════════════════════════════════
def _tools_node_state(calls, *, budget=None):
    retrievals = set(EG.RETRIEVAL_TOOLS) | set(AGENTS.PHILO_EXTRA_TOOLS)
    return {"messages": [AIMessage(content="", tool_calls=calls)],
            "guard": AR.DuplicateGuard(),
            "budget": budget or AR.ToolBudget(retrieval_tools=retrievals),
            "trace": AR.ToolLoopTrace("c-o5", "m-o5", "general"),
            "evidence_state": EvidenceState(),
            "raw_tool_log": [], "agent": "general", "language": "zh",
            "tool_count": 0, "forced": False}


def _run_tools_node(calls, *, budget=None):
    for k in _STUB_CALLS:
        _STUB_CALLS[k] = []
    tools = _fake_tools()
    EG.get_tools = lambda agent: tools
    st = _tools_node_state(calls, budget=budget)
    out = asyncio.run(EG.tools_node(st))
    msgs = [m for m in out["messages"] if isinstance(m, ToolMessage)]
    return st, msgs


class TestT5ToolAuthorityIntact:
    def test_hard_ceiling_is_the_only_denial_gate(self):
        retrievals = set(EG.RETRIEVAL_TOOLS) | set(AGENTS.PHILO_EXTRA_TOOLS)
        budget = AR.ToolBudget(retrieval_tools=retrievals,
                               cfg={"hard_retrieval": 1, "hard_total": 1})
        budget.count("search_books", "unique", True, "new")   # total_executed → 1（hard 达标）
        st, msgs = _run_tools_node(
            [{"name": "get_chapter", "args": {"book_id": _BID, "chapter_idx": 13}, "id": "c1"}],
            budget=budget)
        assert len(msgs) == 1
        assert "RESOURCE_CEILING_REACHED" in msgs[0].content
        # 机械资源约束文案——绝不暗含语义判断（且明确否认"库中无相关内容"推断）
        blob = msgs[0].content
        assert "检索准入未通过" not in blob and "义务" not in blob and "配额" not in blob
        assert "证据已充分" not in blob
        assert "不代表库中无相关内容" in blob
        assert _STUB_CALLS["get_chapter"] == []               # 确未执行

    def test_unknown_tool_mechanical_error_only(self):
        st, msgs = _run_tools_node([{"name": "no_such_tool", "args": {}, "id": "c2"}])
        assert "未知工具" in msgs[0].content


# ═══════════════════════════════════════════════════════
# T6 No fake tool record
# ═══════════════════════════════════════════════════════
class TestT6NoFakeToolRecord:
    def test_tool_internal_retrieval_keeps_honest_provenance(self):
        st, msgs = _run_tools_node(
            [{"name": "compare_views", "args": {"topic_a": "柏拉图灵魂", "topic_b": "亚里士多德灵魂"},
              "id": "cv1"}])
        pseudo = [e for e in st["raw_tool_log"] if e.get("pseudo")]
        assert pseudo, "工具内部检索证据如实入池（契约核验用）"
        for e in pseudo:
            # 伪装成 Main Agent 亲自宣告的 top-level search 是禁止项
            assert e.get("initiated_by") == "tool_internal"
            assert e.get("parent_tool_call_id") == "cv1"
            assert e.get("parent_tool") == "compare_views"
            assert e["name"] == "search_books" and e.get("args", {}).get("query", "").startswith("[")
        # 内部检索绝不真实执行 search_books（无 fake top-level call）
        assert _STUB_CALLS["search_books"] == []


# ═══════════════════════════════════════════════════════
# T7 Event vocabulary
# ═══════════════════════════════════════════════════════
_DEAD_EVENT_TYPES = {"thought_stream", "thought", "reasoning_summary",
                     "answer_retract", "auto_read"}
_EVENT_VOCABULARY = {"status", "thinking_summary", "thinking_summary_delta",
                     "tool_start", "tool_note", "tool", "tool_cancel", "token",
                     "validation_failed", "error", "done", "suggestions"}


class TestT7EventVocabulary:
    def test_normal_request_emits_no_dead_events(self):
        evs = _run_stream("言必有中出处", _R_SCRIPT)
        types = {e["type"] for e in evs}
        assert types & _DEAD_EVENT_TYPES == set(), types & _DEAD_EVENT_TYPES
        assert types <= _EVENT_VOCABULARY, types - _EVENT_VOCABULARY

    def test_zero_tool_request_vocabulary_clean(self):
        script = [_msg("虚无主义指价值根基的崩塌。这一回答直接给出，无需检索。")]
        evs = _run_stream("什么是虚无主义？", script)
        types = {e["type"] for e in evs}
        assert types & _DEAD_EVENT_TYPES == set()
        assert types <= _EVENT_VOCABULARY
        assert "tool" not in types and "tool_start" not in types


# ═══════════════════════════════════════════════════════
# T8 Public ownership（thinking / activity / answer 三通道）
# ═══════════════════════════════════════════════════════
class TestT8PublicOwnership:
    def test_three_channels_attributed_correctly(self):
        evs = _run_stream("言必有中出处", _R_SCRIPT)
        # thinking 通道: 只能来自 Main Agent
        notes = _of(evs, "thinking_summary", "thinking_summary_delta")
        assert notes, "公开工作笔记应存在"
        assert all(n.get("initiated_by") == "main_agent" for n in notes)
        # activity 通道: 机械注记 / validator 状态, 绝不冒充思考
        activities = _of(evs, "tool_note")
        assert activities
        assert all(a.get("initiated_by") in ("runtime_mechanical", "validator") for a in activities)
        assert all(not a.get("activity") or a.get("initiated_by") != "main_agent" for a in activities)
        # 工具通道: 宣告/执行归属 Main Agent（runtime 只机械执行）
        tools = _of(evs, "tool", "tool_start")
        assert all(t.get("initiated_by") == "main_agent" for t in tools)
        # answer 通道: 可见正文 = 模型最终候选原样（runtime 零追加/零改写）
        final_text = _R_SCRIPT[-1].content
        assert _answer_text(evs) == final_text


# ═══════════════════════════════════════════════════════
# T9 Hard ceiling（机械回包, 无 ghostwrite / 无多余 closeout invocation）
# ═══════════════════════════════════════════════════════
class TestT9HardCeiling:
    def test_ceiling_mechanical_closeout_no_ghostwrite(self, monkeypatch):
        monkeypatch.setattr(AR, "TOOL_BUDGET", {"hard_retrieval": 1, "hard_total": 1})
        final = "预算耗尽，仅基于已读材料作答：此句见于《论语》先进篇，细节以库中原文为准。"
        script = [
            _msg("先检索。", [{"name": "search_books", "args": {"query": "言必有中"}, "id": "c1"}]),
            # hard 达标轮仍宣告工具 → 机械拒绝（RESOURCE_CEILING_REACHED）, 补跑一轮后强制结束
            _msg("再补一次检索。", [{"name": "search_books", "args": {"query": "言必有中 原文"}, "id": "c2"}]),
            _msg(final),
        ]
        evs = _run_stream("言必有中出处", script)
        ceiling_tools = [t for t in _of(evs, "tool") if "RESOURCE_CEILING_REACHED" in (t.get("result") or "")]
        assert len(ceiling_tools) == 1, "硬上限后的新宣告被机械拒绝一次"
        # 无 ghostwrite: 可见正文 = 模型自己写的 final, runtime 零追加
        assert _answer_text(evs) == final
        done = _done(evs)
        assert done["validation"]["result"]["ok"] is True
        assert done["tool_loop"]["budget"]["hard"] is True
        assert done["final_ownership"]["runtime_factual_appends"] == 0
        # 机械收口: 无语义 closeout 措辞进入任何事件
        for e in evs:
            blob = str(e.get("content") or "") + str(e.get("thought") or "")
            assert "检索已收口" not in blob and "证据已充分" not in blob


# ═══════════════════════════════════════════════════════
# T10 Format discipline（blockquote == intended quotation）
# ═══════════════════════════════════════════════════════
class TestT10FormatDiscipline:
    def test_main_strategy_contains_blockquote_rule(self):
        prompt = EG._build_context_messages("general", "zh")[0].content
        # 短语级断言（不锁 exact wording）: 引用块只用于呈现原文/出处文本
        assert "blockquote" in prompt
        assert "引用块" in prompt
        assert "原文" in prompt and "出处" in prompt
        # 规则同时保留"凭记忆措辞不得作为逐字原文呈现"纪律
        assert "逐字" in prompt
        assert "记忆" in prompt
        # 主策略真源即引擎 SYSTEM_PROMPT_LG（O5: routes/agent 旧副本已删）
        assert prompt.startswith(EG.SYSTEM_PROMPT_LG[:40])
        assert not hasattr(AG, "SYSTEM_PROMPT")


# ═══════════════════════════════════════════════════════
# T11 Temporal persona intact
# ═══════════════════════════════════════════════════════
class TestT11TemporalPersonaIntact:
    def test_temporal_directive_still_injected_for_philosopher(self):
        msgs = EG._build_context_messages("nietzsche", "zh",
                                          user_message="以1888年的你谈谈永恒轮回。")
        content = msgs[0].content
        detected = AGENTS.detect_temporal("以1888年的你谈谈永恒轮回。")
        assert detected["detected"] and 1888 in detected["years"]
        assert "【时期要求】" in content, "时期人格上下文不受 runtime cleanup 影响"
        assert "1888年→late" in content
        # 人格保持提醒仍在
        assert "你就是你" in content or "内心独白" in content

    def test_general_agent_gets_no_temporal_layer(self):
        msgs = EG._build_context_messages("general", "zh",
                                          user_message="以1888年的你谈谈永恒轮回。")
        assert "【时期要求】" not in msgs[0].content

    def test_nietzsche_prompt_discipline_intact(self):
        # O5 只删了与 thinking 通道冲突的"工具调用前不要输出任何文字"铁律并修复编号;
        # 人格、语言与伦理边界纪律不受影响
        p = AGENTS.NIETZSCHE_PROMPT
        assert "查拉图斯特拉的作者" in p
        assert "禁止用英文思考" in p
        assert "我的锤子砸向偶像, 不砸向活人" in p
        assert "工具调用前不要输出任何文字" not in p


# ═══════════════════════════════════════════════════════
# T12 Repair intact
# ═══════════════════════════════════════════════════════
class TestT12RepairIntact:
    def test_validator_fail_goes_back_to_same_agent(self):
        bad_final = "结论：原文如下——\n\n> 「这是一段凭记忆写出的引文文本足够长以触发核验逻辑」\n"
        good_final = ("经核验更正：上一稿引文未经原文支持, 现予撤回。"
                      "「言必有中」出自《论语·先进篇》孔子评价闵子骞之语, 以库中原文为准。")
        script = _R_SCRIPT[:2] + [_msg(bad_final), _msg(good_final)]
        evs = _run_stream("言必有中出处", script)
        answer = _answer_text(evs)
        done = _done(evs)
        assert done["validation"]["repairs_used"] == 1
        assert done["validation"]["repair_protocol"] == "same_main_agent"
        assert good_final in answer and "这是一段凭记忆写出的引文" not in answer
        # repair 反馈是 validator 发起的中性 activity, 不产生 runtime 代写正文
        vb = [e for e in _of(evs, "tool_note") if e.get("initiated_by") == "validator"]
        assert vb, "validator 状态经 activity 通道披露"
