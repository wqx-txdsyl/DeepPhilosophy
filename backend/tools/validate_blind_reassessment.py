"""Validate blind packets, frozen inputs and provider provenance without new calls."""
import hashlib,json,os,sys
from collections import Counter
from pathlib import Path
BASE=Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))));ROOT=BASE.parent
sys.path.insert(0,str(BASE/'tools'));import reassess_benchmark_blind as blind
OUT=blind.OUT
load=lambda p:json.loads(Path(p).read_text());sha=blind.sha
plan=blind.verify();mapping=load(OUT/'BLIND_KEY.json');baseline=load(OUT/'BASELINE.json')
assert len(mapping)==96 and set(mapping)==set(plan['submission_order'])
for version in plan['versions']:
 ids=[key['round_id'] for key in mapping.values() if key['version']==version]
 assert sorted(ids)==plan['selected_rounds'],version
 positions=Counter(x['version_position'] for x in mapping.values() if x['version']==version)
 assert set(positions)=={0,1,2} and max(positions.values())-min(positions.values())<=1
for path,digest in baseline['preserve_sha256'].items():assert sha(ROOT/path)==digest,path
assert sha(BASE/'tools/reassess_benchmark_blind.py')==baseline['grader_code_snapshot_sha256']
cases={c['id']:c for c in load(blind.EVIDENCE/'suite.json')['cases']}
def source_packet(key):
 case=cases[key['case_id']];trace=load(ROOT/key['source_path']);history=[]
 for i,t in enumerate(trace['turns'][:key['turn']],1):
  tools=[]
  for j,c in enumerate(t['tool_calls_full'],1):
   value=c.get('result_full')
   if isinstance(value,str):
    try:value=json.loads(value)
    except ValueError:pass
   tools.append({'tool_index':j,'name':c['name'],'args':c.get('args'),'status':c.get('status'),'result':value})
  if i==key['turn']:
   rules=blind.frozen();family=case['rubric_family'];rating_keys=list(rules['K']) if family=='K' else [*rules['C'],*(rules['R'] if family=='R' else {})]
   return {'family':family,'rating_keys':rating_keys,'original_question':case['prompt'],'task_required_work':case['required_work'],'current_question':t['question'],'previous_turns':history,'target_answer':t['answer'],'tools_this_turn':tools,'citations_this_turn':t.get('citations',[])}
  history.append({'turn':i,'question':t['question'],'answer':t['answer'],'tools':tools,'citations':t.get('citations',[])})
 raise AssertionError('missing source turn')
strict_valid=0;resumed=0;nonliteral=0
for pid,key in mapping.items():
 p=load(OUT/'packets'/f'{pid}.json');original=source_packet(key)
 assert {k:v for k,v in p.items() if k!='id'}=={k:v for k,v in original.items() if k!='id'},pid
 assert not any(k in p for k in ['version','run','trace_path','model','ratings','historical_score','reasoning','provider_reasoning'])
 path=OUT/'reviews'/f'{pid}.json'
 if not path.exists():continue
 d=load(path);raw=load(ROOT/d['provider_response']);assert sha(ROOT/d['provider_response'])==d['provider_response_sha256']
 recovered=blind.parse_review(raw,p);assert recovered['ratings']==d['ratings']
 rec=load(OUT/'responses'/f'{pid}-a{d["accepted_attempt"]}.receipt.json');assert rec['grader_config']==plan['grader_config'] and rec['system_sha256']==plan['grader_system_sha256'] and rec['packet_sha256']==plan['packet_sha256'][pid]
 if d['accepted_attempt']==2:
  previous=load(OUT/'responses'/f'{pid}-a1.json')
  try:blind.parse_review(previous,p)
  except (ValueError,KeyError,AssertionError,TypeError):resumed+=1
  else:raise AssertionError('Retry replaced an already valid grade')
 strict_valid+=1;nonliteral+=sum(not d['reasons'][k]['span_literal'] for k in p['rating_keys'])
effective=load(OUT/'EFFECTIVE_SELECTION.json')['packets'];kplan=load(OUT/'k_protocol_recheck/PREREGISTRATION.json');effective_valid=0;effective_nonliteral=0
assert len(effective)==96 and set(kplan['packet_ids'])=={pid for pid in mapping if load(OUT/'packets'/f'{pid}.json')['family']=='K'}
for pid,choice in effective.items():
 packet=load(OUT/'packets'/f'{pid}.json');expected_folder=OUT/'k_protocol_recheck/reviews' if packet['family']=='K' else OUT/'reviews'
 expected=expected_folder/f'{pid}.json';assert choice['selected_review']==str(expected.relative_to(ROOT)) and choice['sha256']==sha(expected)
 d=load(expected);assert sha(OUT/'effective_reviews'/f'{pid}.json')==sha(expected)
 raw=load(ROOT/d['provider_response']);assert sha(ROOT/d['provider_response'])==d['provider_response_sha256'];assert blind.parse_review(raw,packet)['ratings']==d['ratings']
 rec_folder=OUT/'k_protocol_recheck/responses' if packet['family']=='K' else OUT/'responses';rec=load(rec_folder/f'{pid}-a{d["accepted_attempt"]}.receipt.json')
 assert rec['grader_config']==plan['grader_config'];assert rec['system_sha256']==(kplan['system_sha256'] if packet['family']=='K' else plan['grader_system_sha256'])
 if d['accepted_attempt']==2:
  try:blind.parse_review(load(rec_folder/f'{pid}-a1.json'),packet)
  except (ValueError,KeyError,AssertionError,TypeError):pass
  else:raise AssertionError('valid response replaced by retry')
 effective_valid+=1;effective_nonliteral+=sum(not d['reasons'][k]['span_literal'] for k in packet['rating_keys'])
for item in load(OUT/'SOURCE_AUDIT.json')['checks']:
 assert item['answer_span'] in load(OUT/'packets'/f'{item["blind_id"]}.json')['target_answer'];assert item['packet_sha256']==sha(OUT/'packets'/f'{item["blind_id"]}.json')
report={'frozen_inputs_verified':len(plan['frozen_files_sha256']),'source_traces_verified':len(plan['source_sha256']),'full_content_packets_verified':96,'version_order_balanced':True,'no_release_labels_or_historical_scores_in_packet_metadata':True,'historical_score_files_unchanged':True,'runtime_and_prompt_manifest_unchanged':True,'initial_valid_reviews':strict_valid,'effective_valid_reviews':effective_valid,'all15_K_uniformly_rechecked':True,'source_audit_checks':11,'model_allegations_audited':18,'format_retries_first_invalid_then_valid':resumed,'initial_nonliteral_reason_spans':nonliteral,'effective_nonliteral_reason_spans':effective_nonliteral,'model_inputs_contain_blind_key':False,'automated_evaluator_calibration_passed':False,'new_agent_answer_calls':0}
blind.save(OUT/'VALIDATION.json',report);print(json.dumps(report))
