"""Uniform blinded reassessment of existing answers; never invokes the agent.

prepare fixes sampling, anonymous mapping, inputs, grader and aggregation before
any requests. run stores every provider response, taking the first valid response
only. report creates a separate diagnostic index, not new full-suite grades.
"""
import argparse,datetime,hashlib,html,itertools,json,os,random,re,sys,time,threading,urllib.request,urllib.error
from collections import Counter
from concurrent.futures import ThreadPoolExecutor,as_completed
from fractions import Fraction
from pathlib import Path
BASE=Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))));ROOT=BASE.parent
EVIDENCE=ROOT/'docs/evidence/phiagent_benchmark_v0_1'
OUT=EVIDENCE/'blind_reassessment_20261003'
SOURCES={'0.1.1':'traces_run2','0.1.4':'traces_run5','0.1.5':'traces_run6'}
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
load=lambda p:json.loads(Path(p).read_text())
def save(p,value):Path(p).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def frozen():return load(ROOT/'docs/evidence/rubric_v1_2/RULES_FROZEN.json')
def setup_client():
 sys.path.insert(0,str(BASE));from routes.agent_llm import MODEL,API_KEY,_chat_url
 return MODEL,API_KEY,_chat_url()
def verify():
 plan=load(OUT/'PREREGISTRATION.json')
 for path,digest in plan['source_sha256'].items():assert sha(ROOT/path)==digest,path
 for path,digest in plan['frozen_files_sha256'].items():assert sha(ROOT/path)==digest,path
 for pid,digest in plan['packet_sha256'].items():assert sha(OUT/'packets'/f'{pid}.json')==digest,pid
 assert sha(OUT/'reviewer_instructions.txt')==plan['grader_system_sha256']
 assert sha(OUT/'BLIND_KEY.json')==plan['blind_key_sha256']
 return plan

