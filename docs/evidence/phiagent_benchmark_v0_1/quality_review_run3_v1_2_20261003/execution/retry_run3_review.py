from pathlib import Path
import sys,json,urllib.request
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'backend'))
from routes.agent_llm import API_KEY,MODEL,_chat_url
OUT=ROOT/'docs/evidence/phiagent_benchmark_v0_1/quality_review_run3_v1_2_20261003';folder=OUT/'format_retries';folder.mkdir(exist_ok=True)
p=json.loads((OUT/'packets/C03-T1.json').read_text());system=(OUT/'reviewer_instructions.txt').read_text()
body={'model':MODEL,'messages':[{'role':'system','content':system},{'role':'user','content':json.dumps(p,ensure_ascii=False)}],'temperature':0,'max_tokens':6000,'thinking':{'type':'disabled'},'response_format':{'type':'json_object'}}
req=urllib.request.Request(_chat_url(),data=json.dumps(body).encode(),headers={'Content-Type':'application/json','Authorization':'Bearer '+API_KEY})
with urllib.request.urlopen(req,timeout=120) as response:r=json.load(response)
(folder/'C03-T1.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');parsed=json.loads(r['choices'][0]['message']['content']);print('retried',parsed['id'],parsed['ratings'])
