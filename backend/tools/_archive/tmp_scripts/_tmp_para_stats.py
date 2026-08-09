# -*- coding: utf-8 -*-
"""段落重建后段长分布统计 (临时)"""
import json, os, sys, io, re

if sys.platform == "win32":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
    except Exception:
        pass

BASE = r'F:/program/Python/DeepPhilosophy/DeepPhilosophy'
CKPT = os.path.join(BASE, 'backend/data/dp_pdf_import_ckpt.json')
KEY = '西方_格奥尔格_威廉_弗里德里希_黑格尔_精神现象学.pdf'
ck = json.load(open(CKPT, encoding='utf-8'))
pages = ck['ocr'][KEY]
n = len(pages)

HEADER = '精神现象学'
VARS = ['一精神现象学', '1精神现象学', '厂精神现象学', 'I精神现象学']
NAMES = ['第一章感性确定性，或“这一个”和意谓', '第二章知觉，或物与错觉',
         '第三章力与知性，现象和超感性世界', '第四章自身确定性的真理',
         '第五章理性的确定性和真理', '第六章精神', '第七章宗教', '第八章绝对知识',
         '序言', '导论', '译者序', '总序', '主要译名对照及索引',
         '第一部分 意识', '第二部分 自我意识',
         '第三部分（AA） 理性', '第三部分（BB） 精神',
         '第三部分(CC) 宗教', '第三部分(DD) 绝对知识']

def clean_line(ln):
    if ln == HEADER or ln in VARS or ln == '+++':
        return True
    if re.fullmatch(r'\d{1,3}', ln):
        return True
    if re.fullmatch(r'\[\s*\d+\s*\]', ln):
        return True
    if ln in NAMES:
        return True
    return False

def para_end(line):
    s = line.strip()
    while s and s[-1] in '\u201d\u300d\u300f)）】':
        s = s[:-1]
    return bool(s) and s[-1] in '。？！…'

def build_paras(lines):
    paras, cur = [], []
    for ln in lines:
        cur.append(ln)
        if para_end(ln):
            paras.append('\n'.join(cur))
            cur = []
    if cur:
        paras.append('\n'.join(cur))
    return [p for p in paras if p.strip()]

ANCH = [(0, '导读', True), (11, '序言', False), (68, '导论', False), (82, '意识', False),
        (137, '自我意识', False), (178, '理性', False), (324, '精神', False),
        (495, '宗教', False), (575, '绝对知识', False)]

loc_pages = {}
for no, ti, is_f in ANCH:
    if is_f:
        continue
    for pgi in range(n):
        t = pages.get(str(pgi), '')
        hit = False
        for l in t.split('\n'):
            if re.search(r'\[\s*%d\s*\]' % no, l) and len(l) < 60:
                loc_pages[no] = pgi
                hit = True
                break
        if hit:
            break
print('锚点页:', loc_pages)

for k in range(len(ANCH)):
    no, ti, is_f = ANCH[k]
    pgi = 0 if is_f else loc_pages[no]
    end = loc_pages.get(ANCH[k + 1][0], n) if k + 1 < len(ANCH) else n
    stream = []
    for pi in range(pgi, end):
        t = pages.get(str(pi), '')
        if not t or t == '__FAILED__':
            continue
        for l in t.split('\n'):
            s = l.strip()
            if s and not clean_line(s):
                stream.append(s)
    i = 0
    while i < len(stream) and i < 4 and not para_end(stream[i]):
        if '部分' in stream[i] or len(stream[i]) <= 4:
            i += 1
        else:
            break
    del stream[:i]
    paras = build_paras(stream)
    lens = sorted(len(p) for p in paras)
    med = lens[len(lens) // 2] if lens else 0
    avg = sum(lens) / len(lens) if lens else 0
    over = sum(1 for l in lens if l > 800)
    print('[%d] %-8s 段数:%3d 中位:%4d 平均:%4d 超800:%3d 最短:%3d 最长:%5d'
          % (k, ti, len(paras), med, avg, over, lens[0] if lens else 0, lens[-1] if lens else 0))
