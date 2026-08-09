# -*- coding: utf-8 -*-
"""OCR 引擎常驻监视: ckpt 变化才读, 状态变化才输出; 每本完成自动跟进下一本"""
import json, os, hashlib, time, datetime

CK = r'F:\program\Python\DeepPhilosophy\DeepPhilosophy\backend\data\dp_pdf_import_ckpt.json'
CD = r'F:\program\Python\DeepPhilosophy\DeepPhilosophy\backend\data\book_chapters'
KEY = '西方_柏拉图_柏拉图对话集.pdf'
REL = '西方/柏拉图/柏拉图对话集.pdf'

def bid_of(rel):
    return hashlib.md5(rel.encode()).hexdigest()[:12]

last_state = None
last_mt = 0
while True:
    try:
        mt = os.path.getmtime(CK)
        if mt == last_mt:
            time.sleep(20)
            continue
        last_mt = mt
        ck = json.load(open(CK, encoding='utf-8'))
    except Exception:
        time.sleep(20)
        continue

    books = ck.get('books', {})
    ocr = ck.get('ocr', {})
    # 只显示: 已完成书中重建异常的(n<=0) + ocr 缓存中未登记的进行中书
    parts = []
    registered = set()
    for rel, v in books.items():
        if v.get('src') != 'ocr':
            continue
        registered.add(rel)
        mp = os.path.join(CD, bid_of(rel), 'meta.json')
        n = -1
        if os.path.exists(mp):
            try:
                n = json.load(open(mp, encoding='utf-8'))['chapterCount']
            except Exception:
                pass
        if n <= 0:
            parts.append('%s:书 %d章!' % (rel.split('/')[-1][:16], n))
    for key, pages in ocr.items():
        rel = key[:-4].replace('_', '/')
        if rel in registered:
            continue
        done = sum(1 for x in pages.values() if isinstance(x, str) and len(x) > 5)
        parts.append('%s:OCR %d/%d' % (key[:-4].split('_')[-1][:16], done, len(pages)))
    state = '已完成%d本' % len(books) + (' | ' + ' | '.join(parts) if parts else ' | (无进行中)')
    if state != last_state:
        print('%s | %s' % (datetime.datetime.now().strftime('%H:%M:%S'), state), flush=True)
        last_state = state
    time.sleep(20)
