"""Freeze imported browser answers, then grade with the existing frozen rubric.

No agent/browser answer generation. Source files and existing reviews are untouched.
"""
import argparse,datetime,hashlib,json,random,re,shutil,sys,time,urllib.request
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
ROOT=Path(__file__).resolve().parents[3]
BASE=ROOT/'docs/evidence/phiagent_benchmark_v0_1'
SOURCE=BASE/'browser_run1_20261002'
OUT=BASE/'browser_review_v1_2_20261002'
RULEFILE=ROOT/'docs/evidence/rubric_v1_2/RULES_FROZEN.json'
sys.path.insert(0,str(ROOT/'backend'))
from routes.agent_llm import API_KEY,MODEL,_chat_url
rules=json.loads(RULEFILE.read_text());suite=json.loads((BASE/'suite.json').read_text())
parser=argparse.ArgumentParser();parser.add_argument('--prepare-only',action='store_true');parser.add_argument('--ids',nargs='*');args=parser.parse_args()
for folder in ['source','packets','reviews','provider_responses','failures']:(OUT/folder).mkdir(parents=True,exist_ok=True)
# Preserve the established judge instructions exactly, with a browser-evidence
# addendum distinguishing citation widgets from actual search/read transcripts.
prior=(ROOT/'backend/tools/_tmp/review_live_run2_20261002.py').read_text()
start=prior.index("SYSTEM='''")+len("SYSTEM='''");end=prior.index("'''+json.dumps(rules",start)
SYSTEM=prior[start:end]+json.dumps(rules,ensure_ascii=False)+'''
本批次是托管聊天产品采集，没有可注入的本地工具、书库或秘塔。不能假装它有这些能力，也不能因此免除明确研究任务；如实拒绝不可达的任务可正确区分状态。未知执行事实用U，不因没有操作日志就定造假。
当前材料包含回答内的来源链接、少量可见网页操作迹象；它们不等于实际读过全文。某些captured_search_flag=false与正文出现的“搜索/参考资料”等相矛盾，标志没捕获不能证明没联网，给出的链接也不能单独证明实际全文阅读。回答中的来源数、程序执行或本库检索声明若无证据，应保留未知或pending，不凭记忆核验实际执行。
若仅给书名/段号、思想标签或来源列表，而没有题目要求的可读原文/版本/真实研究与方法，缺失是可判断的不足，不都填U；也不得以大量链接抵销释义与论证缺口。
正文采集有时连带界面“搜索X关键词/参考Y资料”标记、编号或折叠摘要。这些界面附带字符不等于模型自己的论证，也不因网页文字拼接和citation控件丢换行给表达维度额外扣分。严重错误需精确引用本轮原句；不要对合理不同立场或不会暴露的思考流评分。
'''
SYSTEM_SHA=hashlib.sha256(SYSTEM.encode()).hexdigest()
manifest={'imported_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'rules_sha256':hashlib.sha256(RULEFILE.read_bytes()).hexdigest(),'suite_sha256':hashlib.sha256((BASE/'suite.json').read_bytes()).hexdigest(),'judge_requested':MODEL,'judge_instructions_sha256':SYSTEM_SHA,'source_unmodified':True,'raw_thinking_used_in_grades':False,'platforms':{},'blinding':'Product names, chat URLs, mode labels and native thinking excluded from judge packets. Source URLs/style may still hint at a platform. Not an expert or fully blind comparison.','aggregation':'Existing case-turn mean, then case macro mean; original scales/U/errors unchanged; frozen historical cohorts retained.'}
jobs=[];token_index=[]
for platform in ['deepseek','doubao']:
 copied=OUT/'source'/platform;copied.mkdir(exist_ok=True)
 report={'cases':0,'turns':0,'missing_thinking':[],'missing_completed_at':[],'records':{},'raw_link_records':0,'unique_links_within_turn':0,'case_conversations':{},'search_flag_conflicts':[]}
 for case in suite['cases']:
  if not case['manual_prompt_ready']:continue
  filename=case['id']+'.json';src=SOURCE/platform/filename;raw=src.read_bytes();digest=hashlib.sha256(raw).hexdigest();dest=copied/filename
  if dest.exists() and dest.read_bytes()!=raw:raise ValueError('Archived browser source changed: '+str(src))
  if not dest.exists():dest.write_bytes(raw)
  trace=json.loads(raw);assert trace['case_id']==case['id'] and trace['status']=='COMPLETED'
  turns=trace['turns'];questions=[case['prompt'],*case['follow_up_turns']]
  assert len(turns)==len(questions)
  report['cases']+=1;report['records'][case['id']]=digest;urls=[];previous=[]
  for turn_idx,turn in enumerate(turns,1):
   assert turn['question'].strip()==questions[turn_idx-1].strip(),(platform,case['id'],turn_idx)
   answer=turn.get('answer');assert isinstance(answer,str) and answer.strip()
   url=turn.get('conversation_url','');assert url.startswith('https://') and 'local_' not in url
   urls.append(url);report['turns']+=1
   ident=f'{case["id"]}-T{turn_idx}'
   if not turn.get('think_text'):report['missing_thinking'].append(ident)
   if not turn.get('completed_at'):report['missing_completed_at'].append(ident)
   search=turn.get('web_search') or {};links=turn.get('links') or search.get('citations') or []
   report['raw_link_records']+=len(links);report['unique_links_within_turn']+=len({l.get('href') for l in links if isinstance(l,dict) and l.get('href')})
   if search.get('triggered') is False and (links or re.search('搜索.{0,15}关键词|参考.{0,8}资料',answer)):
    report['search_flag_conflicts'].append(ident)
   anon=hashlib.sha256((platform+':'+ident).encode()).hexdigest()[:16]
   family=case['rubric_family'];keys=list(rules['K']) if family=='K' else list(rules['C'])+(list(rules['R']) if family=='R' else [])
   evidence={'citation_widgets':links,'captured_search_flag':search.get('triggered'),'completion_evidence':turn.get('completion_evidence'),'scope':'Visible UI capture only. No independent read/search tool receipts.'}
   packet={'id':anon,'family':family,'rating_keys':keys,'original_question':case['prompt'],'task_required_work':case['required_work'],'current_question':turn['question'],'previous_turns':list(previous),'target_answer':answer,'tools_this_turn':[],'browser_evidence':evidence}
   # completion descriptions could identify the product; use only factual UI
   # observations, retaining the original description in the source archive.
   packet['browser_evidence']['completion_evidence']=re.sub(r'deepseek|doubao|豆包|深度思考','[界面]',str(evidence['completion_evidence']),flags=re.I)
   packet_path=OUT/'packets'/f'{anon}.json';encoded=json.dumps(packet,ensure_ascii=False,indent=2)+'\n'
   if packet_path.exists() and packet_path.read_text()!=encoded:raise ValueError('Review packet changed: '+anon)
   packet_path.write_text(encoded)
   jobs.append(packet);token_index.append({'id':anon,'platform':platform,'case_id':case['id'],'turn':turn_idx,'question':turn['question'],'answer_sha256':hashlib.sha256(answer.encode()).hexdigest(),'source_sha256':digest})
   previous.append({'turn':turn_idx,'question':turn['question'],'answer':answer,'browser_evidence':packet['browser_evidence']})
  if case['id'].startswith('J'):assert len(set(urls))==1,(platform,case['id'],'changed chat')
  report['case_conversations'][case['id']]=urls[0]
 for meta_name in ['STATUS.json']:
  src=SOURCE/platform/meta_name;dest=copied/meta_name
  if dest.exists() and dest.read_bytes()!=src.read_bytes():raise ValueError('Status changed after intake')
  if not dest.exists():shutil.copy2(src,dest)
 report['mode']=json.loads((SOURCE/platform/'STATUS.json').read_text()).get('mode')
 report['status']='65 cases / 77 turns structurally complete; missing observation fields recorded, not inferred'
 manifest['platforms'][platform]=report
assert len(jobs)==154
for name in ['PLAN.json','BROWSER_RUN1_DEEPSEEK_DOUBAO_ANSWERS.md']:
 src=SOURCE/name
 if src.exists():
  dest=OUT/'source'/name
  if dest.exists() and dest.read_bytes()!=src.read_bytes():raise ValueError('Run document changed')
  if not dest.exists():shutil.copy2(src,dest)
if (OUT/'INTAKE.json').exists():
 manifest['imported_at']=json.loads((OUT/'INTAKE.json').read_text())['imported_at']
(OUT/'INTAKE.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
(OUT/'INDEX.json').write_text(json.dumps(token_index,ensure_ascii=False,indent=2)+'\n')
(OUT/'reviewer_instructions.txt').write_text(SYSTEM)
print('INTAKE 65 cases / 77 turns each, 154 judge packets; no question/URL context mismatch.',flush=True)
if args.prepare_only:sys.exit(0)
if args.ids:jobs=[p for p in jobs if p['id'] in args.ids]
random.Random(20261002).shuffle(jobs)


def run(packet):
 name=packet['id'];dest=OUT/'reviews'/f'{name}.json'
 if dest.exists():return name,'existing'
 existing=[int(f.stem.rsplit('attempt',1)[-1]) for f in (OUT/'provider_responses').glob(name+'.attempt*.json')]
 offset=max(existing,default=0)
 for attempt in range(offset+1,offset+4):
  started=time.monotonic();extra='' if attempt==1 else '\n先前输出格式无效。严格按JSON要求，所有等级使用本题允许的整数或U，片段必须逐字摘录当前target_answer。不要改写片段。'
  typed = '\n当前family=K，所有K项只准0、1或字符串U，没有2/3/4。逐项判定是否满足：满足1，不满足0，无法核实U；不报告部分正确等级，也不把之前输出除以4。reasons中四个键都必须是包含reason/span/evidence的对象，不能为null。' if packet['family']=='K' else ''
  body={'model':MODEL,'messages':[{'role':'system','content':SYSTEM+typed+extra},{'role':'user','content':json.dumps(packet,ensure_ascii=False)}],
   'temperature':0,'max_tokens':5000,'thinking':{'type':'disabled'},'response_format':{'type':'json_object'}}
  req=urllib.request.Request(_chat_url(),data=json.dumps(body).encode(),headers={'Content-Type':'application/json','Authorization':'Bearer '+API_KEY})
  try:
   with urllib.request.urlopen(req,timeout=120) as r:response=json.loads(r.read())
   (OUT/'provider_responses'/f'{name}.attempt{attempt}.json').write_text(json.dumps(response,ensure_ascii=False,indent=2)+'\n')
   choice=response['choices'][0]
   if choice.get('finish_reason')!='stop':raise ValueError('provider did not finish normally')
   review=json.loads(choice['message']['content']);assert review['id']==name and set(review['ratings'])==set(packet['rating_keys'])
   assert all(v=='U' or type(v)is int and 0<=v<=(1 if packet['family']=='K' else 4) for v in review['ratings'].values())
   assert set(review['reasons'])==set(packet['rating_keys'])
   assert isinstance(review.get('errors'),list) and isinstance(review.get('findings'),list)
   assert isinstance(review.get('review_limits'),list) and isinstance(review.get('environment_effect'),str)
   for reason in review['reasons'].values():
    assert reason.get('reason');span=reason.get('span','');assert isinstance(span,str) and (not span or span in packet['target_answer'])
   for finding in review.get('errors',[]):
    assert finding['code'] in rules['errors'] and finding['status'] in ['confirmed','pending']
    assert finding.get('answer_span') in packet['target_answer'] and finding.get('reference_or_condition')
   for finding in review.get('findings',[]):
    span=finding.get('answer_span','');assert isinstance(span,str) and(not span or span in packet['target_answer'])
   review.update(family=packet['family'],model_returned=response.get('model'),seconds=round(time.monotonic()-started,2),usage=response.get('usage'),
     packet_sha256=hashlib.sha256((OUT/'packets'/f'{name}.json').read_bytes()).hexdigest(),status='anonymous_model_initial_review',instructions_sha256=SYSTEM_SHA,effective_instructions_sha256=hashlib.sha256((SYSTEM+typed+extra).encode()).hexdigest())
   dest.write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n');return name,review['ratings']
  except Exception as e:
   # Do not print credentials or raw HTTP response bodies.
   (OUT/'failures'/f'{name}.attempt{attempt}.json').write_text(json.dumps({'error_type':type(e).__name__,'status_code':getattr(e,'code',None),'format_failure':not isinstance(e,urllib.error.HTTPError)},ensure_ascii=False)+'\n')
   if isinstance(e,urllib.error.HTTPError):return name,'PROVIDER_ERROR_'+str(e.code)
 return name,'FORMAT_PENDING'

with ThreadPoolExecutor(max_workers=2) as pool:
 work={pool.submit(run,p):p['id'] for p in jobs}
 for f in as_completed(work):
  try:print(*f.result(),flush=True)
  except Exception as e:print('ERROR',work[f],type(e).__name__,flush=True)
print('REVIEW LOOP COMPLETE',flush=True)
