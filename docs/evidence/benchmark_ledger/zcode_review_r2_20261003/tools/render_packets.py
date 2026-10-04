#!/usr/bin/env python3
"""R2 zcode评审：把648份匿名输入包按题渲染成紧凑评审材料。

只做离线抽取，不改任何输入。输出到 backend/tools/_tmp/r2_zcode_work/render/。
"""
import json
import glob
import hashlib
import os
import re
import sys

_d = os.path.dirname(os.path.abspath(__file__))
ROOT = _d
while not os.path.isdir(os.path.join(ROOT, 'docs')):
    ROOT = os.path.dirname(ROOT)
    if ROOT == '/':
        raise SystemExit('repo root not found')
PACKETS = os.path.join(ROOT, 'docs/evidence/benchmark_ledger/review_r2_20261003/full_review/packets')
SUITE = os.path.join(ROOT, 'docs/evidence/phiagent_benchmark_v0_1/suite.json')
OUT = os.path.join(ROOT, 'backend/tools/_tmp/r2_zcode_work/render')


def digest(x, n=160):
    s = json.dumps(x, ensure_ascii=False) if not isinstance(x, str) else x
    s = re.sub(r'\s+', ' ', s)
    return s[:n] + ('…' if len(s) > n else '')


def render_packet(p, pool_ref):
    L = []
    L.append(f"PACKET {p['id']}  family={p['family']}  keys={','.join(p['rating_keys'])}")
    L.append(f"[本轮问题] {p['current_question']}")
    for i, w in enumerate(p.get('task_required_work') or [], 1):
        L.append(f"[必做工作{i}] {w}")
    prev = p.get('previous_turns') or []
    L.append(f"[历史轮数] {len(prev)}")
    for i, t in enumerate(prev, 1):
        q = t.get('question') or t.get('current_question') or ''
        a = t.get('answer') or t.get('target_answer') or ''
        L.append(f"--- 历史第{i}轮用户: {q}")
        L.append(f"--- 历史第{i}轮回答: {a}")
    tools = p.get('tools_this_turn') or []
    L.append(f"[本轮工具回执] {len(tools)} 条")
    for t in tools:
        L.append(f"  #{t.get('tool_index')} {t.get('name')} status={t.get('status')} args={digest(t.get('args'), 140)} result={digest(t.get('result'), 180)}")
    cits = p.get('citations_this_turn') or []
    L.append(f"[本轮引用] {len(cits)} 条")
    for c in cits:
        L.append(f"  {c.get('evidence_id')} {c.get('source_type','')} 《{c.get('book','?')}》{c.get('chapter','')} used={c.get('used')} excerpt={digest(c.get('excerpt',''), 120)}")
    sl = p.get('visible_source_links') or []
    if sl:
        L.append(f"[可见来源链接] {digest(sl, 300)}")
    sm = p.get('visible_search_metadata')
    if sm:
        L.append(f"[可见搜索元数据] {digest(sm, 300)}")
    L.append(f"[共同参考池] {len(p.get('reference_material') or [])} 条 -> 见 {pool_ref}（仅作独立解释核对，不回填执行事实）")
    units = p.get('answer_units') or []
    L.append(f"[待评正文] 共{p.get('answer_char_count', 0)}字，{len(units)}个单位：")
    for u in units:
        L.append(f"  {u['id']}: {u['text']}")
    if not units and (p.get('target_answer') or '').strip():
        L.append(f"  (无单位切分) {p['target_answer']}")
    return '\n'.join(L)


def main():
    suite = json.load(open(SUITE))
    by_prompt = {c['prompt']: c for c in suite['cases']}
    packets = []
    for f in sorted(glob.glob(os.path.join(PACKETS, '*.json'))):
        packets.append(json.load(open(f)))
    # 组：池哈希 + 原始问题
    groups = {}
    for p in packets:
        rh = hashlib.sha256(json.dumps(p.get('reference_material'), ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:10]
        groups.setdefault((rh, p['original_question']), []).append(p)
    case_map = {}
    for (rh, q), ps in sorted(groups.items(), key=lambda kv: kv[0][1]):
        cands = [c for c in suite['cases'] if c['prompt'] == q]
        nturns = len({p['current_question'] for p in ps})
        case = None
        for c in cands:
            fu = c['follow_up_turns'] or []
            if 1 + len(fu) == nturns:
                case = c
                break
        if case is None and len(cands) == 1:
            case = cands[0]
        if case is None:
            raise SystemExit(f'cannot identify case for prompt {q[:40]} turns={nturns}')
        cid = case['id']
        d = os.path.join(OUT, cid)
        os.makedirs(d, exist_ok=True)
        pool_ref = ''
        pool = ps[0].get('reference_material') or []
        if pool:
            pool_ref = f'{cid}/pool.json'
            json.dump(pool, open(os.path.join(d, 'pool.json'), 'w'), ensure_ascii=False, indent=1)
            heads = []
            for i, item in enumerate(pool):
                r = item.get('result') or {}
                heads.append(f"  [{i}] {item.get('type')} tool={item.get('tool')} key={digest({k: r.get(k) for k in ('book_title','quote','found','query','title','url','chapter') if k in r}, 200)}")
            open(os.path.join(d, 'POOL_HEADINGS.txt'), 'w').write('\n'.join(heads))
        ctx = [
            f"CASE {cid}  category={case['category']}  rubric_family={case['rubric_family']}",
            f"[原始提问] {case['prompt']}",
        ]
        for i, fu in enumerate(case['follow_up_turns'] or [], 2):
            ctx.append(f"[第{i}轮追问] {fu}")
        ctx += [
            f"[哲学工作] {case['philosophical_work']}",
            f"[工具要求] {json.dumps(case['tool_expectation'], ensure_ascii=False)}",
            f"[失败信号] " + ' / '.join(case['failure_signals']),
            f"[比较注记] {case['comparison_note']}",
        ]
        open(os.path.join(d, 'CONTEXT.txt'), 'w').write('\n'.join(ctx) + '\n')
        ids = []
        for p in sorted(ps, key=lambda x: x['id']):
            txt = render_packet(p, pool_ref or '（本题为空池）')
            open(os.path.join(d, p['id'] + '.txt'), 'w').write(txt + '\n')
            ids.append(p['id'])
        turns = sorted({p['current_question'] for p in ps})
        case_map[cid] = {'pool_hash': rh, 'packet_ids': ids, 'turn_questions': turns,
                         'family': ps[0]['family'], 'source_file': os.path.relpath(os.path.join(PACKETS, ps[0]['id'] + '.json'), ROOT)}
    json.dump(case_map, open(os.path.join(OUT, '..', 'case_map.json'), 'w'), ensure_ascii=False, indent=1)
    print('cases:', len(case_map), 'packets:', sum(len(v['packet_ids']) for v in case_map.values()))


if __name__ == '__main__':
    main()
