# -*- coding: utf-8 -*-
"""O6 Gate A — §20 Error/Failure Gate（controlled harness, monkeypatch 全部进程内）。
覆盖: tool timeout / tool execution error / unknown tool / missing-param schema /
hard ceiling / model provider error / validator exhaustion / cancel(simulated)。
逐项断言: 无 stack trace 泄漏、无伪造事实、无 ghostwritten final、无效候选零泄漏、
干净 done/error 收口。产出 error_gate.json"""
import asyncio
import json
import os
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
import agent_runtime as AR  # noqa: E402
import routes.agent as AG  # noqa: E402

_LUNYU_PASSAGE = ("鲁人为长府，闵子骞曰：“仍旧贯如之何？何必改作？”"
                  "子曰：“夫人不言，言必有中。”")
_LEAK_MARKERS = ["Traceback", 'File "', "boom-db-SECRET", "429", "rate limit", "RateLimitError",
                 "stack trace", "INTERNAL_", "raise "]


class ScriptedChat(BaseChatModel):
    script: list = []
    idx: int = 0

    @property
    def _llm_type(self):
        return "scripted-o6err"

    def bind_tools(self, tools, **kwargs):
        return self

    def _next(self):
        msg = self.script[self.idx] if self.idx < len(self.script) else AIMessage(content=" ")
        self.idx += 1
        return msg

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        from langchain_core.outputs import ChatResult, ChatGeneration
        return ChatResult(generations=[ChatGeneration(message=self._next())])

    def _stream(self, messages, stop=None, run_manager=None, **kwargs):
        from langchain_core.messages import AIMessageChunk
        from langchain_core.outputs import ChatGenerationChunk
        msg = self._next()
        text = msg.content or ""
        for i in range(0, len(text), 12):
            yield ChatGenerationChunk(message=AIMessageChunk(content=text[i:i + 12]))
        for tc in (msg.tool_calls or []):
            yield ChatGenerationChunk(message=AIMessageChunk(
                content="",
                tool_call_chunks=[{"name": tc["name"],
                                   "args": json.dumps(tc.get("args") or {}, ensure_ascii=False),
                                   "id": tc.get("id"), "index": 0, "type": "tool_call_chunk"}]))


class RateLimitedChat(BaseChatModel):
    """模拟 provider 错误（可重试错误文本 → invoke_llm_with_retry 重试后 ModelCallError）"""
    calls: int = 0

    @property
    def _llm_type(self):
        return "rate-limited-stub"

    def bind_tools(self, tools, **kwargs):
        return self

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        self.calls += 1
        raise Exception("HTTP 429 rate limit exceeded (SECRET-PROVIDER-DETAIL)")

    def _stream(self, messages, stop=None, run_manager=None, **kwargs):
        self.calls += 1
        raise Exception("HTTP 429 rate limit exceeded (SECRET-PROVIDER-DETAIL)")
        yield  # pragma: no cover


def make_stub(name, fn):
    return StructuredTool.from_function(func=fn, name=name, description=f"{name} stub")


def base_tools(slow=False, timeout_s=1.5, fail=False, missing_param=False):
    def search_books(**a):
        if missing_param and not a.get("query"):
            return {"error": "缺少必需参数: query（schema 校验失败）"}
        return {"results": [{"book_title": "论语", "chapter_title": "先进篇", "book_id": "lunyu",
                             "chapter_idx": 13, "snippet": _LUNYU_PASSAGE, "score": 0.9}]}
    import time as _t

    def get_chapter(**a):
        if slow:
            _t.sleep(timeout_s + 2.0)
        if fail:
            raise Exception("boom-db-SECRET: connection refused")
        return {"book_id": a.get("book_id"), "chapter_idx": a.get("chapter_idx"),
                "title": "先进篇", "text": _LUNYU_PASSAGE}
    return [make_stub("search_books", search_books),
            make_stub("get_chapter", get_chapter)]


GOOD = "核验结论：「言必有中」出自《论语·先进篇》，为孔子评价闵子骞之语。"


def run_case(script, tools, patch_budget=None, patch_timeout=None, llm_override=None):
    real = (EG.get_llm, EG.get_tools, AG.llm_chat, AR.TOOL_BUDGET, AR.TOOL_TIMEOUT,
            AR.MODEL_RETRY["backoff_seconds"])
    _chat = ScriptedChat(script=list(script))
    EG.get_llm = llm_override or (lambda: _chat)
    EG.get_tools = lambda agent: tools
    AG.llm_chat = lambda *a, **k: (_ for _ in ()).throw(AssertionError("hidden LLM"))
    if patch_budget:
        AR.TOOL_BUDGET = patch_budget
    if patch_timeout:
        AR.TOOL_TIMEOUT = patch_timeout
    AR.MODEL_RETRY["backoff_seconds"] = [0.05, 0.05]

    async def _collect():
        evs = []
        async for ev in EG.stream_agent("言必有中出处", [], agent="general", language="zh"):
            evs.append(ev)
        return evs

    try:
        return asyncio.run(_collect())
    finally:
        EG.get_llm, EG.get_tools, AG.llm_chat = real[0], real[1], real[2]
        AR.TOOL_BUDGET, AR.TOOL_TIMEOUT = real[3], real[4]
        AR.MODEL_RETRY["backoff_seconds"] = real[5]


