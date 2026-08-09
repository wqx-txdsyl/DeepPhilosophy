# -*- coding: utf-8 -*-
"""分析页眉/页脚残渣在原始页中的分布, 确认清洗规则"""
import json, os, sys, io, re
from collections import Counter, defaultdict

if sys.platform == "win32":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
    except Exception:
        pass

BASE = r'F:/program/Python/DeepPhilosophy/DeepPhilosophy'
CKPT = os.path.join(BASE, 'backend/data/dp_pdf_import_ckpt.json')
KEY = '西方_格奥尔格_威廉_弗里德里希_黑格尔_精神现象学.pdf'
ck = json.load(open(CKPT, encoding='utf-8'))
pages = ck['ocr'][KEY]
n = len(pages)
print('总页数:', n)

# 1. 页眉候选行: 出现页数 >= 3 的短行
line_pages = defaultdict(set)   # 行文本 -> 出现页集合
line_cnt = Counter()
for pi in range(n):
    t = pages.get(str(pi), '')
    if not t or t == '__FAILED__':
        continue
    for ln in t.split('\n'):
        ln = ln.strip()
        if not ln:
            continue
        line_pages[ln].add(pi)
        line_cnt[ln] += 1

print()
print('== 出现页数 >= 3 的短行 (页眉候选) ==')
cands = sorted([(ln, len(ps), line_cnt[ln]) for ln, ps in line_pages.items() if len(ps) >= 3 and len(ln) < 12],
               key=lambda x: -x[1])
for ln, npg, cnt in cands[:25]:
    pages_sample = sorted(list(line_pages[ln]))[:6]
    print('  %-16s 页数:%3d 次数:%3d  例页:%s' % (repr(ln), npg, cnt, pages_sample))

# 2. 独立数字行 (页脚页码候选) 分布
print()
print('== 纯数字独立行 (页脚页码候选) ==')
digit_cnt = Counter()
digit_pages = defaultdict(list)
for pi in range(n):
    t = pages.get(str(pi), '')
    if not t or t == '__FAILED__':
        continue
    for ln in t.split('\n'):
        ln = ln.strip()
        if re.fullmatch(r'\d{1,3}', ln):
            digit_cnt[ln] += 1
            if len(digit_pages[ln]) < 3:
                digit_pages[ln].append(pi)
print('  数字行种类: %d, 总次数: %d' % (len(digit_cnt), sum(digit_cnt.values())))
for ln, c in digit_cnt.most_common(15):
    print('  「%s」 %d 次, 例页:%s' % (ln, c, digit_pages[ln]))

# 3. 单行文本重复率最高行 (含长行, 找出所有页眉)
print()
print('== 全部重复行 (>=3 页), 含长行 ==')
long_cands = sorted([(ln, len(ps)) for ln, ps in line_pages.items() if len(ps) >= 3],
                    key=lambda x: -x[1])
for ln, npg in long_cands[:40]:
    print('  页数:%3d  「%s」' % (npg, ln[:40]))
print('共 %d 种' % len(long_cands))
