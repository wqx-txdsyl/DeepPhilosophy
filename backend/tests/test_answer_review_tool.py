import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import deep_answer_review as review

def response(issues):return {'choices':[{'message':{'content':json.dumps({'issues':issues})},'finish_reason':'stop'}]}

def test_review_requires_real_span_and_never_returns_replacement(monkeypatch):
    monkeypatch.setattr(review,'llm_chat',lambda *a,**k:response([{'code':'CONCLUSION_REVERSAL','paragraph_id':'p1','reason':'与前文不一致','suggestion':'保持条件'}]))
    result=review.review_answer({'question':'问题','draft':'前文如此，结论相反。'})
    assert result['requires_revision'] is True and 'answer' not in result
    assert result['issues'][0]['span']=='前文如此，结论相反。'
    monkeypatch.setattr(review,'llm_chat',lambda *a,**k:response([{'code':'CONCLUSION_REVERSAL','paragraph_id':'p999','reason':'与前文不一致','suggestion':'保持条件'}]))
    assert review.review_answer({'question':'问题','draft':'没有那个段落'})['error']=='UNLOCATABLE_REVIEW'

def test_review_empty_findings_are_not_a_correctness_proof(monkeypatch):
    monkeypatch.setattr(review,'llm_chat',lambda *a,**k:response([]))
    result=review.review_answer({'question':'问题','draft':'有依据的回答'})
    assert not result['requires_revision'] and result['validation_scope']=='reasoning_critique_not_proof'

def test_review_never_silently_truncates():
    assert review.review_answer({'question':'问题','draft':'a'*16001})['error']=='REVIEW_INPUT_TOO_LONG'


def test_review_uses_actual_request_not_a_reframed_question(monkeypatch):
    from deep_context import current_request_question
    seen=[]
    def provider(messages,**kwargs):
        seen.append(json.loads(messages[-1]['content'])['question']);return response([])
    monkeypatch.setattr(review,'llm_chat',provider)
    token=current_request_question.set('全部后果相同，永远不知道动机。')
    try:
        result=review.review_answer({'question':'假如后来发现真相','draft':'草稿'})
    finally:current_request_question.reset(token)
    assert seen==['全部后果相同，永远不知道动机。'] and result['question_source']=='request_context'