def audit(case_id, evs, expect):
    public = "".join(str(e.get("content", "")) for e in evs
                     if e.get("type") in ("token", "tool_note", "thinking_summary",
                                          "thinking_summary_delta", "validation_failed", "error",
                                          "status", "tool"))
    leaks = [m for m in _LEAK_MARKERS if m in public]
    answer = "".join(e.get("content", "") for e in evs if e.get("type") == "token")
    dones = [e for e in evs if e.get("type") == "done"]
    errors = [e for e in evs if e.get("type") == "error"]
    row = {"case": case_id,
           "stack_trace_leak": leaks,
           "no_stack_trace_clean": not leaks,
           "answer_chars": len(answer.strip()),
           "done_count": len(dones), "error_count": len(errors),
           "clean_close": (len(dones) == 1 and dones[0]["validation"]["result"]["ok"]) or
                          (len(errors) == 1 and not answer.strip()),
           "event_types": sorted({e["type"] for e in evs}),
           "expect": expect}
    return row, answer, dones, errors


def main():
    rows = []
    N1 = "这句话可能与闵子骞有关，需要定位原典核验。"
    N2 = "检索已定位《论语·先进篇》，下一步读取原文核对措辞。"

    # E1 tool timeout（TOOL_TIMEOUT=1.5s, stub sleep 3.5s）
    evs = run_case([AIMessage(content=N1, tool_calls=[{"name": "get_chapter",
                                                       "args": {"book_id": "lunyu", "chapter_idx": 13}, "id": "c1"}]),
                    AIMessage(content=GOOD)],
                   base_tools(slow=True, timeout_s=1.5), patch_timeout=1.5)
    row, answer, dones, errors = audit("E1_tool_timeout", evs, "工具超时→error结果→正常发布")
    tool_evs = [e for e in evs if e.get("type") == "tool"]
    row["tool_error_surfaced"] = bool(tool_evs) and "超时" in str(tool_evs[0].get("result", ""))
    row["published_ok"] = bool(answer.strip()) and dones and dones[0]["validation"]["result"]["ok"]
    rows.append(row)

    # E2 tool execution error（stub raise → 轮内重试 → error 结果 + fallback 提示）
    evs = run_case([AIMessage(content=N1, tool_calls=[{"name": "get_chapter",
                                                       "args": {"book_id": "lunyu", "chapter_idx": 13}, "id": "c1"}]),
                    AIMessage(content=GOOD)],
                   base_tools(fail=True))
    row, answer, dones, errors = audit("E2_tool_execution_error", evs, "工具异常→error结果→正常发布")
    tool_evs = [e for e in evs if e.get("type") == "tool"]
    row["tool_error_surfaced"] = bool(tool_evs) and ("boom-db-SECRET" in str(tool_evs[0].get("result", ""))
                                                     or "error" in str(tool_evs[0].get("result", "")))
    row["secret_in_public_answer"] = "boom-db-SECRET" in answer
    row["published_ok"] = bool(answer.strip()) and dones and dones[0]["validation"]["result"]["ok"]
    rows.append(row)

    # E3 unknown tool（宣告未注册工具）
    evs = run_case([AIMessage(content=N1, tool_calls=[{"name": "totally_unknown_tool", "args": {}, "id": "c1"}]),
                    AIMessage(content=GOOD)],
                   base_tools())
    row, answer, dones, errors = audit("E3_unknown_tool", evs, "未知工具→error结果→正常发布")
    tool_evs = [e for e in evs if e.get("type") == "tool"]
    row["tool_error_surfaced"] = bool(tool_evs) and "未知工具" in str(tool_evs[0].get("result", ""))
    row["published_ok"] = bool(answer.strip()) and dones and dones[0]["validation"]["result"]["ok"]
    rows.append(row)

    # E4 missing-param schema（必需参数缺失）
    evs = run_case([AIMessage(content=N1, tool_calls=[{"name": "search_books", "args": {}, "id": "c1"}]),
                    AIMessage(content=GOOD)],
                   base_tools(missing_param=True))
    row, answer, dones, errors = audit("E4_missing_param_schema", evs, "缺参→error结果→正常发布")
    tool_evs = [e for e in evs if e.get("type") == "tool"]
    row["tool_error_surfaced"] = bool(tool_evs) and "缺少必需参数" in str(tool_evs[0].get("result", ""))
    row["published_ok"] = bool(answer.strip()) and dones and dones[0]["validation"]["result"]["ok"]
    rows.append(row)

    # E5 hard ceiling（hard_total=1: forced 轮中的 get_chapter 宣告被机械拒绝
    #   RESOURCE_CEILING_REACHED → 补跑 → 干净发布, repairs=0）
    evs = run_case([AIMessage(content=N1, tool_calls=[{"name": "search_books",
                                                       "args": {"query": "言必有中"}, "id": "c1"}]),
                    AIMessage(content=N2, tool_calls=[{"name": "get_chapter",
                                                       "args": {"book_id": "lunyu", "chapter_idx": 13}, "id": "c2"}]),
                    AIMessage(content=GOOD)],
                   base_tools(), patch_budget={"hard_retrieval": 20, "hard_total": 1})
    row, answer, dones, errors = audit("E5_hard_ceiling", evs, "硬上限→机械拒绝→forced→干净发布")
    all_text = json.dumps([{ "t": e["type"], "c": str(e.get("content", ""))[:200]} for e in evs],
                          ensure_ascii=False)
    row["ceiling_mechanical_reject"] = "RESOURCE_CEILING_REACHED" in all_text
    row["no_semantic_sufficiency_language"] = ("证据已充分" not in all_text) and ("库中无相关内容" not in all_text)
    row["cancels"] = [e.get("name") for e in evs if e.get("type") == "tool_cancel"]
    row["published_ok"] = bool(answer.strip()) and dones and dones[0]["validation"]["result"]["ok"]
    row["repairs_used"] = dones[0]["validation"]["repairs_used"] if dones else None
    rows.append(row)

    # E6 model provider error（429 → 重试耗尽 → ModelCallError → 干净脱敏 error）
    rl = RateLimitedChat()
    evs = run_case([], base_tools(), llm_override=lambda: rl)
    row, answer, dones, errors = audit("E6_provider_error", evs, "provider错误→脱敏error→无答案泄漏")
    row["model_retry_count"] = rl.calls
    row["sanitized_error"] = bool(errors) and ("暂时出错" in errors[0].get("content", "")) and \
        ("SECRET-PROVIDER-DETAIL" not in errors[0].get("content", ""))
    row["no_ghostwritten_final"] = not answer.strip()
    rows.append(row)

    # E7 validator exhaustion（恒坏候选）
    sentinel = "UNSUPPORTED_QUOTE_SENTINEL_ZZZQ"
    evs = run_case([AIMessage(content="结论：原文如下——\n\n> " + sentinel + "\n（1）"),
                    AIMessage(content="结论：原文如下——\n\n> " + sentinel + "\n（2）"),
                    AIMessage(content="结论：原文如下——\n\n> " + sentinel + "\n（3）")],
                   base_tools())
    row, answer, dones, errors = audit("E7_validator_exhaustion", evs, "耗尽→validation_failed+error→零泄漏")
    row["sentinel_leak"] = sentinel in answer
    row["invalid_candidate_leak"] = sentinel in json.dumps([str(e.get("content", "")) for e in evs
                                                            if e.get("type") in ("token",)])
    rows.append(row)

    # E8 cancel + BUG F2 repro（forced_tools_done 后仍宣告 → tool_cancel;
    #   该路径 pending.has_tools 卡 True → repair 轮新文本被当作"残留工具轮"降级丢弃
    #   → candidate 恒空 → 耗尽。记录为 O6 发现 F2: 修复机制在该边界路径被击穿
    #   （收口仍安全: 无无效内容发布, 干净 error 收口））
    evs = run_case([AIMessage(content=N1, tool_calls=[{"name": "search_books",
                                                       "args": {"query": "言必有中"}, "id": "c1"}]),
                    AIMessage(content=N2, tool_calls=[{"name": "get_chapter",
                                                       "args": {"book_id": "lunyu", "chapter_idx": 13}, "id": "c2"}]),
                    AIMessage(content=GOOD, tool_calls=[{"name": "websearch", "args": {"query": "x"}, "id": "c3"}]),
                    AIMessage(content=GOOD)],
                   base_tools(), patch_budget={"hard_retrieval": 20, "hard_total": 1})
    row, answer, dones, errors = audit("E8_cancel_and_repair_loss_F2", evs,
                                       "宣告未执行→tool_cancel; repair文本被丢→耗尽(BUG F2 取证)")
    row["cancels"] = [e.get("name") for e in evs if e.get("type") == "tool_cancel"]
    row["repairs_used"] = dones[0]["validation"]["repairs_used"] if dones else None
    row["final_issues"] = [i["code"] for i in dones[0]["validation"]["result"]["issues"]] if dones else None
    row["bug_F2_reproduced"] = bool(row["cancels"]) and row["repairs_used"] == 2 and not answer.strip()
    row["published_ok"] = bool(answer.strip()) and dones and dones[0]["validation"]["result"]["ok"]
    rows.append(row)

    ok_all = all(r["no_stack_trace_clean"] and r["clean_close"] for r in rows)
    out = {"cases": rows, "all_clean": ok_all}
    with open(os.path.join(OUT, "error_gate.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    for r in rows:
        print(r["case"], "| leak:", r["stack_trace_leak"], "| clean_close:", r["clean_close"],
              "| tool_err:", r.get("tool_error_surfaced"), "| pub:", r.get("published_ok"),
              "| cancels:", r.get("cancels"))
    print("ALL_CLEAN:", ok_all)


if __name__ == "__main__":
    main()