def prepare():
 if (OUT/'PREREGISTRATION.json').exists():verify();print('Existing preregistration unchanged.');return
 OUT.mkdir(exist_ok=True)
 for folder in ['packets','responses','reviews']:(OUT/folder).mkdir(exist_ok=True)
 rules=frozen();cases={c['id']:c for c in load(EVIDENCE/'suite.json')['cases']}
 selection=load(EVIDENCE/'quality_review_run6_v1_2_20261003/PLAN.json')['direct_review_ids'];assert len(selection)==32
 registry=load(ROOT/'docs/evidence/benchmark_ledger/registry.json');fixed10=registry.get('comparison_cohorts',{}).get('reviewed_case_ids')
 # Obtain the registered immutable cohort without inventing a new intersection.
 if fixed10 is None:
  fixed10=load(ROOT/'docs/evidence/benchmark_ledger/aggregate.json')['runs']['0.1.5']['common_independently_reviewed_cases']['case_ids']
 assert len(fixed10)==10 and all(cid+'-T1' in selection and not cases[cid]['follow_up_turns'] for cid in fixed10)
 system=(EVIDENCE/'quality_review_run6_v1_2_20261003/reviewer_instructions.txt').read_text()
 (OUT/'reviewer_instructions.txt').write_text(system)
 model,_,url=setup_client();rng=random.Random(202610030616);groups=list(selection);rng.shuffle(groups)
 versions=list(SOURCES);perms=list(itertools.permutations(versions));rng.shuffle(perms)
 orders=(perms*5)+[perms[0],perms[0][1:]+perms[0][:1]];rng.shuffle(orders)
 key={};order=[];hashes={};packets={};positions={v:Counter() for v in versions}
 for group,version_order in zip(groups,orders):
  cid,turnpart=group.split('-T');target=int(turnpart);case=cases[cid]
  for pos,version in enumerate(version_order):
   path=EVIDENCE/SOURCES[version]/f'{cid}.json';trace=load(path);hashes[str(path.relative_to(ROOT))]=sha(path)
   previous=[];packet=None
   for i,t in enumerate(trace['turns'][:target],1):
    tools=[]
    for j,call in enumerate(t['tool_calls_full'],1):
     result=call.get('result_full')
     if isinstance(result,str):
      try:result=json.loads(result)
      except ValueError:pass
     tools.append({'tool_index':j,'name':call['name'],'args':call.get('args'),'status':call.get('status'),'result':result})
    expected=[case['prompt'],*case['follow_up_turns']][i-1];assert t['question'].strip()==expected.strip(),(version,group)
    if i==target:
     family=case['rubric_family'];keys=list(rules['K']) if family=='K' else [*rules['C'],*(rules['R'] if family=='R' else {})]
     packet={'id':'B'+rng.randbytes(6).hex(),'family':family,'rating_keys':keys,'original_question':case['prompt'],'task_required_work':case['required_work'],'current_question':t['question'],'previous_turns':previous.copy(),'target_answer':t['answer'],'tools_this_turn':tools,'citations_this_turn':t.get('citations',[])}
    previous.append({'turn':i,'question':t['question'],'answer':t['answer'],'tools':tools,'citations':t.get('citations',[])})
   assert packet and packet['target_answer'].strip();pid=packet['id'];assert pid not in key
   save(OUT/'packets'/f'{pid}.json',packet);packets[pid]=sha(OUT/'packets'/f'{pid}.json')
   key[pid]={'version':version,'round_id':group,'case_id':cid,'turn':target,'source_path':str(path.relative_to(ROOT)),'version_position':pos,'full_case_turn_count':1+len(case['follow_up_turns'])};order.append(pid);positions[version][pos]+=1
 save(OUT/'BLIND_KEY.json',key)
 freeze=load(ROOT/'docs/evidence/rubric_v1_2/FREEZE_MANIFEST.json')['files']
 freeze.update(registry['frozen_inputs'])
 config={'model':model,'temperature':0,'max_tokens':5000,'thinking':{'type':'disabled'},'response_format':{'type':'json_object'}}
 plan={'created_at':now(),'status':'preregistered_before_grading','versions':versions,'selected_rounds':selection,'selected_unique_cases':len({x.split('-')[0] for x in selection}),'fixed10_case_ids':fixed10,'answer_generation_runs':0,'request_count':96,'seed':202610030616,'submission_order':order,'version_order_counts':{v:dict(c) for v,c in positions.items()},'blinding':'Each stateless request contains no release name, run identifier, historical grades, reasoning, commentary or blind key. Actual answer/tool content retained without truncation; style or capabilities may still reveal clues.','source_sha256':hashes,'frozen_files_sha256':freeze,'packet_sha256':packets,'grader_system_sha256':sha(OUT/'reviewer_instructions.txt'),'blind_key_sha256':sha(OUT/'BLIND_KEY.json'),'grader_config':config,'grader_endpoint_host':urllib.parse.urlsplit(url).hostname,'grader_revision_limit':'Requested model alias fixed; record returned model and system_fingerprint per call. Provider weight revision may not be exposed.','response_selection':'First valid response. At most one identical-config retry for format/protocol errors, never select higher score. Transport failures remain missing. Stop queued calls after 402.','aggregation':'Diagnostic32: retain frozen relative turn weight 1/full_case_turn_count, renormalized over selected turns. This is not a 29-case complete score, nor 65/70-case suite score. Fixed10: original ten single-turn cases equal. C/R/K normalized only in separately authorized aggregate layer; U remains bounds. Dimensions retain same relative turn weights among applicable rounds.','serious_errors':'Model allegations remain pending until evidence audited; flags never silently erased or given invented numerical penalties. Original ratings remain separate from source audits.','decision_rule':'Consider one narrowly scoped v0.1.6 only if evidence audit confirms condition/motive or empirical-to-normative bridge defects recur in at least two compared versions including current0.1.5. No threshold invented from evaluator scores; no automatic promotion to0.2.0.','limits':['Selected32 are a nonrandom defect-focused cohort.','Same judge configuration reduces method variation, does not validate the previously uncalibrated judge.','Original runs have mutable sources/cache/model aliases and incomplete runtime fingerprints; no prompt-only causal claim.']}
 assert len(key)==96 and len(hashes)==87
 assert all(max(c.values())-min(c.values())<=1 for c in positions.values())
 save(OUT/'PREREGISTRATION.json',plan);verify();print({'preregistered':96,'rounds_per_version':32,'unique_cases':29,'position_counts':plan['version_order_counts'],'model':model})

def parse_review(raw,packet):
 c=raw['choices'][0];assert c.get('finish_reason')!='length','truncated grader response'
 d=json.loads(c['message']['content']);assert d['id']==packet['id'],'id mismatch';keys=set(packet['rating_keys'])
 assert set(d['ratings'])==keys,'rating keys';maximum=1 if packet['family']=='K' else 4
 assert all(v=='U' or type(v)is int and 0<=v<=maximum for v in d['ratings'].values()),'rating scale'
 assert keys<=set(d['reasons']),'reason keys'
 compact=lambda x:re.sub(r'\s+','',x)
 for k in keys:
  r=d['reasons'][k];assert isinstance(r,dict) and r.get('reason'),'reason text'
  assert isinstance(r.get('span',''),str),'span type';r['span_literal']=not r.get('span') or compact(r['span']) in compact(packet['target_answer'])
 assert isinstance(d.get('errors'),list) and isinstance(d.get('findings'),list),'findings/errors'
 for e in d['errors']:
  assert e.get('code') in frozen()['errors'] and e.get('status') in ['pending','confirmed'],'error type'
  assert e.get('answer_span') and e.get('reference_or_condition'),'error evidence'
  e['original_provider_status']=e['status'];e['status']='pending';e['span_literal']=compact(e['answer_span']) in compact(packet['target_answer'])
 return d

