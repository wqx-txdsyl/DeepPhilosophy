# -*- coding: utf-8 -*-
"""O7-E scholarly judge——复用 O7-A 已资格认证的 glm-4.6（temperature=0,
thinking=disabled, json_object）, k=3 ensemble + deterministic aggregator。

judge 输入（§31）: question / final answer / case category / applicability /
persona / primary evidence digest / scholarly source records / abstract-passage
evidence / bibliographic provenance / access levels。
禁止: expected scholar / reference answer / target score。

用法: SCHOLARLY_NETWORK_MODE=TRUSTED_PROXY .venv/bin/python backend/tools/evaluation/o7e_judge.py CAL|HOLDOUT
产出: backend/tools/_tmp/o7e_judge_<scope>.json（断点续跑）
"""
import hashlib
import json
import os
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, "backend"))
sys.path.insert(0, os.path.join(ROOT, "backend", "tools", "evaluation"))

import o7e_cases as CASES
import o7_scholarly_judge as O7A   # O7-A 宪法: JUDGE_SYSTEM_PROMPT / 聚合不变量

TMP = os.path.join(ROOT, "backend", "tools", "_tmp")
_key = None
for line in open(os.path.join(ROOT, ".env"), encoding="utf-8"):
    if line.strip().startswith("ZHIPU_API_KEY="):
        _key = line.split("=", 1)[1].strip().strip('"').strip("'")

K = 3


def _call(prompt):
    payload = {"model": "glm-4.6", "temperature": 0, "max_tokens": 4000,
               "thinking": {"type": "disabled"},
               "response_format": {"type": "json_object"},
               "messages": [{"role": "system", "content": O7A.JUDGE_SYSTEM_PROMPT},
                            {"role": "user", "content": prompt}]}
    req = urllib.request.Request(
        O7A.JUDGE_BASE_URL, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json",
                 "Authorization": "Bearer " + (_key or "")})
    with urllib.request.urlopen(req, timeout=240) as r:
        return json.loads(r.read())["choices"][0]["message"]["content"] or ""


def _scholarly_digest(run):
    """从 run 记录提取二手证据 digest（judge 输入 §31）。"""
    ev = run.get("evidence_digest") or {}
    items = []
    if isinstance(ev, dict):
        facts = ev.get("facts") or {}
        for k, v in (facts.items() if isinstance(facts, dict) else []):
            items.append({"key": str(k)[:60], "value": str(v)[:200]})
    return items[:12]


def render_prompt(case, run):
    app = case["applicability"]
    scholar = _scholarly_digest(run)
    return f"""[CASE]
CATEGORY: {case['category']}
PERSONA: {case['persona']}
APPLICABILITY: TEXTUAL_GROUNDING={app['TEXTUAL_GROUNDING']}; ARGUMENT_RECONSTRUCTION={app['ARGUMENT_RECONSTRUCTION']}; INTERPRETIVE_PLURALITY={app['INTERPRETIVE_PLURALITY']}; HISTORICAL_DISCIPLINE={app['HISTORICAL_DISCIPLINE']}; LITERATURE_ORIENTATION={app['LITERATURE_ORIENTATION']}

[USER QUESTION]
{case['question']}

[PRIMARY EVIDENCE DIGEST（本回答可用的原典检索事实摘要）]
{json.dumps(scholar, ensure_ascii=False)[:1500]}

[CITATIONS（validator 已机械核验的正式引用）]
{json.dumps(run.get('citations', [])[:8], ensure_ascii=False)[:800]}

[ANSWER TO JUDGE]
{run.get('answer', '')[:9000]}"""


