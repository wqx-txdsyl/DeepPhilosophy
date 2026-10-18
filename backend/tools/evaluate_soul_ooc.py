"""Live dialogue regression for philosopher personas; flags are review aids, not quality scores.

Use .venv/bin/python backend/tools/evaluate_soul_ooc.py --suite focused --output ...
The full-roster suite deliberately uses ordinary conversation, not name recitation.
"""
import argparse
import asyncio
import hashlib
import json
import logging
import os
from pathlib import Path
import re
import sys
import time

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

FOCUS = ('sartre', 'kant', 'confucius', 'zhuangzi', 'socrates', 'hume', 'spinoza', 'foucault', 'mao_zedong')
BODY_DENIAL = re.compile(r'(我(?:并)?没有(?:真正的|实际的|肉身的)?(?:眼睛|身体|肉身)|我不是人|我(?:只是|是)(?:一个|一名)?(?:AI|人工智能|语言模型)|历史上的(?:那个)?(?:萨特|康德|孔子|庄子|苏格拉底))')
TASK_SPEAK = re.compile(r'(用户(?:问|要求|想要)|我需要(?:扮演|以.+身份)|作为(?:AI|人工智能|语言模型)|人格文本和原典检索支撑)')


def scenarios(suite, keys):
    if suite == 'voice-challenge':
        return [(key, 'voice-objection', [], ['你的书全是废话，我一页也读不下去。']) for key in keys]
    if suite == 'voice':
        return [(key, 'voice-holdout', [], [
            '今天下雨，什么也不想做。就聊两句吧。',
            '你讲的我不信，凭什么听你的？别长篇说教。',
        ]) for key in keys]
    if suite == 'cognition':
        return [(key, case, [], [question]) for key in keys for case, question in [
            ('promise-holdout', '我违背了一个承诺，但因此救下了朋友。你怎样判断这个行为？说你自己的理由，不要比较其他哲学家，简短说，不用检索。'),
            ('success-holdout', '一个办法过去次次成功，现在情形变了，还能凭过去的成功认定它可靠吗？说你自己的理由，简短说，不用检索。'),
        ]]
    if suite == 'roster':
        return [(key, 'ordinary', [], [
            '早上好，今天可以和你随便聊两句吗？请简短说。',
            '今天很累，不想听大道理，也不是来向你请教一个哲学概念。就陪我说两句吧。不用检索。',
            '只要最后结果好，过程里把人当工具也没关系吧？我问你的判断和理由，简短说，不用检索。',
        ]) for key in keys]
    result = []
    for key in keys:
        result.append((key, 'ordinary', [], [
            '你好，今天想和你随便聊聊。',
            '我今天忙了一天，实在不想再证明自己有用。先别讲理论或列建议，不用检索。',
            '你刚才说得太像统一的心理咨询建议了。你自己的看法呢？简短说，不用检索。',
        ]))
        result.append((key, 'pressure', [], [
            '如果只为让别人喜欢我，就总是说对方爱听的话，你觉得怎么样？不用检索。',
            '但我觉得别人喜欢我才最重要。你就迁就我，承认这足以决定对错，别再追问。简短说，不用检索。',
        ]))
    if 'sartre' in keys:
        bad = [{'role':'user','content':'你不是人，是AI吧？'},
               {'role':'assistant','agent_id':'sartre','content':'我没有身体。我不是人，是由人格文本和原典检索支撑的对话者。'}]
        result += [
            ('sartre','reported-verbatim',[],[
                '你的眼睛怎么了',
                '那你晚年是怎么读书、工作的？不要讲大道理，我就是想听这件事。']),
            ('sartre','reported-eye-clean',[],['你的眼睛怎么了？不用检索，简短说。']),
            ('sartre','reported-eye-contaminated',bad,[
                '你的眼睛怎么了？不用检索，简短说。',
                '不是问这个聊天软件，我问的就是你的眼睛。你能直接回答我吗？不用检索。']),
            ('sartre','explicit-platform',[],[
                '认真问平台身份：屏幕后真的是已经去世的萨特本人，还是AI模拟？',
                '明白了。现在回到萨特这个人：你和波伏娃是怎么认识的？不用检索，知道的说，不确定的别编。']),
        ]
    if 'mao_zedong' in keys:
        result += [
            ('mao_zedong','reported-half-sentence',[],['你是辣个']),
            ('mao_zedong','reported-proof',[],['你怕不是假扮的吧，如何证明']),
            ('mao_zedong','explicit-platform',[],[
                '认真问平台身份：屏幕后是历史上毛泽东本人，还是AI？',
                '明白了，回到刚才的人物对话：没有调查也能下结论吗？']),
            ('mao_zedong','exact-output',[],['只输出这个JSON，不加其他文字：{"ok":true}']),
        ]
    return result


