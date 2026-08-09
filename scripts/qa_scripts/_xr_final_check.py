# -*- coding: utf-8 -*-
"""三书重建最终人工核查：残留扫描 + 行内栏标 + 段落结构 + 首尾抽查"""
import json, os, re
base = os.path.dirname(os.path.abspath(__file__))
HDRS = [re.compile(r'^\d{1,4}第.卷论[人上]?\S{0,8}\s*$'), re.compile(r'^问题\d+[^\d][^\n]{0,49}\d{1,4}\s*$'),
        re.compile(r'^\d{3,4}[a-z]?\s*$'), re.compile(r'^问题\d+\s*$'), re.compile(r'^\d{1,3}\s*$'),
        re.compile(r'^第[—\-一二]卷\s*$'), re.compile(r'^新工具[①②]?\s*$'), re.compile(r'^序言[·.]?\s*$'),
        re.compile(r'^语录[?？]?\s*$'), re.compile(r'^第一章\s*$'), re.compile(r'^__FAILED__\s*$'),
        re.compile(r'^附录[一二三四五][：:（(《\S][^\n]{0,40}\d{1,4}\s*$'),
        re.compile(r'^[\d０-９]{1,4}译后记\s*$')]
INLINE = re.compile(r'(?<=[一-鿿])\d{3,4}[a-z]')
for name, d in [('第6卷', '_xr_out_aquinas6'), ('第7卷', '_xr_out_aquinas7'), ('新工具', '_xr_out_bacon')]:
    od = os.path.join(base, d)
    files = sorted([f for f in os.listdir(od) if f.endswith('.json') and f != 'meta.json'], key=lambda f: int(f.split('.')[0]))
    total_hdr = total_inl = total_fail = 0
    print('===== %s (%d 章) =====' % (name, len(files)))
    for fn in files:
        ch = json.load(open(os.path.join(od, fn), encoding='utf-8'))
        v = ch['content'][0]['value']
        lines = v.split('\n')
        hdr = [s for s in lines if s.strip() and any(h.match(s.strip()) for h in HDRS)]
        inl = INLINE.findall(v)
        fail = v.count('__FAILED__')
        total_hdr += len(hdr); total_inl += len(inl); total_fail += fail
        if hdr or inl or fail:
            print('  !! %s: 行首残留%d 行内栏标%d __FAILED__%d %s' % (fn, len(hdr), len(inl), fail, hdr[:2]))
    print('  合计: 行首残留 %d / 行内栏标 %d / __FAILED__ %d' % (total_hdr, total_inl, total_fail))
    # 段落结构抽查：第 1 章
    ch = json.load(open(os.path.join(od, files[0]), encoding='utf-8'))
    v = ch['content'][0]['value']
    paras = [p for p in v.split('\n\n') if p.strip()]
    print('  [%s] 段数 %d | 首段 100 字: %s' % (files[0], len(paras), paras[0][:100].replace('\n', '')))
    print('  末段 80 字: %s' % paras[-1][-80:].replace('\n', ''))
