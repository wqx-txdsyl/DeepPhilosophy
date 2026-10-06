from pathlib import Path
import json,hashlib,collections,statistics,datetime
ROOT=Path(__file__).resolve().parents[3];BASE=ROOT/'docs/evidence/phiagent_benchmark_v0_1';OUT=BASE/'quality_review_run4_v1_2_20261003'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
suite=json.loads((BASE/'suite.json').read_text())['cases'];issues=[];turns=[];cases=[];hashes={}
for c in suite:
 p=BASE/'traces_run4'/f'{c["id"]}.json';v=json.loads(p.read_text());hashes[p.name]=sha(p);cases.append(v)
 if not c['manual_prompt_ready']:
  assert v['status']=='SKIPPED_NOT_READY' and not v.get('turns');continue
 assert [t['question'] for t in v['turns']]==[c['prompt'],*c['follow_up_turns']]
 for t in v['turns']:
  key=f'{c["id"]}-T{t["turn"]}';turns.append((key,t))
  assert t['answer']==t['done_content'] and t['done_matches_tokens'] is True
  assert len(t['answer'])==t['answer_chars']
  assert t['status']=='DONE' and not t['stream_error']
  starts=[e for e in t['events'] if e['ev']=='tool_start'];ends=[e for e in t['events'] if e['ev']=='tool']
  assert len(starts)==len(ends)==len(t['tool_calls_full'])
  for call in t['tool_calls_full']:json.loads(call['result_full'])
  assert sum(e['ev']=='done' for e in t['events'])==1
  if not t['answer'].strip():issues.append({'id':key,'issue':'empty_final_answer','public_notes':[n.get('content') for n in t['public_notes']], 'preview_events':t.get('preview_events'),'ttft_s':t['ttft_s'],'finish_reason':t['finish_reason'],'tool_count':len(t['tool_calls_full']),'scoring':'C dimensions absent = 0; retain in 65-case denominator; notes only describe planned work.'})
for f in ['_RUN_META.json','_PREFLIGHT.json']:hashes[f]=sha(BASE/'traces_run4'/f)
freeze=json.loads((ROOT/'docs/evidence/rubric_v1_2/FREEZE_MANIFEST.json').read_text())
for f,h in freeze['files'].items():assert sha(ROOT/f)==h
calls=[c for _,t in turns for c in t['tool_calls_full']]
report={'date':'2026-10-03','case_records':len(cases),'case_statuses':dict(collections.Counter(c['status'] for c in cases)),'eligible_cases':65,'turns':len(turns),'final_answers_present':sum(bool(t['answer'].strip()) for _,t in turns),'tool_calls':len(calls),'tool_statuses':dict(collections.Counter(c['status'] for c in calls)),'answer_chars':sum(t['answer_chars'] for _,t in turns),'ttft_median_s':statistics.median(t['ttft_s'] for _,t in turns if t['ttft_s'] is not None),'trace_sha256':hashes,'issues':issues,'frozen_manifest_verified':len(freeze['files']),'actual_runtime_provenance_limitations':['Actual collector is _tmp/bench_v01_run4.py; no per-turn runtime_metadata or done.release retained.','Initial git and manifest selector are not an immutable snapshot of the 192 dirty workspace entries.','Token usage from main_model_usage was not collected.','External sources, cache and provider behavior were not frozen; this is a successive-version observation, not a strict single-factor experiment.']}
(OUT/'INTAKE_AUDIT.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ['trace_sha256','actual_runtime_provenance_limitations']},ensure_ascii=False))
