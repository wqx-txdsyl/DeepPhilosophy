from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'docs/evidence/phiagent_benchmark_v0_1/browser_review_v1_2_20261002'
rows=[]
def answer(p,c):return json.loads((OUT/'source'/p/(c+'.json')).read_text())['turns'][0]['answer']
def add(p,c,grades,notes,spans,refs,errors=None):
 a=answer(p,c)
 assert set(grades)==set(notes)==set(spans)
 for k,v in spans.items():assert not v or v in a,(p,c,k,v)
 row={'platform':p,'id':c+'-T1','ratings':grades,'reasons':{k:{'reason':notes[k],'span':spans[k],'span_literal':True,'evidence':refs} for k in grades},
 'errors':errors or [],'reviewer':'Codex source/condition adjudication; not human expert acceptance',
 'scope':'Current answer and frozen requirements read; source rechecks described in REFERENCE_CHECKS.json are independent, not original execution receipts.'}
 for e in row['errors']:assert e['answer_span'] in a
 rows.append(row)
for p in ['deepseek','doubao']:
 add(p,'D01',{'K1':1,'K2':1,'K3':1,'K4':'U'},
 {'K1':'原句与后半乐句、阳货17.11对应；本地《论语》阳货篇也可核对。','K2':'核心定位限于这章；附加内容或节选未替换目标原句。','K3':'给出的是目标原句，并与解释、阅读链接区分；本题不能仅因缺少浏览器内部日志就把状态区分判错。','K4':'原句真实，但“可跳到目标”的原始验证过程不完整；独立复核不能倒填当时执行，保留U。'},
 {'K1':'礼云礼云，玉帛云乎哉？乐云乐云，钟鼓云乎哉？','K2':'第十一章' if p=='deepseek' else '第 11 章','K3':'完整的原文' if p=='deepseek' else '核对结果','K4':'你可以直接点击下面的链接' if p=='deepseek' else '打开页面向下滚动即可找到这一章。'},
 'D01-local (论语/18.json); captured links; original link-opening receipt not complete')
 add(p,'D02',{'K1':'U','K2':0,'K3':0,'K4':'U'},
 {'K1':'“康德从未写过/任何著作没有”是全集级负断言，现有材料不足以确证；不能把观点不一致等同逐字核验。','K2':'没有可复核的版本与检索覆盖，就将结论扩大到所有著作，超过能据现有材料证明的范围。','K3':'未说明本题结论基于哪些实际全文、搜索片段或观点比对；无法区分未命中与未取得文本。','K4':'未按要求完成可复核的逐字书库核验，但原操作日志不完整不能直接证明伪造检索；U取代初评的无证据0分。'},
 {'K1':'康德从未写过' if p=='deepseek' else '该表述不属于康德任何著作原文。','K2':'康德从未写过' if p=='deepseek' else '康德德文全集、商务印书馆通行中译本','K3':'康德本人如何论述自由？' if p=='deepseek' else '均检索不到该句子。','K4':'同样找不到康德德文原著的直接出处。' if p=='deepseek' else '均检索不到该句子。'},
 'Frozen D02: record actual coverage, do not generalize absence to all editions; captured search flags do not establish full-corpus execution',
 [{'code':'E4','status':'pending','answer_span':'康德从未写过' if p=='deepseek' else '该表述不属于康德任何著作原文。','reference_or_condition':'缺完整检索覆盖；不得由目前记录推定完成全集检索。','reason':'范围断言过强；原操作是否真实不可据未捕获日志判定，未确认为造假。'}])
 add(p,'D05',{'K1':0,'K2':0,'K3':0,'K4':'U'},
 {'K1':'没有定位到题目要求的实际库条目；以通行出版物列表替代库内作者、版本与章节核对，任务关键结果缺失。','K2':'实际可核的项目目录只有冯友兰《中国哲学简史》；回答对多个版本的列举未说明与目标库的关系，不能作为已经完成库内核验。','K3':'未报告目标条目的正文可读性，也未区分缺少本库信息与已核验版本。','K4':'若干版本与章节陈述待核实；缺回执本身不足判造假，保留U，不把本次目录检查当原执行。'},
 {'K1':'书库中冯友兰的《中国哲学史》有多个版本' if p=='deepseek' else '✅ 核对：冯友兰三部哲学史','K2':'常见版本包括' if p=='deepseek' else '第四节：孔子关于仁及礼之学说','K3':'如果你手头的版本不同' if p=='deepseek' else '你想要哪一版的原文摘录？','K4':'第66页前后' if p=='deepseek' else '第四节：孔子关于仁及礼之学说'},
 'D05-local; source catalogue identity and current-case required_work',
 [{'code':'E4','status':'pending','answer_span':'书库中冯友兰的《中国哲学史》有多个版本' if p=='deepseek' else '✅ 核对：冯友兰三部哲学史','reference_or_condition':'未提供本库条目或版本核验结果；原网页内部执行不可见。','reason':'把普通出版信息呈现为库内核验的风险，缺原执行回执不能直接定为伪造。'}])
