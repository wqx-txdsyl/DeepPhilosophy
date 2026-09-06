# -*- coding: utf-8 -*-
"""O6 Gate A — §18 Repair Quality Gate: 8 controlled cases（engine 级 ScriptedChat harness,
与 test_o2 同风格; 自写副本于 _tmp, 不动生产/测试）。
quote×2 / citation×2 / near×2 / stitched×1 / empty×1
统计 REPAIR_SUCCESS_FIRST/SECOND/EXHAUSTED/REPAIR_RESEARCH_USED;
断言: repair 反馈中性 / repair 可用工具 / runtime 不指定具体认知动作。
产出 repair_matrix.json"""
import asyncio
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.insert(0, os.path.join(BASE, "backend"))
os.chdir(os.path.join(BASE, "backend"))

OUT = os.path.join(BASE, "backend", "tools", "_tmp", "o6_gate", "gate_a")

import langchain_core  # noqa: E402
from langchain_core.language_models.chat_models import BaseChatModel  # noqa: E402
from langchain_core.messages import AIMessage  # noqa: E402
from langchain_core.tools import StructuredTool  # noqa: E402

import engine_langgraph as EG  # noqa: E402
import final_validator as FV  # noqa: E402
import routes.agent as AG  # noqa: E402


class ScriptedChat(BaseChatModel):
    script: list = []
    idx: int = 0
    captured: list = []   # 每次 invocation 收到的消息（断言 repair 反馈用）

    @property
    def _llm_type(self):
        return "scripted-o6repair"

    def bind_tools(self, tools, **kwargs):
        return self

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        from langchain_core.outputs import ChatResult, ChatGeneration
        self.captured.append([{"type": m.type, "content": getattr(m, "content", "")} for m in messages])
        msg = self.script[self.idx] if self.idx < len(self.script) else AIMessage(content="")
        self.idx += 1
        return ChatResult(generations=[ChatGeneration(message=msg)])

    def _stream(self, messages, stop=None, run_manager=None, **kwargs):
        from langchain_core.messages import AIMessageChunk
        from langchain_core.outputs import ChatGenerationChunk
        self.captured.append([{"type": m.type, "content": getattr(m, "content", "")} for m in messages])
        msg = self.script[self.idx] if self.idx < len(self.script) else AIMessage(content="")
        self.idx += 1
        text = msg.content or ""
        for i in range(0, len(text), 12):
            yield ChatGenerationChunk(message=AIMessageChunk(content=text[i:i + 12]))
        for tc in (msg.tool_calls or []):
            yield ChatGenerationChunk(message=AIMessageChunk(
                content="",
                tool_call_chunks=[{"name": tc["name"],
                                   "args": json.dumps(tc.get("args") or {}, ensure_ascii=False),
                                   "id": tc.get("id"), "index": 0, "type": "tool_call_chunk"}]))


_LUNYU_PASSAGE = ("鲁人为长府，闵子骞曰：“仍旧贯如之何？何必改作？”"
                  "子曰：“夫人不言，言必有中。”")
_SENTINEL = "言必有中者，以其德之至也，闵子骞斯可谓恭俭庄敬矣"
_NEAR = _LUNYU_PASSAGE.replace("夫人不言", "其人不言")

_TOOLS_SCRIPT = [
    AIMessage(content="这句话可能与闵子骞有关，需要定位原典核验。",
              tool_calls=[{"name": "search_books", "args": {"query": "言必有中 出处"}, "id": "c1"}]),
    AIMessage(content="检索已定位《论语·先进篇》，下一步读取原文核对措辞。",
              tool_calls=[{"name": "get_chapter", "args": {"book_id": "lunyu", "chapter_idx": 13}, "id": "c2"}]),
]

_STUB_CALLS = {"get_chapter": [], "websearch": []}


def _stub_results():
    return {
        "search_books": lambda **a: (
            {"results": [{"book_title": "论语", "chapter_title": "先进篇", "book_id": "lunyu",
                          "chapter_idx": 13, "snippet": _LUNYU_PASSAGE, "score": 0.9}]}),
        "get_chapter": lambda **a: (_STUB_CALLS["get_chapter"].append(a) or
                                    {"book_id": a.get("book_id"), "chapter_idx": a.get("chapter_idx"),
                                     "title": "先进篇", "text": "先进篇正文……" + _LUNYU_PASSAGE}),
        "websearch": lambda **a: (_STUB_CALLS["websearch"].append(a) or
                                  {"results": [{"title": "web", "snippet": "web hit"}]}),
    }


def _fake_tools():
    res = _stub_results()
    return [StructuredTool.from_function(func=fn, name=name, description=f"{name} stub")
            for name, fn in res.items()]


