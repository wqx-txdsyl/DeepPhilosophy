"""Finalize a uniformly selected reassessment; historical scores are never overwritten."""
import hashlib,html,json,os,sys,shutil
from pathlib import Path
from fractions import Fraction
BASE=Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))));ROOT=BASE.parent
sys.path.insert(0,str(BASE/'tools'))
from reassess_benchmark_blind import OUT,SOURCES,load,save,sha,verify,frozen

def select():
 plan=verify();dest=OUT/'effective_reviews';dest.mkdir(exist_ok=True);choices={}
 kplan=load(OUT/'k_protocol_recheck/PREREGISTRATION.json');assert kplan['parent_preregistration_sha256']==sha(OUT/'PREREGISTRATION.json')
 for pid in plan['submission_order']:
  packet=load(OUT/'packets'/f'{pid}.json');folder=OUT/'k_protocol_recheck/reviews' if packet['family']=='K' else OUT/'reviews';src=folder/f'{pid}.json'
  if src.exists():
   shutil.copyfile(src,dest/src.name);choices[pid]={'family':packet['family'],'selected_review':str(src.relative_to(ROOT)),'sha256':sha(src),'selection_rule':'all_K_clarified_protocol' if packet['family']=='K' else 'original_first_valid'}
  else:
   assert not (dest/f'{pid}.json').exists();choices[pid]={'family':packet['family'],'selected_review':None,'selection_rule':'missing_U_no_imputation'}
 save(OUT/'EFFECTIVE_SELECTION.json',{'rule':'All15 K packets use clarified protocol, regardless of first-pass validity or scores;81 C/R packets use original first valid response.','packets':choices,'historical_scores_modified':False,'new_agent_answers':0})

