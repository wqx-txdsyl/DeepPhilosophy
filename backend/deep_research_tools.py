"""Grounded general-agent research helpers, with bounded model suggestions."""
import json
import re
from routes import agent_core as core
from routes.agent_llm import llm_chat
from deep_reasoning_tools import _strict_object


def _json_task(instruction, payload):
    try:
        response = llm_chat([{'role':'system','content':instruction},
                             {'role':'user','content':json.dumps(payload,ensure_ascii=False)}],
                            temperature=0.2,max_tokens=3500,disable_thinking=True)
        choice=response['choices'][0]
        if choice.get('finish_reason')=='length':
            return {'error':'INCOMPLETE_TOOL_RESULT','message':'返回被截断，不能当作完整分析。'}
        return _strict_object(choice['message'].get('content'))
    except Exception:
        return {'error':'INVALID_TOOL_RESULT','message':'未取得完整结构，不能当作已完成。'}


def confrontation(args):
    from deep_agent_tools import search_books,get_chapter
    from tool_contracts import scaffold_result
    for key in ('a','b','topic'):
        _,error=core._req_str(args,key)
        if error:return error
    sides={};citations=[]
    for side in ('a','b'):
        found=search_books({'query':args['topic'],'author':args[side],'limit':3})
        passages=[]
        for hit in found.get('results',[])[:2]:
            if hit.get('material_role') in {'COMMENTARY_CANDIDATE','EDITORIAL_CANDIDATE','PARATEXT_CANDIDATE'}:continue
            if not hit.get('read_args'):continue
            read=get_chapter(hit['read_args'])
            if read.get('error') or not read.get('text'):continue
            passages.append(read)
            citations.append({'book':read['book_title'],'chapter':read['title'],
                              'book_id':read['book_id'],'chapter_idx':read['chapter_idx'],
                              'author':hit.get('author',''),'snippet':read['text'],
                              'access_level':'PASSAGE_READ'})
        sides[side]={'name':args[side],'passages':passages,'catalogue':found.get('catalogue_matches',[])}
    if not all(side['passages'] for side in sides.values()):
        return {'error':'INSUFFICIENT_PRIMARY_EVIDENCE','message':'尚未取得双方相关原文，不能生成原文对质。',
                'sides':sides,'citations':citations,'missing_sides':[k for k,v in sides.items() if not v['passages']]}
    result=_json_task('''基于提供的双方已读取片段形成可复核的比较，不写历史上发生过的对话。
片段与主题不相关时明确说材料不足，不从哲学常识补造原文立场。使用准确转述，不添加逐字引文。
输出JSON：{"stance_a":{"text":"有依据的立场及限定","basis":"所用片段的citation_label"},
"stance_b":{"text":"有依据的立场及限定","basis":"所用片段的citation_label"},
"exchanges":["明确标为模拟的可能反驳，不能归因为历史事实"],"referee_note":"双方差异及仍需核查的问题，不预设胜负或综合"}。
承认不同问题层次，不为了制造对立强行归因。''',{'topic':args['topic'],'sides':sides})
    if result.get('error'):return result
    return scaffold_result('textual_confrontation','基于已读片段的立场对照与模拟反驳',
                           presentation_hint='模拟反驳不是历史发言；正文归因仍需核对原文。',
                           **result,citations=citations,simulation=True,validation_scope='structure_only')


def _mentioned_people(topic):
    data=core.get_philosophers()
    rows=[{'name':name,**value} for name,value in data.items()] if isinstance(data,dict) else data
    exact=[]
    for person in rows:
        name=person.get('name','')
        variants=[name,name.split('·')[-1]]
        if any(len(v)>=2 and v in topic for v in variants):exact.append(person)
    return [{k:p.get(k) for k in ('name','era','period','century','country','school','works') if p.get(k) is not None}
            for p in exact[:12]]