def run():
 plan=verify();model,key,url=setup_client();assert model==plan['grader_config']['model'],'model config changed'
 system=(OUT/'reviewer_instructions.txt').read_text();stopped=threading.Event();started=now()
 def one(pid):
  packet=load(OUT/'packets'/f'{pid}.json');dest=OUT/'reviews'/f'{pid}.json'
  if dest.exists():return pid,'existing'
  for attempt in [1,2]:
   if stopped.is_set():return pid,'not_sent_after402'
   response=OUT/'responses'/f'{pid}-a{attempt}.json';receipt=OUT/'responses'/f'{pid}-a{attempt}.receipt.json'
   body={**plan['grader_config'],'messages':[{'role':'system','content':system},{'role':'user','content':json.dumps(packet,ensure_ascii=False)}]};sent_at=now()
   if not response.exists():
    req=urllib.request.Request(url,data=json.dumps(body).encode(),headers={'Content-Type':'application/json','Authorization':'Bearer '+key})
    try:
     with urllib.request.urlopen(req,timeout=120) as r:raw=json.loads(r.read())
    except urllib.error.HTTPError as e:
     if e.code==402:stopped.set()
     save(receipt,{'id':pid,'attempt':attempt,'started':sent_at,'finished':now(),'http_status':e.code,'status':'transport_failure','agent_answer_runs':0});return pid,'http_'+str(e.code)
    except Exception as e:
     save(receipt,{'id':pid,'attempt':attempt,'started':sent_at,'finished':now(),'status':'transport_failure','exception_class':type(e).__name__,'agent_answer_runs':0});return pid,'transport_failure'
    save(response,raw);save(receipt,{'id':pid,'attempt':attempt,'started':sent_at,'finished':now(),'status':'response_received','request_sha256':hashlib.sha256(json.dumps(body).encode()).hexdigest(),'packet_sha256':plan['packet_sha256'][pid],'system_sha256':plan['grader_system_sha256'],'grader_config':plan['grader_config'],'model_returned':raw.get('model'),'system_fingerprint':raw.get('system_fingerprint'),'response_sha256':sha(response),'agent_answer_runs':0})
   else:raw=load(response)
   try:d=parse_review(raw,packet)
   except (ValueError,KeyError,AssertionError,TypeError) as e:
    rec=load(receipt);rec.update(validation='invalid_protocol',validation_error=str(e)[:180]);save(receipt,rec);continue
   d.update(status='uniform_blinded_model_initial_unverified',family=packet['family'],accepted_attempt=attempt,packet_sha256=plan['packet_sha256'][pid],provider_response=str(response.relative_to(ROOT)),provider_response_sha256=sha(response),model_returned=raw.get('model'),system_fingerprint=raw.get('system_fingerprint'),usage=raw.get('usage'));save(dest,d);return pid,'valid'
  return pid,'invalid_after_fixed_retry'
 with ThreadPoolExecutor(max_workers=2) as pool:
  work={pool.submit(one,pid):pid for pid in plan['submission_order']}
  for f in as_completed(work):
   try:print(*f.result(),flush=True)
   except Exception as e:print('ERROR',work[f],type(e).__name__,flush=True)
 save(OUT/'RUN_META.json',{'started':started,'finished':now(),'preregistration_sha256':sha(OUT/'PREREGISTRATION.json'),'reviews_valid':len(list((OUT/'reviews').glob('*.json'))),'attempt_responses':len(list((OUT/'responses').glob('*-a[12].json'))),'stopped_after402':stopped.is_set(),'new_agent_answers':0});print('GRADING_FINISHED',flush=True)

