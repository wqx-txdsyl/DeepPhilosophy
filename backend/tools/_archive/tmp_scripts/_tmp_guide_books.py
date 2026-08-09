# -*- coding: utf-8 -*-
"""扫描导读/评传类书: 最伟大的思想家/导读/传/解读/简史 等, 列当前作者"""
import json

cat = json.load(open(r'F:\program\Python\DeepPhilosophy\DeepPhilosophy\backend\data\books_catalog.json', encoding='utf-8'))
KW = ['最伟大的思想家', '导读', '传', '解读', '简史', '评传', '浅说', '入门', '导论', '介绍', '和快乐', '研究']
for item in cat['books']:
    t = item['title']
    if any(k in t for k in ('最伟大的思想家', '导读', '解读', '简史', '评传', '浅说', '入门')):
        print('%-55s | %-20s | %s' % (t[:52], item.get('author', '')[:18], item['id']))
