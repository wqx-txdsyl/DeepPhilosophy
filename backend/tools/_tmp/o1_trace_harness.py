# -*- coding: utf-8 -*-
"""O1 因果 trace harness（临时调试脚本）——baseline BEFORE / refactor AFTER 通用。

运行方式（.venv, 仓库根）:
    .venv/Scripts/python.exe backend/tools/_tmp/o1_trace_harness.py \
        --label before_r1 --question "言必有中出处" --out backend/tools/_tmp/o1_before_r1.json

捕获全部 SSE 事件并为每个事件标注 EVENT_SOURCE:
    MAIN_AGENT          模型自身输出（内容通道文字 / rationale / 原生 reasoning_content / 模型宣告的工具）
    RUNTIME             引擎代执行 / 引擎生成的文本（auto-read / auto-websearch / 摘要生成器 / 活动注记）
    TOOL_INTERNAL       工具执行内部（工具结果载荷）
    VALIDATOR           确定性校验器（quote/citation/consistency 收口补正）

对 baseline 代码, RUNTIME 判定基于已知发射路径的指纹（thought 文案 / _auto 标记 /
llm_stream 摘要生成器活动窗口）; 对 refactor 后代码, 事件自带 initiated_by 字段, 直接采用。
"""
import argparse
import asyncio
import json
import os
import sys
import time

BACKEND = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ROOT = os.path.dirname(os.path.dirname(BACKEND))
sys.path.insert(0, BACKEND)

# ── 摘要生成器活动窗口探测: baseline 的 _gen_summary 是唯一 llm_stream 消费者 ──
_harness_state = {"summary_gen_active": 0, "summary_gen_last": 0.0}

_real_llm_stream = None


def _patch_llm_stream():
    global _real_llm_stream
    import routes.agent_llm as AL
    _real_llm_stream = AL.llm_stream

    def wrapper(msgs, **kw):
        _harness_state["summary_gen_active"] += 1
        _harness_state["summary_gen_last"] = time.time()
        try:
            for piece in _real_llm_stream(msgs, **kw):
                yield piece
        finally:
            _harness_state["summary_gen_active"] = max(0, _harness_state["summary_gen_active"] - 1)
            _harness_state["summary_gen_last"] = time.time()
    AL.llm_stream = wrapper


AUTO_READ_THOUGHT_MARK = "search→read 升级"
AUTO_WS_THOUGHT_MARK = "自动上网搜索补充"
PRIMARY_READ_NOTE_MARK = "已完成主文本核验读取"


def classify(ev, ts):
    """→ (EVENT_SOURCE, impersonation_flag, detail)"""
    t = ev.get("type", "")
    # refactor 后: 事件自带 provenance
    if "initiated_by" in ev:
        src = ev["initiated_by"]
        src = {"main_agent": "MAIN_AGENT", "runtime_mechanical": "RUNTIME",
               "tool_internal": "TOOL_INTERNAL", "validator": "VALIDATOR"}.get(src, src.upper())
        return src, False, ""
    # baseline: 按发射路径指纹分类
    if t == "thought_stream":
        return "MAIN_AGENT", False, "provider reasoning_content（模型原生思维链, 仅展示通道）"
    if t in ("thinking_summary", "thinking_summary_delta"):
        # 摘要生成器窗口内（或 1.5s 余量内）→ 引擎侧 mini-LLM 生成 → RUNTIME
        if _harness_state["summary_gen_active"] > 0 or (ts - _harness_state["summary_gen_last"]) < 1.5:
            return "RUNTIME", True, "引擎摘要生成器（独立 mini-LLM）产出, 冒充 Main Agent thinking"
        return "MAIN_AGENT", False, "模型内容通道文字（规划文本/rationale 标签）降级转发"
    if t == "tool_start":
        return "MAIN_AGENT", False, "模型 tool_call 宣告"
    if t == "tool":
        thought = str(ev.get("thought") or "")
        if AUTO_WS_THOUGHT_MARK in thought:
            return "RUNTIME", True, "引擎 auto-websearch（search_books 空结果后自动执行）"
        if AUTO_READ_THOUGHT_MARK in thought:
            return "RUNTIME", True, "引擎 _ensure_primary_read 代执行 get_chapter"
        return "MAIN_AGENT", False, "模型宣告的工具执行结果"
    if t == "tool_note":
        c = str(ev.get("content") or "")
        if PRIMARY_READ_NOTE_MARK in c:
            return "RUNTIME", True, "引擎注入「已完成主文本核验读取」— runtime 文案表现为 Agent 核验行为"
        return "RUNTIME", False, "确定性活动/解读注记（interpret_thinking）"
    if t in ("token",):
        return "MAIN_AGENT", False, "回答正文（模型生成或校验器补正, 正文层无法逐字区分）"
    return ("VALIDATOR" if t in ("suggestions", "reasoning_summary") else "RUNTIME"), False, t


