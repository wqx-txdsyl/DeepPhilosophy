"""Assemble immutable RUN4 grades and evidence-backed adjudications offline."""
import hashlib,importlib.util,json,os,re
from pathlib import Path
BASE=Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))));ROOT=BASE.parent
OUT=ROOT/'docs/evidence/phiagent_benchmark_v0_1/quality_review_run4_v1_2_20261003'
spec=importlib.util.spec_from_file_location('frozen',ROOT/'docs/evidence/rubric_v1_2/validate.py');frozen=importlib.util.module_from_spec(spec);spec.loader.exec_module(frozen)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manual={x['id']:x for x in json.loads((OUT/'CODEX_ADJUDICATION.json').read_text())}
error_checks={}

def anchor(reason,answer):
 value=dict(reason) if isinstance(reason,dict) else {'reason':str(reason or '初评未提供理由'),'span':''}
 span=value.get('span') or '';value['span']=span
 if span and span not in answer:
  value['provider_span']=span
  positions=[i for i,c in enumerate(answer) if not c.isspace()];compact=''.join(answer[i] for i in positions);needle=re.sub(r'\s+','',span);at=compact.find(needle)
  if needle and at>=0:value['span']=answer[positions[at]:positions[at+len(needle)-1]+1];value['anchor_resolution']='source substring after whitespace normalization'
  else:
   value['span']='';value['span_parts']=[x.strip() for x in re.split(r'\n|……|\.\.\.',span) if len(x.strip())>=8 and x.strip() in answer];value['anchor_resolution']='no literal contiguous match; original retained, not presented as quotation'
 return value
rows=[];protocol=[]
for path in sorted((OUT/'packets').glob('*.json')):
 p=json.loads(path.read_text());key=p['id'];answer=p['target_answer'];override=manual.get(key);raw=None;initial=None
 response=OUT/'provider_responses'/path.name
 if (OUT/'format_retries'/path.name).exists():response=OUT/'format_retries'/path.name
 if answer and response.exists():
  raw=json.loads(response.read_text());assert raw['choices'][0]['finish_reason']!='length'
  try:initial=json.loads(raw['choices'][0]['message']['content'])
  except ValueError:
   assert override;protocol.append({'id':key,'issue':'invalid_initial_json','resolution':'direct Codex review; malformed original retained, no guessed fields'})
  if initial:
   assert initial['id']==key
   rating=initial['ratings'];valid=set(rating)==set(p['rating_keys']) and all(v=='U' or type(v)is int and 0<=v<=(1 if p['family']=='K' else 4) for v in rating.values())
   if not valid:
    assert override;protocol.append({'id':key,'issue':'invalid_initial_rating_scale','original':rating,'resolution':'independent binary/U adjudication; no numeric rescaling'})
   if not (OUT/'reviews'/path.name).exists():protocol.append({'id':key,'issue':'initial_strict_output_rejected','resolution':'retained raw response; extracted valid scoring fields or direct adjudication'})
 elif answer:
  assert override
  protocol.append({'id':key,'issue':'provider_402_initial_review_unavailable','resolution':'direct Codex review; no provider grade fabricated'})
 else:raise AssertionError('RUN4 should have no empty answer')
 ratings=override['ratings'] if override else initial['ratings']
 reasons=override['reasons'] if override else {k:initial['reasons'][k] for k in p['rating_keys']}
 reasons={k:anchor(v,answer) for k,v in reasons.items()}
 errors=override.get('errors',[]) if override else initial.get('errors',[])
 if key in error_checks:errors=[]
 if not override:errors=[{**x,'status':'pending'} for x in errors if isinstance(x,dict)]
 for e in errors:
  if e['status']=='confirmed':assert e['answer_span'] in answer
 row={'id':key,'case_id':key.split('-')[0],'family':p['family'],'question':p['current_question'],
  'review_level':'Codex targeted review' if override else 'model_initial_unverified',
  'ratings':ratings,'score':frozen.score(p['family'],ratings,errors),'reasons':reasons,'errors':errors,
  'initial_model_ratings':initial.get('ratings') if initial else None,
  'initial_error_allegations':initial.get('errors') if initial else [],
  'model_findings':initial.get('findings') if initial else [],'error_adjudication':error_checks.get(key),
  'packet_sha256':sha(path),'answer_sha256':hashlib.sha256(answer.encode()).hexdigest(),
  'provider_response':str(response.relative_to(ROOT)) if raw else None,'provider_response_sha256':sha(response) if raw else None,
  'review_limits':override['limits'] if override else initial.get('review_limits'),
  'answer_status':'EMPTY_FINAL_ANSWER' if not answer else 'ANSWER_PRESENT'}
 rows.append(row)
assert len(rows)==77
plan=json.loads((OUT/'PLAN.json').read_text())
for cid,digest in plan['trace_sha256'].items():assert sha(ROOT/'docs/evidence/phiagent_benchmark_v0_1/traces_run4'/f'{cid}.json')==digest
out={'status':'development_review_not_validated_quality_gate','rubric_version':'1.2','case_count':65,'turn_count':77,'independent_reviewed_turns':len(manual),'additional_error_adjudications':len(error_checks),'source_traces_unchanged':True,'formal_expert_acceptance':False,'skipped_cases':plan['skipped_cases'],'empty_answer_cases':[],'initial_provider_responses':55,'provider_402_missing_initial_reviews':22,'protocol_issues':protocol,'rows':rows}
(OUT/'SCORES.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
(OUT/'ERROR_ADJUDICATION.json').write_text(json.dumps(error_checks,ensure_ascii=False,indent=2)+'\n')
lines=['# RUN4 冻结 v1.2 逐轮评审','','65题77轮；初评返回55份（含1份非法JSON和3份K量尺错误），22轮因402未获初评。32轮Codex直接评审/复核，覆盖全部缺失初评、非法评分和固定对照题；其余45轮保留模型初评。不是人类专家验收，分数为开发暂定；评审覆盖与RUN3不同。','']
for r in rows:
 lines += [f"## {r['id']} · {r['family']} · {r['review_level']}",'',r['question'],'','|维度|等级|理由|答案片段|证据|','|---|---:|---|---|---|']
 for k,v in r['ratings'].items():
  reason=r['reasons'][k];clean=lambda x:str(x).replace('|','／').replace('\n',' ')
  lines.append('|'+ '|'.join(map(clean,[k,v,reason.get('reason'),reason.get('span'),reason.get('evidence','')]))+'|')
 if r['errors']:lines+=['',json.dumps(r['errors'],ensure_ascii=False)]
 if r['error_adjudication']:lines+=['','初评错误指控复核：'+r['error_adjudication']]
 lines+=['']
(OUT/'SCORES_AND_REASONS.md').write_text('\n'.join(lines).rstrip()+'\n')
print({'rows':len(rows),'reviewed':len(manual),'empty_answers':0,'protocol_issues':len(protocol)})
