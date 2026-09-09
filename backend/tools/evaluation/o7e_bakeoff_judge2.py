# -*- coding: utf-8 -*-
"""O7-E Bakeoff V2 §B: canonical academic judge——零自写合同。

唯一 judge 合同 = O7-A 冻结件（JUDGE_SYSTEM_PROMPT/build_judge_input/
render_judge_prompt/validate_verdict/DIMENSIONS/FATAL_FLAGS）。
O7-E 只固定 invocation（glm-4.6/temp0/disabled/json/k3）与 manifest applicability。
"""
import json
import os
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, "backend"))
sys.path.insert(0, os.path.join(ROOT, "backend", "tools", "evaluation"))

import o7_scholarly_judge as O7A   # canonical judge constitution（冻结）

_key = None
for line in open(os.path.join(ROOT, ".env"), encoding="utf-8"):
    if line.strip().startswith("ZHIPU_API_KEY="):
        _key = line.split("=", 1)[1].strip().strip('"').strip("'")


def _call(prompt):
    payload = {"model": "glm-4.6", "temperature": 0, "max_tokens": 4000,
               "thinking": {"type": "disabled"},
               "response_format": {"type": "json_object"},
               "messages": [{"role": "system", "content": O7A.JUDGE_SYSTEM_PROMPT},
                            {"role": "user", "content": prompt}]}
    req = urllib.request.Request(O7A.JUDGE_BASE_URL,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + (_key or "")})
    with urllib.request.urlopen(req, timeout=240) as r:
        return json.loads(r.read())["choices"][0]["message"]["content"] or ""


def _judge_evidence_parts(r):
    """PF-RP2 §0: 拆分 canonical judge 的四类正式字段。
    PRIMARY_TEXT_EVIDENCE 只含既有 run 的真实 source text（used_evidence primary
    条目）; 答案侧引文是 answer_quote 映射, 不冒充 source text; secondary 与
    access_levels 走 build_judge_input 的独立正式字段; 缺的数据保持空。"""
    ev = r.get("evidence_digest") or {}
    facts = ev.get("facts") or {}
    used = [e for e in (ev.get("used_evidence") or []) if isinstance(e, dict)]
    primary = [{"evidence_id": e.get("evidence_id"),
                "source_type": e.get("source_type"),
                "book": e.get("book"), "chapter": e.get("chapter"),
                "source_text": ((e.get("text") or e.get("snippet") or "")[:400])
                } for e in used
               if e.get("source_type") in ("primary_read", "primary", "snippet")
               and (e.get("text") or e.get("snippet"))][:10]
    qb = [e for e in (r.get("quote_bound") or [])
          if e.get("verification_state") in ("VERIFIED_EXACT", "VERIFIED_NEAR")]
    answer_quotes = [{"answer_quote": e.get("preview"),
                      "evidence_id": e.get("source_evidence_id"),
                      "state": e.get("verification_state")} for e in qb[:12]]
    primary_ev = [
        {"source": "primary_evidence_from_existing_run",
         "entries": primary},
        {"source": "answer_quote_to_evidence_mapping",
         "entries": answer_quotes},
        {"source": "read_chapters", "chapters": facts.get("read_chapters")},
    ]
    secondary = [{"book": e.get("book"), "chapter": e.get("chapter"),
                  "source_type": e.get("source_type"),
                  "evidence_id": e.get("evidence_id")}
                 for e in used if e.get("source_type") == "secondary"][:6]
    access_levels = []   # 本 run 未记录 access 状态——保持空, 不编造
    return primary_ev, secondary, access_levels


