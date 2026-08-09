# -*- coding: utf-8 -*-
"""验证访谈页（137-168）奇偶分流：检查左右流各自拼接的通顺度"""
import json, re
ck = json.load(open('f:/program/Python/PhiAgent/backend/data/dp_pdf_import_ckpt.json', encoding='utf-8'))
pages = ck['ocr']['西方_托马斯_库恩_结构之后的路.pdf']

def lines_of(pn):
    return [l.strip() for l in str(pages[str(pn)]).split('\n') if l.strip()]

def is_bookhead(l): return l.startswith('结构之后')
def is_pageno(l): return re.match(r'^\d{1,3}$', l)
def is_volhead(l): return re.match(r'^第[一二三]+部分(?:/[^0-9]{1,14}\d{1,3})?$', l) or re.match(r'^第[一二三]+部分/与托马斯', l)

def strip_header(lines):
    out = []
    for i, l in enumerate(lines):
        if i < 3 and (is_bookhead(l) or is_pageno(l) or is_volhead(l)):
            continue
        out.append(l)
    return out

ENDMARK = '。！？；”'

for pn in range(137, 169):
    L = strip_header(lines_of(pn))
    odd = L[0::2]    # 左页（叙述流，先读）
    even = L[1::2]   # 右页（问答流，后读）
    # 拼接评分：行尾+行首直接拼接为同句（行尾无句末标点 且 行首非说话人前缀）的占比
    def score(seq):
        ok = 0
        for i in range(len(seq) - 1):
            a, b = seq[i], seq[i + 1]
            if a[-1] not in ENDMARK and not re.match(r'^(库恩|巴尔塔斯|伽伏罗格鲁|金迪|考斯塔斯|瓦塞里奇)[：:]', b):
                ok += 1
        return ok / max(1, len(seq) - 1)
    s_odd, s_even = score(odd), score(even)
    flag = ''
    if s_odd < 0.5 or s_even < 0.5:
        flag = '  ⚠ 低拼接'
    print(f'页{pn}: odd(左){len(odd)}行 拼接{s_odd:.0%} | even(右){len(even)}行 拼接{s_even:.0%}{flag}')
    if flag:
        print('   odd 前3:', [x[:22] for x in odd[:3]])
        print('   even 前3:', [x[:22] for x in even[:3]])