def report():
 sys.path.insert(0,str(BASE/'tools'));import aggregate_benchmark_scores as agg
 plan=verify();key=load(OUT/'BLIND_KEY.json');rules=frozen();by_version={v:[] for v in SOURCES};findings=[];protocol=[]
 for pid,item in key.items():
  packet=load(OUT/'packets'/f'{pid}.json');path=OUT/'reviews'/f'{pid}.json'
  d=load(path) if path.exists() else None
  ratings=d['ratings'] if d else dict.fromkeys(packet['rating_keys'],'U')
  row={**item,'id':item['round_id'],'blind_id':pid,'family':packet['family'],'ratings':ratings,'review':str(path.relative_to(ROOT)) if d else None,'errors':d.get('errors',[]) if d else [],'score_status':'model_unverified' if d else 'missing_no_imputation','bounds':agg.export(agg.turn_bounds({'family':packet['family'],'ratings':ratings},rules))}
  by_version[item['version']].append(row)
  if d:
   for e in d.get('errors',[]):findings.append({'blind_id':pid,'kind':'serious_error_allegation',**e})
   for f in d.get('findings',[]):
    if f.get('severity') in ['major','pending']:findings.append({'blind_id':pid,'kind':'model_finding',**f})
  if not d:protocol.append({'blind_id':pid,'issue':'no valid grade; U retained'})
 def weighted(rows,dimension=None):
  numerator=[Fraction(),Fraction()];den=Fraction()
  for r in rows:
   if dimension and dimension not in r['ratings']:continue
   w=Fraction(1,r['full_case_turn_count']);den+=w
   if dimension:
    value=r['ratings'][dimension];maxval=1 if dimension.startswith('K') else 4
    low=Fraction(0) if value=='U' else Fraction(value*100,maxval);high=Fraction(100) if value=='U' else low
   else:low,high=agg.turn_bounds(r,rules)
   numerator[0]+=w*low;numerator[1]+=w*high
  return agg.export(tuple(n/den for n in numerator)) if den else agg.export(None)
 summaries={}
 for v,rows in by_version.items():
  summaries[v]={'selected_rounds':32,'selected_unique_cases':29,'valid_grades':sum(r['score_status']=='model_unverified' for r in rows),'diagnostic32':weighted(rows),'fixed10':weighted([r for r in rows if r['case_id'] in plan['fixed10_case_ids']]),'dimensions':{k:weighted(rows,k) for layer in ['C','R','K'] for k in rules[layer]},'errors_pending':sum(len(r['errors']) for r in rows)}
 save(OUT/'RESULTS.json',{'status':'uniform_configuration_blinded_development_reassessment_not_calibrated','preregistration_sha256':sha(OUT/'PREREGISTRATION.json'),'historical_grades_modified':False,'agent_answer_runs':0,'summaries':summaries,'rows_by_version':by_version,'protocol':protocol})
 save(OUT/'MODEL_FINDINGS.json',findings)
 lines=['# 同配置匿名复评 · v0.1.1 / v0.1.4 / v0.1.5','','固定32轮来自29道题；部分多轮题只抽规定回合。诊断指数按原题回合权重加权后在此样本归一，不能充作29题完整成绩或65/70题总分。固定10题为原登记的十道单轮题。未经校准的同一模型配置，非专家验收或严格因果实验。','', '|维度 /100|v0.1.1|v0.1.4|v0.1.5|','|---|---:|---:|---:|']
 def fmt(d):return '—' if d['lower'] is None else f"{d['score']:.2f}" if d['score'] is not None else f"{d['lower']:.2f}–{d['upper']:.2f}"
 for title,field in [('32轮诊断指数','diagnostic32'),('固定10题指数','fixed10')]:lines.append('|'+title+'|'+'|'.join(fmt(summaries[v][field]) for v in SOURCES)+'|')
 for layer in ['C','R','K']:
  for k in rules[layer]:
   name=rules[layer][k]['name'] if isinstance(rules[layer][k],dict) else rules[layer][k]
   lines.append('|'+k+' '+name+'|'+'|'.join(fmt(summaries[v]['dimensions'][k]) for v in SOURCES)+'|')
 lines+=['','原始逐维量尺仍为C/60、R增加40、K四项二元；百分制仅为已授权汇总层。U只形成上下界，不填零、不取中点。严重错误指控保留待核，不能由均分抵消。','', '每版有效评分：'+', '.join(v+': '+str(summaries[v]['valid_grades'])+'/32' for v in SOURCES)+'。', '', '[计划与指纹](PREREGISTRATION.json) · [原始等级和汇总](RESULTS.json) · [模型缺陷候选](MODEL_FINDINGS.json)']
 (OUT/'COMPARISON.md').write_text('\n'.join(lines)+'\n')
 print(json.dumps({v:{k:summaries[v][k] for k in ['valid_grades','diagnostic32','fixed10','errors_pending']} for v in SOURCES},ensure_ascii=False))

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['prepare','run','report','verify']);args=p.parse_args()
 {'prepare':prepare,'run':run,'report':report,'verify':lambda:print({'verified':len(verify()['packet_sha256'])})}[args.command]()
