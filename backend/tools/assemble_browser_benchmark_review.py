"""Build reportable rows from preserved provider responses, no score imputation."""
import json,sys,hashlib,importlib.util,re,os
from pathlib import Path
BACKEND=Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))));ROOT=BACKEND.parent;BASE=ROOT/'docs/evidence/phiagent_benchmark_v0_1';OUT=BASE/'browser_review_v1_2_20261002'
spec=importlib.util.spec_from_file_location('frozen',ROOT/'docs/evidence/rubric_v1_2/validate.py');frozen=importlib.util.module_from_spec(spec);spec.loader.exec_module(frozen)
index=json.loads((OUT/'INDEX.json').read_text());suite={c['id']:c for c in json.loads((BASE/'suite.json').read_text())['cases']}

def repair_anchor(reason, answer):
 reason=dict(reason);span=reason.get('span')
 if isinstance(span,str) and (not span or span in answer):return reason
 reason['provider_span']=span
 # Whitespace-only variants are mapped back to the actual source substring.
 positions=[i for i,c in enumerate(answer) if not c.isspace()]
 compact=''.join(answer[i] for i in positions)
 needle=re.sub(r'\s+','',span or '')
 pos=compact.find(needle) if needle else -1
 if pos>=0:
  reason['span']=answer[positions[pos]:positions[pos+len(needle)-1]+1]
  reason['anchor_resolution']='literal source range; whitespace normalization only'
 else:
  parts=[part.strip() for part in re.split(r'\n|……|\.\.\.',span or '') if len(part.strip())>=8 and part.strip() in answer]
  if parts:
   reason['span_parts']=parts;reason['span']=max(parts,key=len)
   reason['anchor_resolution']='exact source fragments retained separately; provider ellipsis/join preserved in provider_span'
  else:
   # This is a missing/global criterion, not a quotation. Never invent a span.
   reason['span']='';reason['anchor_resolution']='provider span not found; rationale refers to whole answer/condition, no literal quote asserted'
 reason['span_literal']=True
 return reason

recovered=[];rows=[]
for item in index:
 packet=json.loads((OUT/'packets'/f'{item["id"]}.json').read_text());keys=packet['rating_keys'];chosen=None
 files=sorted((OUT/'provider_responses').glob(item['id']+'.attempt*.json'),key=lambda f:int(f.stem.rsplit('attempt',1)[-1]))
 for path in reversed(files):
  try:
   raw=json.loads(path.read_text());r=json.loads(raw['choices'][0]['message']['content'])
   if raw['choices'][0]['finish_reason']!='stop' or r['id']!=item['id'] or set(r['ratings'])!=set(keys):continue
   if not all(v=='U' or type(v)is int and 0<=v<=(1 if packet['family']=='K' else 4) for v in r['ratings'].values()):continue
   if not all(isinstance(r.get('reasons',{}).get(k),dict) and r['reasons'][k].get('reason') for k in keys):continue
   chosen=(path,raw,r);break
  except Exception:continue
 if not chosen:raise ValueError('Unscorable '+item['id'])
 path,raw,r=chosen;answer=packet['target_answer'];notes=[]
 reasons={k:dict(r['reasons'][k]) for k in keys}
 extra_reason_keys=sorted(set(r['reasons'])-set(keys))
 if extra_reason_keys:notes.append({'kind':'extra_reason_fields_ignored_in_score','fields':extra_reason_keys})
 for key,reason in reasons.items():
  span=reason.get('span');reason['span_literal']=isinstance(span,str) and(not span or span in answer)
  if not reason['span_literal']:notes.append({'kind':'evidence_anchor_needs_review','dimension':key,'span':span})
 errors=[]
 for e in r.get('errors') or []:
  if not isinstance(e,dict) or e.get('code') not in frozen.RULES['errors'] or e.get('status') not in {'pending','confirmed'} or not e.get('answer_span') or not e.get('reference_or_condition'):
   notes.append({'kind':'unusable_serious_error_record','record':e});continue
  e=dict(e);e['span_literal']=e['answer_span'] in answer
  if not e['span_literal']:
   e['provider_status']=e['status'];e['status']='pending';notes.append({'kind':'unlocated_serious_error_anchor','span':e['answer_span']})
  errors.append(e)
 findings=[]
 for f in r.get('findings') or []:
  if not isinstance(f,dict):continue
  f=dict(f);span=f.get('answer_span');f['span_literal']=isinstance(span,str) and(not span or span in answer)
  if not f['span_literal']:notes.append({'kind':'finding_anchor_needs_review','span':span})
  findings.append(f)
 row={'id':f'{item["case_id"]}-T{item["turn"]}','case_id':item['case_id'],'family':packet['family'],'question':item['question'],
   'review_level':'anonymous_model_initial_review','reviewer':raw.get('model'),'ratings':r['ratings'],'reasons':reasons,'errors':errors,'findings':findings,
   'score':frozen.score(packet['family'],r['ratings'],errors),'answer_sha256':item['answer_sha256'],'source_sha256':item['source_sha256'],
   'anonymous_packet_id':item['id'],'packet_sha256':hashlib.sha256((OUT/'packets'/f'{item["id"]}.json').read_bytes()).hexdigest(),
   'provider_response':str(path.relative_to(ROOT)),'provider_response_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
   'environment_effect':r.get('environment_effect'),'strength':r.get('strength'),'review_limits':r.get('review_limits'),'schema_notes':notes,
   'original_read_search_execution':'partial browser observations; citation widgets are not full execution receipts'}
 rows.append((item['platform'],row))
 if not(OUT/'reviews'/f'{item["id"]}.json').exists():recovered.append({'platform':item['platform'],'id':row['id'],'source':path.name,'notes':notes,'ratings_changed':False})
