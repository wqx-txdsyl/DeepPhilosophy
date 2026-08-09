# -*- coding: utf-8 -*-
"""注标删除后样本抽查：打印关键段落当前形态"""
import json, os, re

BASE = 'f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/aa21ac425e87'

def paragraphs(fname, key=None, maxlen=120):
    c = json.load(open(os.path.join(BASE, fname), encoding='utf-8'))
    out = []
    for b in c['content']:
        v = b.get('value', '') if isinstance(b, dict) else ''
        if not isinstance(v, str) or not v.strip():
            continue
        if key and key not in v:
            continue
        out.append(v.strip()[:maxlen])
    return out

print('=== 0.json 首段（原"［164］ (1)(1) 方括号中的数字…"）===')
print(paragraphs('0.json')[0])
print()
print('=== 0.json 含"方括号中的数字"段 ===')
for p in paragraphs('0.json', '方括号中的数字'):
    print(' ', p)
print()
print('=== 1.json 注文段（原"…(1) 指《〈反杜林论〉旧序…——编者注[1] "）===')
for p in paragraphs('1.json', '编者注'):
    print(' ', p)
print()
print('=== 2.json 含"意大利伟大人物"段 ===')
for p in paragraphs('2.json', '意大利伟大人物'):
    print(' ', p)
print()
print('=== 2.json 含"独立宣言"段（原"[12] ，诚然"）===')
for p in paragraphs('2.json', '独立宣言'):
    print(' ', p)
print()
print('=== 2.json 含"手稿此处缺损"注文段（原"…(2) 手稿此处缺损。——编者注(3)…"）===')
for p in paragraphs('2.json', '手稿此处缺损'):
    print(' ', p)
print()
print('=== 0.json 含"［第"段（出处标注应保留）===')
for p in paragraphs('0.json', '［第'):
    print(' ', p)
