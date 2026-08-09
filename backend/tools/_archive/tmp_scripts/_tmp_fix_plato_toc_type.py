# -*- coding: utf-8 -*-
"""柏拉图 toc type 修正: section -> chapter (四处同步)"""
import json

targets = [
    r'F:\program\Python\DeepPhilosophy\DeepPhilosophy\backend\data\book_chapters\35279e2e439d\meta.json',
    r'F:\program\Python\DeepPhilosophy\DeepPhilosophy\app\public\backend\data\book_chapters\35279e2e439d\meta.json',
    r'F:\program\Python\DeepPhilosophy\DeepPhilosophy\backend\data\book_detail\35279e2e439d.json',
    r'F:\program\Python\DeepPhilosophy\DeepPhilosophy\app\public\book_detail\35279e2e439d.json',
]
for p in targets:
    d = json.load(open(p, encoding='utf-8'))
    for t in d['toc']:
        t['type'] = 'chapter'
    json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False)
    print('更新 %s: toc[0]=%s' % (p.split('DeepPhilosophy\\')[-1], json.dumps(d['toc'][0], ensure_ascii=False)))
