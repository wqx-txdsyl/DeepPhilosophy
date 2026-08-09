# -*- coding: utf-8 -*-
"""查看 4 本 1-block 异常章的块值结构 + ckpt OCR 覆盖情况"""
import json, os, re

PA_BC = 'f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters'
CKPT = 'f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/dp_pdf_import_ckpt.json'
ckpt = json.load(open(CKPT, encoding='utf-8'))

targets = {
    '9dc98919ade8': [('18', '思想录 附录三年表'), ('19', '思想录 附录四索引')],
    '88dc7d5961df': [('551', '西方百年 第五章'), ('662', '西方百年 论拓荒移民')],
    'bedc9c78dfdf': [('556', '尼采文集 三'), ('591', '尼采文集 七')],
    '1085686cbd33': [('5', 'MEGA 答布鲁诺·鲍威尔')],
}
# ckpt 里这些书的 rel
rel_map = {}
for rel, info in ckpt.get('books', {}).items():
    b = os.path.join('西方', '东方')
    import hashlib
    bid = hashlib.md5(rel.encode()).hexdigest()[:12]
    if bid in targets:
        rel_map[bid] = rel

print('ckpt books 命中:')
for bid, rel in rel_map.items():
    info = ckpt['books'][rel]
    print('  %s -> %s | chapters=%s | src=%s' % (bid, rel, info.get('chapters'), info.get('src', '')[:30]))
print()
for bid, pairs in targets.items():
    print('=' * 60)
    for idx, label in pairs:
        p = os.path.join(PA_BC, bid, idx + '.json')
        if not os.path.exists(p):
            print('%s [%s] 不存在' % (label, idx))
            continue
        ch = json.load(open(p, encoding='utf-8'))
        blocks = [b for b in ch.get('content', []) if b.get('type') == 'text']
        print('%s [%s] 块数=%d' % (label, idx, len(blocks)))
        for b in blocks[:2]:
            v = b.get('value', '')
            print('  块值 %d 字符 | \\n\\n=%d | \\n=%d | 前60字: %s' % (
                len(v), v.count('\n\n'), v.count('\n'), v[:60].replace('\n', '↵')))
