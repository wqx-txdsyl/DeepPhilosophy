# -*- coding: utf-8 -*-
"""O6 Gate B runner — Live 实测评估（EVIDENCE-ONLY, 不改任何生产代码）。

运行:
  .venv/Scripts/python.exe backend/tools/_tmp/o6_gate_b_runner.py --mode cases [--only A1,B2]
  .venv/Scripts/python.exe backend/tools/_tmp/o6_gate_b_runner.py --mode convos [--only M1]
  .venv/Scripts/python.exe backend/tools/_tmp/o6_gate_b_runner.py --mode all

产出: backend/tools/_tmp/o6_gate/gate_b/cases/*.json
      backend/tools/_tmp/o6_gate/gate_b/conversations/*.json
      backend/tools/_tmp/o6_gate/gate_b/summary.json
      backend/tools/_tmp/o6_gate/gate_b/digest.md
模式参照 o3_live_uat.py: asyncio 驱动 EG.stream_agent, 收集全部事件 + done payload。
失败 case: 如实记录; 引擎 error 事件 → 重试 1 次, 仍失败标 FAIL-ENGINE（原始失败保留）。
"""
import argparse
import asyncio
import json
import os
import re
import statistics
import sys
import time

BACKEND = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BACKEND)

import engine_langgraph as EG  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, "o6_gate", "gate_b_fresh")
CASES_DIR = os.path.join(OUT_DIR, "cases")
CONV_DIR = os.path.join(OUT_DIR, "conversations")
QUESTIONS = os.path.join(HERE, "o6_gate", "fresh_questions.json")
CASE_TIMEOUT_S = 900
os.makedirs(CASES_DIR, exist_ok=True)
os.makedirs(CONV_DIR, exist_ok=True)   # 单 case 硬墙钟（含 repair）; 超时记 FAIL-TIMEOUT

# §15 事件白名单（12 类）
EVENT_WHITELIST = {"status", "thinking_summary", "thinking_summary_delta", "tool_start",
                   "tool_note", "tool", "tool_cancel", "token", "validation_failed",
                   "error", "done", "suggestions"}

READ_TOOLS = {"get_chapter", "get_book_detail", "get_philosopher", "philosopher_memory",
              "philosopher_period", "philosopher_style", "philosopher_graph",
              "philosopher_concepts", "philosopher_user"}
SEARCH_TOOLS = {"search_books", "websearch", "philosopher_quote", "philosopher_corpus", "query_graph", "query_database"}

# §16 runtime 追加指纹（O2 已删除 emit_append; 若出现即违归）
OWNERSHIP_FINGERPRINTS = ["（据通行理解", "（与库中原文近似", "（原典核验：", "（更正：", "（补充：",
                          "（据原典", "（核验注：", "（注：以下为"]

RUNTIME_INITIATORS = {"validator", "runtime_mechanical", "runtime", "system", "safety_runtime"}


def classify_tool(name):
    if name in SEARCH_TOOLS:
        return "search"
    if name in READ_TOOLS:
        return "read"
    return "other"


async def _collect(case, history):
    """驱动 stream_agent, 收集全部事件（token 事件如实收集）。"""
    evs = []
    async with asyncio.timeout(CASE_TIMEOUT_S):
        async for ev in EG.stream_agent(case["question"], history,
                                        agent=case.get("agent", "general"), language="zh"):
            evs.append(ev)
    return evs


def run_once(case, history, tag):
    t0 = time.time()
    timeout = False
    exc = None
    evs = []
    try:
        evs = asyncio.run(_collect(case, history))
    except (asyncio.TimeoutError, TimeoutError):
        timeout = True
    except Exception as e:  # 引擎外层兜底之外的异常（不应发生）
        exc = e
    dur = round(time.time() - t0, 1)
    return evs, dur, timeout, exc


def compact_events(evs):
    """压缩 token 事件（逐字流, 每字一条）为计数标记, 其余原样保留。"""
    out = []
    for e in evs:
        if e.get("type") == "token":
            if out and isinstance(out[-1], dict) and out[-1].get("type") == "__tokens__":
                out[-1]["n"] += 1
                out[-1]["chars"] += len(str(e.get("content") or ""))
            else:
                out.append({"type": "__tokens__", "n": 1, "chars": len(str(e.get("content") or ""))})
        else:
            out.append(e)
    return out


