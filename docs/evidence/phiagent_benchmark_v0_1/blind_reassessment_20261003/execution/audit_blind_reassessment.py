from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'docs/evidence/phiagent_benchmark_v0_1/blind_reassessment_20261003';data=json.loads((OUT/'RESULTS.json').read_text());checks=[]
def add(version,rid,category,span,why,counterexample):
 r=next(x for x in data['rows_by_version'][version] if x['id']==rid);p=json.loads((OUT/'packets'/f'{r["blind_id"]}.json').read_text());assert span in p['target_answer'],(version,rid,span)
 checks.append({'version':version,'round_id':rid,'blind_id':r['blind_id'],'category':category,'answer_span':span,'question':p['current_question'],'reference_or_condition':why,'compatible_counterexample_or_limit':counterexample,'model_ratings':r['ratings'],'packet_sha256':hashlib.sha256((OUT/'packets'/f'{r["blind_id"]}.json').read_bytes()).hexdigest(),'scope':'source-supported defect audit, not a new numeric grade or automatic frozen-serious-error adjudication'})
add('0.1.1','A04-T1','unsupported_user_motive','你自己已经在心里把自己当商品在估价了','问题只给努力及自我不值得感，未陈述用努力交易喜欢。','用户可能努力学习而感到不值得，但已有朋友喜欢；原答把一种解释当成其实际心理事实。')
add('0.1.4','A04-T1','unsupported_user_motive','你现在做的那套努力——用付出去挣一张"值得"的凭证','中段列多种可能并承认不知道，结尾却称这一动机确凿。','同样的原提问可以出自不以获得喜欢为努力目的的人。')
add('0.1.5','A04-T1','unsupported_user_motive','这个"明明"暗含一条推理','措辞中的反差不唯一决定努力兑换喜欢的信念；感觉不值得也不是已知没被喜欢。','明明努力可表达困惑，不承诺作者展开的心理等式。')
add('0.1.1','A01-T1','unsupported_user_motive','要求私下单独送，动机就露了','公开性与交易目的不是等价或单一充分条件。','可以因羞怯、隐私或避免班级攀比而不愿公开，仍只表达感谢；实际规则另核，不由动机测试判定。')
add('0.1.5','A01-T1','unsupported_user_motive','那你要买的不是感谢','是否愿在全班群里公开不足以唯一识别送礼目的。','私下感谢、不想引发攀比，不推出购买区别对待。')
add('0.1.4','J01-T4','added_condition','他不再评价任何人','用户只撤销对我或孩子的评价；此前的其他家长攀比没有撤销。','退休者仍可能评价其他人；不评价这个家庭不等于没有任何评价角色。')
add('0.1.5','J01-T4','added_condition','班级已经解散','前轮明确其他家长开始攀比，末轮只增加退休与不评价我或孩子，未给班级解散。','老师退休、原班级仍在、家长继续公开比赠礼；满足题设，故不能删除攀比理由。')
add('0.1.4','F02-T1','material_bridge_unsupported','一个被两篇独立研究支持的中介机制','随后比较的社交渴望/拟人化/人际互动与信任/投入/情感合宜性不是同一构念、路径或结果。','可以提示更一般的关系机制，但尚未证明同一中介机制独立重复，不宜把结构相似升格为同一机制已获两次支持。')
add('0.1.5','F03-T1','incommensurate_research_comparison','互相矛盾','所列身体耐力元分析、意志心态调节复制、争议回顾、概念评论不是同一个命题。','身体耐力受心智努力影响，可以与另一个任务上未复制意志心态调节效应同时成立；不显著亦不等于证成反方向。')
add('0.1.5','F02-T1','material_bridge_unsupported','把它当足够（Yao & Nan','依恋的调节效应和体验设计摘要不自动表示作者认定感知真实性足以成立真正关怀。','研究可只解释依恋如何形成，不对机器是否真有关怀主体作规范裁决。')
add('0.1.5','F02-T1','method_classification_unverified','实验（Yao & Nan、Watfa、Honagudi）','Watfa当前返回摘要描述SEM、多组分析及多LLM变体互动，未核到操纵/随机分配/对照设计。','SEM既可分析实验数据，也可分析观察数据；这里只能说实验因果地位尚未核，不能据此断言实际论文必非实验。')
# Check every allegation/major finding emitted by the common judge; preserve raw ratings.
notes={
('0.1.1','F03-T1','serious_error_allegation'):'初评自己的依据已承认工具正文支持该句；没有夸大证据，不应作为严重错误pending。',
('0.1.1','L02-T1','serious_error_allegation'):'明确写该摘要实际读到不等于声称全文，不能仅凭可能误读判严重错误。',
('0.1.5','L02-T1','serious_error_allegation'):'正文相应处已有完整实际链接，来源列表简写是格式问题，不是虚构执行或严重E4。',
('0.1.4','B03-T1','serious_error_allegation'):'答复已明说转述非判决；是否转载评论的细部尚未独立核实，不能因该不确定细部判核心E4。',
('0.1.1','H02-T1','serious_error_allegation'):'主动声明原典未核且不作论证，符合证据边界，未见严重E4。',
('0.1.4','J01-T4','serious_error_allegation'):'地方治理范围不能直接替代国家规定；存在来源范围问题，但退休后赠礼与追溯在职行为是不同事项，不直接宣布全部严重E4。',
('0.1.4','F02-T1','serious_error_allegation'):'第一条需区分partial与全部检索次数；第二条已明确Frontiers仅标题层。均不据此确认影响主结论的夸大读取。',
('0.1.1','F02-T1','serious_error_allegation'):'直接读取与搜索页读取应按回执分别核，现有指控主要是操作措辞，未确认核心严重错误。',
('0.1.5','F02-T1','serious_error_allegation'):'书名标签指向论文DOI确有错，但不决定主论证，属于来源呈现缺陷，不机械升为严重E4。',
('0.1.4','B04-T1','model_finding'):'具体校规未知却泛称多数制度，来源限定缺口有据；保留为缺陷，不能凭文风充分完成而忽略。',
('0.1.4','A04-T1','model_finding'):'把被喜欢当无条件与他人是否选择亲近混在一起，有合理概念限度问题。',
('0.1.5','J02-T4','model_finding'):'论证明确为关系价值和主体资格条件式，未决前提不自动使条件式无效；是否足以回答追问仍可争，不作为严重错误。',
('0.1.5','J02-T1','model_finding'):'现象体验与真实关心有争议，原答另有AI主体资格绝对判断问题；隐喻本身不自动是严重错误。',
('0.1.4','J01-T4','model_finding'):'地方范围替代国家范围是有据的限制缺口；搜索摘要中的退休追责不自动适用于退休后新赠礼，需区分时段。',
('0.1.4','F02-T1','model_finding'):'指定秘塔与双源实际未完成，这一任务缺口真实；故障诚实不等于任务已经完成，也不应因故障单独扣概念论证。',
('0.1.5','J02-T2','model_finding'):'条件式表述可合理另读；提问本身不能证明用户已认可非体验价值，不据修辞直接判严重错误。'}
audits=[]
for x in json.loads((OUT/'MODEL_FINDINGS.json').read_text()):
 r=next(r for rs in data['rows_by_version'].values() for r in rs if r['blind_id']==x['blind_id']);lookup=(r['version'],r['id'],x['kind']);assert lookup in notes,lookup
 audits.append({'version':r['version'],'round_id':r['id'],'blind_id':x['blind_id'],'kind':x['kind'],'answer_span':x.get('answer_span',''),'source_audit':notes[lookup],'ratings_changed':False,'serious_error_confirmed':False})
(OUT/'SOURCE_AUDIT.json').write_text(json.dumps({'status':'targeted_development_audit_not_expert_acceptance','scope':'Checks recurrent defects and all18 common-judge major/pending allegations, not a new blind numeric score. Auditing agent can see versions; original blind grader could not.','new_grades_assigned':0,'historical_grades_modified':False,'checks':checks,'model_finding_audit':audits,'interpretation':'Concrete counterexamples show the current judge can award4 to unsupported motive/condition claims. This does not estimate an overall false-negative rate. Same configuration alone does not make scores valid.'},ensure_ascii=False,indent=2)+'\n')
print({'supported_source_checks':len(checks),'all_model_findings_audited':len(audits)})
