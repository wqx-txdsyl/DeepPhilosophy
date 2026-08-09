# -*- coding: utf-8 -*-
"""诊断 27 本结构问题书的 meta/detail 实际内容"""
import json, os, sys, io

if sys.platform == "win32":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
    except Exception:
        pass

BASE = r'F:/program/Python/DeepPhilosophy/DeepPhilosophy'
BC = os.path.join(BASE, 'backend/data/book_chapters')
DETAIL = os.path.join(BASE, 'backend/data/book_detail')

bids = [
    ('10e1874c2255','康德三大批判合集'),('8c0c6955c793','纯粹理性批判'),('f08c1ead3164','判断力批判'),
    ('88b56fb4da52','第一哲学沉思集'),('7729ccdecb0f','马克思恩格斯文集'),('178e7d06d42d','人性论'),
    ('40750581f8e8','存在主义人道主义'),('48f7bf321598','快乐的科学'),('dd75d637a2ad','托马斯·霍布斯'),
    ('74ee21ced920','道德与立法原理导论'),('4fc33e4af5fb','梦的解析'),('d1a2be0b5837','荣格心理学'),
    ('64056c6623ee','新弗雷格主义'),('1085686cbd33','MEGA德意志意识形态'),('e2a4c4f78c40','现象学的观念'),
    ('221f09d04944','自然与快乐'),('978ade412255','雅斯贝尔斯传'),('cc9d0d9358a7','擬仿物'),
    ('b3219ec260ed','读资本论'),('23ab04b02f68','塞涅卡'),('8a451d16f1b4','哲学的慰藉'),
    ('4be7b72cf01d','图斯库兰论辩集'),('26f5e0df6d76','哲学规劝录'),('0d31135f957d','公共领域新结构转型'),
    ('b2fbc225f414','你的第一本哲学书'),('2cbf90eb6f69','大问题'),('219b862077e1','道家与道教思想简史'),
]

for bid, name in bids:
    D = os.path.join(BC, bid)
    m = json.load(open(os.path.join(D, 'meta.json'), encoding='utf-8'))
    n = m.get('chapterCount', 0)
    toc = m.get('toc', [])
    toc_type = type(toc[0]).__name__ if toc else 'EMPTY'
    files = sorted(f for f in os.listdir(D) if f.endswith('.json') and f != 'meta.json')
    num_files = len(files)
    missing = [str(i) for i in range(n) if not os.path.exists(os.path.join(D, '%d.json' % i))]
    ct = m.get('chapterTitles', [])
    dfp = os.path.join(DETAIL, bid + '.json')
    d = json.load(open(dfp, encoding='utf-8')) if os.path.exists(dfp) else {}
    print('==== %s %s' % (bid, name))
    print('  meta.title=%r' % (m.get('title', '')[:24]))
    print('  meta.author=%r' % (m.get('author', '')[:24]))
    print('  detail.title=%r' % (d.get('title', '')[:24]))
    print('  detail.author=%r' % (d.get('author', '')[:24]))
    print('  chapterCount=%d 文件=%d 缺=%s' % (n, num_files, missing[:6] if missing else '无'))
    print('  toc[0] 类型=%s 样例=%s' % (toc_type, json.dumps(toc[0], ensure_ascii=False)[:50] if toc else ''))
    print('  toc 项数=%d chapterTitles=%d 项 前2=%s' % (len(toc), len(ct), json.dumps(ct[:2], ensure_ascii=False)[:40]))