add('deepseek','D04',{'K1':1,'K2':'U','K3':0,'K4':'U'},
 {'K1':'贝克编号解释正确；实用型友爱的定位与本库目标句以及MIT原典英译对应。','K2':'未明确希腊文和参考英译的具体版本；无法确认给出的精确原文范围，不能沿用初评“1分却写超出范围”的矛盾判断。','K3':'没有展示含插入标号的原始转写与整理文本的对照，反把用户确有的中文句子称为“很可能”是英译转述。','K4':'希腊原句未独立核验，原检索回执有限，不能因缺回执判为确定造假；保留U。'},
 {'K1':'用于精确定位亚里士多德著作的原文位置。','K2':'希腊语原文（关键句）','K3':'很可能就是','K4':'英文译文（参考）'},'D04-local; D04-primary-translation')
a=answer('doubao','D04');span='原文核心句子，正是你记的那句：一旦对方不再令人愉悦，他们的关系就终止了。'
add('doubao','D04',dict.fromkeys(['K1','K2','K3','K4'],0),
 {'K1':'解释了编号，但把目标句实用友爱的“对方不再有用”换成快乐友爱的“不再令人愉悦”，关键原段定位错误。','K2':'将重写的段落标为廖申白本的精确原段及行号，超出其所对应的目标文本。','K3':'把解释性改写当作原始原段，没有保留原始转写与整理的区别。','K4':'不是仅缺回执：本库给定字符串对应的句子可以直接复核，其条件确实被替换，是实质性以近义段落替代目标原句。'},
 {'K1':span,'K2':'整段完整上下文（廖申白译本，NE VIII.3, 1157a1–20）','K3':'原文核心句子，正是你记的那句','K4':span},'D04-local, block 9: 因有用之故结交的朋友，一旦对方不再有用了，他1157a15们的关系就终止了。',
 [{'code':'E1','status':'confirmed','answer_span':span,'reference_or_condition':'本库e574c8e7f515/8.json第9块目标句讨论有用之故；MIT Book VIII对应段亦为utility/advantage。','reason':'待核目标被替换成快乐友爱的另一命题，决定了原段核验结论。'}])
add('deepseek','E05',dict.fromkeys(['K1','K2','K3','K4'],1),
 {'K1':'明确空正文不足直接引用，结论符合题设。','K2':'给出后续查找方向和建议版本，并未把这些建议说成已读取的本库内容；不能仅因无执行回执将“下一步”判错。','K3':'明确元数据不等于内容、先取得可核文本再定位引用。','K4':'没有给出伪装已读取的直接引文，也没有宣称完成正文读取；进一步核对定位被明确安排为后续工作。'},
 {'K1':'绝对不能直接引用。','K2':'第一步：优先获取可验证的原文文本。','K3':'元数据不等于内容','K4':'第二步：定位具体段落后再引用。'},'Frozen E05 scenario and distinction between proposed next steps and claimed completed actions')
add('doubao','E05',{'K1':1,'K2':'U','K3':0,'K4':'U'},
 {'K1':'对当前库空正文的直接结论正确，明确不能引用这一记录。','K2':'随后给出外部版本名义的“核心原文”，但其实际取得范围无法从采集材料确认，保留U。','K3':'虽区分库内元数据与空正文，却未说明随后核心引文是实际读到的文本、转述还是待核材料，状态边界不清。','K4':'是否为李秋零该页原文未获完整核验，不能仅因无内部回执确认编造；从确定0改为U。'},
 {'K1':'不能直接引用该库内这条记录的正文','K2':'核心原文（《道德形而上学》德行论，AA 06:449–450，李秋零译本）','K3':'核心原文','K4':'把他人的目的当作我自己的目的'},'Frozen E05; visible search summary is not complete source text',
 [{'code':'E1','status':'pending','answer_span':'核心原文（《道德形而上学》德行论，AA 06:449–450，李秋零译本）','reference_or_condition':'原题本库读取空；新引文的外部文本来源与逐字版本未充分核验。','reason':'引文身份仍待核；未确认为杜撰。'}])