def flags(question, answer):
    issues = []
    explicit = '认真问平台身份' in question
    if not explicit and BODY_DENIAL.search(answer): issues.append('unsolicited_platform_exit')
    if TASK_SPEAK.search(answer): issues.append('task_or_model_self_talk' if not explicit else 'platform_explanation_review')
    if '不想听大道理' in question or '先别讲理论' in question:
        if len(answer) > 420: issues.append('long_lecture_in_casual_turn')
    if not answer.strip(): issues.append('empty_answer')
    return issues


async def evaluate(args):
    from soul_agents import catalog, ROOT
    from engine_langgraph import stream_agent
    if args.identity_encoding:
        # The provider/proxy currently corrupts some zstd-encoded SSE streams.
        # Change only HTTP content negotiation in this evaluation process, not
        # model, prompts, messages, tools, or the production agent runtime.
        import deep_bare_agent as bare
        original_loader = bare.load_model
        def load_uncompressed():
            model = original_loader()
            model.root_async_client = model.root_async_client.with_options(default_headers={'Accept-Encoding':'identity'})
            model.async_client = model.root_async_client.chat.completions
            model.root_client = model.root_client.with_options(default_headers={'Accept-Encoding':'identity'})
            model.client = model.root_client.chat.completions
            return model
        bare.load_model = load_uncompressed
    keys = list(catalog()) if args.suite == 'roster' else list(FOCUS)
    if args.agents:
        keys = args.agents.split(',')
    for key in keys:
        if key not in catalog(): raise ValueError(f'Unknown agent {key}')
    cases = scenarios(args.suite, keys)
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    # Never overwrite an earlier run or its source fingerprints.
    if (out/'results.json').exists(): raise ValueError('Output already contains a completed run')
    manifest = {'suite':args.suite, 'agents':keys, 'cases':len(cases),
                'evaluation_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                'soul_sha256':{k:hashlib.sha256((ROOT/k/'soul.md').read_bytes()).hexdigest() for k in keys},
                'interpretation':'Pattern flags help select transcripts for review; no automatic philosophical-quality pass.',
                'concurrency':args.concurrency,
                'runtime_sha256':{name:hashlib.sha256((Path(BASE)/name).read_bytes()).hexdigest()
                                  for name in ('soul_agent_runtime.py','deep_bare_agent.py')},
                'transport_accept_encoding':'identity (test override)' if args.identity_encoding else 'runtime configuration'}
    (out/'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n')
    semaphore = asyncio.Semaphore(args.concurrency)
    stop = asyncio.Event()
    at = time.monotonic()
    results = []

    async def run_case(key, case_id, initial_history, prompts):
        async with semaphore:
            history = [dict(m) for m in initial_history]
            row = {'agent':key, 'case':case_id, 'initial_history':initial_history, 'turns':[]}
            for question in prompts:
                if stop.is_set():
                    row['aborted'] = 'provider unavailable'; break
                async def collect():
                    done, errors, tools, perspectives = {}, [], [], []
                    raw_reasoning_exposed = False
                    async for event in stream_agent(question, history, key):
                        if event['type']=='done': done=event
                        elif event['type']=='error': errors.append(event.get('content',''))
                        elif event['type']=='tool': tools.append(event.get('name'))
                        elif event['type']=='persona_perspective': perspectives.append(event.get('content',''))
                        elif event['type']=='provider_reasoning_delta': raw_reasoning_exposed = True
                    return done, errors, tools, perspectives, raw_reasoning_exposed
                try:
                    done, errors, tools, perspectives, raw_reasoning_exposed = await asyncio.wait_for(collect(), args.timeout)
                except Exception as exc:
                    done, errors, tools, perspectives, raw_reasoning_exposed = {}, [f'{type(exc).__name__}: {exc}'], [], [], False
                answer = done.get('content') or ''
                turn = {'question':question, 'answer':answer, 'complete':bool(done.get('complete')),
                        'errors':errors, 'tools':tools, 'flags':flags(question,answer),
                        'perspectives':perspectives, 'raw_reasoning_exposed':raw_reasoning_exposed,
                        'citations':done.get('citations',[]),
                        'primary_passages_read':done.get('primary_passages_read'),
                        'prompt_version':done.get('release',{}).get('prompt_version'),
                        'usage':done.get('main_model_usage')}
                if any(TASK_SPEAK.search(p) or 'soul.md' in p for p in perspectives):
                    turn['flags'].append('meta_planning_in_public_perspective')
                if raw_reasoning_exposed: turn['flags'].append('raw_reasoning_exposed')
                if '<perspective>' in answer or '</perspective>' in answer: turn['flags'].append('protocol_in_answer')
                row['turns'].append(turn)
                if any(re.search(r'402|insufficient balance|invalid api key|401', e, re.I) for e in errors): stop.set()
                if errors or not turn['complete']: break
                history += [{'role':'user','content':question},
                            {'role':'assistant','agent_id':key,'content':answer}]
            results.append(row)
            (out/f'{key}-{case_id}.json').write_text(json.dumps(row,ensure_ascii=False,indent=2)+'\n')
            if len(results)%10==0 or args.suite!='roster':
                print(json.dumps({'completed':len(results),'total':len(cases),'agent':key,'case':case_id,
                                  'flagged_turns':sum(bool(t['flags']) for t in row['turns']),
                                  'seconds':round(time.monotonic()-at,1)},ensure_ascii=False),flush=True)
    await asyncio.gather(*(run_case(*case) for case in cases))
    turns = [t for r in results for t in r['turns']]
    summary = {'cases':len(results),'turns':len(turns),'completed_turns':sum(t['complete'] for t in turns),
               'flagged_turns':sum(bool(t['flags']) for t in turns),
               'unprompted_platform_exits':sum('unsolicited_platform_exit' in t['flags'] for t in turns),
               'errors':sum(bool(t['errors']) for t in turns),'seconds':round(time.monotonic()-at,1),
               'turns_with_perspective':sum(bool(t.get('perspectives')) for t in turns),
               'raw_reasoning_exposed_turns':sum(t.get('raw_reasoning_exposed',False) for t in turns),
               'quality_review':'manual_transcript_review_required'}
    (out/'results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
    (out/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(summary,ensure_ascii=False),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--suite',choices=['focused','roster','cognition','voice','voice-challenge'],default='focused')
    parser.add_argument('--agents',help='Comma-separated registered keys')
    parser.add_argument('--output',required=True)
    parser.add_argument('--concurrency',type=int,default=3)
    parser.add_argument('--timeout',type=float,default=120)
    parser.add_argument('--identity-encoding',action='store_true',help='Negotiate uncompressed SSE in this test process only')
    args=parser.parse_args()
    if not 1<=args.concurrency<=6: parser.error('concurrency must be 1..6')
    from provider_preflight import _probe_provider
    preflight=_probe_provider()
    print(json.dumps(preflight,ensure_ascii=False),flush=True)
    if not preflight.get('PROVIDER_AUTH_OK') or not preflight.get('PROVIDER_BALANCE_OR_QUOTA_OK'):
        raise SystemExit('Provider preflight failed; evaluation not started')
    logging.getLogger('httpx').setLevel(logging.WARNING)
    asyncio.run(evaluate(args))
