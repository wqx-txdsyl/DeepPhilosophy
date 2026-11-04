#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""39c09 ch5(卷五) 注释迁移 — 2026-11-05 主会话逐块实读定案
结构: 交错页注(TAIL块尾注=注自身标号,最近前驱同号配对)/纯注块/中段注夹断(blk19)
      /头注+正文同块(blk29/44/90)/页眉+页码嵌入14处/星号译者注(blk81)
用法: python3 mig39c09_ch1.py [--write]
"""
import json, re, sys

BID = '39c09c0f8d09'; CH = 5
DP = f'backend/data/book_chapters/{BID}'
MARKS = ''.join(chr(c) for c in range(0x2460, 0x2474))
MR = re.compile('[' + MARKS + ']')
WRITE = '--write' in sys.argv

d = json.load(open(f'{DP}/{CH}.json'))
bs = d['content']
V = [b['value'] for b in bs]
V0 = list(V)
N0 = len(bs)

# ---- 页眉+页码剥离(嵌入句中, 14处) ----
HEADERS = [
]
hdr_hits = []
for i, v in enumerate(V):
    for h in HEADERS:
        if h in v:
            V[i] = v = v.replace(h, '')
            hdr_hits.append((i, h))
print(f'页眉剥离 {len(hdr_hits)} 处: blocks', sorted(set(x[0] for x in hdr_hits)))
assert len(hdr_hits) == len(HEADERS), (len(hdr_hits), len(HEADERS))

A_NOTES = []       # (text, ('NUM', n, atblk) 消费最近前驱同号)
PA_BLOCKS = set()
SKIP = set()
ORPHAN_KEEP = set()

MID = []
HEAD_STRIP = []
TAIL_STRIP = []
# ---- 分类(逐块实读定案) ----
def segs_of(v):
    ms = list(MR.finditer(v))
    out = []
    for j, m in enumerate(ms):
        end = ms[j + 1].start() if j + 1 < len(ms) else len(v)
        out.append({'glyph': m.group(), 'n': MARKS.index(m.group()),
                    's': m.start(), 'e': m.end(), 'body': v[m.end():end]})
    return out

PURE = [3, 5, 8, 10, 13, 21, 25, 27, 30, 31, 33, 34, 35, 40, 41, 44, 47, 48, 54, 55, 60, 63, 70, 71, 79, 84, 86, 90, 91, 94, 96, 99, 104, 109, 111, 112, 115, 117, 123, 124, 128, 138, 158, 159, 162, 170, 172, 176, 177, 179, 180, 183, 185, 190, 194, 197, 202, 203, 209, 213, 216, 222, 223, 226, 227, 230, 232, 238, 240, 241, 246]
TAIL = [2, 4, 7, 9, 12, 15, 16, 18, 20, 22, 24, 26, 29, 32, 37, 39, 43, 46, 51, 52, 53, 58, 59, 62, 66, 68, 72, 74, 77, 78, 83, 87, 93, 95, 106, 108, 110, 113, 116, 119, 121, 122, 127, 130, 132, 135, 136, 137, 139, 140, 142, 144, 150, 155, 156, 157, 161, 169, 173, 174, 175, 178, 181, 182, 184, 186, 187, 188, 189, 192, 193, 195, 196, 200, 201, 206, 208, 211, 212, 214, 215, 218, 220, 221, 224, 225, 228, 229, 231, 234, 235, 236, 237, 239, 242, 243, 245]
TAILN = {}

plan = {}
pending = {}
notes_seq = []
for i, v in enumerate(V):
    if v is None or i in SKIP or i in PA_BLOCKS or i in ORPHAN_KEEP:
        continue
    segs = segs_of(v)
    if i in PURE:
        kinds = [True] * len(segs)
    elif i in TAILN:
        k = TAILN[i]
        kinds = [False] * (len(segs) - k) + [True] * k
    elif i in TAIL:
        kinds = [False] * (len(segs) - 1) + [True]
    else:
        kinds = [False] * len(segs)
    plan[i] = (segs, kinds)
    for j, seg in enumerate(segs):
        if kinds[j]:
            notes_seq.append((seg['n'], i, j, seg['body'].strip()))
        else:
            pending.setdefault(seg['n'], []).append((i, j))

# A 注消费(NUM = 最近前驱同号, ALIAS = 别名位)
def seg_pos(blk, num, atblk, occ=0):
    """在 atblk 的 pending 中找该号(第 occ 枚, 默认最早); 返回 (blk, segj)"""
    lst = pending.get(num) or []
    hits = [x for x in lst if x[0] == atblk]
    assert len(hits) > occ, ('NUM consume', num, atblk, occ, len(hits))
    return hits[occ]

a_pairs = {}
NUM_HITS = []
ALIASAT_POS = {}
for ai, (text, spec) in enumerate(A_NOTES):
    if spec[0] == 'ALIAS':
        _, blk, tok = spec
        p = V[blk].find(tok)
        assert p >= 0, ('alias', blk, tok)
        a_pairs[ai] = ('ALIAS', blk, p)
    elif spec[0] == 'ALIASAT':
        _, pat = spec
        found = None
        for bi, vv in enumerate(V):
            if vv is None:
                continue
            q = vv.find(pat)
            if q >= 0:
                found = (bi, q + len(pat))
                break
        assert found, ('ALIASAT', pat[:16])
        ALIASAT_POS[ai] = found
        a_pairs[ai] = ('DIRECT', found[0], found[1])
    else:
        num, atblk = spec[1], spec[2]
        occ = spec[3] if len(spec) > 3 else 0
        hit = seg_pos(ai, num, atblk, occ)
        pending[num].remove(hit)
        NUM_HITS.append((hit[0], hit[1], num, ('A', ai)))
        a_pairs[ai] = ('DIRECT', hit[0], plan[hit[0]][0][hit[1]]['s'])

# ---- 通用配对(注位置之前最近未用同号 ref) ----
pairs = {}
used = set()
for (k, blk, sj, text) in notes_seq:
    mypos = plan[blk][0][sj]['s']
    lst = pending.get(k) or []
    cand = None
    for idx in range(len(lst) - 1, -1, -1):
        (b2, j2) = lst[idx]
        if lst[idx] in used:
            continue
        p2 = plan[b2][0][j2]['s']
        if (b2, p2) < (blk, mypos):
            cand = lst[idx]; used.add(cand); break
    pairs[('B', blk, sj)] = cand

# ---- 编号(按 ref 正文位置) ----
items = []
for ai, r in a_pairs.items():
    if r is None:
        items.append((None, ('A', ai)))
    else:
        items.append(((r[1], r[2]), ('A', ai)))
owner_lookup = {}
for key, r in pairs.items():
    if r is None:
        items.append((None, key))
    else:
        (blk, j) = r
        items.append(((blk, plan[blk][0][j]['s']), key))
        owner_lookup[(blk, j)] = key

withref = sorted([x for x in items if x[0] is not None], key=lambda x: x[0])
orphan = [x for x in items if x[0] is None]
num_of = {}
notes_final = []
for idx, ((blk, pos), key) in enumerate(withref, start=1):
    num_of[key] = idx
    if key[0] == 'A':
        text = A_NOTES[key[1]][0]
    else:
        text = [x for x in notes_seq if ('B', x[1], x[2]) == key][0][3]
    notes_final.append({'n': idx, 'kind': 'translator', 'text': text})
print(f'有ref注 {len(withref)}  孤注 {len(orphan)}')
for x in orphan:
    print('   ORPHAN', x[1])

# ---- 回写 ----
for i in sorted(plan.keys(), reverse=True):
    segs, kinds = plan[i]
    v = V[i]
    for j in range(len(segs) - 1, -1, -1):
        seg = segs[j]
        end = segs[j + 1]['s'] if j + 1 < len(segs) else len(v)
        if kinds[j]:
            if ('B', i, j) in num_of:
                v = v[:seg['s']] + v[end:]
        else:
            key = owner_lookup.get((i, j))
            if key is not None:
                v = v[:seg['s']] + '{{n:%d}}' % num_of[key] + v[seg['e']:]
    V[i] = v

# A 注 ref 标记 → token
# NUM 消费的 ref 在通用回写中未被 token 化(不在 owner_lookup), 按块内同号序数补替
for (blk, segj, num, key) in NUM_HITS:
    v = V[blk]
    ms = list(MR.finditer(v))
    same = [m for m in ms if MARKS.index(m.group()) == num]
    occ = sum(1 for j, s in enumerate(plan[blk][0]) if j < segj and s['n'] == num)
    m = same[occ]
    V[blk] = v[:m.start()] + '{{n:%d}}' % num_of[key] + v[m.end():]

for ai, (text, spec) in enumerate(A_NOTES):
    if spec[0] == 'ALIASAT':
        _, pat = spec
        r = [x for x in a_pairs.items() if x[1][0] == 'DIRECT' and True]
        # 从 a_pairs 取回记录位置
        pos_rec = ALIASAT_POS[ai]
        blk, pp = pos_rec
        v = V[blk]
        assert v[pp - len(pat):pp] == pat, ('aliasat pos', blk)
        V[blk] = v[:pp] + '{{n:%d}}' % num_of[('A', ai)] + v[pp:]

for ai, (text, spec) in enumerate(A_NOTES):
    if spec[0] == 'ALIAS':
        _, blk, tok = spec
        v = V[blk]
        assert v.count(tok) == 1, ('alias tok', blk, tok)
        V[blk] = v.replace(tok, '{{n:%d}}' % num_of[('A', ai)])

# ============ 级联(倒序应用支持链) ============
CASCADE = [
]
merged = set()
for (a, b) in reversed(CASCADE):
    assert V[a] is not None and V[b] is not None, ('cascade', a, b)
    assert a not in merged, ('double merge', a, b)
    V[a] = V[a] + V[b]
    V[b] = None
    merged.add(a)
    merged.add(b)

# ============ 删除 + 落盘 ============
left = [(i, V[i]) for i, v in enumerate(V) if v is not None and MR.search(v)]
dead = set()
for i, v in enumerate(V):
    if v is None:
        dead.add(i)
    elif not MR.search(v):
        if i in plan and plan[i][0] and not any(plan[i][1]):
            continue
        if v.strip() == '':
            dead.add(i)
for di in sorted(dead, reverse=True):
    del V[di]; del bs[di]
for b, v in zip(bs, V):
    b['value'] = v
d['notes'] = notes_final

for i, v in left:
    m = MR.search(v)
    pp = m.start()
    print(f'残余 orig-blk{i}: …{v[max(0,pp-30):pp+6]}…')
if WRITE:
    with open(f'{DP}/{CH}.json', 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False, indent=1)
    print(f'落盘: notes {len(notes_final)} 条, blocks {N0}→{len(bs)}')
else:
    print(f'DRY: notes {len(notes_final)} 条, blocks {N0}→{len(bs)-len(dead)}')
    print('--- 配对总表(锚前文…【标】 | 注文前40字) ---')
    for idx, ((b, p), key) in enumerate(withref, start=1):
        ctx = V0[b][max(0, p - 16):p]
        if key[0] == 'A':
            t = A_NOTES[key[1]][0] or '(alias)'
        else:
            t = [x for x in notes_seq if ('B', x[1], x[2]) == key][0][3]
        print(f'{idx:3d} blk{b:>3} …{ctx}【】| {t[:40]}')
