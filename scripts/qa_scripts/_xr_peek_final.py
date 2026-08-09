# -*- coding: utf-8 -*-
"""重建后核查：各书关键章开头 200 字 + 残留扫描"""
import json, os, re
outs = {'第6卷': '_xr_out_aquinas6', '第7卷': '_xr_out_aquinas7', '新工具': '_xr_out_bacon'}
HDRS = [re.compile(r'^\d{1,4}第.卷论人\s*$'), re.compile(r'^问题\d+论[^\n]{0,40}\d{1,4}\s*$'),
        re.compile(r'^\d{3,4}[a-z]?\s*$'), re.compile(r'^问题\d+\s*$'), re.compile(r'^\d{1,3}\s*$'),
        re.compile(r'^第[一二]卷\s*$'), re.compile(r'^新工具[①②]?\s*$'), re.compile(r'^序言[·.]?\s*$'),
        re.compile(r'^语录[?？]?\s*$'), re.compile(r'^第一章\s*$'), re.compile(r'^__FAILED__\s*$'),
        re.compile(r'^附录[一二三四五][：:（(《\S][^\n]{0,40}\d{1,4}\s*$'),
        re.compile(r'^[\d０-９]{1,4}译后记\s*$')]
show = {'第6卷': ['0.json', '1.json'], '第7卷': ['0.json', '17.json', '22.json'], '新工具': ['0.json', '1.json', '2.json']}
base = os.path.dirname(os.path.abspath(__file__))
for name, d in outs.items():
    od = os.path.join(base, d)
    print('===== %s =====' % name)
    for fn in show[name]:
        ch = json.load(open(os.path.join(od, fn), encoding='utf-8'))
        v = ch['content'][0]['value']
        print('  [%s] %s — 开头 150 字:' % (fn, ch['title']))
        print('    ' + v[:150].replace('\n', '⏎'))
    # 残留扫描
    for fn in sorted(os.listdir(od)):
        if fn == 'meta.json':
            continue
        ch = json.load(open(os.path.join(od, fn), encoding='utf-8'))
        hits = [s for s in ch['content'][0]['value'].split('\n') if s.strip()
                and ('\ufffd' in s or '__FAILED__' in s or any(h.match(s.strip()) for h in HDRS))]
        if hits:
            print('  !! %s 残留 %d: %s' % (fn, len(hits), ' '.join(h[:25] for h in hits[:6])))
    print('  残留扫描完成')
