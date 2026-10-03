"""Seal development scoring record R1; never edits rubric, answers or old grades.

Primary single-number comparison uses the same60 completed C/R cases for all
subjects. Five pure-verification cases remain a separate evidence record; their
unverifiable execution assertions are not imputed. Five fault-fixture cases are
unrun. This is a frozen development snapshot, not evaluator calibration.
"""
import argparse,copy,hashlib,json,os,sys
from collections import Counter
from pathlib import Path
BASE=Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))));ROOT=BASE.parent
sys.path.insert(0,str(BASE/'tools'));import aggregate_benchmark_scores as agg
OUT=ROOT/'docs/evidence/benchmark_ledger/frozen_r1_20261003'
sha=agg.sha
load=lambda p:json.loads(Path(p).read_text())
def save(p,d):Path(p).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def assemble():
 reg=load(OUT/'REGISTRY_SNAPSHOT.json' if (OUT/'REGISTRY_SNAPSHOT.json').exists() else agg.REGISTRY);rules=load(ROOT/reg['rubric']);suite=load(ROOT/reg['suite'])['cases']
 primary=[c['id'] for c in suite if c['manual_prompt_ready'] and c['rubric_family'] in ['C','R']]
 verification=[c['id'] for c in suite if c['manual_prompt_ready'] and c['rubric_family']=='K'];unrun=[c['id'] for c in suite if not c['manual_prompt_ready']]
 assert len(primary)==60 and len(verification)==len(unrun)==5
 adjudication={'subject':'phiagent-0.1.0','id':'D04-T1','ratings_changed':{'K1':{'from':'U','to':1}},'reason':'K1核验结论与给定证据一致：原段与Bekker页栏行已在tool5实际正文核到；原纸书排版未核属于K2范围问题，原K2=0保留，不能把该不确定性再当K1未知。','source_packet':'docs/evidence/phiagent_benchmark_v0_1/quality_review_v1_2_20261002/packets/D04-T1.json','answer_span':'他1157a15们的关系就终止了','historical_file_modified':False}
 packet=load(ROOT/adjudication['source_packet']);assert adjudication['answer_span'] in packet['target_answer'];t=next(x for x in packet['tools_this_turn'] if x['tool_index']==5);assert adjudication['answer_span'] in t['result']['text']
 inputs={**reg['frozen_inputs'],adjudication['source_packet']:sha(ROOT/adjudication['source_packet'])};subjects=[]
 for e in [*reg['versions'],*reg['external_baselines']]:
  assert e.get('review');path=ROOT/e['review'];assert sha(path)==e['review_sha256']
  raw=load(path);rows=copy.deepcopy(raw['rows']);sid='phiagent-'+e['version'] if 'version' in e else e['id'];inputs[e['review']]=sha(path)
  if sid==adjudication['subject']:
   r=next(r for r in rows if r['id']==adjudication['id']);assert r['ratings']['K1']=='U'
   r['source_K1_reason_before_adjudication']=copy.deepcopy(r.get('reasons',{}).get('K1'));r['source_score_before_adjudication']=copy.deepcopy(r.get('score'))
   r['ratings']['K1']=1;r['final_record_adjudication']=adjudication
   r.setdefault('reasons',{})['K1']={'reason':adjudication['reason'],'span':adjudication['answer_span'],'evidence':'D04-T1 packet tool5 get_chapter e574c8e7f515 chapter8'}
   import importlib.util
   spec=importlib.util.spec_from_file_location('frozen_arithmetic',ROOT/'docs/evidence/rubric_v1_2/validate.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
   r['score']=module.score('K',r['ratings'],r.get('errors',[]))
  result=agg.summarize(rows,suite,rules);main=agg.cohort(result,set(primary));assert main['score'] is not None
  selected=[r for r in rows if r['case_id'] in primary];assert len(selected)==72 and all('U' not in r['ratings'].values() for r in selected)
  dimensions={}
  for layer in ['C','R']:
   for key in rules[layer]:
    bycase={}
    for r in selected:
     if key in r['ratings']:bycase.setdefault(r['case_id'],[]).append(r['ratings'][key])
    from fractions import Fraction
    value=sum(sum(Fraction(x,4)*100 for x in values)/len(values) for values in bycase.values())/len(bycase)
    dimensions[key]={'score':float(value),'applicable_cases':len(bycase)}
  krows=[r for r in rows if r['case_id'] in verification];known=sum('U' not in r['ratings'].values() for r in krows)
  subjects.append({'id':sid,'name':'PhiAgent' if 'version' in e else e.get('display_name',e['name']),'label':'v'+e['version'] if 'version' in e else ('Work · '+e['model_snapshot']+' · '+e['mode'] if e.get('surface')=='Work' else e['model_snapshot']+' · '+e['mode']),'kind':'phiagent' if 'version' in e else 'external','source_review':e['review'],'source_review_sha256':sha(path),'review_condition':e.get('review_method') or raw.get('status','existing_development_review'),'reviewed_primary_turns':sum(r.get('review_level') in agg.REVIEWED for r in selected),'primary':main,'dimensions':dimensions,'primary_serious_error_records':dict(Counter(x['status'] for r in selected for x in r.get('errors',[]))),'verification':{'status':'complete' if known==5 else 'evidence_incomplete_not_imputed','complete_cases':known,'case_count':5,'rows':krows},'rows':rows})
 freeze=load(ROOT/'docs/evidence/rubric_v1_2/FREEZE_MANIFEST.json')['files'];inputs.update(freeze)
 record={'record_id':'R1-20261003','status':'frozen_development_scoring_record','scoring_rubric':'1.2','benchmark_suite':'0.1','primary_label':'统一60题总分','primary_scope':'Same60 complete C/R cases from original frozen70-case suite; this is explicitly a subset, never a full65/70-case score.','primary_case_ids':primary,'primary_turn_count':72,'primary_weighting':'Each case equal, all specified turns averaged within case; frozen C/60 and R/100 ratios. No U in primary. Empty A05 RUN3 retained as zero.','verification_case_ids':verification,'unrun_fixture_case_ids':unrun,'source_grades_preserved':True,'new_answer_runs':0,'automated_evaluator_calibrated':False,'quality_acceptance_claim':False,'review_limit':'Mixed development review methods retained. Freeze locks the record, not truth or causal/model ranking validity.','rejected_reassessment':'docs/evidence/phiagent_benchmark_v0_1/blind_reassessment_20261003/VERDICT.json','future_update_rule':'New evidence/review must produce a new named record with reasons; never silently overwrite R1 or original source grades.','adjudications':[adjudication],'subjects':subjects}
 return record,inputs

def verify():
 manifest=load(OUT/'FREEZE_MANIFEST.json')
 for p,h in manifest['source_files_sha256'].items():assert sha(ROOT/p)==h,p
 for p,h in manifest['record_files_sha256'].items():assert sha(OUT/p)==h,p
 record,_=assemble();assert record==load(OUT/'SCORES.json'),'frozen record not reproducible'
 print({'record':record['record_id'],'subjects':len(record['subjects']),'primary_cases':60,'primary_turns_per_subject':72,'source_files_verified':len(manifest['source_files_sha256']),'no_primary_U':True,'historical_scores_modified':False,'full70_complete':False,'evaluator_calibration_claimed':False})

def create():
 if (OUT/'FREEZE_MANIFEST.json').exists():verify();return
 OUT.mkdir(exist_ok=True);save(OUT/'REGISTRY_SNAPSHOT.json',load(agg.REGISTRY));record,inputs=assemble();save(OUT/'SCORES.json',record);save(OUT/'ADJUDICATIONS.json',record['adjudications'])
 lines=['# 冻结开发评审记录 R1','','唯一主成绩：原冻结70题中的同一60道分析与研究题，72轮／对象。5道纯核验题单列，5道故障fixture未测。不把未知项置零，不把未测题冒充完成。','', '|对象|统一60题总分 /100|','|---|---:|']
 for s in record['subjects']:lines.append(f"|{s['name']} {s['label']}|{s['primary']['score']:.2f}|")
 lines+=['','冻结评分记录，未宣称评分器校准通过或正式学术验收。评审方法、模型与工具条件仍有差异；适合追踪当前答卷表现，不是受控模型能力排行榜。旧65题、64题、10题记录只留档，不在主表并列。','', '## 纯原典核验待核说明','','|对象|评分确定题数|未知项|','|---|---:|---|']
 for s in record['subjects']:
  unknown=[r['id']+': '+','.join(k for k,v in r['ratings'].items() if v=='U') for r in s['verification']['rows'] if 'U' in r['ratings'].values()]
  lines.append(f"|{s['name']} {s['label']}|{s['verification']['complete_cases']}/5|{'；'.join(unknown) or '无'}|")
 lines+=['','PhiAgent v0.1.0 D04的K1从U核定为1：真实tool5已提供所引段落及坐标；未核原版排印仍保留K2=0。原评分不回写，更正只存在R1快照。其余历史执行无法回溯的项保持U；冻结的是当前证据状态，未伪称核验完成。','', '完整题号、逐轮等级、误差标记、来源hash在[SCORES.json](SCORES.json)。冻结校验见[FREEZE_MANIFEST.json](FREEZE_MANIFEST.json)。新增证据须另建R2等修订记录，不覆盖R1。']
 (OUT/'SUMMARY.md').write_text('\n'.join(lines)+'\n')
 save(OUT/'FREEZE_MANIFEST.json',{'record_id':record['record_id'],'source_files_sha256':inputs,'record_files_sha256':{n:sha(OUT/n) for n in ['SCORES.json','ADJUDICATIONS.json','SUMMARY.md','REGISTRY_SNAPSHOT.json']},'frozen_rules_modified':False,'historical_source_grades_modified':False,'permitted_future_change':'New explicit revision record only; never edit these frozen files.'});verify()

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['create','verify']);args=p.parse_args();{'create':create,'verify':verify}[args.command]()