def audit_events(evs, answer):
    """§14/§15 机械事件审计。"""
    audit = {
        "n_events": len(evs),
        "type_counts": {},
        "unknown_event_types": [],
        "thinking_events": 0, "thinking_by_initiator": {}, "thinking_phase_seq": [],
        "runtime_thinking_events": 0,
        "raw_cot_marker_hits": [],
        "tool_start": 0, "tool_exec": 0, "tool_cancel": 0,
        "unparented_tool_results": 0,
        "duplicate_visible_events": 0, "duplicate_examples": [],
        "validation_failed_events": 0, "error_events": 0,
        "decision_group_missing": 0, "initiated_by_missing": 0,
        "tool_call_id_missing_on_start": 0, "tool_exec_unbound_ids": 0,
    }
    open_starts = {}   # name -> count of tool_start not yet matched by tool exec
    last_visible = None  # (type, key) for consecutive-duplicate detection
    for e in evs:
        et = e.get("type")
        audit["type_counts"][et] = audit["type_counts"].get(et, 0) + 1
        if et not in EVENT_WHITELIST and et != "__na__":
            audit["unknown_event_types"].append(et)
        if et in ("thinking_summary", "thinking_summary_delta"):
            audit["thinking_events"] += 1
            ini = e.get("initiated_by") or "?"
            audit["thinking_by_initiator"][ini] = audit["thinking_by_initiator"].get(ini, 0) + 1
            if ini in RUNTIME_INITIATORS:
                audit["runtime_thinking_events"] += 1
            audit["thinking_phase_seq"].append(e.get("phase"))
            if not e.get("decision_group_id"):
                audit["decision_group_missing"] += 1
            if not e.get("initiated_by"):
                audit["initiated_by_missing"] += 1
        elif et == "tool_start":
            audit["tool_start"] += 1
            nm = e.get("name")
            open_starts[nm] = open_starts.get(nm, 0) + 1
            if not e.get("tool_call_id"):
                audit["tool_call_id_missing_on_start"] += 1
            if not e.get("decision_group_id") or not e.get("initiated_by"):
                audit["decision_group_missing"] += 1 if not e.get("decision_group_id") else 0
                audit["initiated_by_missing"] += 1 if not e.get("initiated_by") else 0
        elif et == "tool":
            audit["tool_exec"] += 1
            nm = e.get("name")
            if open_starts.get(nm, 0) > 0:
                open_starts[nm] -= 1
            else:
                audit["unparented_tool_results"] += 1
            if not e.get("tool_call_id"):
                audit["tool_exec_unbound_ids"] += 1
            if not e.get("decision_group_id") or not e.get("initiated_by"):
                audit["decision_group_missing"] += 1 if not e.get("decision_group_id") else 0
                audit["initiated_by_missing"] += 1 if not e.get("initiated_by") else 0
        elif et == "tool_cancel":
            audit["tool_cancel"] += 1
        elif et == "validation_failed":
            audit["validation_failed_events"] += 1
        elif et == "error":
            audit["error_events"] += 1
        # 连续重复可见事件检测（token 除外——逐字流天然连续）
        if et in ("thinking_summary", "thinking_summary_delta", "tool_note", "tool", "tool_start"):
            key = (et, e.get("content") or e.get("name"), e.get("name"))
            if last_visible == key and et != "tool_start":
                audit["duplicate_visible_events"] += 1
                if len(audit["duplicate_examples"]) < 5:
                    audit["duplicate_examples"].append(
                        {"type": et, "content": str(e.get("content") or e.get("name"))[:80]})
            last_visible = key
    # raw CoT 公开粗查：thinking/answer 中出现 provider reasoning 残留标记
    blob = answer + " " + " ".join(str(e.get("content") or "") for e in evs
                                   if e.get("type") in ("thinking_summary", "thinking_summary_delta"))
    for marker in ["<think>", "reasoning_content", "</think>", "<rationale>"]:
        if marker in blob:
            audit["raw_cot_marker_hits"].append(marker)
    return audit