def judge_run(case, run):
    prompt = render_prompt(case, run)
    votes = []
    for k in range(K):
        for attempt in range(3):
            try:
                raw = _call(prompt)
                votes.append(json.loads(raw))
                break
            except Exception as e:
                time.sleep(2 * (attempt + 1))
        else:
            votes.append(None)
    valid = [v for v in votes if v]
    if not valid:
        return {"case_id": case["case_id"], "error": "all judge calls failed"}
    # 复用 O7-A 聚合语义: 维度中位数 / applicability 多数 / fatal 多数
    dims = {}
    for d in ("textual_grounding", "argument_reconstruction", "interpretive_plurality",
              "historical_discipline", "literature_orientation"):
        scores, applics = [], []
        for v in valid:
            dd = (v.get("dimensions") or {}).get(d) or {}
            s = dd.get("score")
            if isinstance(s, (int, float)):
                scores.append(float(s))
            applics.append(dd.get("applicability", "NOT_APPLICABLE"))
        applic = max(set(applics), key=applics.count)
        dims[d] = {"applicability": applic,
                   "scores": sorted(scores),
                   "median": sorted(scores)[len(scores)//2] if scores else None}
    flags = {}
    for f in ("FABRICATED_BIBLIOGRAPHY", "FABRICATED_SCHOLAR_ATTRIBUTION",
              "PRIMARY_TEXT_MISREPRESENTATION", "MAJOR_ANACHRONISM",
              "FALSE_EXACT_QUOTE", "LITERATURE_ACCESS_OVERCLAIM"):
        vs = [bool(((v.get("fatal_flags") or {}).get(f) or {}).get("value"))
              for v in valid if v.get("fatal_flags")]
        flags[f] = (sum(vs) * 2 > len(vs)) if vs else None
    return {"case_id": case["case_id"], "k": len(valid), "dims": dims,
            "fatal_flags_majority": flags,
            "answer_len": len(run.get("answer", "")),
            "published": bool(run.get("delivery", {}).get("published"))}


def main(scope):
    cases = {"CAL": CASES.CALIBRATION_CASES,
             "HOLDOUT": CASES.HOLDOUT_CASES}[scope]
    runs = {r["case_id"]: r for r in json.load(
        open(os.path.join(TMP, f"o7e_runs_{scope}.json"), encoding="utf-8"))}
    out_path = os.path.join(TMP, f"o7e_judge_{scope}.json")
    judged = []
    if os.path.exists(out_path):
        judged = json.load(open(out_path, encoding="utf-8"))
    done = {j["case_id"] for j in judged}
    for c in cases:
        if c["case_id"] in done:
            continue
        run = runs.get(c["case_id"])
        if not run:
            print(f"  skip {c['case_id']} (no run)")
            continue
        if not run.get("delivery", {}).get("published"):
            judged.append({"case_id": c["case_id"], "unpublished": True,
                           "published": False})
            continue
        r = judge_run(c, run)
        judged = [x for x in judged if x["case_id"] != c["case_id"]] + [r]
        json.dump(judged, open(out_path, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        dm = r.get("dims", {})
        print(f"  {c['case_id']}: " + " ".join(
            f"{d.split('_')[0]}={dm.get(d,{}).get('median')}" for d in dm) +
            f" fatal={[f for f,v in (r.get('fatal_flags_majority') or {}).items() if v]}",
            flush=True)
    # 汇总
    agg = aggregate(judged, cases)
    print(json.dumps(agg, ensure_ascii=False, indent=1))
    json.dump({"per_case": judged, "aggregate": agg},
              open(out_path.replace(".json", "_agg.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)


def aggregate(judged, cases):
    by_case = {c["case_id"]: c for c in cases}
    dim_scores = {}
    fatal_hits = []
    for j in judged:
        if not j.get("published"):
            fatal_hits.append(f"{j['case_id']}:UNPUBLISHED")
            continue
        for d, dv in (j.get("dims") or {}).items():
            if dv.get("applicability") == "REQUIRED" and dv.get("median") is not None:
                dim_scores.setdefault(d, []).append(dv["median"])
        for f, v in (j.get("fatal_flags_majority") or {}).items():
            if v:
                fatal_hits.append(f"{j['case_id']}:{f}")
    out = {"cases_judged": len(judged)}
    for d, xs in dim_scores.items():
        out[f"{d}_required_mean"] = round(sum(xs) / len(xs), 3)
        out[f"{d}_required_median_lt_2"] = sum(1 for x in xs if x < 2)
    all_req = [x for xs in dim_scores.values() for x in xs]
    out["APPLICABLE_DIMENSION_MEAN"] = round(sum(all_req) / max(len(all_req), 1), 3)
    out["fatal_hits"] = fatal_hits
    return out


if __name__ == "__main__":
    main(sys.argv[1])