def judge_candidate(mid, runs_path=None, out_tag=None):
    runs = json.load(open(runs_path or os.path.join(
        ROOT, "backend/tools/_tmp", f"o7e_bakeoff_B_{mid.replace('.','_')}.json"),
        encoding="utf-8"))
    man = {m["case_id"]: m for m in json.load(open(os.path.join(
        ROOT, "docs/evidence/PHIAGENT_O7E_BAKEOFF_EVALUATION_MANIFEST.json"),
        encoding="utf-8"))}
    tag = out_tag or f"o7e_bakeoff_judge2_{mid.replace('.','_')}"
    out_path = os.path.join(ROOT, "backend/tools/_tmp", f"{tag}.json")
    judged = []
    if os.path.exists(out_path):
        judged = json.load(open(out_path, encoding="utf-8"))
    done = {j["case_id"] for j in judged}
    for r in runs:
        cid = r["case_id"]
        if cid in done or not r.get("delivery", {}).get("published"):
            continue
        m = man[cid]
        primary_ev, secondary, access_levels = _judge_evidence_parts(r)
        inp = O7A.build_judge_input(
            user_question=m["question"], task_category=m["task_category"],
            answer=r.get("answer", ""), agent_identity=m["agent_identity"],
            evidence_digest=json.dumps(
                {k: v for k, v in (r.get("evidence_digest") or {}).items()
                 if k != "facts"}, ensure_ascii=False)[:2000],
            primary_text_evidence=primary_ev,
            bibliographic_records=(r.get("citations") or [])[:8],
            secondary_source_records=secondary,
            access_levels=access_levels)
        prompt = O7A.render_judge_prompt(inp)
        votes = []
        for k in range(3):
            for attempt in range(3):
                try:
                    votes.append(json.loads(_call(prompt)))
                    break
                except Exception:
                    time.sleep(2 * (attempt + 1))
            else:
                votes.append(None)
        valid = [v for v in votes if v and not O7A.validate_verdict(v)]
        if not valid:
            judged.append({"case_id": cid, "error": "all judge votes invalid"})
            json.dump(judged, open(out_path, "w", encoding="utf-8"),
                      ensure_ascii=False, indent=1)
            continue
        # applicability 取 manifest 真值（judge 不猜）
        dims = {}
        required_missing = []
        for d in O7A.DIMENSIONS:
            scores = [((v.get("dimensions", {}).get(d) or {}).get("score"))
                      for v in valid]
            scores = [s for s in scores if isinstance(s, (int, float))]
            median = sorted(scores)[len(scores)//2] if scores else None
            applic = m["applicability"].get(d.upper(), "OPTIONAL")
            # D1: REQUIRED 维度无有效分 → 该 case 记 required_missing,
            # 不静默出分母、不当 0 分（聚合层置 EVALUATION_INVALID）
            if applic == "REQUIRED" and median is None:
                required_missing.append(d)
            dims[d] = {"median": median, "applicability": applic}
        fatal = set()
        for v in valid:
            for f in O7A.FATAL_FLAGS:
                if ((v.get("fatal_flags") or {}).get(f) or {}).get("value"):
                    fatal.add(f)
        judged.append({"case_id": cid, "dims": dims, "fatal": sorted(fatal),
                       "required_missing": required_missing})
        json.dump(judged, open(out_path, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        print(f"  {cid}: " + " ".join(f"{d.split('_')[0]}={dims[d]['median']}"
                                      for d in dims) + f" fatal={sorted(fatal)}",
              flush=True)
    # aggregate（PF-RP2 §0: REQUIRED 与 applicable 分开记账）
    #   required_dims: 每维 REQUIRED 中位数均值（REQUIRED_*_MEAN 用, 不含 OPTIONAL）
    #   applicable_dims / applicable_mean: numeric REQUIRED + numeric OPTIONAL
    #   （NOT_APPLICABLE 与合法 OPTIONAL null 排除）
    required_scores = {}
    applicable_scores = {}
    fatal_total = set()
    fatal_counts = {f: 0 for f in O7A.FATAL_FLAGS}
    median_lt2 = 0
    missing_required = []
    expected = len([r for r in runs if r.get("delivery", {}).get("published")])
    valid = [j for j in judged if j.get("dims")]
    missing = expected - len(valid)
    for j in valid:
        if j.get("fatal"):
            fatal_total.update(j["fatal"])
            for f in j["fatal"]:
                if f in fatal_counts:
                    fatal_counts[f] += 1
        for d, dv in j.get("dims", {}).items():
            if dv["median"] is None:
                continue
            # PF-RP3: REQUIRED_MEDIAN_LT_2 = published case × manifest REQUIRED 维
            # 中 median < 2 的数量
            if dv["applicability"] == "REQUIRED" and dv["median"] < 2:
                median_lt2 += 1
            if dv["applicability"] == "REQUIRED":
                required_scores.setdefault(d, []).append(dv["median"])
                applicable_scores.setdefault(d, []).append(dv["median"])
            elif dv["applicability"] == "OPTIONAL":
                applicable_scores.setdefault(d, []).append(dv["median"])
        for d in (j.get("required_missing") or []):
            missing_required.append({"case_id": j["case_id"], "dimension": d})
    # error case（三票全废）也算 missing
    for j in judged:
        if j.get("error"):
            missing_required.append({"case_id": j["case_id"],
                                     "dimension": "ALL_JUDGE_VOTES_INVALID"})
    evaluation_invalid = bool(missing_required) or missing > 0
    out = {"candidate": mid, "judged": len(valid),
           "JUDGE_CASES_EXPECTED": expected,
           "JUDGE_CASES_VALID": len(valid),
           "JUDGE_CASES_MISSING": max(missing, 0),
           "EVALUATION_INVALID": evaluation_invalid,
           "REQUIRED_DIMENSION_MISSING_SCORE": len(missing_required),
           "REQUIRED_DIMENSION_MEDIAN_LT_2": median_lt2,
           "FATAL_FLAG_COUNTS_BY_TYPE": fatal_counts,
           "missing_required": missing_required,
           "required_dims": {d: round(sum(xs) / len(xs), 3)
                             for d, xs in required_scores.items()},
           "applicable_dims": {d: round(sum(xs) / len(xs), 3)
                               for d, xs in applicable_scores.items()},
           "dims": {d: round(sum(xs) / len(xs), 3)
                    for d, xs in applicable_scores.items()},
           "applicable_mean": round(
               sum(x for xs in applicable_scores.values() for x in xs) /
               max(sum(len(xs) for xs in applicable_scores.values()), 1), 3),
           "fatal_flags": sorted(fatal_total)}
    json.dump(out, open(out_path.replace(".json", "_summary.json"), "w",
                        encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    judge_candidate(sys.argv[1])
