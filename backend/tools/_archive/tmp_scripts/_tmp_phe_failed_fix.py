# -*- coding: utf-8 -*-
"""精神现象学 FAILED 页补跑: 对 ckpt 中 __FAILED__ 页重新 OCR, 写回 ckpt
用法: .venv python _tmp_phe_failed_fix.py [--pages 92,94,...]
      --pages 省略则自动找该 PDF 所有 __FAILED__ 页
补完后重跑 _tmp_phe_rebuild.py --apply 吸收新页文本
"""
import json, os, sys, io, re, time

# 注意: 后台重定向时不要包装 stdout (会 I/O closed), 直接 print

BASE = r'F:/program/Python/DeepPhilosophy/DeepPhilosophy'
CKPT_FILE = os.path.join(BASE, 'backend/data/dp_pdf_import_ckpt.json')
KEY = '西方_格奥尔格_威廉_弗里德里希_黑格尔_精神现象学.pdf'
SAFE = re.sub(r"[^\w\-.]", "_", KEY)
PDF = os.path.join(BASE, r'F:/philosophy/西方/格奥尔格·威廉·弗里德里希·黑格尔/精神现象学.pdf')
ZOOM = 1.2

sys.path.insert(0, os.path.join(BASE, 'backend/tools'))
from dp_pdf_import import ocr_page

ckpt = json.load(open(CKPT_FILE, encoding='utf-8'))
done = ckpt['ocr'].get(SAFE, {})

# 目标页: 参数指定或自动找 __FAILED__
if '--pages' in sys.argv:
    targets = [int(x) for x in sys.argv[sys.argv.index('--pages') + 1].split(',')]
else:
    targets = [int(k) for k, v in done.items() if v == '__FAILED__']
    targets.sort()
print('补跑页:', targets)

import fitz
doc = fitz.open(PDF)
total = doc.page_count
print('PDF 页数:', total)
ok = 0
for i in targets:
    if i >= total:
        print('  [%d] 越界, 跳过' % i)
        continue
    pix = doc[i].get_pixmap(matrix=fitz.Matrix(ZOOM, ZOOM))
    tmp = os.path.join(os.environ.get('TEMP', '.'), 'dp_paddle')
    os.makedirs(tmp, exist_ok=True)
    img = os.path.join(tmp, 'phe_fix_p%04d.png' % i)
    pix.save(img)
    t0 = time.time()
    try:
        text = ocr_page(img)
    except Exception as e:
        print('  [%d] OCR 异常: %s' % (i, e))
        continue
    if text and text.strip():
        done[str(i)] = text
        ok += 1
        print('  [%d] ✓ %d 字 (%.1fs)' % (i, len(text), time.time() - t0))
    else:
        print('  [%d] 仍空, 保持 FAILED' % i)
    # 每页写回 (防崩溃丢进度)
    ckpt['ocr'][SAFE] = done
    json.dump(ckpt, open(CKPT_FILE, 'w', encoding='utf-8'), ensure_ascii=False)
    time.sleep(0.1)
doc.close()
print('完成: %d/%d 页补回' % (ok, len(targets)))
