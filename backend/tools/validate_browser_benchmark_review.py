"""Validate frozen browser evidence, compatible capture schemas and score layers."""
import datetime,hashlib,json,os,subprocess,sys
from pathlib import Path
BASE=Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))));ROOT=BASE.parent
sys.path.insert(0,str(BASE/'tools'));import aggregate_benchmark_scores as aggregate
OUT=ROOT/'docs/evidence/phiagent_benchmark_v0_1/browser_review_v1_2_20261002'
SOURCE=ROOT/'docs/evidence/phiagent_benchmark_v0_1/browser_run1_20261002'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
load=lambda p:json.loads(Path(p).read_text())
suite=load(ROOT/'docs/evidence/phiagent_benchmark_v0_1/suite.json');eligible={c['id']:c for c in suite['cases'] if c['manual_prompt_ready']}
intake=load(OUT/'INTAKE.json');index=load(OUT/'INDEX.json');by_id={(r['platform'],r['case_id'],r['turn']):r for r in index}
report={'validated_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'suite_and_rubric_unchanged':True,'original_browser_records_unchanged':True,'platforms':{},'grade_scale_and_evidence_hashes_valid':True}
freeze=load(ROOT/'docs/evidence/rubric_v1_2/FREEZE_MANIFEST.json')
for filename,digest in freeze['files'].items():
 assert sha(ROOT/filename)==digest, filename
report['frozen_manifest_files_verified']=len(freeze['files'])
report['automated_evaluator_accepted']=freeze['automated_evaluator_accepted']
for platform in ['deepseek','doubao']:
 counts={'cases':0,'turns':0,'thought_text_present':0,'preferred_think_text':0,'legacy_visible_markdown_thought':0,'no_exposed_thought':[],
         'preferred_completed_at':0,'legacy_completion_observed_at':0,'completion_timestamp_missing':[], 'question_mismatches':0,'J_conversation_changes':0,'judged_turns':0,'anchor_repairs':0}
 scores=load(OUT/platform/'SCORES.json');rows={r['id']:r for r in scores['rows']}
 assert len(rows)==77
 for cid,case in eligible.items():
  path=OUT/'source'/platform/(cid+'.json');assert sha(path)==sha(SOURCE/platform/path.name)==intake['platforms'][platform]['records'][cid]
  trace=load(path);counts['cases']+=1;questions=[case['prompt'],*case['follow_up_turns']];assert len(trace['turns'])==len(questions)
  urls=[]
  for n,turn in enumerate(trace['turns'],1):
   counts['turns']+=1;key=f'{cid}-T{n}';assert turn['question'].strip()==questions[n-1].strip();assert turn['answer'].strip()
   urls.append(turn['conversation_url']);assert 'local_' not in urls[-1] and urls[-1].startswith('https://')
   thought=turn.get('think_text')
   legacy=[x.get('text','') for x in turn.get('visible_markdown',[]) if isinstance(x,dict) and x.get('is_answer') is False and x.get('text')]
   if thought:counts['preferred_think_text']+=1
   elif legacy:counts['legacy_visible_markdown_thought']+=1
   if thought or legacy:counts['thought_text_present']+=1
   else:counts['no_exposed_thought'].append(key)
   if turn.get('completed_at'):counts['preferred_completed_at']+=1
   elif turn.get('completion_observed_at'):counts['legacy_completion_observed_at']+=1
   else:counts['completion_timestamp_missing'].append(key)
   row=rows[key];item=by_id[(platform,cid,n)];assert row['answer_sha256']==hashlib.sha256(turn['answer'].encode()).hexdigest()
   assert row['source_sha256']==sha(path) and row['packet_sha256']==sha(OUT/'packets'/f'{item["id"]}.json')
   assert row['provider_response_sha256']==sha(ROOT/row['provider_response'])
   aggregate.turn_bounds(row,aggregate.json.loads((ROOT/'docs/evidence/rubric_v1_2/RULES_FROZEN.json').read_text()))
   for reason in row['reasons'].values():
    assert not reason.get('span') or reason['span'] in turn['answer']
    assert all(s in turn['answer'] for s in reason.get('span_parts',[]))
    counts['anchor_repairs']+=bool(reason.get('anchor_resolution'))
   for error in row['errors']:
    if error['status']=='confirmed':assert error['answer_span'] in turn['answer']
   counts['judged_turns']+=1
  if cid.startswith('J'):assert len(set(urls))==1
 report['platforms'][platform]=counts
# Correct the preliminary preferred-field-only audit; retain its original copy.
initial=OUT/'INTAKE_INITIAL_FIELD_CHECK.json'
if not initial.exists():initial.write_bytes((OUT/'INTAKE.json').read_bytes())
for platform,counts in report['platforms'].items():
 info=intake['platforms'][platform]
 info['initial_preferred_field_diagnostics']={'missing_thinking':info.get('missing_thinking',[]),'missing_completed_at':info.get('missing_completed_at',[])} if 'initial_preferred_field_diagnostics' not in info else info['initial_preferred_field_diagnostics']
 info['missing_thinking']=counts['no_exposed_thought'];info['missing_completed_at']=counts['completion_timestamp_missing']
 info['compatible_field_audit']=counts
 info['status']='65 cases / 77 turns complete; legacy capture fields recognized. Timing and tool-execution scope remain limited.'
intake['audit_correction']='Early 7 DeepSeek thought records exist in visible_markdown and 2 completion observations in completion_observed_at. Initial absence report was a schema-compatibility error; answers/grades unchanged.'
(OUT/'INTAKE.json').write_text(json.dumps(intake,ensure_ascii=False,indent=2)+'\n')
# Frozen inputs are verified by aggregate.build; update only the intake manifest hash.
registry=load(aggregate.REGISTRY)
for entry in registry['external_baselines']:
 if entry.get('surface')=='official_web_chat':entry['intake_sha256']=sha(OUT/'INTAKE.json')
aggregate.REGISTRY.write_text(json.dumps(registry,ensure_ascii=False,indent=2)+'\n')
data=aggregate.build()
old=json.loads(subprocess.check_output(['git','show','HEAD:docs/evidence/benchmark_ledger/aggregate.json'],cwd=ROOT))
assert old['runs']==data['runs']
chat='chatgpt-work-sol61-high-20261002'
for key in ['completed_cases','common_fully_scored_cases','common_independently_reviewed_cases','case_bounds']:
 assert old['external_results'][chat][key]==data['external_results'][chat][key]
report['previous_phiagent_and_chatgpt_scores_unchanged']=True
report['frozen_inputs_checked']=len(registry['frozen_inputs'])
report['C5_recheck_turns']=len(load(OUT/'EXPRESSION_RECHECK.json'));assert report['C5_recheck_turns']==144
report['targeted_Codex_turns']=len(load(OUT/'CODEX_ADJUDICATION.json'));assert report['targeted_Codex_turns']==19
(OUT/'VALIDATION.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False))
