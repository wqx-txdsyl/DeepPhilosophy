# -*- coding: utf-8 -*-
"""补查：黑格尔目录章定位 / 尼采 epub 源章标题 / 瓦尔登湖数字形态抽样 / 现象学[13-16]首段"""
import json, os, re, glob, zipfile

def load(bid, n):
    return json.load(open(f'f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{bid}/{n}.json', encoding='utf-8'))

def paras(c):
    return [b.get('value', '').strip() for b in c['content'] if isinstance(b, dict) and isinstance(b.get('value'), str) and b['value'].strip()]

# 1) 黑格尔：找"目录"章——用首段判断（目录列表特征）
bid = 'bbac1be0bb4b'
m = json.load(open(f'f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{bid}/meta.json', encoding='utf-8'))
print('=== 黑格尔 toc 全部 460 条的标题 + 首段前 12 字（可疑的）===')
for t in m['toc']:
    n = t.get('index')
    ti = t.get('title', '')
    try:
        ps = paras(load(bid, n))
    except Exception:
        ps = []
    first = ps[0][:18] if ps else ''
    if (re.search(r'目录|凡例|出版|说明|译者|序', ti) or
        re.search(r'^目\s*录|^凡例|^出版说明', first)):
        print('  [%3d] %-30s %4d段 首段: %s' % (n, ti[:30], len(ps), first))
print()

# 2) 尼采：查 epub 源有没有"第二章/第三章"标题
print('=== 尼采 epub 源扫描 ===')
hits = []
for root, dirs, files in os.walk('F:/philosophy'):
    for f in files:
        if '尼采经典' in f or '尼采经典' in root:
            hits.append(os.path.join(root, f))
for h in hits:
    print('  源:', h)
if hits:
    z = zipfile.ZipFile(hits[0])
    print('  含"第二章"/"第三章"的 html 节点:')
    for n in z.namelist():
        if n.endswith(('.html', '.xhtml', '.htm')):
            t = z.read(n).decode('utf-8', errors='ignore')
            if re.search(r'第[一二三四五]章', t):
                import html as h
                body = re.sub(r'<[^>]+>', '', t)
                body = h.unescape(body).strip()
                body = re.sub(r'\s+', ' ', body)[:80]
                print('    ', n.split('/')[-1], ':', body)
print()

# 3) 瓦尔登湖：数字+空格+中文 形态抽样 20 条
bid = '5135fe68ee4a'
files = sorted(glob.glob(f'f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{bid}/[0-9]*.json'),
               key=lambda p: int(re.search(r'(\d+)\.json', p).group(1)))
pat = re.compile(r'([\u4e00-\u9fff])\s+(\d{1,4})\s+(?=[\u4e00-\u9fff])')
samples = []
total = 0
for f in files:
    c = json.load(open(f, encoding='utf-8'))
    ps = paras(c)
    for p in ps:
        for mm in pat.finditer(p):
            total += 1
            if len(samples) < 24:
                s = p[max(0, mm.start() - 12):mm.end() + 12]
                samples.append(s.replace('\n', ' '))
print('=== 瓦尔登湖 中文+空格+数字+空格+中文: %d 处（抽样24）===' % total)
for s in samples:
    print('    …%s…' % s)
print()

# 4) 现象学 [13][14][15][16] 首段
bid = 'ef76ae88994f'
for n in (13, 14, 15, 16):
    ps = paras(load(bid, n))
    print('=== 现象学 [%d] 课堂讨论 %d段 首段: %s' % (n, len(ps), ps[0][:70] if ps else '空'))
    print('     末段: %s' % (ps[-1][:70] if ps else ''))
