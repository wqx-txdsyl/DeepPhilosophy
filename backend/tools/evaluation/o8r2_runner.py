# -*- coding: utf-8 -*-
"""O8-R2 Execution Audit runner — 72-case capability benchmark.

Evaluation-only（不得被 production runtime import）。真实生产路径:
engine_langgraph.stream_agent 无注入运行（与 o7e_production_calibration §E 同型）,
另加 O8-R2 效率遥测（LLM_CALLS/TOOL_CALLS/RETRIEVAL_ROUNDS/DUPLICATE_CALLS/
TOTAL_LATENCY/TOKEN_USAGE）。

用法: o8r2_runner.py [case_ids 逗号分隔 | -]
增量写入 backend/tools/_tmp/o8r2_bench.json（断点续跑, 按 case_id 去重）。
"""
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, "backend"))
sys.path.insert(0, os.path.join(ROOT, "backend", "tools", "evaluation"))

import engine_langgraph as EG  # noqa: E402
from o7e_candidate_config import RP_B, v4pro_config, build_candidate_langchain_client  # noqa: E402

CASESET = os.path.join(ROOT, "docs/evidence/O8_R2_CASESET.json")
OUT_PATH = os.path.join(ROOT, "backend/tools/_tmp/o8r2_bench.json")

RETRIEVAL_TOOLS = {"search_books", "get_book_detail", "get_chapter",
                   "search_scholarship", "get_scholarly_source", "websearch",
                   "query_database", "query_graph", "concept_trace"}


class CountingClient:
    """透明计数代理: 引擎经 .invoke(m) 调 LLM; 统计呼叫数与 token usage。"""

    def __init__(self, base, kind, counter):
        self._base = base
        self._kind = kind
        self._counter = counter

    def invoke(self, m, *a, **kw):
        t0 = time.perf_counter()
        resp = self._base.invoke(m, *a, **kw)
        dt = time.perf_counter() - t0
        usage = getattr(resp, "usage_metadata", None) or {}
        rm = getattr(resp, "response_metadata", {}) or {}
        tu = rm.get("token_usage") or {}
        rec = {"kind": self._kind, "latency_s": round(dt, 3),
               "input_tokens": usage.get("input_tokens") or tu.get("prompt_tokens"),
               "output_tokens": usage.get("output_tokens") or tu.get("completion_tokens"),
               "total_tokens": usage.get("total_tokens") or tu.get("total_tokens")}
        self._counter["llm_calls"].append(rec)
        return resp

    def bind_tools(self, *a, **kw):
        inner = self._base.bind_tools(*a, **kw)
        return _BoundCounting(inner, self._kind, self._counter)

    def __getattr__(self, name):
        return getattr(self._base, name)


class _BoundCounting:
    def __init__(self, base, kind, counter):
        self._base = base
        self._kind = kind
        self._counter = counter

    def invoke(self, m, *a, **kw):
        t0 = time.perf_counter()
        resp = self._base.invoke(m, *a, **kw)
        dt = time.perf_counter() - t0
        usage = getattr(resp, "usage_metadata", None) or {}
        rm = getattr(resp, "response_metadata", {}) or {}
        tu = rm.get("token_usage") or {}
        self._counter["llm_calls"].append(
            {"kind": self._kind, "latency_s": round(dt, 3),
             "input_tokens": usage.get("input_tokens") or tu.get("prompt_tokens"),
             "output_tokens": usage.get("output_tokens") or tu.get("completion_tokens"),
             "total_tokens": usage.get("total_tokens") or tu.get("total_tokens")})
        return resp

    def __getattr__(self, name):
        return getattr(self._base, name)


