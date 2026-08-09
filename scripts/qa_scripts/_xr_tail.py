# -*- coding: utf-8 -*-
"""查瓦尔登湖残留 5 段 + 认识世界残留【 2 段"""
import json, os, re, glob

def paras(c):
    return [b.get('value', '').strip() for b in c['content'] if isinstance(b, dict) and isinstance(b.get('value'), str) and b['value'].strip()]

pat = re.compile(r'[\u4e00-\u9fff]\s+\d{1,4}\s+[\u4e00-\u9fff，。]')
for f in glob.glob('f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/5135fe68ee4a/[0-9]*.json'):
    c = json.load(open(f, encoding='utf-8'))
    for b in c['content']:
        if isinstance(b, dict) and pat.search(b.get('value', '')):
            n = int(re.search(r'(\d+)\.json', f).group(1))
            v = b['value'].strip()
            print('=== 瓦尔登湖 章%d 残留段:' % n)
            print('   ', v[:160])

for f in glob.glob('f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/c97cb4e6161a/[0-9]*.json'):
    c = json.load(open(f, encoding='utf-8'))
    for b in c['content']:
        if isinstance(b, dict) and '【' in b.get('value', ''):
            n = int(re.search(r'(\d+)\.json', f).group(1))
            v = b['value'].strip()
            print('=== 认识世界 章%d 残留段:' % n)
            print('   ', v[:160])
