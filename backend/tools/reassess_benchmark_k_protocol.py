"""Uniform K-family protocol clarification; criteria and original responses retained."""
import json,hashlib,os,sys,time,threading,urllib.request,urllib.error
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
BASE=Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))));sys.path.insert(0,str(BASE/'tools'))
import reassess_benchmark_blind as blind
OUT=blind.OUT;KOUT=OUT/'k_protocol_recheck'
CLARIFICATION='''\n本次输入是K类纯定位/核验任务。K1-K4是四个二元检查，不采用C/R的0-4等级锚点，也不能先评0-4再换算。
每项仅允许：1=符合对应冻结检查；0=不符合对应冻结检查；"U"=证据不足无法判断。4、3、2都是非法输出。
ratings必须且只能含K1、K2、K3、K4。每个值只能为整数0、整数1或字符串"U"。例如全部符合时是{"K1":1,"K2":1,"K3":1,"K4":1}；这个例子不预设本答卷全部符合。其余reasons/errors/findings等字段仍按前述协议完整输出。
这段仅明确冻结K量尺的输出编码，没有增加评价标准或修正待评答案。'''

def prepare():
 plan=blind.verify();KOUT.mkdir(exist_ok=True)
 for name in ['responses','reviews']:(KOUT/name).mkdir(exist_ok=True)
 ids=[pid for pid in plan['submission_order'] if blind.load(OUT/'packets'/f'{pid}.json')['family']=='K'];assert len(ids)==15
 system=(OUT/'reviewer_instructions.txt').read_text()+CLARIFICATION
 path=KOUT/'PREREGISTRATION.json'
 if path.exists():
  old=blind.load(path);assert old['packet_ids']==ids and old['system_sha256']==hashlib.sha256(system.encode()).hexdigest();return old
 (KOUT/'reviewer_instructions.txt').write_text(system)
 data={'created_at':blind.now(),'parent_preregistration_sha256':blind.sha(OUT/'PREREGISTRATION.json'),'trigger':'Protocol validation observed K values2/3/4; no scores compared or version ranking inspected before this amendment.','selection':'ALL fifteen K packets, every compared version and every selected pure-verification task, regardless of first-pass validity or grade. No numeric rescaling.','packet_ids':ids,'system_sha256':blind.sha(KOUT/'reviewer_instructions.txt'),'grader_config':plan['grader_config'],'response_selection':'First valid clarified-protocol response, at most one identical retry for invalid JSON/schema. Supersedes ALL first-pass K grades uniformly; other families retain original first-valid responses. Invalid output stays missing/U.','agent_answer_runs':0,'rubric_modified':False,'source_packets_modified':False,'limits':'Same provider configuration by task family across all versions. This is a disclosed protocol amendment, not the byte-identical original system across families.'}
 blind.save(path,data);return data

def run():
 plan=prepare();model,key,url=blind.setup_client();assert model==plan['grader_config']['model'];system=(KOUT/'reviewer_instructions.txt').read_text();stop=threading.Event();started=blind.now()
 def one(pid):
  dest=KOUT/'reviews'/f'{pid}.json';packet=blind.load(OUT/'packets'/f'{pid}.json')
  if dest.exists():return pid,'existing'
  for a in [1,2]:
   if stop.is_set():return pid,'stopped_after402'
   path=KOUT/'responses'/f'{pid}-a{a}.json';recpath=KOUT/'responses'/f'{pid}-a{a}.receipt.json';sent=blind.now()
   body={**plan['grader_config'],'messages':[{'role':'system','content':system},{'role':'user','content':json.dumps(packet,ensure_ascii=False)}]}
   if not path.exists():
    req=urllib.request.Request(url,data=json.dumps(body).encode(),headers={'Content-Type':'application/json','Authorization':'Bearer '+key})
    try:
     with urllib.request.urlopen(req,timeout=120) as r:raw=json.loads(r.read())
    except urllib.error.HTTPError as e:
     if e.code==402:stop.set()
     blind.save(recpath,{'id':pid,'attempt':a,'http_status':e.code,'status':'transport_failure','started':sent,'finished':blind.now()});return pid,'http_'+str(e.code)
    except Exception as e:
     blind.save(recpath,{'id':pid,'attempt':a,'status':'transport_failure','exception_class':type(e).__name__,'started':sent,'finished':blind.now()});return pid,'transport_failure'
    blind.save(path,raw);blind.save(recpath,{'id':pid,'attempt':a,'status':'response_received','started':sent,'finished':blind.now(),'grader_config':plan['grader_config'],'system_sha256':plan['system_sha256'],'packet_sha256':blind.sha(OUT/'packets'/f'{pid}.json'),'response_sha256':blind.sha(path),'request_sha256':hashlib.sha256(json.dumps(body).encode()).hexdigest(),'model_returned':raw.get('model'),'system_fingerprint':raw.get('system_fingerprint')})
   else:raw=blind.load(path)
   try:d=blind.parse_review(raw,packet)
   except (ValueError,KeyError,TypeError,AssertionError) as e:
    rec=blind.load(recpath);rec.update(validation='invalid_protocol',validation_error=str(e)[:150]);blind.save(recpath,rec);continue
   d.update(status='uniform_blinded_K_protocol_clarification_unverified',family='K',accepted_attempt=a,packet_sha256=blind.sha(OUT/'packets'/f'{pid}.json'),provider_response=str(path.relative_to(blind.ROOT)),provider_response_sha256=blind.sha(path),model_returned=raw.get('model'),system_fingerprint=raw.get('system_fingerprint'),usage=raw.get('usage'));blind.save(dest,d);return pid,'valid_binary'
  return pid,'invalid_after_fixed_retry'
 with ThreadPoolExecutor(max_workers=2) as pool:
  for future in as_completed([pool.submit(one,p) for p in plan['packet_ids']]):
   try:print(*future.result(),flush=True)
   except Exception as e:print('ERROR',type(e).__name__,flush=True)
 blind.save(KOUT/'RUN_META.json',{'started':started,'finished':blind.now(),'valid_reviews':len(list((KOUT/'reviews').glob('*.json'))),'stopped_after402':stop.is_set(),'answer_generation_runs':0});print('K_PROTOCOL_DONE',flush=True)

if __name__=='__main__':
 command=sys.argv[1] if len(sys.argv)>1 else 'prepare'
 if command=='prepare':print({'preregistered_K_packets':len(prepare()['packet_ids'])})
 elif command=='run':run()
 else:raise SystemExit('prepare or run')