def report():
 sys.path.insert(0,str(BASE/'tools'));import aggregate_benchmark_scores as agg
 plan=verify();key=load(OUT/'BLIND_KEY.json');rules=frozen();by_version={v:[] for v in SOURCES};findings=[];protocol=[]
 for pid,item in key.items():
  packet=load(OUT/'packets'/f'{pid}.json');path=OUT/'effective_reviews'/f'{pid}.json'
  d=load(path) if path.exists() else None
  ratings=d['ratings'] if d else dict.fromkeys(packet['rating_keys'],'U')
  row={**item,'id':item['round_id'],'blind_id':pid,'family':packet['family'],'ratings':ratings,'review':str(path.relative_to(ROOT)) if d else None,'errors':d.get('errors',[]) if d else [],'score_status':'model_unverified' if d else 'missing_no_imputation','bounds':agg.export(agg.turn_bounds({'family':packet['family'],'ratings':ratings},rules))}
  by_version[item['version']].append(row)
  if d:
   for e in d.get('errors',[]):findings.append({'blind_id':pid,'kind':'serious_error_allegation',**e})
   for f in d.get('findings',[]):
    if f.get('severity') in ['major','pending']:findings.append({'blind_id':pid,'kind':'model_finding',**f})
  if not d:protocol.append({'blind_id':pid,'issue':'no valid grade; U retained'})
 def weighted(rows,dimension=None):
  numerator=[Fraction(),Fraction()];den=Fraction()
  for r in rows:
   if dimension and dimension not in r['ratings']:continue
   w=Fraction(1,r['full_case_turn_count']);den+=w
   if dimension:
    value=r['ratings'][dimension];maxval=1 if dimension.startswith('K') else 4
    low=Fraction(0) if value=='U' else Fraction(value*100,maxval);high=Fraction(100) if value=='U' else low
   else:low,high=agg.turn_bounds(r,rules)
   numerator[0]+=w*low;numerator[1]+=w*high
  return agg.export(tuple(n/den for n in numerator)) if den else agg.export(None)
 summaries={}
 for v,rows in by_version.items():
  summaries[v]={'selected_rounds':32,'selected_unique_cases':29,'valid_grades':sum(r['score_status']=='model_unverified' for r in rows),'diagnostic32':weighted(rows),'fixed10':weighted([r for r in rows if r['case_id'] in plan['fixed10_case_ids']]),'dimensions':{k:weighted(rows,k) for layer in ['C','R','K'] for k in rules[layer]},'errors_pending':sum(len(r['errors']) for r in rows)}
 save(OUT/'RESULTS.json',{'status':'uniform_by_family_blinded_development_reassessment_not_calibrated','K_protocol_amended_for_all15':True,'selection_sha256':sha(OUT/'EFFECTIVE_SELECTION.json'),'preregistration_sha256':sha(OUT/'PREREGISTRATION.json'),'historical_grades_modified':False,'agent_answer_runs':0,'summaries':summaries,'rows_by_version':by_version,'protocol':protocol})
 save(OUT/'MODEL_FINDINGS.json',findings)
 lines=['**本轮自动评分未通过来源实质核验；以下为保留的原始数字，不用于排名、发布或替代历史成绩。**','','# 同配置匿名复评 · v0.1.1 / v0.1.4 / v0.1.5','','固定32轮来自29道题；部分多轮题只抽规定回合。诊断指数按原题回合权重加权后在此样本归一，不能充作29题完整成绩或65/70题总分。固定10题为原登记的十道单轮题。未经校准的同一模型配置，非专家验收或严格因果实验。','', '|维度 /100|v0.1.1|v0.1.4|v0.1.5|','|---|---:|---:|---:|']
 def fmt(d):return '—' if d['lower'] is None else f"{d['score']:.2f}" if d['score'] is not None else f"{d['lower']:.2f}–{d['upper']:.2f}"
 for title,field in [('32轮诊断指数','diagnostic32'),('固定10题指数','fixed10')]:lines.append('|'+title+'|'+'|'.join(fmt(summaries[v][field]) for v in SOURCES)+'|')
 for layer in ['C','R','K']:
  for k in rules[layer]:
   name=rules[layer][k]['name'] if isinstance(rules[layer][k],dict) else rules[layer][k]
   lines.append('|'+k+' '+name+'|'+'|'.join(fmt(summaries[v]['dimensions'][k]) for v in SOURCES)+'|')
 lines+=['','原始逐维量尺仍为C/60、R增加40、K四项二元；百分制仅为已授权汇总层。U只形成上下界，不填零、不取中点。严重错误指控保留待核，不能由均分抵消。','', '每版有效评分：'+', '.join(v+': '+str(summaries[v]['valid_grades'])+'/32' for v in SOURCES)+'。', '', '全部K题采用统一澄清的二元输出协议；初次非法0–4结果完整保留，没有换算或择高分。C/R保持原始首份有效评分。协议修订仅改输出编码，不改量尺。', '', '[K输出协议说明](k_protocol_recheck/PREREGISTRATION.json) · [有效结果选择](EFFECTIVE_SELECTION.json)', '', '[计划与指纹](PREREGISTRATION.json) · [原始等级和汇总](RESULTS.json) · [模型缺陷候选](MODEL_FINDINGS.json)']
 (OUT/'COMPARISON.md').write_text('\n'.join(lines)+'\n')
 html_rows=''.join('<tr>'+''.join('<th>'+html.escape(c.strip())+'</th>' if n==0 else '<td>'+html.escape(c.strip())+'</td>' for n,c in enumerate(line.strip('|').split('|')))+'</tr>' for line in lines if line.startswith('|') and '---' not in line)
 page='<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>同配置匿名复评 · 未通过核验</title><style>body{margin:0;background:#f7f7f5;color:#252622;font:16px/1.7 -apple-system,BlinkMacSystemFont,PingFang SC,sans-serif}main{max-width:1060px;margin:auto;padding:36px 24px}h1{font-size:28px}.notice{border-left:3px solid #a1814a;background:#f5f0e6;padding:16px 20px}.scroll{overflow:auto;background:white;margin:24px 0;padding:16px;border:1px solid #e1e2dc;border-radius:10px}table{width:100%;border-collapse:collapse;min-width:660px}th,td{padding:12px 14px;border-bottom:1px solid #eee;text-align:right;font-variant-numeric:tabular-nums}th:first-child{text-align:left;font-weight:500}tr:first-child th,tr:first-child td{font-weight:600}a{color:#52674d}.meta{color:#777;font-size:14px}</style><main><h1>同配置匿名复评</h1><p class="notice"><strong>评分器未通过实质核验。</strong>以下只保留原始自动分数，不作为版本排名、发布依据或历史成绩替代。题集和冻结v1.2标准未改。</p><p class="meta">三版各32轮、共96份有效评分。指定32轮涉及29题，部分多轮题只选规定回合，不能充作全套跑分。</p><div class="scroll"><table>'+html_rows+'</table></div><p>诊断指数按原题回合权重加权，在指定样本内归一；固定10题沿用原有单轮子集。各维度仅统计适用回合。</p><p><a href="SUMMARY.md">评审结论与已核缺陷</a> · <a href="SOURCE_AUDIT.json">来源审计</a> · <a href="RESULTS.json">原始等级</a> · <a href="../../benchmark_ledger/matrix.html">历史多维表</a></p></main></html>'
 (OUT/'comparison.html').write_text(page+'\n')
 print(json.dumps({v:{k:summaries[v][k] for k in ['valid_grades','diagnostic32','fixed10','errors_pending']} for v in SOURCES},ensure_ascii=False))

if __name__=='__main__':
 select();report()
