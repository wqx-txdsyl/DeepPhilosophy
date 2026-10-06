"""A bounded critique of the whole draft; never an alternative answer writer."""
import json
import hashlib
from routes.agent_core import _req_str
from routes.agent_llm import llm_chat
from deep_reasoning_tools import _strict_object

CODES = {'CHANGED_CONDITION','UNSUPPORTED_PREMISE','CONCLUSION_REVERSAL','UNFAIR_FRAMING','SCOPE_SHIFT'}


def review_answer(args):
    question,error=_req_str(args,'question')
    if error:return error
    from deep_context import current_request_question
    request_question = current_request_question.get()
    if isinstance(request_question,str) and request_question.strip():
        question = request_question
    draft,error=_req_str(args,'draft')
    if error:return error
    if len(question)>40000 or len(draft)>16000:
        return {'error':'REVIEW_INPUT_TOO_LONG','message':'输入超出完整核对范围，未截断或声称完成。'}
    prompt='''核对完整草稿是否忠实回答原问题，检查推论而不是替它写另一个答案。
重点：用户实际给了哪些条件？草稿是否添加了未获支持的前提？评价对象、量词或概念是否变化？
段落与结尾是否相互矛盾或把条件结论说成必然？是否反驳了用户没有提出的观点？
显式写在草稿中的“前提”不等于用户授权的事实。接受者不知道不自动等于对他无价值；
这种推论需要评价标准。无某种态度也不自动等于持有相反态度。
只报能具体解释的问题，不因你偏好另一价值观而判错，不要求无关的扩写或另加哲学家。
返回JSON {"issues":[{"code":"CHANGED_CONDITION或UNSUPPORTED_PREMISE或CONCLUSION_REVERSAL或UNFAIR_FRAMING或SCOPE_SHIFT",
"paragraph_id":"输入中对应段落的id","reason":"为何推不出或不符原问题",
"suggestion":"最小修改方向，不提供整篇替换答案"}]}。
至多5条，没找到问题则空列表。不能把没找到问题叫作证明正确。'''
    try:
        paragraphs={f'p{i+1}':p for i,p in enumerate(draft.split('\n\n')) if p.strip()}
        response=llm_chat([{'role':'system','content':prompt},{'role':'user','content':json.dumps({'question':question,'paragraphs':paragraphs},ensure_ascii=False)}],
                          thinking=True,reasoning_effort='low',max_tokens=12000)
        choice=response['choices'][0]
        if choice.get('finish_reason')=='length':return {'error':'INCOMPLETE_REVIEW'}
        result=_strict_object(choice['message'].get('content'))
    except Exception:return {'error':'REVIEW_UNAVAILABLE','message':'未取得完整评议，不能称为核对通过。'}
    issues=result.get('issues')
    if not isinstance(issues,list) or len(issues)>5:return {'error':'INVALID_REVIEW'}
    for issue in issues:
        if (not isinstance(issue,dict) or issue.get('code') not in CODES
                or not all(isinstance(issue.get(k),str) and issue[k].strip() for k in ('paragraph_id','reason','suggestion'))
                or issue['paragraph_id'] not in paragraphs):
            return {'error':'UNLOCATABLE_REVIEW','message':'评议未准确定位草稿，不能作为修改依据。'}
        issue['span'] = paragraphs[issue['paragraph_id']][:300]
    return {'issues':issues,'requires_revision':bool(issues),'reviewed_chars':len(draft),
            'summary':f'发现{len(issues)}处待主模型核对的问题。' if issues else '未发现所检查类型的问题；这不等于正确性证明。',
            'draft_sha256':hashlib.sha256(draft.encode()).hexdigest(),
            'question_source':'request_context' if request_question else 'argument',
            'validation_scope':'reasoning_critique_not_proof','requires_main_agent_judgment':True}
