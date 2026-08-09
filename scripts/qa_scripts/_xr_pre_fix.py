# -*- coding: utf-8 -*-
"""修复前精查：现象学/尼采 toc 全貌、黑格尔删章候选确认、瓦尔登湖/认识世界注标形态统计"""
import json, os, re, glob

def load(bid, n):
    return json.load(open(f'f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{bid}/{n}.json', encoding='utf-8'))

def paras(c):
    return [b.get('value', '').strip() for b in c['content'] if isinstance(b, dict) and isinstance(b.get('value'), str) and b['value'].strip()]

# 1) 现象学导论七讲 完整 toc + 每章段数
bid = 'ef76ae88994f'
m = json.load(open(f'f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{bid}/meta.json', encoding='utf-8'))
print('=== %s 现象学导论七讲 toc 全 %d 条 ===' % (bid, len(m['toc'])))
for t in m['toc']:
    n = t.get('index')
    try:
        ps = paras(load(bid, n))
    except Exception:
        ps = []
    print('  [%3d] %-34s %d段' % (n, t.get('title', '')[:34], len(ps)))
print()

# 2) 尼采经典著作及研究丛书 完整 toc
bk = json.load(open('f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/books.json', encoding='utf-8'))
nb = next((x for x in bk if '尼采经典' in (x.get('title') or '')), None)
bid = nb['id'] if nb else None
print('=== 尼采经典 bid:', bid, '===')
m = json.load(open(f'f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{bid}/meta.json', encoding='utf-8'))
print('=== %s 尼采经典 toc 全 %d 条 ===' % (bid, len(m['toc'])))
for t in m['toc']:
    print('  [%3d] %s' % (t.get('index'), t.get('title', '')[:50]))
print()

# 3) 黑格尔 删章候选确认：toc 里"目录"/"我馆历来"的章首段
bid = 'bbac1be0bb4b'
m = json.load(open(f'f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{bid}/meta.json', encoding='utf-8'))
print('=== %s 黑格尔：目录类/商务序类/空格标题类 章 ===' % bid)
for t in m['toc']:
    n = t.get('index')
    ti = t.get('title', '')
    try:
        ps = paras(load(bid, n))
    except Exception:
        ps = []
    first = ps[0][:40] if ps else ''
    if re.search(r'目\s*录', ti) or re.search(r'我馆历来', first) or re.match(r'^第\s+一\s+章', ti) or re.match(r'^[A-Z]$', ti):
        print('  [%3d] %-24s %4d段 首段: %s' % (n, ti[:24], len(ps), first))
print()
# 商务序第 1 处是否完整（41 章）
c = load(bid, 41)
ps = paras(c)
print('  [41] 商务序段数:', len(ps), '末段:', ps[-1][:50] if ps else '')
print()

# 4) 瓦尔登湖 数字上标形态统计
bid = '5135fe68ee4a'
files = sorted(glob.glob(f'f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{bid}/[0-9]*.json'),
               key=lambda p: int(re.search(r'(\d+)\.json', p).group(1)))
print('=== %s 瓦尔登湖 数字上标形态 ===' % bid)
pat = re.compile(r'([\u4e00-\u9fff])\s+(\d{1,4})\s+([，。；、：！？）】」』）\n])')
total = 0
samples = []
for f in files:
    c = json.load(open(f, encoding='utf-8'))
    ps = paras(c)
    for p in ps:
        for mm in pat.finditer(p):
            total += 1
            if len(samples) < 12:
                s = p[max(0, mm.start() - 15):mm.end() + 15]
                samples.append(s)
print('  中文+空格+数字+空格+标点 形态: %d 处' % total)
for s in samples:
    print('    …%s…' % s)
# 其他形态：数字前后只有一侧空格
pat2 = re.compile(r'([\u4e00-\u9fff])\s+(\d{1,4})(?!\s*[年月日点时分])')
total2 = 0
for f in files:
    c = json.load(open(f, encoding='utf-8'))
    ps = paras(c)
    for p in ps:
        total2 += len(pat2.findall(p))
print('  中文+空格+数字（后面无 年月日 单位）: %d 处' % total2)
print()

# 5) 认识世界【N】形态统计
bid = 'c97cb4e6161a'
files = sorted(glob.glob(f'f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{bid}/[0-9]*.json'),
               key=lambda p: int(re.search(r'(\d+)\.json', p).group(1)))
print('=== %s 认识世界【N】统计 ===' % bid)
pat = re.compile(r'【\d+】')
total = 0
for f in files:
    c = json.load(open(f, encoding='utf-8'))
    ps = paras(c)
    for p in ps:
        total += len(pat.findall(p))
print('  正文【N】: %d 处' % total)
# 标题里的
m = json.load(open(f'f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{bid}/meta.json', encoding='utf-8'))
t_title = sum(1 for t in m['toc'] if pat.search(t.get('title', '')))
print('  toc 标题含【N】: %d 条' % t_title)
for t in m['toc']:
    if pat.search(t.get('title', '')):
        print('    [%3d] %s' % (t.get('index'), t.get('title')))
# 首段"导言【11】 *"里 * 的形态
c = load(bid, 2)
ps = paras(c)
print('  章2 首段:', repr(ps[0][:60]) if ps else '')
