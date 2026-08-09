# -*- coding: utf-8 -*-
"""同步 3 本章数变化书的 chapterCount（双端 books.json + book_detail）+ 四步验证 8 本"""
import json, os, re, sys, hashlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _xr_verify_generic import verify

DP = 'f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters'
PA = 'f:/program/Python/PhiAgent/backend/data/book_chapters'
DP_PUB = 'f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/backend/data/book_chapters'
CC_CHANGED = {'7657ef4a2cd3': 117, 'ef76ae88994f': 33, 'bbac1be0bb4b': 445}

def chap_count(bid, base):
    p = os.path.join(base, bid)
    if not os.path.isdir(p):
        return None
    return len([f for f in os.listdir(p) if f.endswith('.json') and f != 'meta.json'])

def set_cc(books_path, detail_path, bid, cc):
    # books.json
    bk = json.load(open(books_path, encoding='utf-8'))
    for b in bk:
        if b.get('id') == bid:
            old = b.get('chapterCount')
            b['chapterCount'] = cc
            json.dump(bk, open(books_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
            print('  books.json %s: cc %s -> %s' % (bid, old, cc))
            break
    # book_detail
    if os.path.exists(detail_path):
        d = json.load(open(detail_path, encoding='utf-8'))
        old = d.get('chapterCount', d.get('chapters_count'))
        if 'chapterCount' in d:
            d['chapterCount'] = cc
        if 'chapters_count' in d:
            d['chapters_count'] = cc
        json.dump(d, open(detail_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
        print('  detail %s: cc %s -> %s' % (bid, old, cc))

print('=== 1) 同步 chapterCount ===')
for bid, cc in CC_CHANGED.items():
    # 实际文件数确认（DP 为准）
    real = chap_count(bid, DP)
    print('  %s 实际文件数: %s (目标 %s)' % (bid, real, cc))
    set_cc('f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/books.json',
           'f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/book_detail/%s.json' % bid, bid, cc)
    set_cc('f:/program/Python/PhiAgent/app/public/books.json',
           'f:/program/Python/PhiAgent/app/public/book_detail/%s.json' % bid, bid, cc)

print()
print('=== 2) 四步验证 8 本 ===')
for bid in ['5f838ef64e5e', 'c0e78ea6f80a', '5135fe68ee4a', 'c97cb4e6161a',
            '7657ef4a2cd3', 'ef76ae88994f', 'bbac1be0bb4b', '4cc9d23c7dbf']:
    verify(bid)
