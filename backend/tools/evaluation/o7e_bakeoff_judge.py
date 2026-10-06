# -*- coding: utf-8 -*-
"""Bakeoff §10: 学术轴 judge——对 Stage B 已发布答案跑 glm-4.6 k3。"""
import json, os, sys, time, urllib.request
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, "backend"))
sys.path.insert(0, os.path.join(ROOT, "backend", "tools", "evaluation"))
import o7e_cases as CASES
import o7_scholarly_judge as O7A

_key = None
for line in open(os.path.join(ROOT, ".env"), encoding="utf-8"):
    if line.strip().startswith("ZHIPU_API_KEY="):
        _key = line.split("=", 1)[1].strip().strip('"').strip("'")

SYS = ("You are a scholarly quality judge for a philosophy research agent. "
       "Given user question, final answer, and evidence summary, score dimensions "
       "0-4: TEXTUAL_GROUNDING, ARGUMENT_RECONSTRUCTION, INTERPRETIVE_PLURALITY, "
       "HISTORICAL_DISCIPLINE, LITERATURE_ORIENTATION (mark NOT_APPLICABLE where "
       "genuinely inapplicable). Also flag fatal errors (fabricated bibliography/"
       "scholar attribution/primary misrepresentation/major anachronism/false exact "
       "quote/literature access overclaim). Output JSON: {\"dimensions\": {"
       "\"textual_grounding\": {\"score\": n, \"applicability\": \"REQUIRED|OPTIONAL|NOT_APPLICABLE\"}, ...}, "
       "\"fatal_flags\": {\"FABRICATED_BIBLIOGRAPHY\": {\"value\": false}, ...}}")

def call(prompt):
    payload = {"model": "glm-4.6", "temperature": 0, "max_tokens": 3000,
               "thinking": {"type": "disabled"},
               "response_format": {"type": "json_object"},
               "messages": [{"role": "system", "content": SYS},
                            {"role": "user", "content": prompt}]}
    req = urllib.request.Request(O7A.JUDGE_BASE_URL,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + (_key or "")})
    with urllib.request.urlopen(req, timeout=240) as r:
        return json.loads(r.read())["choices"][0]["message"]["content"] or ""

mid = sys.argv[1]
runs = json.load(open(os.path.join(ROOT, "backend/tools/_tmp", f"o7e_bakeoff_B_{mid.replace('.','_')}.json"), encoding="utf-8"))
pool = {p["case_id"]: p["question"] for p in json.load(open(os.path.join(ROOT, "backend/tools/_tmp/o7e_rp2_repair_pool.json"), encoding="utf-8"))}
out_path = os.path.join(ROOT, "backend/tools/_tmp", f"o7e_bakeoff_judge_{mid.replace('.','_')}.json")
judged = []
if os.path.exists(out_path):
    judged = json.load(open(out_path, encoding="utf-8"))
done = {j["case_id"] for j in judged}
for r in runs:
    cid = r["case_id"]
    if cid in done or not r.get("delivery", {}).get("published"):
        continue
    q = pool.get(cid, "")
    prompt = (f"QUESTION: {q}\n\nANSWER:\n{r.get('answer','')[:8000]}\n\n"
              f"EVIDENCE DIGEST: {json.dumps(r.get('evidence_digest') or {}, ensure_ascii=False)[:1000]}")
    votes = []
    for k in range(3):
        for attempt in range(3):
            try:
                votes.append(json.loads(call(prompt)))
                break
            except Exception:
                time.sleep(2 * (attempt + 1))
        else:
            votes.append(None)
    valid = [v for v in votes if v]
    dims = {}
    for d in ("textual_grounding", "argument_reconstruction", "interpretive_plurality",
              "historical_discipline", "literature_orientation"):
        scores = [(v.get("dimensions", {}).get(d, {}) or {}).get("score")
                  for v in valid]
        scores = [s for s in scores if isinstance(s, (int, float))]
        applics = [(v.get("dimensions", {}).get(d, {}) or {}).get("applicability", "NOT_APPLICABLE") for v in valid]
        dims[d] = {"median": sorted(scores)[len(scores)//2] if scores else None,
                   "applicability": max(set(applics), key=applics.count)}
    fatal = []
    for v in valid:
        for f, fv in (v.get("fatal_flags") or {}).items():
            if isinstance(fv, dict) and fv.get("value"):
                fatal.append(f)
    judged.append({"case_id": cid, "dims": dims, "fatal": sorted(set(fatal))})
    json.dump(judged, open(out_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"  {cid}: " + " ".join(f"{d.split('_')[0]}={dims[d]['median']}" for d in dims) + f" fatal={sorted(set(fatal))}", flush=True)
# aggregate
dim_scores = {}
fatal_total = []
for j in judged:
    for d, dv in j["dims"].items():
        if dv["applicability"] == "REQUIRED" and dv["median"] is not None:
            dim_scores.setdefault(d, []).append(dv["median"])
    fatal_total += j["fatal"]
out = {"candidate": mid, "judged": len(judged),
       "dims": {d: round(sum(xs)/len(xs), 3) for d, xs in dim_scores.items()},
       "applicable_mean": round(sum(x for xs in dim_scores.values() for x in xs) /
                                max(sum(len(xs) for xs in dim_scores.values()), 1), 3),
       "fatal_total": fatal_total}
json.dump(out, open(out_path.replace(".json", "_summary.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps(out, ensure_ascii=False))