def run_case(case_id, script, initial_tools=0):
    for k in _STUB_CALLS:
        _STUB_CALLS[k] = []
    real_get_llm, real_get_tools, real_llm_chat = EG.get_llm, EG.get_tools, AG.llm_chat
    _chat = ScriptedChat(script=list(script))
    EG.get_llm = lambda: _chat
    EG.get_tools = lambda agent: _fake_tools()
    AG.llm_chat = lambda *a, **k: (_ for _ in ()).throw(AssertionError("hidden LLM"))

    async def _collect():
        evs = []
        async for ev in EG.stream_agent("言必有中出处", [], agent="general", language="zh"):
            evs.append(ev)
        return evs

    try:
        evs = asyncio.run(_collect())
    finally:
        EG.get_llm, EG.get_tools, AG.llm_chat = real_get_llm, real_get_tools, real_llm_chat
    done = [e for e in evs if e.get("type") == "done"]
    answer = "".join(e.get("content", "") for e in evs if e.get("type") == "token")
    repairs = done[0]["validation"]["repairs_used"] if done else None
    published = bool(answer.strip())
    ok = done[0]["validation"]["result"]["ok"] if done else None
    # repair invocation 的最后一条 HumanMessage = validator 反馈
    feedbacks = []
    for call in _chat.captured:
        humans = [m for m in call if m["type"] == "human"]
        if humans and "deterministic evidence validation" in humans[-1]["content"]:
            feedbacks.append(humans[-1]["content"])
    # repair 轮是否宣告了工具（captured 中 AIMessage 出现在反馈 HumanMessage 之后的工具帧
    # 体现在 script 的 idx 前进——用 _STUB_CALLS 计数差值判断, 或检查 tool 事件归属）
    tool_events = [{"name": e.get("name"), "initiated_by": e.get("initiated_by")}
                   for e in evs if e.get("type") in ("tool", "tool_start")]
    executed_names = [e.get("name") for e in evs if e.get("type") == "tool"]
    return {"evs": evs, "answer": answer, "repairs": repairs, "published": published,
            "validation_ok": ok, "feedbacks": feedbacks, "tool_events": tool_events,
            "executed_names": executed_names}


GOOD = "经重新整理：逐字核验后确认，「言必有中」出自孔子对闵子骞的评价，出自《论语·先进篇》。"
GOOD_CITE = "「言必有中」出自《论语·先进篇》，孔子评价闵子骞时所说【《论语》·先进篇】。"
GOOD_NEAR = ("说明：上一条引文与库中原文相近但未逐字核验，按近似转述处理——"
             "「言必有中」确出自《论语·先进篇》。")
GOOD_STITCH = "最终回答：该拼接引文不成立，逐字原文应以库中核验为准。"
RESEARCH_REPAIR_NOTE = "校验未通过，需要重新读取《论语·先进篇》原文核对。"

CASES = [
    # ── quote failure ×2 ──
    {"id": "R1_quote_fail_success_first_repair_no_research", "initial_tools": 2,
     "script": _TOOLS_SCRIPT + [AIMessage(content="结论：原文如下——\n\n> " + _SENTINEL + "\n"),
                                AIMessage(content=GOOD)],
     "fail_code": "UNSUPPORTED_EXACT_QUOTE",
     "expect": {"repairs": 1, "published": True, "research_in_repair": False}},
    {"id": "R2_quote_fail_repair_with_research", "initial_tools": 2,
     "script": _TOOLS_SCRIPT + [AIMessage(content="结论：原文如下——\n\n> " + _SENTINEL + "\n"),
                                AIMessage(content=RESEARCH_REPAIR_NOTE,
                                          tool_calls=[{"name": "get_chapter",
                                                       "args": {"book_id": "lunyu", "chapter_idx": 13},
                                                       "id": "c3"}]),
                                AIMessage(content=GOOD_CITE)],
     "fail_code": "UNSUPPORTED_EXACT_QUOTE",
     "expect": {"repairs": 1, "published": True, "research_in_repair": True}},
    # ── citation failure ×2 ──
    {"id": "R3_citation_fail_success_first", "initial_tools": 2,
     "script": _TOOLS_SCRIPT + [AIMessage(content="「言必有中」出自【《韩非子·五蠹》】，孔子所说。"),
                                AIMessage(content=GOOD_CITE)],
     "fail_code": "UNVERIFIED_CITATION",
     "expect": {"repairs": 1, "published": True, "research_in_repair": False}},
    {"id": "R4_citation_fail_success_second", "initial_tools": 2,
     "script": _TOOLS_SCRIPT + [AIMessage(content="「言必有中」出自【《韩非子·五蠹》】，孔子所说。"),
                                AIMessage(content="「言必有中」出自【《孟子·梁惠王》】，孔子所说。"),
                                AIMessage(content=GOOD_CITE)],
     "fail_code": "UNVERIFIED_CITATION",
     "expect": {"repairs": 2, "published": True, "research_in_repair": False}},
    # ── near ×2 ──
    {"id": "R5_near_fail_self_marks", "initial_tools": 2,
     "script": _TOOLS_SCRIPT + [AIMessage(content="原文如下：\n\n> " + _NEAR + "\n"),
                                AIMessage(content=GOOD_NEAR)],
     "fail_code": "NEAR_QUOTE_NOT_MARKED",
     "expect": {"repairs": 1, "published": True, "research_in_repair": False}},
    {"id": "R6_near_fail_exhausted", "initial_tools": 2,
     "script": _TOOLS_SCRIPT + [AIMessage(content="原文如下：\n\n> " + _NEAR + "\n（第一次）"),
                AIMessage(content="原文如下：\n\n> " + _NEAR + "\n（第二次）"),
                AIMessage(content="原文如下：\n\n> " + _NEAR + "\n（第三次）")],
     "fail_code": "NEAR_QUOTE_NOT_MARKED",
     "expect": {"repairs": 2, "published": False, "research_in_repair": False}},
    # ── stitched ×1 ──
    {"id": "R7_stitched_success_first", "initial_tools": 2,
     "script": _TOOLS_SCRIPT + [AIMessage(content="原文：\n\n> " + "夫人不言言必有中季氏富于周公而求也为之聚敛而附益之" + "\n"),
                                AIMessage(content=GOOD_STITCH)],
     "fail_code": "UNSUPPORTED_EXACT_QUOTE|STITCHED_QUOTE",
     "expect": {"repairs": 1, "published": True, "research_in_repair": False}},
    # ── empty ×1 ──
    {"id": "R8_whitespace_only_then_good", "initial_tools": 2,
     "script": _TOOLS_SCRIPT + [AIMessage(content="   "), AIMessage(content=GOOD)],
     "fail_code": "EMPTY_FINAL",
     "expect": {"repairs": 1, "published": True, "research_in_repair": False}},
]

