# -*- coding: utf-8 -*-
"""O7-A JR1 Stage-1 screening（evaluation-only; 同一冻结语义 prompt/payload/schema/labels）。

用法: python o7_jr1_screening.py <model> [thinking_disabled]
"""
import json, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))) if False else sys.path.insert(0, 'backend/tools/evaluation')
import os
sys.path.insert(0, 'backend/tools/evaluation')
import o7_scholarly_judge as J
from o7_scholarly_cases import calibration_fixtures, fixture_evidence_scope
from o7_quote_probe import probe_from_judge_input

MODEL = sys.argv[1]
DISABLE_THINKING = len(sys.argv) > 2 and sys.argv[2] == 'nothink'

SUBSET = ["C1-bad", "C3-bad", "C8-bad", "C4-bad", "C6-L1-bad", "F6-M2-bad", "F6-M4-bad",
          "C1-good", "C5-good", "C2-mid", "C6-mid", "C5-bad", "C8-good"]
EXPECTED = {"C1-bad": ["FABRICATED_BIBLIOGRAPHY"], "C3-bad": ["FABRICATED_SCHOLAR_ATTRIBUTION"],
            "C8-bad": ["PRIMARY_TEXT_MISREPRESENTATION"], "C4-bad": ["MAJOR_ANACHRONISM"],
            "C6-L1-bad": ["LITERATURE_ACCESS_OVERCLAIM"], "F6-M2-bad": ["LITERATURE_ACCESS_OVERCLAIM"],
            "F6-M4-bad": ["LITERATURE_ACCESS_OVERCLAIM"]}
NEGATIVES = ["C1-good", "C5-good", "C2-mid", "C6-mid", "C5-bad", "C8-good"]

# model 适配（transport 等价层: 仅 invocation, 语义输入等价）
import urllib.request, urllib.error
_key = None
with open('.env', encoding='utf-8') as f:
    for line in f:
        if line.strip().startswith('ZHIPU_API_KEY='):
            _key = line.split('=', 1)[1].strip().strip('"').strip("'")

def transport_call(payload):
    body = json.dumps(payload).encode()
    req = urllib.request.Request(J.JUDGE_BASE_URL, data=body, headers={
        "Content-Type": "application/json", "Authorization": "Bearer " + (_key or "")})
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.loads(r.read())["choices"][0]["message"]["content"] or ""

def call_model(prompt):
    payload = {"model": MODEL, "temperature": 0, "max_tokens": 8000,
               "response_format": {"type": "json_object"},
               "messages": [{"role": "system", "content": J.JUDGE_SYSTEM_PROMPT},
                            {"role": "user", "content": prompt}]}
    if DISABLE_THINKING:
        payload["thinking"] = {"type": "disabled"}
    return transport_call(payload)

fixtures = calibration_fixtures()
results, raw_recall, lat, fails = {}, 0, [], 0
detected = []
for fid in SUBSET:
    f = fixtures[fid]
    inp = f["judge_input"]
    pr = probe_from_judge_input(inp, fixture_evidence_scope(fid))
    votes, raws = [], []
    for k in range(3):
        t0 = time.time()
        try:
            v = J.run_judge(inp, transport=call_model, model=MODEL,
                            temperature=0 if not DISABLE_THINKING else 0)
            lat.append(time.time() - t0)
        except Exception as e:
            fails += 1
            print(f"FAIL {fid} call{k}: {str(e)[:160]}", flush=True)
            v = None
        if v is not None:
            raws.append(v)
            raised = J.raised_fatal_flags(v)
            votes.append(raised)
        time.sleep(1)
    good_raws = [r for r in raws if r is not None] or None
    if not good_raws:
        results[fid] = {"error": "all calls failed"}
        continue
    agg = J.aggregate_ensemble(good_raws, mechanical_f5=pr["mechanical_f5"],
                               evidence_scope=fixture_evidence_scope(fid))
    results[fid] = {"raised": J.raised_fatal_flags(agg), "votes": agg["vote_distribution"],
                    "review_required": agg["review_required"]}
    for fl in EXPECTED.get(fid, []):
        raw_recall += 1
        if fl in J.raised_fatal_flags(agg):
            detected.append((fid, fl))
    ff = [x for x in J.raised_fatal_flags(agg) if fid in NEGATIVES]
    if ff:
        results[fid]["false_fatal"] = ff

total = sum(len(v) for v in EXPECTED.values())
recalled = len(detected)
false_fatal = [(fid, fl) for fid in NEGATIVES for fl in results.get(fid, {}).get("false_fatal", [])]
out = {"model": MODEL, "thinking_disabled": DISABLE_THINKING,
       "seeded_assertions": total, "detected": recalled,
       "screen_recall": round(recalled / total, 3),
       "missed": [(fid, fl) for fid in EXPECTED for fl in EXPECTED[fid]
                  if (fid, fl) not in detected],
       "false_fatal": false_fatal,
       "schema_failures": fails,
       "latency_p50": sorted(lat)[len(lat)//2] if lat else None,
       "results": results}
json.dump(out, open(f'backend/tools/_tmp/o7a_jr1_screen_{MODEL.replace(".", "_")}.json',
                    'w', encoding='utf-8'), ensure_ascii=False, indent=1, default=str)
print(json.dumps({k: out[k] for k in ("model", "seeded_assertions", "detected", "screen_recall",
                                      "missed", "false_fatal", "schema_failures", "latency_p50")},
                 ensure_ascii=False, indent=1))
