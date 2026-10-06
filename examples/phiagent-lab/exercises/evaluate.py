"""Offline mechanical evaluation only. Prints JSON, never calls a real model."""
import asyncio
import json
import time
from phiagent_lab.engine import build_graph, initial_state
from phiagent_lab.model import MockModel

CASES = [
    {'id': 'freedom', 'question': '自由与责任有什么关系？', 'expected': 'demo-freedom'},
    {'id': 'evidence', 'question': '知识与证据', 'expected': 'demo-knowledge'},
    {'id': 'resentment', 'question': '怨恨与价值判断', 'expected': 'demo-resentment'},
    {'id': 'missing', 'question': 'zzzzzzzzz', 'expected': None},
]

async def main():
    graph = build_graph(MockModel())
    results = []
    for case in CASES:
        start = time.perf_counter()
        state = await graph.ainvoke(initial_state(case['question']))
        expected = case['expected']
        passed = (expected in state['evidence'] and f'[{expected}]' in state['answer']) if expected else not state['evidence']
        results.append({'id': case['id'], 'passed': passed, 'rounds': state['rounds'],
                        'elapsed_ms': round(1000 * (time.perf_counter() - start), 2),
                        'answer': state['answer']})
    print(json.dumps({'mode': 'mock', 'scope': 'mechanical, NOT model quality', 'results': results}, ensure_ascii=False, indent=2))
    if not all(row['passed'] for row in results):
        raise SystemExit(1)

if __name__ == '__main__':
    asyncio.run(main())
