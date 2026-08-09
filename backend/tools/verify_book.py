# -*- coding: utf-8 -*-
"""书重建/修复完成验证: 模拟前端完整读取链 (2026-08-09 皮尔斯三连错后固化)
用法: python verify_book.py <bid> [--vite-check]
检查项:
  1. backend/book_chapters/<bid>/ 文件完整 (meta + 章节 0..N-1)
  2. public 双端 MD5 一致
  3. meta.chapterCount == 章节文件数
  4. meta.toc 必须对象数组 (前端 ChapterReader 按 item.title/item.index 渲染; 字符串数组=目录空白)
  5. meta.chapterTitles 字符串数组且长度 == chapterCount
  6. book_detail/<bid>.json 存在 (详情页目录/摘要来源) 且 toc 同结构
  7. books.json 里该书 chapterCount 一致
  8. --vite-check: curl 5173 meta.json + book_detail 真内容 (vite public 预索引, 新文件须重启 vite)
全部通过才可宣布完成; 任何一项失败 → 修完重跑
"""
import json, hashlib, os, sys, urllib.request

BASE = r'F:/program/Python/DeepPhilosophy/DeepPhilosophy'
BID = sys.argv[1] if len(sys.argv) > 1 else ''
VITE = '--vite-check' in sys.argv
if not BID:
    print('用法: python verify_book.py <bid> [--vite-check]')
    sys.exit(1)

fails = []

def check(name, ok, detail=''):
    if ok:
        print('  ✓ %s%s' % (name, (' — ' + detail if detail else '')))
    else:
        print('  ✗ %s%s' % (name, (' — ' + detail if detail else '')))
        fails.append(name)

print('== 验证 %s ==' % BID)

# 1. 章节文件完整
D = BASE + '/backend/data/book_chapters/%s' % BID
P = BASE + '/app/public/backend/data/book_chapters/%s' % BID
meta = json.load(open(D + '/meta.json', encoding='utf-8'))
n = meta.get('chapterCount', 0)
files = [f for f in os.listdir(D) if f.endswith('.json') and f != 'meta.json']
check('章节文件数 == chapterCount(%d)' % n, len(files) == n, '%d 个文件' % len(files))
missing = [str(i) for i in range(n) if not os.path.exists(D + '/%d.json' % i)]
check('章节 0..%d 齐全' % (n - 1), not missing, '缺: %s' % ','.join(missing) if missing else '')

# 2. 双端 MD5
bad = [f for f in files if hashlib.md5(open(D + '/' + f, 'rb').read()).hexdigest() !=
       hashlib.md5(open(P + '/' + f, 'rb').read()).hexdigest()]
check('public 双端 MD5 一致', not bad, '不一致: %s' % ','.join(bad) if bad else '')

# 3. toc 对象数组 (ChapterReader 目录渲染要求)
# epub 多级 toc: type='part' 分组项(无 index 或 level) + type='chapter' 章节项(index 指向章节文件)
# 检查标准: 对象数组 + chapter 项 index 集合 == 0..N-1 全覆盖; 不要求 len(toc)==N (part 项允许)
toc = meta.get('toc', [])
check('toc 存在', bool(toc), '%d 项' % len(toc))
if toc:
    check('toc 为对象数组 (item.title/item.index)', isinstance(toc[0], dict) and 'title' in toc[0] and 'index' in toc[0],
          repr(toc[0])[:60])
    ch_idx = [it.get('index') for it in toc if isinstance(it, dict) and isinstance(it.get('index'), int)]
    missing = set(range(n)) - set(ch_idx)
    check('toc chapter index 覆盖 0..%d 齐全' % (n - 1), not missing,
          '缺 %s' % sorted(missing)[:6] if missing else '')
    idx_ok = all(isinstance(it.get('index'), int) and 0 <= it.get('index') < n
                 for it in toc if isinstance(it, dict) and 'index' in it)
    check('toc index 均在 [0, %d)' % n, idx_ok)

# 4. chapterTitles
ct = meta.get('chapterTitles', [])
check('chapterTitles 字符串数组且长度 == chapterCount',
      isinstance(ct, list) and all(isinstance(t, str) for t in ct) and len(ct) == n,
      '%d 项' % len(ct))

# 5. book_detail 条目 (详情页 /book_detail/<bid>.json)
bd = BASE + '/app/public/book_detail/%s.json' % BID
if os.path.exists(bd):
    d = json.load(open(bd, encoding='utf-8'))
    dtoc = d.get('toc', [])
    check('book_detail toc 对象数组', bool(dtoc) and isinstance(dtoc[0], dict),
          repr(dtoc[0])[:60] if dtoc else '')
    # book_detail 的 toc 与 meta 同构: chapter 项 index 覆盖一致 (part 项允许)
    dch = [it.get('index') for it in dtoc if isinstance(it, dict) and isinstance(it.get('index'), int)]
    dmiss = set(range(n)) - set(dch)
    check('book_detail toc index 覆盖一致', not dmiss,
          '缺 %s' % sorted(dmiss)[:6] if dmiss else '')
    check('book_detail chapterCount 一致', d.get('chapterCount') == n,
          'detail=%s meta=%s' % (d.get('chapterCount'), n))
    check('book_detail title/author', d.get('title') == meta.get('title') and d.get('author') == meta.get('author'))
else:
    check('book_detail/<bid>.json 存在', False, '缺失 → 详情页无目录')

# 6. books.json
bj = json.load(open(BASE + '/app/public/books.json', encoding='utf-8'))
items = bj if isinstance(bj, list) else bj.get('books', [])
hit = next((it for it in items if it.get('id') == BID), None)
if hit:
    check('books.json chapterCount 一致', hit.get('chapterCount') == n, 'books=%s' % hit.get('chapterCount'))
else:
    check('books.json 有该书条目', False)

# 7. vite 读取链 (可选)
if VITE:
    for path, name in [('/backend/data/book_chapters/%s/meta.json' % BID, '5173 meta.json'),
                       ('/book_detail/%s.json' % BID, '5173 book_detail.json'),
                       ('/backend/data/book_chapters/%s/0.json' % BID, '5173 0.json')]:
        try:
            r = urllib.request.urlopen('http://localhost:5173' + path, timeout=5)
            body = r.read(200)
            check(name, r.status == 200 and not body.startswith(b'<!doctype'), '%dB' % len(body))
        except Exception as e:
            check(name, False, str(e)[:40])
else:
    print('  (跳过 vite 读取链 — 加 --vite-check; 新文件需先重启 vite)')

print()
if fails:
    print('✗ 未通过: %s' % ', '.join(fails))
    sys.exit(1)
print('✓ 全部通过 — 可以宣布完成')
