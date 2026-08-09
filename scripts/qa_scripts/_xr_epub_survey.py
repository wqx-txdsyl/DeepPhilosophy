# -*- coding: utf-8 -*-
"""epub 书 toc + 正文形态抽查：打印 toc 标题（限 18 条）+ 各章字数/段数统计 + 正文样本
用法: python _xr_epub_survey.py <bid1> <bid2> ...
"""
import json, os, re, sys

DP = 'f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters'

def survey(bid):
    base = os.path.join(DP, bid)
    if not os.path.isdir(base):
        print(f'=== {bid} 无章节目录 ===')
        return
    m = json.load(open(os.path.join(base, 'meta.json'), encoding='utf-8'))
    toc = m.get('toc', [])
    print(f'=== {bid} toc {len(toc)} 章 ===')
    for t in toc[:18]:
        idx = t.get('index')
        title = t.get('title', '')[:38]
        print(f'  [{idx:>3}] {title}')
    if len(toc) > 18:
        print(f'  …共 {len(toc)} 章')
    # 各章字数/段数
    import glob
    files = sorted(glob.glob(os.path.join(base, '*.json')), key=lambda p: int(os.path.basename(p)[:-5]) if os.path.basename(p) != 'meta.json' else 999)
    print('  字数分布（章: 字数/段数）:')
    for f in files:
        if os.path.basename(f) == 'meta.json':
            continue
        c = json.load(open(f, encoding='utf-8'))
        paras = [b.get('value', '') for b in c['content'] if isinstance(b, dict) and isinstance(b.get('value'), str) and b['value'].strip()]
        n = sum(len(p) for p in paras)
        print(f'    [{os.path.basename(f)[:-5]:>3}] {n:>7}字 {len(paras):>4}段', end='')
        if len(paras) >= 1:
            first = paras[0][:22].replace('\n', ' ')
            print(f'  首段: {first}', end='')
        print()
    # 正文样本：中段某章随机段落（乱码/页眉噪声检测）
    print('  样本（第 60% 章的中段段落）:')
    if len(files) > 1:
        f = files[max(1, int(len(files) * 0.6))]
        c = json.load(open(f, encoding='utf-8'))
        paras = [b.get('value', '') for b in c['content'] if isinstance(b, dict) and isinstance(b.get('value'), str) and b['value'].strip()]
        if paras:
            for p in paras[len(paras) // 2: len(paras) // 2 + 3]:
                print('    ', p[:90].replace('\n', ' '))
    print()

if __name__ == '__main__':
    for bid in sys.argv[1:]:
        survey(bid)
