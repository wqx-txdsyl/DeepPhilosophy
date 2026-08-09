# -*- coding: utf-8 -*-
"""皮尔斯重建前自查: ①全书页眉残留(皮尔斯文选/第一部分xxx/纯页码行) ②每章首块头部 ③可疑短块"""
import json, re

CK = r'F:\program\Python\DeepPhilosophy\DeepPhilosophy\backend\data\dp_pdf_import_ckpt.json'
ck = json.load(open(CK, encoding='utf-8'))
ocr = ck['ocr']['西方_查尔斯_桑德斯_皮尔士_皮尔斯文选.pdf']

import importlib.util
spec = importlib.util.spec_from_file_location('rb', r'F:\program\Python\DeepPhilosophy\DeepPhilosophy\backend\tools\_tmp_pierce_rebuild.py')
rb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rb)

# 1. 页眉残留: 清洗后每页首行是否还有书名/部分名/页码
print('== 页眉残留检查 (清洗后页首行仍像页眉的) ==')
bad = 0
for pg in sorted(ocr, key=lambda x: int(x)):
    v = ocr[pg]
    if not isinstance(v, str) or len(v) < 5:
        continue
    cv = rb.clean_page(v)
    first = next((l.strip() for l in cv.split('\n') if l.strip()), '')
    if re.match(r'^第[一二三四五]部分', first) or first in ('皮尔斯文选', '皮尔土文选'):
        print('  页%s 残留: %s' % (pg, first[:30]))
        bad += 1
print('  残留 %d 处' % bad)

# 2. 每章首块头部 (标题页是否正确)
print('\n== 每章首块头部 ==')
for i, (idx, t, pg) in enumerate(rb.starts):
    blocks = rb.chapter_blocks(pg, rb.starts[i + 1][2] if i + 1 < len(rb.starts) else max(rb.PAGES) + 1)
    if not blocks:
        print('  [%2d] %s 页%d — 空!?' % (idx, t[:20], pg))
        continue
    head = next((l.strip() for l in blocks[0]['value'].split('\n') if l.strip()), '')
    print('  [%2d] 页%3d 首行: %s' % (idx, pg, head[:40]))

# 3. 可疑短块 (<80字, 可能是页眉残留页)
print('\n== 可疑短块 (<80字, 章节非末块) ==')
n = 0
for i, (idx, t, pg) in enumerate(rb.starts):
    pg_to = rb.starts[i + 1][2] if i + 1 < len(rb.starts) else max(rb.PAGES) + 1
    blocks = rb.chapter_blocks(pg, pg_to)
    for b in blocks[:-1]:
        if len(b['value']) < 80:
            head = next((l.strip() for l in b['value'].split('\n') if l.strip()), '')
            print('  [%2d] %s' % (idx, head[:60]))
            n += 1
print('  共 %d 个' % n)
