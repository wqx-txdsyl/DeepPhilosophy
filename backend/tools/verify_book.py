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
  8. 正文块必须为 dict，type 为阅读器支持的 text/image/html（防缺失类型导致整页崩溃）
  9. 章节内部 index 必须与文件名一致；已声明的 section.sec 不得越界
  9. --vite-check: curl 5173 meta.json + book_detail 真内容 (vite public 预索引, 新文件须重启 vite)
全部通过才可宣布完成; 任何一项失败 → 修完重跑
"""
import json, hashlib, os, sys, urllib.request

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BID = sys.argv[1] if len(sys.argv) > 1 else ''
VITE = '--vite-check' in sys.argv
VITE_BASE = os.environ.get('DP_VITE_BASE', 'http://localhost:5173').rstrip('/')
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
# 实际目录覆盖所有阅读单元；旧标题或旧卷入口保留文件地址，直接跳至对应正文。
redirects = meta.get('chapterRedirects', {})
valid_redirects = isinstance(redirects, dict) and all(
    key.isascii() and key.isdigit() and str(int(key)) == key
    and 0 <= int(key) < n - 1 and type(target) is int
    and int(key) < target < n and str(target) not in redirects
    for key, target in redirects.items()
)
check('旧章节跳转仅指向后续正文且没有链式跳转', valid_redirects)
redirect_slots = {int(key) for key in redirects} if valid_redirects else set()
reading_slots = set(range(n)) - redirect_slots
toc = meta.get('toc', [])
section_redirects = meta.get('chapterTocRedirects', {})
note_redirects = meta.get('chapterNoteRedirects', {})
note_targets = meta.get('chapterNoteTargets', {})
valid_section_redirects = isinstance(section_redirects, dict) and all(
    key in redirects and isinstance(mapping, dict) and bool(mapping)
    and all((old == 'default' or (old.isascii() and old.isdigit() and str(int(old)) == old))
            and type(target) is int and 0 <= target < len(toc)
            and isinstance(toc[target], dict) and toc[target].get('type') == 'section'
            and toc[target].get('index') in reading_slots
            and (old != 'default' or toc[target].get('index') == redirects[key])
            for old, target in mapping.items())
    for key, mapping in section_redirects.items()
)
check('旧目录节跳转仅指向真实正文节', valid_section_redirects)
check('toc 存在', bool(toc), '%d 项' % len(toc))
if toc:
    check('toc 为对象数组 (item.title/item.index)', isinstance(toc[0], dict) and 'title' in toc[0] and 'index' in toc[0],
          repr(toc[0])[:60])
    ch_idx = [it.get('index') for it in toc if isinstance(it, dict) and isinstance(it.get('index'), int)]
    missing = reading_slots - set(ch_idx)
    check('toc 覆盖所有正文索引', not missing,
          '缺 %s' % sorted(missing)[:6] if missing else '')
    check('toc 不包含旧标题占位', redirect_slots.isdisjoint(ch_idx))
    if redirect_slots:
        chapter_entries = {it.get('index') for it in toc if isinstance(it, dict) and it.get('type') == 'chapter'}
        check('旧章节跳转目标在目录中有正文入口', set(redirects.values()) <= chapter_entries)
    idx_ok = all(isinstance(it.get('index'), int) and 0 <= it.get('index') < n
                 for it in toc if isinstance(it, dict) and 'index' in it)
    check('toc index 均在 [0, %d)' % n, idx_ok)

# 4. chapterTitles
ct = meta.get('chapterTitles', [])
check('chapterTitles 字符串数组且长度 == chapterCount',
      isinstance(ct, list) and all(isinstance(t, str) for t in ct) and len(ct) == n,
      '%d 项' % len(ct))
title_mismatches = []
index_mismatches = []
invalid_blocks = []
chapter_lengths = {}
chapter_note_counts = {}
for i in range(n):
    path = D + '/%d.json' % i
    if not os.path.exists(path):
        continue
    with open(path, encoding='utf-8') as f:
        chapter = json.load(f)
    if not isinstance(chapter, dict) or i >= len(ct) or chapter.get('title') != ct[i]:
        title_mismatches.append(i)
    if not isinstance(chapter, dict) or type(chapter.get('index')) is not int or chapter.get('index') != i:
        index_mismatches.append(i)
    content = chapter.get('content') if isinstance(chapter, dict) else None
    chapter_lengths[i] = len(content) if isinstance(content, list) else 0
    notes = chapter.get('notes') if isinstance(chapter, dict) else None
    chapter_note_counts[i] = len(notes) if isinstance(notes, list) else 0
    if not isinstance(content, list) or not content:
        invalid_blocks.append('%d.json: 正文块缺失' % i)
    else:
        for bi, block in enumerate(content):
            if not isinstance(block, dict) or block.get('type') not in {'text', 'image', 'html'}:
                invalid_blocks.append('%d.json:%d 缺少或未知块类型' % (i, bi))
check('meta.chapterTitles 与实际章节标题逐项一致', not title_mismatches,
      '不一致: %s' % title_mismatches[:10] if title_mismatches else '')
check('章节内部 index 与文件名逐项一致', not index_mismatches,
      '不一致: %s' % index_mismatches[:10] if index_mismatches else '')
check('旧注释章节跳转仅指向实际章末注', valid_redirects and isinstance(note_redirects, dict) and all(
    key in redirects and type(note) is int and 1 <= note <= chapter_note_counts.get(redirects[key], 0)
    for key, note in note_redirects.items()
))
check('旧章内注号跳转仅指向实际章末注', isinstance(note_targets, dict) and all(
    key in redirects and isinstance(mapping, dict) and bool(mapping)
    and all(old.isascii() and old.isdigit() and str(int(old)) == old and int(old) > 0
            and isinstance(target, dict) and type(target.get('chapter')) is int
            and target['chapter'] in reading_slots and target['chapter'] > int(key)
            and type(target.get('note')) is int and 1 <= target['note'] <= chapter_note_counts.get(target['chapter'], 0)
            for old, target in mapping.items())
    for key, mapping in note_targets.items()
))

invalid_sections = [ti for ti, item in enumerate(toc) if isinstance(item, dict)
                    and item.get('type') == 'section' and 'sec' in item
                    and (type(item.get('sec')) is not int or item['sec'] < 0
                         or item['sec'] >= chapter_lengths.get(item.get('index'), 0))]
check('已声明的 section.sec 指向实际存在的正文块', not invalid_sections,
      '越界目录项: %s' % invalid_sections[:12] if invalid_sections else '')

check('正文块具有阅读器支持的类型', not invalid_blocks,
      '; '.join(invalid_blocks[:10]))

# 5. book_detail 条目 (详情页 /book_detail/<bid>.json)
bd = BASE + '/app/public/book_detail/%s.json' % BID
if os.path.exists(bd):
    d = json.load(open(bd, encoding='utf-8'))
    dtoc = d.get('toc', [])
    check('book_detail toc 对象数组', bool(dtoc) and isinstance(dtoc[0], dict),
          repr(dtoc[0])[:60] if dtoc else '')
    # book_detail 的 toc 与 meta 同构: chapter 项 index 覆盖一致 (part 项允许)
    dch = [it.get('index') for it in dtoc if isinstance(it, dict) and isinstance(it.get('index'), int)]
    dmiss = reading_slots - set(dch)
    check('book_detail toc index 覆盖一致', not dmiss,
          '缺 %s' % sorted(dmiss)[:6] if dmiss else '')
    check('book_detail 旧章节跳转与 meta 一致', d.get('chapterRedirects', {}) == redirects)
    check('book_detail 旧目录节跳转与 meta 一致', d.get('chapterTocRedirects', {}) == section_redirects)
    check('book_detail 旧注释章节跳转与 meta 一致', d.get('chapterNoteRedirects', {}) == note_redirects)
    check('book_detail 旧章内注号跳转与 meta 一致', d.get('chapterNoteTargets', {}) == note_targets)
    check('book_detail chapterCount 一致', d.get('chapterCount') == n,
          'detail=%s meta=%s' % (d.get('chapterCount'), n))
    check('book_detail chapterTitles 与 meta 逐项一致', d.get('chapterTitles') == ct)
    check('book_detail toc 与 meta 逐项一致', dtoc == toc)
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
    for path, name in [('/backend/data/book_chapters/%s/meta.json' % BID, 'Vite meta.json'),
                       ('/book_detail/%s.json' % BID, 'Vite book_detail.json'),
                       ('/backend/data/book_chapters/%s/0.json' % BID, 'Vite 0.json')]:
        try:
            r = urllib.request.urlopen(VITE_BASE + path, timeout=5)
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
print('✓ 结构和同步检查通过；原文完整性、语言校勘与注释定位仍需对应来源验收')
