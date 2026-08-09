# -*- coding: utf-8 -*-
"""修复效果抽查：注标删除后正文可读性 + 现象学合并衔接 + 黑格尔商务序保留"""
import json, os, re, glob

def load(bid, n):
    return json.load(open(f'f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{bid}/{n}.json', encoding='utf-8'))

def paras(c):
    return [b.get('value', '').strip() for b in c['content'] if isinstance(b, dict) and isinstance(b.get('value'), str) and b['value'].strip()]

# 1) 哲学书简：章6 首段（原"第六封信：关于长老会注38信徒英国圣公会…"）+ 章26 注释章完好
ps = paras(load('5f838ef64e5e', 6))
print('=== 哲学书简 章6 首段:', ps[0][:70] if ps else '空')
ps = paras(load('5f838ef64e5e', 26))
print('=== 哲学书简 章26 注释章首段:', ps[0][:60] if ps else '空')
rem = 0
for f in glob.glob('f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/5f838ef64e5e/[0-9]*.json'):
    c = json.load(open(f, encoding='utf-8'))
    for b in c['content']:
        if isinstance(b, dict) and re.search(r'注\d+', b.get('value', '')):
            n = int(re.search(r'(\d+)\.json', f).group(1))
            if n < 26:
                rem += 1
print('  章0-25 残留注N 段:', rem)
print()

# 2) 维特根斯坦：章0 首段 + 章1 首段 + 残留
ps = paras(load('c0e78ea6f80a', 0))
print('=== 维特根斯坦 章0 首段:', ps[0][:70] if ps else '空')
ps = paras(load('c0e78ea6f80a', 1))
print('=== 维特根斯坦 章1 首段:', ps[0][:50] if ps else '空')
rem = 0
for f in glob.glob('f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/c0e78ea6f80a/[0-9]*.json'):
    c = json.load(open(f, encoding='utf-8'))
    for b in c['content']:
        if isinstance(b, dict) and re.search(r'注\d+', b.get('value', '')):
            rem += 1
print('  残留注N 段:', rem)
# 逻辑符号完好检查
allv = []
for f in glob.glob('f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/c0e78ea6f80a/[0-9]*.json'):
    c = json.load(open(f, encoding='utf-8'))
    allv.extend(b.get('value', '') for b in c['content'] if isinstance(b, dict))
joined = '\n'.join(allv)
print('  逻辑符号 aRb 保留:', 'aRb' in joined, '| 全称量词 (x).φ(x) 保留:', '(x).' in joined)
print()

# 3) 瓦尔登湖：数字上标删除效果
ps = paras(load('5135fe68ee4a', 0))
print('=== 瓦尔登湖 章0 前3段:')
for p in ps[:3]:
    print('   ', p[:90])
# 检查"空格数字空格"残留
rem = 0
for f in glob.glob('f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/5135fe68ee4a/[0-9]*.json'):
    c = json.load(open(f, encoding='utf-8'))
    for b in c['content']:
        if isinstance(b, dict) and re.search(r'[\u4e00-\u9fff]\s+\d{1,4}\s+[\u4e00-\u9fff，。]', b.get('value', '')):
            rem += 1
print('  残留 中文+空格数字空格 段:', rem)
print()

# 4) 认识世界：章2 首段 + 残留
ps = paras(load('c97cb4e6161a', 2))
print('=== 认识世界 章2 首段:', ps[0][:60] if ps else '空')
rem = 0
for f in glob.glob('f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/c97cb4e6161a/[0-9]*.json'):
    c = json.load(open(f, encoding='utf-8'))
    for b in c['content']:
        if isinstance(b, dict) and '【' in b.get('value', ''):
            rem += 1
print('  残留【 段:', rem)
print()

# 5) 现象学：13 章（合并后）开头+结尾 + 12/13 衔接
ps = paras(load('ef76ae88994f', 13))
print('=== 现象学 章13 (合并后 %d段) 首段: %s' % (len(ps), ps[0][:60] if ps else ''))
print('   末段: %s' % (ps[-1][:60] if ps else ''))
ps12 = paras(load('ef76ae88994f', 12))
print('   章12 末段: %s' % (ps12[-1][:60] if ps12 else ''))
print()

# 6) 黑格尔：章41 商务序保留 + 章1（原42→40?） 重排后检查
ps = paras(load('bbac1be0bb4b', 41))
print('=== 黑格尔 章41 首段:', ps[0][:50] if ps else '空')
print('=== 黑格尔 章0 首段:', paras(load('bbac1be0bb4b', 0))[0][:50] if paras(load('bbac1be0bb4b', 0)) else '')
print('=== 黑格尔 章444 (末) 标题:', [t.get('title') for t in json.load(open('f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/bbac1be0bb4b/meta.json', encoding='utf-8'))['toc'] if t.get('index') == 444])
print()

# 7) 尼采 toc 抽查
m = json.load(open('f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/4cc9d23c7dbf/meta.json', encoding='utf-8'))
print('=== 尼采 toc 前 20 条 ===')
for t in m['toc'][:20]:
    print('  [%3d] %s' % (t.get('index'), t.get('title')))
