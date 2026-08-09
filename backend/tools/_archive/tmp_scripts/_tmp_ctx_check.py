# -*- coding: utf-8 -*-
"""查看特定行在原始页中的上下文, 确认是页眉/页脚残渣还是正文"""
import json, os, sys, io, re

if sys.platform == "win32":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
    except Exception:
        pass

BASE = r'F:/program/Python/DeepPhilosophy/DeepPhilosophy'
CKPT = os.path.join(BASE, 'backend/data/dp_pdf_import_ckpt.json')
KEY = '西方_格奥尔格_威廉_弗里德里希_黑格尔_精神现象学.pdf'
ck = json.load(open(CKPT, encoding='utf-8'))
pages = ck['ocr'][KEY]

targets = sys.argv[1:] or ['者注', '第六章精神', '1精神现象学', 'a.快乐与必然性']
for tgt in targets:
    print()
    print('===== 「%s」=====' % tgt)
    shown = 0
    for pi in range(len(pages)):
        t = pages.get(str(pi), '')
        if not t or t == '__FAILED__':
            continue
        lines = [l.strip() for l in t.split('\n') if l.strip()]
        for li, ln in enumerate(lines):
            if ln == tgt and shown < 4:
                lo = max(0, li - 2)
                hi = min(len(lines), li + 3)
                print('  [页 %d]' % pi)
                for j in range(lo, hi):
                    mark = '>>' if j == li else '  '
                    print('    %s %s' % (mark, lines[j][:50]))
                print()
                shown += 1
    if shown == 0:
        print('  (未找到)')
