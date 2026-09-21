"""Capture paired end-to-end answers and provider traces; scores are separate."""
import argparse,json,time,uuid,urllib.request
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed

def main():
    p=argparse.ArgumentParser();p.add_argument('--endpoint',required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--cases',type=Path,default=Path(__file__).with_name('prompt_v2_cases.json'));p.add_argument('--workers',type=int,default=2)
    args=p.parse_args();cases=json.loads(args.cases.read_text());args.output.mkdir(parents=True,exist_ok=True)
    def run(case):
        folder=args.output/case['id'];folder.mkdir(exist_ok=True)
        if (folder/'summary.json').exists():return json.loads((folder/'summary.json').read_text())
        payload={'message':case['question'],'agent':'general','language':'zh','history':[],
                 'conversation_id':'evaluation-'+uuid.uuid4().hex,'message_id':uuid.uuid4().hex}
        (folder/'request.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2))
        request=urllib.request.Request(args.endpoint,data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'})
        start=time.monotonic();events=[];buffer=[];error=None
        try:
            with urllib.request.urlopen(request,timeout=600) as response,(folder/'events.jsonl').open('w') as log:
                for raw in response:
                    line=raw.decode().rstrip('\r\n')
                    if line.startswith('data:'):buffer.append(line[5:].lstrip())
                    elif not line and buffer:
                        data='\n'.join(buffer);buffer=[]
                        if data=='[DONE]':continue
                        event=json.loads(data);events.append(event)
                        log.write(json.dumps({'seconds':round(time.monotonic()-start,3),'event':event},ensure_ascii=False)+'\n');log.flush()
        except Exception as exc:error=type(exc).__name__+': '+str(exc)[:200]
        done=next((e for e in reversed(events) if e['type']=='done'),{})
        answer=done.get('content','') or ''.join(e.get('content','') for e in events if e['type']=='token')
        reasoning=''.join(e.get('content','') for e in events if e['type']=='provider_reasoning_delta')
        tools=[e for e in events if e['type']=='tool']
        summary={'id':case['id'],'question':case['question'],'complete':done.get('complete',False),
                 'seconds':round(time.monotonic()-start,3),'answer_chars':len(answer),'reasoning_chars':len(reasoning),
                 'tools':[{'name':e.get('name'),'status':e.get('status'),'args':e.get('args')} for e in tools],
                 'citations':done.get('citations',[]),'checks':case['checks'],'error':error or [e for e in events if e['type']=='error']}
        summary['configuration']=next((e for e in events if e['type']=='evaluation_metadata'),{})
        summary['validation']=done.get('validation',{})
        summary['research_discipline']=done.get('research_discipline',{})
        (folder/'answer.md').write_text(answer);(folder/'provider-reasoning.txt').write_text(reasoning)
        (folder/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
        return summary
    rows=[]
    with ThreadPoolExecutor(max_workers=max(1,min(args.workers,3))) as pool:
        for future in as_completed([pool.submit(run,c) for c in cases]):
            row=future.result();rows.append(row);print(row['id'],row['complete'],row['seconds'],'tools',len(row['tools']),flush=True)
            (args.output/'index.json').write_text(json.dumps([{k:r[k] for k in ('id','complete','seconds','answer_chars','reasoning_chars','error')} for r in rows],ensure_ascii=False,indent=2))

if __name__=='__main__':main()