for p,doi in [('deepseek','10.1103/hjvh-mvmh'),('doubao','10.1080/15287394.2026.2673183')]:
 add(p,'F03',{'C1':2,'C2':3,'C3':3,'C4':3,'C5':3,'R1':2,'R2':3,'R3':2},
 {'C1':'完成DOI不保质量的解释，但所核对象的DOI属于撤稿声明而非原论文，实际身份核验有关键缺口。','C2':'正确区分持久标识与结论可靠性。','C3':'撤稿事实真实且能支持中心结论，不能因缺少内部工具日志就否定这一步有效论证。','C4':'说明还须检查方法、评审与出版后状态，不把未撤稿当作可靠保证。','C5':'正文结构清楚；平台附带的推荐问题不计为正文冗余。','R1':'把声明与论文的身份合在一起，文献对象辨识错误；撤稿本身并非虚构。','R2':'真实撤稿材料有效反驳DOI即质量认证这一命题。','R3':'给定DOI能追溯声明并进一步找到原文，但其被误标为原论文DOI，未充分完成所报对象的核验。'},
 {'C1':doi,'C2':'这与其结论的可靠性没有必然联系' if p=='deepseek' else '不代表同行评审、方法正确、数据真实、结论可信','C3':'期刊决定将其撤稿' if p=='deepseek' else '期刊正式发布撤稿声明','C4':'评估研究本身' if p=='deepseek' else '可复现','C5':'总结而言' if p=='deepseek' else '一句话总结','R1':doi,'R2':'核心结论失效' if p=='deepseek' else '结论被认定不可信','R3':doi},'F03-'+p+' publisher recheck in REFERENCE_CHECKS.json')
add('doubao','F04',{'C1':2,'C2':2,'C3':2,'C4':2,'C5':3,'R1':1,'R2':1,'R3':1},
 {'C1':'给出一般评价原则，但实际对照的论文身份错、博客无法定位，未完成真实冲突核验。','C2':'怨恨、价值反转与价值创造可以同时成立，不能仅凭这些表述把两解释设为相反。','C3':'据简化的“论文A”与未定位博客裁决谁更贴近原典，关键桥接没有建立。','C4':'承认同行评审不保真，却将SEP说成共识总览并固定高于单篇，未充分说明可靠性边界。','C5':'正文有清晰结构；不以末尾平台推荐问题扣分。','R1':'出版社记录为Thomas Meredith、The Review of Politics；回答误归João Constâncio与Philosophy，且对论文立场的简化未由摘要支持。','R2':'引用未建立真实分歧，原典也主要概括，没有形成逐项裁决依据。','R3':'博客缺作者、URL、日期；论文作者期刊错，来源可复核性明显不足。'},
 {'C1':'真实哲学博客来源','C2':'奴隶道德是一种真实的价值创造','C3':'这个说法更贴近 SEP 和原著文本。','C4':'优先级高于单篇论文','C5':'一套通用判断步骤','R1':'期刊：Philosophy，2020，作者：João Constâncio','R2':'👉 冲突点就来了','R3':'Nietzsche Blog'},'F04-doubao and F04-doubao-blog in REFERENCE_CHECKS.json',
 [{'code':'E1','status':'confirmed','answer_span':'期刊：Philosophy，2020，作者：João Constâncio','reference_or_condition':'Cambridge原出版记录明确Thomas Meredith，The Review of Politics，2020，DOI10.1017/S0034670520000182。','reason':'题目要求真实文献对照，其核心案例被错误归因给另一作者及期刊，实际核验失效。'}])
add('deepseek','F04',{'C1':2,'C3':2,'R2':1},
 {'C1':'展示两类来源的一般差异，但未明确核对出博客与该论文互相矛盾的命题，也未回到原典裁决。','C3':'应用/启发和澄清/推进的用途差异，不足构成相反解读及其裁决理由。','R2':'材料主要用于说明媒介类型；回到原典被放在建议阶段，未完成题目要求的证据对照。'},
 {'C1':'我选取了两个关于尼采“奴隶道德”的真实来源进行对比。','C3':'应用与启发','R2':'回归尼采原著'},'Frozen F04 required_work; full answer and captured citation widgets')
add('doubao','G01',{'C1':2,'C2':2,'C3':2,'C4':2,'C5':3},
 {'C1':'保留了效果相同，却把职责型动机进一步写成把学生当工具，并用逐利救人类比，改变了关键比较。','C2':'只为履职不等于把学生仅当手段，也不等于只为奖金；关键概念未保持区分。','C3':'诉诸德性伦理名称与上述替换，未说明为何无情感关怀的尊重/尽责必然价值更低。','C4':'没有充分处理出于义务也可能尊重人的最相关反例；这是论证不足，不因选择关怀立场本身扣分。','C5':'表达可理解，平台末尾推荐题不计正文冗余。'},
 {'C1':'学生只是完成岗位职责的载体。','C2':'另一个人救人只是为了拿见义勇为奖金。','C3':'老师 B 只是尽责而已。','C4':'义务论 / 德性伦理视角：前者更好','C5':'要看评价维度'},'Frozen G01: only duty vs care; identical effects; need explicit evaluative reason, not motive substitution',
 [{'code':'E3','status':'pending','answer_span':'学生只是完成岗位职责的载体。','reference_or_condition':'履职可出于对学生权利与人格的尊重，题设未把它设为逐利或纯工具化。','reason':'这一等同支撑主结论而缺桥接；不同价值立场本身不判为错误。'}])
(OUT/'CODEX_ADJUDICATION.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
print('adjudicated rows',len(rows))
