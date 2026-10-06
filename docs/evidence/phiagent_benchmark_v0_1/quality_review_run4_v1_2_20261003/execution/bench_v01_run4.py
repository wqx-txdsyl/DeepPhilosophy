# -*- coding: utf-8 -*-
"""PhiAgent benchmark v0.1 live run4 runner — 65 题实测（prompts.jsonl）。

与 run3（bench_v01_run3.py）同一合同, 差异:
  - 轨迹目录 traces_run4/;
  - SP 基线: agent_release.json active_prompt_version=0.1.3（run3 为 0.1.2;
    0.1.3 是 RUN3 评审后的提示词修订, 本次为其首次全量实测）;
  - general 管线代码相对 run3（2f066b99）仅 SP 文本变化 + soul agent 路径重构
    （不影响 general）; deep_bare_agent 的 suggest 门控等价改写。

执行路径: 进程内直调 engine_langgraph.stream_agent（= 生产 SSE /api/agent/stream_lg）。
DEEP_AGENT_RUNTIME 默认 bare → general 走 deep_bare_agent.stream_bare_agent,
tool 事件携带完整 JSON 序列化返回; assistant_commentary = 内容通道工作笔记（思考流）。

合同:
  - manual_prompt_ready=false 的 K 组 5 题不执行（落盘 SKIPPED 轨迹）;
  - J 组多轮: follow_up_turns 逐轮追加 history（user/assistant 交替）;
  - 每轮记录: 墙钟/首 token 时间, 思考流（assistant_commentary 笔记 +
    provider_reasoning_delta 原生思维链）, 工具调用（tool_start + tool 事件,
    完整返回）, 最终回答（token 拼接, 与 done.content 核对）, citations/evidence;
  - done 即停; 402/余额不足 → 中止剩余题目并如实记录;
  - 轨迹可续跑: traces_run4/<ID>.json 存在即跳过。
"""
import argparse
import asyncio
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone

BACKEND = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REPO = os.path.dirname(BACKEND)
sys.path.insert(0, BACKEND)

SUITE_DIR = os.path.join(REPO, "docs", "evidence", "phiagent_benchmark_v0_1")
PROMPTS = os.path.join(SUITE_DIR, "prompts.jsonl")
TRACE_DIR = os.path.join(SUITE_DIR, "traces_run4")
CONCURRENCY = 2
TURN_TIMEOUT_S = 600

_BALANCE_ERR = ("402", "Insufficient Balance", "余额不足")


def _now_iso():
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _git_head():
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO,
                                       text=True).strip()
    except Exception:
        return None


def _git_dirty():
    try:
        out = subprocess.check_output(["git", "status", "--porcelain"], cwd=REPO,
                                      text=True)
        return len([l for l in out.splitlines() if l.strip()])
    except Exception:
        return None


