"""测试单个 EPUB 提取"""
import os, sys, hashlib
sys.path.insert(0, 'backend/tools')
from rebuild_spine import extract

fp = 'F:/philosophy/西方/维特根斯坦/逻辑哲学论-维特根斯坦.epub'
if not os.path.exists(fp):
    search = 'F:/philosophy/西方/维特根斯坦/'
    for f in os.listdir(search):
        if '逻辑哲学论' in f and f.endswith('.epub'):
            fp = os.path.join(search, f)
            break

print('File:', fp)
print('Exists:', os.path.exists(fp))

rel = os.path.relpath(fp, 'F:/philosophy').replace('\\', '/')
bid = hashlib.md5(rel.encode()).hexdigest()[:12]
print('Rel:', rel)
print('ID:', bid)

chs, toc, cover, images = extract(fp, bid)
print('Chapters:', len(chs))
print('TOC:', len(toc))
print('Cover:', cover)
if chs:
    print('First chapter title:', chs[0].get('title', '?')[:50])
