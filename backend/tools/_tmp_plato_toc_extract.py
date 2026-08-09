# -*- coding: utf-8 -*-
"""提取柏拉图目录页 + 正文篇目标题, 建立重切清单"""
import json, os, re

CD = r'F:\program\Python\DeepPhilosophy\DeepPhilosophy\backend\data\book_chapters\35279e2e439d'

# 1. 目录页全文 (在 2.json)
ch2 = json.load(open(os.path.join(CD, '2.json'), encoding='utf-8'))
toc_text = ''
for b in ch2.get('content', []):
    v = b.get('value', '')
    if '目录' in v and '篇' in v and len(v) < 800:
        toc_text += v + '\n'
print('=== 目录页原文 ===')
print(toc_text)

# 2. 正文篇目标题: 块内 "X篇" 行首短行
title_pat = re.compile(r'^([\u4e00-\u9fff·]{2,8}篇)(?:[（\(]|$)')
for fi in (3, 4):
    ch = json.load(open(os.path.join(CD, '%d.json' % fi), encoding='utf-8'))
    print()
    print('=== %d.json 篇目标题行 ===' % fi)
    for bi, b in enumerate(ch.get('content', [])):
        v = b.get('value', '')
        for line in v.split('\n'):
            m = title_pat.match(line.strip())
            if m:
                print('  块%4d %r' % (bi, line.strip()[:40]))