async def run_turn(question, history):
    """单轮执行: 返回 (turn_record, fatal_balance_error)."""
    from engine_langgraph import stream_agent
    t0 = time.time()
    rec = {"turn": None, "question": question, "wall_s": None, "ttft_s": None,
           "public_notes": [], "provider_reasoning": "",
           "tool_calls_full": [], "tool_timeline": [],
           "answer": "", "answer_chars": 0, "done_content": None,
           "done_matches_tokens": None, "citations": None, "evidence_stats": None,
           "safety": None, "suggestions_status": None,
           "finish_reason": None, "engine_duration_s": None, "validation": None,
           "token_usage": None, "scholarly_sources_count": None,
           "timing_phases": None, "stream_error": None, "events": [],
           "status": "RUNNING"}
    answer_parts = []
    reasoning_parts = []
    preview_events = 0
    fatal = False

    async def consume():
        nonlocal fatal, preview_events
        agen = stream_agent(question, list(history), agent="general", language="zh")
        try:
            async for ev in agen:
                await _handle(ev)
        finally:
            # done 即停会弃流: 显式 aclose 收敛清理, 防止 RuntimeError
            # "generator didn't stop after athrow()" 在 gather 中炸掉后续 worker
            try:
                await asyncio.wait_for(agen.aclose(), timeout=10)
            except Exception:
                pass

    async def _handle(ev):
        nonlocal fatal, preview_events
        t = ev.get("type")
        rel = round(time.time() - t0, 1)
        if t == "status":
            rec["events"].append({"t": rel, "ev": "status", "content": ev.get("content")})
        elif t == "assistant_commentary":
            rec["public_notes"].append({"source": "assistant_commentary",
                                        "id": ev.get("id"),
                                        "content": ev.get("content") or ""})
            rec["events"].append({"t": rel, "ev": "assistant_commentary",
                                  "chars": len(ev.get("content") or "")})
        elif t == "thinking_summary":
            rec["public_notes"].append({"source": "summary", "phase": ev.get("phase"),
                                        "content": ev.get("content") or ""})
        elif t == "thinking_summary_delta":
            rec["public_notes"].append({"source": "delta", "phase": ev.get("phase"),
                                        "content": ev.get("content") or ""})
        elif t == "provider_reasoning_delta":
            c = ev.get("content") or ""
            reasoning_parts.append(c)
        elif t == "tool_start":
            rec["events"].append({"t": rel, "ev": "tool_start", "name": ev.get("name"),
                                  "call_id": ev.get("call_id") or ev.get("tool_call_id")})
            rec["tool_timeline"].append({"t": rel, "phase": "start",
                                         "name": ev.get("name"),
                                         "call_id": ev.get("call_id") or ev.get("tool_call_id")})
        elif t == "tool":
            res = ev.get("result")
            res = res if isinstance(res, str) else json.dumps(res, ensure_ascii=False, default=str)
            entry = {"name": ev.get("name"), "args": ev.get("args"),
                     "status": ev.get("status"),
                     "duration_seconds": ev.get("duration_seconds"),
                     "result_full": res}
            rec["tool_calls_full"].append(entry)
            if rec["tool_timeline"] and rec["tool_timeline"][-1]["name"] == ev.get("name") \
                    and rec["tool_timeline"][-1]["phase"] == "start":
                rec["tool_timeline"][-1].update({"phase": "result", **{k: entry[k] for k in
                                                                      ("status", "duration_seconds")}})
            else:
                rec["tool_timeline"].append({"t": rel, "phase": "result_orphan", **entry})
            rec["events"].append({"t": rel, "ev": "tool", "name": ev.get("name"),
                                  "status": ev.get("status"),
                                  "duration_s": ev.get("duration_seconds"),
                                  "result_chars": len(res),
                                  "result_head": res[:160]})
        elif t == "tool_note":
            rec["events"].append({"t": rel, "ev": "tool_note", "content": ev.get("content")})
        elif t == "tool_cancel":
            rec["events"].append({"t": rel, "ev": "tool_cancel", "name": ev.get("name")})
        elif t == "answer_preview":
            preview_events += 1
            if rec["ttft_s"] is None:
                rec["ttft_s"] = rel
        elif t == "answer_preview_reset":
            rec["events"].append({"t": rel, "ev": "answer_preview_reset"})
        elif t == "token":
            if rec["ttft_s"] is None:
                rec["ttft_s"] = rel
            answer_parts.append(ev.get("content", ""))
        elif t == "validation_failed":
            rec["events"].append({"t": rel, "ev": "validation_failed",
                                  "content": str(ev.get("content"))[:200]})
        elif t == "error":
            msg = str(ev.get("content") or ev.get("code") or "")[:300]
            rec["stream_error"] = msg
            rec["events"].append({"t": rel, "ev": "error", "content": msg})
            if any(b in msg for b in _BALANCE_ERR):
                fatal = True
                return
        elif t == "done":
            d = dict(ev)
            rec["done_content"] = d.get("content")
            rec["citations"] = d.get("citations")
            rec["safety"] = d.get("safety")
            rec["suggestions_status"] = d.get("suggestions_status")
            rec["finish_reason"] = d.get("finish_reason")
            rec["engine_duration_s"] = d.get("duration_seconds")
            rec["validation"] = d.get("validation")
            disc = d.get("research_discipline") or {}
            if isinstance(disc, dict) and isinstance(disc.get("token_usage"), dict):
                rec["token_usage"] = disc["token_usage"]
            timing = d.get("timing") or {}
            if isinstance(timing, dict):
                rec["timing_phases"] = timing.get("phases")
            ss = d.get("scholarly_sources")
            if isinstance(ss, list):
                rec["scholarly_sources_count"] = len(ss)
            evd = d.get("evidence") or {}
            if isinstance(evd, dict):
                rec["evidence_stats"] = {
                    "keys": sorted(evd.keys()),
                    "retrieved_count": len(evd.get("retrieved_evidence") or []),
                    "display_citations": len(evd.get("display_citations") or []),
                    "primary_research": evd.get("primary_research")}
            rec["events"].append({"t": rel, "ev": "done"})
            return   # done 即停
    try:
        await asyncio.wait_for(consume(), timeout=TURN_TIMEOUT_S)
        rec["status"] = "DONE" if rec["done_content"] is not None else "STREAM_END_NO_DONE"
    except asyncio.TimeoutError:
        rec["stream_error"] = f"TURN_TIMEOUT_{TURN_TIMEOUT_S}s"
        rec["status"] = "TIMEOUT"
    except Exception as e:
        rec["stream_error"] = f"{type(e).__name__}: {str(e)[:200]}"
        rec["status"] = "EXCEPTION"
    rec["provider_reasoning"] = "".join(reasoning_parts)
    answer = "".join(answer_parts)
    rec["answer"] = answer
    rec["answer_chars"] = len(answer)
    rec["done_matches_tokens"] = (rec["done_content"] is not None
                                  and rec["done_content"] == answer)
    rec["wall_s"] = round(time.time() - t0, 1)
    if preview_events:
        rec["preview_events"] = preview_events
    if fatal:
        rec["status"] = "FATAL_BALANCE"
    return rec, fatal


