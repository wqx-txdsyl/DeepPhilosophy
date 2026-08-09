# -*- coding: utf-8 -*-
"""自然辩证法 [num] 残留形态统计：
1) 全角［N］段尾（A修复后）/段中
2) 半角 [N]（段中/段尾/段首）
3) 半角 (N)（行内注标）
4) 注文形态（'——N。' '编者注' 等）"""
import json, os, re

BASE = 'f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/aa21ac425e87'

FULL_TAIL = re.compile(r'［\d+］$')      # 段尾全角
FULL_MID = re.compile(r'［\d+］')        # 段中/段尾全角（任意位置）
HALF = re.compile(r'\[\d{1,4}\]')        # 半角 [N]
HALF_HEAD = re.compile(r'^\[\d{1,4}\]')  # 段首半角
PAREN = re.compile(r'\(\d{1,3}\)')       # 半角圆括号 (N)
NOTE_MARK = re.compile(r'——\d{1,3}。|编者注|原编者注')  # 注文结尾标记

tot = {'full': 0, 'half': 0, 'half_head': 0, 'paren': 0, 'notemark': 0}
per_file = {}
examples = {'full': [], 'half': [], 'paren': []}
for f in sorted(os.listdir(BASE), key=lambda x: int(x.split('.')[0]) if x.endswith('.json') and x != 'meta.json' else 99):
    if not f.endswith('.json') or f == 'meta.json':
        continue
    c = json.load(open(os.path.join(BASE, f), encoding='utf-8'))
    for b in c['content']:
        v = b.get('value', '') if isinstance(b, dict) else ''
        if not isinstance(v, str):
            continue
        nf = len(FULL_MID.findall(v))
        nh = len(HALF.findall(v))
        nhh = 1 if HALF_HEAD.match(v.strip()) else 0
        np = len(PAREN.findall(v))
        nm = 1 if NOTE_MARK.search(v) else 0
        tot['full'] += nf; tot['half'] += nh; tot['half_head'] += nhh; tot['paren'] += np; tot['notemark'] += nm
        per_file.setdefault(f, [0, 0, 0, 0, 0])
        per_file[f][0] += nf; per_file[f][1] += nh; per_file[f][2] += nhh; per_file[f][3] += np; per_file[f][4] += nm
        if nf and len(examples['full']) < 8:
            m = FULL_MID.search(v)
            examples['full'].append(v[max(0, m.start() - 12):m.end() + 6])
        if nh and len(examples['half']) < 10:
            m = HALF.search(v)
            examples['half'].append(v[max(0, m.start() - 12):m.end() + 8])
        if np and len(examples['paren']) < 8:
            m = PAREN.search(v)
            examples['paren'].append(v[max(0, m.start() - 12):m.end() + 10])

print('=== 全局统计 ===')
print(f'  全角［N］(段中/段尾): {tot["full"]}')
print(f'  半角 [N]: {tot["half"]}（其中段首: {tot["half_head"]}）')
print(f'  半角 (N): {tot["paren"]}')
print(f'  注文标记(——N。/编者注): {tot["notemark"]}')
print()
print('=== 各章分布（全角/半角[ ]/半角( )/注文标记）===')
for f, (a, b, hh, p, nm) in sorted(per_file.items(), key=lambda x: -(x[1][0] + x[1][1] + x[1][3])):
    print(f'  [{f[:-5]:>2}] 全角{a:>3} 半角[{b:>3}] (N){p:>3} 注文{nm:>3}')
print()
print('=== 全角［N］样本 ===')
for s in examples['full']:
    print('  …', s)
print()
print('=== 半角 [N] 样本 ===')
for s in examples['half']:
    print('  …', s)
print()
print('=== 半角 (N) 样本 ===')
for s in examples['paren']:
    print('  …', s)
