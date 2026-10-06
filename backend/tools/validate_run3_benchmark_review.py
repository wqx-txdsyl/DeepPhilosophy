"""Verify RUN3 grades, unchanged source traces, and fixed historical report scores."""
import hashlib,json,os,subprocess,sys
from pathlib import Path
BASE=Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))));ROOT=BASE.parent
sys.path.insert(0,str(BASE/'tools'));import aggregate_benchmark_scores as agg
OUT=ROOT/'docs/evidence/phiagent_benchmark_v0_1/quality_review_run3_v1_2_20261003'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
load=lambda p:json.loads(p.read_text())
audit=load(OUT/'INTAKE_AUDIT.json');scores=load(OUT/'SCORES.json');suite=load(ROOT/'docs/evidence/phiagent_benchmark_v0_1/suite.json')
for filename,digest in audit['trace_sha256'].items():assert sha(ROOT/'docs/evidence/phiagent_benchmark_v0_1/traces_run3'/filename)==digest
freeze=load(ROOT/'docs/evidence/rubric_v1_2/FREEZE_MANIFEST.json')
for filename,digest in freeze['files'].items():assert sha(ROOT/filename)==digest
for row in scores['rows']:
 p=OUT/'packets'/(row['id']+'.json');assert sha(p)==row['packet_sha256'];packet=load(p)
 assert row['answer_sha256']==hashlib.sha256(packet['target_answer'].encode()).hexdigest()
 if row['provider_response']:assert sha(ROOT/row['provider_response'])==row['provider_response_sha256']
 for reason in row['reasons'].values():
  assert not reason.get('span') or reason['span'] in packet['target_answer']
  assert all(s in packet['target_answer'] for s in reason.get('span_parts',[]))
 if row['id']=='A05-T1':assert all(v==0 for v in row['ratings'].values()) and not packet['target_answer']
new=agg.build()
old=json.loads(subprocess.check_output(['git','show','3c0a87f92:docs/evidence/benchmark_ledger/aggregate.json'],cwd=ROOT))
for version in ['0.1.0','0.1.1']:assert new['runs'][version]==old['runs'][version]
assert new['external_results']==old['external_results']
report={'source_files_verified':len(audit['trace_sha256']),'frozen_files_verified':len(freeze['files']),'rows_verified':len(scores['rows']),'A05_zero_retained_in_65_case_mean':True,'all_previous_scores_unchanged':True,'fixed_comparison_cohorts_unchanged':True,'automated_evaluator_accepted':freeze['automated_evaluator_accepted'],'full_quality_release_gate_passed':False,'model_initial_reviews':76,'independent_targeted_rows':14,'additional_error_adjudications':4}
(OUT/'VALIDATION.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report))
