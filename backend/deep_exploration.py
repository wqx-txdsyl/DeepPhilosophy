"""Generate contextual follow-up questions after the answer, without agent tools."""
import json
from deep_streaming import wants_suggestions


def generate_exploration(question, answer, language='zh', previous=None):
    if not answer.strip() or not wants_suggestions(question):
        return {'suggestions':[], 'status':'disabled'}
    from routes.agent_llm import llm_chat
    system = ('根据完整问答，生成两条值得继续深入的具体哲学问题。每条抓住回答里尚未解决的前提、概念张力、'
              '证据缺口或有力异议，推进讨论而非复述答案。不得把有争议的判断当作已经证明的事实。'
              '不用“检验反例”“比较不同立场”“联系具体处境”等泛泛方向，不推销工具、论文、辩论或脑图。'
              '每条是自然、独立完整的问句，不带序号、解释和答案；避免重复之前的问题。'
              '只返回JSON：{"questions":["问题一？","问题二？"]}。'
              + ('Questions must be in English.' if language=='en' else '问题用中文。'))
    try:
        response=llm_chat([{'role':'system','content':system},
                           {'role':'user','content':json.dumps({'question':question,
                            'answer':answer,'previous_questions':previous or []},ensure_ascii=False)}],
                          temperature=0.8,max_tokens=512,disable_thinking=True)
        choice=response['choices'][0]
        if choice.get('finish_reason')=='length':return {'suggestions':[],'status':'unavailable'}
        content=choice['message'].get('content') or ''
        if content.strip().startswith('```'):
            content=content.strip().split('\n',1)[1].rsplit('```',1)[0]
        questions=json.loads(content).get('questions')
        if not isinstance(questions,list):raise ValueError('Invalid questions')
        seen={q.strip() for q in previous or [] if isinstance(q,str)}
        output=[]
        for question in questions:
            if not isinstance(question,str):continue
            q=question.strip()
            if q and q.endswith(('?','？')) and q not in seen and q.rstrip('?？') not in {'检验反例','比较不同立场','联系具体处境'}:
                output.append(q);seen.add(q)
            if len(output)==2:break
        return {'suggestions':output,'status':'ready' if output else 'unavailable'}
    except Exception:
        return {'suggestions':[],'status':'unavailable'}