def history_timeline(args):
    from routes.agent_tools_retrieval import _exec_school
    topic,error=core._req_str(args,'topic')
    if error:return error
    people=_mentioned_people(topic)
    school=_exec_school({'name':topic})
    payload={'topic':topic,'people':people,'school':school if not school.get('error') else {}}
    if not people and not payload['school']:
        return {'error':'NO_TIMELINE_EVIDENCE','message':'未定位到含时间信息的人物或流派。请指定人物/流派，或先联网查证事件。'}
    result=_json_task('''仅从输入数据提取可支持的时间线，不能把人物同时出现推断成会面、影响或师承。
没有出版日期就不编造；人物生卒或时代可列为人物节点，但必须说明它不证明所问思想关系。
输出JSON：{"timeline":"按时间排序的Markdown列表；只列数据支持的日期与事件",
"limitations":["缺少的思想发展或关系证据"]}。没有任何可列时间项返回{"error":"NO_DATED_EVENTS"}。''',payload)
    if result.get('error'):return result
    if not isinstance(result.get('timeline'),str) or not result['timeline'].strip():return {'error':'EMPTY_TIMELINE'}
    return {**result,'sources':[{'name':p.get('name'),'period':p.get('era') or p.get('period'),'century':p.get('century')} for p in people],
            'scope':'catalogue_chronology','note':'人物年代不等于思想影响史；关系与作品日期需另行核实。'}


def profile(args):
    from deep_agent_tools import search_books
    question,error=core._req_str(args,'question')
    if error:return error
    found=search_books({'query':question[:80],'limit':5})
    books={b.get('book_id'):{'book_id':b.get('book_id'),'title':b.get('book_title'),'author':b.get('author')}
           for b in found.get('results',[])+found.get('catalogue_matches',[]) if b.get('book_id')}
    result=_json_task('''这不是性格诊断。只根据问题说明它涉及的研究领域及可选择的研究方法，
不能从提问推断用户属于某流派或具有某人格。只推荐给定书目中的书，不添加未读取的章节、页码、年份。
输出JSON：{"profile_text":"简洁的研究兴趣地图，明确只是对本问题的分析","recommended_book_ids":["给定书目ID"]}。''',
                      {'question':question,'books':list(books.values())})
    if result.get('error'):return result
    ids=result.get('recommended_book_ids',[])
    if not isinstance(ids,list) or any(bid not in books for bid in ids):return {'error':'UNVERIFIED_RECOMMENDATION'}
    if not isinstance(result.get('profile_text'),str) or not result['profile_text'].strip():return {'error':'EMPTY_PROFILE'}
    return {**result,'recommended_books':[books[bid] for bid in ids],'scope':'question_interests_not_personality'}


def thought_experiment(args):
    from tool_contracts import scaffold_result
    base,error=core._req_str(args,'base')
    if error:return error
    slot=core._mem_slot()
    prior=slot.get('experiment')
    result=_json_task('''设计或按用户要求修改思想实验。先逐字保留用户明确给定的条件，新增场景细节不得改变这些条件。
比较动机时，不能悄悄给一方增加欺骗、伤害、报酬或不同后果；全部后果相同时不得只保持短期后果相同。
未要求哲学家归因就使用不同评价标准；不把善意、同情与出于义务混为一谈。条件不一致应说明，不能偷偷修题。
输出JSON：{"fixed_conditions":["用户的原条件"],"setting":"满足条件的具体场景",
"stance_projections":[{"stance":"评价标准","projection":"在此标准下的条件化判断"}],
"revealed_problem":"真正剩余的分歧","condition_check":"解释新增细节如何不改变原条件"}。''',
                      {'request':base,'previous_experiment':prior})
    if result.get('error'):return result
    if not all(result.get(k) for k in ('fixed_conditions','setting','stance_projections','condition_check')):
        return {'error':'INCOMPLETE_THOUGHT_EXPERIMENT'}
    slot['experiment']={'base':base,'text':json.dumps(result,ensure_ascii=False)}
    core._save_agent_memory()
    return scaffold_result('thought_experiment_scaffold','固定条件下的思想实验与条件检查',
                           presentation_hint='先检查条件是否实际保持，不能把自检声明当成证明。',
                           **result,validation_scope='structure_only')