async def run(label, question, out_path, history=None, agent="general", language="zh"):
    import engine_langgraph as EG
    _patch_llm_stream()
    events = []
    t0 = time.time()
    err = None
    try:
        async for ev in EG.stream_agent(question, history or [], agent=agent, language=language):
            ts = time.time() - t0
            src, imp, detail = classify(ev, time.time())
            rec = {"t": round(ts, 3), "type": ev.get("type"), "source": src}
            if imp:
                rec["impersonation"] = True
            if detail:
                rec["detail"] = detail
            for k in ("name", "thought", "phase"):
                if ev.get(k):
                    rec[k] = str(ev[k])[:80]
            for k in ("content",):
                if ev.get(k):
                    rec[k] = str(ev[k])[:220]
            if ev.get("type") == "done":
                rec["tool_calls"] = [
                    {"name": tc.get("name"), "thought": str(tc.get("thought") or "")[:60]}
                    for tc in (ev.get("tool_calls") or [])]
                ob = ev.get("obligation_ledger") or {}
                rec["ledger"] = {
                    "obligations_satisfied": ob.get("obligations_satisfied"),
                    "read_execs": ob.get("read_execs"),
                    "search_execs": ob.get("search_execs"),
                    "verification_states": (ob.get("verification_states") or {})},
                rec["quote_bound"] = (ev.get("quote_bound") or {}).get("summary")
                rec["causal"] = ev.get("causal")
                rec["timing_total_ms"] = (ev.get("timing") or {}).get("total_ms")
                # 最终正文（用于人工核对理想 trace / 出处 / blockquote）
                rec["answer"] = None
            events.append(rec)
    except Exception as e:  # noqa: BLE001
        err = f"{type(e).__name__}: {e}"

    # ── 因果分析（回答 A-F）──
    tool_events = [e for e in events if e.get("type") == "tool"]
    ts_events = [e for e in events if e.get("type") in ("thinking_summary", "thinking_summary_delta")]
    runtime_tools = [e for e in tool_events if e.get("source") == "RUNTIME"]
    impersonations = [e for e in events if e.get("impersonation")]

    def _between(a, b):
        """事件序列里位于 a 和 b 之间的元素（按 tool 事件定位）"""
        try:
            ia = events.index(a)
            ib = events.index(b)
        except ValueError:
            return []
        return events[ia + 1:ib]

    q_a = q_b = q_c = q_d = q_e = q_f = None
    if tool_events:
        first = tool_events[0]
        q_a = {"tool": first.get("name"), "decided_by": first.get("source"),
               "detail": first.get("detail", "")}
        searches = [e for e in tool_events if e.get("name") == "search_books"]
        if len(searches) >= 2:
            second = searches[1]
            q_b = {"decided_by": second.get("source"), "detail": second.get("detail", "")}
        else:
            q_b = {"decided_by": "N/A（本轮只发生一次 search_books）",
                   "second_search": tool_events[1].get("name") if len(tool_events) > 1 else None}
        reads = [e for e in tool_events if e.get("name") == "get_chapter"]
        if reads:
            rd = reads[0]
            q_c = {"decided_by": rd.get("source"), "detail": rd.get("detail", ""),
                   "thought": rd.get("thought", "")}
            q_d = _between(tool_events[-2], rd) if len(tool_events) >= 2 else []
            main_llm_between = [e for e in q_d if e.get("source") == "MAIN_AGENT"
                                and e.get("type") in ("thinking_summary", "thinking_summary_delta")]
            q_d = {"events_between_second_tool_and_read": q_d,
                   "main_agent_thinking_between": bool(main_llm_between)}
        else:
            q_c = {"decided_by": "N/A（未发生 get_chapter）"}
            q_d = "N/A"
        note_hits = [e for e in events if e.get("type") == "tool_note"
                     and PRIMARY_READ_NOTE_MARK in str(e.get("content") or "")]
        q_e = {"generated": bool(note_hits), "by": "RUNTIME（engine_langgraph 收口阶段注入）"} if note_hits \
            else {"generated": False}
    q_f = {"count": len(impersonations), "events": impersonations}

    result = {"label": label, "question": question, "error": err,
              "duration_s": round(time.time() - t0, 1),
              "event_count": len(events),
              "answer": "".join(str(e.get("content") or "") for e in events if e.get("type") == "token"),
              "answers": {"A_first_search": q_a, "B_second_search": q_b,
                          "C_get_chapter": q_c, "D_main_llm_between": q_d,
                          "E_primary_read_note": q_e, "F_runtime_as_thinking": q_f},
              "runtime_initiated_tools": [{"name": e.get("name"), "thought": e.get("thought")}
                                          for e in runtime_tools],
              "events": events}
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=1)
    print(f"[{label}] events={len(events)} runtime_tools={len(runtime_tools)} "
          f"impersonations={len(impersonations)} error={err}")
    for k, v in result["answers"].items():
        print(f"  {k}: {json.dumps(v, ensure_ascii=False)[:300]}")
    return result


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    ap.add_argument("--question", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--agent", default="general")
    ap.add_argument("--lang", default="zh")
    ap.add_argument("--repeat", type=int, default=1)
    args = ap.parse_args()
    for i in range(args.repeat):
        lab = args.label if args.repeat == 1 else f"{args.label}_run{i + 1}"
        out = args.out if args.repeat == 1 else args.out.replace(".json", f"_run{i + 1}.json")
        asyncio.run(run(lab, args.question, out, agent=args.agent, language=args.lang))
