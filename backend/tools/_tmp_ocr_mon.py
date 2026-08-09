# -*- coding: utf-8 -*-
"""OCR 进度监控（Monitor 用）：每 3 分钟输出一行进度事件
格式: [HH:MM] OCR {完成}/{121} 本 | 当前: {书名} 页 {已识别}/{总页} | 日志 {最后活动}"""
import sys, os, re, json, hashlib
sys.stdout.reconfigure(encoding='utf-8')

BASE = r'F:/program/Python/DeepPhilosophy/DeepPhilosophy'
CKPT = os.path.join(BASE, 'backend/data/dp_pdf_import_ckpt.json')
LOG = os.path.join(BASE, 'backend/data/ocr_s0.log')
BOOKS_DIR = r'F:/philosophy'

c = json.load(open(CKPT, encoding='utf-8'))
n = len(c.get('books', {}))

# 当前处理中的书：日志最后一条 [i/121] 行
cur = ''
last_act = ''
with open(LOG, encoding='utf-8', errors='replace') as f:
    lines = f.readlines()
for ln in reversed(lines):
    m = re.search(r'\[(\d+)/(\d+)\] (\S+)', ln)
    if m:
        cur = m.group(3)
        break
for ln in reversed(lines):
    m = re.search(r'\[(20\d\d/\d\d/\d\d \d\d:\d\d:\d\d)\]', ln)
    if m:
        last_act = m.group(1)
        break

# 页级进度：c['ocr'][safe_key]
pages_done = total_pages = 0
if cur:
    safe = re.sub(r'[^\w\-.]', '_', cur)
    v = c.get('ocr', {}).get(safe, {})
    if isinstance(v, dict):
        pages_done = sum(1 for x in v.values() if x)
        total_pages = len(v) or pages_done
    # PDF 总页数（fitz，较准）
    try:
        import fitz
        fp = None
        for region in ['东方', '西方']:
            rp = os.path.join(BOOKS_DIR, region)
            for root, dirs, fs in os.walk(rp):
                for fn in fs:
                    if fn.lower().endswith('.pdf') and re.sub(r'[^\w\-.]', '_', os.path.join(root, fn).replace('\\', '/').replace('F:/philosophy/', '')) == safe:
                        fp = os.path.join(root, fn)
                        break
        if fp:
            doc = fitz.open(fp)
            total_pages = doc.page_count
            doc.close()
    except Exception:
        pass

print('[%s] OCR %d/121 | %s 页 %d/%d | 日志 %s' % (
    __import__('time').strftime('%H:%M'), n, cur or '?', pages_done, total_pages, last_act))
