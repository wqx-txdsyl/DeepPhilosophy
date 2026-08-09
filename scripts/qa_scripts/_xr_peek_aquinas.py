# -*- coding: utf-8 -*-
"""神学大全6/7卷核查：打开正式数据（DP backend）抽查 + 残留扫描"""
import json, os, re
BASE = 'f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters'
HDRS = [re.compile(r'^\d{1,4}第.卷论人\s*$'), re.compile(r'^问题\d+论[^\n]{0,40}\d{1,4}\s*$'),
        re.compile(r'^\d{3,4}[a-z]?\s*$'), re.compile(r'^问题\d+\s*$'), re.compile(r'^\d{1,3}\s*$'),
        re.compile(r'^第[一二]卷\s*$'), re.compile(r'^附录[一二三四五][：:（(《\S][^\n]{0,40}\d{1,4}\s*$'),
        re.compile(r'^[\d０-９]{1,4}译后记\s*$')]
for bid, name in [('f52ed83b99d9', '第6卷'), ('9ed36aca09c5', '第7卷')]:
    d = os.path.join(BASE, bid)
    files = sorted([f for f in os.listdir(d) if f.endswith('.json') and f != 'meta.json'],
                   key=lambda f: int(f.split('.')[0]))
    print('===== %s %d 章 =====' % (name, len(files)))
    for fn in files:
        ch = json.load(open(os.path.join(d, fn), encoding='utf-8'))
        v = ch['content'][0]['value']
        lines = v.split('\n')
        # 残留行收集（前 8 条）
        hits = []
        for ln in lines:
            s = ln.strip()
            if not s or '\ufffd' in s or '__FAILED__' in s or '（共' in s and '条）' in s:
                hits.append('<' + s[:40] + '>')
            else:
                for h in HDRS:
                    if h.match(s):
                        hits.append('<' + s[:40] + '>')
                        break
        if hits:
            print('  [%s] 残留 %d 行: %s' % (fn, len(hits), ' '.join(hits[:8])))
