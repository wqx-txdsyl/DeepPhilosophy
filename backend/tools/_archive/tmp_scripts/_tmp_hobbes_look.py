# -*- coding: utf-8 -*-
"""霍布斯 309K 超大章结构: 章标题列表 + 超长块内容形态（找切章线索）"""
import json, os, hashlib, re

B = 'f:/program/Python/DeepPhilosophy/DeepPhilosophy'
CD = B + '/backend/data/book_chapters'
rel = '西方/托马斯·霍布斯/托马斯•霍布斯.pdf'
bid = hashlib.md5(rel.encode()).hexdigest()[:12]
cdir = os.path.join(CD, bid)
m = json.load(open(os.path.join(cdir, 'meta.json'), encoding='utf-8'))
print('章数:', m['chapterCount'])
for i, t in enumerate(m['chapterTitles']):
    p = os.path.join(cdir, '%d.json' % i)
    ch = json.load(open(p, encoding='utf-8'))
    sz = sum(len(b.get('value', '')) for b in ch.get('content', []) if b.get('type') == 'text')
    print('  %2d %-40s %6d字符' % (i, t[:38], sz))

# 看最大章的块和超长块
max_i = max(range(m['chapterCount']), key=lambda i: sum(len(b.get('value','')) for b in json.load(open(os.path.join(cdir,'%d.json'%i),encoding='utf-8')).get('content',[]) if b.get('type')=='text'))
ch = json.load(open(os.path.join(cdir, '%d.json' % max_i), encoding='utf-8'))
print()
print('=== 最大章 %d: %s ===' % (max_i, ch['title']))
print('块数:', len(ch['content']))
# 超长块前 3 个的内容开头（判断是否整页无换行）
shown = 0
for bi, b in enumerate(ch['content']):
    v = b.get('value', '')
    if len(v) > 2400:
        print('-- 块%d (%d字符): %s...' % (bi, len(v), v[:80].replace('\n', '⏎')))
        shown += 1
        if shown >= 4:
            break
# 章内搜索章标题模式
txt = ''.join(b.get('value','') for b in ch['content'] if b.get('type')=='text')
print()
print('章内"第X卷/章/编"模式:', re.findall(r'第[一二三四五六七八九十百\d]+[卷篇章编]', txt)[:20])
print('章内"目录"出现:', txt.count('目录'))