def extract_case(case, evs, dur, tag, attempt):
    """事件流 → 结构化 case 结果。"""
    answer = "".join(str(e.get("content") or "") for e in evs if e.get("type") == "token")
    done = next((e for e in reversed(evs) if e.get("type") == "done"), None)
    error_evs = [e for e in evs if e.get("type") == "error"]
    vfail = [e for e in evs if e.get("type") == "validation_failed"]
    tool_calls = (done or {}).get("tool_calls") or []
    tool_seq = [{"name": t.get("name"), "cls": classify_tool(t.get("name") or ""),
                 "args": t.get("args"),
                 "reused": str(t.get("thought") or "").startswith("EXACT_DUPLICATE_REUSED"),
                 "err": bool(isinstance(t.get("result_summary"), str) and "error" in str(t.get("result_summary")).lower())}
                for t in tool_calls]
    validation = (done or {}).get("validation")
    ok = bool((validation or {}).get("result", {}).get("ok"))
    published = bool(answer.strip()) and ok and not error_evs
    audit = audit_events(evs, answer)
    fingerprints = [fp for fp in OWNERSHIP_FINGERPRINTS if fp in answer]
    budget = ((done or {}).get("tool_loop") or {}).get("budget") or {}
    record = {
        "id": case["id"], "category": case.get("category"), "fresh": case.get("fresh", True),
        "question": case["question"], "agent": case.get("agent", "general"),
        "attempt": attempt, "tag": tag,
        "duration_s": dur, "answer_chars": len(answer), "answer": answer,
        "published": published,
        "validation": validation,
        "validation_failed_payload": vfail[-1] if vfail else None,
        "error_payload": error_evs[-1] if error_evs else None,
        "tool_calls": tool_calls,
        "tool_seq": tool_seq,
        "tool_count": len(tool_seq),
        "search_calls": sum(1 for t in tool_seq if t["cls"] == "search"),
        "read_calls": sum(1 for t in tool_seq if t["cls"] == "read"),
        "budget": budget,
        "quote_bound": (done or {}).get("quote_bound"),
        "citations": (done or {}).get("citations"),
        "citation_sanitize": (done or {}).get("citation_sanitize"),
        "causal": (done or {}).get("causal"),
        "final_ownership": (done or {}).get("final_ownership"),
        "temporal": (done or {}).get("temporal"),
        "timing": (done or {}).get("timing"),
        "event_audit": audit,
        "ownership_fingerprints": fingerprints,
    }
    record["status"] = ("FAIL-TIMEOUT" if tag == "timeout"
                        else "FAIL-ENGINE" if tag == "engine"
                        else "PUBLISHED" if published
                        else "SAFE_REJECT" if (not ok and vfail)
                        else "NO_PUBLISH" if not answer.strip() and not error_evs
                        else "ERROR")
    return record


def save_case(rec, evs):
    path = os.path.join(CASES_DIR, f"{rec['id']}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"result": rec, "events_compact": compact_events(evs)}, f,
                  ensure_ascii=False, indent=1, default=str)
    return path


def _engine_crash(evs, timeout, exc):
    """真引擎故障（区别于 validator 耗尽的干净 safe-reject 收口）。"""
    if timeout or exc:
        return True
    has_error = any(e.get("type") == "error" for e in evs)
    has_vfail = any(e.get("type") == "validation_failed" for e in evs)
    has_done = any(e.get("type") == "done" for e in evs)
    return has_error and not has_vfail or (has_error and not has_done)


def run_single(case):
    """单 case: 首跑; 仅真引擎故障才重试 1 次（原始失败保留）。"""
    print(f"\n═══ {case['id']} [{case.get('category')}] agent={case.get('agent','general')} "
          f"fresh={case.get('fresh', True)}: {case['question'][:40]}… ═══")
    evs, dur, timeout, exc = run_once(case, [], "first")
    if _engine_crash(evs, timeout, exc):
        reason = "timeout" if timeout else ("engine-exception" if exc else "engine-error-event")
        print(f"  ! first attempt problem: {reason}; retrying once (original preserved)")
        evs2, dur2, timeout2, exc2 = run_once(case, [], "retry")
        rec = extract_case(case, evs2, dur2, "timeout" if timeout2 else ("engine" if exc2 else "ok"), 2)
        rec["first_attempt_summary"] = {"duration_s": dur, "timeout": timeout,
                                        "exception": str(exc) if exc else None,
                                        "had_error_event": any(e.get("type") == "error" for e in evs),
                                        "had_validation_failed": any(e.get("type") == "validation_failed" for e in evs)}
        save_case(rec, evs2)
    else:
        rec = extract_case(case, evs, dur, "ok", 1)
        save_case(rec, evs)
    print(f"  status={rec['status']} dur={rec['duration_s']}s chars={rec['answer_chars']} "
          f"tools={rec['tool_count']} (S={rec['search_calls']}/R={rec['read_calls']}) "
          f"repaired={((rec.get('validation') or {}).get('repairs_used'))} "
          f"quotes={((rec.get('quote_bound') or {}).get('summary') or {})}")
    return rec


