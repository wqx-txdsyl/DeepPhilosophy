"""Exercise the actual general-agent tool boundary, with isolated conversation memory.

Live smoke tests are deliberately separate from semantic review: a nonempty
artifact is not proof that its philosophy is sound. Raw results are retained.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from pathlib import Path
import sys
import time

BASE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--workers', type=int, default=2)
    parser.add_argument('--only', nargs='*')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    from engine_langgraph import get_tools
    from deep_agent_tools import search_books
    from deep_context import current_memory_overlay, current_tool_agent, current_request_question
    tools = {t.name: t for t in get_tools('general') if t.name != 'declare_research_need'}
    hit = search_books({'query': '人不知而不愠', 'author': '孔子', 'limit': 1})['results'][0]
    cases = {
        'search_books': {'query': '人不知而不愠', 'author': '孔子'},
        'verify_quote': {'book_id':hit['book_id'],'quote':'人不知而不愠，不亦君子乎'},
        'get_book_detail': {'book_id': hit['book_id']},
        'get_chapter': hit['read_args'],
        'query_graph': {'philosopher': '苏格拉底'},
        'get_philosopher': {'name': '康德'},
        'list_books': {'author': '休谟'},
        'get_school': {'name': '斯多葛主义'},
        'query_database': {'table': 'books', 'key': '论语', 'limit': 3},
        'concept_trace': {'concept': '人不知而不愠'},
        'phti_test': {},
        'analyze_argument': {'text': '所有猫都是动物。所有狗都是动物。所以所有猫都是狗。', 'question': '这个推论有效吗？'},
        'review_answer': {'question':'全部后果相同是否证明价值相同？','draft':'这取决于采用什么价值标准。若承认独立于后果的价值，可能不同。因此不需要任何价值前提就能证明两者价值必然相同。'},
        'paper_review': {'text': '论点：真诚是友谊的必要条件。理由：我认识的真诚的人都有朋友。结论：只要真诚就一定能获得友谊。'},
        'compare_views': {'a': '休谟', 'b': '康德', 'focus': '因果必然性'},
        'socratic_tutor': {'topic': '自由就是可以做任何想做的事'},
        'philosopher_debate': {'topic': '快乐是否足以衡量幸福？', 'speakers': ['亚里士多德', '康德'], 'mode': 'step', 'action': 'start'},
        'thought_experiment': {'base': '甲乙获得的全部短期与长期后果完全相同，且永远不知道帮助者的动机；只有帮助者是否出于善意不同。比较善意的额外价值，不改变给定条件。'},
        'advisor_council': {'question': '我希望兼顾学习与照顾朋友，不替我作决定，请分析可选择的边界。'},
        'profile': {'question': '责任与自由意志有何关系？只讨论本问题反映的研究兴趣，不推断我的性格。'},
        'conceptual_map': {'concept': '推论结构', 'map_type': 'ARGUMENT_GRAPH', 'nodes': ['前提', '结论'], 'relations': [{'from': '前提', 'to': '结论', 'label': '支持'}]},
        'websearch': {'url': 'https://davidhume.org/texts/e/4', 'focus': 'Relations of Ideas'},
        'role_play': {'philosopher': '尼采', 'question': '如何理解自我超越？'},
        'essay_outline': {'topic': '善意与有效帮助的关系，给出两个不同立场及各自前提，不编造出处'},
        'write_essay': {'topic': '善意与有效帮助', 'word_count': 150, 'extra': '只写短文，不编造引文'},
        'life_coach': {'question': '普通日常困扰：朋友总迟到，我怎样表达自己的边界？'},
        'dialectic': {'topic': '自由与规则', 'constraints': '不使用正题反题合题标签，不预设双方必然可以调和'},
        'history_timeline': {'topic': '休谟与康德的因果问题；区别思想影响与直接会面'},
        'confrontation': {'topic': '因果必然性', 'a': '休谟', 'b': '康德'},
        'school_arena': {'topic': '快乐与幸福', 'school_a': '斯多葛主义', 'school_b': '伊壁鸠鲁主义'},
        'agent_council': {'topic': '善意是否足以证明一种帮助是好的？'},
        'generate_image': {'prompt': '测试图：白底上两个黑色圆环相交的极简几何图案，无文字，无人物', 'size': '1K', 'ratio': '1:1'},
        'search_scholarship': {'query': 'Confucian ethics', 'limit': 3},
        'get_scholarly_source': {'source_record_id': 'doi:10.1007/s13347-011-0021-z', 'requested_access': 'FULL_TEXT_IF_LEGALLY_AVAILABLE'},
    }
    missing = sorted(set(tools) - set(cases))
    assert not missing, f'Every registered tool needs a case: {missing}'
    selected = [n for n in tools if not args.only or n in args.only]

    def run(name):
        output = args.output / f'{name}.json'
        if output.exists():
            return json.loads(output.read_text())
        overlay = {'essays': {}, 'image': None, 'experiment': None, 'debate': None, 'socratic': None}
        tokens = [(current_memory_overlay, current_memory_overlay.set(overlay)),
                  (current_tool_agent, current_tool_agent.set('general')),
                  (current_request_question, current_request_question.set(cases[name].get('question') or cases[name].get('base') or cases[name].get('topic') or json.dumps(cases[name], ensure_ascii=False)))]
        start = time.monotonic()
        try:
            result = tools[name].invoke(cases[name])
            status = 'ERROR' if isinstance(result, dict) and (result.get('error') or result.get('accepted') is False) else 'RETURNED'
            row = {'tool': name, 'args': cases[name], 'status': status, 'result': result,
                   'semantic_review': 'PENDING', 'memory_isolated': True}
        except Exception as exc:
            row = {'tool': name, 'args': cases[name], 'status': 'EXCEPTION', 'exception_type': type(exc).__name__,
                   'error': str(exc)[:500], 'semantic_review': 'NOT_APPLICABLE', 'memory_isolated': True}
        finally:
            for var, token in reversed(tokens): var.reset(token)
        row['seconds'] = round(time.monotonic() - start, 3)
        output.write_text(json.dumps(row, ensure_ascii=False, indent=2, default=str))
        return row

    rows = []
    with ThreadPoolExecutor(max_workers=max(1, min(args.workers, 3))) as pool:
        jobs = {pool.submit(run, n): n for n in selected}
        for future in as_completed(jobs):
            row = future.result(); rows.append(row)
            print(row['tool'], row['status'], row.get('seconds'), flush=True)
            (args.output/'index.json').write_text(json.dumps([{k:r[k] for k in ('tool','status','seconds','semantic_review')} for r in rows], ensure_ascii=False, indent=2))
    print('REGISTERED',len(tools),'TESTED',len(rows),'RETURNED',sum(r['status']=='RETURNED' for r in rows),flush=True)


if __name__ == '__main__': main()
