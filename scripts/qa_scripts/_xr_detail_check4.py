# -*- coding: utf-8 -*-
"""三十六计 epub 源内容 + 维特根斯坦注标统计"""
import zipfile, re, json

# 1) 三十六计 epub 源：读出所有文本节点
epub = 'F:/philosophy/东方/佚名/三十六计.epub'
z = zipfile.ZipFile(epub)
print('=== 三十六计.epub 结构 ===')
texts = []
for n in z.namelist():
    if n.endswith(('.html', '.xhtml', '.htm')):
        try:
            t = z.read(n).decode('utf-8', errors='ignore')
            texts.append((n, t))
        except Exception as e:
            print('  读取失败', n, e)
print('html 文件数:', len(texts))
for n, t in texts[:5]:
    # 提取可见文本
    import html as h
    body = re.sub(r'<[^>]+>', '', t)
    body = h.unescape(body).strip()
    print('--- %s (%d字符):' % (n, len(body)))
    print('   ', body[:300].replace('\n', ' | '))
print()

# 2) 维特根斯坦 全书注标"注N"统计
bid = 'c0e78ea6f80a'
import glob, os
files = sorted(glob.glob(f'f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{bid}/[0-9]*.json'),
               key=lambda p: int(re.search(r'(\d+)\.json', p).group(1)))
pat = re.compile(r'注\d+')
total = 0
for f in files:
    n = int(re.search(r'(\d+)\.json', f).group(1))
    c = json.load(open(f, encoding='utf-8'))
    ps = [b.get('value', '').strip() for b in c['content'] if isinstance(b, dict) and isinstance(b.get('value'), str) and b['value'].strip()]
    cnt = sum(len(pat.findall(p)) for p in ps)
    if cnt:
        total += cnt
        print('  章%d: %d 处注标' % (n, cnt))
print('维特根斯坦共 %d 处注N' % total)
# 章数
m = json.load(open(f'f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{bid}/meta.json', encoding='utf-8'))
print('toc 共', len(m['toc']), '条; 无注释章' if not any('注' in (t.get('title') or '') and '释' in (t.get('title') or '') for t in m['toc']) else '')
