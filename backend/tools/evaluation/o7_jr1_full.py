# -*- coding: utf-8 -*-
"""O7-A JR1 Stage-2 + anti-luck gate（evaluation-only; model invocation adapter only）。"""
import json, sys, time
sys.path.insert(0, 'backend/tools/evaluation')
import o7_scholarly_judge as J
from o7_scholarly_cases import calibration_fixtures, expected_fatal_flags, probe_fixtures, fixture_evidence_scope
from o7_quote_probe import probe_from_judge_input

MODEL = sys.argv[1] if len(sys.argv) > 1 else 'glm-4.6'

import urllib.request
_key = None
with open('.env', encoding='utf-8') as f:
    for line in f:
        if line.strip().startswith('ZHIPU_API_KEY='):
            _key = line.split('=', 1)[1].strip().strip('"').strip("'")

def call_model(prompt):
    payload = {"model": MODEL, "temperature": 0, "max_tokens": 8000,
               "thinking": {"type": "disabled"},
               "response_format": {"type": "json_object"},
               "messages": [{"role": "system", "content": J.JUDGE_SYSTEM_PROMPT},
                            {"role": "user", "content": prompt}]}
    body = json.dumps(payload).encode()
    req = urllib.request.Request(J.JUDGE_BASE_URL, data=body, headers={
        "Content-Type": "application/json", "Authorization": "Bearer " + (_key or "")})
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.loads(r.read())["choices"][0]["message"]["content"] or ""

fixtures = calibration_fixtures()
ensembles = {}
for ens in ('A', 'B'):
    aggs = {}
    for fid, f in sorted(fixtures.items()):
        raws = [J.run_judge(f['judge_input'], transport=call_model, model=MODEL,
                            temperature=0) for _ in range(3)]
        scope = fixture_evidence_scope(fid)
        pr = probe_from_judge_input(f['judge_input'], scope)
        agg = J.aggregate_ensemble(raws, mechanical_f5=pr['mechanical_f5'], evidence_scope=scope)
        agg['quote_probe'] = pr
        aggs[fid] = agg
        print(f'ok {ens} {fid}', flush=True)
    ensembles[ens] = aggs
    json.dump({'ensembles': ensembles}, open('backend/tools/_tmp/o7a_jr1_full_partial.json',
               'w', encoding='utf-8'), ensure_ascii=False, default=str)

neg = [k for k, f in fixtures.items() if not expected_fatal_flags().get(k)]
res = {}
for ens in ('A', 'B'):
    groups = {**ensembles[ens],
              '__good__': [k for k, f in fixtures.items() if f['tier'] == 'GOOD'],
              '__mid__': [k for k, f in fixtures.items() if f['tier'] == 'MID'],
              '__bad__': [k for k, f in fixtures.items() if f['tier'] == 'BAD']}
    res[ens] = J.calibration_gate(groups, expected_fatal_flags(), negative_pool=neg)
stab = J.stability_compare(ensembles['A'], ensembles['B'])

# ── Anti-luck gate（§11）: kill cases + 2 clean negatives, 额外 k3 ──
KILL = ["C1-bad", "C3-bad", "C8-bad", "C4-bad", "C6-L1-bad", "F6-M2-bad", "F6-M4-bad",
        "C1-good", "C5-good"]
KILL_EXPECT = {"C1-bad": ["FABRICATED_BIBLIOGRAPHY"], "C3-bad": ["FABRICATED_SCHOLAR_ATTRIBUTION"],
               "C8-bad": ["PRIMARY_TEXT_MISREPRESENTATION"], "C4-bad": ["MAJOR_ANACHRONISM"],
               "C6-L1-bad": ["LITERATURE_ACCESS_OVERCLAIM"], "F6-M2-bad": ["LITERATURE_ACCESS_OVERCLAIM"],
               "F6-M4-bad": ["LITERATURE_ACCESS_OVERCLAIM"]}
aluck, detected = {}, 0
for fid in KILL:
    f = fixtures[fid]
    raws = [J.run_judge(f['judge_input'], transport=call_model, model=MODEL,
                        temperature=0) for _ in range(3)]
    scope = fixture_evidence_scope(fid)
    pr = probe_from_judge_input(f['judge_input'], scope)
    agg = J.aggregate_ensemble(raws, mechanical_f5=pr['mechanical_f5'], evidence_scope=scope)
    raised = set(J.raised_fatal_flags(agg))
    aluck[fid] = sorted(raised)
    for fl in KILL_EXPECT.get(fid, []):
        if fl in raised:
            detected += 1
    if fid in ("C1-good", "C5-good") and raised:
        aluck[fid + '_FALSE_FATAL'] = sorted(raised)
aluck_recall = detected / 7
aluck_false = [k for k in aluck if k.endswith('_FALSE_FATAL')]

out = {'model': MODEL, 'gate_A': res['A'], 'gate_B': res['B'], 'stability': stab,
       'anti_luck': {'recall': aluck_recall, 'detected': detected, 'detail': aluck,
                     'false_fatal_fixtures': aluck_false},
       'ensembles': ensembles}
json.dump(out, open('backend/tools/_tmp/o7a_jr1_full_glm46.json', 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1, default=str)
print(json.dumps({'gate_A': {k: v for k, v in res['A'].items() if k != 'missed_fatal'},
                  'gate_B': {k: v for k, v in res['B'].items() if k != 'missed_fatal'},
                  'missed_A': res['A']['missed_fatal'], 'missed_B': res['B']['missed_fatal'],
                  'stability': {k: v for k, v in stab.items() if k != 'dimension_diff_le1_rate_detail'},
                  'anti_luck': {'recall': aluck_recall, 'false_fatal_fixtures': aluck_false,
                                'detail': aluck}}, ensure_ascii=False, indent=1))