async def run_case(case, meta):
    turns = [case["messages"][0]["content"]] + list(case.get("follow_up_turns") or [])
    trace = {"case_id": case["id"], "category": case["id"][0],
             "prompt": case["messages"][0]["content"],
             "follow_up_turns": case.get("follow_up_turns") or [],
             "manual_prompt_ready": case.get("manual_prompt_ready"),
             "fixture_id": case.get("fixture_id"),
             "runner": meta,
             "turns": [], "total_wall_s": None, "status": "RUNNING"}
    t0 = time.time()
    history = []
    fatal = False
    for i, q in enumerate(turns, 1):
        rec, fatal = await run_turn(q, history)
        rec["turn"] = i
        trace["turns"].append(rec)
        history.append({"role": "user", "content": q})
        history.append({"role": "assistant",
                        "content": rec["answer"] or f"[{rec['status']}] {rec['stream_error'] or ''}"})
        print(f"  [{case['id']}#{i}] {rec['status']} {rec['wall_s']}s "
              f"tools={len(rec['tool_calls_full'])} ans={rec['answer_chars']}c"
              + (f" ERR={rec['stream_error'][:80]}" if rec['stream_error'] else ""), flush=True)
        if fatal or rec["status"] in ("TIMEOUT", "EXCEPTION", "FATAL_BALANCE", "STREAM_END_NO_DONE"):
            break
    trace["total_wall_s"] = round(time.time() - t0, 1)
    if fatal:
        trace["status"] = "ABORTED_BALANCE"
    elif len(trace["turns"]) < len(turns):
        trace["status"] = "PARTIAL_" + trace["turns"][-1]["status"]
    else:
        last = trace["turns"][-1]
        ok = bool(last["answer"].strip()) and last["status"] == "DONE"
        trace["status"] = "COMPLETED" if ok else "COMPLETED_NO_ANSWER"
    return trace, fatal