def run_case(case, cfg):
    counter = {"llm_calls": [], "tool_calls": []}
    orig_llm, orig_rllm = EG.get_llm, EG.get_repair_llm

    def mk(kind):
        def _mk():
            return CountingClient(build_candidate_langchain_client(cfg, kind),
                                  kind, counter)
        return _mk

    EG.get_llm = mk("normal")
    EG.get_repair_llm = mk("repair")
    EG._llm = None
    EG._llm_repair = None

    history = case.get("history") or []
    t_start = time.perf_counter()
    evs = []
    try:
        async def collect():
            out = []
            async for ev in EG.stream_agent(case["question"], history,
                                            agent=case.get("agent") or "general",
                                            language=case.get("lang") or "zh"):
                out.append(ev)
            return out
        evs = asyncio_run(collect())
    except Exception as e:
        counter["run_exception"] = str(e)[:300]
    finally:
        total_s = time.perf_counter() - t_start
        EG.get_llm, EG.get_repair_llm = orig_llm, orig_rllm
        EG._llm = None
        EG._llm_repair = None

    done = next((e for e in reversed(evs) if e.get("type") == "done"), {})
    errors = [e for e in evs if e.get("type") == "error"]
    answer = "".join(e.get("content", "") for e in evs if e.get("type") == "token")
    val = done.get("validation") or {}
    tool_events = [e for e in evs if e.get("type") == "tool_start"]
    tool_seq = [e.get("name") for e in tool_events]
    tool_args = [e.get("args") for e in tool_events]
    retrieval_calls = [n for n in tool_seq if n in RETRIEVAL_TOOLS]
    # DUPLICATE_CALLS: 同名工具同参数的重复调用（JSON 规范化）
    seen, dups = {}, 0
    for name, args in zip(tool_seq, tool_args):
        key = (name, json.dumps(args, sort_keys=True, ensure_ascii=False,
                                default=str)[:400])
        seen[key] = seen.get(key, 0) + 1
    dups = sum(v - 1 for v in seen.values() if v > 1)
    calls = counter["llm_calls"]
    tok = {k: sum(c.get(k) or 0 for c in calls)
           for k in ("input_tokens", "output_tokens", "total_tokens")}
    record = {
        "case_id": case["case_id"],
        "category": case["category"],
        "question": case["question"],
        "history_turns": len(history),
        "public_thinking_summary": {
            "answer": answer,
            "tool_sequence": tool_seq,
            "retrieval_rounds": len(retrieval_calls),
            "run_exception": counter.get("run_exception"),
        },
        "delivery": {
            "run_status": "COMPLETED" if done else "RUN_ERROR",
            "published": bool(val.get("result", {}).get("ok")),
            "repairs_used": val.get("repairs_used", 0),
            "terminal_pending": not bool(done),
            "final_validation_issue_codes": [i.get("code") for i in
                                             (val.get("result") or {}).get("issues", [])][:8],
        },
        "evidence_refs": {
            "citations": (done.get("citations") or [])[:20],
            "quote_bound": (done.get("quote_bound") or [])[:20],
            "evidence_digest": _digest(done.get("evidence")),
            "scholarly_provenance": _scholarly(done),
        },
        "repair_history": [
            {"round": i + 1,
             "issue_codes": [c for c in (h.get("issue_codes") or [])][:8]}
            for i, h in enumerate((val.get("history") or [])[:4])
        ],
        "failure_codes": [str(e.get("content") or "")[:160] for e in errors][:3],
        "efficiency": {
            "LLM_CALLS": len(calls),
            "TOOL_CALLS": len(tool_seq),
            "RETRIEVAL_ROUNDS": len(retrieval_calls),
            "DUPLICATE_CALLS": dups,
            "TOTAL_LATENCY_S": round(total_s, 2),
            "REPAIR_COUNT": val.get("repairs_used", 0),
            "TOKEN_USAGE": tok,
            "TOKEN_COST": None,
            "COST_SOURCE": "UNAVAILABLE",
        },
        "llm_call_latency_s": [c["latency_s"] for c in calls],
        "tool_args_digest": [json.dumps(a, sort_keys=True, ensure_ascii=False,
                                        default=str)[:200] for a in tool_args],
    }
    return record


def _digest(ev):
    if not isinstance(ev, dict):
        return ev
    keep = {"used_evidence", "citations", "unverified_citations", "claims",
            "retrieved_evidence", "candidate_evidence", "scholarly_records",
            "scholarly_evidence"}
    out = {}
    for k, v in ev.items():
        if isinstance(v, list):
            out[k] = v if k in keep else v[:10]
        elif isinstance(v, dict):
            out[k] = {kk: v[kk] for kk in list(v)[:10]}
        else:
            out[k] = v
    return out


def _scholarly(done):
    ss = done.get("scholarly_sources") or {}
    return {"SCHOLARLY_SEARCH_CALLS": ss.get("scholarly_search_calls", 0),
            "SCHOLARLY_SOURCE_FETCH_CALLS": ss.get("scholarly_source_fetch_calls", 0),
            "SCHOLARLY_RECORD_COUNT": len(ss.get("scholarly_records") or []),
            "SCHOLARLY_ACCESS_LEVELS": ss.get("scholarly_access") or {}}


def asyncio_run(coro):
    import asyncio
    return asyncio.run(coro)


def main(only=None):
    caseset = json.load(open(CASESET, encoding="utf-8"))
    cases = caseset["cases"]
    cfg = v4pro_config(dict(RP_B, id="RP-B"), requested_model="deepseek-flash",
                       candidate_id="deepseek-flash@RP-B")
    runs = []
    if os.path.exists(OUT_PATH):
        runs = json.load(open(OUT_PATH, encoding="utf-8"))
    done_ids = {r["case_id"] for r in runs}
    for case in cases:
        if only and case["case_id"] not in only:
            continue
        if case["case_id"] in done_ids:
            continue
        print(f"== {case['case_id']} [{case['category']}]", flush=True)
        t0 = time.perf_counter()
        try:
            r = run_case(case, cfg)
        except Exception as e:
            r = {"case_id": case["case_id"], "category": case["category"],
                 "question": case["question"],
                 "failure_codes": [f"HARNESS_ERROR: {e}"[:200]],
                 "delivery": {"run_status": "RUN_ERROR", "published": False}}
        runs = [x for x in runs if x["case_id"] != case["case_id"]] + [r]
        json.dump(runs, open(OUT_PATH, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        d = r.get("delivery", {})
        eff = r.get("efficiency", {})
        print(f"   pub={d.get('published')} tools={eff.get('TOOL_CALLS')} "
              f"llm={eff.get('LLM_CALLS')} lat={eff.get('TOTAL_LATENCY_S')}s "
              f"({time.perf_counter() - t0:.0f}s wall)", flush=True)
    print(f"DONE total={len(runs)}/{len(cases)}", flush=True)


if __name__ == "__main__":
    _only = None
    for a in sys.argv[1:]:
        if a not in ("-", ""):
            _only = a.split(",")
    main(only=_only)
