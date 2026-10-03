"""Assemble immutable RUN6 grades and evidence-backed adjudications offline."""
import hashlib,importlib.util,json,os,re
from pathlib import Path
BASE=Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))));ROOT=BASE.parent
OUT=ROOT/'docs/evidence/phiagent_benchmark_v0_1/quality_review_run6_v1_2_20261003'
spec=importlib.util.spec_from_file_location('frozen',ROOT/'docs/evidence/rubric_v1_2/validate.py');frozen=importlib.util.module_from_spec(spec);spec.loader.exec_module(frozen)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manual={x['id']:x for x in json.loads((OUT/'CODEX_ADJUDICATION.json').read_text())}
error_checks={
'H01-T1':'初评声称未读取先事后得，实际工具3检索回执与工具9章节正文均含该句；使民如承大祭亦有回执。撤回未读取E4指控，不因此验证全部释义或改动其他等级。',
'M04-T1':'答案明确说没有帕菲特原著，另举Ehring章节并署其名，没有把章节归为帕菲特所作。引用转述与摘要一致，撤回归属混淆E4指控。'}
protocol_reasons={'J03-T3':{
'R1':{'reason':'经文与荀子、孟子各文本角色、所引原句对应实际回执；称情、性伪、权等语境相连。','span':'文貌情用，相为内外表里。','reason_source':'Codex protocol completion; initial rating unchanged'},
'R2':{'reason':'材料分别支持构成、公共主张、称情尺度、存续及权衡限制，不只列名句；来源未支撑的细部外推仍属初评限制。','span':'可推翻的推定','reason_source':'Codex protocol completion; initial rating unchanged'},
'R3':{'reason':'正文reader链接和实际阅读窗口明确，没取得的注疏不当已读；原版版面未独立核。','span':'本轮实际读到','reason_source':'Codex protocol completion; initial rating unchanged'}}}


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
  assert key in json.loads((OUT/'PLAN.json').read_text())['direct_review_ids']
 else:raise AssertionError('RUN6 should have no empty answer')
 ratings=override['ratings'] if override else initial['ratings']
 if not override and key in protocol_reasons:
  assert set(initial['ratings'])==set(p['rating_keys'])
  missing=set(p['rating_keys'])-set(initial['reasons']);assert missing==set(protocol_reasons[key])
  initial['reasons'].update(protocol_reasons[key])
  protocol.append({'id':key,'issue':'missing_R_reasons','resolution':'Codex inspected full answer and receipts, supplemented three explanations; all initial ratings unchanged'})
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
for cid,digest in plan['trace_sha256'].items():assert sha(ROOT/'docs/evidence/phiagent_benchmark_v0_1/traces_run6'/f'{cid}.json')==digest
out={'status':'development_review_not_validated_quality_gate','rubric_version':'1.2','case_count':65,'turn_count':77,'independent_reviewed_turns':len(manual),'fixed_direct_review_turns':32,'additional_protocol_direct_reviews':1,'same_manual_judge_established':False,'manual_reviewer_provenance':'Final direct review after user-requested model switch; exact historical direct judge revision not recorded','additional_error_adjudications':len(error_checks),'source_traces_unchanged':True,'formal_expert_acceptance':False,'skipped_cases':plan['skipped_cases'],'empty_answer_cases':[],'initial_provider_responses':45,'provider_402_missing_initial_reviews':0,'planned_direct_reviews':32,'protocol_issues':protocol,'rows':rows}
(OUT/'SCORES.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
(OUT/'ERROR_ADJUDICATION.json').write_text(json.dumps(error_checks,ensure_ascii=False,indent=2)+'\n')
lines=['# RUN6 冻结 v1.2 逐轮评审','','65题77轮；固定相同32轮直接复核，45轮请求相同初评指令。M03-T1原始JSON无效，增加一轮独立直接复核；J03-T3等级有效但遗漏R理由，补全理由且不改等级。另核两条错误指控。用户在本轮评审中切换模型，历史直接评审者修订未记录，不能保证同一评审模型。非专家验收，均为开发暂定分。','']
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
