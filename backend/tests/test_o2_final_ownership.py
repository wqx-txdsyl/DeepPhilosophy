# -*- coding: utf-8 -*-
"""O2 — Final Answer Ownership / Validator → Main-Agent Repair Loop（行为回归测试）

架构契约（见 docs/PHIAGENT_O2_FINAL_ANSWER_OWNERSHIP.md）:
  ① 最终用户看到的自然语言答案只能由 Main Agent 写——runtime 零改写/零追加/零语义 retract。
  ② Final Candidate 先内部缓冲, 经确定性校验（final_validator）PASS 后才首次公开
     （INVALID_FINAL_PUBLICLY_STREAMED = false; 无 publish→retract→correct 模式）。
  ③ 校验 FAIL → 结构化 issues 以中性反馈打回同一个 Main Agent repair
     （repair 绑定完整工具集, 可继续研究; 上限 MAX_VALIDATION_REPAIRS = 2）。
  ④ 机械 formatter（工具标记/控制标签剥离、措辞净化）保留——不改变语义文本。

测试全部走 production path（真实 LangGraph 图 + 真实工具桩 + 脚本化假 LLM）,
复用 O1 的 harness 口径（含 AG.llm_chat 禁用桩——收口路径不得存在隐藏第二 writer）。
"""
import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import langchain_core
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.tools import StructuredTool
import pytest

import engine_langgraph as EG
import quote_bound as QB
import routes.agent as AG
import final_validator as FV
from final_validator import (ValidationResult, ValidationIssue, validate_final_candidate,
                             check_citations, check_quotes,
                             MAX_VALIDATION_REPAIRS)


# ═══════════════════════════════════════════════════════
# harness（与 test_o1_causal_loop.py 同口径）
# ═══════════════════════════════════════════════════════
class ScriptedChat(BaseChatModel):
    script: list = []
    idx: int = 0

    @property
    def _llm_type(self):
        return "scripted-o2"

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

_STUB_CALLS = {"websearch": [], "locate_exact_phrase": [], "get_chapter": []}


