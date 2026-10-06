"""Assemble immutable RUN3 grades and evidence-backed adjudications offline."""
import hashlib,importlib.util,json,os,re
from pathlib import Path
BASE=Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))));ROOT=BASE.parent
OUT=ROOT/'docs/evidence/phiagent_benchmark_v0_1/quality_review_run3_v1_2_20261003'
spec=importlib.util.spec_from_file_location('frozen',ROOT/'docs/evidence/rubric_v1_2/validate.py');frozen=importlib.util.module_from_spec(spec);spec.loader.exec_module(frozen)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manual={x['id']:x for x in json.loads((OUT/'CODEX_ADJUDICATION.json').read_text())}
error_checks={
 'B03-T1':'原指控自身承认两次已读来源支持核心事实；未逐字核法院文书不等于捏造读取。日期仍需独立核验，保留为来源可靠性限制，不判E4。',
 'C05-T1':'工具9前3000字符中，§307出现在109、§308在190字符；原指控称未覆盖是读错回执。所指各节实际返回，不以整章未读否定目标段上下文。',
 'J04-T3':'get_chapter工具16实际读到“一切变化都按照因果连结的规律而发生”，此前verify_quote未命中少“而”的不同句。人工读取原文可支持更正，不要求必须由verify_quote命中。',
 'M05-T1':'答案明确“开头的正文”，工具回执也是开头片段；原指控承认一致却臆测读者会当全文，不成立。',
}
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
 if answer:
  raw=json.loads(response.read_text());assert raw['choices'][0]['finish_reason']!='length'
  initial=json.loads(raw['choices'][0]['message']['content']);assert initial['id']==key
  rating=initial['ratings'];valid=set(rating)==set(p['rating_keys']) and all(v=='U' or type(v)is int and 0<=v<=(1 if p['family']=='K' else 4) for v in rating.values())
  if not valid:
   assert override;protocol.append({'id':key,'issue':'invalid_initial_rating_scale','original':rating,'resolution':'independent binary/U adjudication; no numeric rescaling'})
  if not (OUT/'reviews'/path.name).exists():protocol.append({'id':key,'issue':'initial_strict_output_rejected','resolution':'retained raw response; extracted only valid scoring fields, or independent adjudication'})
 else:assert override and all(x==0 for x in override['ratings'].values())
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
for cid,digest in plan['trace_sha256'].items():assert sha(ROOT/'docs/evidence/phiagent_benchmark_v0_1/traces_run3'/f'{cid}.json')==digest
out={'status':'development_review_not_validated_quality_gate','rubric_version':'1.2','case_count':65,'turn_count':77,'independent_reviewed_turns':len(manual),'additional_error_adjudications':len(error_checks),'source_traces_unchanged':True,'formal_expert_acceptance':False,'skipped_cases':plan['skipped_cases'],'empty_answer_cases':['A05'],'protocol_issues':protocol,'rows':rows}
(OUT/'SCORES.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
(OUT/'ERROR_ADJUDICATION.json').write_text(json.dumps(error_checks,ensure_ascii=False,indent=2)+'\n')
lines=['# RUN3 冻结 v1.2 逐轮评审','','65题77轮；76轮模型初评，A05空回答直接按缺失0级记录。14轮Codex完整定向复核，另4轮仅复核错误指控。不是人类专家验收；初评模型未校准，分数为开发暂定。','']
for r in rows:
 lines += [f"## {r['id']} · {r['family']} · {r['review_level']}",'',r['question'],'','|维度|等级|理由|答案片段|证据|','|---|---:|---|---|---|']
 for k,v in r['ratings'].items():
  reason=r['reasons'][k];clean=lambda x:str(x).replace('|','／').replace('\n',' ')
  lines.append('|'+ '|'.join(map(clean,[k,v,reason.get('reason'),reason.get('span'),reason.get('evidence','')]))+'|')
 if r['errors']:lines+=['',json.dumps(r['errors'],ensure_ascii=False)]
 if r['error_adjudication']:lines+=['','初评错误指控复核：'+r['error_adjudication']]
 lines+=['']
(OUT/'SCORES_AND_REASONS.md').write_text('\n'.join(lines).rstrip()+'\n')
print({'rows':len(rows),'reviewed':len(manual),'empty_answer_scored_zero':True,'protocol_issues':len(protocol)})