def run_conversation(conv):
    """多轮: history 串接。返回记录。"""
    cid = conv["id"]
    path = os.path.join(CONV_DIR, f"{cid}.json")
    if os.path.exists(path):
        print(f"  (exists, skip) {path}")
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    history = []
    turns = []
    print(f"\n═══ CONV {cid} [{conv['gate']}] {len(conv['turns'])} turns ═══")
    for i, turn in enumerate(conv["turns"], 1):
        case = {"id": f"{cid}-T{i}", "category": f"CONV-{conv['gate']}", "fresh": True,
                "agent": turn.get("agent", "general"), "question": turn["question"]}
        print(f"  T{i} agent={case['agent']}: {turn['question'][:44]}…")
        evs, dur, timeout, exc = run_once(case, history, "first")
        if _engine_crash(evs, timeout, exc):
            print(f"    ! retry ({'timeout' if timeout else ('exception' if exc else 'engine-error')})")
            evs, dur, timeout, exc = run_once(case, history, "retry")
        rec = extract_case(case, evs, dur, "timeout" if timeout else ("engine" if exc else "ok"), 1)
        turns.append(rec)
        if rec["answer"].strip():
            history.append({"role": "user", "content": turn["question"]})
            history.append({"role": "assistant", "content": rec["answer"]})
        else:
            history.append({"role": "user", "content": turn["question"]})
            history.append({"role": "assistant", "content": "（本轮未产生有效回答）"})
    out = {"id": cid, "gate": conv["gate"], "turns": turns,
           "n_turns": len(turns),
           "published_turns": sum(1 for t in turns if t["published"])}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1, default=str)
    print(f"  saved → {path} ({out['published_turns']}/{out['n_turns']} published)")
    return out


def p95(vals):
    if not vals:
        return 0
    s = sorted(vals)
    idx = max(0, min(len(s) - 1, int(round(0.95 * (len(s) - 1)))))
    return s[idx]


