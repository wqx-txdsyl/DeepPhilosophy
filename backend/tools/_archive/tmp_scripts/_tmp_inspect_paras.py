# -*- coding: utf-8 -*-
"""检查 OCR 页面文本的段落结构：页内是否有 \n\n 段落分隔（决定重建脚本如何保留段落）"""
import json

CKPT = r'F:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/dp_pdf_import_ckpt.json'
ckpt = json.load(open(CKPT, encoding='utf-8'))

for safe in ['西方_托马斯_霍布斯_托马斯_霍布斯.pdf', '西方_扬布里柯_哲学规劝录_哲学的慰藉.pdf']:
    ocr = ckpt.get('ocr', {}).get(safe, {})
    print('=' * 70)
    print(safe, '| 页数:', len(ocr))
    # 找第一个超过 1 个 \n\n 的页
    shown = 0
    for k in sorted(int(x) for x in ocr):
        v = ocr[str(k)]
        if not v or v == '__FAILED__':
            continue
        dd = v.count('\n\n')
        if dd > 0:
            print('--- 页 %d: \\n\\n 段分隔 %d 处 ---' % (k, dd))
            lines = v.split('\n')
            print('前 12 行:', repr(lines[:12]))
            # 找 \n\n 附近上下文
            idx = v.find('\n\n')
            print('首个 \\n\\n 上下文:', repr(v[max(0, idx-40):idx+40]))
            shown += 1
            if shown >= 2:
                break
    # 统计各页 \n\n 数量分布
    from collections import Counter
    cnt = Counter()
    for k in sorted(int(x) for x in ocr):
        v = ocr[str(k)]
        if not v or v == '__FAILED__':
            continue
        d = v.count('\n\n')
        cnt[d] += 1
    print('页间 \\n\\n 分布 (段分隔数:页数):', dict(sorted(cnt.items())))
