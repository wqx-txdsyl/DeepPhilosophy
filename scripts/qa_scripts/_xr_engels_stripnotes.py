# -*- coding: utf-8 -*-
"""自然辩证法：删除正文注标（0-32 章），保留注文段
删：半角 [N]、全角［N］、半角 (N)（纯数字）
留："［第X页］"出处标注、33/34/35 条目编号、32 人名索引页码、注文段
用法: python _xr_engels_stripnotes.py [--apply]
"""
import json, os, re, sys

BID = 'aa21ac425e87'
BASE = f'f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{BID}'

HALF = re.compile(r'\[\d{1,4}\]')       # [N]
FULL = re.compile(r'［\d+］')           # ［N］
PAREN = re.compile(r'\(\d{1,3}\)')      # (N)
PAGE_MARK = re.compile(r'［第\d+页］')  # 保留：出处标注

def strip(s):
    # 保留 PAGE_MARK，删其他三套注标
    s2 = PAGE_MARK.sub(lambda m: '\x00' + m.group(0) + '\x00', s)  # 保护
    s2 = HALF.sub('', s2)
    s2 = FULL.sub('', s2)
    s2 = PAREN.sub('', s2)
    s2 = s2.replace('\x00', '')
    # 清理注标删除后的残留空格/标点粘连（只动半角空格与半角标点，绝不动全角括号）
    s2 = re.sub(r' +([，。、；：])', r'\1', s2)
    s2 = re.sub(r' +\)', ')', s2)
    s2 = re.sub(r' +\]', ']', s2)
    s2 = re.sub(r'([一-鿿])\x20+([一-鿿])', r'\1\2', s2)  # 中文间空格（OCR 残渣）
    s2 = re.sub(r'\x20{2,}', ' ', s2)
    s2 = s2.strip()
    return s2

def main():
    apply = '--apply' in sys.argv
    total = {'half': 0, 'full': 0, 'paren': 0}
    samples = []
    for f in sorted(os.listdir(BASE), key=lambda x: int(x.split('.')[0]) if x.endswith('.json') and x != 'meta.json' else 99):
        if not f.endswith('.json') or f == 'meta.json':
            continue
        idx = int(f.split('.')[0])
        if idx >= 33:   # 33/34/35 细目章不动（条目编号）
            continue
        path = os.path.join(BASE, f)
        c = json.load(open(path, encoding='utf-8'))
        changed = 0
        for b in c['content']:
            v = b.get('value', '') if isinstance(b, dict) else ''
            if not isinstance(v, str):
                continue
            nh, nf, np = len(HALF.findall(v)), len(FULL.findall(v)), len(PAREN.findall(v))
            if nh or nf or np:
                total['half'] += nh; total['full'] += nf; total['paren'] += np
                if len(samples) < 10:
                    samples.append((f, v[:60]))
                b['value'] = strip(v)
                changed += 1
        if apply and changed:
            json.dump(c, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)

    print('=== 注标删除统计（' + ('已落盘' if apply else '预览') + '）===')
    print(f'  半角 [N]: {total["half"]}')
    print(f'  全角［N］: {total["full"]}')
    print(f'  半角 (N): {total["paren"]}')
    if not apply:
        print('=== 样本（删除前）===')
        for f, s in samples:
            print(f'  [{f}] {s}')

if __name__ == '__main__':
    main()
