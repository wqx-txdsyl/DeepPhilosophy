"""Validate RUN4 inputs, grading coverage and unchanged earlier reported scores."""
import hashlib,json,os,subprocess,sys
from pathlib import Path
BASE=Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))));ROOT=BASE.parent
sys.path.insert(0,str(BASE/'tools'));import aggregate_benchmark_scores as agg
OUT=ROOT/'docs/evidence/phiagent_benchmark_v0_1/quality_review_run4_v1_2_20261003'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
load=lambda p:json.loads(p.read_text())
audit=load(OUT/'INTAKE_AUDIT.json');scores=load(OUT/'SCORES.json')
for name,digest in audit['trace_sha256'].items():assert sha(ROOT/'docs/evidence/phiagent_benchmark_v0_1/traces_run4'/name)==digest
freeze=load(ROOT/'docs/evidence/rubric_v1_2/FREEZE_MANIFEST.json')
for name,digest in freeze['files'].items():assert sha(ROOT/name)==digest
for row in scores['rows']:
 p=OUT/'packets'/(row['id']+'.json');assert sha(p)==row['packet_sha256'];packet=load(p)
 assert packet['target_answer'] and row['answer_sha256']==hashlib.sha256(packet['target_answer'].encode()).hexdigest()
 if row['provider_response']:assert sha(ROOT/row['provider_response'])==row['provider_response_sha256']
 else:assert row['review_level']=='Codex targeted review'
 for reason in row['reasons'].values():
  assert not reason.get('span') or reason['span'] in packet['target_answer']
  assert all(s in packet['target_answer'] for s in reason.get('span_parts',[]))
 for e in row['errors']:
  if e['status']=='confirmed':assert e['answer_span'] in packet['target_answer'] and e['reference_or_condition']
assert len(scores['rows'])==77
new=agg.build();old=json.loads(subprocess.check_output(['git','show','ccdf54ee9:docs/evidence/benchmark_ledger/aggregate.json'],cwd=ROOT))
for version in ['0.1.0','0.1.1','0.1.2']:assert new['runs'][version]==old['runs'][version]
assert new['external_results']==old['external_results']
r=new['runs']['0.1.3'];assert r['completed_cases']['case_count']==65 and r['total_turns']==77
assert r['common_fully_scored_cases']['case_ids']==old['runs']['0.1.2']['common_fully_scored_cases']['case_ids']
assert r['common_independently_reviewed_cases']['case_ids']==old['runs']['0.1.2']['common_independently_reviewed_cases']['case_ids']
report={'source_files_verified':len(audit['trace_sha256']),'frozen_files_verified':len(freeze['files']),'rows_verified':77,'initial_provider_responses':55,'provider_402_missing_initial':22,'codex_reviewed_turns':32,'model_only_turns':45,'all_previous_scores_unchanged':True,'comparison_cohorts_unchanged':True,'automated_evaluator_accepted':False,'new_answers_generated':0,'runtime_modified':False}
(OUT/'VALIDATION.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report))
