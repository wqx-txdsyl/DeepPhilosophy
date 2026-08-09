# -*- coding: utf-8 -*-
"""对账: ckpt books(已入库) vs OCR清单(_todo_ocr_list.md) → 找出待检查/待补跑/新入库书"""
import json, re, hashlib

B = r'F:\program\Python\DeepPhilosophy\DeepPhilosophy'
CK = json.load(open(B + r'\backend\data\dp_pdf_import_ckpt.json', encoding='utf-8'))
books = CK['books']

# 解析清单
md = open(B + r'\scripts\qa_scripts\_todo_ocr_list.md', encoding='utf-8').read()
sections = {}
cur = None
for line in md.splitlines():
    m = re.match(r'^## (.+)$', line)
    if m:
        cur = m.group(1)
        sections.setdefault(cur, [])
    elif cur and line.startswith('- [') and '.pdf' in line:
        rel = re.search(r'\s*(\S+?\.pdf)', line)
        if rel:
            sections[cur].append(rel.group(1).strip())

print('=== 清单各区书目 ===')
for k, v in sections.items():
    print('%s: %d 本' % (k, len(v)))

all_list = set()
for v in sections.values():
    all_list.update(v)

done = set(books.keys())
print()
print('=== ckpt 已入库 %d 本 ===' % len(done))

# 1. 清单中已入库 → 需要检查
in_list_and_done = sorted(all_list & done)
print()
print('=== 清单中已入库(需检查) %d 本 ===' % len(in_list_and_done))
for r in in_list_and_done:
    print('  [%s] %s' % (books[r].get('src', '?'), r))

# 2. 已入库但不在清单(新书/未登记)
new_done = sorted(done - all_list)
print()
print('=== 已入库但不在清单(新) %d 本 ===' % len(new_done))
for r in new_done:
    print('  [%s] %s' % (books[r].get('src', '?'), r))

# 3. 清单中未入库(待跑/未完成)
pending = sorted(all_list - done)
print()
print('=== 清单中未入库(待跑) %d 本 ===' % len(pending))
for r in pending:
    print('  %s' % r)
