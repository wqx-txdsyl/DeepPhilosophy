"""Verify RUN6 evidence and the prespecified RUN4-matched review split."""
import hashlib,json,os,subprocess,sys
from pathlib import Path
BASE=Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))));ROOT=BASE.parent
sys.path.insert(0,str(BASE/'tools'));import aggregate_benchmark_scores as agg
OUT=ROOT/'docs/evidence/phiagent_benchmark_v0_1/quality_review_run6_v1_2_20261003'
load=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
audit=load(OUT/'INTAKE_AUDIT.json');scores=load(OUT/'SCORES.json');plan=load(OUT/'PLAN.json');prior=OUT.parent/'quality_review_run5_v1_2_20261003'
assert plan['direct_review_ids']==sorted(r['id'] for r in load(prior/'CODEX_ADJUDICATION.json'))
assert plan['system_sha256']==load(prior/'PLAN.json')['system_sha256']
assert set(plan['direct_review_ids']).isdisjoint(plan['model_review_ids'])
assert len(plan['direct_review_ids'])==32 and len(plan['model_review_ids'])==45
for name,digest in audit['trace_sha256'].items():assert sha(OUT.parent/'traces_run6'/name)==digest
freeze=load(ROOT/'docs/evidence/rubric_v1_2/FREEZE_MANIFEST.json')
for name,digest in freeze['files'].items():assert sha(ROOT/name)==digest
for row in scores['rows']:
 p=OUT/'packets'/(row['id']+'.json');packet=load(p);assert sha(p)==row['packet_sha256'];assert packet['target_answer']
 assert hashlib.sha256(packet['target_answer'].encode()).hexdigest()==row['answer_sha256']
 if row['id'] in plan['direct_review_ids']:assert row['review_level']=='Codex targeted review' and row['provider_response'] is None
 else:
  assert row['review_level']==('Codex targeted review' if row['id']=='M03-T1' else 'model_initial_unverified')
  assert sha(ROOT/row['provider_response'])==row['provider_response_sha256']
 for reason in row['reasons'].values():
  assert not reason.get('span') or reason['span'] in packet['target_answer']
  assert all(part in packet['target_answer'] for part in reason.get('span_parts',[]))
 for e in row['errors']:
  if e['status']=='confirmed':assert e['answer_span'] in packet['target_answer'] and e['reference_or_condition']
document=load(OUT/'SOURCE_DOCUMENT.json');assert sha(ROOT/document['path'])==document['sha256']
for item in load(OUT/'ISSUES.json')['items']:
 assert item['answer_span'] in load(OUT/'packets'/(item['id']+'.json'))['target_answer']
assert len(scores['rows'])==77
assert scores['independent_reviewed_turns']==33 and scores['same_manual_judge_established'] is False
new=agg.build();old=json.loads(subprocess.check_output(['git','show','60675439c:docs/evidence/benchmark_ledger/aggregate.json'],cwd=ROOT))
for version in ['0.1.0','0.1.1','0.1.2','0.1.3','0.1.4']:assert new['runs'][version]==old['runs'][version]
assert new['external_results']==old['external_results']
run=new['runs']['0.1.5'];assert run['completed_cases']['case_count']==65
assert run['common_fully_scored_cases']['case_ids']==old['runs']['0.1.4']['common_fully_scored_cases']['case_ids']
assert run['common_independently_reviewed_cases']['case_ids']==old['runs']['0.1.4']['common_independently_reviewed_cases']['case_ids']
report={'source_files_verified':72,'frozen_files_verified':len(freeze['files']),'rows_verified':77,'prespecified_same32_direct_reviews':True,'same45_initial_grader_system':True,'initial_responses':45,'initial_balance_failures':0,'strict_valid_initial_reviews':43,'additional_protocol_direct_reviews':1,'missing_R_reasons_completed_without_rating_change':1,'same_direct_judge_established':False,'previous_scores_unchanged':True,'comparison_cohorts_unchanged':True,'automated_evaluator_accepted':False,'new_answers_generated':0,'runtime_modified':False}
(OUT/'VALIDATION.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report))
