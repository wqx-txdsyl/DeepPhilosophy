# -*- coding: utf-8 -*-
"""柏拉图对话集 OCR 进度 + 引擎日志尾部"""
import json, os, glob

ck = json.load(open(r'F:\program\Python\DeepPhilosophy\DeepPhilosophy\backend\data\dp_pdf_import_ckpt.json', encoding='utf-8'))
key = '西方_柏拉图_柏拉图对话集.pdf'
pages = ck.get('ocr', {}).get(key, {})
done = sum(1 for v in pages.values() if isinstance(v, str) and len(v) > 5)
total = len(pages)
print('柏拉图对话集 OCR: %d/%d 页 (%d%%)' % (done, total, done * 100 // total if total else 0))

# 引擎日志（找最近的日志文件）
logs = sorted(glob.glob(r'F:\program\Python\DeepPhilosophy\DeepPhilosophy\backend\data\*.log') +
              glob.glob(r'F:\program\Python\DeepPhilosophy\DeepPhilosophy\*.log'), key=os.path.getmtime)
print()
print('最近日志:')
for l in logs[-5:]:
    print('  %s %dKB %s' % (l.split('\\')[-1], os.path.getsize(l) // 1024,
                            __import__('datetime').datetime.fromtimestamp(os.path.getmtime(l)).strftime('%H:%M')))
