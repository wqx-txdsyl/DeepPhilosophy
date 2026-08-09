# -*- coding: utf-8 -*-
"""自然辩证法 切分断裂检测：
1) 下段以接续字/逗号/顿号开头且上段未以句号结尾 → 断段
2) 全角［数字］独立成段统计
3) (N) 半角圆括号注标统计"""
import json, os, re

BID = 'aa21ac425e87'
BASE = f'f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{BID}'

CONT = re.compile(r'^[的了而在并就又以与和或及其它们这那之於于者所把被对从向为给没不无也还]')
PUNCT_HEAD = re.compile(r'^[，。、；：！？）」』】〕）]')

total_break = 0
total_break_ct = {}
fn_standalone = 0      # 全角［N］独立成段
fn_standalone_files = {}
fn_inline = 0          # 行内 (N) 半角注标
fn_inline_files = {}
examples = []

for f in sorted(os.listdir(BASE)):
    if not f.endswith('.json') or f == 'meta.json':
        continue
    c = json.load(open(os.path.join(BASE, f), encoding='utf-8'))
    vals = [b.get('value', '').strip() for b in c['content']
            if isinstance(b, dict) and isinstance(b.get('value', ''), str) and b['value'].strip()]
    # 断段检测
    brk = 0
    for i in range(1, len(vals)):
        prev, cur = vals[i - 1], vals[i]
        # 上段不以句号类结尾（说明句子没完）
        if not prev.endswith(('。', '！', '？', '：', '；', '”', '」', '』')):
            # 下段以接续字或标点开头
            if CONT.match(cur) or PUNCT_HEAD.match(cur) or len(cur) < 12:
                # 排除『［N］』注释段自身（以全角括号开头）
                if not re.match(r'^[［【]?\d+[］】]?$', cur) and not cur.startswith('（'):
                    brk += 1
                    if len(examples) < 15:
                        examples.append((f, prev[-25:], cur[:25]))
    total_break += brk
    if brk:
        total_break_ct[f] = brk
    # 全角［N］独立段
    n1 = sum(1 for v in vals if re.fullmatch(r'［\d+］', v))
    fn_standalone += n1
    if n1:
        fn_standalone_files.setdefault(f, 0)
        fn_standalone_files[f] += n1
    # 行内 (N) 半角注标段
    n2 = sum(1 for v in vals if re.search(r'\([0-9]{1,3}\)', v))
    fn_inline += n2
    if n2:
        fn_inline_files.setdefault(f, 0)
        fn_inline_files[f] += n2

print('=== 断段候选总数:', total_break)
for f, n in sorted(total_break_ct.items(), key=lambda x: -x[1]):
    print(f'  [{f}] {n}')
print('=== 断段样例 ===')
for f, tail, head in examples:
    print(f'  [{f}] …{tail} | {head}…')
print()
print('=== 全角［N］独立成段:', fn_standalone)
for f, n in sorted(fn_standalone_files.items(), key=lambda x: -x[1]):
    print(f'  [{f}] {n}')
print()
print('=== 行内 (N) 注标段:', fn_inline)
for f, n in sorted(fn_inline_files.items(), key=lambda x: -x[1]):
    print(f'  [{f}] {n}')