def _stub_results():
    return {
        "search_books": lambda **a: (
            {"results": [{"book_title": "论语", "chapter_title": "先进篇", "book_id": "lunyu",
                          "chapter_idx": 13, "snippet": _LUNYU_PASSAGE, "score": 0.9}]}
            if "不存在词项" not in (a.get("query") or "") else {"results": []}),
        "get_chapter": lambda **a: (_STUB_CALLS["get_chapter"].append(a) or
                                    {"book_id": a.get("book_id"), "chapter_idx": a.get("chapter_idx"),
                                     "title": "先进篇", "text": "先进篇正文……" + _LUNYU_PASSAGE}),
        "get_book_detail": lambda **a: {"book_id": a.get("book_id"), "title": "论语",
                                        "chapters": [{"index": 13, "title": "先进篇"}]},
        "websearch": lambda **a: (_STUB_CALLS["websearch"].append(a) or
                                  {"results": [{"title": "web", "snippet": "web hit"}]}),
        "query_graph": lambda **a: {"philosopher": "孔子", "relations": []},
        "get_philosopher": lambda **a: {"name": a.get("name"), "region": "先秦"},
        "list_books": lambda **a: {"books": []},
        "query_database": lambda **a: {"records": []},
        "concept_trace": lambda **a: {"trace": []},
        "locate_exact_phrase": lambda **a: (_STUB_CALLS["locate_exact_phrase"].append(a) or
                                            {"found": True, "hits": []}),
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
    return "".join(e.get("content", "") for e in _of(evs, "token"))


def _done(evs):
    ds = _of(evs, "done")
    assert len(ds) == 1
    return ds[0]


# 公共脚本片段: 工作笔记 → 检索 → 工作笔记 → 读取原文
_TOOLS_SCRIPT = [
    _msg("这句话可能与闵子骞有关，需要定位原典核验。",
         [{"name": "search_books", "args": {"query": "言必有中 出处"}, "id": "c1"}]),
    _msg("检索已定位《论语·先进篇》，下一步读取原文核对措辞。",
         [{"name": "get_chapter", "args": {"book_id": "lunyu", "chapter_idx": 13}, "id": "c2"}]),
]

# runtime 代写文本黑名单——O2 后任何公开事件都不得出现
_GHOSTWRITING_MARKS = ("据通行理解", "（与库中原文近似，非逐字）", "（原典核验：",
                       "（更正：", "（补充：先纠正一个前提", "（确定性边界：",
                       "（核验边界：", "（引用核验说明", "（说明：这一解读")


# ═══════════════════════════════════════════════════════
# T1 Unsupported exact quote → validator FAIL → same-agent repair → 发布修复文本
# ═══════════════════════════════════════════════════════
_SENTINEL_FAKE = "言必有中者，以其德之至也。闵子骞斯可谓恭俭矣"


class TestT1UnsupportedExactQuote:
    def test_fabricated_quote_rejected_and_repaired(self):
        bad_final = "结论：原文如下——\n\n> 「" + _SENTINEL_FAKE + "」\n"

        good_final = ("经重新整理：逐字核验后确认，「言必有中」出自孔子对闵子骞的评价，"
                      "原文为「鲁人为长府……夫人不言，言必有中」。")
        script = _TOOLS_SCRIPT + [_msg(bad_final), _msg(good_final)]
        evs = _run_stream("言必有中出处", script)
        answer = _answer_text(evs)
        done = _done(evs)
        # validator 拒绝 + repair 恰好发生一次
        assert done["validation"]["repairs_used"] == 1
        assert done["validation"]["result"]["ok"] is True          # 修复后候选通过
        assert any(i["code"] == "UNSUPPORTED_EXACT_QUOTE"
                   for i in done["validation"]["result"]["issues"]) is False  # issues 属于被拒候选, 不随 done 误报
        assert done["final_ownership"]["validator_repair_invocations"] == 1
        # 发布文本 = Main Agent 修复文本（runtime 零代笔）
        assert good_final in answer
        assert "repair" in json.dumps(done["validation"], ensure_ascii=False)

    def test_runtime_never_paraphrases(self):
        """runtime 不把伪引文转写为 paraphrase——转写只能由模型自己决定"""
        bad_final = "> 「" + _SENTINEL_FAKE + "」"
        script = _TOOLS_SCRIPT + [_msg(bad_final),
                                  _msg("最终回答：该句未能在库中逐字定位，无法作为原文引用。")]
        evs = _run_stream("言必有中出处", script)
        for e in evs:
            content = str(e.get("content", ""))
            for mark in ("据通行理解", "但我尚未在当前原典库中逐字核验"):
                assert mark not in content


# ═══════════════════════════════════════════════════════
# T2 NEAR quote presented as exact → FAIL → 模型自行标注近似
# ═══════════════════════════════════════════════════════
class TestT2NearQuote:
    def test_near_quote_repair_marks_approximate_by_itself(self):
        # 与原文仅一字之差（夫人→其人）→ NEAR（shingle 覆盖率 ~0.68）
        near_quote = _LUNYU_PASSAGE.replace("夫人不言", "其人不言")
        bad_final = "原文如下：\n\n> 「" + near_quote + "」\n\n（《论语·先进篇》）"
        good_final = ("说明：上一条引文与库中原文相近但未逐字核验，按近似转述处理——"
                      "「言必有中」确出自《论语·先进篇》。")
        script = _TOOLS_SCRIPT + [_msg(bad_final), _msg(good_final)]
        evs = _run_stream("言必有中出处", script)
        answer = _answer_text(evs)
        done = _done(evs)
        assert done["validation"]["repairs_used"] == 1
        assert good_final in answer
        # runtime 的自动近似标注不存在——标注必须来自模型自己
        assert "（与库中原文近似，非逐字）" not in answer

    def test_near_quote_validator_code(self):
        near_quote = _LUNYU_PASSAGE.replace("夫人不言", "其人不言")
        raw_log = [{"name": "get_chapter", "args": {}, "result_summary": "",
                    "result_full": {"book_title": "论语", "title": "先进篇", "text": _LUNYU_PASSAGE}}]
        audit, issues = check_quotes("引文：\n\n> 「" + near_quote + "」\n", raw_log)
        assert any(i.code == FV.NEAR_QUOTE_NOT_MARKED for i in issues)
        # 模型自行披露后 → 不再是 issue（披露文本位于引文之后, 处于 audit 视窗内）
        disclosed = ("引文：\n\n> 「" + near_quote + "」\n\n"
                     "（此句未逐字核验，凭记忆给出，按近似转述处理。）\n")
        audit2, issues2 = check_quotes(disclosed, raw_log)
        assert not any(i.code == FV.NEAR_QUOTE_NOT_MARKED for i in issues2)


# ═══════════════════════════════════════════════════════
# T3 Unverified formal citation → FAIL → repair；禁止 runtime 降级
# ═══════════════════════════════════════════════════════
class TestT3UnverifiedCitation:
    def test_unverified_citation_repaired_not_downgraded(self):
        bad_final = "「言必有中」出自【《韩非子·五蠹》】，孔子评价闵子骞时所说。"
        good_final = "「言必有中」出自《论语·先进篇》，孔子评价闵子骞时所说【《论语》·先进篇】。"
        script = _TOOLS_SCRIPT + [_msg(bad_final), _msg(good_final)]
        evs = _run_stream("言必有中出处", script)
        answer = _answer_text(evs)
        done = _done(evs)
        assert done["validation"]["repairs_used"] == 1
        assert good_final in answer
        assert "韩非子" not in answer            # 修复候选替换了未核验引用
        # runtime 不降级: 不存在降级说明文本, 也未把《韩非子》改为"一般提及"保留
        for mark in _GHOSTWRITING_MARKS:
            assert mark not in answer
        assert done["live_citation_sanitize"]["downgraded"] == 0

    def test_check_citations_codes(self):
        raw_log = [{"name": "search_books", "args": {}, "result_summary": "",
                    "result_full": {"results": [{"book_title": "论语", "chapter_title": "先进篇",
                                                 "snippet": _LUNYU_PASSAGE}]}}]
        verified, issues = check_citations("出自【《论语》·先进篇】与【《韩非子·五蠹》】。", raw_log)
        assert verified == 1
        assert len(issues) == 1 and issues[0].code == FV.UNVERIFIED_CITATION
        assert "韩非子" in issues[0].locator

    def test_template_placeholder_markers_skipped(self):
        """格式模板回显（【《书名》·章节】）不构成引用主张——机械跳过, 不打回 repair"""
        raw_log = [{"name": "search_books", "args": {}, "result_summary": "",
                    "result_full": {"results": [{"book_title": "论语", "chapter_title": "先进篇",
                                                 "snippet": _LUNYU_PASSAGE}]}}]
        verified, issues = check_citations("标注格式为【《书名》·章节】，如【《论语》·先进篇】。", raw_log)
        assert verified == 1 and issues == []

    def test_citation_placeholder_audit_C1_real_but_unbound(self):
        """C1: 真实书名但证据池未绑定的引用 → 仍必须 UNVERIFIED_CITATION"""
        verified, issues = check_citations("出自【《论语》·先进篇】。", [])
        assert verified == 0
        assert len(issues) == 1 and issues[0].code == FV.UNVERIFIED_CITATION

    def test_citation_placeholder_audit_C2_template_not_counted(self):
        """C2: 模板字面量既不计入 verified_citations, 也不产生 issue——它不是 citation"""
        raw_log = [{"name": "search_books", "args": {}, "result_summary": "",
                    "result_full": {"results": [{"book_title": "论语", "chapter_title": "先进篇",
                                                 "snippet": _LUNYU_PASSAGE}]}}]
        verified, issues = check_citations("格式见【《书名》·章节】。", raw_log)
        assert verified == 0 and issues == []   # 豁免=不算核验通过, 也不算违规

    def test_citation_placeholder_audit_C3_no_template_bypass(self):
        """C3: 真实书名 + 占位章节（【《论语》·章节】）不得借模板化绕过——照常打回"""
        verified, issues = check_citations("出自【《论语》·章节】。", [])
        assert verified == 0
        assert len(issues) == 1 and issues[0].code == FV.UNVERIFIED_CITATION


# ═══════════════════════════════════════════════════════
# T4 Stitched quote → validator 捕获（结构性）; 候选从不公开
# ═══════════════════════════════════════════════════════
class TestT4StitchedQuote:
    def test_stitched_detected_by_validator(self):
        # 两个等长句放在同一 get_chapter 文本的两个行单元中; 引文 = 两句拼接
        sent_a = "仁者爱人克己复礼"
        sent_b = "见利思义见危授命"
        raw_log = [{"name": "get_chapter", "args": {}, "result_summary": "",
                    "result_full": {"book_title": "礼记", "title": "坊记",
                                    "text": sent_a + "\n" + sent_b}}]
        stitched = sent_a + sent_b
        audit, issues = check_quotes("原文：\n\n> 「" + stitched + "」\n", raw_log)
        assert any(i.code == FV.STITCHED_QUOTE for i in issues)

    def test_stitched_candidate_never_public(self):
        """拼接候选被拒 → 换诚实答案发布; 全事件流无拼接文本"""
        sent_a = "仁者爱人克己复礼"
        sent_b = "见利思义见危授命"
        stitched = sent_a + sent_b
        bad_final = "> 「" + stitched + "」"
        good_final = "最终回答：该拼接引文不成立，逐字原文应以库中核验为准。"
        script = _TOOLS_SCRIPT + [_msg(bad_final), _msg(good_final)]
        evs = _run_stream("拼接检测", script)
        assert stitched not in _answer_text(evs)
        assert _done(evs)["validation"]["repairs_used"] == 1


# ═══════════════════════════════════════════════════════
# T5 First-pass valid final → repair_invocations=0, 语义文本零改动
# ═══════════════════════════════════════════════════════
class TestT5FirstPassValid:
    def test_valid_final_published_verbatim(self):
        final = ("核验结论：「言必有中」出自《论语·先进篇》，孔子评价闵子骞之语。\n\n"
                 "> 「" + _LUNYU_PASSAGE + "」\n\n"
                 "以上为原文【《论语》·先进篇】。")
        script = _TOOLS_SCRIPT + [_msg(final)]
        evs = _run_stream("言必有中出处", script)
        done = _done(evs)
        assert done["validation"]["repairs_used"] == 0
        assert done["validation"]["result"]["ok"] is True
        assert done["final_ownership"]["validator_repair_invocations"] == 0
        assert done["final_ownership"]["semantic_mutators"] == 0
        assert done["final_ownership"]["final_text_owner"] == "main_agent"
        # 除机械剥离外, 发布文本 == 候选原文（逐字, 非近似）
        assert final in _answer_text(evs)

    def test_zero_tool_answer_also_buffered_then_published(self):
        """zero-tool 简单回答同样走缓冲→校验→发布（不做无意义 repair）"""
        final = "苏格拉底以诘问法著称，其思想经由柏拉图对话录传世。"
        evs = _run_stream("苏格拉底的方法是什么", [_msg(final)])
        done = _done(evs)
        assert done["validation"]["repairs_used"] == 0
        assert _answer_text(evs) == final


# ═══════════════════════════════════════════════════════
# T6 Repair can research → repair 轮宣告 get_chapter → 新 final PASS
# ═══════════════════════════════════════════════════════
class TestT6RepairCanResearch:
    def test_repair_invocation_declares_tools(self):
        bad_final = "> 「子曰：言必有中，闻斯行诸。」"      # 伪引文（无出处支撑）
        repair_note = "校验未通过，需要重新读取《论语·先进篇》原文核对。"
        good_final = ("重新核验：原文为「鲁人为长府……夫人不言，言必有中」，"
                      "出自《论语·先进篇》【《论语》·先进篇】。")
        script = [_msg("先检索定位。", [{"name": "search_books", "args": {"query": "言必有中"}, "id": "c1"}]),
                  _msg(bad_final),
                  _msg(repair_note, [{"name": "get_chapter", "args": {"book_id": "lunyu",
                                                                      "chapter_idx": 13}, "id": "c3"}]),
                  _msg(good_final)]
        evs = _run_stream("言必有中出处", script)
        done = _done(evs)
        assert done["validation"]["repairs_used"] == 1
        assert good_final in _answer_text(evs)
        # repair 轮的工具全部来自 Main Agent 宣告（initiated_by=main_agent）,
        # validator 自身零工具调用（websearch/locate 全程零调用）
        for t in _of(evs, "tool", "tool_start"):
            assert t.get("initiated_by") == "main_agent"
        assert _STUB_CALLS["websearch"] == [] and _STUB_CALLS["locate_exact_phrase"] == []
        assert done["causal"]["engine_cognitive_auto_tools"] == 0
        # O1 因果契约在 repair 轮仍然成立: 工具宣告在新 invocation 组中
        assert done["causal"]["agent_invocations"] >= 3


# ═══════════════════════════════════════════════════════
# T7 No runtime factual append → public semantic text 全部 source=main_agent
# ═══════════════════════════════════════════════════════
class TestT7NoRuntimeFactualAppend:
    def test_no_runtime_sentences_anywhere(self):
        final = ("核验结论：「言必有中」出自《论语·先进篇》。\n\n"
                 "> 「" + _LUNYU_PASSAGE + "」")
        script = _TOOLS_SCRIPT + [_msg(final)]
        evs = _run_stream("言必有中出处", script)
        answer = _answer_text(evs)
        for mark in _GHOSTWRITING_MARKS:
            assert mark not in answer
        assert answer == final            # 逐字一致——runtime 未增删任何字符
        done = _done(evs)
        assert done["final_ownership"]["runtime_factual_appends"] == 0
        assert done["final_ownership"]["main_agent_final_ownership_rate"] == 1.0

    def test_done_payload_ownership_block(self):
        evs = _run_stream("简单问题", [_msg("这是一个简单回答。")])
        done = _done(evs)
        fo = done["final_ownership"]
        assert fo["provenance"] == "o2"
        assert fo["invalid_final_publicly_streamed"] is False
        assert fo["final_retract_semantic_use"] == 0
        assert done["safety_enforcement"]["initiated_by"] == "safety_runtime"


# ═══════════════════════════════════════════════════════
# T8 Invalid final never public → sentinel 不出现在任何公开 answer 事件
# ═══════════════════════════════════════════════════════
class TestT8InvalidFinalNeverPublic:
    def test_sentinel_absent_from_public_events(self):
        bad_final = "结论：原文如下——\n\n> 「" + _SENTINEL_FAKE + "」\n"
        good_final = "结论：逐字核验后的原文以《论语·先进篇》为准。"
        script = _TOOLS_SCRIPT + [_msg(bad_final), _msg(good_final)]
        evs = _run_stream("言必有中出处", script)
        public_text = "".join(str(e.get("content", "")) for e in evs
                              if e.get("type") in ("token", "thinking_summary",
                                                   "thinking_summary_delta"))
        # answer 通道从未流出被拒候选（thinking 通道允许: 那是 Main Agent 自己的话,
        # 由脚本提供——此处 sentinel 属被拒 final candidate, 不在脚本任何笔记里）
        assert _SENTINEL_FAKE not in "".join(str(e.get("content", "")) for e in _of(evs, "token"))
        assert _SENTINEL_FAKE not in public_text


# ═══════════════════════════════════════════════════════
# T9 Mechanical formatter 保留——格式可净化, 语义文本不变
# ═══════════════════════════════════════════════════════
class TestT9MechanicalFormatter:
    def test_tool_xml_and_control_tags_stripped_prose_kept(self):
        """机械 formatter（可见文本净化）: 工具标记/控制标签剥离, 语义正文逐字保留"""
        raw = ("结论前有内部标记<invoke name=\"search_books\">{\"query\": \"x\"}</invoke>"
               "<thought>不该出现的内部独白内容整段剥离</thought>"
               "结论：「言必有中」出自《论语·先进篇》。")
        vis = EG._visible_text(raw)
        assert "<invoke" not in vis and "<thought>" not in vis
        assert "不该出现的内部独白内容" not in vis
        assert "结论：「言必有中」出自《论语·先进篇》。" in vis

    def test_engine_stream_passes_prose_through_mechanical_chain(self):
        """引擎级: 无内部标记的正文经机械链后逐字透传（格式净化不改变语义文本）"""
        final = "结论：「言必有中」出自《论语·先进篇》，此为孔子对闵子骞的评语。"
        evs = _run_stream("言必有中", [_msg(final)])
        assert _answer_text(evs) == final
        assert _done(evs)["validation"]["result"]["ok"] is True


# ═══════════════════════════════════════════════════════
# T10 Repair ceiling → ≤2 次修复, 无无限循环, 无 ghostwriting, 如实收口
# ═══════════════════════════════════════════════════════
class TestT10RepairExhaustionNeverPublishes:
    """O2-RP1 Kill Test: repair 耗尽后绝不允许发布无效候选（P0 合同）。
    在 RP1 之前的实现上本测试必须失败（旧 ceiling-publish 会把 sentinel 流出）——
    这就是"旧实现被击杀"的证据。"""

    def test_exhausted_repairs_kill_publication(self):
        sentinel = "UNSUPPORTED_QUOTE_SENTINEL_APQMWK"
        bad1 = "结论：原文如下——\n\n> 「" + sentinel + "」\n（第一次作答）"
        bad2 = "结论：原文如下——\n\n> 「" + sentinel + "」\n（第二次作答）"
        bad3 = "结论：原文如下——\n\n> 「" + sentinel + "」\n（第三次作答）"
        script = [_msg(bad1), _msg(bad2), _msg(bad3)]
        evs = _run_stream("言必有中出处", script)
        done = _done(evs)
        # 修复次数 = 机械上限, validator 仍 FAIL
        assert done["validation"]["repairs_used"] == MAX_VALIDATION_REPAIRS
        assert done["validation"]["result"]["ok"] is False
        # 公开 answer 事件: sentinel 计数 = 0, 最终语义发布 = 0
        assert _answer_text(evs) == ""
        public_text = "".join(str(e.get("content", "")) for e in evs
                              if e.get("type") in ("token", "thinking_summary",
                                                   "thinking_summary_delta"))
        assert sentinel not in public_text
        # 干净失败收口: validation_failed / error 状态事件存在（非语义事件）
        assert _of(evs, "validation_failed") or _of(evs, "error")
        # 零语义 retract, 零 runtime 代写
        assert _of(evs, "answer_retract") == []
        for e in evs:
            for mark in ("据通行理解", "（与库中原文近似，非逐字）"):
                assert mark not in str(e.get("content", ""))


# ═══════════════════════════════════════════════════════
# O2 附带 (O4-RP1 删除确认): verify-later 一致性治理已随 task-intent discipline
# 删除——validator 只依赖 candidate + evidence, 无会话状态/意图参数
# ═══════════════════════════════════════════════════════
class TestConsistencyValidator:
    def test_verify_later_governance_removed(self):
        assert not hasattr(FV, "check_consistency")
        assert not hasattr(FV, "VERIFY_LATER_MISSTATEMENT")
        ans = "如果你需要原文，我可以进一步读取《论语》原文核验。"
        res = validate_final_candidate(ans, raw_tool_log=[], fallback_log=[])
        assert res.ok is True, "verify-later 措辞不再被打回（certainty/时机归 Agent 认知）"

    def test_strong_certainty_no_longer_governed(self):
        """强确定性措辞 + 证据不足 → 不产生任何 validator issue（certainty 归 Agent 认知）"""
        ans = "可以毫无疑问地确认，这句话就是《论语》原文。"
        res = validate_final_candidate(ans, raw_tool_log=[], fallback_log=[])
        assert res.ok is True