# Codex overrides are a separate source-evidenced layer; initial rows immutable.
overrides_path=OUT/'CODEX_ADJUDICATION.json';overrides=json.loads(overrides_path.read_text()) if overrides_path.exists() else []
for platform in ['deepseek','doubao']:
 folder=OUT/platform;folder.mkdir(exist_ok=True)
 initial=[r for p,r in rows if p==platform]
 (folder/'INITIAL_SCORES.json').write_text(json.dumps({'platform':platform,'rows':initial},ensure_ascii=False,indent=2)+'\n')
 final=[]
 expression={(r['platform'],r['id']):r for r in json.loads((OUT/'EXPRESSION_RECHECK.json').read_text())} if (OUT/'EXPRESSION_RECHECK.json').exists() else {}
 for source in initial:
  row=dict(source)
  if (platform,row['id']) in expression:
   e=expression[(platform,row['id'])]
   row['ratings']={**row['ratings'],'C5':e['rating']}
   row['reasons']={**row['reasons'],'C5':{'reason':e['reason'],'span':e['span'],'span_literal':e['span_literal'],'evidence':e['source']}}
   row['expression_recheck']=e
   row['score']=frozen.score(row['family'],row['ratings'],row['errors'])
  for o in overrides:
   if o['platform']!=platform or o['id']!=row['id']:continue
   ratings={**row['ratings'],**o['ratings']};reasons={**row['reasons'],**o['reasons']}
   errors=o.get('errors',row['errors'])
   row.update(ratings=ratings,reasons=reasons,errors=errors,review_level='Codex targeted review',adjudication=o)
   row['score']=frozen.score(row['family'],ratings,errors)
  if (platform,row['id']) in expression:
   e=expression[(platform,row['id'])]
   row['ratings']={**row['ratings'],'C5':e['rating']}
   row['reasons']={**row['reasons'],'C5':{'reason':e['reason'],'span':e['span'],'span_literal':e['span_literal'],'evidence':e['source']}}
   row['score']=frozen.score(row['family'],row['ratings'],row['errors'])
  target=json.loads((OUT/'packets'/f"{row['anonymous_packet_id']}.json").read_text())['target_answer']
  row['reasons']={k:repair_anchor(v,target) for k,v in row['reasons'].items()}
  final.append(row)
 result={'status':'provisional_browser_text_quality_review','rubric_version':'1.2','platform':platform,'case_count':65,'turn_count':77,'document_reviewed_turns':77,
   'model_initial_reviewed_turns':77,'codex_targeted_reviewed_turns':sum(r['review_level']=='Codex targeted review' for r in final),
   'formal_expert_acceptance':False,'rows':final}
 assert len(final)==77
 (folder/'SCORES.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 lines=['# '+('DeepSeek' if platform=='deepseek' else '豆包')+' 浏览器答卷开发评审','冻结v1.2；匿名模型全文初评 + Codex指定题核验。非专家验收，不把引用控件当原始阅读回执。']
 for row in final:
  lines += ['## '+row['id'],row['question'],'原量表：'+json.dumps(row['score']['display'],ensure_ascii=False),'|维度|等级|理由|','|---|---:|---|']
  lines += [f"|{k}|{v}|{row['reasons'][k]['reason'].replace(chr(10),' ')}|" for k,v in row['ratings'].items()]
  if row['errors']:lines += ['严重错误记录：'+json.dumps(row['errors'],ensure_ascii=False)]
  if row['schema_notes']:lines += ['附加格式/片段问题：'+str(len(row['schema_notes']))+'项，见SCORES.json；不宣称所有片段已人工核验。']
  lines.append('')
 (folder/'REVIEW.md').write_text('\n\n'.join(lines[:2])+'\n\n'+'\n'.join(lines[2:])+'\n')
(OUT/'FORMAT_RECOVERY.json').write_text(json.dumps({'raw_provider_files_unchanged':True,'ratings_imputed_or_rescaled':False,'recoverable_records':recovered,'total':len(recovered)},ensure_ascii=False,indent=2)+'\n')
print('assembled 154 rows; format recoveries',len(recovered),'; no ratings converted')
