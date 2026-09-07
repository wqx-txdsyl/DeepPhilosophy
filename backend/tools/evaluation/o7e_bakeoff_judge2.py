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


def judge_candidate(mid):
    runs = json.load(open(os.path.join(
        ROOT, "backend/tools/_tmp", f"o7e_bakeoff_B_{mid.replace('.','_')}.json"),
        encoding="utf-8"))
    man = {m["case_id"]: m for m in json.load(open(os.path.join(
        ROOT, "docs/evidence/PHIAGENT_O7E_BAKEOFF_EVALUATION_MANIFEST.json"),
        encoding="utf-8"))}
    out_path = os.path.join(ROOT, "backend/tools/_tmp",
                            f"o7e_bakeoff_judge2_{mid.replace('.','_')}.json")
    judged = []
    if os.path.exists(out_path):
        judged = json.load(open(out_path, encoding="utf-8"))
    done = {j["case_id"] for j in judged}
    for r in runs:
        cid = r["case_id"]
        if cid in done or not r.get("delivery", {}).get("published"):
            continue
        m = man[cid]
        ev = r.get("evidence_digest") or {}
        facts = ev.get("facts") or {}
        primary_ev = [{"source": "read_chapters",
                       "chapters": facts.get("read_chapters")}]
        inp = O7A.build_judge_input(
            user_question=m["question"], task_category=m["task_category"],
            answer=r.get("answer", ""), agent_identity=m["agent_identity"],
            evidence_digest=json.dumps(
                {k: v for k, v in ev.items() if k != "facts"}, ensure_ascii=False)[:2000],
            primary_text_evidence=primary_ev,
            bibliographic_records=(r.get("citations") or [])[:8])
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
        for d in O7A.DIMENSIONS:
            scores = [((v.get("dimensions", {}).get(d) or {}).get("score"))
                      for v in valid]
            scores = [s for s in scores if isinstance(s, (int, float))]
            dims[d] = {"median": sorted(scores)[len(scores)//2] if scores else None,
                       "applicability": m["applicability"].get(d.upper(), "OPTIONAL")}
        fatal = set()
        for v in valid:
            for f in O7A.FATAL_FLAGS:
                if ((v.get("fatal_flags") or {}).get(f) or {}).get("value"):
                    fatal.add(f)
        judged.append({"case_id": cid, "dims": dims, "fatal": sorted(fatal)})
        json.dump(judged, open(out_path, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        print(f"  {cid}: " + " ".join(f"{d.split('_')[0]}={dims[d]['median']}"
                                      for d in dims) + f" fatal={sorted(fatal)}",
              flush=True)
    # aggregate（manifest applicability 分母）
    dim_scores = {}
    fatal_total = set()
    for j in judged:
        for d, dv in j.get("dims", {}).items():
            if dv["applicability"] == "REQUIRED" and dv["median"] is not None:
                dim_scores.setdefault(d, []).append(dv["median"])
            if j.get("fatal"):
                fatal_total.update(j["fatal"])
    out = {"candidate": mid, "judged": len([j for j in judged if j.get("dims")]),
           "dims": {d: round(sum(xs) / len(xs), 3) for d, xs in dim_scores.items()},
           "applicable_mean": round(
               sum(x for xs in dim_scores.values() for x in xs) /
               max(sum(len(xs) for xs in dim_scores.values()), 1), 3),
           "fatal_flags": sorted(fatal_total)}
    json.dump(out, open(out_path.replace(".json", "_summary.json"), "w",
                        encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    judge_candidate(sys.argv[1])