def build_summary(records):
    """聚合指标（机械部分）。"""
    core = [r for r in records if r["category"] not in ("CONV",) ]
    pubs = [r for r in core if r["status"] == "PUBLISHED"]
    rejects = [r for r in core if r["status"] == "SAFE_REJECT"]
    engines = [r for r in core if r["status"] == "FAIL-ENGINE"] + [r for r in core if r["status"] == "FAIL-TIMEOUT"]
    tools = [r["tool_count"] for r in core]
    zero = [r for r in core if r["tool_count"] == 0]
    repair_attempted = [r for r in core if ((r.get("validation") or {}).get("repairs_used") or 0) > 0]
    repair_success = [r for r in repair_attempted if r["status"] == "PUBLISHED"]
    qb = {"quotes": 0, "verified_exact": 0, "verified_near": 0, "memory_only": 0,
          "stitched": 0, "unverified_blockquote": 0, "memory_only_exact_claim": 0}
    for r in pubs:
        s = ((r.get("quote_bound") or {}).get("summary") or {})
        for k in qb:
            qb[k] += s.get(k, 0) or 0
    unverified_citation_public = 0
    # 与 final_validator 同一边界: 模板占位符回显（【《书名》·章节】）不构成引用主张
    _PB = {"书名", "作品", "Book", "book"}
    _PC = {"章节", "篇名", "章名", "Chapter", "chapter"}
    for r in pubs:
        cs = r.get("citation_sanitize") or {}
        real_unv = [u for u in (cs.get("unverified_before") or [])
                    if not (u.get("book") in _PB
                            and (u.get("chapter") in (None, "") or u.get("chapter") in _PC))]
        if real_unv:
            unverified_citation_public += 1
    dur = sorted(r["duration_s"] for r in core)
    return {
        "n_cases": len(core),
        "published": len(pubs),
        "publication_rate": round(len(pubs) / max(1, len(core)), 4),
        "safe_reject": len(rejects),
        "safe_reject_rate": round(len(rejects) / max(1, len(core)), 4),
        "engine_fail": len(engines),
        "tools_avg": round(statistics.mean(tools), 2) if tools else 0,
        "tools_median": statistics.median(tools) if tools else 0,
        "tools_p95": p95(tools),
        "search_calls_total": sum(r["search_calls"] for r in core),
        "read_calls_total": sum(r["read_calls"] for r in core),
        "zero_tool_cases": len(zero),
        "zero_tool_published": sum(1 for r in zero if r["status"] == "PUBLISHED"),
        "duplicate_reused_total": sum((r.get("budget") or {}).get("duplicate_reused", 0) for r in core),
        "no_gain_total": sum((r.get("budget") or {}).get("no_gain", 0) for r in core),
        "hard_ceiling_hits": sum(1 for r in core if (r.get("budget") or {}).get("hard")),
        "repair_attempted": len(repair_attempted),
        "repair_success": len(repair_success),
        "repair_exhausted": len([r for r in repair_attempted if r["status"] != "PUBLISHED"]),
        "quote_bound_pub_agg": qb,
        "unverified_citation_public_cases": unverified_citation_public,
        "runtime_thinking_events": sum(r["event_audit"]["runtime_thinking_events"] for r in core),
        "unknown_event_types": sorted({t for r in core for t in r["event_audit"]["unknown_event_types"]}),
        "duplicate_visible_events": sum(r["event_audit"]["duplicate_visible_events"] for r in core),
        "unparented_tool_results": sum(r["event_audit"]["unparented_tool_results"] for r in core),
        "ownership_fingerprint_cases": [r["id"] for r in core if r["ownership_fingerprints"]],
        "duration_p50": dur[len(dur) // 2] if dur else 0,
        "duration_p95": p95([r["duration_s"] for r in core]),
        "duration_max": max(dur) if dur else 0,
        "status_by_case": {r["id"]: {"status": r["status"], "tools": r["tool_count"],
                                     "dur": r["duration_s"], "category": r["category"],
                                     "fresh": r["fresh"], "agent": r["agent"]}
                           for r in core},
    }


def write_digest(records, convs):
    lines = ["# O6 Gate B digest（自动生成, 供评阅）", ""]
    for r in records:
        lines.append(f"## {r['id']} [{r['category']}] fresh={r['fresh']} agent={r['agent']} "
                     f"status={r['status']} dur={r['duration_s']}s tools={r['tool_count']} "
                     f"(S={r['search_calls']}/R={r['read_calls']}) "
                     f"repairs={((r.get('validation') or {}).get('repairs_used') or 0)}")
        seq = " → ".join(t["name"] + ("(REUSED)" if t["reused"] else "") for t in r["tool_seq"]) or "(zero-tool)"
        lines.append(f"- tool_seq: {seq}")
        v = (r.get("validation") or {}).get("result") or {}
        if v:
            issues = v.get("issues") or []
            lines.append(f"- validator ok={v.get('ok')} issues={[i.get('code') for i in issues][:6]}")
        qbs = ((r.get("quote_bound") or {}).get("summary") or {})
        if qbs:
            lines.append(f"- quote_bound: {json.dumps(qbs, ensure_ascii=False)}")
        if r.get("error_payload"):
            lines.append(f"- ERROR: {str(r['error_payload'].get('content'))[:120]}")
        lines.append(f"- Q: {r['question']}")
        lines.append(f"- A（{r['answer_chars']} 字）: {r['answer'][:2600]}")
        lines.append("")
    for c in convs:
        lines.append(f"## CONV {c['id']} [{c['gate']}] published {c['published_turns']}/{c['n_turns']}")
        for t in c["turns"]:
            lines.append(f"### {t['id']} agent={t['agent']} status={t['status']} tools={t['tool_count']} dur={t['duration_s']}s")
            seq = " → ".join(x["name"] for x in t["tool_seq"]) or "(zero-tool)"
            lines.append(f"- tool_seq: {seq}")
            lines.append(f"- Q: {t['question']}")
            lines.append(f"- A: {t['answer'][:2200]}")
            lines.append("")
    with open(os.path.join(OUT_DIR, "digest.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", default="all", choices=["cases", "convos", "all"])
    ap.add_argument("--only", default="")
    args = ap.parse_args()
    only = {x.strip().upper() for x in args.only.split(",") if x.strip()}
    with open(QUESTIONS, encoding="utf-8") as f:
        q = json.load(f)
    single = q["single_turn_cases"] + q["supplementary_cases"]
    if only:
        single = [c for c in single if c["id"].upper() in only]
        q["conversations"] = [c for c in q["conversations"] if c["id"].upper() in only]
    records = []
    if args.mode in ("cases", "all"):
        for c in single:
            p = os.path.join(CASES_DIR, f"{c['id']}.json")
            if os.path.exists(p) and not only:
                print(f"  (exists, skip) {p}")
                with open(p, encoding="utf-8") as f:
                    records.append(json.load(f)["result"])
                continue
            records.append(run_single(c))
    convs = []
    if args.mode in ("convos", "all"):
        for conv in q["conversations"]:
            convs.append(run_conversation(conv))
    if args.mode == "cases" and not convs:
        # 载入已有 convos 以便 digest 完整
        for cid in ("M1", "M2", "M3", "M4", "M5"):
            p = os.path.join(CONV_DIR, f"{cid}.json")
            if os.path.exists(p):
                with open(p, encoding="utf-8") as f:
                    convs.append(json.load(f))
    summary = build_summary(records)
    with open(os.path.join(OUT_DIR, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=1)
    write_digest(records, convs)
    print("\n═══ O6 GATE B SUMMARY ═══")
    print(json.dumps({k: v for k, v in summary.items() if k != "status_by_case"},
                     ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
