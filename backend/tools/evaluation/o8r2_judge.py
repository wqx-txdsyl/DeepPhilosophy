# -*- coding: utf-8 -*-
"""O8-R2 §3: per-case capability judge（evaluation-only）。

复用 frozen judge 基建约定（json_object/temperature=0/封闭 taxonomy 风格）。
评分: 7 轴（Question Interpretation/Research Strategy/Tool Selection/Tool
Sequence/Evidence/Repair/Final Answer, 各 PASS|CONCERN|FAIL + 理由）+ 12 能力
维度 0-4 分。禁改 benchmark 本身。
产出 backend/tools/_tmp/o8r2_judge.json（增量断点续跑）。
"""
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, "backend", "tools", "evaluation"))

import o7_scholarly_judge as O7A  # noqa: E402
import urllib.request
import urllib.error
import socket
import hashlib

BENCH = os.path.join(ROOT, "backend/tools/_tmp/o8r2_bench.json")
CASESET = os.path.join(ROOT, "docs/evidence/O8_R2_CASESET.json")
OUT = os.path.join(ROOT, "backend/tools/_tmp/o8r2_judge.json")

AXES = ["Question Interpretation", "Research Strategy", "Tool Selection",
        "Tool Sequence", "Evidence", "Repair", "Final Answer"]
DIMS = ["philosophical_depth", "textual_accuracy", "argument_quality",
        "explanation_quality", "scholarship", "evidence_discipline",
        "tool_selection", "retrieval_strategy", "expression_naturalness",
        "depth_match", "efficiency", "convergence"]

SYSTEM = """你是 PhiAgent O8-R2 执行审计的独立评审（judge）。给你一道哲学基准题
（含期望能力与工具期望）和被测系统的实际回答与遥测。请严格按 JSON 输出，
键名必须逐字使用下列固定键（不得增删改名）：
{"axes": {
  "question_interpretation": {"verdict": "PASS|CONCERN|FAIL", "reason": "一句话中文"},
  "research_strategy": {"verdict": "PASS|CONCERN|FAIL", "reason": "一句话中文"},
  "tool_selection": {"verdict": "PASS|CONCERN|FAIL", "reason": "一句话中文"},
  "tool_sequence": {"verdict": "PASS|CONCERN|FAIL", "reason": "一句话中文"},
  "evidence": {"verdict": "PASS|CONCERN|FAIL", "reason": "一句话中文"},
  "repair": {"verdict": "PASS|CONCERN|FAIL", "reason": "一句话中文"},
  "final_answer": {"verdict": "PASS|CONCERN|FAIL", "reason": "一句话中文"}
 },
 "dimensions": {
  "philosophical_depth": 0,
  "textual_accuracy": 0,
  "argument_quality": 0,
  "explanation_quality": 0,
  "scholarship": 0,
  "evidence_discipline": 0,
  "tool_selection": 0,
  "retrieval_strategy": 0,
  "expression_naturalness": 0,
  "depth_match": 0,
  "efficiency": 0,
  "convergence": 0
 },
 "honesty_flag": false,
 "overresearch_flag": false,
 "summary": "一句话总评"}
dimensions 每项为 0-4 整数。7 轴固定为 question_interpretation / research_strategy /
tool_selection / tool_sequence / evidence / repair / final_answer。
判分原则：证据纪律优先——伪造引文/出处直接 evidence 与 final_answer FAIL 且 honesty_flag=true；
简单题（category 含 simple）按过度研究在 efficiency 与 depth_match 扣分并置 overresearch_flag=true；
空答案/运行错误全轴 FAIL。
不奉承, 不放水。"""


def build_prompt(case, rec):
    eff = rec.get("efficiency") or {}
    ans = (rec.get("public_thinking_summary") or {}).get("answer") or ""
    parts = [
        f"[category] {rec.get('category')}",
        f"[question] {case['question']}",
        f"[expected_capability] {case.get('expected_capability','')}",
        f"[tool_expectation] {json.dumps(case.get('tool_expectation',{}), ensure_ascii=False)}",
        f"[tool_sequence] {json.dumps((rec.get('public_thinking_summary') or {}).get('tool_sequence'))}",
        f"[efficiency] LLM_CALLS={eff.get('LLM_CALLS')} TOOL_CALLS={eff.get('TOOL_CALLS')} "
        f"RETRIEVAL_ROUNDS={eff.get('RETRIEVAL_ROUNDS')} DUPLICATE_CALLS={eff.get('DUPLICATE_CALLS')} "
        f"REPAIR_COUNT={eff.get('REPAIR_COUNT')}",
        f"[publication_state] {json.dumps(rec.get('delivery'), ensure_ascii=False)}",
        f"[failure_codes] {json.dumps(rec.get('failure_codes'), ensure_ascii=False)}",
        f"[final_answer]\n{ans[:7000]}",
    ]
    if case.get("history"):
        parts.append(f"[conversation_history] {json.dumps(case['history'], ensure_ascii=False)[:1500]}")
    return "\n".join(parts)


def call_judge(prompt, _key):
    payload = {"model": "glm-4.6", "temperature": 0, "max_tokens": 3000,
               "thinking": {"type": "disabled"},
               "response_format": {"type": "json_object"},
               "messages": [{"role": "system", "content": SYSTEM},
                            {"role": "user", "content": prompt}]}
    req = urllib.request.Request(O7A.JUDGE_BASE_URL,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json",
                 "Authorization": "Bearer " + (_key or "")})
    with urllib.request.urlopen(req, timeout=240) as r:
        outer = json.loads(r.read())
    return outer["choices"][0]["message"]["content"]


def main(only=None):
    _key = os.environ.get("JUDGE_KEY")
    if not _key:
        env = open(os.path.join(ROOT, ".env"), encoding="utf-8").read()
        for line in env.splitlines():
            if line.strip().startswith("ZHIPU_API_KEY="):
                _key = line.split("=", 1)[1].strip().strip('"').strip("'")
                break
    caseset = {c["case_id"]: c for c in json.load(open(CASESET, encoding="utf-8"))["cases"]}
    bench = json.load(open(BENCH, encoding="utf-8"))
    results = []
    if os.path.exists(OUT):
        results = json.load(open(OUT, encoding="utf-8"))
    done = {r["case_id"] for r in results}
    for rec in bench:
        cid = rec["case_id"]
        if only and cid not in only:
            continue
        if cid in done:
            continue
        case = caseset[cid]
        prompt = build_prompt(case, rec)
        entry = {"case_id": cid}
        t0 = time.perf_counter()
        try:
            content = call_judge(prompt, _key)
            entry["judge"] = json.loads(content)
            entry["judge_status"] = "OK"
        except Exception as e:
            entry["judge_status"] = "ERROR"
            entry["judge_error"] = str(e)[:200]
        entry["latency_s"] = round(time.perf_counter() - t0, 1)
        results = [x for x in results if x["case_id"] != cid] + [entry]
        json.dump(results, open(OUT, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        print(f"== judged {cid}: {entry['judge_status']} ({entry['latency_s']}s)",
              flush=True)
    print(f"JUDGE DONE: {len(results)}/{len(bench)}", flush=True)


if __name__ == "__main__":
    main(only=(sys.argv[1].split(",") if len(sys.argv) > 1 and sys.argv[1] != "-" else None))
