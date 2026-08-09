# -*- coding: utf-8 -*-
"""读资本论 + 康德三本 在库状态 + has_valid_chapters 判定"""
import json, os, hashlib

DP = 'f:/program/Python/DeepPhilosophy/DeepPhilosophy'
bk = json.load(open(os.path.join(DP, 'app/public/books.json'), encoding='utf-8'))
idmap = {b.get('id'): b for b in bk}

def has_valid_chapters(bid):
    """模拟引擎跳过判定"""
    d = os.path.join(DP, 'backend/data/book_chapters', bid)
    if not os.path.isdir(d):
        return False
    m = os.path.join(d, 'meta.json')
    if not os.path.exists(m):
        return False
    meta = json.load(open(m, encoding='utf-8'))
    cc = meta.get('chapterCount') or 0
    files = [f for f in os.listdir(d) if f.endswith('.json') and f != 'meta.json']
    return cc > 0 and len(files) > 0

print('=== 待查书目状态 ===')
checks = [
    ('西方/路易·阿尔都塞/读《资本论》.pdf', '读资本论'),
    ('西方/伊曼努尔·康德/纯粹理性批判.pdf', '纯粹理性批判'),
    ('西方/伊曼努尔·康德/自然科学的形而上学基础.pdf', '自然科学的形而上学基础'),
    ('西方/伊曼努尔·康德/康德三大批判合集（上下）.pdf', '康德三大批判合集'),
]
for rel, name in checks:
    bid = hashlib.md5(rel.encode()).hexdigest()[:12]
    b = idmap.get(bid)
    in_lib = b is not None
    lib_cc = b.get('chapterCount') if b else '-'
    valid = has_valid_chapters(bid)
    print('  %s: bid=%s 库中=%s cc=%s 章节有效=%s' % (name, bid, in_lib, lib_cc, valid))
