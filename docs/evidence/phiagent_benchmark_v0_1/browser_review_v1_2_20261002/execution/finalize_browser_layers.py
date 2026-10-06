from pathlib import Path
import json,re
ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'docs/evidence/phiagent_benchmark_v0_1/browser_review_v1_2_20261002'
index={i['id']:i for i in json.loads((OUT/'INDEX.json').read_text())}
expression=[]
for path in sorted((OUT/'expression_recheck').glob('batch-??.json')):
 d=json.loads(path.read_text())
 for r in d['rows']:
  item=index[r['id']];expression.append({'platform':item['platform'],'id':f'{item["case_id"]}-T{item["turn"]}','rating':r['C5'],'reason':r['reason'],'span':r.get('span',''),'span_literal':r.get('span_literal',False),'source':str(path.relative_to(ROOT))})
assert len(expression)==144 and len({(r['platform'],r['id']) for r in expression})==144
(OUT/'EXPRESSION_RECHECK.json').write_text(json.dumps(expression,ensure_ascii=False,indent=2)+'\n')
# Amend the two conditions whose first-pass rationale improperly penalized UI
# follow-up widgets. Substantive limitations remain in their own dimensions.
p=OUT/'CODEX_ADJUDICATION.json';overrides=json.loads(p.read_text())
for cid,span,note in [('M03','机器 100% 准确预测你的选择，这个假设成立','明确接受预测准确条件，没有以机器算不准回避；C1不因平台推荐问题扣分。公开预测的自反情形和模态区分仍有论证局限，未据此上调其他维度。'),('M04','你是 A，复制出 B，A 和 B 同时存活。','保留两者同时存活并讨论分叉，C1不因文末平台推荐扣分；把全部记忆扩展成人格和意识流的讨论仍有额外假定，故未给最高等级。')]:
 a=json.loads((OUT/'source'/'doubao'/(cid+'.json')).read_text())['turns'][0]['answer'];assert span in a
 entry={'platform':'doubao','id':cid+'-T1','ratings':{'C1':3},'reasons':{'C1':{'reason':note,'span':span,'span_literal':True,'evidence':'Frozen prompt and full answer; UI-tail boundary correction'}},'reviewer':'Codex targeted condition check','scope':'C1 only; remaining dimensions retain their attributed reviewers'}
 overrides=[o for o in overrides if not(o['platform']=='doubao' and o['id']==cid+'-T1')]+[entry]
p.write_text(json.dumps(overrides,ensure_ascii=False,indent=2)+'\n')
print('expression rechecks',len(expression),'targeted adjudications',len(overrides))
