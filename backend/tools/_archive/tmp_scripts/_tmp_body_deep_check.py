# -*- coding: utf-8 -*-
"""正文深度检查: 页眉残留/孤立字符/超长段/段尾句号/FAILED 页空洞
用法: python _tmp_body_deep_check.py <bid> [--all]   (--all 列出全部段落统计)
"""
import json, os, sys, io, re

if sys.platform == "win32":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
    except Exception:
        pass

BASE = r'F:/program/Python/DeepPhilosophy/DeepPhilosophy'
BID = sys.argv[1]
ALL = '--all' in sys.argv
D = os.path.join(BASE, 'backend/data/book_chapters', BID)
meta = json.load(open(os.path.join(D, 'meta.json'), encoding='utf-8'))
n = meta.get('chapterCount', 0)

print('== 正文深度检查 %s (%s) %d 章 ==' % (meta.get('title'), BID, n))

# 页眉/标题残留模式: 书眉在正文中的特征 = 独立短行重复出现
line_counter = {}
for i in range(n):
    ch = json.load(open(os.path.join(D, '%d.json' % i), encoding='utf-8'))
    for b in ch.get('content', []):
        if isinstance(b, dict) and b.get('type') == 'text':
            for ln in b.get('value', '').split('\n'):
                ln = ln.strip()
                if ln:
                    line_counter[ln] = line_counter.get(ln, 0) + 1

# 高频重复短行 = 页眉残留候选 (出现 >= 4 次且 < 12 字)
print()
print('== 高频重复短行 (>=4 次, 页眉残留候选) ==')
sus = [(ln, c) for ln, c in line_counter.items() if c >= 4 and len(ln) < 12]
sus.sort(key=lambda x: -x[1])
for ln, c in sus[:20]:
    print('  %3d 次  「%s」' % (c, ln))
if not sus:
    print('  无')

# FAILED 页空洞
CKPT = os.path.join(BASE, 'backend/data/dp_pdf_import_ckpt.json')
failed = []
if os.path.exists(CKPT):
    try:
        ck = json.load(open(CKPT, encoding='utf-8'))
        pages = ck['ocr'].get('西方_格奥尔格_威廉_弗里德里希_黑格尔_精神现象学.pdf', {})
        failed = [int(k) for k, v in pages.items() if v == '__FAILED__']
        failed.sort()
        print()
        print('== FAILED 页 (OCR 失败空洞, %d 页) ==' % len(failed))
        for f in failed:
            print('  页 %d' % f)
    except Exception as e:
        print('ckpt 读取失败:', e)

# 段落结构: 超长段/段尾非句号
print()
print('== 段落结构 ==')
total_para = 0
total_chars = 0
long_paras = []  # (章, 段号, 长度, 段尾8字)
bad_ends = []    # (章, 段号, 段尾20字) 段尾非句号/引号
for i in range(n):
    ch = json.load(open(os.path.join(D, '%d.json' % i), encoding='utf-8'))
    for k, b in enumerate(ch.get('content', [])):
        if not (isinstance(b, dict) and b.get('type') == 'text'):
            continue
        v = b.get('value', '').strip()
        if not v:
            continue
        total_para += 1
        total_chars += len(v)
        if len(v) > 800:
            long_paras.append((i, k, len(v), v[-8:]))
        tail = v[-1]
        if tail not in '。！？…”」】：；，、—-—':
            bad_ends.append((i, k, v[-24:]))

print('总段落: %d, 总字数: %d' % (total_para, total_chars))
print('超长段 (>800 字): %d 个' % len(long_paras))
for i, k, ln, tail in long_paras[:10]:
    print('  [%d] 段%d  %d 字  尾:…%s' % (i, k, ln, tail))
print('段尾非句号: %d 个 (样本)' % len(bad_ends))
for i, k, tail in bad_ends[:15]:
    print('  [%d] 段%d  …%s' % (i, k, tail))

# 孤立字符/残字: 单字段落 或 1-2 字独立行
print()
print('== 孤立残字 (1-2 字段落) ==')
tots = {}
for i in range(n):
    ch = json.load(open(os.path.join(D, '%d.json' % i), encoding='utf-8'))
    for k, b in enumerate(ch.get('content', [])):
        if isinstance(b, dict) and b.get('type') == 'text':
            v = b.get('value', '').strip()
            if v and len(v) <= 2:
                tots[(i, k)] = v
if tots:
    for (i, k), v in list(tots.items())[:15]:
        print('  [%d] 段%d  「%s」' % (i, k, v))
    print('  共 %d 处' % len(tots))
else:
    print('  无')

# 章内独立短行分布 (全书书的书名作为页眉: 精神现象学/黑格尔 出现位置)
print()
print('== 书名/作者名独立行出现 (页眉残留, 应为 0) ==')
hit = {}
for ln, c in line_counter.items():
    if '精神现象学' == ln or ln in ('格奥尔格·威廉·弗里德里希·黑格尔', '黑格尔'):
        hit[ln] = c
if hit:
    for ln, c in hit.items():
        print('  「%s」 %d 次' % (ln, c))
else:
    print('  无 — 页眉已全部清洗')