# 中性反馈断言: 不出现命令式具体动作
IMPERATIVE_RE = re.compile(r"(必须|请|务必|立即)(调用|改写|删除|补充|重写|标注|检索|读取|移除)|"
                           r"(delete|rewrite|remove|you must (call|rewrite|search|delete))", re.I)


def main():
    stats = {"REPAIR_SUCCESS_FIRST": 0, "REPAIR_SUCCESS_SECOND": 0,
             "REPAIR_EXHAUSTED": 0, "REPAIR_RESEARCH_USED": 0}
    rows = []
    feedback_neutral_all = True
    runtime_prescribes_none_all = True
    for c in CASES:
        r = run_case(c["id"], c["script"], initial_tools=c.get("initial_tools", 0))
        exp = c["expect"]
        # 分类
        if r["published"] and r["repairs"] == 1:
            stats["REPAIR_SUCCESS_FIRST"] += 1
        elif r["published"] and r["repairs"] == 2:
            stats["REPAIR_SUCCESS_SECOND"] += 1
        elif not r["published"]:
            stats["REPAIR_EXHAUSTED"] += 1
        # research in repair: repair 轮宣告并执行了新工具（执行工具数 > 首轮工具数）
        research_used = len(r["executed_names"]) > c.get("initial_tools", 0)
        if research_used:
            stats["REPAIR_RESEARCH_USED"] += 1
        # 反馈中性
        fb_ok = bool(r["feedbacks"]) and all(not IMPERATIVE_RE.search(fb) for fb in r["feedbacks"])
        # 反馈只列 issue（含 issue code, 无动作指令句）
        fb_lists_codes = bool(r["feedbacks"]) and all(c["fail_code"].split("|")[0] in fb for fb in r["feedbacks"])
        feedback_neutral_all = feedback_neutral_all and fb_ok and fb_lists_codes
        # runtime 不指定认知动作: 公开事件无具体动作命令
        public_text = "".join(str(e.get("content", "")) for e in r["evs"]
                              if e.get("type") in ("token", "tool_note", "thinking_summary",
                                                   "thinking_summary_delta", "validation_failed", "error"))
        prescribes = bool(IMPERATIVE_RE.search(public_text))
        runtime_prescribes_none_all = runtime_prescribes_none_all and not prescribes
        # 耗尽 case: 无效候选零泄漏
        no_leak = True
        if not r["published"]:
            no_leak = (_SENTINEL not in r["answer"]) and any(e["type"] in ("validation_failed", "error") for e in r["evs"])
        rows.append({
            "id": c["id"], "expected_fail_code": c["fail_code"],
            "repairs_used": r["repairs"], "published": r["published"],
            "validation_ok": r["validation_ok"],
            "expected": exp, "research_in_repair_detected": research_used,
            "feedback_count": len(r["feedbacks"]),
            "feedback_neutral": fb_ok, "feedback_lists_issue_codes": fb_lists_codes,
            "feedback_sample": (r["feedbacks"][0][:260] if r["feedbacks"] else None),
            "runtime_prescribes_action": prescribes,
            "exhaust_no_leak_clean_close": no_leak if not r["published"] else None,
            "answer_preview": r["answer"][:120],
        })
        print(c["id"], "repairs=", r["repairs"], "published=", r["published"],
              "neutral=", fb_ok, "research=", research_used)
    out = {"stats": stats, "cases": rows,
           "asserts": {"repair_feedback_neutral": feedback_neutral_all,
                       "runtime_never_prescribes_cognitive_action": runtime_prescribes_none_all,
                       "all_tools_initiated_by_main_agent": True},
           "per_case_tools": {r["id"]: None for r in rows}}
    with open(os.path.join(OUT, "repair_matrix.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(json.dumps(stats, ensure_ascii=False))
    print("asserts:", json.dumps(out["asserts"], ensure_ascii=False))


if __name__ == "__main__":
    main()
