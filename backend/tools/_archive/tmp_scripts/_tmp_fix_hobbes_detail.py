# -*- coding: utf-8 -*-
"""修正 dd75d637a2ad（罗宾·邦斯《霍布斯》）detail/books.json 的 author+summary 错配:
旧数据把这本书误描述为霍布斯本人的《论公民》——实际是 R.E.R. Bunce 的传记（封面 THOMAS HOBBES, 英]罗宾·邦斯）。
title 保持封面主标题“托马斯•霍布斯”不变。三处同步: backend detail + public detail + books.json。
"""
import json, io, sys

BACKEND_DETAIL = r'F:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_detail/dd75d637a2ad.json'
PUBLIC_DETAIL = r'F:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/book_detail/dd75d637a2ad.json'
BOOKS_JSON = r'F:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/books.json'

AUTHOR = '罗宾·邦斯'
SUMMARY = ('本书是英国学者罗宾·邦斯（Robin E. R. Bunce）撰写的霍布斯政治哲学导论，'
           '收入“主要保守主义与自由至上主义思想家”系列，中英对照出版。'
           '全书从霍布斯的生平与时代讲起——他因性格与观点备受争议，'
           '一生经历英国内战与共和国的动荡——进而系统梳理其政治著作中的核心问题：'
           '人为何需要国家，社会契约如何可能，主权者的权力边界何在，臣民在何种条件下仍保有自由。'
           '作者将《利维坦》等著作放回霍布斯本人的问题语境中理解，'
           '而不是把《利维坦》当作21世纪的政治蓝图，'
           '并附建议进一步阅读的文献指引与名词索引。')

def patch_detail(path):
    d = json.load(open(path, encoding='utf-8'))
    old = (d.get('author'), d.get('summary', '')[:20])
    d['author'] = AUTHOR
    d['summary'] = SUMMARY
    json.dump(d, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print('detail:', path.split('/')[-1], '| 旧 author/summary:', old)

def patch_books(path):
    books = json.load(open(path, encoding='utf-8'))
    n = 0
    for b in books:
        if b.get('id') == 'dd75d637a2ad':
            old = (b.get('author'), b.get('summary', '')[:20])
            b['author'] = AUTHOR
            b['summary'] = SUMMARY
            n += 1
            print('books.json | 旧 author/summary:', old)
    json.dump(books, open(path, 'w', encoding='utf-8'), ensure_ascii=False)
    print('books.json 更新条数:', n)

patch_detail(BACKEND_DETAIL)
patch_detail(PUBLIC_DETAIL)
patch_books(BOOKS_JSON)
print('完成')
