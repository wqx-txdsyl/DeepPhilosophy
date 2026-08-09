# -*- coding: utf-8 -*-
"""39 本 \n 形态统计：每本含 \n\n(段落分隔) 块数 / 纯单 \n 块数 / 行式块候选数 → 建议模式
行式块候选：行数>=3 且 max 行<=20 字
"""
import json, os, sys
sys.stdout.reconfigure(encoding='utf-8')

BC = 'f:/program/Python/PhiAgent/backend/data/book_chapters'
for bid in sorted(os.listdir(BC)):
    d = os.path.join(BC, bid)
    if not os.path.isdir(d) or '_old_bad' in bid or not os.path.exists(os.path.join(d, 'meta.json')):
        continue
    m = json.load(open(os.path.join(d, 'meta.json'), encoding='utf-8'))
    s_dd = s_single = s_line = s_other = 0
    for f in os.listdir(d):
        if not f.endswith('.json') or f == 'meta.json':
            continue
        ch = json.load(open(os.path.join(d, f), encoding='utf-8'))
        for b in ch.get('content', []):
            if b.get('type') != 'text' or '\n' not in b.get('value', ''):
                continue
            v = b['value']
            lines = v.split('\n')
            line_style = len(lines) >= 3 and max(len(l.strip()) for l in lines) <= 20
            if '\n\n' in v:
                s_dd += 1
            elif line_style:
                s_line += 1
            else:
                s_single += 1
            s_other += 1
    if s_other:
        print('%s %-18s 段落型\n\n:%d 单\n:%d 行式:%d' % (bid, m.get('title', '')[:18], s_dd, s_single, s_line))
