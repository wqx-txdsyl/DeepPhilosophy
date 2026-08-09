# -*- coding: utf-8 -*-
"""OCR 4 本系列书 + 3 本导读类书名页(前2页), 找真实作者"""
import os, sys, io
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
if sys.platform == "win32":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
    except Exception:
        pass
import fitz
from dp_pdf_import import get_ocr, ocr_page

TARGETS = [
    '西方/布莱兹·帕斯卡尔/最伟大的思想家 - 帕斯卡尔.pdf',
    '西方/戈特弗里德·威廉·莱布尼茨/最伟大的思想家 - 莱布尼茨.pdf',
    '西方/索伦·克尔凯郭尔/最伟大的思想家 - 克尔恺廓尔.pdf',
    '西方/苏格拉底/最伟大的思想家 - 苏格拉底.pdf',
    '西方/米歇尔·福柯/导读福柯《规训与惩罚》.pdf',
    '西方/吉尔·德勒兹/导读德勒兹《差异与重复》.pdf',
    '西方/弗里德里希·恩格斯/《反杜林论》导读.pdf',
]
import hashlib, json
BASE = r'F:/program/Python/DeepPhilosophy/DeepPhilosophy'
bj = json.load(open(BASE + '/app/public/books.json', encoding='utf-8'))
items = bj if isinstance(bj, list) else bj.get('books', [])
by_id = {it.get('id'): it for it in items}

# 先找各 PDF 实际路径（文件名可能不同）
import glob
import tempfile
tmp = tempfile.mkdtemp()
for i, t in enumerate(TARGETS):
    fp = os.path.join(r'F:/philosophy', t).replace('\\', '/')
    if not os.path.exists(fp):
        # 模糊找
        cands = glob.glob(os.path.join(r'F:/philosophy', '**', os.path.basename(t)), recursive=True)
        fp = cands[0] if cands else fp
    rel = os.path.relpath(fp, r'F:/philosophy').replace('\\', '/')
    bid = hashlib.md5(rel.encode()).hexdigest()[:12]
    it = by_id.get(bid, {})
    print('== %s (%s) 作者现=%s ==' % (os.path.basename(fp), bid, it.get('author', '?')))
    if not os.path.exists(fp):
        print('   ! 文件不存在')
        continue
    doc = fitz.open(fp)
    for p in range(min(2, doc.page_count)):
        img = os.path.join(tmp, 'p%d.png' % p)
        pix = doc[p].get_pixmap(matrix=fitz.Matrix(2.0, 2.0))
        pix.save(img)
        text = ocr_page(img)
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        for l in lines[:12]:
            print('   %s' % l)
        print('   --- 页%d 结束 ---' % p)
    doc.close()
print('DONE')
