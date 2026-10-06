from pathlib import Path
import json,collections,re,datetime,statistics,sys
ROOT=Path(__file__).resolve().parents[3];BASE=ROOT/'docs/evidence/phiagent_benchmark_v0_1';OUT=BASE/'quality_review_run5_v1_2_20261003'
report={}
for run in [4,5]:
 folder=BASE/f'traces_run{run}';traces=[json.loads(p.read_text()) for p in folder.glob('[A-N][0-9][0-9].json')];turns=[t for c in traces for t in c.get('turns',[])];calls=[x for t in turns for x in t['tool_calls_full']];meta=json.loads((folder/'_RUN_META.json').read_text())
 partial=[];errors=collections.Counter();error_names=collections.Counter();names=collections.Counter();languages={}
 for case in traces:
  for t in case.get('turns',[]):
   for x in t['tool_calls_full']:
    if x['status']=='partial':
     d=json.loads(x['result_full']);names[x['name']]+=1
     for e in d.get('provider_errors') or []:errors[f"{e.get('provider')}:{e.get('error')}"]+=1
     partial.append({'case':case['case_id'],'turn':t['turn'],'name':x['name'],'results':len(d.get('results') or []),'provider_errors':d.get('provider_errors')})
    if x['status']=='error':error_names[x['name']]+=1
 for window in [300,1000,None]:
  ids=[]
  for c in traces:
   if not c.get('turns'):continue
   text=c['turns'][0]['provider_reasoning'][:window];latin=len(re.findall('[A-Za-z]',text));han=len(re.findall('[\u4e00-\u9fff]',text))
   if latin/(latin+han or 1)>.8:ids.append(c['case_id'])
  languages[str(window)]={'high_latin_count':len(ids),'case_ids':sorted(ids)}
 report[str(run)]={'batch_wall_minutes':(datetime.datetime.fromisoformat(meta['finished'])-datetime.datetime.fromisoformat(meta['started'])).total_seconds()/60,'case_duration_sum_minutes':sum(c.get('total_wall_s',0) for c in traces)/60,'ttft_median_s':statistics.median(t['ttft_s'] for t in turns if t['ttft_s'] is not None),'tool_count':len(calls),'partial_tool_names':dict(names),'partial_provider_error_occurrences':dict(errors),'partial_calls_with_results':sum(p['results']>0 for p in partial),'partial_cases':dict(collections.Counter(p['case'] for p in partial)),'error_tool_names':dict(error_names),'partial_calls':partial,'first_turn_language_proxy':languages,'J_turns':{c['case_id']:len(c['turns']) for c in traces if c['case_id'].startswith('J')},'I_tools':{c['case_id']:sum(len(t['tool_calls_full']) for t in c['turns']) for c in traces if c['case_id'].startswith('I')}}
report['language_measurement']='Latin/(Latin+Han)>0.8, first-turn first300/1000 characters or whole text; not formal language identification or a cause test.'
report['limits']=['No per-turn effective prompt/runtime or pinned provider revision in old collector.','Cache root dict has2 top-level keys, not2 cached papers; cache contents were not snapshotted.','Observed successive-version differences are not proof of a prompt-only causal effect.']
(OUT/'RUN_CONDITIONS_COMPARISON.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
sys.path.insert(0,str(ROOT/'backend/tools'));import aggregate_benchmark_scores as agg
rules=json.loads((ROOT/'docs/evidence/rubric_v1_2/RULES_FROZEN.json').read_text());suite=json.loads((BASE/'suite.json').read_text())['cases'];counts={c['id']:1+len(c['follow_up_turns']) for c in suite}
old={r['id']:r for r in json.loads((BASE/'quality_review_run4_v1_2_20261003/SCORES.json').read_text())['rows']};new=json.loads((OUT/'SCORES.json').read_text())['rows'];parts=collections.defaultdict(float);paired=[]
for r in new:
 a=float(agg.turn_bounds(old[r['id']],rules)[0]);b=float(agg.turn_bounds(r,rules)[0]);layer='same32_direct_reviews' if r['review_level']=='Codex targeted review' else 'same45_model_only_reviews';contribution=(b-a)/counts[r['case_id']]/65;parts[layer]+=contribution;paired.append({'id':r['id'],'review_layer':layer,'run4':a,'run5':b,'delta':b-a,'contribution_to_65_case_delta':contribution})
(OUT/'PAIRED_REVIEW_COMPARISON.json').write_text(json.dumps({'same_review_layers':True,'delta_contributions':dict(parts),'note':'Descriptive score decomposition; answer changes and evaluator variation are not separable. No causal or significance claim.','rows':paired},ensure_ascii=False,indent=2)+'\n')
print(json.dumps({r:{k:v for k,v in d.items() if k not in ['partial_calls','first_turn_language_proxy']} for r,d in report.items() if r in ['4','5']},ensure_ascii=False));print(dict(parts))
