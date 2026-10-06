from pathlib import Path
import json,collections,re,datetime,statistics
ROOT=Path(__file__).resolve().parents[3];BASE=ROOT/'docs/evidence/phiagent_benchmark_v0_1';OUT=BASE/'quality_review_run4_v1_2_20261003'
report={}
for run in [3,4]:
 folder=BASE/f'traces_run{run}';traces=[json.loads(p.read_text()) for p in folder.glob('[A-N][0-9][0-9].json')];turns=[t for c in traces for t in c.get('turns',[])];calls=[x for t in turns for x in t['tool_calls_full']]
 partial=[];provider_errors=collections.Counter();names=collections.Counter();languages=[]
 for case in traces:
  if case.get('turns'):
   text=case['turns'][0].get('provider_reasoning','');latin=len(re.findall('[A-Za-z]',text));han=len(re.findall('[\u4e00-\u9fff]',text));ratio=latin/(latin+han) if latin+han else 0
   languages.append({'case':case['case_id'],'latin_ratio':round(ratio,4),'high_latin':ratio>.8})
  for t in case.get('turns',[]):
   for x in t['tool_calls_full']:
    if x['status']=='partial':
     d=json.loads(x['result_full']);errs=d.get('provider_errors') or [];names[x['name']]+=1
     for e in errs:provider_errors[f"{e.get('provider')}:{e.get('error')}"]+=1
     partial.append({'case':case['case_id'],'turn':t['turn'],'name':x['name'],'providers':d.get('providers_queried'),'result_count':len(d.get('results') or []),'errors':errs})
 meta=json.loads((folder/'_RUN_META.json').read_text());wall=(datetime.datetime.fromisoformat(meta['finished'])-datetime.datetime.fromisoformat(meta['started'])).total_seconds()/60
 report[str(run)]={'case_duration_sum_minutes':sum(c.get('total_wall_s',0) for c in traces)/60,'batch_wall_minutes':wall,'tool_calls':len(calls),'partial_tool_names':dict(names),'partial_provider_error_occurrences':dict(provider_errors),'partial_calls_with_results':sum(x['result_count']>0 for x in partial),'partial_cases':dict(collections.Counter(x['case'] for x in partial)),'partial_calls':partial,'first_turn_language_proxy':languages,'high_latin_first_turns':sum(x['high_latin'] for x in languages),'ttft_median_s':statistics.median(t['ttft_s'] for t in turns if t['ttft_s'] is not None)}
report['language_measurement']='Heuristic: latin letters / (latin letters + Han characters) > 0.8 in the entire first-turn provider_reasoning; not a language detector, token count, or causal test.'
report['causal_limit']='Chinese prompt template and differing observed reasoning language cannot distinguish prompt effect, sampling variance, context, or provider changes. No model revision fingerprint was captured.'
for run in [3,4]:
 prefixes={}
 for n in [300,1000]:
  ids=[]
  for f in (BASE/f'traces_run{run}').glob('[A-N][0-9][0-9].json'):
   trace=json.loads(f.read_text());ts=trace.get('turns',[])
   if ts:
    text=ts[0]['provider_reasoning'][:n];latin=len(re.findall('[A-Za-z]',text));han=len(re.findall('[\u4e00-\u9fff]',text))
    if latin/(latin+han or 1)>.8:ids.append(trace['case_id'])
  prefixes[str(n)]={'high_latin_count':len(ids),'case_ids':sorted(ids)}
 report[str(run)]['first_turn_prefix_language_proxy']=prefixes
report['language_interpretation']='45/65 is reproducible for RUN4 first 300 characters (>80% Latin among Latin+Han); RUN3 same rule gives38/65. Entire first-turn text gives30/65 vs18/65. This is a script heuristic, not a verified full-language classification or evidence of vendor drift.'
(OUT/'RUN_CONDITIONS_COMPARISON.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:{x:y for x,y in v.items() if x not in ['partial_calls','first_turn_language_proxy']} for k,v in report.items() if k in ['3','4']},ensure_ascii=False))