async def main_run(only=None):
    os.makedirs(TRACE_DIR, exist_ok=True)
    cases = [json.loads(l) for l in open(PROMPTS, encoding="utf-8") if l.strip()]
    ready = [c for c in cases if c.get("manual_prompt_ready")]
    not_ready = [c for c in cases if not c.get("manual_prompt_ready")]
    done_ids = {fn[:-5] for fn in os.listdir(TRACE_DIR)
                if fn.endswith(".json") and not fn.startswith("_")}
    todo = [c for c in ready if c["id"] not in done_ids
            and (only is None or c["id"] in only)]
    print(f"cases total={len(cases)} ready={len(ready)} not_ready={[c['id'] for c in not_ready]} "
          f"done={len(done_ids)} todo={len(todo)}", flush=True)

    if todo and not done_ids:
        import provider_preflight as PP
        pf = PP.run_preflight()
        json.dump(pf, open(os.path.join(TRACE_DIR, "_PREFLIGHT.json"), "w",
                           encoding="utf-8"), ensure_ascii=False, indent=1)
        print("preflight:", json.dumps({k: pf.get(k) for k in (
            "PROVIDER_AUTH_OK", "PROVIDER_BALANCE_OR_QUOTA_OK", "PRIMARY_CHANNEL_OK",
            "WEB_CHANNEL_OK", "SCHOLARLY_CHANNEL_OK", "PRODUCTION_MODEL")},
            ensure_ascii=False), flush=True)
        if not pf.get("ALL_PROVIDER_GATES_PASS"):
            print("ABORT: provider gates failed — 不开始 run", flush=True)
            return 2

    meta = {"git_head": _git_head(), "git_dirty_files": _git_dirty(),
            "started": _now_iso(),
            "engine": "engine_langgraph.stream_agent → bare runtime (deep_bare_agent), = /api/agent/stream_lg",
            "agent": "general", "language": "zh",
            "turn_timeout_s": TURN_TIMEOUT_S,
            "active_prompt_version": json.load(open(os.path.join(BACKEND, "agent_release.json"),
                                                    encoding="utf-8"))["active_prompt_version"],
            "scholarly_network_mode": os.environ.get("SCHOLARLY_NETWORK_MODE", "AUTO"),
            "scholarly_cache_note": "scholarly_cache.json 根值为 dict（run3 同源延续, 后续评测有增量）",
            "note": "done 即停, 跳过 suggestions 后处理"}

    for c in not_ready:
        if c["id"] not in done_ids and (only is None or c["id"] in only):
            json.dump({"case_id": c["id"], "status": "SKIPPED_NOT_READY",
                       "reason": "manual_prompt_ready=false（需 fixtures 注入工具故障/不可信材料条件，本轮未实测，与 run1/run2/run3 同口径）",
                       "fixture_id": c.get("fixture_id"), "prompt": c["messages"][0]["content"]},
                      open(os.path.join(TRACE_DIR, f"{c['id']}.json"), "w",
                           encoding="utf-8"), ensure_ascii=False, indent=1)
            print(f"[{c['id']}] SKIPPED_NOT_READY (fixture={c.get('fixture_id')})", flush=True)

    sem = asyncio.Semaphore(CONCURRENCY)
    abort = {"flag": False, "case": None}

    async def worker(case):
        if abort["flag"]:
            return
        async with sem:
            if abort["flag"]:
                return
            trace, fatal = await run_case(case, meta)
            json.dump(trace, open(os.path.join(TRACE_DIR, f"{case['id']}.json"), "w",
                                  encoding="utf-8"), ensure_ascii=False, indent=1)
            print(f"[{case['id']}] {trace['status']} total={trace['total_wall_s']}s "
                  f"turns={len(trace['turns'])}", flush=True)
            if fatal:
                abort["flag"] = True
                abort["case"] = case["id"]

    await asyncio.gather(*[worker(c) for c in todo])
    meta["finished"] = _now_iso()
    json.dump(meta, open(os.path.join(TRACE_DIR, "_RUN_META.json"), "w",
                         encoding="utf-8"), ensure_ascii=False, indent=1)
    if abort["flag"]:
        print(f"ABORTED at {abort['case']}: 供应商余额耗尽 — 剩余题目未执行, 如实记录", flush=True)
        return 1
    print("ALL DONE", flush=True)
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="仅跑指定 id（逗号分隔, 用于 smoke）")
    a = ap.parse_args()
    sys.exit(asyncio.run(main_run(only=set(a.only.split(",")) if a.only else None)))
